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


def propagate_pulse(M, shape, tp, nu1, offsets, params, dt=0.5, phi0=0.0):
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

    Returns
    -------
    ndarray
        Outgoing magnetization, shape ``(len(offsets), 3)``.
    """
    offsets = np.asarray(offsets, dtype=float)
    M = np.array(M, dtype=float, copy=True)

    # Mid-step sampling of the waveform (matches the notebook's mid-point rule).
    edges = np.arange(0.0, tp + 0.5 * dt, dt)
    if edges.size < 2:
        edges = np.array([0.0, tp])
    tmid = 0.5 * (edges[:-1] + edges[1:])
    steps = np.diff(edges)                       # per-step durations (ns)

    a, nu = waveform(shape, tmid, tp, params)

    # Running RF phase phi(t) = phi0 + 2*pi * integral(nu dt'), trapezoid on the
    # mid-step grid; for amplitude-only shapes nu == 0 so phi == phi0. Each
    # pulse's phase is referenced to its own start (standard AWG convention).
    phi = phi0 + 2.0 * np.pi * (np.cumsum(nu * steps) - 0.5 * nu * steps)

    # Effective-field components (GHz). bx, by are common to all offsets; bz is
    # the offset itself (constant in time, varies across the axis).
    bx = nu1 * a * np.cos(phi)
    by = nu1 * a * np.sin(phi)

    bz = offsets                                 # (N,)
    for k in range(tmid.size):
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
                       dt=0.5, phi0=0.0, init=(0.0, 0.0, 1.0)):
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
    M = propagate_pulse(M, shape, tp, nu1, offsets, params, dt=dt, phi0=phi0)
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
