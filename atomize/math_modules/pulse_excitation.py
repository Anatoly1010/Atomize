# -*- coding: utf-8 -*-
"""
Excitation / inversion profiles of shaped EPR pulses.
=====================================================

Compute how, and with what phase, a shaped microwave pulse acts on spins across
a range of resonance offsets. The approach is the standard EasySpin one
(numerical spin-dynamics propagation, valid for adiabatic pulses, not just the
linear-response/FFT approximation):

A single S = 1/2 spin in the rotating frame of the microwave carrier sees

    H(t) = dW * Sz  +  w1(t) * [ cos phi(t) * Sx + sin phi(t) * Sy ]

with dW the resonance offset (carrier - Larmor), w1(t) = 2*pi*nu1*a(t) the
instantaneous nutation (B1) drive and phi(t) the running RF phase. The pulse is
propagated piecewise-constant: over each short step dt the Hamiltonian is held
at its mid-step value and the density matrix evolves as

    rho -> U rho U^dag ,   U = exp(-i * 2*pi * dt * H) .

For a two-level system this 2x2 propagator is an SU(2) rotation, so instead of a
matrix exponential per (offset, step) we rotate the Bloch vector M = (Mx,My,Mz)
directly with Rodrigues' formula. exp(-i*theta*(n.S)) acts on the Bloch vector as
a right-handed rotation by +theta about n, which lets the *whole* offset axis be
propagated at once as NumPy array ops — the entire profile of a microsecond WURST
pulse computes in well under a tenth of a second.

Units
-----
Internally everything is in **GHz** (frequencies) and **ns** (time); a product
GHz*ns is a number of cycles, so the rotation angle of a step is simply
``2*pi * dt * Omega_eff``. Frequency arguments and the offset axis are GHz, times
are ns. (Callers that prefer MHz convert on the way in.)

Reference: Doll & Jeschke, https://doi.org/10.5194/mr-1-59-2020 (WURST/chirp);
Stoll & Schweiger, EasySpin (``pulse`` / ``exciteprofile``).
"""

import numpy as np

# AWG sample rate (samples / ns). The shaped-pulse formulas are built on a sample
# grid, as a typical arbitrary-waveform generator does; this is the only place
# that grid leaks into the continuous form (the sech/tanh envelope/sweep arguments
# are defined in samples, so they scale with the sample rate). 1.25 = 1250 MHz.
SAMPLE_RATE = 1.25

# Pulse shapes this module understands. Parameters follow the common AWG
# convention:
#   sigma  : Gaussian/sinc width in ns (NOT FWHM)
#   n      : WURST exponent / sech-tanh order (HSn)
#   b      : sech/tanh truncation (1/ns)
#   bw     : frequency sweep width in MHz (WURST/sech)
#   center : carrier frequency in MHz (rect/gaussian/sinc: the carrier; WURST/sech:
#            the sweep centre).
SHAPES = (
    'rectangular',   # center
    'gaussian',      # sigma (ns), center
    'sinc',          # sigma (ns), center
    'half-sine',     # center
    'quartersine',   # edge (ns), center
    'WURST',         # n, bw (MHz), center
    'sech/tanh',     # b, n, bw (MHz), center
)


def waveform(shape, t, tp, params):
    """Amplitude envelope and instantaneous frequency of a pulse shape.

    The shaped-pulse formulas follow the AWG sample-grid convention, so a pulse
    designed here reproduces the one an arbitrary-waveform generator emits.

    Parameters
    ----------
    shape : str
        One of :data:`SHAPES`.
    t : ndarray
        Times (ns), expected within ``[0, tp]``.
    tp : float
        Pulse length (ns).
    params : dict
        Shape-specific parameters (see :data:`SHAPES`). Widths in ns, frequencies
        in MHz, ``b`` in 1/ns.

    Returns
    -------
    a : ndarray
        Amplitude envelope, peak 1 (may go negative for sinc side-lobes).
    nu : ndarray
        Instantaneous frequency (GHz) relative to the reference.
    """
    t = np.asarray(t, dtype=float)
    tau = t - 0.5 * tp                  # time from pulse centre (ns)
    center = float(params.get('center', 0.0)) / 1000.0      # MHz -> GHz

    if shape == 'rectangular':          # constant envelope (SINE carrier)
        a = np.ones_like(t)
        nu = np.full_like(t, center)

    elif shape == 'gaussian':           # exp(-0.5 ((t-tp/2)/sigma)^2)
        sigma = max(float(params.get('sigma', 0.25 * tp)), 1e-9)
        a = np.exp(-0.5 * (tau / sigma) ** 2)
        nu = np.full_like(t, center)

    elif shape == 'sinc':               # sinc(2 (t-tp/2)/sigma)
        sigma = max(float(params.get('sigma', 0.25 * tp)), 1e-9)
        a = np.sinc(2.0 * tau / sigma)  # np.sinc(u) = sin(pi u)/(pi u)
        nu = np.full_like(t, center)

    elif shape == 'half-sine':          # extra
        a = np.sin(np.pi * t / tp)
        nu = np.full_like(t, center)

    elif shape == 'quartersine':        # extra: flat top, quarter-sine edges
        edge = max(float(params.get('edge', 0.1 * tp)), 1e-9)
        a = np.ones_like(t)
        rise = t < edge
        fall = t > (tp - edge)
        a[rise] = np.sin(0.5 * np.pi * t[rise] / edge)
        a[fall] = np.sin(0.5 * np.pi * (tp - t[fall]) / edge)
        nu = np.full_like(t, center)

    elif shape == 'WURST':
        n = float(params.get('n', 20.0))
        bw = float(params.get('bw', 100.0)) / 1000.0        # MHz -> GHz
        a = 1.0 - np.abs(np.sin(np.pi * tau / tp)) ** n
        nu = center + bw * tau / tp                          # linear sweep across bw

    elif shape == 'sech/tanh':          # HSn (hyperbolic-secant) adiabatic
        # Defined on the sample grid exactly as the AWG buffer:
        #   env_arg = b * x_mean * 2^(n-1) * (|dx|/length)^n
        #   envelope = sech(env_arg)
        #   nu = center + sweep * tanh(b dx) / (2 tanh(b x_mean))
        b = float(params.get('b', 0.02))
        n = float(params.get('n', 1.0))
        bw = float(params.get('bw', 100.0)) / 1000.0         # MHz -> GHz (= sweep)
        x_mean_s = 0.5 * tp * SAMPLE_RATE                    # half-length in samples
        dx_s = tau * SAMPLE_RATE                             # samples from centre
        env_arg = b * x_mean_s * 2.0 ** (n - 1.0) * (np.abs(dx_s) / (tp * SAMPLE_RATE)) ** n
        a = 1.0 / np.cosh(env_arg)
        nu = center + bw * np.tanh(b * dx_s) / (2.0 * np.tanh(b * x_mean_s))

    else:
        raise ValueError("unknown pulse shape: %r" % (shape,))

    return a, nu


def sampled_waveform(shape, tp, params, dt=0.5, phi0=0.0):
    """Mid-step sampled envelope, frequency and running phase of a pulse.

    The shared discretization behind :func:`propagate_pulse` and
    :func:`adiabaticity_profile` (and the density-matrix engine in
    :mod:`spin_dynamics`): the pulse is chopped into ``dt`` steps, the
    waveform is sampled at the step midpoints, and the running RF phase
    ``phi(t) = phi0 + 2*pi * integral(nu dt')`` is accumulated by the
    trapezoid rule on that grid. For amplitude-only shapes ``nu == center``
    so ``phi`` is linear. Each pulse's phase is referenced to its own start
    (standard AWG convention).

    Returns
    -------
    steps : ndarray
        Per-step durations (ns); ``steps.sum() == tp`` up to grid rounding.
    tmid : ndarray
        Mid-step times (ns).
    a : ndarray
        Amplitude envelope at ``tmid`` (peak 1).
    nu : ndarray
        Instantaneous frequency at ``tmid`` (GHz, relative to the carrier).
    phi : ndarray
        Running RF phase at ``tmid`` (rad).
    """
    edges = np.arange(0.0, tp + 0.5 * dt, dt)
    if edges.size < 2:
        edges = np.array([0.0, tp])
    tmid = 0.5 * (edges[:-1] + edges[1:])
    steps = np.diff(edges)                       # per-step durations (ns)
    a, nu = waveform(shape, tmid, tp, params)
    phi = phi0 + 2.0 * np.pi * (np.cumsum(nu * steps) - 0.5 * nu * steps)
    return steps, tmid, a, nu, phi


def resonator_transfer(freqs, nu0, Q, detuning=0.0):
    """Complex voltage transfer function of an ideal (lumped RLC) resonator.

        H(nu) = 1 / (1 + i Q (nu/nu0 - nu0/nu))

    with ``nu`` the *absolute* microwave frequency. A rotating-frame component at
    ``f`` (relative to the carrier) sits at ``nu = nu0 - detuning + f``, where
    ``detuning = nu_resonator - nu_carrier`` — so ``detuning = 0`` means the
    carrier is tuned to the resonator centre and ``|H|`` peaks at ``f = 0``.

    Parameters
    ----------
    freqs : ndarray
        Rotating-frame frequencies (GHz), e.g. ``np.fft.fftfreq(n, dt)``.
    nu0 : float
        Resonator centre frequency (GHz, absolute).
    Q : float
        Loaded quality factor. The power bandwidth (FWHM) is ``nu0 / Q``.
    detuning : float
        Resonator centre minus carrier (GHz). Default 0 (carrier on resonance).

    Returns
    -------
    ndarray (complex)
        ``H`` at each frequency; ``|H| = 1`` exactly at the resonator centre.
    """
    nu = nu0 - detuning + np.asarray(freqs, dtype=float)
    nu = np.where(np.abs(nu) < 1e-12, 1e-12, nu)   # guard the nu->0 pole
    x = nu / nu0
    return 1.0 / (1.0 + 1j * Q * (x - 1.0 / x))


def measured_transfer(freqs, freq_meas, H_meas, carrier):
    """Measured complex transfer function interpolated onto rotating-frame freqs.

    Use this instead of :func:`resonator_transfer` when a *measured* resonator
    response (e.g. a VNA S21 sweep) is available, so the real, non-Lorentzian
    magnitude ripple and phase are modelled rather than an ideal RLC.

    Parameters
    ----------
    freqs : ndarray
        Rotating-frame frequencies (GHz), e.g. ``np.fft.fftfreq(n, dt)``.
    freq_meas : ndarray
        Absolute microwave frequency (GHz) of the measurement points.
    H_meas : ndarray (complex)
        Measured complex transfer at each ``freq_meas`` (e.g. S21).
    carrier : float
        Carrier frequency (GHz): a rotating-frame component at ``f`` maps to the
        absolute frequency ``nu = carrier + f``.

    Returns
    -------
    ndarray (complex)
        ``H`` interpolated onto ``freqs``, normalised to **unit peak magnitude**
        and **zero phase at the carrier** (the same convention as
        :func:`resonator_transfer`: ``|H| = 1`` at centre, phase referenced to the
        pulse start), so only the relative across-band distortion is applied.
        Magnitude and *unwrapped* phase are interpolated separately (a linear
        interp of the raw complex values would chord across phase wraps).
        Out-of-band frequencies clamp to the nearest measured point.
    """
    fm = np.asarray(freq_meas, dtype=float)
    Hm = np.asarray(H_meas, dtype=complex)
    order = np.argsort(fm)
    fm, Hm = fm[order], Hm[order]
    mag_m = np.abs(Hm)
    ph_m = np.unwrap(np.angle(Hm))
    nu = carrier + np.asarray(freqs, dtype=float)
    mag = np.interp(nu, fm, mag_m)
    ph = np.interp(nu, fm, ph_m)
    H = mag * np.exp(1j * ph)
    peak = np.max(mag_m)
    if peak > 0:
        H = H / peak
    ph0 = np.interp(carrier, fm, ph_m)        # reference phase to the carrier
    return H * np.exp(-1j * ph0)


def ringdown_time(nu0, Q):
    """Resonator amplitude ring-down time constant (ns): ``tau = Q / (pi nu0)``.

    The stored field decays as ``exp(-t/tau)``; a window of ~5 tau captures the
    ring-down to ~1%. With ``nu0`` in GHz the result is in ns.
    """
    return Q / (np.pi * nu0)


def apply_resonator(w, dt, nu0, Q, detuning=0.0, mode='simulate', max_gain=10.0,
                    ringdown=0.0, measured=None):
    """Filter a complex baseband waveform through the resonator transfer fn.

    ``w`` is the sampled complex envelope ``a(t) exp(i phi(t))`` on a uniform
    ``dt`` (ns) grid. The waveform is zero-padded before the FFT so the filtering
    is a *linear* (not circular) convolution — this stops a rectangular pulse's
    leading edge from wrapping its ring-up onto its trailing edge.

    Parameters
    ----------
    w : ndarray (complex)
        Programmed complex waveform, one sample per ``dt``.
    dt : float
        Sample spacing (ns) — must match how ``w`` was sampled.
    nu0, Q, detuning
        Resonator parameters, see :func:`resonator_transfer`.
    mode : str
        ``'simulate'``  — multiply by ``H``: what the spins see when the pulse is
        sent *uncorrected* (the resonator distorts amplitude and phase).
        ``'compensate'`` — multiply by ``1/H``: the pre-distortion needed so the
        spins see the ideal pulse. The boost is capped at ``max_gain`` since
        ``1/H`` diverges far off resonance.
    max_gain : float
        Maximum ``|1/H|`` allowed in compensate mode.
    ringdown : float
        If > 0 (and ``mode == 'simulate'``), append this many ns of post-pulse
        ring-down: the resonator keeps emitting after the drive stops, so
        ``ringdown/dt`` extra samples (driven by zero input) are returned. The
        spins keep nutating under this decaying field. Ignored in compensate mode.
    measured : (ndarray, ndarray) or None
        Optional ``(freq_meas_GHz, H_meas_complex)`` measured transfer function. If
        given, ``H`` is built from it via :func:`measured_transfer` (carrier taken
        as ``nu0 - detuning``) instead of the ideal RLC ``resonator_transfer`` —
        ``nu0``/``Q`` then only set the carrier reference and the ring-down clock.

    Returns
    -------
    ndarray (complex)
        Distorted complex waveform. Length ``len(w)`` normally, or
        ``len(w) + round(ringdown/dt)`` when a ring-down tail is appended.
    """
    w = np.asarray(w, dtype=complex)
    n = w.size
    if n < 2:
        return w
    n_rd = int(round(max(0.0, ringdown) / dt)) if mode == 'simulate' else 0
    n_tot = n + n_rd
    m = 1
    while m < 2 * n_tot:                            # next pow2 >= 2*n_tot: linear conv
        m *= 2
    W = np.zeros(m, dtype=complex)
    W[:n] = w                                       # drive is zero during ring-down
    freqs = np.fft.fftfreq(m, d=dt)                 # GHz
    if measured is not None:
        H = measured_transfer(freqs, measured[0], measured[1], nu0 - detuning)
    else:
        H = resonator_transfer(freqs, nu0, Q, detuning)
    if mode == 'compensate':
        G = 1.0 / H
        mag = np.abs(G)
        big = mag > max_gain
        G[big] = G[big] / mag[big] * max_gain       # cap the boost, keep phase
    else:
        G = H
    return np.fft.ifft(np.fft.fft(W) * G)[:n_tot]


def propagate_pulse(M, shape, tp, nu1, offsets, params, dt=0.5, phi0=0.0,
                    resonator=None):
    """Apply one shaped pulse to a Bloch-vector array, return the new array.

    The workhorse: piecewise-constant SU(2)/Rodrigues propagation of every
    offset's Bloch vector through the pulse. :func:`excitation_profile` wraps
    this for a single pulse from equilibrium; chaining it with
    :func:`free_evolution` builds multi-pulse sequences.

    Parameters
    ----------
    M : ndarray
        Incoming magnetization, shape ``(len(offsets), 3)`` — modified copy
        returned (the input is not mutated).
    shape, tp, nu1, params, dt, phi0
        As in :func:`excitation_profile`.
    offsets : ndarray
        Resonance offsets (GHz).
    resonator : dict or None
        If given, the programmed waveform is filtered through the resonator
        before the spins see it (keys: ``nu0``, ``Q``, ``detuning``, ``mode`` —
        see :func:`apply_resonator`). ``None`` = ideal transmitter.

    Returns
    -------
    ndarray
        Outgoing magnetization, shape ``(len(offsets), 3)``.
    """
    offsets = np.asarray(offsets, dtype=float)
    M = np.array(M, dtype=float, copy=True)

    steps, tmid, a, nu, phi = sampled_waveform(shape, tp, params, dt=dt, phi0=phi0)

    # Optional resonator: filter the complex envelope a*exp(i phi) through the
    # transfer function, then read back the distorted amplitude/phase the spins
    # actually see (mid-step grid is uniform at dt, so it is a valid FFT axis).
    # A ring-down tail (resonator['ringdown'] ns) lengthens the waveform; the
    # spins keep nutating under the decaying field, so the step grid grows too.
    if resonator is not None:
        w = apply_resonator(a * np.exp(1j * phi), dt, **resonator)
        a = np.abs(w)
        phi = np.angle(w)
        if a.size > steps.size:                  # extra dt steps for the ring-down
            steps = np.concatenate((steps, np.full(a.size - steps.size, dt)))

    # Effective-field components (GHz). bx, by are common to all offsets; bz is
    # the offset itself (constant in time, varies across the axis).
    bx = nu1 * a * np.cos(phi)
    by = nu1 * a * np.sin(phi)

    bz = offsets                                 # (N,)
    for k in range(steps.size):
        # Effective field for this step at every offset: (N, 3).
        vx = np.full_like(bz, bx[k])
        vy = np.full_like(bz, by[k])
        vz = bz
        norm = np.sqrt(vx * vx + vy * vy + vz * vz)
        theta = 2.0 * np.pi * steps[k] * norm    # rotation angle this step (rad)

        safe = norm > 1e-15
        inv = np.where(safe, 1.0 / np.where(safe, norm, 1.0), 0.0)
        nx, ny, nz = vx * inv, vy * inv, vz * inv

        c = np.cos(theta)
        s = np.sin(theta)
        Mx, My, Mz = M[:, 0], M[:, 1], M[:, 2]

        # Rodrigues: M' = M c + (n x M) s + n (n.M)(1 - c)  — right-handed by +theta.
        dot = nx * Mx + ny * My + nz * Mz
        cx = ny * Mz - nz * My
        cy = nz * Mx - nx * Mz
        cz = nx * My - ny * Mx
        omc = 1.0 - c
        M = np.stack((
            Mx * c + cx * s + nx * dot * omc,
            My * c + cy * s + ny * dot * omc,
            Mz * c + cz * s + nz * dot * omc,
        ), axis=1)

    return M


def free_evolution(M, offsets, tau):
    """Free precession for time ``tau`` (ns): rotate each offset about +z.

    Same sign convention as :func:`propagate_pulse` with nu1 = 0 (a spin at
    offset ``dW`` accumulates phase ``2*pi*dW*tau``). Returns a modified copy.
    """
    M = np.array(M, dtype=float, copy=True)
    theta = 2.0 * np.pi * np.asarray(offsets, dtype=float) * tau
    c, s = np.cos(theta), np.sin(theta)
    Mx, My = M[:, 0].copy(), M[:, 1].copy()
    M[:, 0] = Mx * c - My * s
    M[:, 1] = Mx * s + My * c
    return M


def excitation_profile(shape, tp, nu1, offsets, params,
                       dt=0.5, phi0=0.0, init=(0.0, 0.0, 1.0), resonator=None):
    """Bloch-vector excitation profile of a single pulse over an offset axis.

    Parameters
    ----------
    shape : str
        Pulse shape, one of :data:`SHAPES`.
    tp : float
        Pulse length (ns).
    nu1 : float
        Peak nutation (B1) frequency (GHz). For a rectangular pulse the
        on-resonance flip angle is ``2*pi*nu1*tp``.
    offsets : ndarray
        Resonance offsets (GHz) to evaluate.
    params : dict
        Shape-specific parameters (MHz units), see :func:`waveform`.
    dt : float
        Propagation time step (ns). Smaller = more accurate / slower.
    phi0 : float
        Constant phase added to the RF (rad) — the pulse phase (x/y/...).
    init : tuple
        Initial magnetization (Mx, My, Mz). Default +z (equilibrium).

    Returns
    -------
    Mx, My, Mz : ndarray
        Final magnetization components for every offset. ``Mz`` is the inversion
        profile; ``hypot(Mx, My)`` is the in-phase/transverse excitation.
    """
    offsets = np.asarray(offsets, dtype=float)
    M = np.tile(np.asarray(init, dtype=float), (offsets.size, 1))
    M = propagate_pulse(M, shape, tp, nu1, offsets, params, dt=dt, phi0=phi0,
                        resonator=resonator)
    return M[:, 0], M[:, 1], M[:, 2]


def flip_angle(shape, tp, nu1, params, dt=0.5):
    """On-resonance flip angle (rad) of the pulse — integral of the envelope.

    Exact for non-frequency-swept shapes; for chirp/adiabatic pulses it is just
    the nominal area and not the effective rotation (which is offset-dependent).
    """
    edges = np.arange(0.0, tp + 0.5 * dt, dt)
    if edges.size < 2:
        edges = np.array([0.0, tp])
    tmid = 0.5 * (edges[:-1] + edges[1:])
    steps = np.diff(edges)
    a, _ = waveform(shape, tmid, tp, params)
    return 2.0 * np.pi * nu1 * float(np.sum(a * steps))


def adiabaticity_profile(shape, tp, nu1, offsets, params, dt=0.5, phi0=0.0,
                         resonator=None):
    """Adiabaticity factor Q_crit(offset) of a frequency-swept pulse.

    In the frame following the instantaneous RF frequency a spin at resonance
    offset ``dW`` sees an effective field with transverse component
    ``w1(t) = 2*pi*nu1*a(t)`` and longitudinal component
    ``dOmega(t) = 2*pi*(dW - nu_inst(t))``, where ``nu_inst = (1/2pi) dphi/dt`` is
    the instantaneous pulse frequency. Adiabatic passage requires the effective
    field to reorient slowly compared with its own magnitude:

        Q(t) = |Omega_eff(t)| / |d(alpha)/dt| ,   alpha = atan2(w1, dOmega)

    and ``Q`` evaluated at the spin's resonance crossing (where ``dOmega = 0`` and
    the field tips through the transverse plane) decides whether the spin is
    inverted. ``Q_crit >> 1`` (rule of thumb >~ 5) means adiabatic. This is the
    Garwood-DelaBarre / Doll-Jeschke adiabaticity parameter and is only
    meaningful for swept pulses (WURST, sech/tanh); for amplitude-only shapes it
    just reflects the envelope ramp.

    Parameters mirror :func:`propagate_pulse`. ``resonator`` (dict or None) is
    applied to the waveform first, so a *compensated* pulse can be compared with
    a *simulated* (distorted) one to see whether the AWG pre-distortion restores
    adiabaticity across the band. Returns ``Q_crit`` for every offset (the same
    shape as ``offsets``).
    """
    offsets = np.asarray(offsets, dtype=float)
    steps, tmid, a, nu, phi = sampled_waveform(shape, tp, params, dt=dt, phi0=phi0)

    # The resonator is a filter: it cannot move the frequency sweep, only
    # attenuate the amplitude (and add phase). Its effect on adiabaticity is the
    # amplitude roll-off at the band edges, so take the filtered amplitude
    # a = |w| but keep the *programmed* sweep nu(t) as the instantaneous
    # frequency. Differentiating the filtered phase instead is numerically
    # unstable wherever |w| -> 0 (envelope edges, resonator nulls, ring-down) and
    # peppered the Q profile with spurious spikes once the resonator was on.
    if resonator is not None:
        w = apply_resonator(a * np.exp(1j * phi), dt, **resonator)
        a = np.abs(w)
        if a.size > steps.size:                           # ring-down tail
            extra = a.size - steps.size
            steps = np.concatenate((steps, np.full(extra, dt)))
            nu = np.concatenate((nu, np.full(extra, nu[-1])))   # decays at last freq

    # Mid-step time grid for the angle derivative (ns).
    t = np.cumsum(steps) - 0.5 * steps
    if t.size < 3:
        return np.full(offsets.shape, np.inf)

    w1 = np.abs(nu1) * np.abs(a)                          # transverse drive (GHz)
    dOmega = offsets[:, None] - nu[None, :]               # (Noff, Nt) GHz
    Omega = np.hypot(w1[None, :], dOmega)                 # |B_eff| (GHz)
    alpha = np.arctan2(w1[None, :], dOmega)               # angle from z (rad)
    dalpha = np.gradient(alpha, t, axis=1)                # rad/ns
    # Q = 2*pi*|Omega| / |dalpha/dt|  (both numerator and denom are rad/ns).
    Q = 2.0 * np.pi * Omega / np.maximum(np.abs(dalpha), 1e-12)
    # Evaluate Q at each spin's resonance crossing — the instant the instantaneous
    # frequency sweeps through the spin (|dOmega| minimal), where the effective
    # field tips through the transverse plane and adiabaticity is hardest to keep.
    # (The global min over time would just pick the trivial zero-field envelope
    # edges.) Spins never swept through (|dOmega| never small) get a large Q and
    # are simply not inverted, which is correct.
    kstar = np.argmin(np.abs(dOmega), axis=1)
    return Q[np.arange(offsets.size), kstar]
