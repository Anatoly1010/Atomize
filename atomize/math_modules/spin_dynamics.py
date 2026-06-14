# -*- coding: utf-8 -*-
"""
Density-matrix spin-dynamics engine for pulse EPR.
==================================================

Simulate complete pulse-EPR sequences -- shaped (AWG) or ideal pulses, free
evolution, transient detection windows, phase cycling -- for small coupled
spin systems: an electron with nuclei (ESEEM / HYSCORE modulation), electron
pairs (dipolar experiments), or a bare S = 1/2, where it reproduces the
Bloch module :mod:`pulse_excitation` to machine precision (see the validation
suite). The approach is the standard one of EasySpin's ``saffron`` and of
SPIDYAN: piecewise-constant propagation of the density matrix in Hilbert
space, vectorized over an ensemble of spin packets.

Physics
-------
In the rotating frame of the microwave carrier each ensemble member (a spin
packet at electron resonance offset ``dW`` with B1 scale ``b1``) evolves under

    H(t) = dW * Sz_e  +  H_int  +  b1 * w1(t) * [cos phi(t) Sx_e + sin phi(t) Sy_e]

where ``H_int`` holds the internal couplings (nuclear Zeeman, hyperfine,
quadrupole, electron-electron, ... -- whatever was added to the
:class:`SpinSystem`), ``Sx_e / Sy_e / Sz_e`` are the *total electron* spin
operators (the microwave drives only the electrons), and ``w1(t), phi(t)``
come from the same :func:`pulse_excitation.sampled_waveform` /
:func:`pulse_excitation.apply_resonator` pipeline as the Bloch tool, so
resonator distortion and ring-down are modelled identically.

Propagation is piecewise constant, which is *exact* for an AWG waveform (the
DAC output is itself piecewise constant at its dwell time):

    rho -> U rho U^dag ,   U = exp(-i * 2*pi * dt * H) .

Free evolution runs in the eigenbasis of the static Hamiltonian
``H0 = dW*Sz_e + H_int`` (diagonalized once per ensemble member), so a delay
costs O(dim) phase factors regardless of its length. Phenomenological
relaxation acts there too: coherences damp as ``exp(-tau/Tm)`` and
populations recover towards thermal equilibrium as ``exp(-tau/T1)`` -- exact
while the microwave is off; relaxation *during* pulses is not modelled
(pulses are normally much shorter than Tm).

Units, states, detection
------------------------
GHz and ns throughout, as in :mod:`pulse_excitation` (GHz * ns = cycles).
The density matrix is the traceless high-temperature deviation, initialised
to ``rho0 = Sz_e``. The detected signal is

    V = Tr(rho * S+_e) / Tr(Sz_e^2)        ( == Mx + i*My for a bare S = 1/2 )

i.e. the p = -1 electron coherence, normalised so an ideal pi/2 pulse from
equilibrium gives |V| = 1.

Phase cycling
-------------
The coherence order of a matrix element rho_ab is ``p = m_a - m_b`` (total
electron magnetic quantum numbers); detection picks ``p = -1``. Shifting a
pulse phase by ``dphi`` multiplies every p -> p' transfer amplitude by
``exp(-i*dphi*(p' - p))``. The engine exploits the exact operator identity

    U(phase + dphi) = exp(-i*dphi*Sz_e) U(phase) exp(+i*dphi*Sz_e)

(valid because every electron-only term of H0 is high-field, i.e. enters via
Sz_e), so each pulse propagator is built **once** and a whole phase cycle
costs only diagonal conjugations. A cycle is a list of steps
``(per-pulse phase shifts in rad, receiver phase in rad)``; the detected
signal of each step is multiplied by ``exp(-i*receiver)`` and the steps are
averaged. In the usual +x/+y/-x/-y notation a phase maps to 0, pi/2, pi,
3*pi/2 rad. To keep exactly one pathway with order changes ``dp_i``, set the
receiver of each step to ``-sum_i(dp_i * phi_i)`` and give every pulse enough
phase steps to resolve its ``dp_i`` from the alternatives (an n-step cycle on
a pulse separates dp modulo n). Example -- the 8-step cycle that isolates the
single stimulated-echo pathway (dp = +1, -1, -1) in 3-pulse ESEEM:

    cycle = [([f1, f2, 0], (f2 - f1) % (2*np.pi))
             for f1 in (0, np.pi/2, np.pi, 3*np.pi/2)
             for f2 in (0, np.pi)]

(The textbook 2-step-per-pulse cycle is enough in a *broad-line ensemble*,
where the mirror pathway dp = (-1, +1, -1) dephases on its own; on a single
on-resonance packet only quadrature cycling of the first pulse separates
dp1 = +1 from -1 -- see the validation suite.)

Limitations (by design, for now): single rotating frame (no second microwave
frequency -- a selective DEER pump pulse needs the offset of the B spins
instead), electron high-field approximation for H0 terms involving electrons,
relaxation only between pulses.

References: Stoll & Schweiger, EasySpin ``saffron``; Pribitzer, Doll &
Jeschke, J. Magn. Reson. 263, 45 (2016) (SPIDYAN); Mims, Phys. Rev. B 5,
2409 (1972); Schweiger & Jeschke, *Principles of pulse EPR* (2001), ch. 10.

Validated against the Bloch module, analytic Hahn-echo results and the exact
Mims ESEEM formulas by ``tests/test_spin_dynamics.py`` in this package.

    import atomize.math_modules.spin_dynamics as sd
"""

import numpy as np

import atomize.math_modules.pulse_excitation as pex


# --------------------------------------------------------------------------- #
# Operators
# --------------------------------------------------------------------------- #
def spin_matrices(j):
    """Sx, Sy, Sz for a single spin of quantum number ``j`` (complex (d, d)).

    Basis ordering |j>, |j-1>, ..., |-j>; ``S+ = Sx + i*Sy`` raises m.
    """
    j = float(j)
    d = int(round(2.0 * j)) + 1
    if d < 2 or abs(2.0 * j - round(2.0 * j)) > 1e-9:
        raise ValueError("spin must be a positive half-integer or integer, got %r" % (j,))
    m = j - np.arange(d)
    Sz = np.diag(m).astype(complex)
    amp = np.sqrt(j * (j + 1.0) - m[1:] * (m[1:] + 1.0))   # <m+1|S+|m>
    Sp = np.zeros((d, d), dtype=complex)
    Sp[np.arange(d - 1), np.arange(1, d)] = amp
    Sx = 0.5 * (Sp + Sp.conj().T)
    Sy = -0.5j * (Sp - Sp.conj().T)
    return Sx, Sy, Sz


def _expm_unitary(H, dt):
    """``U = exp(-i * 2*pi * dt * H)`` for Hermitian ``H``, batched (..., d, d).

    d == 2 uses the closed-form SU(2) exponential (the same rotation the Bloch
    module applies via Rodrigues' formula); larger systems go through a batched
    eigendecomposition. Unitary by construction either way.
    """
    d = H.shape[-1]
    if d == 2:
        # H = c0*I + cx*sx + cy*sy + cz*sz (Pauli/2 basis absorbed into angles).
        c0 = 0.5 * (H[..., 0, 0] + H[..., 1, 1]).real
        cz = 0.5 * (H[..., 0, 0] - H[..., 1, 1]).real
        cx = H[..., 0, 1].real
        cy = -H[..., 0, 1].imag
        nrm = np.sqrt(cx * cx + cy * cy + cz * cz)
        ang = 2.0 * np.pi * dt * nrm
        ca, sa = np.cos(ang), np.sin(ang)
        safe = nrm > 1e-15
        f = np.where(safe, sa / np.where(safe, nrm, 1.0), 2.0 * np.pi * dt)
        U = np.empty(H.shape, dtype=complex)
        U[..., 0, 0] = ca - 1j * f * cz
        U[..., 0, 1] = -1j * f * (cx - 1j * cy)
        U[..., 1, 0] = -1j * f * (cx + 1j * cy)
        U[..., 1, 1] = ca + 1j * f * cz
        return np.exp(-2j * np.pi * dt * c0)[..., None, None] * U
    w, V = np.linalg.eigh(H)
    ph = np.exp(-2j * np.pi * dt * w)
    return np.einsum('...ik,...k,...jk->...ij', V, ph, V.conj())


# --------------------------------------------------------------------------- #
# Spin system
# --------------------------------------------------------------------------- #
class SpinSystem:
    """Spin system: quantum numbers, couplings and the operators the engine needs.

    Parameters
    ----------
    spins : sequence of float
        Quantum numbers, e.g. ``(0.5,)`` one electron, ``(0.5, 0.5)`` electron
        plus an I = 1/2 nucleus, ``(0.5, 1.0)`` electron plus N-14.
    electrons : sequence of int
        Indices into ``spins`` that are electrons (microwave-driven and
        detected). Default: spin 0 only.

    All couplings are in GHz. The electron Zeeman offset is *not* part of the
    system -- it is the per-ensemble-member ``offsets`` argument of
    :class:`Engine`, which is what turns the inhomogeneous line into one
    batched array axis.

    Example (electron + one proton, ESEEM)::

        sys = SpinSystem((0.5, 0.5))
        sys.zeeman(1, 0.0149)              # nuclear Larmor (GHz)
        sys.hyperfine(0, 1, A=0.004, B=0.003)
    """

    def __init__(self, spins=(0.5,), electrons=(0,)):
        self.spins = tuple(float(j) for j in spins)
        self.dims = tuple(int(round(2.0 * j)) + 1 for j in self.spins)
        self.dim = int(np.prod(self.dims))
        self.electrons = tuple(int(e) for e in electrons)
        if not self.electrons:
            raise ValueError("at least one electron spin is required")
        for e in self.electrons:
            if not 0 <= e < len(self.spins):
                raise ValueError("electron index %d out of range" % e)
        self.H_int = np.zeros((self.dim, self.dim), dtype=complex)
        self.Sx_e = sum(self.op(e, 'x') for e in self.electrons)
        self.Sy_e = sum(self.op(e, 'y') for e in self.electrons)
        self.Sz_e = sum(self.op(e, 'z') for e in self.electrons)
        self.Sp_e = sum(self.op(e, '+') for e in self.electrons)
        # Detection normalisation: an ideal pi/2 from rho0 = Sz_e gives |V| = 1.
        self.det_norm = float(np.trace(self.Sz_e @ self.Sz_e).real)

    def op(self, k, comp):
        """Operator ``comp`` ('x', 'y', 'z', '+', '-') of spin ``k`` in the product space."""
        Sx, Sy, Sz = spin_matrices(self.spins[k])
        single = {'x': Sx, 'y': Sy, 'z': Sz,
                  '+': Sx + 1j * Sy, '-': Sx - 1j * Sy}[comp]
        out = np.eye(1, dtype=complex)
        for i, d in enumerate(self.dims):
            out = np.kron(out, single if i == k else np.eye(d, dtype=complex))
        return out

    def zeeman(self, k, nu):
        """Add ``nu * Sz_k`` (GHz): a nuclear Larmor term, or a fixed extra
        electron offset (e.g. the second spin of a DEER pair)."""
        self.H_int = self.H_int + nu * self.op(k, 'z')

    def hyperfine(self, e, n, A, B=0.0):
        """Secular + pseudo-secular hyperfine ``A*Sz_e*Iz_n + B*Sz_e*Ix_n`` (GHz).

        The standard high-field ESEEM form; ``B != 0`` is what makes the
        nuclear quantisation axes of the two electron manifolds differ and
        produces echo-envelope modulation."""
        sz = self.op(e, 'z')
        self.H_int = self.H_int + A * (sz @ self.op(n, 'z')) + B * (sz @ self.op(n, 'x'))

    def zz_coupling(self, k1, k2, d):
        """Secular (weak-coupling) ``d * Sz_k1 * Sz_k2`` (GHz) -- e.g. the
        electron-electron dipolar term of a DEER/SIFTER pair."""
        self.H_int = self.H_int + d * (self.op(k1, 'z') @ self.op(k2, 'z'))

    def add_term(self, H):
        """Escape hatch: add an arbitrary Hermitian ``(dim, dim)`` term (GHz),
        e.g. a quadrupole interaction built from :meth:`op` products."""
        H = np.asarray(H, dtype=complex)
        if H.shape != (self.dim, self.dim):
            raise ValueError("term must be (%d, %d)" % (self.dim, self.dim))
        self.H_int = self.H_int + H


# --------------------------------------------------------------------------- #
# Sequence events
# --------------------------------------------------------------------------- #
class Pulse:
    """One microwave pulse event.

    Shaped (default): the same parameters as
    :func:`pulse_excitation.propagate_pulse` -- ``shape``, ``tp`` (ns),
    ``nu1`` (peak nutation, GHz), ``params`` (shape dict, MHz/ns units),
    ``dt`` (propagation step, ns), plus ``phase`` (rad) and an optional
    ``resonator`` dict (keys ``nu0``, ``Q``, ``detuning``, ``mode``,
    ``ringdown``, ``measured`` -- see :func:`pulse_excitation.apply_resonator`).
    A ring-down tail extends the pulse duration accordingly.

    Ideal: pass ``flip=<angle rad>`` (with ``phase``); an instantaneous,
    offset-independent rotation of the electron spins -- B1 scale and
    resonator do not apply, duration 0.

    Treat a Pulse as immutable once an :class:`Engine` has run it: propagators
    are cached per (engine, pulse object) and a later attribute change would
    go unnoticed.
    """

    def __init__(self, shape='rectangular', tp=16.0, nu1=0.0, params=None,
                 phase=0.0, dt=0.5, resonator=None, flip=None):
        self.shape = shape
        self.tp = float(tp)
        self.nu1 = float(nu1)
        self.params = dict(params or {})
        self.phase = float(phase)
        self.dt = float(dt)
        self.resonator = dict(resonator) if resonator else None
        self.flip = None if flip is None else float(flip)


class Delay:
    """Free evolution for ``tau`` ns (with T1/Tm relaxation if enabled)."""

    def __init__(self, tau):
        self.tau = float(tau)


class Detect:
    """Detection window: sample ``V = Tr(rho S+_e)/Tr(Sz_e^2)`` vs time.

    ``length`` ns sampled every ``dt`` ns, i.e. ``round(length/dt) + 1``
    points including both ends; ``length = 0`` (default) is a single point at
    the current sequence time. The density matrix keeps evolving (and
    relaxing) through the window.
    """

    def __init__(self, length=0.0, dt=1.0):
        self.length = float(length)
        self.dt = float(dt)
        if self.dt <= 0:
            raise ValueError("Detect dt must be > 0")


# --------------------------------------------------------------------------- #
# Engine
# --------------------------------------------------------------------------- #
class Engine:
    """Ensemble propagator: spin system + static ensemble, run sequences on it.

    Parameters
    ----------
    system : SpinSystem
    offsets : float or ndarray
        Electron resonance offsets (GHz), one per ensemble member. Use e.g.
        :func:`gaussian_weights` over a dense axis for an inhomogeneous line.
    b1 : float or ndarray
        B1 scale factor per member (broadcast against ``offsets``); models
        B1 inhomogeneity. Applies to shaped pulses only (ideal pulses are
        exact rotations by definition).
    weights : ndarray or None
        Ensemble weights (normalised internally). Default: uniform.
    relaxation : dict or None
        ``{'T1': ns, 'Tm': ns}`` (either optional). Phenomenological, applied
        in the H0 eigenbasis during delays and detection windows only.

    The static Hamiltonian of every member is diagonalized once at
    construction; pulse propagators are cached per Pulse object, so sweeping
    a delay (ESEEM, DEER, ...) and re-calling :meth:`run` on the same Engine
    re-uses all pulse propagators. After :meth:`run`, ``rho_last`` holds the
    final density matrix (of the last phase-cycle step) and :meth:`expect`
    evaluates observables on it.
    """

    def __init__(self, system, offsets=0.0, b1=1.0, weights=None, relaxation=None):
        self.sys = system
        off = np.atleast_1d(np.asarray(offsets, dtype=float))
        b1v = np.atleast_1d(np.asarray(b1, dtype=float))
        off, b1v = np.broadcast_arrays(off, b1v)
        self.offsets = off.copy()
        self.b1 = b1v.copy()
        self.n = self.offsets.size
        if weights is None:
            w = np.full(self.n, 1.0 / self.n)
        else:
            w = np.asarray(weights, dtype=float).astype(float).ravel().copy()
            if w.size != self.n:
                raise ValueError("weights size %d != ensemble size %d" % (w.size, self.n))
            s = w.sum()
            if s != 0:
                w = w / s
        self.weights = w
        relaxation = relaxation or {}
        self.T1 = float(relaxation.get('T1', np.inf))
        self.Tm = float(relaxation.get('Tm', np.inf))
        self._relaxing = np.isfinite(self.T1) or np.isfinite(self.Tm)

        # Static Hamiltonian per member, diagonalized once: delays become
        # O(dim) phase factors and relaxation acts in this eigenbasis.
        self.H0 = system.H_int[None, :, :] + self.offsets[:, None, None] * system.Sz_e[None, :, :]
        self.w0, self.V0 = np.linalg.eigh(self.H0)
        self.V0h = self.V0.conj().swapaxes(-1, -2)
        self.Sp_eig = self.V0h @ system.Sp_e @ self.V0
        self.eq_pop = np.real(np.einsum('nij,jk,nki->ni', self.V0h,
                                        system.Sz_e, self.V0))
        # Sz_e is diagonal in the product basis -> Rz phase shifts are diagonal.
        self.mz_e = np.real(np.diag(system.Sz_e))
        self._ucache = {}
        self.rho_last = None

    # ----------------------------------------------------------------- #
    def run(self, events, phase_cycle=None, keep_members=False):
        """Propagate ``rho0 = Sz_e`` through ``events``, return detections.

        Parameters
        ----------
        events : sequence of Pulse / Delay / Detect
        phase_cycle : list of (shifts, receiver) or None
            Each step: ``shifts`` = extra phase (rad) per Pulse in sequence
            order (or None for no shift), ``receiver`` = receiver phase (rad).
            Step signals are multiplied by ``exp(-i*receiver)`` and averaged.
        keep_members : bool
            Also return the per-member signals (key ``'vm'``, shape (N, nt)).

        Returns
        -------
        list of dict, one per Detect event, in sequence order:
        ``{'t': absolute times (ns), 'v': ensemble-averaged complex signal}``
        (plus ``'vm'`` if requested). ``self.rho_last`` is set to the final
        density matrix of the last cycle step (N, dim, dim).
        """
        npulse = sum(1 for ev in events if isinstance(ev, Pulse))
        cycle = list(phase_cycle) if phase_cycle else [(None, 0.0)]
        for shifts, _ in cycle:
            if shifts is not None and len(shifts) < npulse:
                raise ValueError("phase-cycle step has %d shifts for %d pulses"
                                 % (len(shifts), npulse))
        acc_t, acc_v = None, None
        rho = None
        for shifts, recv in cycle:
            rho = np.tile(self.sys.Sz_e, (self.n, 1, 1))
            t = 0.0
            ip = 0
            wins = []
            for ev in events:
                if isinstance(ev, Pulse):
                    U, dur = self._propagator(ev)
                    if shifts is not None and shifts[ip] != 0.0:
                        rz = np.exp(-1j * float(shifts[ip]) * self.mz_e)
                        U = U * (rz[:, None] * rz.conj()[None, :])
                    rho = U @ rho @ U.conj().swapaxes(-1, -2)
                    t += dur
                    ip += 1
                elif isinstance(ev, Delay):
                    rho = self._free(rho, ev.tau)
                    t += ev.tau
                elif isinstance(ev, Detect):
                    rho, times, sig = self._detect(rho, ev, t)
                    t = float(times[-1])
                    wins.append((times, sig))
                else:
                    raise TypeError("unknown sequence event: %r" % (ev,))
            scale = np.exp(-1j * float(recv)) / len(cycle)
            if acc_v is None:
                acc_t = [w[0] for w in wins]
                acc_v = [w[1] * scale for w in wins]
            else:
                for k, w in enumerate(wins):
                    acc_v[k] = acc_v[k] + w[1] * scale
        self.rho_last = rho
        out = []
        for tt, vm in zip(acc_t, acc_v):
            rec = {'t': tt, 'v': np.einsum('n,nt->t', self.weights, vm)}
            if keep_members:
                rec['vm'] = vm
            out.append(rec)
        return out

    def expect(self, op, rho=None):
        """``Tr(rho op)`` per ensemble member, shape (N,) complex.

        ``rho`` defaults to ``rho_last`` (the state after the last
        :meth:`run`). E.g. Bloch components of a bare S = 1/2:
        ``Mz = 2 * eng.expect(sys.op(0, 'z')).real``.
        """
        rho = self.rho_last if rho is None else rho
        return np.einsum('nij,ji->n', rho, np.asarray(op, dtype=complex))

    # ----------------------------------------------------------------- #
    def _propagator(self, p):
        """(Cached) total propagator of a Pulse: (N, d, d) or (1, d, d), and
        its duration in ns (0 for ideal pulses, tp + ring-down for shaped)."""
        key = id(p)
        if key in self._ucache:
            return self._ucache[key][1:]
        s = self.sys
        if p.flip is not None:
            G = p.flip * (np.cos(p.phase) * s.Sx_e + np.sin(p.phase) * s.Sy_e)
            w, V = np.linalg.eigh(G)
            U = ((V * np.exp(-1j * w)[None, :]) @ V.conj().T)[None, :, :]
            dur = 0.0
        else:
            steps, _, a, _, phi = pex.sampled_waveform(
                p.shape, p.tp, p.params, dt=p.dt, phi0=p.phase)
            if p.resonator is not None:
                wv = pex.apply_resonator(a * np.exp(1j * phi), p.dt, **p.resonator)
                a = np.abs(wv)
                phi = np.angle(wv)
                if a.size > steps.size:        # extra dt steps for the ring-down
                    steps = np.concatenate((steps, np.full(a.size - steps.size, p.dt)))
            amp = self.b1 * p.nu1                          # (N,) per-member drive
            bx = a * np.cos(phi)
            by = a * np.sin(phi)
            U = np.tile(np.eye(s.dim, dtype=complex), (self.n, 1, 1))
            for k in range(steps.size):
                Hk = self.H0 + amp[:, None, None] * (bx[k] * s.Sx_e + by[k] * s.Sy_e)[None, :, :]
                U = _expm_unitary(Hk, steps[k]) @ U
            dur = float(np.sum(steps))
        # Keep a reference to the Pulse itself: id() values are reused after
        # garbage collection, so the cache must pin the object alive.
        self._ucache[key] = (p, U, dur)
        return U, dur

    def _free(self, rho, tau):
        """Free evolution (+ relaxation) for tau ns via the H0 eigenbasis."""
        if tau <= 0:
            return rho
        r = self.V0h @ rho @ self.V0
        ph = np.exp(-2j * np.pi * self.w0 * tau)
        r = r * (ph[:, :, None] * ph.conj()[:, None, :])
        if self._relaxing:
            r = self._relax(r, tau)
        return self.V0 @ r @ self.V0h

    def _relax(self, r, tau):
        """Phenomenological relaxation; ``r`` MUST be in the H0 eigenbasis.

        Coherences damp with Tm; populations (diagonal) recover towards the
        thermal equilibrium populations with T1 and never see Tm.
        """
        idx = np.arange(r.shape[-1])
        pops = r[:, idx, idx]
        r = r * (np.exp(-tau / self.Tm) if np.isfinite(self.Tm) else 1.0)
        if np.isfinite(self.T1):
            pops = self.eq_pop + (pops - self.eq_pop) * np.exp(-tau / self.T1)
        r[:, idx, idx] = pops               # r is a fresh array (the product above)
        return r

    def _detect(self, rho, ev, t0):
        """Sample the detection window; returns (rho_after, times, sig (N, nt))."""
        n = 1 if ev.length <= 0 else int(round(ev.length / ev.dt)) + 1
        r = self.V0h @ rho @ self.V0
        sig = np.empty((self.n, n), dtype=complex)
        if n > 1:
            ph = np.exp(-2j * np.pi * self.w0 * ev.dt)
            P = ph[:, :, None] * ph.conj()[:, None, :]
        for k in range(n):
            sig[:, k] = np.einsum('nij,nji->n', r, self.Sp_eig) / self.sys.det_norm
            if k < n - 1:
                r = r * P
                if self._relaxing:
                    r = self._relax(r, ev.dt)
        rho = self.V0 @ r @ self.V0h
        times = t0 + ev.dt * np.arange(n)
        return rho, times, sig


# --------------------------------------------------------------------------- #
# Conveniences
# --------------------------------------------------------------------------- #
def run(system, events, offsets=0.0, b1=1.0, weights=None, relaxation=None,
        phase_cycle=None, keep_members=False):
    """One-shot wrapper: build an :class:`Engine` and :meth:`Engine.run` it.

    For sweeps (ESEEM tau/T axes, DEER traces, ...) build the Engine once and
    call ``run`` per sweep point instead -- the static eigenbasis and all
    pulse propagators are then computed only once.
    """
    eng = Engine(system, offsets=offsets, b1=b1, weights=weights,
                 relaxation=relaxation)
    return eng.run(events, phase_cycle=phase_cycle, keep_members=keep_members)


def gaussian_weights(offsets, sigma, center=0.0):
    """Normalised Gaussian ensemble weights over an offset axis (GHz).

    The discrete stand-in for an inhomogeneous (Gaussian) EPR line; a measured
    spectral lineshape resampled onto the offset axis works the same way."""
    x = (np.asarray(offsets, dtype=float) - center) / float(sigma)
    w = np.exp(-0.5 * x * x)
    return w / np.sum(w)


def lorentzian_weights(offsets, gamma, center=0.0):
    """Normalised Lorentzian ensemble weights (``gamma`` = HWHM, GHz)."""
    x = (np.asarray(offsets, dtype=float) - center) / float(gamma)
    w = 1.0 / (1.0 + x * x)
    return w / np.sum(w)
