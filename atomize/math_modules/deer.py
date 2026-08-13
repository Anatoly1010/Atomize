#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DEER / PDS distance-distribution analysis (math core).

Pulsed-dipolar spectroscopy traces (DEER/PELDOR, and the closely related
RIDME / DQC / SIFTER) share one model: a background-corrected form factor F(t)
is the integral over the distance distribution P(r) of an orientation-averaged
dipolar kernel,

    F(t) = \\int K(t, r) P(r) dr ,
    K(t, r) = \\int_0^1 cos[(1 - 3 xi^2) w(r) t] dxi ,

with the dipolar angular frequency w(r) = 2*pi * NU_DD / r^3 (rad/us, r in nm,
t in us). The kernel integral has a closed form in Fresnel integrals, so K is
built without a per-orientation loop.

Recovering P(r) from F(t) is a Fredholm equation of the first kind (ill-posed);
this module solves it two ways: Tikhonov regularization + non-negativity (NNLS),
the regularization weight chosen by GCV / the L-curve corner (`deer_invert`,
`deer_invert_joint`); and a model-free analytic integral Mellin-transform
inversion (Matveeva/Nekrasov/Maryasov, doi 10.1039/C7CP04059H) in
`deer_invert_mellin`.

Conventions: t in microseconds, r in nanometres. P is handled internally as
discrete probability masses (sum = 1); the matching density P(r) = masses / dr
is returned for plotting.

All heavy routines need scipy (the `math` extra: pip install -e .[math]); scipy
is imported lazily so importing this module never fails on a minimal install.
"""

import warnings

import numpy as np

# scipy is an optional dependency (pip install -e .[math]) and slow to import
# (~0.6 s on Windows). Probe availability cheaply -- find_spec does NOT import
# scipy -- and defer the real import to _require_scipy(), so importing this
# module stays numpy-only and GUIs that embed it start fast.
import importlib.util
SCIPY_AVAILABLE = importlib.util.find_spec('scipy') is not None
fresnel = nnls = curve_fit = isotonic_regression = None

# np.trapz was renamed np.trapezoid in NumPy 2.0 (np.trapz deprecated); pick
# whichever exists so the Mellin quadrature stays warning-free on either.
_trapz = getattr(np, 'trapezoid', getattr(np, 'trapz'))

# Perpendicular dipolar frequency constant: nu_perp = NU_DD / r^3 [MHz], r in nm
# (g = 2.0023). w(r) = 2*pi*nu_perp is then in rad/us for t in us.
NU_DD = 52.04  # MHz nm^3

# Modulation-depth clamps. Every route divides by lambda to form F, so LAM_MIN is
# the shared floor. The ceiling differs by what produced the estimate: a fitted
# background amplitude is bounded only by physics (A >= 0, i.e. full modulation is
# admissible -- `_no_background` exists for exactly that data), while a TAIL PIN
# reading lambda = 1 - mean(V/B) that high has failed rather than measured, so the
# pinned routes cap lower and report `lambda_clamped`.
LAM_MIN = 0.02
LAM_MAX = 1.0
LAM_MAX_PINNED = 0.95


def _require_scipy():
    """Lazily import scipy on first use and bind the symbols this module needs.
    Every scipy-using function calls this first, so the module-level fresnel /
    nnls / curve_fit globals are guaranteed populated before they are read."""
    global fresnel, nnls, curve_fit, isotonic_regression
    if not SCIPY_AVAILABLE:
        raise RuntimeError('DEER analysis requires scipy (pip install -e .[math]).')
    if fresnel is None:
        from scipy.special import fresnel as _fresnel
        from scipy.optimize import (nnls as _nnls, curve_fit as _curve_fit,
                                    isotonic_regression as _isotonic)
        fresnel, nnls, curve_fit = _fresnel, _nnls, _curve_fit
        isotonic_regression = _isotonic


# --------------------------------------------------------------------------- #
#  Dipolar kernel
# --------------------------------------------------------------------------- #
def dipolar_frequency(r, nu_dd=NU_DD):
    """Perpendicular dipolar frequency nu_perp(r) = nu_dd / r^3 [MHz], r in nm."""
    r = np.asarray(r, dtype=float)
    return nu_dd/r**3


def dipolar_kernel(t, r, nu_dd=NU_DD):
    """Orientation-averaged DEER kernel K[t, r] (no background, no modulation).

    `t` in us, `r` in nm. Returns shape (len(t), len(r)) with K(0, r) = 1,
    evaluated in closed form via Fresnel integrals:

        K(t, r) = sqrt(pi / (6 a)) [cos(a) C(z) + sin(a) S(z)],
        a = w(r) |t|,  z = sqrt(6 a / pi),  w(r) = 2*pi*nu_dd / r^3 .

    The a -> 0 limit is K = 1 (set explicitly to avoid 0/0).
    """
    _require_scipy()
    t = np.asarray(t, dtype=float).reshape(-1, 1)     # (nt, 1)
    r = np.asarray(r, dtype=float).reshape(1, -1)     # (1, nr)
    w = 2*np.pi*nu_dd/r**3                             # (1, nr) rad/us
    a = np.abs(w*t)                                    # (nt, nr) >= 0
    z = np.sqrt(6*a/np.pi)
    S, C = fresnel(z)                                  # scipy returns (S, C)
    with np.errstate(divide='ignore', invalid='ignore'):
        K = np.sqrt(np.pi/(6*a))*(np.cos(a)*C + np.sin(a)*S)
    K[a == 0] = 1.0
    return K


# --------------------------------------------------------------------------- #
#  Background correction
# --------------------------------------------------------------------------- #
def _echo_top(t, V, w=5):
    """Robust echo-top height for the V(0)=1 normalization.

    The form factor is anchored by dividing V by its value at t=0, but taking that
    value from the SINGLE nearest sample makes the whole curve hostage to one
    noisy point: at high noise it forces F(0)=1 onto a noise-perturbed sample and
    scales every other point relative to it, which biases the recovered echo top
    too narrow (the t=0-area fit error grows with noise). Instead fit a quadratic
    in a +-`w`-sample window around the sample nearest t=0 and take its vertex
    height (the smoothed echo maximum). Falls back to the single sample when the
    window is too short, the fit is not concave, or the estimate is non-positive."""
    t = np.asarray(t, float); V = np.asarray(V, float)
    i0 = int(np.argmin(np.abs(t)))
    lo, hi = max(0, i0 - w), min(len(V), i0 + w + 1)
    if hi - lo < 3:
        return float(V[i0])
    tt = t[lo:hi] - t[i0]; vv = V[lo:hi]
    try:
        a, b, c = np.polyfit(tt, vv, 2)
    except Exception:
        return float(V[i0])
    vtx = float(np.clip(-b/(2*a) if a < 0 else 0.0, tt[0], tt[-1]))
    val = a*vtx**2 + b*vtx + c
    return float(val) if val > 0 else float(V[i0])


def _no_background(t, V, bg_start=None, bg_end=None):
    """NO intermolecular background: B(t) = 1 (k = 0). For data that has none --
    pre-corrected traces, simulations, or full-modulation (lambda -> 1) signals.

    Fitting a decaying background to such a trace is actively harmful: with no flat
    asymptote the fit mistakes the DIPOLAR decay of the form factor for a background
    and divides a spurious exp() into F, badly broadening P(r) (e.g. a sigma 0.20
    Gaussian recovered at sigma 0.7, overlap 0.81 instead of 0.99). Here B is fixed
    to 1 and only the modulation depth lambda is estimated, from the decayed tail
    baseline (lambda = 1 - mean(V_norm) over [bg_start, bg_end]); F = (V_norm -
    (1-lambda))/lambda. Returns the same dict shape as `background_fit`."""
    t = np.asarray(t, dtype=float)
    V = np.asarray(V, dtype=float)
    V = V/_echo_top(t, V)                               # normalize V(0) = 1
    if bg_start is None:
        bg_start = t[0] + 0.5*(t[-1] - t[0])
    mask = t >= bg_start
    if bg_end is not None:
        mask = mask & (t <= bg_end)
    if int(mask.sum()) < 3:
        mask = t >= (t[0] + 0.5*(t[-1] - t[0]))
    lam = float(np.clip(1.0 - float(np.mean(V[mask])), LAM_MIN, LAM_MAX))
    B = np.ones_like(t)
    F = (V - (1.0 - lam))/lam
    return {'lambda': lam, 'k': 0.0, 'dim': 3.0, 'A': float(1.0 - lam),
            'B': B, 'form_factor': F, 'V_norm': V, 't': t,
            'bg_start': float(bg_start),
            'bg_end': (None if bg_end is None else float(bg_end)), 'mask': mask}


def _bg_model(t, A, k, d):
    return A*np.exp(-(k*np.abs(t))**(d/3.0))


def background_fit(t, V, bg_start, bg_end=None, dim=3.0, fit_dim=False):
    """Fit the intermolecular background on the window bg_start <= t (<= bg_end)
    and return the background-corrected form factor.

    `V` is normalized so V(t=0) = 1. The tail window is fit to
    (1 - lambda) * exp(-(k|t|)^(d/3)); the modulation depth lambda = 1 - A. The
    full-trace background is B(t) = exp(-(k|t|)^(d/3)) and the form factor

        F(t) = (V(t)/B(t) - (1 - lambda)) / lambda .

    Only the fit window is bounded by [bg_start, bg_end]; B(t) and F(t) are still
    evaluated over the whole trace. `bg_end=None` uses everything past bg_start
    (the default). `dim` is the fractal background dimension (3 = homogeneous 3D);
    set `fit_dim=True` to float it. Returns a dict with lambda, k, dim, A, B,
    form_factor, t, bg_start, bg_end, mask.
    """
    _require_scipy()
    t = np.asarray(t, dtype=float)
    V = np.asarray(V, dtype=float)
    V = V/_echo_top(t, V)                              # normalize at t = 0 (robust)
    mask = t >= bg_start
    if bg_end is not None:
        mask = mask & (t <= bg_end)
    if mask.sum() < 4:
        raise ValueError('Background region has too few points; widen [bg_start, bg_end].')
    tt, vv = t[mask], V[mask]
    a0 = float(np.clip(vv[0], 0.05, 1.0))
    if fit_dim:
        popt, _ = curve_fit(_bg_model, tt, vv, p0=[a0, 0.1, dim],
                            bounds=([0.0, 0.0, 1.0], [1.5, np.inf, 6.0]),
                            maxfev=10000)
        A, k, d = popt
    else:
        f = lambda tx, A, k: _bg_model(tx, A, k, dim)
        popt, _ = curve_fit(f, tt, vv, p0=[a0, 0.1],
                            bounds=([0.0, 0.0], [1.5, np.inf]), maxfev=10000)
        A, k = popt
        d = dim
    lam = 1.0 - A
    B = np.exp(-(k*np.abs(t))**(d/3.0))
    # A > 1 on a degenerate tail fit flips the sign of F; clip as the siblings do
    lam_raw = lam
    lam = float(np.clip(lam, LAM_MIN, LAM_MAX))
    # clipping stops the sign flip but the fit is still degenerate -- say so
    degenerate = not (LAM_MIN <= lam_raw <= LAM_MAX)
    if degenerate:
        warnings.warn(
            'DEER background fit is degenerate: raw modulation depth lambda = '
            '%.3f is outside (0, 1] (A = %.3f hit its bound). The tail window '
            '[bg_start, bg_end] is probably too short or the trace has not '
            'reached its asymptote; try fit_dim=False or a later bg_start. '
            'lambda was clipped to %.3f and the resulting P(r) is unreliable.'
            % (lam_raw, A, lam), RuntimeWarning, stacklevel=2)
    F = (V/B - (1 - lam))/lam
    return {'lambda': lam, 'lambda_raw': float(lam_raw),
            'lambda_degenerate': bool(degenerate),
            'k': float(k), 'dim': float(d), 'A': float(A),
            'B': B, 'form_factor': F, 'V_norm': V, 't': t,
            'bg_start': float(bg_start),
            'bg_end': (None if bg_end is None else float(bg_end)), 'mask': mask}


def background_general(t, V, bg_start, bg_end=None,
                       a=None, b=None, c=None, d=None, fit=True, **_ignored):
    """General empirical intermolecular background on the tail window
    bg_start <= t (<= bg_end):

        g(t) = a * exp( b * (t + c * d^t) )       (a, b, c, d free)

    A flexible alternative to the stretched-exponential `background_fit` for traces
    whose intermolecular decay is not well described by exp(-(k|t|)^(d/3)). Same
    convention as `background_fit`: V is normalized to V(0)=1, the tail baseline
    g(t) = (1-lambda)*B(t), so the background normalized to B(0)=1 is
    B(t) = g(t)/g(0), the modulation depth is lambda = 1 - g(0) (g(0) = a*exp(b*c),
    since d^0 = 1), and  F(t) = (V(t)/B(t) - (1 - lambda)) / lambda . The amplitude
    `a` cancels in B = g/g(0), so b / c / d set the background SHAPE and `a` only
    its t=0 level (hence lambda); B(t) = exp(b*(t + c*(d^t - 1))) stays positive.

    With `fit=True` (default) the four coefficients are fit on the tail; any of
    a / b / c / d that are supplied are used as the initial guess. With `fit=False`
    they are used DIRECTLY as the background (manual mode -- the GUI's hand-set
    coefficients), no fitting. When fitting, `d` is constrained so the d^t term
    retains >= 5% of its t=0 amplitude across the fit window (d^span >= 0.05):
    otherwise c and d are unconstrained by the tail (where d^t has vanished) and
    the fit is degenerate; a faster decay is not an intermolecular background
    anyway. Time `t` is in microseconds, so the manual coefficients act on t in us.
    Returns the same dict shape as `background_fit`, with k / dim = NaN and the
    coefficients in `params` (a, b, c, d) and `model` = 'general'.
    """
    _require_scipy()
    t = np.asarray(t, dtype=float)
    V = np.asarray(V, dtype=float)
    V = V/_echo_top(t, V)                              # normalize at t = 0 (robust)
    if bg_start is None:
        bg_start = t[0] + 0.5*(t[-1] - t[0])
    mask = t >= bg_start
    if bg_end is not None:
        mask = mask & (t <= bg_end)

    def _model(x, aa, bb, cc, dd):
        dd = min(max(float(dd), 1e-9), 1.0)
        return aa*np.exp(bb*(x + cc*np.power(dd, x)))

    if fit:
        if int(mask.sum()) < 4:
            raise ValueError('Background region has too few points; widen [bg_start, bg_end].')
        tt, vv = t[mask], V[mask]
        span = float(tt[-1] - tt[0]) or 1.0
        # bound d so the d^t term stays data-constrained over the fit window
        d_lo = float(np.clip(0.05**(1.0/span), 0.05, 0.95))
        # in the tail the d^t term has decayed, so g ~ a*exp(b*t): seed a / b from
        # a log-linear fit of the (positive) tail, c from the early curvature.
        lv = np.log(np.clip(vv, 1e-6, None))
        b_lin = float(np.polyfit(tt, lv, 1)[0]) if span > 0 else -0.05
        a_lin = float(np.exp(np.mean(lv - b_lin*tt)))
        a0 = float(a) if a is not None else max(a_lin, 1e-6)
        b0 = float(b) if b is not None else b_lin
        c0 = float(c) if c is not None else 0.0
        d0 = float(np.clip(d if d is not None else np.sqrt(d_lo), d_lo, 1.0))
        p0 = [a0, b0, c0, d0]
        bounds = ([1e-9, -np.inf, -np.inf, d_lo], [np.inf, np.inf, np.inf, 1.0])
        try:
            popt, _ = curve_fit(_model, tt, vv, p0=p0, bounds=bounds, maxfev=10000)
        except Exception:
            popt = p0
        af, bf, cf, df = (float(x) for x in popt)
    else:                                              # manual: use the given coefficients
        af = 1.0 if a is None else float(a)
        bf = 0.0 if b is None else float(b)
        cf = 0.0 if c is None else float(c)
        df = float(np.clip(0.8 if d is None else float(d), 1e-6, 1.0))
    g = _model(t, af, bf, cf, df)                     # = (1-lambda)*B(t) baseline
    g0 = af*np.exp(bf*cf)                              # g(0): d^0 = 1
    lam = float(np.clip(1.0 - g0, LAM_MIN, LAM_MAX))
    B = g/g0 if abs(g0) > 1e-9 else np.ones_like(t)
    F = (V/np.clip(B, 1e-3, None) - (1 - lam))/lam
    return {'lambda': lam, 'k': float('nan'), 'dim': float('nan'), 'A': float(g0),
            'B': B, 'form_factor': F, 'V_norm': V, 't': t,
            'bg_start': float(bg_start),
            'bg_end': (None if bg_end is None else float(bg_end)), 'mask': mask,
            'model': 'general', 'params': {'a': af, 'b': bf, 'c': cf, 'd': df}}


# --------------------------------------------------------------------------- #
#  Tikhonov regularization + non-negativity
# --------------------------------------------------------------------------- #
def _crop_pre_zero(t, V, policy='crop', tol=3.0):
    """Handle samples recorded BEFORE the dipolar zero time.

    `policy='crop'` drops them all. `dipolar_kernel` evaluates |w*t|, so a t < 0
    sample is modelled as evolution at +|t|; where the data there really is the echo
    rising edge, the inversion pays for the mismatch with P(r) mass at short r.

    `policy='even_fold'` keeps the same samples but AVERAGES each into its mirrored
    positive twin, so the result stays on t >= 0 with the original uniform spacing.
    That is the form the engines which cannot take negative rows need -- Mellin
    substitutes u = ln T, `_gauss_mc`'s `_pake_transform` assumes uniform sampling --
    and it lets every engine work from the same information on a given trace, so a
    Mellin-vs-Tikhonov disagreement diagnoses the METHOD rather than the input. On
    Mellin it is worth +0.0064 overlap (t = 5.2) over 756 traces, rising to +0.0226 at
    sigma 0.06: its delta-split fits the head parabola's curvature from the data on
    [0, delta], and folding halves the noise exactly there. On the multi-Gaussian
    engine the same change is NOT significant (+0.0034, t = 1.7) and is mildly
    negative at low noise, so that engine keeps `'crop'`.

    `policy='even'` keeps the ones that are demonstrably NOT a rising edge. Dropping
    them unconditionally has its own cost, and it is the larger one: every K(.,r) is
    even, so any model form factor has F'(0) = 0 exactly, and on a symmetric window
    an odd data error is orthogonal to the whole model space -- a zero-time error
    costs variance and no bias. Cropping to t >= 0 destroys that orthogonality, and
    the only basis direction that can supply a non-zero initial slope is the short-r
    end, so a t0 error late by D buys spurious mass ~ (r_s/<r>)^6 * w_s * D there,
    with the shoulder in F_fit that goes with it. Measured over the 756-trace
    synthetic catalogue, keeping them is worth +0.008 overlap (t = 7.6), positive at
    every noise level and in every shape class, and worth more than a PERFECT t0.

    Which ones are safe is decided from the data, not assumed: walk outward from
    t = 0 and keep the contiguous run whose mirror residual V(-t) - V(+t) stays
    inside `tol` * sqrt(2) * sigma, since a rising edge, when there is one, sits at
    the far end. On the YopO ring test this keeps 74 % of the pre-zero samples and
    moves no reported peak at all, while rejecting the traces whose V-space residual
    would otherwise degrade (keeping them unconditionally costs 44 % on the 7 traces
    whose mirror residual exceeds 3 sigma, and 4 % on the other 21).
    """
    t = np.asarray(t, float); V = np.asarray(V, float)
    m = t >= 0.0
    if m.all():
        return t, V, 0
    n_pre = int((~m).sum())
    tp, Vp = t[m], V[m]
    if policy not in ('even', 'even_fold') or len(tp) < 3:
        return tp, Vp, n_pre
    sig = _tail_noise(t, V)
    if not np.isfinite(sig) or sig <= 0.0:      # cannot judge -> crop, as before
        return tp, Vp, n_pre
    tn = -t[~m][::-1]                                  # ascending in |t|
    Vn = V[~m][::-1]
    thr = tol*np.sqrt(2.0)*sig
    keep = 0
    while (keep < len(tn) and tn[keep] <= tp[-1]
           and abs(Vn[keep] - np.interp(tn[keep], tp, Vp)) <= thr):
        keep += 1
    if keep == 0:
        return tp, Vp, n_pre
    if policy == 'even_fold':
        # Same samples, same information, but AVERAGED into their positive twins so
        # the result stays on t >= 0 with the original uniform spacing. The engines
        # that cannot take negative rows -- Mellin substitutes u = ln T, and
        # `_gauss_mc`'s `_pake_transform` assumes uniform sampling -- need this form,
        # and using it keeps every engine looking at the same data on a given trace.
        add = np.zeros_like(tp); w = np.zeros_like(tp)
        idx = np.clip(np.searchsorted(tp, tn[:keep]), 0, len(tp) - 1)
        for j, val in zip(idx, Vn[:keep]):
            add[j] += val; w[j] += 1.0
        Vf = np.where(w > 0, (Vp + add)/(1.0 + w), Vp)
        return tp, Vf, n_pre - keep
    tk = np.concatenate([-tn[:keep][::-1], tp])
    Vk = np.concatenate([Vn[:keep][::-1], Vp])
    return tk, Vk, n_pre - keep


def alias_r_min(t, nu_dd=NU_DD):
    """Shortest distance the sampling can carry: r = (4 nu_dd dt)^(1/3).

    The kernel's argument is a(1 - 3cos^2 th) with a = w|t|, which spans [-2a, a], so
    its fastest component is 2w and it aliases once 2w > pi/dt. With
    w = 2 pi nu_dd / r^3 that is r^3 < 4 nu_dd dt. Grid points below this are not
    resolved by the data: 1.28 nm at 10 ns sampling but 1.88 nm at 32 ns.
    """
    t = np.asarray(t, float)
    if len(t) < 2:
        return 0.0
    dt = float(np.median(np.diff(np.sort(t))))
    if not np.isfinite(dt) or dt <= 0:
        return 0.0
    return float((4.0*nu_dd*dt)**(1.0/3.0))


def _check_bg_start_periods(bg, r, P_density, min_periods=0.75, nu_dd=NU_DD):
    """Is the background window late enough for the distance actually recovered?

    The background rate is only meaningful where the dipolar signal has finished
    evolving. How late that is depends on the DISTANCE: one dipolar period is
    T_dd = r^3 / nu_dd, so 2.4 us at 5 nm but 0.17 us at 2 nm. A bg_start that is
    comfortably late for a 3 nm sample opens at a fifth of a period for a 5 nm one,
    and the fit then absorbs dipolar decay into k -- pulling the reported distance
    SHORT, by 0.12-0.35 nm on the measured sweep.

    Calibrated over 1260 cells (7 distances x 5 t_max x 6 bg_start x 3 noise x 2
    widths, 7560 inversions): with bg_start below 0.75 dipolar periods of the
    recovered mean distance, 95 % of the cells whose mean is wrong by >0.05 nm are
    caught, at a 24 % false-alarm rate; below 0.5 periods only 77 % are caught. Mean
    |error| by band: 0.21 nm under 0.5 periods, 0.09 at 0.5-0.75, 0.017 at
    0.75-1.0, 0.013 beyond. The effect is confined to long distances -- no band
    exceeds 0.018 nm at r <= 3.5 nm -- so this never fires on a routine 2-4 nm
    measurement.

    KNOWN BLIND SPOT (measured, not theoretical): the reference distance is the
    engine's OWN r_mean, and the failure this detects biases exactly that number
    SHORT. A shorter r_mean means a shorter dipolar period, hence MORE periods,
    hence a pass -- the detector is least sensitive precisely where the fit is
    worst. Measured on a 5.5 nm synthetic at bg_start = 1.50 us: Mellin returns
    4.598 nm (0.90 nm short) at 0.80 periods and is NOT flagged, while the joint
    engine on the same trace is only 0.42 nm short, reports 0.60 periods, and IS.
    Re-referencing to a fit-independent distance was tried and REJECTED: the
    trace-supported cap 5*(Tmax/2)^(1/3) puts every one of 84 real engine results
    below 0.75 periods, i.e. it flags everything (`~/deer_benchmark/s6q/
    detectors.log`). Treat a pass as weak evidence and cross-check engines; a
    non-circular reference needs the 1260-cell recalibration, not a swapped
    denominator.

    Returns (flagged, periods, r_mean) with periods = bg_start / T_dd(r_mean).
    """
    try:
        r = np.asarray(r, float)
        d = np.clip(np.asarray(P_density, float), 0.0, None)
        m = float(np.trapezoid(d, r))
        if not (m > 0):
            return False, float('nan'), float('nan')
        r_mean = float(np.trapezoid(r*d, r)/m)
        t_dd = r_mean**3/nu_dd
        bs = float(bg.get('bg_start', float('nan')))
        if not (np.isfinite(bs) and t_dd > 0):
            return False, float('nan'), r_mean
        per = bs/t_dd
        return bool(per < float(min_periods)), float(per), r_mean
    except Exception:
        return False, float('nan'), float('nan')


def _flag_bg_start_early(bg, r, P_density, nu_dd=NU_DD, min_periods=0.75):
    """Record `_check_bg_start_periods` on the background dict and warn if it fires.

    Every engine that fits a background needs this, not just the joint Tikhonov one:
    Mellin and the multi-Gaussian both default to `bg_engine='joint'` and so inherit
    the same early-window failure. It has to run after the inversion because the
    dipolar period is set by the distance actually recovered.
    """
    early, per, r_mean = _check_bg_start_periods(
        bg, r, P_density, min_periods=min_periods, nu_dd=nu_dd)
    bg['bg_start_periods'] = per
    bg['bg_start_early'] = early
    if early:
        warnings.warn(
            'DEER background window starts at %.2f dipolar periods of the recovered '
            'distance (%.2f nm): the rate is fitted where the dipolar signal is still '
            'evolving, which biases the reported distance SHORT (0.09-0.35 nm on the '
            'calibration sweep). Move bg_start later -- at least %.2f us here -- or '
            'lengthen the trace.'
            % (per, r_mean, min_periods*r_mean**3/nu_dd), RuntimeWarning, stacklevel=3)
    return early


def _flag_not_deer_like(bg, lam=None, absF_max=1.2, lam_floor=LAM_MIN):
    """Is this a DEER trace at all? Records two specific tells on `bg`.

    Every engine happily returns a distance distribution for input that carries no
    dipolar modulation -- a bare exponential, a linear ramp, pure noise. Measured:
    V = exp(-0.35 t) with bg_engine='none' comes back as 3 Gaussians at a mean of
    6.32 nm, a straight ramp as 6.75 nm, and pure noise as 1.63 nm. Nothing in the
    result says the input was not a measurement.

    `form_factor_implausible` -- a normalized form factor is bounded by F(0) = 1,
    so |F| far above 1 means the background division blew up rather than that the
    sample has a distance. `lambda_collapsed` -- essentially no modulation depth,
    so there is nothing for a distance to be fitted to (the engines that PIN lambda
    clamp it at LAM_MIN and also raise `lambda_clamped`; the multi-Gaussian engine
    re-fits it free and can return 0.0000 with no other tell).

    Both thresholds are set from the healthy range, not guessed: over 84 real
    results (28 traces x 3 engines) max|F| spans 0.914-1.046 and lambda 0.224-0.505,
    so 1.2 and LAM_MIN fire on 0/84 while the garbage cases above read 4.73 and
    0.0000. See `~/deer_benchmark/s6q/detectors.log`.

    On REAL data the work they do is catching `bg_engine='general'` collapsing:
    its empirical g(t) needs a clean tail, and on 4 of 29 traces it swallowed the
    modulation instead, reaching |F| = 1.33 / 4.25 / 13.1 / 18.4 with lambda at
    0.040-0.258 of what the joint engine gets on the same trace (every other trace:
    0.52-1.16, median 0.94). Those four were reported as ordinary distributions --
    one of them 7.85 nm with half its mass on the grid edges.

    They catch the LOUD failures only: pure noise trips both, and the bare
    exponential trips `lambda_collapsed` under bg_engine='joint'. A smooth decay
    that the background cannot absorb still passes -- the same exponential under
    bg_engine='none' (lambda 0.560, |F| 1.003) and a linear ramp (0.318, 1.029)
    are reported as 6-7 nm distributions with no flag. Catching those needs a
    no-oscillation test on F, which a genuinely broad P(r) would also trip, so it
    wants its own false-alarm measurement before it exists.
    """
    F = np.asarray(bg.get('form_factor', ()), float)
    aF = float(np.max(np.abs(F))) if F.size else float('nan')
    lam = float(bg.get('lambda', float('nan')) if lam is None else lam)
    bad_F = bool(np.isfinite(aF) and aF > float(absF_max))
    bad_lam = bool(np.isfinite(lam) and lam <= float(lam_floor))
    bg['form_factor_absmax'] = aF
    bg['form_factor_implausible'] = bad_F
    bg['lambda_collapsed'] = bad_lam
    if bad_F or bad_lam:
        why = []
        if bad_F:
            why.append('the form factor reaches |F| = %.2f, but a normalized form '
                       'factor is bounded by F(0) = 1' % aF)
        if bad_lam:
            why.append('the modulation depth is %.4f, i.e. there is no dipolar '
                       'modulation to fit a distance to' % lam)
        warnings.warn(
            'DEER input does not look like a dipolar trace: ' + '; '.join(why)
            + '. The reported P(r) is what the engine does with this input, not a '
              'measured distance distribution.', RuntimeWarning, stacklevel=3)
    return bad_F or bad_lam


def _apply_alias_floor(t, r, clamp=True, nu_dd=NU_DD):
    """Drop distance-grid points the sampling cannot resolve; returns (r, r_alias).

    Below `alias_r_min` the kernel's parallel (2*omega) component folds back to a lower
    apparent frequency, so a column there no longer represents the distance it is
    labelled with. Those columns are not merely useless: they are weakly constrained by
    the data, and a non-negative fit with a roughness penalty will use them to absorb
    residual it cannot otherwise explain -- the same failure shape as an unpenalized
    grid edge, from a different cause.

    Measured on coarse-sampled synthetic traces, clamping is worth +0.0071 (t 4.1) at
    dt = 24 ns and +0.0080 (t 2.7) at 32 ns, with no measured cost to short-distance
    shapes, and is exactly a no-op at dt <= 16 ns where the floor sits below the usual
    1.5 nm grid start. Applied in every engine so they keep working on the same grid.

    `clamp=False` restores the previous behaviour (warn only).
    """
    r = np.asarray(r, float)
    ra = alias_r_min(t, nu_dd=nu_dd)
    if ra <= 0 or not len(r):
        return r, ra
    keep = r >= ra - 1e-9
    if keep.all():
        return r, ra
    dt_ns = float(np.median(np.diff(np.sort(np.asarray(t, float)))))*1e3
    if not clamp:
        warnings.warn(
            'DEER distance grid starts at %.2f nm but this trace samples at %.1f ns, '
            'which cannot resolve below %.2f nm ((4*nu_dd*dt)^(1/3): the kernel\'s '
            'fastest component 2*omega aliases there). Those points are unconstrained '
            'by the data; raise r_min to about %.2f nm.'
            % (float(r[0]), dt_ns, ra, ra), RuntimeWarning, stacklevel=3)
        return r, ra
    if int(keep.sum()) < 8:
        warnings.warn(
            'DEER sampling at %.1f ns cannot resolve below %.2f nm, which would leave '
            'only %d of %d distance-grid points. The grid was left alone -- lower '
            'r_max or sample faster; the short end of this P(r) is not supported by '
            'the data.' % (dt_ns, ra, int(keep.sum()), len(r)),
            RuntimeWarning, stacklevel=3)
        return r, ra
    warnings.warn(
        'DEER distance grid clamped to %.2f nm: this trace samples at %.1f ns and '
        'cannot resolve below that ((4*nu_dd*dt)^(1/3) -- the kernel\'s fastest '
        'component 2*omega aliases there), so %d grid point(s) below it were dropped. '
        'Sample faster to reach shorter distances; a finer r grid cannot recover what '
        'the sampling did not capture.'
        % (ra, dt_ns, int((~keep).sum())), RuntimeWarning, stacklevel=3)
    return r[keep], ra


def _first_min_time(t, F, smooth=5):
    """Time of the first local minimum of F, i.e. where the echo-top region ends.

    A parabola is only meaningful on the initial monotone decay; past the first
    dipolar minimum F turns back up and a least-squares fit there returns nonsense
    curvature. Smoothed first, so one noise excursion does not call a minimum.
    Expects t >= 0 -- on a trace that still carries pre-zero samples it would call a
    minimum inside the rising side and hand back a time below zero.
    """
    t = np.asarray(t, float); F = np.asarray(F, float)
    o = np.argsort(t)
    tp, fp = t[o], F[o]
    k = max(1, int(smooth))
    if k > 1 and len(fp) >= k:
        fp = _boxcar(fp, k)
    d = np.diff(fp)
    up = np.where(d > 0)[0]
    for i in up:
        if np.any(d[:i] < 0):
            return float(tp[i])
    return float(tp[-1])


def _head_delta(t, F, level=0.60, floor=0.0, cap=0.35, iters=6, n_min=4):
    """Echo-top head width from the FITTED curvature, not from a raw crossing.

    delta = sqrt((1-level)*a/-b) with (a, b) least-squares over the window itself,
    iterated to a fixed point from the wide end. Taking delta from where a noisy
    sample first drops below a level makes the window SHRINK as noise rises, which is
    backwards; the curvature is a fit over many points, so it keeps the r^3 scaling of
    the honest window. The floor is sample-count-driven (a fixed floor can hold two
    points on a coarse grid) and the first dipolar minimum bounds it from above.

    `t` must already be restricted to t >= 0.
    """
    t = np.asarray(t, float); F = np.asarray(F, float)
    tp = np.sort(t[t >= 0.0])
    if len(tp) < n_min:
        return float(np.clip(floor, floor, cap))
    lo = max(float(floor), float(tp[n_min - 1]))
    hi = min(float(cap), _first_min_time(t, F))
    d = float(np.clip(hi, lo, max(float(tp[-1]), lo)))
    for _ in range(int(iters)):
        m = (t >= 0.0) & (t <= d)
        if int(m.sum()) < n_min:
            break
        A = np.vstack([np.ones(int(m.sum())), t[m]**2]).T
        c, *_ = np.linalg.lstsq(A, F[m], rcond=None)
        a, b = float(c[0]), float(c[1])
        if not (b < 0.0 and a > 0.0):
            break
        d_new = float(np.clip(np.sqrt((1.0 - level)*a/(-b)), lo, hi))
        done = abs(d_new - d) < 1e-4
        d = d_new
        if done:
            break
    return float(np.clip(d, lo, hi))


def _even_head(t, F, delta):
    """Replace F on |t| <= h by an even parabola fitted to the trace's EVEN PART.

    Returns (F_new, b, h) or (F, nan, nan) when the window is too thin.

    The head is a parity device: F is even about t0, so the echo top carries far fewer
    degrees of freedom than it has samples and replacing it by its own parabola
    denoises the highest-leverage part of the trace. Fitting that parabola on the
    ONE-SIDED window [0, delta] defeats the purpose -- there the odd part of a
    zero-time error D is not orthogonal to {1, t^2}, and projecting it gives
    b_hat = b(1 + 15 D/(8 delta)), a curvature bias linear in D. Since
    b = -(2/5)<w^2> and w = 2*pi*nu_dd/r^3, that is a DISTANCE bias: measured over
    D = +-40 ns on noiseless traces the one-sided curvature swings 17x on a narrow
    shape. Adding an odd term and discarding it does not help either, because on a
    one-sided window t is not orthogonal to t^4 -- a shift and F's quartic term are
    confounded, and the fit reads D = 33 ns on a trace with no shift at all.

    Averaging mirrored pairs, G(u) = [F(u) + F(-u)]/2, cancels the odd part
    identically. That needs the pre-zero samples, so it is only available under
    `pre_zero='even'`. The replacement window is clipped to the fit half-width h:
    h is capped by the available pre-zero span, and applying a parabola fitted over
    120 ns out to a 322 ns delta is extrapolation that costs 0.013 overlap on exactly
    the broad shapes the construction exists to protect.
    """
    a, b, _c, h = _pair_fit(t, F, delta, order=2)
    if not np.isfinite(b):
        return F, np.nan, np.nan
    m = np.abs(np.asarray(t, float)) <= h
    if int(m.sum()) < 4 or not (b < 0.0):
        return F, np.nan, np.nan
    out = np.asarray(F, float).copy()
    out[m] = a + b*np.asarray(t, float)[m]**2
    return out, b, h


def _pair_fit(t, F, delta, order=2):
    """Even polynomial fitted to G(u) = [F(u) + F(-u)]/2; returns (a, b, c, h).

    `order=2` gives the head's own replacement parabola. `order=4` adds the quartic
    and is what the GUARD reads: b there is a better estimate of the true curvature,
    because over a window wide enough to denoise, the t^4 term of
    K = 1 - (2/5)w^2 t^2 + (2/35)w^4 t^4 is not negligible and biases a two-term fit.
    The two are deliberately different -- the replacement wants two parameters, the
    diagnostic wants an accurate <w^2>.
    """
    t = np.asarray(t, float); F = np.asarray(F, float)
    h = min(float(delta), -float(np.min(t)))
    if h <= 0:
        return (np.nan,)*3 + (np.nan,)
    dt = float(np.median(np.diff(np.sort(t))))
    if not np.isfinite(dt) or dt <= 0:
        return (np.nan,)*3 + (np.nan,)
    n_u = int(max(4, round(h/dt)))
    u = np.linspace(h/n_u, h, n_u)
    o = np.argsort(t); ts, Fs = t[o], F[o]
    G = 0.5*(np.interp(u, ts, Fs) + np.interp(-u, ts, Fs))
    cols = [np.ones_like(u), u**2] + ([u**4] if order >= 4 else [])
    A = np.vstack(cols).T
    if len(u) <= A.shape[1]:
        return (np.nan,)*3 + (h,)
    co, *_ = np.linalg.lstsq(A, G, rcond=None)
    return (float(co[0]), float(co[1]),
            float(co[2]) if order >= 4 else np.nan, h)


def _r_from_curvature(b, nu_dd=NU_DD):
    """Distance implied by the echo-top curvature alone: b = -(2/5)<w^2>."""
    if not (b < 0):
        return np.nan
    return float((2*np.pi*nu_dd/np.sqrt(-2.5*b))**(1.0/3.0))


def _echo_head_solve(t, F, K, L, r, dr, alphas, method, alpha, alpha_factor,
                     scan_lcurve, P_base, lc_base, alpha_base, level, cap,
                     ratio_max, nu_dd):
    """Apply the guarded even head and re-solve; returns (F, P, lc, alpha, info).

    The guard is a BREADTH test, not a distance one. The blocker this exists for --
    the 5.9-7.35 nm YopO group, where the head shifted the mean distance +0.148 nm --
    is not a long-r effect: those traces have an echo-top curvature implying 3.3 nm
    while reporting 7 nm peaks, because <w^2> ~ r^-6 is dominated by the shortest
    component present. Every distance-scale candidate (delta/t_max, t_max/delta, "the
    first dipolar minimum is not reached") puts that group in the middle of the others
    and cannot separate it; and cv60's delta rule makes delta*w_rms ~ 1 at every
    distance by construction, so nothing built on that product can discriminate
    either.

    What separates it is r_mean/r_eff: the mean distance of the unheaded solution
    against the distance the echo top alone implies. It is 1 for a single distance and
    grows with breadth, and a two-parameter head cannot stand in for an echo top that
    is a mixture of very different decay rates. On the ring test it is 1.02-1.23
    everywhere except that group, which spans 1.27-1.47.

    A failed head fit (nan) also declines the head, which is the safe direction. The
    unheaded solution is reused for the guard, so the second regularization scan is
    paid only when the head is actually applied.
    """
    info = {'applied': False, 'requested': True, 'delta': None,
            'r_eff': None, 'r_ratio': None}
    pos = t >= 0.0
    if int(pos.sum()) < 8:
        return F, P_base, lc_base, alpha_base, info
    delta = _head_delta(t[pos], F[pos], level=level, cap=cap)
    info['delta'] = float(delta)
    if not (delta > 0):
        return F, P_base, lc_base, alpha_base, info
    F_head, b, _h = _even_head(t, F, delta)
    _a4, b4, _c4, _h4 = _pair_fit(t, F, delta, order=4)
    r_eff = _r_from_curvature(b4, nu_dd=nu_dd)
    info['r_eff'] = (None if not np.isfinite(r_eff) else float(r_eff))
    if not (np.isfinite(r_eff) and np.isfinite(b)):
        return F, P_base, lc_base, alpha_base, info
    dens = np.clip(np.asarray(P_base, float), 0.0, None)
    mass = float(np.trapezoid(dens, r))
    r_mean = float(np.trapezoid(r*dens, r)/mass) if mass > 0 else np.nan
    ratio = r_mean/r_eff if np.isfinite(r_mean) else np.nan
    info['r_ratio'] = (None if not np.isfinite(ratio) else float(ratio))
    if not (np.isfinite(ratio) and ratio <= float(ratio_max)):
        return F, P_base, lc_base, alpha_base, info
    lc = (l_curve(K, F_head, alphas, L, method=method)
          if (scan_lcurve or alpha is None) else None)
    a_use = (float(alpha) if alpha is not None
             else lc['alpha_opt']*float(alpha_factor))
    if alpha is None and alpha_factor == 1.0 and lc is not None:
        P = lc['P']
    else:
        P = tikhonov_nnls(K, F_head, a_use, L)
    info['applied'] = True
    return F_head, P, lc, a_use, info


def regularization_matrix(n, order=2, include_edges=False):
    """Discrete derivative operator L for Tikhonov smoothing (default 2nd order).

    `include_edges` closes the operator's FREE ENDS. The plain second difference is
    (n-2, n): P[0] and P[-1] each appear in exactly one row where an interior point
    appears in three, so edge mass is ~3x under-penalized and a spike sitting exactly
    at the grid edge is the cheapest roughness the fit can buy. That is a real
    artefact generator, not a curiosity -- it is why a spurious short-r peak MOVES
    when the distance grid's lower bound moves, tracking the boundary rather than any
    distance. With `include_edges` the two extra rows [-2, 1, ...] and [..., 1, -2]
    treat P as zero just outside the grid, so the boundary points carry the same
    curvature penalty as the interior.

    Use it when the grid comfortably contains the distribution; it is WRONG when the
    truth genuinely has mass at the boundary, because it then forces P -> 0 where the
    data says otherwise (measured: a true 2.03 nm distribution recovers its peak at
    2.02 nm on a grid starting at 1.5 nm, but at 2.19 nm on one starting at 2.0).
    """
    if order == 0:
        return np.eye(n)
    if order == 1:
        L = np.zeros((n - 1, n))
        idx = np.arange(n - 1)
        L[idx, idx] = -1.0
        L[idx, idx + 1] = 1.0
        return L
    L = np.zeros((n - 2, n))            # second order (curvature)
    idx = np.arange(n - 2)
    L[idx, idx] = 1.0
    L[idx, idx + 1] = -2.0
    L[idx, idx + 2] = 1.0
    if include_edges and n >= 2:
        top = np.zeros((1, n)); top[0, 0] = -2.0; top[0, 1] = 1.0
        bot = np.zeros((1, n)); bot[0, -1] = -2.0; bot[0, -2] = 1.0
        L = np.vstack([top, L, bot])
    return L


def tikhonov_nnls(K, F, alpha, L=None):
    """Non-negative Tikhonov solution of K P = F.

    Minimizes ||K P - F||^2 + alpha^2 ||L P||^2 subject to P >= 0 by solving the
    augmented NNLS problem [[K]; [alpha L]] P = [F; 0]. Returns P (masses, >= 0).
    """
    _require_scipy()
    K = np.asarray(K, float)
    F = np.asarray(F, float)
    if L is None:
        L = regularization_matrix(K.shape[1], 2)
    A = np.vstack([K, alpha*L])
    b = np.concatenate([F, np.zeros(L.shape[0])])
    # scipy's default maxiter (3n) raises RuntimeError at large alpha on fine r
    # grids, aborting the whole scan; give it room, then degrade to clipped lstsq
    try:
        try:
            P, _ = nnls(A, b, maxiter=max(3*A.shape[1], 5000))
        except TypeError:                              # scipy without maxiter
            P, _ = nnls(A, b)
    except RuntimeError:
        P = np.clip(np.linalg.lstsq(A, b, rcond=None)[0], 0.0, None)
    return P


def _menger(x1, y1, x2, y2, x3, y3):
    """Signed Menger curvature of three points (L-curve corner detector)."""
    a2 = (x2 - x1)**2 + (y2 - y1)**2
    b2 = (x3 - x2)**2 + (y3 - y2)**2
    c2 = (x3 - x1)**2 + (y3 - y1)**2
    twice_area = (x2 - x1)*(y3 - y1) - (x3 - x1)*(y2 - y1)
    denom = np.sqrt(a2*b2*c2)
    return 0.0 if denom == 0 else 2*twice_area/denom


def l_curve(K, F, alphas, L=None, method='gcv'):
    """Regularization scan over `alphas`: for each one solve the NNLS-Tikhonov
    problem and record the residual norm rho, the roughness norm eta, the Menger
    L-curve curvature, and the GCV score.

    The optimal alpha is chosen by `method`:
      'gcv'       -- minimum of the generalized cross-validation score (default).
                     Matches DeerLab's 'gcv' selection exactly on the same grid.
      'curvature' -- classic maximum-Menger-curvature L-corner. Unreliable here:
                     the DEER L-curve is nearly vertical (the residual stays at
                     the noise floor across decades of alpha), so there is no
                     well-defined corner and the pick lands at either end of the
                     grid depending on the background window -- measured swings of
                     six decades (alpha 1.6e-4 <-> 158) on one trace with only
                     `bg_start` moved, i.e. 17 modes <-> 1. Over-smoothing (merged
                     peaks) is the more common outcome, not the spiky P(r) the
                     older docs warned about. DeerLab's own 'lc' picks differently
                     again on the identical grid. Use GCV unless cross-checking.

    GCV uses the (unconstrained) Tikhonov influence-matrix trace as the effective
    degrees of freedom paired with the NNLS residual -- the standard DEER GCV
    approximation. That approximation biases alpha *upward* relative to a
    constrained-dof GCV, never downward.

    Returns dict: alphas, rho, eta, curvature, gcv, alpha_opt, index, method,
    P (the solution at the chosen alpha), `at_bound` (the pick sits on the first
    or last grid point -- a clipped, not an interior, optimum; also raises a
    RuntimeWarning) and `corner_ok` (False when 'curvature' found no corner and
    fell back to GCV).

    Note that alpha is in the units of the raw [1,-2,1] operator from
    `regularization_matrix`, i.e. dr^2 times the true second derivative, so a
    given numeric alpha means more smoothing on a coarser distance grid and the
    value is not directly comparable to DeerLab's (alpha_here*dr^2 ~ alpha_DL).
    """
    _require_scipy()
    K = np.asarray(K, float)
    F = np.asarray(F, float)
    if L is None:
        L = regularization_matrix(K.shape[1], 2)
    alphas = np.asarray(alphas, float)
    n = len(F)
    KtK = K.T@K
    LtL = L.T@L
    rho = np.empty(len(alphas))
    eta = np.empty(len(alphas))
    gcv = np.empty(len(alphas))
    Ps = []
    for i, al in enumerate(alphas):
        P = tikhonov_nnls(K, F, al, L)
        Ps.append(P)
        rho[i] = np.linalg.norm(K@P - F)
        eta[i] = np.linalg.norm(L@P)
        try:                                          # effective d.o.f. (hat trace)
            dof = float(np.trace(K@np.linalg.solve(KtK + (al**2)*LtL, K.T)))
        except np.linalg.LinAlgError:
            dof = 0.0
        denom = n - dof
        gcv[i] = n*rho[i]**2/denom**2 if abs(denom) > 1e-9 else np.inf
    x = np.log(rho + 1e-300)
    y = np.log(eta + 1e-300)
    kappa = np.zeros(len(alphas))
    for i in range(1, len(alphas) - 1):
        kappa[i] = _menger(x[i - 1], y[i - 1], x[i], y[i], x[i + 1], y[i + 1])
    corner_ok = True
    if method == 'curvature':
        # kappa[0] / kappa[-1] are unfilled sentinels; search the interior only
        if len(alphas) > 2 and kappa[1:-1].max() > 0:
            idx = 1 + int(np.argmax(kappa[1:-1]))
        else:                                         # no corner at all: fall back
            idx = int(np.argmin(gcv)) if len(alphas) > 2 else len(alphas)//2
            corner_ok = False
    else:                                             # 'gcv' (default)
        idx = int(np.argmin(gcv))
    at_bound = bool(idx in (0, len(alphas) - 1))
    if at_bound:
        warnings.warn(
            'DEER regularization scan picked alpha = %.4g at the %s end of the '
            'search grid [%.4g, %.4g]: this is a grid boundary, not an interior '
            'optimum, so the true optimum probably lies outside the grid and the '
            'reported alpha is clipped. Widen `alphas`, or treat the resulting '
            'P(r) as over-/under-smoothed.'
            % (alphas[idx], 'lower' if idx == 0 else 'upper', alphas[0], alphas[-1]),
            RuntimeWarning, stacklevel=2)
    return {'alphas': alphas, 'rho': rho, 'eta': eta, 'curvature': kappa,
            'gcv': gcv, 'alpha_opt': float(alphas[idx]), 'index': idx,
            'method': method, 'P': Ps[idx],
            'at_bound': at_bound, 'corner_ok': corner_ok}


# --------------------------------------------------------------------------- #
#  Full pipeline + forward simulation
# --------------------------------------------------------------------------- #
def default_r_axis(rmin=1.5, rmax=8.0, n=200):
    """Default distance grid (nm)."""
    return np.linspace(rmin, rmax, int(n))


def _normalize_masses(P):
    s = float(np.sum(P))
    return P/s if s > 0 else P


def tikhonov_ci(K, F, alpha, P, L=None, dr=1.0, z=1.96):
    """Pointwise NOISE-PROPAGATION band on the regularized P(r).

    For the linear Tikhonov estimator P = (KᵀK + α²LᵀL)⁻¹ Kᵀ F, the noise on the
    form factor propagates as cov(P) = σ² M Mᵀ with M = (KᵀK + α²LᵀL)⁻¹ Kᵀ and σ²
    estimated from the fit residuals (effective dof = N − tr(K M)). Returns
    (lower, upper) at confidence z (default 95%) on the same density scale as
    P/sum(P)/dr, clipped at 0.

    This is NOT a calibrated confidence interval, and it is not DeerLab's band:
      * It excludes the regularization bias, which is the dominant error at the
        peaks. Measured coverage of a nominal-95% band at the mode: 0.84 at the
        GCV alpha, 0.08 at alpha x2, ~0 at alpha x3 (the `alpha_factor` 2-4 that
        `deer_invert` recommends). Coverage gets WORSE as the data get cleaner,
        because the bias stops being masked by noise.
      * It is conservative only where NNLS pins P = 0 (3-12x too wide there) and
        anti-conservative at the modes.
      * It is ~1.6-2.4x narrower than DeerLab's covariance band on the same data
        (3.6x on the real ring-test traces) and has the opposite alpha
        dependence: this band NARROWS as alpha grows, DeerLab's is flat.
      * With engine='joint' it is narrower again by up to ~7x, because it holds
        the background and lambda fixed at their fitted values while the joint
        fit's own lambda/k scatter is the dominant uncertainty there.
    Treat it as a display aid for the noise level. For a coverage-honest interval
    use `deer_validate` (background-window ensemble) or the Mellin / multi-Gaussian
    Monte-Carlo bands."""
    K = np.asarray(K, float)
    F = np.asarray(F, float)
    P = np.asarray(P, float)
    n = K.shape[1]
    if L is None:
        L = regularization_matrix(n, 2)
    G = K.T @ K + (alpha**2)*(L.T @ L)
    try:
        Ginv = np.linalg.inv(G)
    except np.linalg.LinAlgError:
        Ginv = np.linalg.pinv(G)
    M = Ginv @ K.T
    resid = F - K @ P
    dof = max(float(K.shape[0]) - float(np.trace(K @ M)), 1.0)
    sigma2 = float(np.sum(resid**2)/dof)
    std = np.sqrt(np.maximum(sigma2*np.einsum('ij,ij->i', M, M), 0.0))
    scale = 1.0/((float(np.sum(P)) or 1.0)*dr)         # masses -> density
    dens = P*scale
    band = z*std*scale
    return np.maximum(dens - band, 0.0), dens + band


def deer_invert(t, V, r=None, bg_start=None, bg_end=None, dim=3.0, fit_dim=False,
                alpha=None, alphas=None, reg_order=2, nu_dd=NU_DD,
                scan_lcurve=True, method='gcv', engine='sequential',
                alpha_factor=1.0, pre_zero=None, reg_edges=True,
                clamp_alias=True, **kwargs):
    """Full DEER pipeline: background-correct V(t), build the kernel, invert to
    P(r) by Tikhonov + NNLS. When `alpha` is not supplied it is chosen
    automatically by `method` ('gcv' default, or 'curvature' for the classic
    L-corner) -- see `l_curve`.

    `alpha_factor` scales the auto-selected alpha (ignored when an explicit
    `alpha` is given). A factor > 1 (e.g. 2-4) reproduces the heavier hand-picked
    L-corner regularization the DeerAnalysis ring-test labs used to get smooth
    distributions (Schiemann et al., JACS 2021). It is a deliberate trade of bias
    for smoothness: P(r) is pulled measurably off the truth, and the `tikhonov_ci`
    band -- which propagates noise only -- NARROWS while the bias grows, so its
    coverage at the mode collapses (0.84 at factor 1, 0.08 at 2, ~0 at 3). Above
    factor 1 read the band as a noise scale, not as a confidence interval.

    `engine` selects how the background is handled:
      'sequential' -- fit the background on the tail window, divide it out, then
                       invert the form factor (this function; fast, the default).
      'joint'      -- fit background + modulation depth together with P(r) in one
                       separable-NLLS pass (`deer_invert_joint`; DeerLab-style,
                       more robust on short/shallow backgrounds).
      'mellin'     -- analytic integral Mellin transform (`deer_invert_mellin`;
                       model-free, no Tikhonov). Extra Mellin params (delta,
                       tau_max, n_tau, bg_engine, n_mc) pass through via **kwargs.
      'gauss'      -- parametric sum-of-N-Gaussians fit (`deer_invert_gauss`; N
                       chosen by AICc). Extra params (n_gauss, max_gauss, ic,
                       bg_engine, n_mc) pass through via **kwargs.

    `method` does double duty: it is the regularization selector ('gcv' / 'lcurve')
    on the Tikhonov engines and the SOLVER ('lsq' / 'mc') on 'gauss'. The two name
    sets are disjoint, so pass whichever the engine needs; a selector name on
    'gauss' leaves its default solver ('lsq') in place.

    `pre_zero` decides what happens to samples below the zero time -- 'even' keeps
    the ones that pass a mirror test, 'crop' drops them all, 'even_fold' averages
    each into its mirror twin; see `_crop_pre_zero`. None (the default) means the
    engine's own policy: 'even' on the Tikhonov paths, 'even_fold' on Mellin,
    'crop' on gauss. An explicit value is honoured on EVERY engine -- passing
    'crop' to Mellin used to be silently overridden.

    `t` in us, `r` in nm. With `scan_lcurve` (default) the regularization scan is
    always computed for display, even when an explicit `alpha` is given. Returns a dict:
    t, r, form_factor F(t), F_fit = K P, residuals, P (raw masses), P_norm
    (masses, sum = 1), P_density (P_norm / dr, integrates to 1), kernel, alpha,
    l_curve (when scanned), background result, lambda / k / dim, and engine.
    """
    # coefficients for the 'general' background (a/b/c/d, fit flag); flows through
    # kwargs so deer_validate and the engine dispatch carry it transparently.
    bg_params = kwargs.pop('bg_params', None)
    # `pre_zero_engine` is the older engine-only spelling; it still wins when given
    pz_engine = kwargs.pop('pre_zero_engine', None)
    if engine == 'joint':
        # the head parameters are named arguments there, so they arrive in kwargs
        head_kw = {k: kwargs.pop(k) for k in
                   ('head_level', 'head_cap', 'head_ratio_max') if k in kwargs}
        return deer_invert_joint(t, V, r=r, bg_start=bg_start, bg_end=bg_end,
                                 dim=dim, fit_dim=fit_dim, alpha=alpha,
                                 alphas=alphas, reg_order=reg_order, nu_dd=nu_dd,
                                 method=method, scan_lcurve=scan_lcurve,
                                 alpha_factor=alpha_factor,
                                 pre_zero=(pre_zero or 'even'),
                                 reg_edges=reg_edges, clamp_alias=clamp_alias,
                                 echo_head=kwargs.pop('echo_head', False),
                                 **head_kw)
    if engine == 'mellin':
        return deer_invert_mellin(t, V, r=r, bg_start=bg_start, bg_end=bg_end,
                                  dim=dim, fit_dim=fit_dim, nu_dd=nu_dd,
                                  bg_params=bg_params,
                                  pre_zero=(pz_engine or pre_zero or 'even_fold'),
                                  clamp_alias=clamp_alias, **kwargs)
    if engine == 'gauss':
        # `method` is the alpha selector for the regularized engines and the SOLVER
        # for this one; the two name sets are disjoint, so a caller passing a solver
        # name means it. Without this the gauss solver never arrived and
        # method='mc' silently ran 'lsq' -- the estimator, not just the search.
        if method in ('lsq', 'mc'):
            kwargs['method'] = method
        return deer_invert_gauss(t, V, r=r, bg_start=bg_start, bg_end=bg_end,
                                 dim=dim, fit_dim=fit_dim, nu_dd=nu_dd,
                                 bg_params=bg_params,
                                 pre_zero=(pz_engine or pre_zero or 'crop'),
                                 clamp_alias=clamp_alias, **kwargs)
    _require_scipy()
    t, V, _n_pre = _crop_pre_zero(t, V, policy=(pre_zero or 'even'))
    r = default_r_axis() if r is None else np.asarray(r, float)
    r, r_alias = _apply_alias_floor(t, r, clamp=clamp_alias, nu_dd=nu_dd)
    if bg_start is None:
        bg_start = t[0] + 0.5*(t[-1] - t[0])
    if engine == 'none':          # no intermolecular background (B=1); fit lambda only
        bg = _no_background(t, V, bg_start=bg_start, bg_end=bg_end)
    elif engine == 'general':     # general empirical background a + b*t + c*d^t
        bg = background_general(t, V, bg_start, bg_end=bg_end, **(bg_params or {}))
    else:
        bg = background_fit(t, V, bg_start, bg_end=bg_end, dim=dim, fit_dim=fit_dim)
    F = bg['form_factor']
    K = dipolar_kernel(t, r, nu_dd=nu_dd)
    L = regularization_matrix(len(r), reg_order, include_edges=reg_edges)
    if alphas is None:
        # wide grid (1e-4 .. 1e3): GCV needs room above the old 1e1 ceiling to
        # find its true minimum, which for well-separated peaks sits at alpha~1e2.
        alphas = np.logspace(-4, 3, 36)
    lc = l_curve(K, F, alphas, L, method=method) if (scan_lcurve or alpha is None) else None
    if alpha is None:
        alpha = lc['alpha_opt']*float(alpha_factor)
        P = lc['P'] if alpha_factor == 1.0 else tikhonov_nnls(K, F, alpha, L)
    else:
        P = tikhonov_nnls(K, F, alpha, L)
    F_fit = K@P
    P_norm = _normalize_masses(P)
    dr = float(r[1] - r[0]) if len(r) > 1 else 1.0
    P_density = P_norm/dr
    P_lower, P_upper = tikhonov_ci(K, F, alpha, P, L=L, dr=dr)
    _flag_bg_start_early(bg, r, P_density, nu_dd=nu_dd)
    _flag_not_deer_like(bg)
    return {'t': t, 'r': r, 'form_factor': F, 'F_fit': F_fit,
            'residuals': F - F_fit, 'P': P, 'P_norm': P_norm,
            'P_density': P_density, 'P_lower': P_lower, 'P_upper': P_upper,
            'kernel': K, 'alpha': float(alpha), 'r_alias': float(r_alias), 'ci_kind': 'noise',
            'l_curve': lc, 'background': bg, 'lambda': bg['lambda'],
            'k': bg['k'], 'dim': bg['dim'],
            'engine': engine if engine in ('none', 'general') else 'sequential'}


def deer_invert_joint(t, V, r=None, bg_start=None, bg_end=None, dim=3.0,
                      fit_dim=False, alpha=None, alphas=None, reg_order=2,
                      nu_dd=NU_DD, method='gcv', scan_lcurve=True,
                      alpha_factor=1.0, pre_zero='even', reg_edges=True,
                      clamp_alias=True, echo_head=False, head_level=0.60,
                      head_cap=0.35, head_ratio_max=1.25):
    """DEER inversion with a *joint* (separable-NLLS / variable-projection) fit of
    the background and modulation depth together with the regularized non-negative
    P(r) -- the strategy DeerLab uses. More robust than the sequential
    'fit background, then invert' pipeline (`deer_invert`) on real traces with
    short or shallow backgrounds, where the tail fit and the inversion are coupled.

    Model:  V(t) = B(t) * [ (1 - lam) + lam * (K P)(t) ],  B(t) = exp(-(k|t|)^(d/3)).

    The background + modulation depth are fit by `joint_background` (shared with the
    Mellin engine): the decay rate k (and d when `fit_dim`) is the nonlinear unknown,
    lam is *pinned* to the tail baseline of V/B, and the rate is fit jointly with a
    coarse non-negative P(r) on a distance grid TRUNCATED at the trace-supported
    r_max. Truncating that grid is what breaks the background / long-r degeneracy:
    on the full r grid a gentle (few-percent-over-the-trace) background can be
    reproduced by spurious long-r P(r) mass instead, so an unconstrained rate search
    collapses k -> 0 and leaves residual curvature in F that broadens P(r). (An
    earlier version fit the rate here on the full grid and fell into exactly that
    trap, returning a flat background even on traces with a real shallow one and
    costing ~0.02 overlap at low noise on the synthetic benchmark.) Pinning lam
    removes the depth degeneracy. `bg_start`/`bg_end` set the baseline window.

    The full-resolution non-negative P(r) then follows from K P = (V/B - (1-lam))/lam
    by Tikhonov + NNLS, the regularization weight chosen by GCV on the fitted-
    background form factor (the same `l_curve` selection as `deer_invert`). Same
    return dict as `deer_invert`, with engine='joint'.

    `echo_head` (default OFF) replaces the echo top with an even parabola fitted to
    the trace's own even part -- F is even about t0, so the head carries far fewer
    degrees of freedom than it has samples, and this denoises the highest-leverage
    part of the trace. Guarded (see `_echo_head_solve`) it is worth **+0.0016 overlap
    (t = 3.2)** over 756 synthetic traces on top of the edge-closed operator, and the
    guard is what makes it safe on the broad real traces where the unguarded head
    moved the mean distance +0.072 nm. Note the value has fallen as the defects it was
    partly compensating for were fixed: +0.0046 standalone, +0.0033 once `pre_zero`
    kept the mirrored samples, +0.0016 once `reg_edges` closed the operator's ends --
    all three suppress the same short-r/edge pile-up. It costs a second regularization
    scan when it fires, so it is opt-in rather than default.
    `head_level` sets the head width (0.60 = the fitted parabola falls to 0.60),
    `head_cap` bounds it, `head_ratio_max` is the guard threshold. The result carries
    an `echo_head` dict: applied, delta, r_eff, r_ratio.

    Caveat on the uncertainty band: `P_lower`/`P_upper` come from `tikhonov_ci`,
    which conditions on the FITTED background and lambda. Here those are themselves
    fitted, and their scatter dominates -- measured up to 7x too narrow versus the
    Monte-Carlo spread, where the same formula is honest to ~1.3x in the sequential
    engine on the same data (`ci_kind` = 'noise_fixed_bg' marks this). The
    background's own reliability flags (`lambda_clamped`, `tail_abs_F`,
    `k_disagrees` -- see `joint_background`) are the ones to check before trusting
    lambda or a distance from this engine.
    """
    _require_scipy()
    t, V, _n_pre = _crop_pre_zero(t, V, policy=pre_zero)
    r = default_r_axis() if r is None else np.asarray(r, float)
    r, r_alias = _apply_alias_floor(t, r, clamp=clamp_alias, nu_dd=nu_dd)
    K = dipolar_kernel(t, r, nu_dd=nu_dd)
    L = regularization_matrix(len(r), reg_order, include_edges=reg_edges)
    if alphas is None:
        alphas = np.logspace(-4, 3, 24)

    # Background + modulation depth from the capped-grid, lambda-pinned joint fit
    # (`joint_background` -- the SAME background the Mellin engine uses). Fitting
    # the decay rate on a TRUNCATED distance grid is what breaks the background /
    # long-r degeneracy: on the FULL r grid a gentle (few-percent-over-the-trace)
    # background can be reproduced by spurious long-r P(r) mass instead, so an
    # unconstrained rate search collapses k -> 0 and leaves residual curvature in F
    # that broadens P(r) (the old scalar-k-search behaviour here -- it returned a
    # flat background even on traces with a real shallow one, costing ~0.02 overlap
    # at low noise). The capped fit recovers the true shallow k, giving a clean
    # F -> 0 and a sharper, better-resolved P(r). The lambda pin (tail baseline)
    # also removes the depth degeneracy. bg_start/bg_end set the baseline window.
    bg = joint_background(t, V, bg_start=bg_start, bg_end=bg_end, dim=dim,
                          fit_dim=fit_dim, nu_dd=nu_dd)
    Vn, B, lam, k, d = bg['V_norm'], bg['B'], bg['lambda'], bg['k'], bg['dim']
    F = bg['form_factor']

    # regularization weight on the fitted-background form factor (F(0)=1)
    lc = (l_curve(K, F, alphas, L, method=method)
          if (scan_lcurve or alpha is None) else None)
    alpha_use = float(alpha) if alpha is not None else lc['alpha_opt']*float(alpha_factor)
    if alpha is None and alpha_factor == 1.0 and lc is not None:
        P_masses = lc['P']                         # reuse the scan solution
    else:
        P_masses = tikhonov_nnls(K, F, alpha_use, L)
    dr = float(r[1] - r[0]) if len(r) > 1 else 1.0
    head = {'applied': False, 'requested': bool(echo_head), 'delta': None,
            'r_eff': None, 'r_ratio': None}
    if echo_head:
        F, P_masses, lc, alpha_use, head = _echo_head_solve(
            t, F, K, L, r, dr, alphas, method, alpha, alpha_factor, scan_lcurve,
            P_masses, lc, alpha_use, head_level, head_cap, head_ratio_max, nu_dd)
    P_norm = _normalize_masses(P_masses)
    F_fit = K@P_masses                                 # the solved masses, as deer_invert
    P_lower, P_upper = tikhonov_ci(K, F, alpha_use, P_masses, L=L, dr=dr)
    _flag_bg_start_early(bg, r, P_norm/dr, nu_dd=nu_dd)
    _flag_not_deer_like(bg)
    return {'t': t, 'r': r, 'form_factor': F, 'F_fit': F_fit,
            'residuals': F - F_fit, 'P': P_masses, 'P_norm': P_norm,
            'P_density': P_norm/dr, 'P_lower': P_lower, 'P_upper': P_upper,
            'kernel': K, 'alpha': float(alpha_use),
            'ci_kind': 'noise_fixed_bg', 'echo_head': head,
            'r_alias': float(r_alias),
            'l_curve': lc, 'background': bg, 'lambda': lam,
            'k': float(k), 'dim': float(d), 'engine': 'joint'}


# --------------------------------------------------------------------------- #
#  Analytic Mellin-transform inversion (Matveeva/Nekrasov/Maryasov,
#  Phys. Chem. Chem. Phys. 2017, doi 10.1039/C7CP04059H)
# --------------------------------------------------------------------------- #
#
# A model-free, regularization-light alternative to Tikhonov. Writing the
# (background-corrected, normalized) form factor as a multiplicative convolution
# over the dipolar variable w = 2*pi*nu_dd / r^3,
#
#     F(T) = \int_0^inf p(w) phi(w T) dw ,   phi(u) = \int_0^1 cos(u(1-3x^2)) dx ,
#
# the Mellin transform separates the variables: with V~(s) = Mellin{F}, Phi(s) =
# Mellin{phi} and P(s) = Mellin{p}, one has V~(s) = P(1-s) Phi(s), hence
# P(s) = V~(1-s) / Phi(1-s). Evaluating on the critical line s = 1/2 + i*tau and
# using that F and phi are real (so the (1-s) image is the conjugate of the s
# image), P(1/2 + i tau) = conj( V~(1/2+i tau) / Phi(1/2+i tau) ); the inverse
# Mellin transform then gives p(w) directly, and the Jacobian maps it to f(r).
#
# Two ingredients are computed cleanly here rather than via the paper's 3F3
# hypergeometric appendix:
#
#  * Kernel image Phi(s).  Swapping the order of integration,
#        Phi(s) = Gamma(s) cos(pi s/2) \int_0^1 |1 - 3 x^2|^{-s} dx ,
#    using \int_0^inf u^{s-1} cos(b u) du = Gamma(s) cos(pi s/2) / b^s. The
#    remaining x-integral, singular (integrable) at x0 = 1/sqrt(3), splits under
#    two substitutions into a closed Beta-function term plus a smooth one:
#        \int_0^{x0} (1-3x^2)^{-s} dx = x0 (sqrt(pi)/2) Gamma(1-s)/Gamma(3/2-s)
#                                                              [x = x0 sin th],
#        \int_{x0}^1 (3x^2-1)^{-s} dx = x0 \int_0^{arccosh sqrt3} sinh(u)^{1-2s} du
#                                                              [x = x0 cosh u].
#    The x-integral converges only for Re s < 1 (|1-3x^2| ~ 2 sqrt3 |x-x0| at x0);
#    both pieces above are its analytic continuation, and the poles of Gamma(1-s)
#    cancel against the zeros of cos(pi s/2). On the critical line the sinh
#    integrand has unit MODULUS, but its phase -2 tau ln sinh(u) turns over ever
#    faster as u -> 0, so the plain grid at `n_u` converges only as O(1/n_u)
#    (~2.4e-2 relative at tau = 30; ~1e-4 nm on a recovered mean distance).
#
#  * Signal image V~(s).  Direct numeric Mellin of F(T) is hard near T=0, where
#    cos/sin(tau ln T) oscillate ever faster. Following the paper, split at a
#    small delta: on [0, delta] take F ~ F(0) and integrate analytically
#    (\int_0^delta T^{-1/2+i tau} dT = delta^{1/2+i tau}/(1/2 + i tau)); on
#    [delta, Tmax] substitute u = ln T so e^{i tau ln T} -> e^{i tau u} has a
#    *constant* frequency tau, and integrate F(e^u) e^{u/2} e^{i tau u} on a log-T
#    grid. delta is the lone regularizing parameter; the practical estimate is
#    F(delta) ~ 0.95 (the paper's recommendation).
#
# Noise enters f(r) additively (the whole chain is linear) and groups at small r
# (the technique's signature), so the recovered density is unbiased but spiky at
# short distances; it does not broaden or merge true peaks the way Tikhonov can.

def mellin_kernel_spectrum(tau, n_u=512):
    """Mellin image Phi(1/2 + i*tau) of the orientation-averaged dipolar kernel
    phi(u) = \\int_0^1 cos(u(1-3x^2)) dx, on the critical line. Vectorized over
    `tau`. Closed-form (Gamma ratio) + smooth quadrature; see section header."""
    _require_scipy()
    from scipy.special import gamma as cgamma
    tau = np.asarray(tau, dtype=float)
    s = 0.5 + 1j*tau
    x0 = 1.0/np.sqrt(3.0)
    # left piece [0, x0]: closed form via x = x0 sin(theta) -> Beta function
    left = x0*(np.sqrt(np.pi)/2.0)*cgamma(1.0 - s)/cgamma(1.5 - s)
    # right piece [x0, 1]: x = x0 cosh(u) -> x0 * \int_0^u1 sinh(u)^{1-2s} du,
    # integrand bounded (|sinh^{1-2s}| -> 1 as u->0 on the line); smooth grid.
    u1 = np.arccosh(np.sqrt(3.0))
    u = np.linspace(0.0, u1, int(n_u))
    u[0] = u[1]*1e-9                                   # avoid log(0); ~zero weight
    log_sh = np.log(np.sinh(u))
    integ = np.exp((1.0 - 2.0*s)[:, None]*log_sh[None, :])
    right = x0*_trapz(integ, u, axis=1)
    I = left + right
    return cgamma(s)*np.cos(np.pi*s/2.0)*I


def mellin_signal_spectrum(t, F, tau, delta, F0=1.0, du=0.02, parabolic=True,
                           fit_level=0.80, rel_noise=0.0):
    """Mellin image V~(1/2 + i*tau) of the form factor F(T), via the delta-split
    of doi 10.1039/C7CP04059H. `t` in the kernel unit (us), only T > 0 used; F is
    normalized to F(0) = `F0` (~1). `delta` is the split point (same unit as t);
    the [delta, Tmax] part is integrated on a log-T grid of step `du` (chosen to
    resolve the constant post-substitution frequency tau, so du < ~pi/max|tau|).
    Vectorized over `tau`.

    On [0, delta] the integral is analytic. The form factor has a *parabolic* echo
    top F(T) ~ F0 + b T^2 (it is even in T with negative curvature), so with
    `parabolic` the [0,delta] term keeps that quadratic instead of assuming F
    constant -- this removes a systematic error in the recovered F_fit right at the
    echo (the 'thin parabola' near t=0) and lets `delta` be widened:
        int_0^delta (F0 + b T^2) T^{s-1} dT = F0 delta^s/s + b delta^{s+2}/(s+2).
    The curvature b is least-squares fit over a widened low-T window (out to where
    F has fallen to `fit_level`*F0, and never narrower than three positive samples
    so a coarse step cannot silently drop the term back to the constant-F split).
    Set parabolic=False for the original constant-F split.

    `rel_noise` (sig_e/lambda) raises that three-sample floor to nine. F carries the
    1/lambda-amplified electrical noise, so on a noisy shallow-modulation trace a
    three-sample window fits the curvature to noise (measured |b| ~ 560 against a
    noise-only scatter of ~230) and the analytic term then holds the forward fit
    ABOVE the data across the whole echo top. The floor must NOT be raised
    unconditionally: on clean data the parabola is only valid very near the top, and
    forcing nine samples fits b beyond that (measured on real traces: early-time
    residual up to 6.6x worse, R2 -0.015, one reported peak moved 1.40 nm). Widening
    it where the noise demands it repairs the forward fit (-46% early residual on the
    case it was found on) but does NOT improve the recovered P(r) there -- the wrong
    curvature had been acting as an accidental regularizer, and removing it costs
    ~0.10 overlap on that case. At that noise the engine is outside its usable range
    either way."""
    t = np.asarray(t, dtype=float)
    F = np.asarray(F, dtype=float)
    tau = np.asarray(tau, dtype=float)
    pos = t > 0
    Tp, Fp = t[pos], F[pos]
    order = np.argsort(Tp)
    Tp, Fp = Tp[order], Fp[order]
    s = 0.5 + 1j*tau
    analytic = F0*delta**s/s                            # delta^{1/2+i tau}/(1/2+i tau)
    if parabolic and len(Tp) >= 3:                      # + parabolic curvature term
        f0 = float(Fp[0]) or F0
        below = np.where(Fp < fit_level*f0)[0]
        wfit = float(Tp[below[0]]) if len(below) else float(Tp[-1])
        n_min = 3 if float(rel_noise) < 0.09 else 9    # see the docstring
        msk = Tp <= max(wfit, delta, float(Tp[min(n_min - 1, len(Tp) - 1)]))
        if int(np.count_nonzero(msk)) >= 3:
            Tw, Fw = Tp[msk], Fp[msk]
            q = float(np.sum(Tw**4))
            if q > 0:
                b = float(np.sum(Tw**2*(Fw - F0))/q)
                analytic = analytic + b*delta**(s + 2)/(s + 2)
    Tmax = float(Tp[-1])
    if Tmax <= delta:
        return analytic
    u_lo, u_hi = np.log(delta), np.log(Tmax)
    n_u = max(64, int((u_hi - u_lo)/max(du, 1e-6)) + 1)
    u = np.linspace(u_lo, u_hi, n_u)
    Fu = np.interp(np.exp(u), Tp, Fp)                  # clamps below first sample
    g = Fu*np.exp(0.5*u)                               # \int g(u) e^{i tau u} du
    numeric = _trapz(g[None, :]*np.exp(1j*np.outer(tau, u)), u, axis=1)
    return analytic + numeric


def mellin_inverse(P_tau, tau, w):
    """Inverse Mellin transform on the line s = 1/2 + i*tau back to p(w):
    Re[p(w)] = (1/2pi) w^{-1/2} \\int Re[P(tau) e^{-i tau ln w}] dtau. `P_tau` is
    P(1/2 + i tau) sampled on `tau`; returns the real p(w) for each w."""
    w = np.asarray(w, dtype=float)
    lw = np.log(w)
    integ = _trapz(P_tau[None, :]*np.exp(-1j*np.outer(lw, tau)), tau, axis=1)
    return (1.0/(2.0*np.pi))*w**(-0.5)*np.real(integ)


# Reliability keys that describe the background fit that PRODUCED them. An engine
# that re-fits the background moves these under `background['prep']` instead of
# shipping them beside its own lambda/k, where they read as verdicts on a fit they
# never saw. They are moved, never recomputed: recomputing `k_ratio` on a refitted
# rate is a measured regression (real sample3_labA 1.003 -> 0.435, which crosses
# the < 0.5 gate and starts warning on a healthy trace).
_PREP_BG_KEYS = ('lambda_raw', 'lambda_clamped', 'lambda_degenerate',
                 'tail_abs_F', 'k_ref', 'k_ratio', 'k_disagrees',
                 'bg_drop', 'bg_flat', 'conc_implied_uM', 'conc_implausible',
                 'k_at_bound', 'k_fit_failed', 'rmax_cap')


def joint_background(t, V, bg_start=None, bg_end=None, dim=3.0, fit_dim=False,
                     nu_dd=NU_DD, n_r=60, rate_alpha=1.0, lam_pin_frac=0.5,
                     prep_only=False):
    """Joint (DeerLab-style) intermolecular background returning ONLY the
    background (same dict shape as `background_fit`). Fits the decay rate k (and d
    when `fit_dim`) together with a non-negative P(r), with the modulation depth
    lambda pinned to the tail baseline of V/B -- the degeneracy-breaking background
    fit shared by BOTH inversion engines (`deer_invert_joint` for Tikhonov and
    `deer_invert_mellin` for Mellin call this), stripped of the final full-
    resolution inversion / L-curve. The rate is fit on a coarse internal distance
    grid (`n_r`) at a fixed regularization (`rate_alpha`): k and lambda are
    insensitive to the P(r) resolution, so this is ~30x faster than a full joint
    inversion, and re-runnable per background-start during Mellin validation.

    Hardened against the short-bg_end collapse: the lambda pin uses the full
    available tail [bg_start, t_max] rather than [bg_start, bg_end], so k is
    essentially independent of bg_end and cannot slide to a spurious near-flat
    background when bg_end is pulled in (see the inline note). bg_end here only
    seeds kref via the sequential `background_fit`.

    The rate is fit on the trace-supported distance cap r_max ~ 5*(Tmax/2)^(1/3)
    (the DeerAnalysis rule), which keeps k determined on short single-peak traces.
    An earlier version also fit a wider cap and preferred it unless the background
    collapsed toward flat; that discrete guard bifurcated on ~10 ns of bg_start
    (0.03% in the objective, 19x in k) and was bit-identical to the tight cap on
    the long-r family it was meant to protect, so it was removed.

    Reliability keys in the returned dict (the pin can fail silently otherwise):
    `lambda_raw` / `lambda_clamped` (the raw pin estimate and whether it hit the
    [0.02, 0.95] clamp), `tail_abs_F` (mean |F| over the pin window -- the pin only
    forces mean F = 0 there, so mean |F| above ~0.05 says the tail has NOT decayed
    and lambda is a guess: measured 6.6x low on a 1 us trace of a 4.5 nm pair),
    `k_ref` / `k_ratio` / `k_disagrees` (the sequential tail-fit rate and how far
    the joint rate sits from it -- a disagreement between the two background routes,
    NOT a reliability verdict: measured 56 % detection at a 45 % false-alarm rate,
    and structurally blind to an early background window because both routes then
    absorb the same dipolar decay; it is also SUPPRESSED when there is no background
    to compare -- see `bg_flat`), `bg_drop` / `bg_flat` (the fraction by which the
    fitted background decays across the whole trace, and whether that is below 1 %.
    k_ratio is a ratio of two rates and swings freely when both sit near their
    floor, so on a flat-background trace it fired on nothing: with k = 0 the joint
    rate lands at ~5e-5 and the warning read "0.0x the sequential tail-fit rate".
    A routine background decays ~10 % over a 2 us trace, ten times the threshold),
    `k_at_bound` (k landed on an edge of its [kref/100, kref*100] bracket, which
    happens when kref itself collapses and means k carries no information),
    `k_fit_failed` (the rate fit raised or returned a non-finite k, so the reported
    k is the SEQUENTIAL kref and `k_ratio` is 1.0 by construction -- without this
    the fallback looks like the two routes agreeing exactly), and
    `conc_implied_uM` / `conc_implausible` --
    the spin concentration the fitted rate implies, k = 9.974e-4 * C * lambda.
    Flagged above 1000 uM, which no spin-labelled DEER sample reaches: 43 %
    detection at a 1 % false-alarm rate, so it is the specific one. The SENSITIVE
    detector for that failure is `bg_start_early` (92 % / 23 %), which every engine
    that fits a background records on this dict after its inversion, via
    `_flag_bg_start_early`. Any of these firing raises a RuntimeWarning.

    Set `prep_only=True` when the caller re-fits this background rather than
    reporting it (the multi-Gaussian `lsq` engine does): the warning then says the
    reliability keys describe the STARTING estimate. That caller also moves the
    keys under `background['prep']` -- see `_PREP_BG_KEYS`.
    """
    _require_scipy()
    from scipy.optimize import least_squares, minimize_scalar
    t = np.asarray(t, float)
    V = np.asarray(V, float)
    V = V/_echo_top(t, V)                              # normalize V(0) = 1 (robust)
    Tmax = float(np.max(np.abs(t))) or 1.0
    if bg_start is None:
        bg_start = t[0] + 0.6*(t[-1] - t[0])
    # Pin lambda over the FULL available tail [bg_start, t_max], NOT [bg_start,
    # bg_end]. lambda is the asymptotic modulation level and is best estimated
    # from the longest decayed tail. A short bg_end gives a biased pin and lets
    # the rate fit slide down the shallow-k branch of the background/long-r
    # degeneracy (k -> ~0): the background then leaves a slow residual in the form
    # factor that Tikhonov hides as long-r mass but the Mellin kernel (phi -> 0)
    # cannot represent, collapsing the Mellin fit. Using the full tail makes k
    # essentially independent of bg_end. (bg_end here only seeds kref via the
    # sequential background_fit.)
    mask = t >= bg_start
    if int(mask.sum()) < 3:                            # bg_start too late: latter half
        mask = t >= (t[0] + 0.5*(t[-1] - t[0]))
    # lambda is the ASYMPTOTIC baseline (F -> 0). Pinning mean(F) = 0 over the
    # whole tail biases it high when a broad/long-r component has not decayed
    # (mean F > 0 there), underestimating lambda and pushing the rate fit to a
    # too-steep k -- a residual tail pedestal the Mellin engine cannot represent
    # (a small systematic droop). Pin over the LATER part of the tail (last
    # `lam_pin_frac`), which is more decayed, to reduce that bias. The rate-fit
    # residual (vss) still spans the whole trace.
    if 0.0 < lam_pin_frac < 1.0:
        tt = t[mask]
        cut = (tt[0] + (1.0 - lam_pin_frac)*(tt[-1] - tt[0])) if len(tt) else bg_start
        pin_mask = mask & (t >= cut)
        if int(pin_mask.sum()) < 3:
            pin_mask = mask
    else:
        pin_mask = mask
    bg0 = background_fit(t, V, bg_start, bg_end=bg_end, dim=dim, fit_dim=fit_dim)
    k0, d0 = bg0['k'], bg0['dim']
    kref = max(float(k0), 1e-4)

    def lam_of(B):
        return min(max(1.0 - float(np.mean((V/B)[pin_mask])), LAM_MIN), LAM_MAX_PINNED)

    def _fit_rate(rmax_cap):
        """Fit the background rate k (and d when fit_dim) jointly with a coarse
        non-negative P(r) on a distance grid truncated at rmax_cap. Returns
        (k, d, at_bound, failed) -- at_bound when k lands on an edge of the
        [kref/100, kref*100] search bracket, where it carries no information, and
        failed when the optimizer raised or returned a non-finite rate and the
        SEQUENTIAL kref is returned in its place. That fallback is silent
        otherwise: k == kref makes k_ratio exactly 1.0, which reads as the two
        background routes agreeing perfectly when in fact only one of them ran."""
        rc = np.linspace(1.5, float(rmax_cap), int(n_r))
        Kc = dipolar_kernel(t, rc, nu_dd=nu_dd)
        Lc = regularization_matrix(len(rc), 2)

        def vss(k, d):
            B = np.exp(-(k*np.abs(t))**(d/3.0))
            lam = lam_of(B)
            F = (V/B - (1 - lam))/lam
            P = tikhonov_nnls(Kc, F, rate_alpha, Lc)
            return float(np.sum((V - B*((1 - lam) + lam*(Kc@P)))**2))

        if fit_dim:
            def resid(theta):
                k = abs(theta[0]); d = min(max(theta[1], 1.0), 6.0)
                B = np.exp(-(k*np.abs(t))**(d/3.0))
                lam = lam_of(B)
                F = (V/B - (1 - lam))/lam
                P = tikhonov_nnls(Kc, F, rate_alpha, Lc)
                return V - B*((1 - lam) + lam*(Kc@P))
            try:
                sol = least_squares(resid, [kref, d0],
                                    bounds=([0.0, 1.0], [np.inf, 6.0]), max_nfev=120)
                kk, dd = abs(sol.x[0]), min(max(sol.x[1], 1.0), 6.0)
                if not (np.isfinite(kk) and np.isfinite(dd)):
                    return kref, d0, False, True
                return kk, dd, False, False
            except Exception:
                return kref, d0, False, True
        lo_lk, hi_lk = np.log(kref/100.0), np.log(kref*100.0)
        try:
            sol = minimize_scalar(lambda lk: vss(np.exp(lk), d0),
                                  bounds=(lo_lk, hi_lk),
                                  method='bounded', options={'xatol': 3e-2})
            at_bound = bool(min(abs(sol.x - lo_lk), abs(hi_lk - sol.x)) < 5e-2)
            kk = float(np.exp(sol.x))
            if not np.isfinite(kk):
                return kref, d0, False, True
            return kk, d0, at_bound, False
        except Exception:
            return kref, d0, False, True

    # rate fit on the trace-supported cap only (see the docstring)
    rmax_tight = float(np.clip(5.0*(Tmax/2.0)**(1.0/3.0), 3.0, 8.0))
    k, d, k_at_bound, k_fit_failed = _fit_rate(rmax_tight)
    B = np.exp(-(k*np.abs(t))**(d/3.0))
    lam_raw = 1.0 - float(np.mean((V/B)[pin_mask]))
    lam = lam_of(B)
    F = (V/B - (1 - lam))/lam
    # the pin only fixes mean(F) = 0 over its window; mean|F| there is what says
    # whether the tail has actually decayed, i.e. whether lambda means anything
    tail_absF = float(np.mean(np.abs(F[pin_mask])))
    lam_clamped = not (LAM_MIN <= lam_raw <= LAM_MAX_PINNED)
    k_ratio = float(k)/kref if kref > 0 else float('nan')
    # `k_ratio` compares the joint rate with the SEQUENTIAL tail fit on the SAME
    # window. Measured over 1260 calibration cells it detects 56 % of the fits whose
    # mean distance is wrong by >0.05 nm but false-alarms on 45 % of the good ones --
    # against a 25 % base rate that lifts the odds to 29 %, i.e. it is nearly
    # uninformative on its own. In particular it CANNOT see an early background
    # window: there both fits absorb the same dipolar decay and agree on the same
    # wrong rate (k_ratio 0.81-0.91 while k itself was 10-33x the truth). Read it as
    # "the two background routes disagree", not as a reliability verdict; the flags
    # that detect the early-window failure are `conc_implausible` here and
    # `bg_start_early` on the engine result.
    #
    # A self-consistency variant -- refit the rate on the window's own second half
    # and compare -- was implemented and MEASURED at 21 % detection, then removed:
    # on a long-distance trace that second half is still inside the dipolar
    # evolution, so it fails in the same way for the same reason. Do not re-derive it.
    conc_implied = (float(k)/(9.974e-4*lam) if lam > 1e-6 else float('nan'))
    conc_implausible = bool(np.isfinite(conc_implied) and conc_implied > 1000.0)
    # a ratio of two rates says nothing when both are negligible: judge the decay
    def _bg_drop(rate):
        if not (np.isfinite(rate) and rate > 0):
            return 0.0
        return float(-np.expm1(-(rate*Tmax)**(d/3.0)))
    bg_drop = max(_bg_drop(float(k)), _bg_drop(kref))
    bg_flat = bool(bg_drop < 0.01)
    k_disagrees = bool(np.isfinite(k_ratio) and not bg_flat
                       and (k_ratio > 2.0 or k_ratio < 0.5))
    reasons = []
    if conc_implausible:
        reasons.append('the fitted rate implies a spin concentration of %.0f uM '
                       '(k = %.4g, lambda = %.3f), which is not a physical DEER '
                       'sample -- the background fit has absorbed the dipolar decay'
                       % (conc_implied, float(k), lam))
    if lam_clamped:
        reasons.append('the modulation depth hit the [%.2f, %.2f] clamp '
                       '(raw %.3g, used %.3f)'
                       % (LAM_MIN, LAM_MAX_PINNED, lam_raw, lam))
    if tail_absF > 0.05:
        reasons.append('the tail has not decayed under the lambda pin (mean|F| = '
                       '%.3g over the pin window), so lambda = %.3f is a guess'
                       % (tail_absF, lam))
    if k_disagrees and float(k0) <= 1e-4:              # kref sat on its floor
        reasons.append('the sequential tail fit found essentially no decay '
                       '(k = %.2g) where the joint fit gives k = %.4g'
                       % (float(k0), float(k)))
    elif k_disagrees:
        reasons.append('the joint decay rate k = %.4g is %.1fx the sequential '
                       'tail-fit rate %.4g' % (float(k), k_ratio, kref))
    if k_at_bound:
        reasons.append('the joint rate sat on an edge of its [kref/100, kref*100] '
                       'search bracket (k = %.4g, kref = %.4g), so it carries no '
                       'information' % (float(k), kref))
    if k_fit_failed:
        reasons.append('the joint rate fit did not return a usable k, so the '
                       'SEQUENTIAL tail-fit rate %.4g is reported in its place -- '
                       'this is not a joint background, and k_ratio is 1 by '
                       'construction rather than by agreement' % kref)
    if reasons:
        warnings.warn(
            ('DEER starting background needs checking: ' if prep_only else
             'DEER joint background needs checking: ') + '; '.join(reasons)
            + ('. The caller re-fits lambda and k from here, so read the reported '
               'values, not these; a later bg_start still moves the starting point.'
               if prep_only else
               '. Cross-check against engine=\'sequential\' and a later bg_start '
               'before quoting lambda or a distance.'), RuntimeWarning, stacklevel=2)
    return {'lambda': lam, 'lambda_raw': float(lam_raw),
            'lambda_clamped': bool(lam_clamped),
            'tail_abs_F': tail_absF, 'k_ref': float(kref),
            'k_ratio': k_ratio, 'k_disagrees': k_disagrees,
            'bg_drop': float(bg_drop), 'bg_flat': bg_flat,
            'conc_implied_uM': float(conc_implied),
            'conc_implausible': conc_implausible,
            'k_at_bound': bool(k_at_bound), 'k_fit_failed': bool(k_fit_failed),
            'rmax_cap': float(rmax_tight),
            'k': float(k), 'dim': float(d), 'A': float(1 - lam),
            'B': B, 'form_factor': F, 'V_norm': V, 't': t,
            'bg_start': float(bg_start),
            'bg_end': (None if bg_end is None else float(bg_end)), 'mask': mask}


def mellin_delta(t, F, level=0.95, floor=0.09, cap=0.12, floor_ratio=2.0,
                 rel_noise=0.0):
    """Practical split point delta: the first T > 0 where the form factor has
    fallen to `level` of F(0) (the paper's F(delta) ~ 0.95 estimate). Falls back
    to the first positive sample if F never drops that far.

    The raw F-level estimate is then clipped to [`floor`, `cap`] (in the kernel
    time unit, us). The floor widens a too-narrow analytic [0,delta] echo-top
    anchor -- the 'thin parabola' at t=0 -- which otherwise leaves the recovered
    F_fit top too steep and the short-r density unstable; the cap (~120 ns) stops
    a slow-decaying (long-r) trace from over-smoothing P(r) by handling too much
    of the modulation analytically. Both were tuned on the synthetic benchmark,
    whose peaks all lie between 3.0 and 4.3 nm.

    `floor_ratio` bounds how far the floor may stretch delta beyond the trace's
    OWN decay scale: delta is raised to at most `floor_ratio` * the raw crossing.
    Without it the floor is an absolute time, so for r0 <~ 2.5 nm -- where the
    raw crossing is a few times smaller than 90 ns -- it hands most of the first
    dipolar oscillation to a single parabola and the reconstruction collapses
    (measured overlap at r0 = 2.0 nm: 0.76 clamped vs 0.92 unclamped, noiseless;
    0.42 vs 0.64 at sigma 0.04). Above ~3 nm the raw crossing already exceeds
    floor/floor_ratio, so the clamp binds exactly as before and the tuned regime
    is unchanged. Set floor/cap to None to disable. The bounds are also clamped
    to the trace so delta never exceeds the last positive sample.

    `rel_noise` is the measured relative noise on F (sig_e/lambda). F carries the
    1/lambda-amplified electrical noise, so once that noise approaches the level
    drop (1 - `level`) the FIRST sample below the level is a noise dip rather than
    the decay, and `floor_ratio` -- which caps delta at floor_ratio times the raw
    crossing -- then locks delta onto that dip. The caller's noise-adaptive
    widening therefore runs BACKWARDS exactly where it is needed: measured on the
    synthetic benchmark at sigma 0.04 / lambda 0.20, the crossing collapsed from a
    true ~110 ns to 27 ns and delta with it (124 -> 41 ns), leaving the forward fit
    sitting above the data at short T (early-time residual 1.2-1.4x the Tikhonov
    fit on the same trace, against ~1.0x at delta 60-130 ns). So the crossing is
    read off an F smoothed over `w` samples, with w sized to keep the smoothed
    noise under half the level drop: w = 1 -- the identical, unsmoothed code path
    -- for rel_noise below ~0.09, which covers the whole tuned low-noise regime.
    Leave at 0 to disable. NOTE this repairs the forward fit, not the accuracy:
    the collapsed delta happened to sit at a better point of the overlap-vs-delta
    curve, so P(r) at that noise level is slightly worse, not better."""
    t = np.asarray(t, dtype=float)
    F = np.asarray(F, dtype=float)
    pos = t > 0
    Tp, Fp = t[pos], F[pos]
    order = np.argsort(Tp)
    Tp, Fp = Tp[order], Fp[order]
    if len(Tp) == 0:
        return 1e-3
    # w = 1 (no smoothing, bit-identical) until the noise can fake the crossing
    w = int(np.clip(round((2.0*float(rel_noise)/max(1.0 - level, 1e-3))**2), 1, 9)) | 1
    if w > 1 and len(Fp) > w:
        Fp_s = np.convolve(np.r_[np.full(w//2, Fp[0]), Fp, np.full(w//2, Fp[-1])],
                           np.ones(w)/w, mode='valid')
    else:
        Fp_s = Fp
    f0 = float(Fp_s[0]) or 1.0
    below = np.where(Fp_s < level*f0)[0]
    d_raw = float(Tp[below[0]]) if len(below) else float(Tp[0])
    d = d_raw
    if floor is not None:
        d = max(d, min(float(floor), float(floor_ratio)*d_raw))
    if cap is not None:
        d = min(d, float(cap))
    return float(min(d, Tp[-1]))                        # never past the last sample


def _tail_noise(t, y, frac=0.35, smooth_w=7):
    """Electrical white-noise level sigma from the decayed tail, by smoothing.

    Over the last `frac` of the t > 0 trace the dipolar signal is gone (only the
    smooth background + additive electrical noise remain), so sigma is the std of
    (y - moving-average(y)) there, corrected for the variance a width-`w` moving
    average removes: var(y - movavg) = sigma^2 (1 - 1/w). `mode='same'` zero-pads
    BOTH ends, so both convolution edges are excluded; on a trace too short for the
    tail window to hold four non-edge points the window is pulled back toward the
    middle rather than into the padding, and NaN is returned if even that fails.
    NaN means "cannot measure" and 0.0 means "measured zero" (a bit-constant tail,
    e.g. a clamped or zero-padded trace) -- callers must distinguish them: both
    disable the Monte-Carlo band, but only the second is a property of the data."""
    t = np.asarray(t, float); y = np.asarray(y, float)
    yp = y[t > 0]
    n = len(yp)
    if n < 12:
        return float('nan')
    w = int(max(3, smooth_w | 1))                       # odd window
    ys = np.convolve(yp, np.ones(w)/w, mode='same')
    resid = yp - ys
    hi = n - w                                          # drop the right conv edge
    lo = min(max(int(n*(1.0 - frac)), w), max(hi - 4, w))   # inside BOTH edges
    tail = resid[lo:hi]
    if len(tail) < 4:
        return float('nan')
    return float(np.std(tail))/np.sqrt(max(1.0 - 1.0/w, 1e-6))


def residual_whiteness(resid, max_lag=None):
    """Residual-whiteness goodness-of-fit diagnostic (DeerLab-style).

    An adequate DEER fit leaves a WHITE (uncorrelated) residual; a structured,
    *oscillating* residual is the hallmark of a distance distribution that has
    not captured all the dipolar modulation -- typically an over-smoothed (too
    broad) P(r) at an over-regularized cutoff, but also missing dipolar pathways
    or orientation selection. Such model inadequacy shows up as autocorrelation
    in the residual even when its amplitude already matches the noise level (so
    the discrepancy principle alone cannot see it). See Edwards & Stoll, J. Magn.
    Reson. 288 (2018) 58; Fabregas Ibanez et al., Magn. Reson. 1 (2020) 209
    (DeerLab reports exactly this via the Durbin-Watson statistic).

    Returns a dict:
      durbin_watson : DW = sum (e_i - e_{i-1})^2 / sum e_i^2, in [0, 4]; ~2 = white,
                      < 2 = positive autocorrelation (the oscillating-residual case),
                      > 2 = anti-correlation.
      acf1          : lag-1 autocorrelation r_1 = sum e_i e_{i-1} / sum e_i^2
                      (~ 1 - DW/2); 0 = white. The single headline number.
      acf, lags     : autocorrelation function vs lag (for an autocorrelogram).
      ci95          : +-1.96/sqrt(N), the 95% white-noise band for the ACF. It is
                      the band for RAW white noise; a fitted, regularized residual
                      has a different null distribution and sits slightly
                      anti-correlated, so `white` over-flags on that side.
      offset        : mean(e)/std(e) BEFORE the mean subtraction below. DW and the
                      ACF are computed on the demeaned residual, which is blind to
                      a constant pedestal from a mis-fitted lambda or background --
                      exactly the systematic this diagnostic is meant to catch. A
                      |offset| of order 1 is a bad fit however white it looks.
      white         : bool, |acf1| <= ci95 (residual consistent with white noise).
    """
    e = np.asarray(resid, float)
    e = e[np.isfinite(e)]
    n = int(len(e))
    if n < 4:
        return {'durbin_watson': float('nan'), 'acf1': float('nan'),
                'acf': np.array([1.0]), 'lags': np.array([0]),
                'ci95': float('nan'), 'offset': float('nan'), 'white': True}
    mu = float(e.mean())
    e = e - mu
    sd = float(np.std(e)) or 1e-30
    denom = float(np.sum(e*e)) or 1e-30
    dw = float(np.sum(np.diff(e)**2)/denom)
    if max_lag is None:
        max_lag = int(min(max(10, n//5), n - 1))
    lags = np.arange(0, int(max_lag) + 1)
    acf = np.array([float(np.sum(e[k:]*e[:n - k])/denom) for k in lags])
    ci95 = float(1.96/np.sqrt(n))
    return {'durbin_watson': dw, 'acf1': float(acf[1]) if len(acf) > 1 else 0.0,
            'acf': acf, 'lags': lags, 'ci95': ci95, 'offset': float(mu/sd),
            'white': bool(abs(acf[1] if len(acf) > 1 else 0.0) <= ci95)}


# Analytic kernel-integral constants I(s) = Phi(s)/(2 pi nu_dd)^s (Nekrasov,
# Matveeva, Syryamina, Agarkin & Bowman, Phys. Chem. Chem. Phys. 2026,
# DOI 10.1039/D5CP04144A; their Eqns. 5-6), with s = n/3 for the n-th moment.
_TAUMAX_REMOVED = ('noise_space', 'taumax_extend', 'extend_short_frac')

_MELLIN_I_S = {1: 4.31512, 2: 3.06158, 3: 2.77339, 4: 2.56993}


def distribution_moments(r, P):
    """Shape descriptors of a distance distribution P(r) on grid r (nm).

    From the non-central moments  M_n = int r^n P(r) dr  of the clipped,
    area-normalized density, returns the quantities most PDS work reports:
        mean   r0    = M1                       (mean distance, nm)
        width  dr    = sqrt(M2 - M1^2)          (rms width, nm)
        skew   gamma = (M3 - 3 M1 dr^2 - M1^3)/dr^3
    plus the raw m1..m4. Negative excursions (the signed Mellin output) are
    clipped before normalizing so these stay proper distribution moments. See
    Nekrasov et al., PCCP 2026 (DOI 10.1039/D5CP04144A), Eqns. 6-7 & 17."""
    r = np.asarray(r, float)
    p = np.clip(np.asarray(P, float), 0.0, None)
    area = float(_trapz(p, r))
    if not np.isfinite(area) or area <= 0:
        nan = float('nan')
        return {'mean': nan, 'width': nan, 'skew': nan,
                'm1': nan, 'm2': nan, 'm3': nan, 'm4': nan}
    p = p/area
    m1 = float(_trapz(r*p, r))
    m2 = float(_trapz(r**2*p, r))
    m3 = float(_trapz(r**3*p, r))
    m4 = float(_trapz(r**4*p, r))
    var = max(m2 - m1*m1, 0.0)
    dr = float(np.sqrt(var))
    skew = float((m3 - 3*m1*var - m1**3)/dr**3) if dr > 1e-9 else 0.0
    return {'mean': m1, 'width': dr, 'skew': skew,
            'm1': m1, 'm2': m2, 'm3': m3, 'm4': m4}


def moment_error_apriori(eps, dt, n_points, n=1):
    """A priori rms error of the n-th non-central moment M_n of P(r) from random
    noise alone -- the closed form of Nekrasov, Matveeva, Syryamina, Agarkin &
    Bowman, PCCP 2026 (DOI 10.1039/D5CP04144A), Eqn. 9, for uniform acquisition:

        ME_n = (eps * dt^s / I(s)) * sqrt( 1/4 + sum_{i=2}^{NT-1} i^{2(s-1)} )

    with s = n/3 and I(s) the analytic kernel integral (their Eqns. 5-6). It needs
    NO inversion and NO ground truth -- the precision of a moment is a property of
    the *acquisition* (noise level, step, length), because the additivity of the
    Mellin transform decouples the noise from the (unknown) distribution.

    Parameters
    ----------
    eps : float
        Per-point rms noise on the NORMALIZED form factor F(t) (F(0)=1). For a
        background-corrected trace with modulation depth lambda this is the raw
        trace noise amplified by 1/(lambda*B): eps ~ sigma_trace/lambda.
    dt : float
        Time step in NANOSECONDS (the constants I(s) are fixed for g=2 with the
        dipolar frequency in GHz, i.e. time in ns). Pass dt_us*1e3.
    n_points : int
        Number of dipolar-trace points (t >= 0).
    n : int
        Moment order (1..4). n=1 is the mean distance -- the robust one; its
        i^{-4/3} weight is dominated by the EARLY points, so ME_1 is nearly flat
        in n_points (extending the trace does not improve the mean distance).

    Returns
    -------
    float : ME_n in nm^n  (nm for the mean distance, n=1).

    Notes
    -----
    Against the paper's reported uniform-acquisition std(M1) = 0.0400 nm for
    eps=0.04, dt=24 ns, NT=231, this returns 0.0411 nm.

    ME_n is the propagated NOISE error of the linear Mellin moment integral and
    nothing else -- it carries no resolution and no regularization-bias term, so
    it is NOT a bound on the scatter of a recovered distance. Measured
    std(M1)/ME_1 over 200 Mellin inversions runs 0.97 (3.0 nm, sigma 0.15,
    NT=231) up to 2.64 (5.5 nm, sigma 0.30, NT=40), and once bias is included
    RMSE/ME_1 reaches ~40x on a trace too short to resolve the distance -- ME_1
    is smallest exactly where the answer is worst. Report it as a noise floor,
    not as an error bar."""
    n = int(n)
    if n not in _MELLIN_I_S:
        raise ValueError('moment order n must be 1..4')
    nt = int(n_points)
    if nt < 3 or eps <= 0 or dt <= 0:
        return float('nan')
    s = n/3.0
    I = _MELLIN_I_S[n]
    i = np.arange(2, nt, dtype=float)
    S = 0.25 + float(np.sum(i**(2.0*(s - 1.0))))      # alpha_1^2=(1/2)^2 + tail
    return float(eps*dt**s/I*np.sqrt(S))


def _nonneg_cumulative(f):
    """Closest non-negative density to a SIGNED one, by isotonic regression of its
    cumulative mass.

    A density is non-negative exactly when its cumulative is non-decreasing, so the
    isotonic least-squares fit of that cumulative is the projection onto the
    non-negative cone that stays closest to the data in the cumulative -- which is
    what determines distances. Pool-adjacent-violators does it in O(n).

    Two properties matter. It is the IDENTITY wherever the density is already
    non-negative, touching only the intervals where the cumulative runs backwards.
    And it CANCELS rather than deletes: the Mellin noise signature is a paired
    +spike/-dip, and pooling the pair leaves their small net instead of keeping the
    spike at full height, which is what clipping does -- and why clipping costs a
    far worse forward fit at the echo top, where that spike lives.
    """
    _require_scipy()
    f = np.asarray(f, float)
    if not np.any(f < 0.0):
        return f
    c = isotonic_regression(np.cumsum(f)).x
    return np.maximum(np.diff(c, prepend=0.0), 0.0)


def deer_invert_mellin(t, V, r=None, bg_start=None, bg_end=None, dim=3.0,
                       fit_dim=False, nu_dd=NU_DD, delta=None, tau_max=None,
                       n_tau=601, bg_engine='joint', bg_params=None,
                       n_mc=0, ci_z=1.96, seed=0,
                       taumax_method='penalty', wiener=0.0,
                       fit_rmin_abs=2.0, fit_rmin_width=0.5,
                       signed_fit=True, taper_short=True, pre_zero='even_fold',
                       clamp_alias=True,
                       **_ignored):
    """Model-free DEER inversion by the analytic integral Mellin transform
    (doi 10.1039/C7CP04059H). Background-corrects V(t), then recovers the distance
    distribution analytically: no Tikhonov, no NNLS, no L-curve. The only
    regularizing knob is the Mellin split point `delta` (auto = F(delta) ~ 0.95)
    together with the cutoff `tau_max`.

    `bg_engine` selects how the form factor is prepared, and it matters a lot here:
    the Mellin kernel phi(wT) -> 0, so the recovered density cannot represent any
    DC pedestal left in F by an imperfect background. A too-shallow background
    leaves a slowly-decaying offset that shows up as a near-constant gap between
    the data and the forward fit. 'joint' (default) fits the modulation depth and
    background together (lambda pinned to the tail baseline; `deer_invert_joint`)
    and gives a clean F -> 0; 'sequential' does the faster tail-window fit
    (`background_fit`) but can leave that pedestal on shallow backgrounds.

    `t` in us, `r` in nm. `tau` runs symmetrically over [-tau_max, tau_max] with
    `n_tau` points. `tau_max=None` -- the DEFAULT -- selects the cutoff
    automatically; pass a number only to pin it deliberately.
    tau_max IS the regularization knob here (it plays the role alpha plays in
    Tikhonov: Phi(tau) -> 0 at high |tau|, so truncation sets how much amplified
    noise reaches P(r)), and a pinned value regularizes by a constant regardless of
    the data's noise. The former default of 30.0 measured -0.173 mean overlap
    against auto over 756 catalogue traces (0.638 vs 0.812, winning on 0.9% of
    them, roughness 41x higher), so it is auto unless you say otherwise.

    `taumax_method='penalty'` is the only selector: minimize the forward-fit RMS
    regularized by a SYMMETRIC-NOISE penalty. The fit residual rmsF (RMS of
    F - F_fit over t > 0) falls as the cutoff captures the parabolic echo top, then
    sits on a broad noise-floor plateau; chasing its minimum over-extends and
    injects the noisy high-tau Mellin spectrum into P(r). That injected noise enters
    the area-normalized SIGNED density as paired +bump/-dip excursions, so the
    |negative area| `neg` measures it directly (symmetric: every spurious positive
    spike is balanced by a negative one under area normalization). Picks
    argmin(rmsF/min(rmsF) + neg): the ratio term forces an adequate fit (>= 1, large
    while the echo top is under-resolved), the neg term halts the extension once the
    fit plateaus and the cutoff would only add symmetric noise. Self-adapts: clean
    data plateaus late (sharp P(r) kept), noisy data accrues neg early (stays
    smooth). On the synthetic benchmark it beats the older discrepancy floor +
    leakage extension in both the no-background (mean overlap 0.922 -> 0.933) and
    with-background (0.828 -> 0.831) regimes, landing ~0.002-0.003 from the
    overlap-optimal oracle.

    The 'discrepancy' and 'lcurve' selectors, their `noise_space` /
    `taumax_extend` / `extend_short_frac` settings and the resolution extension were
    REMOVED: both lost to 'penalty' on the benchmark above and both were broken.
    The discrepancy threshold is floored at min(sigma_fit) so that it always accepts
    a candidate, which on 17 of 28 real traces made it argmin(sigma_fit) -- exactly
    the over-fit it was written to avoid -- and the L-curve scored curvature only on
    the interior candidates, so it could never return either end of the grid and had
    no fallback when the corner detector found none. Passing any of them now raises,
    rather than being swallowed by `**_ignored` and silently running 'penalty'.
    (The removed extension: after the discrepancy pick the
    cutoff was pushed UP while the spurious short-r leakage (mass in the bottom
    `extend_short_frac` of the r grid -- the Mellin noise signature) kept DROPPING,
    and stopped at the first increase. Self-adapts to noise: clean/low-noise data
    extended (sharper echo top, better-resolved bimodals -- e.g. a clean narrow
    Gaussian 0.92 -> 0.96 overlap), noisy data did not. The penalty subsumes it.)

    `wiener` (default 0 = OFF, opt-in) sets the strength of a Wiener-regularized
    inverse filter on the kernel-image division (see `_build`). The plain Mellin
    inverse 1/Phi(tau) amplifies noise where Phi is small (high |tau|), which the
    r-space Jacobian concentrates into a spurious SHORT-r spike that can steal the
    real peak on noisy bimodal traces; the Wiener filter conj(Phi)/(|Phi|^2 + eps)
    rolls that off, with eps scaled by the measured tail noise so it is a no-op on
    clean data and only suppresses noise-dominated (not signal) spectrum, leaving
    genuine short-r peaks intact. A value of ~0.12 works well at MODERATE noise
    (sigma ~0.02: it removes the short-r spike and recovers the true peak --
    benchmark overlap gains of +0.1 to +0.2, e.g. gauss_narrow_broad 0.68 -> 0.88).

    CAVEAT -- left OFF by default because, like the t0 cross-check, it is a net
    benchmark regression as a blanket default (mean overlap 0.853 -> 0.840). At
    EXTREME noise (sigma ~0.04) the recovered P(r) is dominated by zero-time and
    tau_max auto-selection instability, not by the inverse filter, and the Wiener
    term interacts with that selection to regress several cases. Enable it when the
    data are moderately noisy and the result shows the tell-tale short-r spike.

    With `n_mc` > 0 a Monte-Carlo confidence band is returned (additive-noise
    propagation): the white electrical-noise level `sig_e` is read from the
    decayed tail of V by smoothing (`_tail_noise`, returned as `noise_level`),
    n_mc realizations of that Gaussian noise are added to the smooth V fit and
    propagated through the *fixed* background to the form factor (so F inherits the
    realistic 1/(lam*B) amplification toward the tail, not a single stationary
    sigma), each is re-inverted, and the band is the per-distance STD across
    realizations: P_lower/P_upper = P_density -/+ ci_z*P_std (P_std also returned).
    ~100 realizations are typical.

    Returns the same dict shape as `deer_invert` (so the GUI and exporters are
    shared): t, r, form_factor, F_fit (forward kernel applied to the recovered
    density), residuals, P / P_norm / P_density. The Mellin density is kept
    *signed* and area-normalized (negative excursions, the propagated-noise
    signature at short r, are NOT clipped to zero -- so P(r) can dip below zero).
    The DISPLAYED P_density keeps every negative (they are genuine short-r noise
    and are not corrected), but with `taper_short` (default on) it is multiplied by
    the low-r taper before normalization -- so the taper DOES affect the reported
    P(r), not only the fit. The taper exists because the propagated noise piles
    into a spurious spike at short r (the r^-2.5 Jacobian, the visible "double peak
    near t=0"), which also makes the F_fit echo top decay too fast; a raised cosine
    attenuates it without deleting a genuine short-r peak, and the area
    re-normalization returns the stolen area to the real peaks. Its window is
    ABSOLUTE: it ramps from the grid bottom to at most `fit_rmin_abs` nm (the limit
    below which a DEER distance is not meaningful anyway) over at most
    `fit_rmin_width` nm, and vanishes on a grid starting above `fit_rmin_abs`. It
    used to be a fraction of the r range, which made the reported mean distance a
    function of the user's r_max (2.554 -> 3.170 nm on one trace over r_max 6 -> 20)
    and kept tapering into grids that already start above the unreliable region.
    F_fit is the forward kernel applied to those same tapered masses, which is why
    `signed_fit` reaches only the tau_max selector in that mode. With
    `taper_short=False` the reported density is the raw signed one and F_fit follows
    `signed_fit`: the clipped, low-r-tapered density (negatives would flip the t=0
    curvature into a spurious double peak) or the signed one. kernel,
    background, lambda / k / dim. Mellin-specific extras: engine='mellin', delta,
    tau_max, auto_taumax, sigma_fit, sigma_noise, neg_area, ci_kind, ci_unavailable,
    P_signed_density (== P_density, kept for back-compat), tau, V_image,
    kernel_image, n_mc. There is no covariance band when n_mc=0, and no L-curve, so
    P_lower / P_upper / l_curve are None then; `ci_unavailable` says why when a
    band was requested but could not be built.

    `sigma_noise` is the last 30% of the SAME residual `sigma_fit` is computed
    from, so it is not an independent noise floor: their ratio says whether the
    tail is fit worse than average, NOT whether the fit is over- or under-fitting.
    Use `noise_level` (the model-free tail noise of V) as the denominator for that.
    No residual statistic detects this engine's over-fitting -- the extra structure
    is paired +/- excursions in the density that the forward kernel averages out --
    so `neg_area` (the negative area of the signed density, monotone in tau_max) is
    the over-fit indicator.
    """
    _require_scipy()
    # a removed selector must not fall into **_ignored and silently run 'penalty'
    _dead = ([] if taumax_method == 'penalty' else
             ['taumax_method=%r' % (taumax_method,)]) \
        + [kk for kk in _TAUMAX_REMOVED if kk in _ignored]
    if _dead:
        raise ValueError(
            "deer_invert_mellin: 'penalty' is the only tau_max selector; %s was "
            "removed as measured worse and broken (see the docstring). Drop the "
            "argument, or pin tau_max to a number." % ', '.join(_dead))
    t, V, _n_pre = _crop_pre_zero(t, V, policy=pre_zero)
    r = default_r_axis() if r is None else np.asarray(r, float)
    r, r_alias = _apply_alias_floor(t, r, clamp=clamp_alias, nu_dd=nu_dd)
    if bg_start is None:
        bg_start = t[0] + 0.5*(t[-1] - t[0])
    if bg_engine == 'none':
        # no intermolecular background (B=1); only lambda is estimated. Use for
        # pre-corrected / simulated / full-modulation data where fitting a decay
        # would absorb the dipolar decay and broaden P(r) (see `_no_background`).
        bg = _no_background(t, V, bg_start=bg_start, bg_end=bg_end)
    elif bg_engine == 'joint':
        # robust lambda-pinned background (clean F -> 0); the lightweight helper
        # fits only the background (no full-res NNLS / L-curve) so it is fast
        # enough to also re-run per background-start during validation
        bg = joint_background(t, V, bg_start=bg_start, bg_end=bg_end,
                              dim=dim, fit_dim=fit_dim, nu_dd=nu_dd)
    elif bg_engine == 'general':
        bg = background_general(t, V, bg_start, bg_end=bg_end, **(bg_params or {}))
    else:
        bg = background_fit(t, V, bg_start, bg_end=bg_end, dim=dim, fit_dim=fit_dim)
    F = bg['form_factor']
    Vn, B, lam = bg['V_norm'], bg['B'], bg['lambda']
    # White electrical-noise level from the decayed tail; reused for the MC band.
    sig_e_raw = _tail_noise(t, Vn)
    # NaN = could not be measured, 0.0 = a genuinely constant tail
    sig_e_ok = bool(np.isfinite(sig_e_raw))
    sig_e = float(sig_e_raw) if sig_e_ok else 0.0
    if delta is None or delta <= 0:
        # Noise-adaptive split point. delta governs how much of the echo top is
        # handled by the clean analytic PARABOLA term ([0,delta]) versus the numeric
        # Mellin integral over [delta, Tmax] -- and that numeric part is where the
        # high-|tau| noise that maps to the spurious SHORT-r spike (the "double peak
        # near t=0", and the too-narrow forward-fit echo top) enters. A larger delta
        # hands more of the steep, noisy near-echo region to the parabola, so the
        # spike and the thin parabola are suppressed AT SOURCE rather than cleaned up
        # afterwards. But a large delta over-smooths SHARP distributions (it models
        # too much real modulation as a single parabola), so it must NOT be raised on
        # clean data: scale the floor/cap up only with the measured relative noise
        # sig_e/lambda. Clean (rel < 0.02): unchanged 0.09/0.12 (sharp resolution
        # kept). Noisy (rel ~ 0.1, e.g. sigma 0.04 at lambda 0.4): floor/cap pushed
        # to ~0.13/0.16, which restores the echo-top width (benchmark forward-fit
        # half-width vs the true F: 0.78 -> ~1.0 at sigma 0.04) and roughly halves the
        # short-r spurious mass. Tuned on the synthetic benchmark.
        rel = float(sig_e)/max(float(lam), 1e-3)
        bump = min(max(rel - 0.02, 0.0)*0.6, 0.04)
        delta = mellin_delta(t, F, level=0.85, floor=0.09 + bump, cap=0.12 + bump,
                             rel_noise=rel)
    D = 2.0*np.pi*nu_dd                                 # w = D / r^3 (rad/us)
    w = D/r**3
    dr = float(r[1] - r[0]) if len(r) > 1 else 1.0
    K = dipolar_kernel(t, r, nu_dd=nu_dd)
    pos = t > 0

    def _masses(fr):
        """Area-normalized signed density/masses -- the honest model-free Mellin
        output, keeping the negative excursions (the propagated-noise signature)
        instead of clipping them to zero. Normalized so the SIGNED density
        integrates to 1, with a positive-area fallback if the signed area is
        degenerate. Returns (masses, density)."""
        area = float(_trapz(fr, r))
        if not np.isfinite(area) or abs(area) < 1e-12:
            area = float(_trapz(np.maximum(fr, 0.0), r)) or 1.0
        dens = fr/area
        return dens*dr, dens

    def _phys(fr):
        """Non-negative, sum-normalized masses (used by the tau_max auto-selection
        residual). The displayed P(r) keeps every negative excursion (genuine
        short-r noise), but the forward model must be physical: a negative density
        propagated through K flips the F_fit curvature at t=0 into a double peak."""
        m = np.maximum(fr, 0.0)*dr
        s = float(np.sum(m))
        return m/s if s > 0 else m

    # low-r noise penalty over an ABSOLUTE window (see the docstring)
    _w_span = float(np.clip(float(fit_rmin_abs) - r[0], 0.0, float(fit_rmin_width)))
    if _w_span > 0.0:
        _u = np.clip((r - r[0])/_w_span, 0.0, 1.0)
        _fit_w = 0.5*(1.0 - np.cos(np.pi*_u))
    else:
        _fit_w = np.ones_like(r)

    def _phys_fit(fr):
        """Non-negative density for F_fit, with the low-r taper applied."""
        m = np.maximum(fr, 0.0)*_fit_w*dr
        s = float(np.sum(m))
        return m/s if s > 0 else m

    def _fwd(fr):
        """Forward fit K*density. `signed_fit` (default) uses the honest SIGNED
        density the Mellin inverse produced -- it reproduces the echo-top/trough
        amplitude faithfully (a whiter residual). Otherwise the clipped, low-r-
        tapered non-negative density is used (guards against a double-peaked echo
        top from a large short-r negative noise spike, e.g. low-lambda data).
        Reached from the penalty selector's rmsF always, but from the reported
        F_fit only when `taper_short` is OFF -- with the taper on (the default)
        F_fit is K@masses of the tapered density, so `signed_fit` moves the tau_max
        choice, not the displayed curve."""
        if signed_fit:
            m, _ = _masses(fr)
            return K@m
        return K@_phys_fit(fr)

    def _build(tm, ntau):
        """Return a Mellin core inverter (F -> signed f(r)) for cutoff tm.

        The inverse divides the signal image by the kernel image, P(tau) =
        Vimg / Phi(tau). Phi decays toward large |tau| (Gamma-function tails), so
        plain division amplifies any noise in Vimg exactly where Phi is small --
        and the r-space Jacobian (~r^-2.5 after the w^-1/2 factor) then dumps that
        amplified high-tau noise into a spurious spike at SHORT r (the technique's
        signature; it can dominate P(r) and steal the real peak on noisy bimodal
        traces). With `wiener` > 0 the plain inverse filter 1/Phi is replaced by
        the Wiener-regularized inverse conj(Phi)/(|Phi|^2 + eps): identical to
        1/Phi where |Phi|^2 >> eps (the well-determined low-tau core, so sharp
        features and genuine short-r peaks are kept) but rolled off smoothly toward
        zero where |Phi|^2 << eps (the noise-dominated high-tau tail). eps scales
        with the measured tail-noise level `sig_e`, so the filter self-adapts --
        ~0 on clean data (a no-op) and stronger as noise grows -- and it only acts
        where the spectrum is noise- rather than signal-dominated, leaving real
        peaks (even at short r) untouched."""
        tau_g = np.linspace(-float(tm), float(tm), int(ntau))
        Phi_g = mellin_kernel_spectrum(tau_g)
        eps = (float(wiener)*sig_e*float(np.max(np.abs(Phi_g)))**2
               if wiener and sig_e > 0 else 0.0)
        def inv(Fx):
            Vimg = mellin_signal_spectrum(t, Fx, tau_g, delta,
                                          rel_noise=sig_e/max(float(lam), 1e-3))
            if eps > 0:
                Ptau = Vimg*np.conj(Phi_g)/(np.abs(Phi_g)**2 + eps)
            else:
                Ptau = Vimg/Phi_g
            return mellin_inverse(np.conj(Ptau), tau_g, w)*(3.0*D/r**4), Vimg
        return tau_g, Phi_g, inv

    def _ntau_for(tm):
        return int(max(401, round(2.0*tm/0.03)))        # fixed dtau ~ 0.03

    # Auto cutoff (tau_max=None): minimize the forward-fit RMS regularized by a
    # SYMMETRIC-NOISE penalty. rmsF (RMS of the form-factor residual F - F_fit over
    # t > 0) falls as the cutoff captures the parabolic echo top, then sits on a
    # broad noise-floor plateau -- so chasing its minimum, or stopping at a noise
    # floor, is ambiguous: it under-shoots (the floor is reached before P(r) has
    # sharpened) or over-extends (the plateau injects the noisy high-tau spectrum
    # into P(r)). That injected noise enters the area-normalized SIGNED density as
    # paired +bump / -dip excursions, so the |negative area| `neg` is a direct,
    # model-free measure of it (symmetric because every spurious positive spike is
    # balanced by a negative one under area normalization). Pick the cutoff
    # minimizing rmsF/min(rmsF) + neg: the ratio term (>= 1, large while the echo
    # top is under-resolved) forces an adequate fit; the neg term halts the
    # extension the moment the fit plateaus and the cutoff would only be adding
    # symmetric noise. Self-adapts to noise -- clean data plateaus late (sharp P(r)
    # kept), noisy data accrues neg early (stays smooth). Beats the discrepancy
    # floor + leakage extension on the synthetic benchmark in both the
    # no-background (mean overlap 0.922 -> 0.933) and with-background
    # (0.828 -> 0.831) regimes, landing ~0.002-0.003 from the overlap-optimal
    # oracle.
    auto_taumax = tau_max is None
    if auto_taumax:
        cands = [6.0, 8.0, 10.0, 12.0, 15.0, 18.0, 22.0, 26.0, 32.0, 40.0]
        rmsF = np.empty(len(cands)); neg = np.empty(len(cands))
        for j, tm in enumerate(cands):
            fr_j, _ = _build(tm, _ntau_for(tm))[2](F)
            Ff_j = _fwd(fr_j)                           # forward fit (signed by default)
            rmsF[j] = (float(np.sqrt(np.mean((F - Ff_j)[pos]**2)))
                       if pos.any() else np.inf)
            _, dens_j = _masses(fr_j)                   # signed density
            neg[j] = float(_trapz(np.abs(np.minimum(dens_j, 0.0)), r))
        rmin = float(np.min(rmsF)) or 1.0
        tau_max = cands[int(np.argmin(rmsF/rmin + neg))]
        n_tau = _ntau_for(tau_max)

    tau, Phi, _invert_F = _build(float(tau_max), int(n_tau))
    f_r, Vimg = _invert_F(F)

    # short-r taper on the REPORTED density, not only on F_fit (see the docstring)
    f_disp = f_r*_fit_w if taper_short else f_r
    masses, P_density = _masses(f_disp)                  # signed density (displayed)
    # The reported density keeps every negative excursion (genuine short-r noise,
    # and the diagnostic the overlay shows); the forward MODEL must not. Built from
    # the non-negative projection, F_fit is a convex mixture of kernels, and since
    # |K(t,r)| <= K(0,r) = 1 that guarantees F_fit(0) = max F_fit -- a form factor
    # must peak at the zero time. Signed masses do not: a negative mass at short r
    # subtracts |m| at t=0 but less at t>0 (its kernel decays fastest), so F_fit
    # rises after t=0 and, the fit being even in t, renders as two humps straddling
    # a dip at t0 -- on a third of noisy traces. This changes only the fit curve and
    # the residual diagnostics derived from it, never the reported P(r).
    masses_fit, _ = _masses(_nonneg_cumulative(f_disp))
    F_fit = K@masses_fit

    # discrepancy diagnostics (V space); see the docstring on sigma_noise
    vfit = B*((1 - lam) + lam*F_fit)
    sigma_fit = float(np.std((Vn - vfit)[pos])) if pos.any() else float('nan')
    tail = pos & (t > (t[pos][0] + 0.7*(t[-1] - t[pos][0]))) if pos.any() else pos
    sigma_noise = (float(np.std((Vn - vfit)[tail]))
                   if np.count_nonzero(tail) > 2 else float('nan'))
    # residual-whiteness goodness-of-fit: a structured/oscillating residual flags
    # an over-smoothed P(r) that has not captured all the dipolar modulation, even
    # when sigma_fit already matches the noise floor (the discrepancy is blind to
    # this). See residual_whiteness().
    whiteness = (residual_whiteness((Vn - vfit)[pos])
                 if pos.any() and np.count_nonzero(pos) >= 4 else None)

    # Monte-Carlo confidence band by additive-noise propagation. The recovered
    # density is signal + additive noise (the whole chain is linear), so the band
    # is built by re-running the inversion on the smooth fit perturbed by white
    # ELECTRICAL noise: the noise level sig_e is read from the decayed tail of V
    # (model-free, _tail_noise), then added to the V-space fit `vfit` and
    # propagated through the *fixed* background to the form factor -- F = (V/B -
    # (1-lam))/lam amplifies it by 1/(lam*B), so the band correctly inherits the
    # non-stationary noise that grows toward the tail (the old code added a single
    # stationary sigma directly to F, underweighting that amplification). The band
    # is the per-distance STD across the n_mc realizations, +-ci_z*STD about the
    # reported (signed) P_density. ~100 realizations are typical.
    P_lower = P_upper = P_std = None
    ci_unavailable = ''
    if n_mc and int(n_mc) > 0 and not (sig_e > 0):
        ci_unavailable = ('no band: the noise level could not be measured '
                          '(trace too short)' if not sig_e_ok else
                          'no band: the tail is exactly constant, so the measured '
                          'noise level is zero (clamped or padded trace?)')
    if n_mc and int(n_mc) > 0 and sig_e > 0:
        rng = np.random.default_rng(seed)
        vfit = B*((1 - lam) + lam*F_fit)                # smooth model of V(t)
        ens = np.empty((int(n_mc), len(r)))
        for j in range(int(n_mc)):
            Vk = vfit + sig_e*rng.standard_normal(Vn.shape)   # add white electrical noise
            Fk = (Vk/B - (1 - lam))/lam                 # propagate (amplifies toward tail)
            fk, _ = _invert_F(Fk)
            _, dk = _masses(fk*_fit_w if taper_short else fk)  # match the displayed taper
            ens[j] = dk
        P_std = ens.std(axis=0)
        P_lower = P_density - ci_z*P_std                # signed band about the estimate
        P_upper = P_density + ci_z*P_std
    _flag_bg_start_early(bg, r, P_density, nu_dd=nu_dd)
    _flag_not_deer_like(bg)
    return {'t': t, 'r': r, 'form_factor': F, 'F_fit': F_fit,
            'residuals': F - F_fit, 'P': masses, 'P_norm': masses,
            'P_density': P_density, 'P_lower': P_lower, 'P_upper': P_upper,
            'P_std': P_std, 'P_signed_density': P_density, 'kernel': K,
            'alpha': float('nan'), 'noise_level': float(sig_e_raw),
            'r_alias': float(r_alias),
            'ci_kind': 'mc_fixed_bg', 'ci_unavailable': ci_unavailable,
            'l_curve': None, 'background': bg, 'lambda': bg['lambda'],
            'k': bg['k'], 'dim': bg['dim'], 'engine': 'mellin',
            'delta': float(delta), 'tau_max': float(tau_max),
            'auto_taumax': bool(auto_taumax), 'sigma_fit': sigma_fit,
            'sigma_noise': sigma_noise, 'n_mc': int(n_mc),
            'neg_area': abs(float(_trapz(np.minimum(P_density, 0.0), r))),
            'tau': tau, 'V_image': Vimg, 'kernel_image': Phi,
            'whiteness': whiteness}


def _gauss_seed_centers(r, P_seed, n):
    """n seed centres for an n-Gaussian fit, from the peaks of a coarse density
    `P_seed` on grid `r`: local maxima ranked by height, padded with evenly
    spaced points across the range when there are fewer peaks than components."""
    r = np.asarray(r, float)
    P = np.clip(np.asarray(P_seed, float), 0.0, None)
    if len(P) >= 3:
        loc = np.where((P[1:-1] > P[:-2]) & (P[1:-1] >= P[2:]) & (P[1:-1] > 0))[0] + 1
        loc = loc[np.argsort(P[loc])[::-1]]               # tallest first
    else:
        loc = np.array([], int)
    centers = [float(x) for x in r[loc[:n]]]
    if len(centers) < n:                                  # pad with an even spread
        even = np.linspace(r[0], r[-1], n + 2)[1:-1]
        for e in even:
            if len(centers) >= n:
                break
            centers.append(float(e))
    return sorted(centers[:n])


def _pake_transform(t, nu):
    """Cosine-transform matrix Phi (n_nu x n_t) mapping a time-domain form factor
    F(t) to its dipolar (Pake) frequency spectrum F(nu) = integral F(t)cos(2*pi*nu*t)dt
    by the trapezoidal rule. `t` in us, `nu` in MHz."""
    t = np.asarray(t, float); nu = np.asarray(nu, float)
    dt = float(t[1] - t[0]) if len(t) > 1 else 1.0
    Phi = 2.0*np.cos(2.0*np.pi*np.outer(nu, t))*dt
    Phi[:, 0] *= 0.5
    if len(t) > 1:
        Phi[:, -1] *= 0.5
    return Phi


def _add_component_mass(components, r, dr):
    """Add the ON-GRID mass beside the analytic `area` / `weight`.

    `area = a*sigma*sqrt(2pi)` integrates the Gaussian over the whole real line,
    but the reported P(r) only exists on [r_min, r_max]: for a component the r
    axis truncates, the two disagree -- by up to 1.9x for a mode sitting on a
    grid edge. `weight` deliberately keeps the analytic definition, because
    `_has_spurious` and its tuned thresholds are calibrated against it;
    `mass_fraction` is the fraction of the DRAWN curve, which is what the panel
    and the CSV are describing."""
    r = np.asarray(r, float)
    tot = 0.0
    for cc in components:
        s = max(abs(float(cc['sigma'])), 1e-12)
        m = float(np.sum(float(cc['amplitude'])
                         * np.exp(-0.5*((r - float(cc['center']))/s)**2))*dr)
        cc['mass'] = m
        tot += m
    tot = tot or 1.0
    for cc in components:
        cc['mass_fraction'] = cc['mass']/tot


def _mark_active_bounds(components, idx, lo_b, hi_b, tol=1e-3):
    """Flag per component whether the fit came back ON one of its box bounds.

    A parameter sitting on an active bound is a BOUND, not a measurement, and its
    linearized +/- bar is meaningless there -- the local quadratic is taken at a
    point the parameter cannot move away from, so the interval runs outside the
    feasible region (a component pinned at the width floor is reported as
    sigma = 0.054 +/- 0.087, 61% of which is negative width). The width floor is
    distance-dependent and re-applied per seed, so the bound actually imposed is
    the one carried in `bounds`, not the floor recomputed from the fitted centre:
    26% of candidate components end up under a bound that differs from it.

    `idx[kk]` is the offset of component kk's amplitude in the full parameter
    vector; centre and sigma follow at +1 and +2. Call BEFORE sorting."""
    for kk, cc in enumerate(components):
        j = idx[kk]
        c_lo, c_hi = float(lo_b[j + 1]), float(hi_b[j + 1])
        s_lo_k, s_hi_k = float(lo_b[j + 2]), float(hi_b[j + 2])
        c, s = float(cc['center']), abs(float(cc['sigma']))
        cc['sigma_bound_lo'] = s_lo_k
        cc['sigma_bound_hi'] = s_hi_k
        cc['sigma_at_floor'] = bool(s <= s_lo_k*(1.0 + tol))
        cc['sigma_at_ceiling'] = bool(np.isfinite(s_hi_k)
                                      and s >= s_hi_k*(1.0 - tol))
        cc['center_at_bound'] = bool(c <= c_lo + tol*max(abs(c_lo), 1.0)
                                     or c >= c_hi - tol*max(abs(c_hi), 1.0))
        cc['bound_active'] = bool(cc['sigma_at_floor'] or cc['sigma_at_ceiling']
                                  or cc['center_at_bound'])


def _gauss_mc(t, V, r, K, F, bg, dr, rmin, rmax, s_lo, s_hi, npts, Ns, forced,
              ic_key, prune, _density, _criterion, _has_spurious, nu_dd,
              mc_trials, mc_tol, seed, ci_z, n_mc):
    """Dzuba/Matveeva multi-Gaussian fit, RANKED in the dipolar (Pake) frequency
    domain (Dzuba, J. Magn. Reson. 269 (2016) 113; Matveeva et al., Z. Phys. Chem.
    231 (2017) 671). For each candidate N a modest number of RANDOM parameter sets
    (a_k in [0,1], r_k in [rmin,rmax], sigma_k in [s_lo,s_hi]) are drawn, and each
    is polished by a local least-squares fit against the TIME-DOMAIN form factor;
    the Pake-domain MSD then only ranks the polished candidates. The random starts
    are what dodge the floor-width-spike basin a single gradient fit can fall
    into, and that is this mode's one measured advantage.

    Two properties it does NOT have, both measured. The background is not re-fit
    here -- it stays at the preparation values, so the returned lambda/k/dim are
    the prep stage's verbatim, and 'mc' is therefore LESS tolerant of a wrong
    background than 'lsq', not more. And the trials within (1+mc_tol) of the best
    MSD are an OPTIMIZER SPREAD, not a confidence band: the tolerance carries no
    noise scale, so the ensemble is empty about as often as it is wide.

    N is selected with the same information criterion + weight-gated spurious test
    as the least-squares path, using the best trial's time-domain residual.
    Returns the deer_invert_gauss dict shape with engine='gauss', method='mc'."""
    rng = np.random.default_rng(seed)
    # dipolar Pake band: nu = nu_dd/r^3 MHz; cover [r_max, r_min]
    nu_hi = min(1.3*nu_dd/max(rmin, 0.5)**3, 0.5/(float(t[1]-t[0]) if len(t) > 1 else 1.0))
    nu = np.linspace(0.0, nu_hi, 200)
    Phi = _pake_transform(t, nu)
    Fnu = Phi @ F
    Kfreq = Phi @ K                                       # (n_nu x n_r)
    band = np.abs(Fnu) > 0.02*np.max(np.abs(Fnu))         # significant Pake band
    if band.sum() < 5:
        band = np.ones_like(Fnu, bool)
    Kb = Kfreq[band]; Fb = Fnu[band]

    from scipy.optimize import least_squares
    # number of random restarts per N. Pure uniform random search in 3N-dim
    # (Dzuba's 1e7-1e9 trials) is far too slow interactively; instead draw a
    # modest number of RANDOM initial parameter sets and polish each with a local
    # least-squares step -- the random starts give the global coverage that
    # dodges the floor-spike basin, the polish gives precision. Trials are
    # selected on the frequency-domain Pake MSD (Dzuba's metric).
    n_restarts = max(20, int(round(mc_trials/1500)))

    def _density_p(p, n):
        g = np.zeros_like(r)
        for kk in range(n):
            g += p[3*kk]*np.exp(-0.5*((r - p[3*kk+1])/p[3*kk+2])**2)
        return g

    def _msd_freq(p, n):
        m = _density_p(p, n)*dr; tot = m.sum() or 1.0
        return float(np.mean(((m/tot) @ Kb.T - Fb)**2))

    def _search(n):
        """Stochastic multi-start: random initial (a,c,s) sets polished by a local
        least-squares fit; keep the best frequency-domain MSD and the ensemble of
        data-consistent (MSD <= (1+mc_tol)*best) polished params."""
        s0 = float(np.clip(0.2, s_lo, s_hi))
        lo = np.array([0., rmin, s_lo]*n); hi = np.array([np.inf, rmax, s_hi]*n)
        best_p, best_m, keep_p, keep_m = None, np.inf, [], []
        for it in range(n_restarts):
            cen = np.sort(rng.uniform(rmin + 0.2, rmax - 0.2, n))
            p0 = np.empty(3*n)
            p0[0::3] = 1.0/(n*s0*np.sqrt(2*np.pi))
            p0[1::3] = cen
            p0[2::3] = rng.uniform(s_lo, min(0.6, s_hi), n)
            try:
                sol = least_squares(lambda p: K@(_density_p(p, n)*dr) - F, p0,
                                    bounds=(lo, hi), max_nfev=600)
                p = sol.x
            except Exception:
                continue
            m = _msd_freq(p, n)
            keep_p.append(p.copy()); keep_m.append(m)
            if m < best_m:
                best_m, best_p = m, p.copy()
        if best_p is None:
            return None, np.inf, None
        keep_p = np.array(keep_p); keep_m = np.array(keep_m)
        ens = keep_p[keep_m <= best_m*(1.0 + mc_tol)]
        return best_p, best_m, ens

    def _rss_time(p, n):
        return float(np.sum((K@(_density(p, n)*dr) - F)**2))

    best = best_clean = None
    ic_curve = []
    cache = {}
    for n in Ns:
        p, m, ens = _search(n)
        if p is None:
            continue
        rss = _rss_time(p, n)
        crit = _criterion(rss, n)
        ic_curve.append((n, float(crit[ic_key]), rss))
        cache[n] = (p, ens, rss, crit)
        if best is None or crit[ic_key] < best['crit'][ic_key]:
            best = {'n': n, 'p': p, 'ens': ens, 'rss': rss, 'crit': crit}
        if not _has_spurious(p, n) and (
                best_clean is None or crit[ic_key] < best_clean['crit'][ic_key]):
            best_clean = {'n': n, 'p': p, 'ens': ens, 'rss': rss, 'crit': crit}
    if best is None:
        raise RuntimeError('Monte-Carlo Gaussian fit failed for every N tried.')
    n_ic = best['n']
    chosen = best if (forced or not prune or best_clean is None) else best_clean
    n = chosen['n']; p = chosen['p']; ens = chosen['ens']

    g = _density(p, n); masses = g*dr
    F_fit = K@masses
    P_norm = _normalize_masses(masses); P_density = P_norm/dr

    # per-component centre/sigma + ensemble-STD error bars (components sorted by
    # centre in every trial so the k-th slot tracks the same mode)
    order = np.argsort(p[1::3][:n])
    ens_cs = None
    if ens is not None and len(ens) >= 5:
        ec = np.sort(ens[:, 1::3], axis=1); es = np.take_along_axis(
            ens[:, 2::3], np.argsort(ens[:, 1::3], axis=1), axis=1)
        ens_cs = (ec.std(0), es.std(0))
    components = []
    for slot, kk in enumerate(order):
        a, c, s = float(p[3*kk]), float(p[3*kk+1]), float(abs(p[3*kk+2]))
        ce = float(ens_cs[0][slot]) if ens_cs is not None else float('nan')
        se = float(ens_cs[1][slot]) if ens_cs is not None else float('nan')
        components.append({'amplitude': a, 'center': c, 'sigma': s,
                           'area': a*s*np.sqrt(2.0*np.pi),
                           'center_err': ce, 'sigma_err': se})
    tot_area = sum(cc['area'] for cc in components) or 1.0
    for cc in components:
        cc['weight'] = cc['area']/tot_area
    _add_component_mass(components, r, dr)
    # this path's sigma bound is the FLAT s_lo, not the distance-dependent floor
    n_c = len(components)
    _mark_active_bounds(components, [3*kk for kk in order],
                        np.array([0., rmin, s_lo]*n_c),
                        np.array([np.inf, rmax, s_hi]*n_c))

    # confidence band from the data-consistent ensemble (per-r 2.5/97.5 pct)
    P_lower = P_upper = P_std = None
    if ens is not None and len(ens) >= 10:
        dd = np.einsum('bk,bkr->br', ens[:, 0::3],
                       np.exp(-0.5*((r[None, None, :] - ens[:, 1::3][:, :, None]) /
                                    ens[:, 2::3][:, :, None])**2))
        m = dd*dr; tot = m.sum(1, keepdims=True); tot[tot == 0] = 1.0
        ensd = (m/tot)/dr
        P_lower = np.percentile(ensd, 2.5, axis=0)
        P_upper = np.percentile(ensd, 97.5, axis=0)
        P_std = ensd.std(0)

    return {'t': t, 'r': r, 'form_factor': F, 'F_fit': F_fit,
            'residuals': F - F_fit, 'P': masses, 'P_norm': P_norm,
            'P_density': P_density, 'P_lower': P_lower, 'P_upper': P_upper,
            'P_std': P_std, 'kernel': K, 'alpha': float('nan'), 'l_curve': None,
            'background': bg, 'lambda': bg['lambda'], 'k': bg['k'],
            'dim': bg['dim'], 'engine': 'gauss', 'method': 'mc', 'n_gauss': int(n),
            'components': components, 'ic': ic_key,
            'aic': float(chosen['crit']['aic']), 'aicc': float(chosen['crit']['aicc']),
            'bic': float(chosen['crit']['bic']), 'ic_curve': ic_curve,
            'n_gauss_ic': int(n_ic), 'pruned': bool(n != n_ic),
            'ic_railed': bool(not forced and Ns and int(n_ic) >= int(max(Ns))),
            'ci_mode': 'mc_ensemble', 'ci_level': 0.95,
            # this path never re-fits the background, so lambda/k/dim are the
            # preparation stage's values, NOT co-fitted ones as on the lsq path
            'lambda_source': 'prep',
            'noise_level': float(_tail_noise(t, bg['V_norm'])),
            'mc_trials': int(mc_trials), 'mc_msd': float(chosen.get('rss', float('nan')))}


def deer_invert_gauss(t, V, r=None, bg_start=None, bg_end=None, dim=3.0,
                      fit_dim=False, nu_dd=NU_DD, n_gauss=None, max_gauss=4,
                      bg_engine='joint', bg_params=None, ic='aicc', n_mc=0,
                      ci_z=1.96, seed=0, sigma_min=None, sigma_max=None,
                      ci_mode='linear', ci_level=0.95, prune_spurious=True,
                      weight_min=0.02, spike_weight_max=0.10,
                      method='lsq', mc_trials=30000, mc_tol=0.5, pre_zero='crop',
                       clamp_alias=True,
                       **_ignored):
    """Parametric DEER inversion: model P(r) as a SUM OF N GAUSSIANS and fit their
    amplitudes / centres / widths to the form factor (the DeerAnalysis "Gaussian"
    mode / DeerLab `dd_gaussN` approach). Complements the regularized (`deer_invert`)
    and model-free (`deer_invert_mellin`) engines: when the distribution really is
    a few discrete modes this is the most robust and gives genuine *parametric*
    error bars from the fit covariance -- something a regularized inversion cannot.

    The number of components N is chosen automatically by an information criterion
    (`ic`, default corrected Akaike 'aicc'; 'aic' / 'bic' also accepted): each
    N = 1..`max_gauss` is fit and the N minimizing the criterion is kept. Pass an
    explicit `n_gauss` to force a fixed N and skip model selection.

    `prune_spurious` (default True) makes that selection robust against OVER-
    fitting. DEER traces are heavily oversampled, so at low noise the criterion's
    per-parameter penalty is negligible and it "explains" the small SYSTEMATIC
    residual left by background / lambda / echo-top preparation (which it wrongly
    treats as i.i.d. noise) by adding a spurious Gaussian -- recognizable as one
    pinned at the width-resolution floor (sigma ~ s_lo) AND carrying little weight
    (< `spike_weight_max`), or carrying negligible weight (< `weight_min`) at any
    width. The weight gate is essential: a floor-width component with SUBSTANTIAL
    weight is a real long-distance mode the solver narrowed (a near-delta is the
    global least-squares optimum there, since the kernel modulates large r only
    weakly), not an over-fit -- gating on width alone collapsed genuine 3-4
    Gaussian distributions to N=1. With pruning on, the chosen N is the criterion-
    best fit that contains NO such spurious component; this keeps simple bimodals
    from being reported as 3-4 Gaussians without an under-fitting global penalty.
    `n_gauss_ic` (the unpruned criterion pick) and `pruned` are returned for
    transparency.

    Model (P(r) a sum of Gaussians):
        P(r) = sum_k a_k * exp(-(r - r_k)^2 / (2 sigma_k^2)),  a_k, sigma_k > 0.
    The 'lsq' solver fits this JOINTLY WITH the background and modulation depth in
    V-space (DeerLab-style):
        V(t) = A * [1 - S + K @ masses(a,r,sigma)] * B(t),   S = sum(masses) = lambda
    rather than the older two-step "fit+divide the background, then fit Gaussians to
    the form factor F". That separation BIASES compact multimodal P(r): when the
    dipolar modulation has not decayed by the background window the tail fit absorbs
    real signal into lambda/k, distorting F so that even the TRUE number of
    Gaussians leaves a systematic residual -- which the criterion then "fixes" with
    a spurious extra component. Fitting everything together removes that bias (an
    ideal N-Gaussian trace is recovered to ~machine precision and the criterion
    stops over-selecting). lambda emerges as the total Gaussian mass S, and the
    free amplitude A absorbs the small echo-top normalization error, so there is no
    redundant overall-scale parameter and the covariance stays well-conditioned.
    The background is the jointly-fit stretched exponential B = exp(-(k|t|)^(d/3))
    (d floated only when fit_dim=True); bg_engine='none' fixes B=1, and 'general'
    holds an empirical background shape fixed while still co-fitting lambda + P. The
    reported P_norm / P_density are the area-normalized result; `components` carries
    each Gaussian's centre / sigma / weight with 1-sigma errors from the covariance.

    Two robustness measures keep the 'lsq' fit from the classic multi-Gaussian
    traps. (1) MULTI-START: the fit is run from both the Tikhonov-peak seed and an
    even spread across the P(r) mass support, keeping the lower-RSS result. The peak
    seed alone can pile every centre on the dominant mode (its tallest local maxima
    are that peak's noise shoulders) -> a clustered start that splits the strong
    mode and never finds a weak long-distance one, under-selecting N and leaving its
    slow modulation as a coherent residual sine. (2) DISTANCE-RESOLUTION WIDTH
    FLOOR: at long r the dipolar frequency f=nu_dd/r^3 is so low that a finite time
    window T resolves a width only to ~r^4/(27 nu_dd T); below that the kernel can't
    tell a Gaussian from a narrower one, so the (near-flat) width direction collapses
    a weak long mode into a floor-width near-delta SPIKE -- a pure single-frequency
    cosine that leaves the same residual sine. sigma is floored at that per-centre
    resolution (re-applied at the fitted centres so a migrating mode can't keep a
    stale floor), blocking the spike while leaving well-resolved short-r narrow peaks
    free. `sigma_min` overrides the floor.

    `method` selects the solver. 'lsq' (default) is the gradient least-squares fit
    described above. 'mc' is a Dzuba/Matveeva-style Monte-Carlo fit (Dzuba,
    J. Magn. Reson. 269 (2016) 113; Matveeva et al., Z. Phys. Chem. 231 (2017)
    671) carried out in the
    dipolar FREQUENCY (Pake) domain: stochastic multi-start (`mc_trials` random
    initial parameter sets, each locally polished) selected by the smallest Pake-
    spectrum MSD. The random starts dodge the floor-spike basin the gradient fit
    can fall into; the trials within (1+`mc_tol`) of the best MSD form an ensemble
    whose per-r 2.5/97.5 percentiles set `P_lower`/`P_upper` and whose per-component
    STD sets `center_err`/`sigma_err`.

    MEASURED LIMITS (S5, 2026-08-07 -- four earlier claims here did not survive):
    'mc' is NOT immune to ESEEM or background error (the 2%-of-peak band always
    contains DC, and an ESEEM line selects itself in as soon as it is present); it
    does NOT tie 'lsq' on clean data (overlap 0.875 -> 0.845, t = -5.46, correct-N
    0.81 -> 0.64 over 104 known-N runs); it does NOT use the joint V-space model
    (it fits the PREPPED form factor, so lambda / A / k are never re-fit, which
    makes the solver choice an estimator choice); and the ensemble is optimizer
    spread, not a confidence band -- bimodal (exactly zero width, or ~0.7), with
    measured coverage 0.27-0.72 against a nominal 0.95. `mc_trials` has no effect
    at any value up to its default. Prefer 'lsq' unless probing search stability.
    `n_mc`/`ci_mode` are ignored for 'mc'.

    `bg_engine` selects how V(t) is prepared, exactly as in `deer_invert_mellin`:
    'joint' (default, lambda-pinned DeerLab-style), 'sequential' (tail-window fit),
    or 'none' (B=1, fit lambda only). `t` in us, `r` in nm.

    With `n_mc` > 0 a parametric confidence band is returned by sampling the fit
    parameter covariance `n_mc` times and re-evaluating the (re-normalized) density:
    P_lower/P_upper = P_density -/+ ci_z*std. This is cheap (no re-inversion).

    `ci_mode` selects the per-component error bars on the centre and width:
      'linear' (default) -- the 1-sigma diagonal of the linearized covariance
          (J^T J)^-1 * resvar. Fast (no extra fits); symmetric; the local-quadratic
          approximation. Good for live use.
      'support' -- RIGOROUS support-plane / profile-likelihood intervals (Stein,
          Beth & Hustedt, Methods Enzymol. 563 (2015) 531, doi 10.1016/bs.mie.
          2015.07.031): for each centre / sigma, fix it on a grid and RE-FIT all
          other parameters, then take the interval where the residual sum of
          squares rises above its minimum by the F-test threshold
          SSR <= SSR_min * (1 + F_{1, N-q}(ci_level)/(N-q)). This accounts for
          parameter correlations and yields ASYMMETRIC intervals (center_ci_lo/hi,
          sigma_ci_lo/hi on each component) -- the magnitudes the linearized bar
          under-/over-states when the chi^2 surface is not parabolic. Costs a fit
          per grid step per parameter (~1-4 s); opt-in. `ci_level` is the
          confidence (default 0.95 ~ 2 sigma; 0.66 ~ 1 sigma).

    Returns the same dict shape as `deer_invert` (shared GUI / exporters): t, r,
    form_factor, F_fit, residuals, P / P_norm / P_density, P_lower / P_upper,
    kernel, background, lambda / k / dim. Gauss-specific extras: engine='gauss',
    n_gauss, components (list of {amplitude, center, sigma, weight, center_err,
    sigma_err, and -- when ci_mode='support' -- center_ci_lo/hi, sigma_ci_lo/hi}),
    aicc / aic / bic (of the chosen N), ic ('aicc'|'aic'|'bic'), ci_mode, ci_level,
    ic_curve (list of (N, criterion, rss)), noise_level. alpha is NaN and l_curve
    is None (no regularization), as for the Mellin engine.

    `background` carries the RE-FIT lambda / k / dim / B / form_factor / V_norm.
    The preparation's own reliability keys (`lambda_clamped`, `tail_abs_F`,
    `k_disagrees`, `conc_implausible`, ... -- see `joint_background`) judge the
    background this fit started from, not the one reported, so on the 'lsq' path
    they are moved to `background['prep']` and must be quoted as such. They are
    NOT recomputed on the refitted rate: that was measured to turn a healthy trace
    into a warning. `bg_start_early` is the exception -- it is re-derived from the
    final P(r) and stays at the top level. The 'mc' path does not re-fit, so its
    keys stay where `joint_background` put them.
    """
    _require_scipy()
    from scipy.optimize import least_squares
    t, V, _n_pre = _crop_pre_zero(t, V, policy=pre_zero)
    r = default_r_axis() if r is None else np.asarray(r, float)
    r, r_alias = _apply_alias_floor(t, r, clamp=clamp_alias, nu_dd=nu_dd)
    if bg_start is None:
        bg_start = t[0] + 0.5*(t[-1] - t[0])
    if bg_engine == 'none':
        bg = _no_background(t, V, bg_start=bg_start, bg_end=bg_end)
    elif bg_engine == 'joint':
        bg = joint_background(t, V, bg_start=bg_start, bg_end=bg_end,
                              dim=dim, fit_dim=fit_dim, nu_dd=nu_dd,
                              prep_only=(method != 'mc'))
    elif bg_engine == 'general':
        bg = background_general(t, V, bg_start, bg_end=bg_end, **(bg_params or {}))
    else:
        bg = background_fit(t, V, bg_start, bg_end=bg_end, dim=dim, fit_dim=fit_dim)
    F = bg['form_factor']                                 # prepped F: seeds + 'mc' path
    Vn, B, lam = bg['V_norm'], bg['B'], bg['lambda']
    k0, dim0 = float(bg.get('k', 0.05) or 0.0), float(bg.get('dim', dim))
    sig_e = _tail_noise(t, Vn)
    K = dipolar_kernel(t, r, nu_dd=nu_dd)
    dr = float(r[1] - r[0]) if len(r) > 1 else 1.0
    rmin, rmax = float(r[0]), float(r[-1])
    # width bounds: the widest meaningful one spans the half-range. The LOWER
    # bound regularizes via the distance-discretization length (Dzuba, J. Magn.
    # Reson. 269 (2016) 113; Matveeva et al., Z. Phys. Chem. 231 (2017) 671) -- a component
    # narrower than ~the resolvable distance step is unphysical and just over-
    # fits a noise wiggle as a near-delta spike. A floor of a few grid steps
    # (>= 0.05 nm, the practical PDS width resolution) blocks those spikes AND,
    # by admitting fewer spurious narrow components, sharpens N selection (the
    # benchmark improves on both N-accuracy and overlap going 0.03 -> 0.05 nm).
    # The weight-gated spurious test handles the rest. Defaults are overridable.
    s_lo = float(sigma_min) if sigma_min else max(2.5*dr, 0.05)
    s_hi = float(sigma_max) if sigma_max else max(0.5*(rmax - rmin), 4*s_lo)
    s0 = float(np.clip(0.2, s_lo, s_hi))
    # Distance-dependent width floor (PDS resolution limit). The dipolar frequency
    # f(r) = nu_dd/r^3 falls steeply with r, so a finite time window T resolves a
    # width only down to dr_res = (1/T)/|df/dr| = r^4/(3 nu_dd T) -- times a ~1/9
    # fit-efficiency factor (a parametric fit resolves finer than the 1/T Rayleigh
    # bin) => r^4/(27 nu_dd T). Below this the kernel cannot distinguish a Gaussian
    # from a narrower one, so least_squares (for which width is a near-flat
    # direction at long r -- forcing the true width costs <1% RSS) collapses a weak
    # long-distance mode to a floor-width NEAR-DELTA SPIKE. That spike is a pure
    # single-frequency cosine where the true broad mode is damped, leaving a
    # coherent residual sine. Flooring sigma at dr_res(centre) blocks the spike
    # (recovering ~the resolvable width) while leaving well-resolved short-r narrow
    # peaks free; user-set sigma_min overrides it. T is the trace time span.
    T_span = float(np.max(t) - np.min(t)) if len(t) > 1 else 1.0

    def _sigma_floor(c):
        if sigma_min:                                     # explicit override wins
            return s_lo
        # cap STRICTLY below s_hi: s_hi is also the sigma UPPER bound, so a plain
        # min(s_hi, ...) makes lo == hi for any centre past
        # (s_hi*27*nu_dd*T)**0.25 and least_squares refuses the box. That needs
        # rmax ~ 2.25x the trace-supported rmax, not a short trace.
        return float(min(s_hi*0.999,
                         max(s_lo, c**4/(27.0*nu_dd*max(T_span, 1e-6)))))
    # coarse Tikhonov pass to seed component centres (peak positions). A fixed
    # moderate alpha is enough just to place peaks; falls back to an even spread.
    try:
        L = regularization_matrix(len(r), 2)
        P_seed = tikhonov_nnls(K, F, 1.0, L)
    except Exception:
        P_seed = np.zeros_like(r)
    npts = len(F)

    def _density(p, n):
        g = np.zeros_like(r)
        for kk in range(n):
            a, c, s = p[3*kk], p[3*kk + 1], p[3*kk + 2]
            g = g + a*np.exp(-0.5*((r - c)/s)**2)
        return g

    # --- V-space joint fit (background + lambda + Gaussians together) ----------
    # The separable prep above (fit background+lambda on the tail, divide them out,
    # then fit Gaussians to the resulting F) BIASES the result whenever a compact,
    # multimodal P(r) still modulates inside the background window: the tail fit
    # absorbs real dipolar signal into lambda/k, distorting F so that even the TRUE
    # number of Gaussians can no longer match it -- a systematic form-factor
    # residual plus a spurious extra component the criterion adds to mop it up. A
    # parametric model needs no such separation: fit lambda, the background, and the
    # Gaussian parameters JOINTLY against V(t) (DeerLab-style). lambda emerges as
    # the total Gaussian mass, so V = [1 - sum(masses) + K@masses]*B(t) gives
    # V(0)=1 with no redundant overall-scale parameter. The prepped 'bg' is kept
    # only to seed the centres (Tikhonov) and as the 'mc' path's target.
    #   bg_engine 'none'     -> B = 1                 (no background, k = 0)
    #   bg_engine 'general'  -> B fixed from the one-shot general fit; fit on V/B
    #   else (default/joint) -> stretched-exp B = exp(-(k|t|)^(d/3)) fit jointly
    #                           (the dimension d is floated only when fit_dim=True)
    # Leading (non-Gaussian) parameters of the joint vector, in order:
    #   p[0]          = A, a free V(0) amplitude (absorbs the small echo-top scale
    #                   error so an IDEAL trace fits to ~machine zero -- otherwise
    #                   the residual normalization, not the data, sets the floor and
    #                   the criterion chases it with a spurious component);
    #   p[1]          = k         (stretched-exp background; 'exp'/'exp_d' only)
    #   p[2]          = d         (background dimension; 'exp_d' only, i.e. fit_dim)
    # 'none' carries B = 1; 'general' fixes B from the one-shot general fit (folded
    # into V_tgt = Vn/B). lambda is NOT a leading parameter -- it emerges as the
    # total Gaussian mass S = sum(masses): V = A*(1 - S + K@masses)*B, so A scales
    # the whole trace while S sets the modulation depth (separately identifiable).
    if bg_engine == 'none':
        bg_mode, n_bg, B_gen = 'none', 1, np.ones_like(t)
        V_tgt = Vn
    elif bg_engine == 'general':
        # empirical background can't be re-parametrized cheaply: hold its SHAPE
        # fixed but APPLY it in the model (multiply), so lambda + the Gaussians are
        # still fit jointly against V. (Dividing it into the target blows up where
        # the extrapolated general background nears zero.)
        bg_mode, n_bg, B_gen = 'general', 1, B
        V_tgt = Vn
    elif fit_dim:
        bg_mode, n_bg, B_gen = 'exp_d', 3, None
        V_tgt = Vn
    else:
        bg_mode, n_bg, B_gen = 'exp', 2, None
        V_tgt = Vn

    def _bg_of(p):
        """(B(t), dim) for the joint model from p's leading background parameters.
        'none' has B=1; 'general' applies the fixed empirical background shape;
        'exp'/'exp_d' build the stretched exponential from the fitted k (and d)."""
        if bg_mode == 'none':
            return np.ones_like(t), dim0
        if bg_mode == 'general':
            return B_gen, dim0
        d = p[2] if bg_mode == 'exp_d' else dim
        return np.exp(-(p[1]*np.abs(t))**(d/3.0)), d

    def _vmodel(p, n):
        """Joint V-space model and its (masses, B). lambda = sum(masses); p[0]=A."""
        Bv = _bg_of(p)[0]
        masses = _density(p[n_bg:], n)*dr
        return p[0]*(1.0 - masses.sum() + K@masses)*Bv, masses, Bv

    def _seed_sets(n):
        """Candidate centre seeds for an n-Gaussian start. MULTI-START is needed
        because the Tikhonov-peak seed alone can pile every centre onto the
        dominant peak (its tallest local maxima are that peak's noise shoulders),
        a clustered start from which least_squares splits the strong mode and never
        reaches a weak long-distance one -- under-selecting N and leaving that
        mode's slow modulation as a coherent residual sine. A spread seed across
        the P_seed mass support escapes that basin (the basin is wide -- ANY
        de-clustered seed converges to the right peaks)."""
        sets = [_gauss_seed_centers(r, P_seed, n)]        # Tikhonov peaks
        if n > 1:
            Pp = np.clip(P_seed, 0.0, None); tot = float(Pp.sum())
            if tot > 0:                                   # span the central mass
                cdf = np.cumsum(Pp)/tot
                a = float(r[int(np.searchsorted(cdf, 0.02))])
                b = float(r[min(len(r) - 1, int(np.searchsorted(cdf, 0.98)))])
            else:
                a, b = rmin, rmax
            if b - a < 1e-3:
                a, b = rmin, rmax
            spread = list(np.linspace(a, b, n))
            if max(abs(x - y) for x, y in zip(sorted(sets[0]), spread)) > 0.05:
                sets.append(spread)                       # only if it differs
        return sets

    def _fit_n(n):
        lam_s = float(np.clip(lam if lam > 0 else 0.3, LAM_MIN, LAM_MAX_PINNED))
        a0 = (lam_s/n)/(s0*np.sqrt(2.0*np.pi))            # split lambda over n modes
        lead0, leadlo, leadhi = [1.0], [0.1], [10.0]      # A: V(0) amplitude
        if bg_mode in ('exp', 'exp_d'):
            lead0.append(max(k0, 1e-3)); leadlo.append(0.0); leadhi.append(np.inf)
        if bg_mode == 'exp_d':
            lead0.append(float(np.clip(dim0, 1.0, 6.0)))
            leadlo.append(1.0); leadhi.append(6.0)
        def _solve(p0, lo, hi):
            sol = least_squares(lambda p: _vmodel(p, n)[0] - V_tgt, p0,
                                bounds=(lo, hi), max_nfev=6000)
            # The distance-resolution width floor is seeded from the START centres,
            # but a mode can MIGRATE to long r during the fit and keep its (stale,
            # too-low) floor -> a residual spike survives. Re-apply the floor at the
            # FITTED centres and refit until no component sits below its own floor
            # (usually 0 or 1 extra fits; the width direction is near-flat so this
            # barely moves RSS).
            for _ in range(3):
                x = sol.x; lo2 = lo.copy(); bumped = False
                for kk in range(n):
                    ci = float(x[n_bg + 3*kk + 1]); fl = _sigma_floor(ci)
                    if abs(x[n_bg + 3*kk + 2]) < fl*0.99:
                        lo2[n_bg + 3*kk + 2] = fl; bumped = True
                if not bumped:
                    break
                lo = lo2
                sol = least_squares(lambda p: _vmodel(p, n)[0] - V_tgt,
                                    np.clip(x, lo, hi), bounds=(lo, hi), max_nfev=4000)
            return sol, float(np.sum(sol.fun**2)), (lo, hi)

        best = None
        for centers in _seed_sets(n):
            p0, lo, hi = list(lead0), list(leadlo), list(leadhi)
            for c in centers:
                cc = float(np.clip(c, rmin, rmax))
                sig_lo = _sigma_floor(cc)                  # distance-resolution floor
                p0 += [a0, cc, max(s0, sig_lo)]
                lo += [0.0, rmin, sig_lo]
                hi += [np.inf, rmax, s_hi]
            # guard the SEED, not the whole N: one unusable start must not delete a
            # component count the other seed could have fit. _solve is inside the
            # try because the re-floor refit can rebuild a degenerate box from a
            # centre that migrated during the fit, even when every seed was legal.
            try:
                sol, rss, bnds = _solve(p0, np.array(lo), np.array(hi))
            except Exception:
                continue
            if best is None or rss < best[1]:
                best = (sol, rss, bnds)
        return best

    def _criterion(rss, n, n_extra=0):
        kpar = 3*n + n_extra + 1                          # +1 for the noise variance
        aic = npts*np.log(rss/npts) + 2*kpar if rss > 0 else -np.inf
        denom = npts - kpar - 1
        aicc = aic + (2*kpar*(kpar + 1)/denom if denom > 0 else np.inf)
        bic = npts*np.log(rss/npts) + kpar*np.log(npts) if rss > 0 else -np.inf
        return {'aic': aic, 'aicc': aicc, 'bic': bic}

    def _has_spurious(pp, n):
        """Flag a fit whose components include a SPURIOUS one. At low noise the
        information criterion over-fits the small SYSTEMATIC residual left by
        background/lambda/echo-top preparation (not random noise, which the
        criterion assumes) by adding an extra component that shows up as a
        Gaussian pinned at the width-resolution floor (sigma ~ s_lo) carrying
        LITTLE weight. Rejecting any N whose best fit contains one keeps the
        count parsimonious without an under-fitting global penalty.

        The weight gate is essential: a floor-width component that carries
        SUBSTANTIAL weight is a REAL peak the least-squares solver narrowed (a
        long-distance mode the kernel modulates only weakly is fit about as well
        by a narrow spike as by its true broad shape -- the spike is the global
        LS optimum, not a local-min artifact), NOT an over-fit. Flagging it on
        width alone collapsed genuine 3-4 Gaussian distributions all the way to
        N=1. So a floor-width component is spurious only when it ALSO carries
        < `spike_weight_max` of the area; a negligible-weight component
        (< `weight_min`, any width) is always spurious.

        SCOPE OF THE WIDTH ARM -- deliberate, and measured. The test compares
        against the GLOBAL `s_lo`, not `_sigma_floor(centre)`, so it can only fire
        below the distance where the resolution floor still equals s_lo, about
        r* = (1.1*s_lo*27*nu_dd*T)**0.25. That is not a fixed distance: it moves
        with the grid AND the trace length (3.5 nm on an auto grid at 2 us,
        5.0 nm on the default grid at 5 us). Beyond r* only the negligible-weight
        arm can condemn a component, and that is right: out there the per-centre
        floor has ALREADY made the near-delta spike unconstructible, so what a
        per-centre test would catch instead is a genuine weak far mode. Re-keying
        the arm on `_sigma_floor(centre)` was tried and measured -- correct-N
        0.843 -> 0.731 over 108 runs, and on the rows it changes N was right 12/13
        before and 0/13 after -- so it must not be "fixed" that way."""
        sig = np.abs(pp[2::3][:n])
        amp = pp[0::3][:n]
        area = amp*sig*np.sqrt(2.0*np.pi)
        tot = float(np.sum(area)) or 1.0
        w = area/tot
        floor = sig <= s_lo*1.1
        return bool(np.any(w < weight_min) or
                    np.any(floor & (w < spike_weight_max)))

    Ns = [int(n_gauss)] if (n_gauss and int(n_gauss) > 0) else \
        list(range(1, int(max_gauss) + 1))
    forced = bool(n_gauss and int(n_gauss) > 0)

    if method == 'mc':
        res = _gauss_mc(t, V, r, K, F, bg, dr, rmin, rmax, s_lo, s_hi, npts,
                        Ns, forced, ic_key=ic if ic in ('aic', 'aicc', 'bic')
                        else 'aicc', prune=prune_spurious, _density=_density,
                        _criterion=_criterion, _has_spurious=_has_spurious,
                        nu_dd=nu_dd, mc_trials=int(mc_trials), mc_tol=float(mc_tol),
                        seed=seed, ci_z=ci_z, n_mc=n_mc)
        # the 'mc' path returns its own dict, so the two reporting mechanisms that
        # live in the 'lsq' tail have to be re-applied here or they vanish
        res['r_alias'] = float(r_alias)
        _flag_bg_start_early(bg, r, res['P_density'], nu_dd=nu_dd)
        _flag_not_deer_like(bg, lam=res.get('lambda'))
        return res
    ic_key = ic if ic in ('aic', 'aicc', 'bic') else 'aicc'
    best = best_clean = None
    ic_curve = []
    ic_failed = []                     # (N, reason) -- an N that never reached the criterion
    for n in Ns:
        try:
            fit = _fit_n(n)
            if fit is None:            # every seed for this N was unusable
                raise RuntimeError('no usable seed')
            sol, rss, bounds = fit
        except Exception as exc:
            ic_failed.append((int(n), '%s: %s' % (type(exc).__name__, exc)))
            continue
        crit = _criterion(rss, n, n_bg)
        ic_curve.append((n, float(crit[ic_key]), rss))
        cand = {'n': n, 'sol': sol, 'rss': rss, 'crit': crit, 'bounds': bounds}
        if best is None or crit[ic_key] < best['crit'][ic_key]:
            best = cand
        if not _has_spurious(sol.x[n_bg:], n) and (
                best_clean is None or crit[ic_key] < best_clean['crit'][ic_key]):
            best_clean = cand
    if best is None:
        why = '; '.join('N=%d %s' % (n, msg) for n, msg in ic_failed[:3])
        raise RuntimeError(
            'Gaussian fit failed for every component count tried (%s). A '
            'degenerate width box is the usual cause: the distance range is far '
            'wider than the trace supports, so the resolution floor meets the '
            'width ceiling. Narrow "Distance max" or set sigma_min.'
            % (why or 'no diagnostics'))

    # Prefer the criterion-best model with NO spurious (floor-width / negligible-
    # weight) component; fall back to the plain criterion pick if every fit has one
    # (or N was forced -- then honour the request).
    n_ic = best['n']
    chosen = best if (forced or not prune_spurious or best_clean is None) else best_clean
    n = chosen['n']
    sol = chosen['sol']
    best = chosen                                          # downstream reads best['*']
    p = sol.x
    gp = p[n_bg:]                                          # gaussian-only parameters
    lo_b, hi_b = chosen['bounds']
    # covariance from the Jacobian: cov = (J^T J)^-1 * residual variance. pinv
    # guards the (near-)singular directions overlapping components produce.
    nparams = len(p)
    dof = max(npts - nparams, 1)
    resvar = best['rss']/dof
    try:
        cov = np.linalg.pinv(sol.jac.T@sol.jac)*resvar
        perr = np.sqrt(np.clip(np.diag(cov), 0.0, None))
    except Exception:
        cov, perr = None, np.full(nparams, np.nan)

    g = _density(gp, n)
    masses = g*dr
    lam_fit = float(masses.sum())                         # modulation depth = total mass
    A_fit = float(p[0])                                   # fitted V(0) amplitude
    Bv, dim_fit = _bg_of(p)
    if bg_mode == 'general':
        Bv = B_gen
    k_fit = float(p[1]) if bg_mode in ('exp', 'exp_d') else \
        (float(bg['k']) if bg_engine == 'general' else 0.0)
    D = K@masses
    lam_safe = lam_fit if abs(lam_fit) > 1e-9 else 1e-9
    Bsafe = np.where(Bv == 0.0, 1.0, Bv)
    Vn_eff = Vn/(A_fit if abs(A_fit) > 1e-9 else 1.0)     # de-scale the fitted V(0)
    F = (Vn_eff/Bsafe - (1.0 - lam_fit))/lam_safe         # data form factor (final bg)
    F_fit = D/lam_safe                                    # model form factor, F(0)=1
    P_norm = _normalize_masses(masses)
    P_density = P_norm/dr
    # This engine RE-FITS the background, so the preparation's reliability keys
    # describe an estimate that no longer exists: park them under 'prep'.
    bg = dict(bg)
    prep = {kk: bg.pop(kk) for kk in _PREP_BG_KEYS if kk in bg}
    bg.update({'lambda': lam_fit, 'k': k_fit, 'dim': float(dim_fit),
               'A': float(1.0 - lam_fit),
               'B': Bv, 'form_factor': F, 'V_norm': Vn_eff})
    if prep:
        bg['prep'] = prep

    components = []
    for kk in range(n):
        a, c, s = float(gp[3*kk]), float(gp[3*kk + 1]), float(abs(gp[3*kk + 2]))
        components.append({'amplitude': a, 'center': c, 'sigma': s,
                           'area': a*s*np.sqrt(2.0*np.pi),
                           'center_err': float(perr[n_bg + 3*kk + 1]),
                           'sigma_err': float(perr[n_bg + 3*kk + 2])})
    tot_area = sum(cc['area'] for cc in components) or 1.0
    for cc in components:
        cc['weight'] = cc['area']/tot_area
    _add_component_mass(components, r, dr)
    _mark_active_bounds(components, [n_bg + 3*kk for kk in range(n)], lo_b, hi_b)
    components.sort(key=lambda d: d['center'])

    # Rigorous support-plane / profile-likelihood confidence intervals (Hustedt,
    # Methods Enzymol. 2015): for each centre / sigma, fix it and RE-FIT the rest,
    # and bound the interval where SSR exceeds SSR_min by the F-test threshold.
    # Accounts for parameter correlations -> asymmetric, correctly-sized intervals.
    if ci_mode == 'support' and npts > nparams:
        from scipy.stats import f as _f_dist
        ssr_min = best['rss']
        Fq = float(_f_dist.ppf(ci_level, 1, npts - nparams))
        target = ssr_min*(1.0 + Fq/(npts - nparams))

        def _ssr_fixed(fix_i, val):
            """Min SSR with parameter fix_i held at val, all others re-fit."""
            free = [j for j in range(nparams) if j != fix_i]
            base = p.copy(); base[fix_i] = val

            def resid(pf):
                pp = base.copy(); pp[free] = pf
                return _vmodel(pp, n)[0] - V_tgt
            try:
                s = least_squares(resid, p[free],
                                  bounds=(lo_b[free], hi_b[free]), max_nfev=2000)
                return float(np.sum(s.fun**2))
            except Exception:
                return np.inf

        def _bound(fix_i, sign):
            """Walk fix_i out from its best value (re-fitting the rest) until SSR
            crosses `target`, then bisect; return the crossing (clamped to the
            box bound, which it returns when the parameter is unbounded there)."""
            th0 = float(p[fix_i]); lim = float(hi_b[fix_i] if sign > 0 else lo_b[fix_i])
            step = perr[fix_i] if (np.isfinite(perr[fix_i]) and perr[fix_i] > 1e-6) \
                else 0.05*abs(hi_b[fix_i] - lo_b[fix_i])
            below, above, th = th0, None, th0
            for _ in range(40):
                th = th + sign*step
                if (sign > 0 and th >= lim) or (sign < 0 and th <= lim):
                    th = lim
                if _ssr_fixed(fix_i, th) > target:
                    above = th; break
                below = th
                step *= 1.6
                if th == lim:
                    break
            if above is None:
                return lim                                # CI runs to the box bound
            a, b = below, above
            for _ in range(16):                           # ~range/65000 precision
                m = 0.5*(a + b)
                if _ssr_fixed(fix_i, m) > target:
                    b = m
                else:
                    a = m
            return 0.5*(a + b)

        # map sorted components back to their parameter block (sorted by centre);
        # gaussian params are offset by the n_bg leading background parameters
        order = sorted(range(n), key=lambda kk: float(gp[3*kk + 1]))
        for cc, kk in zip(components, order):
            cc['center_ci_lo'] = _bound(n_bg + 3*kk + 1, -1)
            cc['center_ci_hi'] = _bound(n_bg + 3*kk + 1, +1)
            cc['sigma_ci_lo'] = _bound(n_bg + 3*kk + 2, -1)
            cc['sigma_ci_hi'] = _bound(n_bg + 3*kk + 2, +1)

    P_lower = P_upper = P_std = None
    if n_mc and int(n_mc) > 0 and cov is not None and np.all(np.isfinite(cov)):
        rng = np.random.default_rng(seed)
        try:
            samples = rng.multivariate_normal(p, cov, size=int(n_mc))
            ens = np.empty((int(n_mc), len(r)))
            for j in range(int(n_mc)):
                gj = samples[j][n_bg:].copy()             # gaussian params only
                gj[0::3] = np.clip(gj[0::3], 0.0, None)    # amplitudes >= 0
                gj[2::3] = np.clip(np.abs(gj[2::3]), s_lo, s_hi)
                ens[j] = _normalize_masses(_density(gj, n)*dr)/dr
            P_std = ens.std(axis=0)
            P_lower = P_density - ci_z*P_std
            P_upper = P_density + ci_z*P_std
        except Exception:
            P_lower = P_upper = P_std = None

    _flag_bg_start_early(bg, r, P_density, nu_dd=nu_dd)
    _flag_not_deer_like(bg, lam=lam_fit)
    return {'t': t, 'r': r, 'form_factor': F, 'F_fit': F_fit,
            'residuals': F - F_fit, 'P': masses, 'P_norm': P_norm,
            'P_density': P_density, 'P_lower': P_lower, 'P_upper': P_upper,
            'P_std': P_std, 'kernel': K, 'alpha': float('nan'), 'l_curve': None,
            'r_alias': float(r_alias),
            'background': bg, 'lambda': bg['lambda'], 'k': bg['k'],
            'dim': bg['dim'], 'engine': 'gauss', 'n_gauss': int(n),
            'components': components, 'ic': ic_key,
            'aic': float(best['crit']['aic']), 'aicc': float(best['crit']['aicc']),
            'bic': float(best['crit']['bic']), 'ic_curve': ic_curve,
            'n_gauss_ic': int(n_ic), 'pruned': bool(n != n_ic),
            'ic_failed': ic_failed,
            # the criterion never turned over inside the cap, so N is the spin
            # box's value rather than the data's. Measured on 28 real traces:
            # true for 25/28 at the default max_gauss = 4, but only 4/28 once the
            # cap is lifted to 8 -- the criterion DOES have an interior minimum
            # (at 5-7), it is just above the default. It matters: the reported
            # peak moves by a median 0.13 nm (worst 4.2 nm) between N and N-1.
            'ic_railed': bool(not forced and int(n_ic) >= int(max_gauss)),
            'ci_mode': ci_mode, 'ci_level': float(ci_level),
            'noise_level': float(sig_e)}


# --------------------------------------------------------------------------- #
#  Zero-time (reference-time) fitting
# --------------------------------------------------------------------------- #
def _boxcar(V, w):
    """Edge-padded moving average; mode='same' zero-pads and would pull the
    argmax off a peak sitting at t[0]."""
    n = len(V)
    if w <= 1:
        return V
    return np.convolve(np.pad(V, w//2, mode='edge'), np.ones(w)/w,
                       mode='same')[w//2:w//2 + n]


def _top_width(Vs, i0, n, drop):
    """Half-width of the echo top: walk out from i0 until the smoothed trace has
    fallen `drop` of the peak-to-min amplitude, and keep the shorter side."""
    amp = max(float(np.max(Vs)) - float(np.min(Vs)), 1e-12)
    thr = float(Vs[i0]) - drop*amp
    lo = i0
    while lo > 0 and Vs[lo] >= thr:
        lo -= 1
    hi = i0
    while hi < n - 1 and Vs[hi] >= thr:
        hi += 1
    lo = max(min(lo, i0 - 3), 0)
    hi = min(max(hi, i0 + 3), n - 1)
    return max(3, min(i0 - lo, hi - i0)), amp, thr


def _centroid_zero_time(t, V, search_frac=0.30, smooth_w=9, drop=0.25,
                        reach=5.0, iters=3):
    """Zero time as the centroid of the echo top, iterated to a fixed point.

    V is even about t0, so the centroid of any weight symmetric about t0 IS t0 --
    no curvature needed. Weight = max(Vs - thr, 0), thr `drop` of the peak-to-min
    amplitude below the peak, over a window `reach` times the top half-width,
    re-centred on the running estimate until it stops moving.

    This is a LINEAR functional of V, which is why it holds up where the parabola
    vertex does not: on a broad distribution at high noise the echo top is flat
    over tens of samples, so the anchoring argmax is a winner-take-all pick among
    near-equal noisy samples (its own error reaches 120 ns) and the vertex -b/2a
    is a ratio of two numbers that are both noise. A centroid averages those
    samples instead of choosing between them, and cannot diverge.

    Where the window runs past the start of the trace the truncation is one-sided
    and shrinks the estimate toward the data that exists. That bias lands only on
    the flattest echoes, which carry almost no zero-time information anyway.
    """
    n = len(t)
    Vs = _boxcar(V, int(max(1, smooth_w)))
    ns = max(5, int(search_frac*n))
    i0 = int(np.argmax(Vs[:ns]))
    if i0 >= ns - 1 and ns < n:
        return None
    hw, _amp, thr = _top_width(Vs, i0, n, drop)
    dt = float(t[1] - t[0])
    h = int(round(reach*hw))
    i, out = i0, float(t[i0])
    for _ in range(int(max(1, iters))):
        lo = max(i - h, 0)
        hi = min(i + h, n - 1)
        if hi - lo < 4:
            return float(t[i])
        wgt = np.clip(Vs[lo:hi + 1] - thr, 0.0, None)
        if wgt.sum() <= 0:
            return float(t[i])
        out = float(np.average(t[lo:hi + 1], weights=wgt))
        j = int(np.clip(round((out - t[0])/dt), 0, n - 1))
        if j == i:
            break
        i = j
    return out


def _parabolic_zero_time(t, V, drop=0.15, smooth_w=5, search_frac=0.30,
                         noisy_rel=0.055, centroid_w=9, centroid_drop=0.25,
                         centroid_reach=5.0, centroid_iters=3):
    """Zero-time t0 from the echo maximum of V(t).

    Below a measured noise-to-amplitude ratio of `noisy_rel` this is the classic
    DeerAnalysis quadratic fit: V near the echo is even and parabolic in (t - t0)
    -- V ~ Vpk - c(t - t0)^2 -- so the vertex of a least-squares parabola is t0.

    Robust against noise: the initial peak is the argmax of a lightly smoothed V
    *restricted to the first `search_frac` of the trace* (so a stray noise spike
    elsewhere can't be mistaken for the echo), and the fit window WIDENS
    symmetrically out to where the smoothed signal has fallen `drop` of its
    peak-to-min amplitude -- wide enough to average down noise, narrow enough to
    stay within the parabolic top (a too-wide window is biased by the dipolar
    oscillation / decay and by the truncated pre-zero side). ~3x more accurate
    than the residual search at high noise on traces with a clear echo maximum.
    Returns t0, or None if no concave peak is found (caller falls back).

    ABOVE `noisy_rel` (measured sigma over the peak-to-min amplitude) the vertex
    is the wrong statistic and the estimator hands over to `_centroid_zero_time`.
    Two things break the parabola together on a broad distance distribution at
    high noise, and both worsen the broader P(r) is: the echo top goes flat, so
    the curvature -- and hence the vertex -- is a ratio of two numbers that are
    both noise; and the argmax anchoring the fit window is a winner-take-all pick
    among dozens of near-equal noisy samples. An earlier round widened the WINDOW
    here instead, which was only half the fix.

    Below the gate the result is bit-identical to the pre-2026-07 estimator: that
    covers every real trace measured (sigma/amplitude 0.004-0.025), though a
    weak-modulation short-distance shape can cross it at sigma 0.02. Set
    `noisy_rel` to inf to force the parabola everywhere.

    Measured over 21 shapes x 168 noisy synthetic traces, out of sample: mean
    |t0 error| 15.2 -> 10.5 ns, worst 163.7 -> 63.7, and no concave-peak failures
    (8 -> 1, each of which costs the caller a full residual search). The
    distance-distribution overlap gains +0.0098 on the Mellin engine and +0.0111
    on Tikhonov -- BOTH engines, which is what distinguishes this from the
    `xcheck` route in `fit_zero_time`: that one improved t0 accuracy yet lost
    overlap, because a slightly-late t0 was cancelling a Mellin-specific forward
    bias, so it moved the two engines in opposite directions."""
    t = np.asarray(t, float); V = np.asarray(V, float)
    n = len(t)
    if n < 7:
        return None
    w = int(max(1, smooth_w))
    Vs = _boxcar(V, w)
    _sig = float(np.std(np.diff(V)))/np.sqrt(2.0)       # white-noise level
    ns = max(5, int(search_frac*n))
    i0 = int(np.argmax(Vs[:ns]))
    if i0 >= ns - 1 and ns < n:
        # still rising at the window edge -- echo top is beyond search_frac
        return None
    vpk = float(Vs[i0]); vmin = float(np.min(Vs)); amp = max(vpk - vmin, 1e-12)
    if _sig/max(float(np.max(Vs)) - float(np.min(Vs)), 1e-12) > noisy_rel:
        _t0 = _centroid_zero_time(t, V, search_frac, centroid_w, centroid_drop,
                                  centroid_reach, centroid_iters)
        if _t0 is not None:                 # else fall through to the parabola
            return _t0
    thr = vpk - drop*amp
    lo = i0
    while lo > 0 and Vs[lo] >= thr:
        lo -= 1
    hi = i0
    while hi < n - 1 and Vs[hi] >= thr:
        hi += 1
    lo = max(min(lo, i0 - 3), 0)
    hi = min(max(hi, i0 + 3), n - 1)
    # symmetric, as documented: the raw walks run up to 22x wider on the decay side
    half = max(3, min(i0 - lo, hi - i0))
    lo = max(i0 - half, 0)
    hi = min(i0 + half, n - 1)
    if hi - lo < 4:
        return None
    tt = t[lo:hi + 1]; vv = V[lo:hi + 1]
    a, b, _c = np.polyfit(tt - tt.mean(), vv, 2)
    if a >= 0:                                          # not concave -> no echo max
        return None
    t0 = float(tt.mean() - b/(2.0*a))
    if not (t[lo] <= t0 <= t[hi]):       # vertex extrapolated outside its own window
        return None
    return t0


def fit_zero_time(t, V, bg_start=None, bg_end=None, n_grid=16, search_frac=0.15,
                  refine=True, method='parabola', drop=0.15, smooth_w=5,
                  xcheck=False, xcheck_tol_frac=0.004, **kwargs):
    """Find the zero-time t0 (the dipolar reference time).

    `method='parabola'` (default) fits a quadratic to the echo maximum and takes
    its vertex (`_parabolic_zero_time`) -- fast, data-only, and ~3x more accurate
    than the residual search at high noise on traces with a clear echo maximum
    (the usual case). It falls back to `method='residual'` when no concave echo
    peak is found (e.g. the trace already starts at the zero-time).

    `xcheck` (default OFF -- opt-in) targets the parabola's one failure mode: a
    FLAT, SHALLOW echo top at high noise. There the maximum is ill-defined and an
    upward noise excursion late in the top drags the vertex tens of ns LATE
    (a systematic late bias that grows with noise -- e.g. +27 ns at sigma 0.04 on
    the synthetic benchmark, vs ~1 ns at low noise). With `xcheck` the
    residual-based t0 is also computed and, when the two disagree by more than
    `xcheck_tol_frac` of the trace span (~0.4 %), the more robust residual is used.

    CAVEAT -- `xcheck` is now WORSE ON BOTH AXES and should stay off. Re-measured
    2026-08-04 over 252 catalogue traces: it raises the mean |t0| error from 8.5 to
    21.3 ns (worst 84 -> 150) AND costs distance overlap on both engines,
    -0.0215 (t -6.5) on Tikhonov and -0.0196 (t -5.5) on Mellin, losing on ~81 % of
    traces at every noise level.

    That is a simpler verdict than the one this docstring used to give, and the
    reason it changed is worth keeping: the older text said xcheck LOWERED the mean
    t0 error (5.1 -> 4.0 ns) and was off only because a slightly-late t0 happened to
    compensate a Mellin forward bias. Both legs are stale. The parabola/centroid
    estimator has improved since (noise-aware gate, symmetric window, boundary and
    vertex checks), so the residual search it defers to is no longer the more robust
    of the two -- deferring to it now just injects the residual path's own variance.
    No Mellin-specific argument is needed to justify the default any more.

    `method='residual'` aligns the kernel by minimizing the V-space reconstruction
    residual (the original method; needs r/dim/bg_start, robust when the echo
    maximum is ambiguous or absent):

    DEER is sensitive to where t = 0 of the dipolar evolution sits: an error of
    even a few tens of ns misaligns the kernel, broadens P(r) and biases the mean
    distance long. DeerLab fits this `reftime` by default; this is the equivalent
    for the engines here. A candidate offset s shifts both the time axis and the
    (data-anchored) background window, so only the kernel alignment changes; the
    residual ‖V - V_fit‖ is smooth with a single minimum in s, so a coarse grid
    over the first `search_frac` of the trace plus a parabolic refine pins it down
    in ~`n_grid` inversions.

    t, V, bg_start, bg_end are in the kernel time unit (µs). `kwargs` pass through
    to `deer_invert` (r, dim, fit_dim, alpha, alpha_factor, ...). Returns the
    optimal t0 in the same units as `t`.

    For speed the search uses a fixed-alpha *sequential* inversion at each offset:
    t0 is set by the shape of the residual, not by the engine or the exact
    regularization, so this avoids a per-offset GCV scan and the slower joint
    background fit. The caller runs its chosen engine once at the returned t0.
    """
    t = np.asarray(t, float)
    V = np.asarray(V, float)
    t0_para = None
    if method == 'parabola':
        t0_para = _parabolic_zero_time(t, V, drop=drop, smooth_w=smooth_w,
                                       search_frac=max(search_frac, 0.30))
        # parabola succeeded and no cross-check requested: original fast path
        if t0_para is not None and not xcheck:
            return t0_para
    span = float(t[-1] - t[0]) or 1.0
    grid = np.linspace(float(t[0]), float(t[0]) + search_frac*span,
                       int(max(3, n_grid)))

    # fast, fixed-alpha sequential inversion for the search, on a capped distance
    # grid (t0 is set by the residual shape, not the P(r) resolution)
    opts = dict(kwargs)
    opts['engine'] = 'sequential'
    opts['scan_lcurve'] = False
    opts['pre_zero'] = 'crop'     # fixed sample set, or the residual is a staircase in s
    opts.pop('alpha_factor', None)
    rr = opts.get('r')
    if rr is not None and len(np.asarray(rr)) > 100:
        rr = np.asarray(rr, float)
        opts['r'] = np.linspace(rr[0], rr[-1], 100)
    if opts.get('alpha') is None:                 # select alpha once, then hold it
        s0 = float(grid[len(grid)//2])
        try:
            res0 = deer_invert(t - s0, V,
                               bg_start=(None if bg_start is None else bg_start - s0),
                               bg_end=(None if bg_end is None else bg_end - s0),
                               **opts)
            opts['alpha'] = float(res0['alpha'])
        except Exception:
            opts['alpha'] = None

    def resid_at(s):
        try:
            res = deer_invert(t - s, V,
                              bg_start=(None if bg_start is None else bg_start - s),
                              bg_end=(None if bg_end is None else bg_end - s),
                              **opts)
        except Exception:
            return np.inf
        bg = res['background']
        lam = res['lambda']
        v_fit = bg['B']*((1 - lam) + lam*res['F_fit'])
        return float(np.sqrt(np.mean((bg['V_norm'] - v_fit)**2)))

    rs = np.array([resid_at(s) for s in grid])
    i = int(np.argmin(rs))
    t0_resid = float(grid[i])
    # parabolic refine through the grid minimum and its two neighbours
    if refine and 0 < i < len(grid) - 1 and np.all(np.isfinite(rs[i-1:i+2])):
        y0, y1, y2 = rs[i-1], rs[i], rs[i+1]
        denom = y0 - 2*y1 + y2
        if denom > 0:
            t0_resid = float(grid[i] + 0.5*(y0 - y2)/denom*(grid[1] - grid[0]))
    # Reconcile the parabola with the residual cross-check: keep the (more
    # accurate) parabola when they agree; defer to the robust residual when they
    # diverge -- the flat-shallow-top high-noise failure (see the docstring). When
    # the parabola found no concave echo (t0_para is None) the residual is the
    # only estimate.
    if t0_para is None:
        return t0_resid
    if abs(t0_para - t0_resid) > xcheck_tol_frac*span:
        return t0_resid
    return t0_para


# --------------------------------------------------------------------------- #
#  Validation (DeerAnalysis-style ensemble averaging)
# --------------------------------------------------------------------------- #
def _bg_start_grid(t, center, span_frac=0.075, n=9):
    """Default background-start sweep: n points spanning +/- span_frac of the
    trace length around `center`, clipped to a sensible interior window."""
    t = np.asarray(t, float)
    t0, t1 = float(t.min()), float(t.max())
    span = t1 - t0
    if center is None:
        center = t0 + 0.5*span
    half = span_frac*span
    lo = max(center - half, t0 + 0.1*span)
    hi = min(center + half, t1 - 0.05*span)
    if hi <= lo:
        return np.array([float(np.clip(center, t0 + 0.1*span, t1 - 0.05*span))])
    return np.linspace(lo, hi, int(n))


def deer_validate(t, V, r=None, bg_start=None, bg_starts=None, bg_end=None,
                  dim=3.0, fit_dim=False, alpha=None, alpha_factor=1.0,
                  reg_order=2, nu_dd=NU_DD, method='gcv', engine='sequential',
                  noise=0.0, n_noise=0, seed=0, percentiles=(5, 95),
                  pre_zero='even', clamp_alias=True, **kwargs):
    """DeerAnalysis-style validation: hold the regularization fixed, re-run the
    inversion over a grid of background-start times (and optionally added-noise
    realizations), collect the ensemble of P(r), and return the consensus P(r)
    with a percentile band. Averaging over the trials suppresses the noise-driven
    spikes a single GCV inversion leaves in P(r), giving a smooth distribution
    plus an honest uncertainty band -- the procedure behind the smooth, banded
    distributions of Fig. 4 in Schiemann et al., JACS 2021 (10.1021/jacs.1c07371).

    `bg_starts` is the explicit sweep of background-start times; when None a
    9-point grid spanning +/- 7.5% of the trace around `bg_start` (or the trace
    midpoint) is used. alpha is selected once on the central trace (honouring
    `alpha`/`alpha_factor`) and then held fixed for every trial -- validation
    probes background/noise sensitivity, not the regularization choice. For
    `engine='mellin'` alpha is not the regularizer, so `tau_max` (with its
    `n_tau` grid) and `delta` are pinned to the central trial instead. On
    `engine='gauss'` there is no regularizer at all and `method` names the SOLVER
    ('lsq' / 'mc') rather than the alpha criterion -- see `deer_invert`; what is
    pinned there is the component count `n_gauss`, since re-selecting it per trial
    would put a model switch inside a band that is meant to show background-start
    sensitivity. Every trial's count is reported in `trials[i]['n_gauss']`. With
    `noise` > 0 and `n_noise` > 0, each background-start trial is additionally
    repeated with `n_noise` Gaussian-noise realizations of std `noise` added to V
    (estimate `noise` from the trace residual). All trials share the grid `r`.

    Returns a dict: r, P_density (the ensemble *median* -- the robust consensus
    curve, always bracketed by the band), P_mean (ensemble mean, exposed for
    reference), P_lower, P_upper (the `percentiles` band), ensemble
    (n_trials x len(r) densities), n_trials, bg_starts, alpha (the fixed value),
    peak (consensus-curve peak r), r_mean (its first moment), base = the
    single inversion at the central bg_start (its form factor / fit / residuals
    for display), trials (per-trial bg_start / r_mean / lambda / k / n_gauss /
    flagged) and
    trial_spread (their ranges plus `disagree`, true when a majority of trials
    raise a background flag or the trial mean distances span more than
    max(0.15 nm, 5%) -- the caller's own flags come from `base` alone and cannot
    see a sweep that splits between background branches).

    `trial_spread['band_degenerate']` says the percentile BAND means nothing on
    this run and must not be shown as an uncertainty: either the ensemble is
    flat (spread below 1% of the curve) or the engine co-fits its background, so
    `bg_start` never enters its objective and the sweep cannot probe it. That is
    the case for `engine='gauss'` with any `bg_engine` except 'general' -- but NOT
    for `method='mc'`, which inverts the prepared form factor instead of re-fitting
    and so does follow `bg_start`. The flag half of the sweep (`n_flagged` /
    `disagree`) stays valid either way, since the per-trial background flags are
    rebuilt at every `bg_start`; on the re-fitting engine they are read from
    `background['prep']` and describe that trial's STARTING background.
    """
    _require_scipy()
    t, V, _n_pre = _crop_pre_zero(t, V, policy=pre_zero)
    r = default_r_axis() if r is None else np.asarray(r, float)
    r, r_alias = _apply_alias_floor(t, r, clamp=clamp_alias, nu_dd=nu_dd)
    if bg_starts is None:
        bg_starts = _bg_start_grid(t, bg_start)
    bg_starts = np.atleast_1d(np.asarray(bg_starts, float))
    reps = max(int(n_noise), 0) if noise > 0 else 0
    rng = np.random.default_rng(seed)
    dr = float(r[1] - r[0]) if len(r) > 1 else 1.0
    bs_mid = float(bg_starts[len(bg_starts)//2])
    af_mid = float(alpha_factor)

    # Pick alpha ONCE on the central background, then hold it fixed across every
    # trial (DeerAnalysis-style validation tests background-start / noise
    # sensitivity, not the regularization choice). Holding alpha fixed also drops
    # the per-trial L-curve scan -- the costly part -- so validation stays fast.
    # r is clamped above; forward the flag or a per-trial re-clamp changes its length
    base = deer_invert(t, V, r=r, bg_start=bs_mid, bg_end=bg_end, dim=dim,
                       fit_dim=fit_dim, alpha=alpha, alphas=None,
                       reg_order=reg_order, nu_dd=nu_dd, method=method,
                       engine=engine, alpha_factor=af_mid,
                       clamp_alias=clamp_alias, **kwargs)
    alpha_fixed = float(base['alpha'])
    # the Mellin regularizer is tau_max, not alpha (and n_tau follows tau_max)
    if engine == 'mellin':
        kwargs['tau_max'] = float(base['tau_max'])
        kwargs['n_tau'] = int(len(base['tau']))
        kwargs['delta'] = float(base['delta'])
    # the multi-Gaussian model complexity is N, and it is re-selected per trial
    # unless pinned: the ensemble then mixes component counts and the percentile
    # band reads as background sensitivity when part of it is a model switch (a
    # 1 -> 2 Gaussian jump moves P(r) far more than the background start does).
    # Pin it to the central trial's pick, exactly as tau_max is pinned above.
    elif engine == 'gauss':
        kwargs['n_gauss'] = int(base['n_gauss'])

    def _invert(Vx, bs):
        return deer_invert(t, Vx, r=r, bg_start=bs, bg_end=bg_end, dim=dim,
                           fit_dim=fit_dim, alpha=alpha_fixed, scan_lcurve=False,
                           reg_order=reg_order, nu_dd=nu_dd, method=method,
                           engine=engine, clamp_alias=clamp_alias, **kwargs)

    ensemble = []
    trials_stat = []
    for bs in bg_starts:
        trials = [V] + [V + noise*rng.standard_normal(V.shape)
                        for _ in range(reps)]
        for Vx in trials:
            try:
                res_i = _invert(Vx, bs)
            except Exception:
                continue
            ensemble.append(res_i['P_density'])
            # per-trial scalars: the caller otherwise only ever sees `base`
            bg_i = res_i.get('background') or {}
            # an engine that re-fits its background parks these under 'prep'
            rel_i = bg_i.get('prep') or bg_i
            m_i = _normalize_masses(np.clip(res_i['P_density'], 0.0, None)*dr)
            trials_stat.append(
                {'bg_start': float(bs), 'r_mean': float(np.sum(r*m_i)),
                 'lambda': float(res_i.get('lambda', float('nan'))),
                 'k': float(res_i.get('k', float('nan'))),
                 'n_gauss': res_i.get('n_gauss'),
                 'flagged': bool(rel_i.get('lambda_clamped')
                                 or rel_i.get('k_disagrees')
                                 or float(rel_i.get('tail_abs_F') or 0.0) > 0.05)})
    if not ensemble:
        raise RuntimeError('DEER validation produced no successful trials.')
    ens = np.vstack(ensemble)
    P_mean = ens.mean(axis=0)
    P_median = np.median(ens, axis=0)
    lo, hi = percentiles
    P_lower = np.percentile(ens, lo, axis=0)
    P_upper = np.percentile(ens, hi, axis=0)
    P_mass = _normalize_masses(P_median*dr)
    rm = np.array([s['r_mean'] for s in trials_stat], float)
    lam_t = np.array([s['lambda'] for s in trials_stat], float)
    n_flag = int(sum(s['flagged'] for s in trials_stat))
    rm_spread = float(np.ptp(rm)) if rm.size else float('nan')
    # a MAJORITY must flag: any-one is a false alarm on healthy real data
    disagree = bool(n_flag*2 > len(trials_stat)
                    or (rm.size and rm_spread > max(0.15, 0.05*float(rm.mean()))))
    # Does the background start reach this engine's OBJECTIVE at all? The
    # multi-Gaussian engine re-fits background + lambda in V-space against
    # V_norm, which is bg_start-free, so bg_start moves only the starting point:
    # the trials then differ by flat-valley jitter orders below a real band, and
    # a percentile band drawn from them reads as certainty rather than as
    # "not measured". The FLAG half of the sweep stays meaningful (the per-trial
    # background flags are rebuilt per bg_start), so only the band is disowned.
    # method='mc' is exempt: it never re-fits, it inverts the PREPARED form factor,
    # which is built at bg_start, so the sweep does move its objective. Read the
    # solver off the result, not off the arguments -- `method` here is the alpha
    # selector, and the gauss solver reaches the engine by its own route.
    bg_cofit = bool(engine == 'gauss' and base.get('method') != 'mc'
                    and kwargs.get('bg_engine', 'joint') != 'general')
    P_spread = float(np.max(np.ptp(ens, axis=0))) if ens.shape[0] > 1 else 0.0
    P_scale = float(np.max(np.abs(P_median))) or 1.0
    spread = {'r_mean_spread': rm_spread,
              'lambda_spread': float(np.ptp(lam_t)) if lam_t.size else float('nan'),
              'n_flagged': n_flag, 'n': len(trials_stat), 'disagree': disagree,
              'P_spread': P_spread, 'P_scale': P_scale,
              'band_degenerate': bool(bg_cofit or P_spread < 0.01*P_scale)}
    return {'r': r, 'P_density': P_median, 'P_mean': P_mean,
            'P_lower': P_lower, 'P_upper': P_upper, 'ensemble': ens,
            'n_trials': ens.shape[0], 'bg_starts': bg_starts,
            'alpha': alpha_fixed, 'r_alias': float(r_alias),
            'peak': float(r[int(np.argmax(P_median))]),
            'r_mean': float(np.sum(r*P_mass)), 'base': base,
            'trials': trials_stat, 'trial_spread': spread,
            'percentiles': tuple(percentiles), 'engine': engine}


def simulate(t, r, P, lam=0.3, k=0.05, dim=3.0, nu_dd=NU_DD, noise=0.0, seed=None):
    """Forward-simulate a DEER trace from a distance distribution P(r).

    V(t) = [(1 - lam) + lam * (K P_masses)] * exp(-(k|t|)^(d/3)) (+ Gaussian
    noise). `t` in us, `r` in nm. Returns V(t) with V(0) = 1 (noise aside).
    """
    _require_scipy()
    t = np.asarray(t, float)
    r = np.asarray(r, float)
    Pn = _normalize_masses(np.asarray(P, float))
    form = dipolar_kernel(t, r, nu_dd=nu_dd)@Pn
    B = np.exp(-(k*np.abs(t))**(dim/3.0))
    V = ((1 - lam) + lam*form)*B
    if noise > 0:
        rng = np.random.default_rng(seed)
        V = V + noise*rng.standard_normal(V.shape)
    return V


# --------------------------------------------------------------------------- #
#  Headless self-test: synthetic round-trip
# --------------------------------------------------------------------------- #
if __name__ == '__main__':
    if not SCIPY_AVAILABLE:
        raise SystemExit('scipy not available; install with pip install -e .[math]')
    r = default_r_axis(2.0, 6.0, 200)
    r0, sig = 3.5, 0.25
    P_true = np.exp(-0.5*((r - r0)/sig)**2)             # density (un-normalized)
    t = np.linspace(0.0, 2.5, 256)                      # us
    V = simulate(t, r, P_true, lam=0.35, k=0.10, dim=3.0, noise=0.01, seed=1)

    res = deer_invert(t, V, r=r, bg_start=1.0)
    F, Ff = res['form_factor'], res['F_fit']
    ss_res = float(np.sum((F - Ff)**2))
    ss_tot = float(np.sum((F - F.mean())**2))
    r2 = 1 - ss_res/ss_tot
    r_peak = r[int(np.argmax(res['P_density']))]
    # first moment of the recovered distribution
    r_mean = float(np.sum(res['r']*res['P_norm']))

    print(f'recovered lambda = {res["lambda"]:.3f}  (true 0.350)')
    print(f'recovered k      = {res["k"]:.3f}  (true 0.100)')
    print(f'alpha (L-corner) = {res["alpha"]:.4g}')
    print(f'form-factor fit R^2 = {r2:.4f}')
    print(f'P(r) peak  = {r_peak:.3f} nm  (true {r0:.3f})')
    print(f'P(r) mean  = {r_mean:.3f} nm')
    ok = (abs(r_peak - r0) < 0.3) and (r2 > 0.95) and (abs(res['lambda'] - 0.35) < 0.1)

    # alpha_factor: heavier regularization must smooth (lower roughness ||L P||)
    Lr = regularization_matrix(len(r), 2)
    res_h = deer_invert(t, V, r=r, bg_start=1.0, alpha_factor=4.0)
    rough = lambda d: float(np.linalg.norm(Lr@d['P_norm']))
    print(f'alpha x1 = {res["alpha"]:.4g}  roughness {rough(res):.4g}')
    print(f'alpha x4 = {res_h["alpha"]:.4g}  roughness {rough(res_h):.4g}')
    smoother = (res_h['alpha'] > res['alpha']) and (rough(res_h) < rough(res))

    # validation ensemble: smooth mean curve + band that brackets it
    val = deer_validate(t, V, r=r, bg_start=1.0, noise=0.01, n_noise=3, seed=2)
    band_ok = (np.all(val['P_lower'] <= val['P_density'] + 1e-12) and
               np.all(val['P_density'] <= val['P_upper'] + 1e-12))
    print(f'validation: {val["n_trials"]} trials, peak {val["peak"]:.3f} nm, '
          f'mean {val["r_mean"]:.3f} nm, band_ok {band_ok}')

    # analytic Mellin transform engine: recover the same single peak (model-free)
    mel = deer_invert_mellin(t, V, r=r, bg_start=1.0, tau_max=25, n_tau=2001)
    Fm, Ffm = mel['form_factor'], mel['F_fit']
    r2m = 1 - float(np.sum((Fm - Ffm)**2))/float(np.sum((Fm - Fm.mean())**2))
    r_peak_m = r[int(np.argmax(mel['P_density']))]
    mellin_ok = (abs(r_peak_m - r0) < 0.3) and (r2m > 0.8)
    print(f'mellin: delta {mel["delta"]:.4g} us, peak {r_peak_m:.3f} nm, '
          f'forward R^2 {r2m:.4f}, mellin_ok {mellin_ok}')

    # multi-Gaussian engine: parametric N-Gaussian fit recovers the single mode
    gss = deer_invert_gauss(t, V, r=r, bg_start=1.0)
    r_peak_g = r[int(np.argmax(gss['P_density']))]
    gauss_ok = (gss['n_gauss'] == 1) and (abs(r_peak_g - r0) < 0.3)
    print(f'gauss: N {gss["n_gauss"]}, peak {r_peak_g:.3f} nm, '
          f'lambda {gss["lambda"]:.3f}, ok {gauss_ok}')

    print('SELF-TEST:', 'PASS' if (ok and smoother and band_ok and mellin_ok and
          gauss_ok and abs(val['peak'] - r0) < 0.3) else 'FAIL')
