# -*- coding: utf-8 -*-
"""
Load AWG / RECT phasing presets into spin-dynamics sequences.
=============================================================

Turn a saved pulse-EPR experiment preset -- the ``*.phase_awg`` files of the
AWG phasing control center (``awg_phasing_insys.py``) and the ``*.phase`` files
of the RECT one (``phasing_insys.py``) -- into the event list and phase cycle
that :mod:`atomize.math_modules.spin_dynamics` runs, so a sequence can be
*simulated exactly as the hardware will play it* before going to the bench.

What it does
------------
:func:`parse_preset` reads a preset into a :class:`Preset` (pulse table +
the scalar parameters the simulator needs). :meth:`Preset.build` produces
``(events, phase_cycle)`` for one sweep point -- ``events`` a list of
:class:`spin_dynamics.Pulse` / :class:`spin_dynamics.Delay` /
:class:`spin_dynamics.Detect`, ``phase_cycle`` the per-step
``(phase shifts, receiver)`` list -- ready for :meth:`spin_dynamics.Engine.run`.
:meth:`Preset.sweep_axis` returns the experiment x-axis (ns). The spin system
and the ensemble (offsets, line shape, B1, relaxation) are *not* part of the
preset -- you build the :class:`spin_dynamics.Engine` for those and feed it
the events::

    import atomize.math_modules.preset_loader as pl
    import atomize.math_modules.spin_dynamics as sd

    pre = pl.parse_preset('experiments/3peseem_4s.phase_awg')
    sys = sd.SpinSystem((0.5, 0.5)); sys.zeeman(1, 0.0149)
    sys.hyperfine(0, 1, A=0.004, B=0.003)
    offs = np.linspace(-0.1, 0.1, 401)
    eng = sd.Engine(sys, offsets=offs, weights=sd.gaussian_weights(offs, 0.03))
    axis = pre.sweep_axis()
    trace = []
    for i in range(axis.size):
        events, cyc = pre.build(step=i)
        trace.append(eng.run(events, phase_cycle=cyc)[0]['v'][0])

Field mapping
-------------
A pulse line is ``TYPE, start, length, sigma, freq, sweep, coef, [phase],
st_inc, len_inc[, st_inc2]`` (AWG) or ``TYPE, start, length, [phase], st_inc,
len_inc`` (RECT). P1 is always the ``DETECTION`` window. The mapping to the
simulator:

* **TYPE** -> shape: ``SINE`` / ``MW`` -> ``rectangular``, ``GAUSS`` ->
  ``gaussian``, ``SINC`` -> ``sinc``, ``WURST``/``SECH/TANH`` kept; ``LASER`` /
  ``BLANK`` lines are dropped (no microwave). ``n``/``b`` of WURST/sech come
  from the preset's global ``N WURST; SECH/TANH`` / ``B SECH/TANH`` lines.
* **start / length** -> absolute timing. Active pulses (``length != 0``) become
  ``Pulse(tp=length)`` separated by ``Delay`` events; the detection line's
  ``start`` places the ``Detect`` window (``length`` = its width).
* **freq / sweep** (MHz) -> the pulse carrier offset ``center`` and the chirp
  width ``bw``. ``center = freq - freq_obs`` with ``freq_obs`` the detection
  pulse's frequency, i.e. the simulation runs in the **observer rotating
  frame**: same-frequency pulses sit at ``center = 0`` and a DEER pump at a
  different ``freq`` gets the right offset automatically. RECT presets carry no
  frequency field -> ``center = 0``.
* **coef** (amplitude %) -> peak nutation ``nu1 = coef * nu1_per_coef`` (GHz).
  This is the one genuinely hardware-/setup-dependent number: the amplifier is
  often nonlinear, so the shipped presets do *not* share a single coef->flip
  slope (a pi/2 is coef 100 at 22.4 ns in the Hahn preset but coef 60 at 16 ns
  in the 3-pulse-ESEEM one). **Pin it from your own nutation measurement** via
  ``build(flip_cal=(coef, length_ns, flip_rad))`` -- e.g.
  ``flip_cal=(100, 22.4, pi/2)``. The bare default (``nu1_per_coef =
  0.25/22.4/15`` GHz/%) is only a nominal fallback. RECT presets set the flip
  angle by *length* at full drive, so they use a single fixed ``nu1_rect``
  (default ``0.25/22.4`` GHz, i.e. length 22.4 -> pi/2).
* **[phase] / detection [phase]** -> phase cycle, via
  :func:`coherence_pathways.expand_phase_cycling` (the same expansion the
  hardware applies): each active pulse's notation gives its per-step phase, and
  the detection line's coefficient list gives the receiver phase.
* **st_inc / len_inc** -> per-step start / length increments: ``build(step=i)``
  uses ``start + i*st_inc`` and ``length + i*len_inc`` (detection included, so
  the window tracks the echo). ``st_inc2`` (ESEEM tau-averaging) is parsed but
  not applied by ``build`` (it is a cumulative per-cycle shift handled at
  acquisition time; out of scope here).

Resonator
---------
The preset does **not** store resonator settings (those are AWG-tab controls).
Pass ``resonator={'nu0':.., 'Q':.., ...}`` to :meth:`Preset.build` to filter
every shaped pulse through the transfer function exactly as
:func:`pulse_excitation.apply_resonator` does (ring-down included -- the
following delay is shortened by the ring-down time so absolute timing is kept).

Limitations: a single rotating frame (a frequency-selective DEER pump is
modelled by its ``center`` offset, not a second frame), and ``st_inc2`` /
laser-triggered modes are not expanded. The phase-cycle *selection* is exact;
amplitudes follow from the nutation calibration above.
"""

import re

import numpy as np

import atomize.math_modules.spin_dynamics as sd
import atomize.math_modules.coherence_pathways as coh


# pi/2 at length 22.4 ns -> nu1 = 0.25/22.4 GHz; at coef 15 that fixes the
# amplitude-per-percent slope. Both are overridable in build().
NU1_REF = 0.25 / 22.4                 # GHz  (full-drive pi/2-at-22.4ns nutation)
COEF_REF = 15.0
NU1_PER_COEF = NU1_REF / COEF_REF     # GHz per amplitude-%

# AWG waveform time quantum (ns). Pulse starts/lengths and inter-pulse delays
# the hardware plays are multiples of this; snapping to it keeps the simulated
# sequence identical to what the spectrometer would emit (matches the other
# tools). Pass ``time_grid=None`` to build()/layout() to keep raw timing.
TIME_GRID = 3.2


def _snap(x, grid):
    """Round a time to the nearest multiple of ``grid`` (no-op if grid falsy)."""
    if not grid:
        return x
    return round(x / grid) * grid

_SHAPE = {
    'SINE': 'rectangular',
    'MW': 'rectangular',
    'GAUSS': 'gaussian',
    'SINC': 'sinc',
    'WURST': 'WURST',
    'SECH/TANH': 'sech/tanh',
}
_SKIP = ('LASER', 'BLANK')            # not microwave pulses
_PHASE_RAD = {'+x': 0.0, '+y': 0.5 * np.pi, '-x': np.pi, '-y': 1.5 * np.pi}


def _strip_outer(s):
    """Strip one outer bracket layer, matching the GUI ``setter`` ([1:-1])."""
    s = s.strip()
    if len(s) >= 2 and s[0] in '[(' and s[-1] in '])':
        return s[1:-1]
    return s


class Preset:
    """Parsed phasing preset; :meth:`build` it into spin-dynamics events.

    Attributes
    ----------
    kind : str
        ``'awg'`` or ``'rect'``.
    pulses : list of dict
        Active microwave pulses (length != 0, detection and laser/blank
        excluded), in file order. Keys: ``shape, start, length, sigma, freq,
        sweep, coef, phase, st_inc, len_inc, st_inc2`` (RECT lacks the
        frequency/coef fields -> 0).
    detection : dict
        The P1 line: ``start, length, recv, st_inc`` (``recv`` is its raw
        coefficient/phase string).
    globals : dict
        Scalar parameters used by the simulator / axis: ``n_wurst, b_sech,
        freq_obs, sweep_points, x0, dx`` (plus the raw file scalars).
    """

    def __init__(self, kind):
        self.kind = kind
        self.pulses = []
        self.detection = None
        self.globals = {}

    # ------------------------------------------------------------------ #
    def _step_shift(self, step, st_inc, npoints=None):
        """Time shift (ns) of a moving element at sweep index ``step``.

        Linear sweeps shift by ``step * st_inc``. For a ``Sweep Type: Log
        Time`` preset every moving element (``st_inc != 0``) instead shifts by
        the log-spaced delay increment ``T(step) - T(0)`` with
        ``T(i) = 10**(log_start + i*(log_end - log_start)/(n-1))`` ns -- so an
        inversion-recovery / T1 sweep covers decades (e.g. 200 ns -> 10 ms)
        instead of a few linear nanosecond steps. ``npoints`` is the total
        number of sweep points actually being run; it MUST match
        :meth:`sweep_axis` or the log schedule and the x-axis disagree."""
        if st_inc == 0.0:
            return 0.0
        if self.globals.get('sweep_type') == 'log':
            n = int(npoints) if npoints else int(self.globals.get('sweep_points', 0))
            a = self.globals.get('log_start', 0.0)
            b = self.globals.get('log_end', 0.0)
            if n > 1 and b > a:
                return 10.0 ** (a + step * (b - a) / (n - 1)) - 10.0 ** a
        return step * st_inc

    # ------------------------------------------------------------------ #
    def build(self, step=0, nu1_per_coef=NU1_PER_COEF, nu1_rect=NU1_REF,
              flip_cal=None, dt=0.5, resonator=None, detect_dt=1.0, detect=True,
              det_window=None, time_grid=TIME_GRID, npoints=None):
        """Events + phase cycle for one sweep point.

        Parameters
        ----------
        step : int
            Sweep index; pulse ``start``/``length`` and the detection window
            are shifted by ``step * st_inc`` / ``step * len_inc``.
        nu1_per_coef : float
            AWG amplitude-% -> peak nutation (GHz/%). See module docstring.
        nu1_rect : float
            RECT peak nutation (GHz) at full drive (flip set by length).
        flip_cal : (coef, length_ns, flip_rad) or None
            Convenience nutation calibration from one known pulse: "amplitude
            ``coef`` at length ``length_ns`` gives a ``flip_rad`` rotation".
            Sets ``nu1_per_coef = flip_rad/(2*pi*length_ns)/coef`` (AWG) and
            ``nu1_rect = flip_rad/(2*pi*length_ns)`` (RECT), overriding the two
            arguments above. This is the recommended way to pin the one
            hardware-dependent number -- e.g. ``flip_cal=(100, 22.4, pi/2)``
            for a preset whose pi/2 is coef 100 at 22.4 ns. ``coef`` is ignored
            for RECT presets (flip there is set by length at full drive).
        dt : float
            Pulse propagation step (ns) passed to each :class:`spin_dynamics.Pulse`.
        resonator : dict or None
            Applied to every shaped pulse (keys as in
            :func:`pulse_excitation.apply_resonator`). A ``ringdown`` entry
            shortens the following delay so absolute timing is preserved.
        detect_dt : float
            Sample spacing inside the detection window (ns).
        detect : bool
            Append the detection window. False returns only the pulse train
            (e.g. to read ``rho_last`` yourself).
        det_window : (left_ns, right_ns) or None
            Integration-window edges as offsets from the detection pulse's
            *start* (exactly the spectrometer's ``Window left`` / ``Window
            right``). The detected window spans ``[det_start + left, det_start +
            right]``. ``None`` uses the preset's stored ``Window left`` /
            ``Window right`` (falling back to the whole record length).
        time_grid : float or None
            Snap every pulse start/length and the detection start to this
            quantum (ns) -- the AWG time grid (default 3.2 ns), so the
            simulated timing matches what the hardware actually plays. ``None``
            keeps raw timing.

        Returns
        -------
        events : list
            Pulse / Delay / Detect events in time order.
        phase_cycle : list of (shifts, receiver) or None
            Per-step phase shifts (rad, one per active pulse) and receiver
            phase (rad); ``None`` if the preset has no cycling.
        """
        if flip_cal is not None:
            cf, ln, fl = flip_cal
            nu1_rect = fl / (2.0 * np.pi * ln)
            nu1_per_coef = nu1_rect / cf
        active = []
        for p in self.pulses:
            start = p['start'] + self._step_shift(step, p['st_inc'], npoints)
            length = p['length'] + step * p['len_inc']
            if length <= 0:
                continue
            start = _snap(start, time_grid)
            length = _snap(length, time_grid)
            if length <= 0:
                continue
            active.append(dict(p, start=start, length=length))
        active.sort(key=lambda q: q['start'])
        if not active:
            raise ValueError("preset has no active pulses at step %d" % step)

        freq_obs = self.globals.get('freq_obs', 0.0)
        n_wurst = self.globals.get('n_wurst', 10.0)
        b_sech = self.globals.get('b_sech', 0.02)
        ring = float(resonator.get('ringdown', 0.0)) if resonator else 0.0

        events = []
        cursor = active[0]['start']            # t = 0 at the first pulse edge
        pulses_in_order = []                   # for phase-cycle alignment
        for q in active:
            gap = q['start'] - cursor
            if gap > 1e-9:
                events.append(sd.Delay(gap))
            shape = q['shape']
            params = {'center': q['freq'] - freq_obs}
            if shape in ('gaussian', 'sinc'):
                params['sigma'] = q['sigma']
            if shape in ('WURST', 'sech/tanh'):
                params['bw'] = q['sweep']
                params['n'] = n_wurst
                if shape == 'sech/tanh':
                    params['b'] = b_sech
            if self.kind == 'awg':
                nu1 = q['coef'] * nu1_per_coef
            else:
                nu1 = nu1_rect
            pulse = sd.Pulse(shape=shape, tp=q['length'], nu1=nu1, params=params,
                             phase=0.0, dt=dt, resonator=resonator)
            events.append(pulse)
            pulses_in_order.append(q)
            # The engine advances time by the pulse's own duration (length +
            # ring-down); the ring-down eats into the following gap.
            cursor = q['start'] + q['length'] + ring

        if detect and self.detection is not None:
            det_start = _snap(self.detection['start']
                              + self._step_shift(step, self.detection['st_inc'], npoints), time_grid)
            if det_window is not None:
                wl, wr = det_window
            else:
                wl = self.detection.get('win_left', 0.0)
                wr = self.detection.get('win_right', self.detection['length'])
            win_start = det_start + wl
            win_len = max(wr - wl, detect_dt)
            gap = win_start - cursor
            if gap > 1e-9:
                events.append(sd.Delay(gap))
            events.append(sd.Detect(length=win_len, dt=detect_dt))

        phase_cycle = self._phase_cycle(pulses_in_order)
        return events, phase_cycle

    # ------------------------------------------------------------------ #
    def layout(self, step=0, freq_obs=None, det_window=None, time_grid=TIME_GRID,
               npoints=None):
        """Absolute pulse/detection timing for a sweep step (for plotting).

        Returns ``(pulses, detection)`` on the same time axis as :meth:`build`
        (``t = 0`` at the first active pulse's leading edge): ``pulses`` is a
        list of ``{start, length, center, shape, coef}`` dicts (sorted by
        start, ``center`` in MHz relative to the observer) and ``detection`` is
        ``{start, length}`` or ``None``. No spin physics -- just geometry.
        """
        active = []
        for p in self.pulses:
            start = _snap(p['start'] + self._step_shift(step, p['st_inc'], npoints), time_grid)
            length = _snap(p['length'] + step * p['len_inc'], time_grid)
            if length > 0:
                active.append(dict(p, start=start, length=length))
        active.sort(key=lambda q: q['start'])
        if not active:
            return [], None
        t0 = active[0]['start']
        fobs = self.globals.get('freq_obs', 0.0) if freq_obs is None else freq_obs
        pulses = [{'start': q['start'] - t0, 'length': q['length'],
                   'center': q['freq'] - fobs, 'shape': q['shape'],
                   'coef': q['coef']} for q in active]
        det = None
        if self.detection is not None:
            det_start = _snap(self.detection['start']
                              + self._step_shift(step, self.detection['st_inc'], npoints), time_grid) - t0
            if det_window is not None:
                wl, wr = det_window
            else:
                wl = self.detection.get('win_left', 0.0)
                wr = self.detection.get('win_right', self.detection['length'])
            det = {'start': det_start + wl, 'length': max(wr - wl, 0.0)}
        return pulses, det

    # ------------------------------------------------------------------ #
    def _phase_cycle(self, pulses_in_order):
        """Per-step (shifts, receiver) in rad, via the shared expansion."""
        notations = [_strip_outer(q['phase']) for q in pulses_in_order]
        recv_spec = _strip_outer(self.detection['recv']) if self.detection else ''
        exp = coh.expand_phase_cycling(recv_spec, *notations)
        per_pulse = exp['pulses']          # [pulse][step] phase string
        receiver = exp['receiver']         # [step] phase string
        nsteps = len(receiver)
        if nsteps <= 1:
            return None
        cycle = []
        for s in range(nsteps):
            shifts = [_PHASE_RAD[per_pulse[j][s]] for j in range(len(per_pulse))]
            cycle.append((shifts, _PHASE_RAD[receiver[s]]))
        return cycle

    # ------------------------------------------------------------------ #
    def sweep_axis(self, npoints=None):
        """Experiment x-axis (ns): ``x0 + i*dx`` for ``i`` in ``0..npoints-1``.

        ``x0``/``dx`` are the preset's explicit axis (``X0``/``dX`` lines). If
        ``dx == 0`` the step falls back to the first active pulse's ``st_inc``
        (the GUI's auto-axis) and ``x0`` to that pulse's start. ``npoints``
        defaults to the preset's sweep ``Points``.
        """
        n = int(self.globals.get('sweep_points', 0)) if npoints is None else int(npoints)
        if n <= 0:
            n = 1
        if self.globals.get('sweep_type') == 'log':
            a = self.globals.get('log_start', 0.0)
            b = self.globals.get('log_end', 0.0)
            if b > a:
                return 10.0 ** np.linspace(a, b, n)
        x0 = self.globals.get('x0', 0.0)
        dx = self.globals.get('dx', 0.0)
        if dx == 0.0:
            inc = next((p['st_inc'] for p in self.pulses if p['st_inc'] != 0.0), 0.0)
            dx = inc
            if x0 == 0.0 and self.pulses:
                x0 = self.pulses[0]['start']
        return x0 + dx * np.arange(n)


# --------------------------------------------------------------------------- #
def parse_preset(path):
    """Read a ``*.phase_awg`` (AWG) or ``*.phase`` (RECT) preset.

    The kind is taken from the extension; ``*.phase_awg`` -> AWG (11/10-field
    pulse lines), anything else -> RECT (6-field lines).
    """
    with open(path, 'r') as fh:
        text = fh.read()
    kind = 'awg' if str(path).endswith('.phase_awg') else 'rect'
    pre = Preset(kind)

    pulse_lines = {}
    scalars = []                       # (key, value) in file order, for Points x2
    for raw in text.splitlines():
        if ':  ' not in raw:
            continue
        key, val = raw.split(':  ', 1)
        key = key.strip()
        m = re.fullmatch(r'P(\d+)', key)
        if m:
            pulse_lines[int(m.group(1))] = val
        else:
            scalars.append((key, val.strip()))

    sc = {}
    points_seen = []
    for k, v in scalars:
        if k == 'Points':
            points_seen.append(v)
        sc.setdefault(k, v)

    def fnum(key, default=0.0):
        try:
            return float(sc[key])
        except (KeyError, ValueError):
            return default

    # Detection line (P1) and the observer frequency it defines.
    freq_obs = 0.0
    det_fields = None
    if 1 in pulse_lines:
        f = [x.strip() for x in pulse_lines[1].split(',  ')]
        if kind == 'awg':
            freq_obs = float(f[4])
            det_fields = {'start': float(f[1]), 'length': float(f[2]),
                          'recv': f[7], 'st_inc': float(f[8])}
        else:
            det_fields = {'start': float(f[1]), 'length': float(f[2]),
                          'recv': f[3], 'st_inc': float(f[4])}
        # Digitizer integration window (offsets from the detection-pulse start).
        # ``length`` above is only the record length; the echo is integrated
        # over [Window left, Window right]. Older presets omit them -> whole
        # record.
        det_fields['win_left'] = fnum('Window left', 0.0)
        det_fields['win_right'] = fnum('Window right', det_fields['length'])
    pre.detection = det_fields

    for idx in sorted(pulse_lines):
        if idx == 1:
            continue
        f = [x.strip() for x in pulse_lines[idx].split(',  ')]
        typ = f[0].upper()
        if typ in _SKIP or typ not in _SHAPE:
            continue
        if kind == 'awg':
            length = float(f[2])
            if length == 0.0:
                continue
            pre.pulses.append({
                'shape': _SHAPE[typ], 'start': float(f[1]), 'length': length,
                'sigma': float(f[3]), 'freq': float(f[4]), 'sweep': float(f[5]),
                'coef': float(f[6]), 'phase': f[7], 'st_inc': float(f[8]),
                'len_inc': float(f[9]),
                'st_inc2': float(f[10]) if len(f) > 10 else 0.0,
            })
        else:
            length = float(f[2])
            if length == 0.0:
                continue
            pre.pulses.append({
                'shape': _SHAPE[typ], 'start': float(f[1]), 'length': length,
                'sigma': 0.0, 'freq': 0.0, 'sweep': 0.0, 'coef': 0.0,
                'phase': f[3], 'st_inc': float(f[4]), 'len_inc': float(f[5]),
                'st_inc2': 0.0,
            })

    sweep_points = 0.0
    if len(points_seen) >= 2:                  # 2nd "Points" = sweep length
        try:
            sweep_points = float(points_seen[1])
        except ValueError:
            sweep_points = 0.0
    sweep_type = 'log' if 'log' in sc.get('Sweep Type', '').lower() else 'linear'
    pre.globals = {
        'freq_obs': freq_obs,
        'n_wurst': fnum('N WURST; SECH/TANH', 10.0),
        'b_sech': fnum('B SECH/TANH', 0.02),
        'sweep_points': sweep_points,
        'x0': fnum('X0', 0.0),
        'dx': fnum('dX', 0.0),
        'rep_rate': fnum('Rep rate', 0.0),
        'field': fnum('Field', 0.0),
        'sweep_type': sweep_type,
        'log_start': fnum('Log Start', 0.0),
        'log_end': fnum('Log End', 0.0),
    }
    return pre
