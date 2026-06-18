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

import numpy as np

# scipy is an optional dependency (pip install -e .[math]) and slow to import
# (~0.6 s on Windows). Probe availability cheaply -- find_spec does NOT import
# scipy -- and defer the real import to _require_scipy(), so importing this
# module stays numpy-only and GUIs that embed it start fast.
import importlib.util
SCIPY_AVAILABLE = importlib.util.find_spec('scipy') is not None
fresnel = nnls = curve_fit = None

# np.trapz was renamed np.trapezoid in NumPy 2.0 (np.trapz deprecated); pick
# whichever exists so the Mellin quadrature stays warning-free on either.
_trapz = getattr(np, 'trapezoid', getattr(np, 'trapz'))

# Perpendicular dipolar frequency constant: nu_perp = NU_DD / r^3 [MHz], r in nm
# (g = 2.0023). w(r) = 2*pi*nu_perp is then in rad/us for t in us.
NU_DD = 52.04  # MHz nm^3


def _require_scipy():
    """Lazily import scipy on first use and bind the symbols this module needs.
    Every scipy-using function calls this first, so the module-level fresnel /
    nnls / curve_fit globals are guaranteed populated before they are read."""
    global fresnel, nnls, curve_fit
    if not SCIPY_AVAILABLE:
        raise RuntimeError('DEER analysis requires scipy (pip install -e .[math]).')
    if fresnel is None:
        from scipy.special import fresnel as _fresnel
        from scipy.optimize import nnls as _nnls, curve_fit as _curve_fit
        fresnel, nnls, curve_fit = _fresnel, _nnls, _curve_fit


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
    lam = float(np.clip(1.0 - float(np.mean(V[mask])), 0.02, 1.0))
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
    if abs(lam) < 1e-6:
        lam = 1e-6
    F = (V/B - (1 - lam))/lam
    return {'lambda': lam, 'k': float(k), 'dim': float(d), 'A': float(A),
            'B': B, 'form_factor': F, 'V_norm': V, 't': t,
            'bg_start': float(bg_start),
            'bg_end': (None if bg_end is None else float(bg_end)), 'mask': mask}


def background_general(t, V, bg_start, bg_end=None, **_ignored):
    """General empirical intermolecular background fit on the tail window
    bg_start <= t (<= bg_end):

        g(t) = a + b*t + c*d^t        (offset + linear drift + exponential, base d)

    A flexible alternative to the stretched-exponential `background_fit` for traces
    whose intermolecular decay is not well described by exp(-(k|t|)^(d/3)) -- the
    four parameters a, b, c, d are free. Same convention as `background_fit`: V is
    normalized to V(0)=1, the fitted tail baseline g(t) = (1-lambda)*B(t), so the
    background normalized to B(0)=1 is B(t) = g(t)/g(0), the modulation depth is
    lambda = 1 - g(0) (g(0) = a + c, since d^0 = 1), and

        F(t) = (V(t)/B(t) - (1 - lambda)) / lambda .

    `d` is constrained to (0, 1] so the exponential term decays (a growing
    background is unphysical for the intermolecular contribution). Returns the same
    dict shape as `background_fit`, with k / dim = NaN (not applicable) and the
    fitted coefficients in `params` (a, b, c, d) and `model` = 'general'.
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
    if int(mask.sum()) < 4:
        raise ValueError('Background region has too few points; widen [bg_start, bg_end].')
    tt, vv = t[mask], V[mask]
    span = float(tt[-1] - tt[0]) or 1.0

    def _model(x, a, b, c, d):
        d = min(max(float(d), 1e-9), 1.0)
        return a + b*x + c*np.power(d, x)

    # The exponential term must be a genuine (slow) BACKGROUND decay -- if d is so
    # small that c*d^t has already collapsed before the fit window, c and d are
    # unconstrained by the tail and the extrapolation to g(0) blows up. Bound d so
    # the term still retains >= 5% of its t=0 amplitude at the END of the fit
    # window (d^span >= 0.05), which keeps it data-constrained; a faster decay is
    # not an intermolecular background anyway. The linear term carries any residual
    # gentle drift.
    d_lo = float(np.clip(0.05**(1.0/span), 0.05, 0.95))
    a0 = float(vv[-1])                                 # tail-end baseline
    b0 = float((vv[-1] - vv[0])/span)                  # gentle slope
    c0 = float(np.clip(vv[0] - vv[-1], -1.0, 1.0))     # exp amplitude across the tail
    d0 = float(np.sqrt(d_lo))
    p0 = [a0, b0, c0, d0]
    bounds = ([-np.inf, -np.inf, -np.inf, d_lo], [np.inf, np.inf, np.inf, 1.0])
    try:
        popt, _ = curve_fit(_model, tt, vv, p0=p0, bounds=bounds, maxfev=10000)
    except Exception:
        popt = p0
    a, b, c, d = (float(x) for x in popt)
    g = _model(t, a, b, c, d)                         # = (1-lambda)*B(t) baseline
    g0 = a + c                                         # g(0): d^0 = 1
    lam = float(np.clip(1.0 - g0, 0.02, 0.98))
    B = g/g0 if abs(g0) > 1e-9 else np.ones_like(t)
    F = (V/np.clip(B, 1e-3, None) - (1 - lam))/lam
    return {'lambda': lam, 'k': float('nan'), 'dim': float('nan'), 'A': float(g0),
            'B': B, 'form_factor': F, 'V_norm': V, 't': t,
            'bg_start': float(bg_start),
            'bg_end': (None if bg_end is None else float(bg_end)), 'mask': mask,
            'model': 'general', 'params': {'a': a, 'b': b, 'c': c, 'd': d}}


# --------------------------------------------------------------------------- #
#  Tikhonov regularization + non-negativity
# --------------------------------------------------------------------------- #
def regularization_matrix(n, order=2):
    """Discrete derivative operator L for Tikhonov smoothing (default 2nd order)."""
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
    P, _ = nnls(A, b)
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
                     Robust for DEER, whose L-curve is nearly vertical (the
                     residual stays at the noise floor across decades of alpha),
                     so the classic L-corner is ill-defined and tends to pick a
                     tiny alpha => spiky P(r).
      'curvature' -- classic maximum-Menger-curvature L-corner.

    GCV uses the (unconstrained) Tikhonov influence-matrix trace as the effective
    degrees of freedom paired with the NNLS residual -- the standard DEER GCV
    approximation.

    Returns dict: alphas, rho, eta, curvature, gcv, alpha_opt, index, method,
    P (the solution at the chosen alpha).
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
    if method == 'curvature':
        idx = int(np.argmax(kappa)) if len(alphas) > 2 else len(alphas)//2
    else:                                             # 'gcv' (default)
        idx = int(np.argmin(gcv))
    return {'alphas': alphas, 'rho': rho, 'eta': eta, 'curvature': kappa,
            'gcv': gcv, 'alpha_opt': float(alphas[idx]), 'index': idx,
            'method': method, 'P': Ps[idx]}


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
    """Covariance-based confidence band on the regularized P(r) — the asymptotic
    (curvature) CI DeerLab shows by default.

    For the linear Tikhonov estimator P = (KᵀK + α²LᵀL)⁻¹ Kᵀ F, the noise on the
    form factor propagates as cov(P) = σ² M Mᵀ with M = (KᵀK + α²LᵀL)⁻¹ Kᵀ and σ²
    estimated from the fit residuals (effective dof = N − tr(K M)). Returns
    (lower, upper) at confidence z (default 95%) on the same density scale as
    P/sum(P)/dr, clipped at 0. The non-negativity constraint is not propagated, so
    the band is a slightly conservative linear approximation (as in DeerLab's
    moment-based CI)."""
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
                alpha_factor=1.0, **kwargs):
    """Full DEER pipeline: background-correct V(t), build the kernel, invert to
    P(r) by Tikhonov + NNLS. When `alpha` is not supplied it is chosen
    automatically by `method` ('gcv' default, or 'curvature' for the classic
    L-corner) -- see `l_curve`.

    `alpha_factor` scales the auto-selected alpha (ignored when an explicit
    `alpha` is given). GCV/AIC tend to under-regularize the near-vertical DEER
    L-curve, leaving noise spikes in P(r); a factor > 1 (e.g. 2-4) reproduces
    the heavier hand-picked L-corner regularization the DeerAnalysis ring-test
    labs used to get smooth distributions (Schiemann et al., JACS 2021).

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

    `t` in us, `r` in nm. With `scan_lcurve` (default) the regularization scan is
    always computed for display, even when an explicit `alpha` is given. Returns a dict:
    t, r, form_factor F(t), F_fit = K P, residuals, P (raw masses), P_norm
    (masses, sum = 1), P_density (P_norm / dr, integrates to 1), kernel, alpha,
    l_curve (when scanned), background result, lambda / k / dim, and engine.
    """
    if engine == 'joint':
        return deer_invert_joint(t, V, r=r, bg_start=bg_start, bg_end=bg_end,
                                 dim=dim, fit_dim=fit_dim, alpha=alpha,
                                 alphas=alphas, reg_order=reg_order, nu_dd=nu_dd,
                                 method=method, scan_lcurve=scan_lcurve,
                                 alpha_factor=alpha_factor)
    if engine == 'mellin':
        return deer_invert_mellin(t, V, r=r, bg_start=bg_start, bg_end=bg_end,
                                  dim=dim, fit_dim=fit_dim, nu_dd=nu_dd, **kwargs)
    if engine == 'gauss':
        return deer_invert_gauss(t, V, r=r, bg_start=bg_start, bg_end=bg_end,
                                 dim=dim, fit_dim=fit_dim, nu_dd=nu_dd, **kwargs)
    _require_scipy()
    t = np.asarray(t, float)
    V = np.asarray(V, float)
    r = default_r_axis() if r is None else np.asarray(r, float)
    if bg_start is None:
        bg_start = t[0] + 0.5*(t[-1] - t[0])
    if engine == 'none':          # no intermolecular background (B=1); fit lambda only
        bg = _no_background(t, V, bg_start=bg_start, bg_end=bg_end)
    elif engine == 'general':     # general empirical background a + b*t + c*d^t
        bg = background_general(t, V, bg_start, bg_end=bg_end)
    else:
        bg = background_fit(t, V, bg_start, bg_end=bg_end, dim=dim, fit_dim=fit_dim)
    F = bg['form_factor']
    K = dipolar_kernel(t, r, nu_dd=nu_dd)
    L = regularization_matrix(len(r), reg_order)
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
    return {'t': t, 'r': r, 'form_factor': F, 'F_fit': F_fit,
            'residuals': F - F_fit, 'P': P, 'P_norm': P_norm,
            'P_density': P_density, 'P_lower': P_lower, 'P_upper': P_upper,
            'kernel': K, 'alpha': float(alpha),
            'l_curve': lc, 'background': bg, 'lambda': bg['lambda'],
            'k': bg['k'], 'dim': bg['dim'],
            'engine': engine if engine in ('none', 'general') else 'sequential'}


def deer_invert_joint(t, V, r=None, bg_start=None, bg_end=None, dim=3.0,
                      fit_dim=False, alpha=None, alphas=None, reg_order=2,
                      nu_dd=NU_DD, method='gcv', scan_lcurve=True,
                      alpha_factor=1.0):
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
    """
    _require_scipy()
    t = np.asarray(t, float)
    V = np.asarray(V, float)
    r = default_r_axis() if r is None else np.asarray(r, float)
    K = dipolar_kernel(t, r, nu_dd=nu_dd)
    L = regularization_matrix(len(r), reg_order)
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
    P_norm = _normalize_masses(P_masses)
    dr = float(r[1] - r[0]) if len(r) > 1 else 1.0
    F_fit = K@P_norm
    P_lower, P_upper = tikhonov_ci(K, F, alpha_use, P_masses, L=L, dr=dr)
    return {'t': t, 'r': r, 'form_factor': F, 'F_fit': F_fit,
            'residuals': F - F_fit, 'P': P_masses, 'P_norm': P_norm,
            'P_density': P_norm/dr, 'P_lower': P_lower, 'P_upper': P_upper,
            'kernel': K, 'alpha': float(alpha_use),
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
#    The sinh integrand has unit modulus near u=0 (Re(1-2s)=0 on the line), so a
#    plain grid integrates it accurately. Valid for 0 < Re s < 3/2.
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
                           fit_level=0.80):
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
    F has fallen to `fit_level`*F0) so a few delta-wide samples cannot make it
    noisy. Set parabolic=False for the original constant-F split."""
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
        msk = Tp <= max(wfit, delta)
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


def joint_background(t, V, bg_start=None, bg_end=None, dim=3.0, fit_dim=False,
                     nu_dd=NU_DD, n_r=60, rate_alpha=1.0, lam_pin_frac=0.5):
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

    The rate-fit distance cap is *adaptive*: k is fit on both the trace-supported
    tight cap (r_max ~ 5*(Tmax/2)^(1/3)) and a wider one, preferring the wider
    result unless it collapses toward a flat background (the long-r/background
    degeneracy the tight cap guards against). This stops a genuine broad/long-r
    component being forced into the background -- which would leave a pedestal in
    F that the Mellin engine (phi -> 0) renders as a drooping forward fit at long
    T -- while still keeping k determined on short single-peak traces.
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
        return min(max(1.0 - float(np.mean((V/B)[pin_mask])), 0.02), 0.95)

    def _fit_rate(rmax_cap):
        """Fit the background rate k (and d when fit_dim) jointly with a coarse
        non-negative P(r) on a distance grid truncated at rmax_cap. Returns
        (k, d)."""
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
                return abs(sol.x[0]), min(max(sol.x[1], 1.0), 6.0)
            except Exception:
                return kref, d0
        try:
            sol = minimize_scalar(lambda lk: vss(np.exp(lk), d0),
                                  bounds=(np.log(kref/100.0), np.log(kref*100.0)),
                                  method='bounded', options={'xatol': 3e-2})
            return float(np.exp(sol.x)), d0
        except Exception:
            return kref, d0

    # Adaptive distance cap (the long-r / background degeneracy guard). The tight
    # cap is the trace-length-supported r_max (DeerAnalysis rule): it keeps k
    # determined on short single-peak traces. But when a genuine broad/long-r
    # component sits near r_max, the tight cap forces that slow modulation into
    # the background -> k biased high and a residual pedestal in F that the Mellin
    # kernel (phi -> 0) cannot represent (its forward fit then droops at long T).
    # So fit at a WIDER cap too and prefer it, UNLESS widening makes the
    # background collapse toward flat (k -> ~0, <5% decay over the trace) while
    # also dropping well below the tight estimate -- the degeneracy the tight cap
    # exists to stop. This keeps both failure modes in check.
    rmax_tight = float(np.clip(5.0*(Tmax/2.0)**(1.0/3.0), 3.0, 8.0))
    rmax_wide = float(min(8.0, max(rmax_tight*1.6, rmax_tight + 1.0)))
    k_t, d_t = _fit_rate(rmax_tight)
    k_w, d_w = _fit_rate(rmax_wide)
    decay_w = 1.0 - float(np.exp(-(k_w*Tmax)**(d_w/3.0)))
    collapsed = (k_w < 0.5*k_t) and (decay_w < 0.05)
    k, d = (k_t, d_t) if collapsed else (k_w, d_w)
    B = np.exp(-(k*np.abs(t))**(d/3.0))
    lam = lam_of(B)
    F = (V/B - (1 - lam))/lam
    return {'lambda': lam, 'k': float(k), 'dim': float(d), 'A': float(1 - lam),
            'B': B, 'form_factor': F, 'V_norm': V, 't': t,
            'bg_start': float(bg_start),
            'bg_end': (None if bg_end is None else float(bg_end)), 'mask': mask}


def mellin_delta(t, F, level=0.95, floor=0.09, cap=0.12):
    """Practical split point delta: the first T > 0 where the form factor has
    fallen to `level` of F(0) (the paper's F(delta) ~ 0.95 estimate). Falls back
    to the first positive sample if F never drops that far.

    The raw F-level estimate is then clipped to [`floor`, `cap`] (in the kernel
    time unit, us). The floor is the key correction for *sharp* distributions:
    a fast-decaying form factor crosses `level` within a couple of samples, which
    leaves the analytic parabolic [0,delta] echo-top anchor too narrow -- the
    'thin parabola' at t=0 -- so the recovered F_fit top comes out too steep and
    the short-r density is unstable. Widening delta to ~90 ns gives the parabolic
    term enough low-T support; the cap (~120 ns) stops a slow-decaying (long-r)
    trace from over-smoothing P(r) by handling too much of the modulation
    analytically. Both bounds were tuned on the synthetic benchmark (overlap-
    optimal across 13 distributions x 4 noise levels x 2 conditions; the floor
    lifts e.g. gauss_narrow easy from 0.90 to 0.92). Set floor/cap to None to
    disable. The bounds are also clamped to the trace so delta never exceeds the
    last positive sample."""
    t = np.asarray(t, dtype=float)
    F = np.asarray(F, dtype=float)
    pos = t > 0
    Tp, Fp = t[pos], F[pos]
    order = np.argsort(Tp)
    Tp, Fp = Tp[order], Fp[order]
    if len(Tp) == 0:
        return 1e-3
    f0 = float(Fp[0]) or 1.0
    below = np.where(Fp < level*f0)[0]
    d = float(Tp[below[0]]) if len(below) else float(Tp[0])
    if floor is not None:
        d = max(d, float(floor))
    if cap is not None:
        d = min(d, float(cap))
    return float(min(d, Tp[-1]))                        # never past the last sample


def _tail_noise(t, y, frac=0.35, smooth_w=7):
    """Electrical white-noise level sigma from the decayed tail, by smoothing.

    Over the last `frac` of the t > 0 trace the dipolar signal is gone (only the
    smooth background + additive electrical noise remain), so sigma is the std of
    (y - moving-average(y)) there, corrected for the variance a width-`w` moving
    average removes: var(y - movavg) = sigma^2 (1 - 1/w). The convolution edge
    (last w points) is excluded."""
    t = np.asarray(t, float); y = np.asarray(y, float)
    yp = y[t > 0]
    n = len(yp)
    if n < 12:
        return 0.0
    w = int(max(3, smooth_w | 1))                       # odd window
    ys = np.convolve(yp, np.ones(w)/w, mode='same')
    resid = yp - ys
    lo, hi = int(n*(1.0 - frac)), n - w                 # tail, minus right edge
    tail = resid[lo:hi] if hi - lo >= 4 else resid[lo:]
    if len(tail) < 4:
        return 0.0
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
      ci95          : +-1.96/sqrt(N), the 95% white-noise band for the ACF.
      white         : bool, |acf1| <= ci95 (residual consistent with white noise).
    """
    e = np.asarray(resid, float)
    e = e[np.isfinite(e)]
    n = int(len(e))
    if n < 4:
        return {'durbin_watson': float('nan'), 'acf1': float('nan'),
                'acf': np.array([1.0]), 'lags': np.array([0]),
                'ci95': float('nan'), 'white': True}
    e = e - e.mean()
    denom = float(np.sum(e*e)) or 1e-30
    dw = float(np.sum(np.diff(e)**2)/denom)
    if max_lag is None:
        max_lag = int(min(max(10, n//5), n - 1))
    lags = np.arange(0, int(max_lag) + 1)
    acf = np.array([float(np.sum(e[k:]*e[:n - k])/denom) for k in lags])
    ci95 = float(1.96/np.sqrt(n))
    return {'durbin_watson': dw, 'acf1': float(acf[1]) if len(acf) > 1 else 0.0,
            'acf': acf, 'lags': lags, 'ci95': ci95,
            'white': bool(abs(acf[1] if len(acf) > 1 else 0.0) <= ci95)}


# Analytic kernel-integral constants I(s) for g=2 (Nekrasov, Matveeva, Syryamina,
# Agarkin & Bowman, Phys. Chem. Chem. Phys. 2026, DOI 10.1039/D5CP04144A; their
# Eqns. 5-6), with s = n/3 for the n-th moment.
_MELLIN_I_S = {1: 4.35466, 2: 3.06158, 3: 2.77339, 4: 2.56993}


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
    Reproduces the paper's reported uniform-acquisition std(M1)=0.0400 nm for
    eps=0.04, dt=24 ns, NT=231 (-> 0.0407 nm). The empirical std of M1 from a full
    Tikhonov / Mellin inversion sits at or below this bound (regularization only
    reduces the noise-driven scatter), so ME_1 is a conservative a priori error
    bar on the recovered mean distance."""
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


def deer_invert_mellin(t, V, r=None, bg_start=None, bg_end=None, dim=3.0,
                       fit_dim=False, nu_dd=NU_DD, delta=None, tau_max=30.0,
                       n_tau=601, bg_engine='joint', n_mc=0, ci_z=1.96, seed=0,
                       taumax_method='penalty', noise_space='V',
                       wiener=0.0, taumax_extend=True, extend_short_frac=0.18,
                       fit_rmin_frac=0.18, signed_fit=True, taper_short=True,
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
    `n_tau` points. `tau_max=None` selects the cutoff automatically by
    `taumax_method`:
      'penalty' (default) -- minimize the forward-fit RMS regularized by a
          SYMMETRIC-NOISE penalty. The fit residual rmsF (RMS of F - F_fit over
          t > 0) falls as the cutoff captures the parabolic echo top, then sits on
          a broad noise-floor plateau; chasing its minimum over-extends and injects
          the noisy high-tau Mellin spectrum into P(r). That injected noise enters
          the area-normalized SIGNED density as paired +bump/-dip excursions, so
          the |negative area| `neg` measures it directly (symmetric: every spurious
          positive spike is balanced by a negative one under area normalization).
          Picks argmin(rmsF/min(rmsF) + neg): the ratio term forces an adequate fit
          (>= 1, large while the echo top is under-resolved), the neg term halts the
          extension once the fit plateaus and the cutoff would only add symmetric
          noise. Self-adapts: clean data plateaus late (sharp P(r) kept), noisy data
          accrues neg early (stays smooth). On the synthetic benchmark it beats the
          older discrepancy floor + leakage extension in both the no-background
          (mean overlap 0.922 -> 0.933) and with-background (0.828 -> 0.831) regimes,
          landing ~0.002-0.003 from the overlap-optimal oracle. The `taumax_extend`
          resolution extension is NOT used (the penalty subsumes it).
      'discrepancy' -- anchor to the NOISE FLOOR: sigma_fit (the V-space forward
          residual) falls with tau_max and flattens at the noise level; chasing its
          minimum overshoots below the floor (an over-fit that injects the noisy
          high-tau spectrum into P(r) -- roughness explodes for a noise-level
          sigma_fit gain). Picks the smallest cutoff whose sigma_fit reaches the
          floor within its statistical spread (floor = std of the V residual's
          successive differences / sqrt2; tolerance ~ 2/sqrt(2N)), then applies the
          `taumax_extend` resolution extension. The prior default; superseded by
          'penalty', which tracks the oracle more closely in both regimes.
      'lcurve' -- corner (max Menger curvature) of (log sigma_fit, log ||L2 P||).
          Provided for comparison; on DEER it under-regularizes because sigma_fit
          is nearly flat in tau_max (a near-vertical L-curve with an ill-defined
          corner), so it tends to pick too large a cutoff on noisy data. Prefer
          'penalty'.
    `taumax_extend` (default on, 'discrepancy' only) is a resolution-aware extension:
    the discrepancy stops as soon as the V-space residual reaches the noise floor,
    but P(r) can keep SHARPENING past that point. After the discrepancy pick the
    cutoff is pushed UP while the spurious short-r leakage (mass in the bottom
    `extend_short_frac` of the r grid -- the Mellin noise signature) keeps DROPPING,
    and stopped at the first increase. Self-adapts to noise: clean/low-noise data
    extends (sharper echo top, better-resolved bimodals -- e.g. a clean narrow
    Gaussian 0.92 -> 0.96 overlap), noisy data does not (the leakage rises at once,
    so it stays at the discrepancy pick). Only active for `taumax_method`
    'discrepancy' and when `tau_max` is auto (None); the default 'penalty' method
    does not use it.

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
    and are not corrected). F_fit is the forward kernel applied to the NON-NEGATIVE
    density with a low-r taper (`fit_rmin_frac`): negatives would flip the t=0
    curvature into a spurious double peak (so they are clipped), and the clipped
    short-r noise spike would make the echo top decay too fast (a too-narrow top),
    so the low-r region -- where the Mellin noise piles up -- is smoothly
    down-weighted for the forward model only. This matches the echo top without a
    double peak; it changes only the fit curve, never the reported P_density. A
    genuine short-r peak is attenuated (not deleted) in F_fit, and is unaffected in
    the displayed P(r). kernel,
    background, lambda / k / dim. Mellin-specific extras: engine='mellin', delta,
    tau_max, auto_taumax, sigma_fit, sigma_noise, P_signed_density (== P_density,
    kept for back-compat), tau, V_image, kernel_image, n_mc. There is no
    covariance band when n_mc=0, and no L-curve, so P_lower / P_upper / l_curve
    are None then.
    """
    _require_scipy()
    t = np.asarray(t, float)
    V = np.asarray(V, float)
    r = default_r_axis() if r is None else np.asarray(r, float)
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
        bg = background_general(t, V, bg_start, bg_end=bg_end)
    else:
        bg = background_fit(t, V, bg_start, bg_end=bg_end, dim=dim, fit_dim=fit_dim)
    F = bg['form_factor']
    Vn, B, lam = bg['V_norm'], bg['B'], bg['lambda']
    # White electrical-noise level from the decayed tail; reused for the MC band.
    sig_e = _tail_noise(t, Vn)
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
        delta = mellin_delta(t, F, level=0.85, floor=0.09 + bump, cap=0.12 + bump)
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

    # Low-r noise penalty for the DISPLAYED forward fit. The Mellin noise piles at
    # short r (the r^-2.5 Jacobian); its positive spike makes the clipped F_fit
    # echo top decay too fast (a too-narrow top), and a hard cut there would wreck
    # F_fit for a genuine short-r peak. So down-weight the low-r density smoothly
    # with a raised-cosine taper (0 at the grid bottom -> 1 by `fit_rmin_frac` of
    # the range): real short-r mass is only attenuated, not deleted. Forward model
    # only -- the reported P_density and the tau_max selection are untouched.
    _u = np.clip((r - r[0])/max(float(fit_rmin_frac)*(r[-1] - r[0]), 1e-9), 0.0, 1.0)
    _fit_w = 0.5*(1.0 - np.cos(np.pi*_u))

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
        top from a large short-r negative noise spike, e.g. low-lambda data). Used
        for BOTH the penalty selector's rmsF and the final reported F_fit, so the
        forward model is consistent between selection and display."""
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
            Vimg = mellin_signal_spectrum(t, Fx, tau_g, delta)
            if eps > 0:
                Ptau = Vimg*np.conj(Phi_g)/(np.abs(Phi_g)**2 + eps)
            else:
                Ptau = Vimg/Phi_g
            return mellin_inverse(np.conj(Ptau), tau_g, w)*(3.0*D/r**4), Vimg
        return tau_g, Phi_g, inv

    def _ntau_for(tm):
        return int(max(401, round(2.0*tm/0.03)))        # fixed dtau ~ 0.03

    def _sigma_fit_at(inv, space='V'):
        fr, _ = inv(F)
        m = _phys(fr)                                   # forward fit uses physical >=0 density
        Ff = K@m
        if space == 'F':                                # form-factor-space residual
            return float(np.std((F - Ff)[pos])) if pos.any() else np.inf
        vfit = B*((1 - lam) + lam*Ff)
        return float(np.std((Vn - vfit)[pos])) if pos.any() else np.inf

    # Auto cutoff (tau_max=None): discrepancy principle anchored to the NOISE
    # FLOOR. The cutoff regularizes the inversion; sigma_fit (the V-space forward
    # residual) decreases with tau_max and flattens once the fit reaches the noise
    # level. Chasing sigma_fit to its minimum overshoots BELOW the noise floor --
    # an over-fit that injects the noisy high-tau Mellin spectrum into P(r):
    # sigma_fit barely improves (a noise-level change) while the P(r) roughness
    # explodes, so the recovered density is badly spiky on noisy/short traces.
    # Instead pick the SMALLEST cutoff whose sigma_fit already reaches the noise
    # floor to within its statistical uncertainty -- the smoothest adequate fit.
    # The floor is estimated robustly and tau-independently from the V residual's
    # successive differences (std/sqrt2); the tolerance ~2/sqrt(2N) is the ~2-sigma
    # spread of that estimate. This self-adapts: clean data needs a large cutoff to
    # reach the (tiny) floor and keeps sharp features; noisy data reaches the floor
    # early and stays smooth.
    auto_taumax = tau_max is None
    if auto_taumax:
        cands = [6.0, 8.0, 10.0, 12.0, 15.0, 18.0, 22.0, 26.0, 32.0, 40.0]
        if taumax_method == 'lcurve':
            # L-curve corner: trade the V-space residual sigma_fit against the
            # P(r) roughness ||L2 P||. As tau_max grows sigma_fit falls (slowly,
            # toward the noise floor) while roughness rises (fast, as the noisy
            # high-tau spectrum enters P(r)); the corner of (log sigma_fit, log
            # roughness) is the balance point. Picked by maximum Menger curvature,
            # same detector as the Tikhonov L-curve.
            Lr = regularization_matrix(len(r), 2)
            sig = np.empty(len(cands)); rough = np.empty(len(cands))
            for j, tm in enumerate(cands):
                fr, _ = _build(tm, _ntau_for(tm))[2](F)
                m, dens = _masses(fr)
                vfit = B*((1 - lam) + lam*(K@m))
                sig[j] = float(np.std((Vn - vfit)[pos])) if pos.any() else np.inf
                rough[j] = float(np.linalg.norm(Lr@dens))
            x = np.log(np.maximum(sig, 1e-12)); y = np.log(np.maximum(rough, 1e-12))
            curv = np.array([_menger(x[k-1], y[k-1], x[k], y[k], x[k+1], y[k+1])
                             for k in range(1, len(cands)-1)])
            idx = int(np.argmax(curv)) + 1 if len(curv) else 0
        elif taumax_method == 'discrepancy':
            # discrepancy principle anchored to the noise floor. The
            # floor and the per-cutoff residual are measured in the same space,
            # set by `noise_space`: 'V' (default) uses the whole background-
            # normalized curve Vn (floor ~ raw sigma, stationary); 'F' uses the
            # background-corrected form factor F (floor ~ sigma/(lam*B), noise-
            # amplified and weighted toward the decayed tail). Floor = std of the
            # signal's successive differences / sqrt2 (robust, tau-independent).
            base = F if noise_space == 'F' else Vn
            sig = np.array([_sigma_fit_at(_build(tm, _ntau_for(tm))[2],
                                          space=noise_space) for tm in cands])
            npos = int(np.count_nonzero(pos))
            if npos > 2:
                sig_floor = float(np.std(np.diff(base[pos])))/np.sqrt(2.0)
                margin = float(np.clip(2.0/np.sqrt(2.0*npos), 0.05, 0.20))
            else:
                sig_floor, margin = float(sig.min()), 0.0
            thr = max(sig_floor*(1.0 + margin), float(sig.min()))
            ok = np.where(sig <= thr)[0]
            idx = int(ok[0]) if len(ok) else int(np.argmin(sig))
        else:
            # 'penalty' (default): minimize the forward-fit RMS regularized by a
            # SYMMETRIC-NOISE penalty. rmsF (RMS of the form-factor residual
            # F - F_fit over t > 0) falls as the cutoff captures the parabolic
            # echo top, then sits on a broad noise-floor plateau -- so chasing its
            # minimum (or the discrepancy floor) is ambiguous: it under-shoots
            # (the floor is reached before P(r) has sharpened) or over-extends
            # (the plateau injects the noisy high-tau spectrum into P(r)). That
            # injected noise enters the area-normalized SIGNED density as paired
            # +bump / -dip excursions, so the |negative area| `neg` is a direct,
            # model-free measure of it (symmetric because every spurious positive
            # spike is balanced by a negative one under area normalization). Pick
            # the cutoff minimizing rmsF/min(rmsF) + neg: the ratio term (>= 1,
            # large while the echo top is under-resolved) forces an adequate fit;
            # the neg term halts the extension the moment the fit plateaus and the
            # cutoff would only be adding symmetric noise. Self-adapts to noise --
            # clean data plateaus late (sharp P(r) kept), noisy data accrues neg
            # early (stays smooth). Beats the discrepancy floor + leakage
            # extension on the synthetic benchmark in both the no-background
            # (mean overlap 0.922 -> 0.933) and with-background (0.828 -> 0.831)
            # regimes, landing within ~0.002-0.003 of the overlap-optimal oracle.
            rmsF = np.empty(len(cands)); neg = np.empty(len(cands))
            for j, tm in enumerate(cands):
                fr_j, _ = _build(tm, _ntau_for(tm))[2](F)
                Ff_j = _fwd(fr_j)                       # forward fit (signed by default)
                rmsF[j] = (float(np.sqrt(np.mean((F - Ff_j)[pos]**2)))
                           if pos.any() else np.inf)
                _, dens_j = _masses(fr_j)               # signed density
                neg[j] = float(_trapz(np.abs(np.minimum(dens_j, 0.0)), r))
            rmin = float(np.min(rmsF)) or 1.0
            idx = int(np.argmin(rmsF/rmin + neg))
        tau_max = cands[idx]

        # Resolution-aware extension (discrepancy only). The discrepancy stops as
        # soon as the V-space residual reaches the noise floor, but P(r) can keep
        # SHARPENING past that point -- visible as the spurious short-r leakage
        # (the Mellin noise signature, piled at the bottom of the r grid) still
        # DROPPING as the cutoff rises. Push tau_max UP while that leakage keeps
        # decreasing and stop at the first increase. This self-adapts to noise:
        # on clean/low-noise data the leakage falls (better resolution) so the
        # cutoff extends and the echo top / bimodal peaks sharpen; on noisy data
        # the leakage rises immediately (high-tau noise enters) so it stays at the
        # discrepancy pick. No effect when tau_max is given explicitly.
        if taumax_extend and taumax_method == 'discrepancy':
            short = r <= (r[0] + float(extend_short_frac)*(r[-1] - r[0]))

            def _short_leak(tm):
                fr_e, _ = _build(tm, _ntau_for(tm))[2](F)
                _, dens_e = _masses(fr_e)
                a = np.maximum(dens_e, 0.0)
                s = float(_trapz(a, r)) or 1.0
                return float(_trapz(a[short], r[short])/s)

            best_leak = _short_leak(tau_max)
            for nt in (tau_max + 3.0, tau_max + 6.0, tau_max + 10.0,
                       tau_max + 15.0, tau_max + 21.0):
                if nt > 40.0:
                    break
                lk = _short_leak(nt)
                if lk < best_leak - 1e-4:
                    best_leak, tau_max = lk, nt
                else:
                    break
        n_tau = _ntau_for(tau_max)

    tau, Phi, _invert_F = _build(float(tau_max), int(n_tau))
    f_r, Vimg = _invert_F(F)

    # Short-r taper on the DISPLAYED density (`taper_short`, default on). The
    # propagated noise piles into a spurious spike at the bottom of the r grid (the
    # r^-2.5 Jacobian) -- the visible "double peak near t=0" -- right where, for
    # DEER, the distance is too short to be reliable anyway. Multiply the signed
    # density by the same raised-cosine `_fit_w` (0 at the grid edge -> 1 by
    # `fit_rmin_frac` of the range) so P(r) goes *smoothly* to zero there instead of
    # carrying that spike. This is purely geometric (distance-based, NOT amplitude-
    # or noise-based), so it leaves the mid/long-r density bit-identical to the
    # honest Mellin result -- no shape carving, no hard zeros -- and only the
    # unreliable short-r edge is down-weighted (a genuine short-r peak is attenuated,
    # not deleted). The area re-normalization then returns the small amount of area
    # the spurious spike had stolen back to the real peaks. The tapered density also
    # feeds F_fit, so the forward-fit echo top widens back to the data (no more thin
    # parabola). Set taper_short=False for the raw signed density + the separate
    # `signed_fit`/`_phys_fit` forward model.
    f_disp = f_r*_fit_w if taper_short else f_r
    masses, P_density = _masses(f_disp)                  # signed density (displayed)
    if taper_short:
        F_fit = K@masses                                # consistent with the displayed P(r)
    else:
        F_fit = _fwd(f_r)                               # signed by default; clipped+low-r taper
                                                        # when signed_fit=False (keeps F_fit
                                                        # monotone vs a short-r negative spike)

    # discrepancy diagnostics (V space): sigma_fit over t>0 vs the noise floor
    # from the decayed tail (where the dipolar signal is gone). sigma_fit ~
    # sigma_noise => well matched; >> => underfit; << => overfit.
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
    return {'t': t, 'r': r, 'form_factor': F, 'F_fit': F_fit,
            'residuals': F - F_fit, 'P': masses, 'P_norm': masses,
            'P_density': P_density, 'P_lower': P_lower, 'P_upper': P_upper,
            'P_std': P_std, 'P_signed_density': P_density, 'kernel': K,
            'alpha': float('nan'), 'noise_level': float(sig_e),
            'l_curve': None, 'background': bg, 'lambda': bg['lambda'],
            'k': bg['k'], 'dim': bg['dim'], 'engine': 'mellin',
            'delta': float(delta), 'tau_max': float(tau_max),
            'auto_taumax': bool(auto_taumax), 'sigma_fit': sigma_fit,
            'sigma_noise': sigma_noise, 'n_mc': int(n_mc),
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


def deer_invert_gauss(t, V, r=None, bg_start=None, bg_end=None, dim=3.0,
                      fit_dim=False, nu_dd=NU_DD, n_gauss=None, max_gauss=4,
                      bg_engine='joint', ic='aicc', n_mc=0, ci_z=1.96, seed=0,
                      sigma_min=None, sigma_max=None, ci_mode='linear',
                      ci_level=0.95, prune_spurious=True, weight_min=0.02,
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
    treats as i.i.d. noise) by adding spurious Gaussians -- always recognizable as
    pinned at the width-resolution floor (sigma ~ 1.5*dr) or carrying < `weight_min`
    of the area. With pruning on, the chosen N is the criterion-best fit that
    contains NO such component; this keeps simple bimodals from being reported as
    3-4 Gaussians without an under-fitting global penalty. `n_gauss_ic` (the
    unpruned criterion pick) and `pruned` are returned for transparency.

    Model (after background correction, F(0)=1):
        P(r) = sum_k a_k * exp(-(r - r_k)^2 / (2 sigma_k^2)),  a_k, sigma_k > 0.
    The amplitudes are fit UN-normalized: the data anchor the overall scale through
    F(0) = sum(masses) = 1, which removes the scale degeneracy a pre-normalized
    model would have and keeps the fit covariance well-conditioned. The reported
    P_norm / P_density are the area-normalized result; `components` carries each
    Gaussian's centre / sigma / weight with 1-sigma errors from the covariance.

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
    """
    _require_scipy()
    from scipy.optimize import least_squares
    t = np.asarray(t, float)
    V = np.asarray(V, float)
    r = default_r_axis() if r is None else np.asarray(r, float)
    if bg_start is None:
        bg_start = t[0] + 0.5*(t[-1] - t[0])
    if bg_engine == 'none':
        bg = _no_background(t, V, bg_start=bg_start, bg_end=bg_end)
    elif bg_engine == 'joint':
        bg = joint_background(t, V, bg_start=bg_start, bg_end=bg_end,
                              dim=dim, fit_dim=fit_dim, nu_dd=nu_dd)
    elif bg_engine == 'general':
        bg = background_general(t, V, bg_start, bg_end=bg_end)
    else:
        bg = background_fit(t, V, bg_start, bg_end=bg_end, dim=dim, fit_dim=fit_dim)
    F = bg['form_factor']
    Vn, B, lam = bg['V_norm'], bg['B'], bg['lambda']
    sig_e = _tail_noise(t, Vn)
    K = dipolar_kernel(t, r, nu_dd=nu_dd)
    dr = float(r[1] - r[0]) if len(r) > 1 else 1.0
    rmin, rmax = float(r[0]), float(r[-1])
    # width bounds: a Gaussian narrower than the grid step cannot be resolved; the
    # widest meaningful one spans the half-range. Defaults are overridable.
    s_lo = float(sigma_min) if sigma_min else max(1.5*dr, 0.02)
    s_hi = float(sigma_max) if sigma_max else max(0.5*(rmax - rmin), 4*s_lo)
    s0 = float(np.clip(0.2, s_lo, s_hi))
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

    def _fit_n(n):
        centers = _gauss_seed_centers(r, P_seed, n)
        a0 = 1.0/(n*s0*np.sqrt(2.0*np.pi))                # so sum(masses) ~ 1 at seed
        p0, lo, hi = [], [], []
        for c in centers:
            p0 += [a0, float(np.clip(c, rmin, rmax)), s0]
            lo += [0.0, rmin, s_lo]
            hi += [np.inf, rmax, s_hi]
        lo, hi = np.array(lo), np.array(hi)
        sol = least_squares(lambda p: K@(_density(p, n)*dr) - F, p0,
                            bounds=(lo, hi), max_nfev=4000)
        rss = float(np.sum(sol.fun**2))
        return sol, rss, (lo, hi)

    def _criterion(rss, n):
        kpar = 3*n + 1                                    # +1 for the noise variance
        aic = npts*np.log(rss/npts) + 2*kpar if rss > 0 else -np.inf
        denom = npts - kpar - 1
        aicc = aic + (2*kpar*(kpar + 1)/denom if denom > 0 else np.inf)
        bic = npts*np.log(rss/npts) + kpar*np.log(npts) if rss > 0 else -np.inf
        return {'aic': aic, 'aicc': aicc, 'bic': bic}

    def _has_spurious(pp, n):
        """Flag a fit whose components include a SPURIOUS one: a Gaussian pinned
        at the width-resolution floor (sigma ~ s_lo) or carrying negligible weight.
        At low noise the information criterion over-fits the small SYSTEMATIC
        residual left by background/lambda/echo-top preparation (not random noise,
        which the criterion assumes) with exactly such floor-width / tiny spikes;
        rejecting any N whose best fit contains one keeps the count parsimonious
        without an under-fitting global penalty."""
        sig = np.abs(pp[2::3][:n])
        amp = pp[0::3][:n]
        area = amp*sig*np.sqrt(2.0*np.pi)
        tot = float(np.sum(area)) or 1.0
        w = area/tot
        return bool(np.any(sig <= s_lo*1.1) or np.any(w < weight_min))

    Ns = [int(n_gauss)] if (n_gauss and int(n_gauss) > 0) else \
        list(range(1, int(max_gauss) + 1))
    forced = bool(n_gauss and int(n_gauss) > 0)
    ic_key = ic if ic in ('aic', 'aicc', 'bic') else 'aicc'
    best = best_clean = None
    ic_curve = []
    for n in Ns:
        try:
            sol, rss, bounds = _fit_n(n)
        except Exception:
            continue
        crit = _criterion(rss, n)
        ic_curve.append((n, float(crit[ic_key]), rss))
        cand = {'n': n, 'sol': sol, 'rss': rss, 'crit': crit, 'bounds': bounds}
        if best is None or crit[ic_key] < best['crit'][ic_key]:
            best = cand
        if not _has_spurious(sol.x, n) and (
                best_clean is None or crit[ic_key] < best_clean['crit'][ic_key]):
            best_clean = cand
    if best is None:
        raise RuntimeError('Gaussian fit failed for every component count tried.')

    # Prefer the criterion-best model with NO spurious (floor-width / negligible-
    # weight) component; fall back to the plain criterion pick if every fit has one
    # (or N was forced -- then honour the request).
    n_ic = best['n']
    chosen = best if (forced or not prune_spurious or best_clean is None) else best_clean
    n = chosen['n']
    sol = chosen['sol']
    best = chosen                                          # downstream reads best['*']
    p = sol.x
    lo_b, hi_b = chosen['bounds']
    # covariance from the Jacobian: cov = (J^T J)^-1 * residual variance. pinv
    # guards the (near-)singular directions overlapping components produce.
    nparams = 3*n
    dof = max(npts - nparams, 1)
    resvar = best['rss']/dof
    try:
        cov = np.linalg.pinv(sol.jac.T@sol.jac)*resvar
        perr = np.sqrt(np.clip(np.diag(cov), 0.0, None))
    except Exception:
        cov, perr = None, np.full(nparams, np.nan)

    g = _density(p, n)
    masses = g*dr
    F_fit = K@masses                                      # fitted curve (~F(0)=1)
    P_norm = _normalize_masses(masses)
    P_density = P_norm/dr

    components = []
    for kk in range(n):
        a, c, s = float(p[3*kk]), float(p[3*kk + 1]), float(abs(p[3*kk + 2]))
        components.append({'amplitude': a, 'center': c, 'sigma': s,
                           'area': a*s*np.sqrt(2.0*np.pi),
                           'center_err': float(perr[3*kk + 1]),
                           'sigma_err': float(perr[3*kk + 2])})
    tot_area = sum(cc['area'] for cc in components) or 1.0
    for cc in components:
        cc['weight'] = cc['area']/tot_area
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
                return K@(_density(pp, n)*dr) - F
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

        # map sorted components back to their parameter block (sorted by centre)
        order = sorted(range(n), key=lambda kk: float(p[3*kk + 1]))
        for cc, kk in zip(components, order):
            cc['center_ci_lo'] = _bound(3*kk + 1, -1)
            cc['center_ci_hi'] = _bound(3*kk + 1, +1)
            cc['sigma_ci_lo'] = _bound(3*kk + 2, -1)
            cc['sigma_ci_hi'] = _bound(3*kk + 2, +1)

    P_lower = P_upper = P_std = None
    if n_mc and int(n_mc) > 0 and cov is not None and np.all(np.isfinite(cov)):
        rng = np.random.default_rng(seed)
        try:
            samples = rng.multivariate_normal(p, cov, size=int(n_mc))
            ens = np.empty((int(n_mc), len(r)))
            for j in range(int(n_mc)):
                pj = samples[j].copy()
                pj[0::3] = np.clip(pj[0::3], 0.0, None)    # amplitudes >= 0
                pj[2::3] = np.clip(np.abs(pj[2::3]), s_lo, s_hi)
                ens[j] = _normalize_masses(_density(pj, n)*dr)/dr
            P_std = ens.std(axis=0)
            P_lower = P_density - ci_z*P_std
            P_upper = P_density + ci_z*P_std
        except Exception:
            P_lower = P_upper = P_std = None

    return {'t': t, 'r': r, 'form_factor': F, 'F_fit': F_fit,
            'residuals': F - F_fit, 'P': masses, 'P_norm': P_norm,
            'P_density': P_density, 'P_lower': P_lower, 'P_upper': P_upper,
            'P_std': P_std, 'kernel': K, 'alpha': float('nan'), 'l_curve': None,
            'background': bg, 'lambda': bg['lambda'], 'k': bg['k'],
            'dim': bg['dim'], 'engine': 'gauss', 'n_gauss': int(n),
            'components': components, 'ic': ic_key,
            'aic': float(best['crit']['aic']), 'aicc': float(best['crit']['aicc']),
            'bic': float(best['crit']['bic']), 'ic_curve': ic_curve,
            'n_gauss_ic': int(n_ic), 'pruned': bool(n != n_ic),
            'ci_mode': ci_mode, 'ci_level': float(ci_level),
            'noise_level': float(sig_e)}


def deer_mellin_consensus(t, V, r=None, bg_start=None, bg_end=None, dim=3.0,
                          fit_dim=False, nu_dd=NU_DD, n_t0=9, n_mc=6,
                          chi_tol=1.05,
                          taumax_window=(0.8, 0.86, 0.91, 0.97, 1.03, 1.09,
                                         1.14, 1.19, 1.25),
                          n_bg=5, bg_span_frac=0.05,
                          gate_rel_noise=0.06, seed=0, percentiles=(2.5, 97.5),
                          **kwargs):
    """Robust ("consensus") Mellin inversion for NOISY traces: marginalize over the
    data-consistent zero-time and tau_max (and noise) instead of committing to one
    fragile point estimate.

    SUPERSEDED (kept for explicit/diagnostic use; no longer in the GUI). The
    noise-adaptive delta + short-r taper in `deer_invert_mellin` (both default-on)
    make the single pick more accurate than this marginalization on the benchmark
    (no-bg mean overlap 0.884 vs 0.861 -- the ensemble median over t0/tau-shifted
    curves over-broadens), so prefer the plain single pick; use this only to inspect
    the t0 x tau_max ambiguity explicitly.

    Why: at high relative noise (sigma/lambda gtrsim 0.06) a DEER trace does not
    determine the zero-time t0 OR the Mellin cutoff tau_max -- the V-space forward
    residual is white (structureless) across a wide range of both, so they are
    *unidentifiable* and a single auto-pick swings wildly per noise realization
    (the recovered P(r) overlap can move 0.5->0.85 with t0 changes the residual
    cannot even see). The honest answer there is not a sharper point estimate but a
    CONSENSUS over everything the data cannot rule out, plus a band that shows the
    real uncertainty -- the same logic as `deer_validate` for Tikhonov.

    How: fit a reference t0 (`fit_zero_time`) and run the standard single-pick
    `deer_invert_mellin` (auto tau_max) as `base`. Estimate the relative noise
    sigma_e/lambda.
      * IDENTIFIABLE (rel noise < `gate_rel_noise`): the single pick is reliable,
        so just return it (with an `n_mc` Monte-Carlo band) -- consensus would only
        add needless spread and broaden genuinely sharp distributions. consensus=False.
      * UNIDENTIFIABLE (rel noise >= gate): build an ensemble that marginalizes
        every uncertain knob, ADDITIVELY (not a full multiplied grid -- that mostly
        triples the cost and makes the per-distance median jaggeder): the
        data-consistent `n_t0` zero-times (forward-fit chi within `chi_tol` of the
        best) x a `taumax_window` of cutoffs *around* the auto-pick (a fraction
        tuple tracking the data -- high/sharp on cleaner traces, low on noisy ones),
        PLUS an `n_bg`-point background-start sweep (+-`bg_span_frac` of the trace,
        subsuming the `deer_validate` axis) and `n_mc` measurement-noise
        realizations at the centre. The reported P(r) is the ensemble MEDIAN and the
        band is the `percentiles` spread. consensus=True.

    Returns the same dict shape as `deer_invert_mellin` (P_density = consensus
    median or single pick; P_lower/P_upper = band), so the GUI/exporters are shared,
    plus: consensus (bool), rel_noise, n_trials, t0 (reference), t0_consistent (the
    accepted grid), tau_maxs, ensemble (n_trials x len(r)), base (the central
    single-pick result, for the time-domain forward-fit display). `**kwargs` pass
    through to `deer_invert_mellin` (delta, taumax_method, wiener, ...)."""
    _require_scipy()
    t = np.asarray(t, float)
    V = np.asarray(V, float)
    r = default_r_axis() if r is None else np.asarray(r, float)
    dr = float(r[1] - r[0]) if len(r) > 1 else 1.0

    # reference zero-time and single-pick inversion (auto tau_max)
    t0_ref = float(fit_zero_time(t, V, bg_start=bg_start, bg_end=bg_end, dim=dim,
                                 r=r, nu_dd=nu_dd))

    def _invert(t0, tau_max, bgs=bg_start, Vx=None, n_mc_=0):
        return deer_invert_mellin(
            t - t0, (V if Vx is None else Vx), r=r,
            bg_start=(None if bgs is None else bgs - t0),
            bg_end=(None if bg_end is None else bg_end - t0), dim=dim,
            fit_dim=fit_dim, nu_dd=nu_dd, tau_max=tau_max, n_mc=n_mc_, seed=seed,
            **kwargs)

    base = _invert(t0_ref, None)
    sig_e = float(base['noise_level'])
    lam = float(base['lambda']) or 1e-3
    rel_noise = sig_e/max(lam, 1e-3)
    pick = float(base['tau_max'])

    # Identifiable regime: trust the single pick; add an MC band for honesty.
    if rel_noise < gate_rel_noise:
        res = _invert(t0_ref, None, n_mc_=n_mc) if n_mc else base
        res = dict(res)
        res.update({'engine': 'mellin_consensus', 'consensus': False,
                    'rel_noise': rel_noise, 'n_trials': 1, 't0': t0_ref,
                    't0_consistent': np.array([t0_ref]),
                    'tau_maxs': np.array([pick]), 'ensemble': None, 'base': base})
        return res

    # Unidentifiable regime: marginalize. t0 grid biased slightly early (the
    # parabola zero-time is biased LATE at high noise), chi-filtered to the
    # data-consistent set; tau_max window tracks the auto-pick.
    span = float(t[-1] - t[0]) or 1.0
    t0_grid = np.linspace(t0_ref - 0.030*span, t0_ref + 0.012*span, int(max(3, n_t0)))
    t0_grid = t0_grid[t0_grid >= t[0] - 1e-9]
    if len(t0_grid) == 0:                              # t0 at/before the trace start
        t0_grid = np.array([max(float(t0_ref), float(t[0]))])   # (e.g. known t0=0)
    tmg = [round(pick*f, 2) for f in taumax_window]

    def _chi(res):
        bg = res['background']; lm = res['lambda']
        Vn = bg['V_norm']; Vfit = bg['B']*((1 - lm) + lm*res['F_fit'])
        pos = res['t'] > 0
        rr = (Vn - Vfit)[pos]
        return float(np.sqrt(np.mean(rr**2))/(res['noise_level'] or 1e-9))

    chis = np.array([_chi(_invert(t0, pick)) for t0 in t0_grid])
    cmin = float(np.min(chis))
    ok = t0_grid[chis <= cmin*chi_tol]
    if len(ok) == 0:
        ok = np.array([t0_ref])

    # background-start sweep (subsumes deer_validate's axis): the bg window is
    # itself uncertain on noisy traces, so marginalize it too. The structural
    # ensemble is the full bg x t0 x tau_max grid; measurement noise is added as a
    # smaller set of perturbed realizations at the central bg / median-consistent
    # t0 (so the band reflects both the model ambiguity and the electrical noise
    # without the cost of noise-perturbing every grid point).
    if bg_start is not None and n_bg and int(n_bg) > 1:
        bg_grid = _bg_start_grid(t, bg_start, span_frac=bg_span_frac, n=int(n_bg))
    else:
        bg_grid = np.array([bg_start])

    rng = np.random.default_rng(seed)
    ens = []
    t0c = float(ok[len(ok)//2])                         # median-consistent t0

    def _add(res):
        a = np.maximum(res['P_density'], 0.0)
        s = float(_trapz(a, r))
        ens.append(a/s if s > 0 else a)

    # The ensemble is ADDITIVE across the uncertainty axes (not a full multiplied
    # grid): t0 x tau_max core, plus a background-start sweep and a noise set at the
    # centre. The bg-start contribution is small on these traces -- the joint
    # background is well determined -- so a full bg x t0 x tau grid mostly triples
    # the cost (and the per-distance median over many t0/tau-shifted curves only
    # gets jaggeder), while the additive sweep still injects the bg-window spread.
    for t0 in ok:                                       # data-consistent t0 x tau
        for tm in tmg:
            _add(_invert(t0, tm))
    if bg_start is not None and n_bg and int(n_bg) > 1:  # background-start sweep
        for bgs in bg_grid:
            _add(_invert(t0c, float(pick), bgs=bgs))
    if n_mc and int(n_mc) > 0 and sig_e > 0:            # measurement-noise set
        for tm in tmg:
            for _ in range(int(n_mc)):
                Vk = V + sig_e*rng.standard_normal(V.shape)
                _add(_invert(t0c, tm, Vx=Vk))
    ens = np.vstack(ens)
    P_density = np.median(ens, axis=0)
    lo, hi = percentiles
    P_lower = np.percentile(ens, lo, axis=0)
    P_upper = np.percentile(ens, hi, axis=0)
    P_mass = _normalize_masses(P_density*dr)
    out = dict(base)
    out.update({'r': r, 'P_density': P_density, 'P_norm': P_mass, 'P': P_mass,
                'P_lower': P_lower, 'P_upper': P_upper, 'P_signed_density': P_density,
                'engine': 'mellin_consensus', 'consensus': True,
                'rel_noise': rel_noise, 'n_trials': int(ens.shape[0]),
                't0': t0_ref, 't0_consistent': ok, 'tau_maxs': np.array(tmg),
                'bg_starts': np.atleast_1d(bg_grid), 'ensemble': ens, 'base': base,
                'peak': float(r[int(np.argmax(P_density))]),
                'r_mean': float(np.sum(r*P_mass))})
    return out


# --------------------------------------------------------------------------- #
#  Zero-time (reference-time) fitting
# --------------------------------------------------------------------------- #
def _parabolic_zero_time(t, V, drop=0.15, smooth_w=5, search_frac=0.30):
    """Zero-time t0 from a quadratic fit to the echo maximum (the classic
    DeerAnalysis approach). V(t) near the echo is even and parabolic in (t - t0)
    -- V ~ Vpk - c(t - t0)^2 -- so the vertex of a least-squares parabola is t0.

    Robust against noise: the initial peak is the argmax of a lightly smoothed V
    *restricted to the first `search_frac` of the trace* (so a stray noise spike
    elsewhere can't be mistaken for the echo), and the fit window WIDENS
    symmetrically out to where the smoothed signal has fallen `drop` of its
    peak-to-min amplitude -- wide enough to average down noise, narrow enough to
    stay within the parabolic top (a too-wide window is biased by the dipolar
    oscillation / decay and by the truncated pre-zero side). ~3x more accurate
    than the residual search at high noise on traces with a clear echo maximum.
    Returns t0, or None if no concave peak is found (caller falls back)."""
    t = np.asarray(t, float); V = np.asarray(V, float)
    n = len(t)
    if n < 7:
        return None
    w = int(max(1, smooth_w))
    Vs = np.convolve(V, np.ones(w)/w, mode='same') if w > 1 else V
    ns = max(5, int(search_frac*n))
    i0 = int(np.argmax(Vs[:ns]))
    vpk = float(Vs[i0]); vmin = float(np.min(Vs)); amp = max(vpk - vmin, 1e-12)
    thr = vpk - drop*amp
    lo = i0
    while lo > 0 and Vs[lo] >= thr:
        lo -= 1
    hi = i0
    while hi < n - 1 and Vs[hi] >= thr:
        hi += 1
    lo = max(min(lo, i0 - 3), 0)
    hi = min(max(hi, i0 + 3), n - 1)
    if hi - lo < 4:
        return None
    tt = t[lo:hi + 1]; vv = V[lo:hi + 1]
    a, b, _c = np.polyfit(tt - tt.mean(), vv, 2)
    if a >= 0:                                          # not concave -> no echo max
        return None
    return float(tt.mean() - b/(2.0*a))


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

    CAVEAT -- this lowers the MEAN |t0| error (5.1 -> 4.0 ns on the benchmark) but
    does NOT improve end-to-end accuracy, and is left off by default for two
    measured reasons: (1) at extreme noise (sigma 0.04) the residual fallback is
    itself high-variance and can overshoot tens of ns EARLY, raising the WORST-case
    t0 error (29.6 -> 45.9 ns); (2) the Mellin forward model has a small residual
    bias that a slightly-late t0 happens to compensate, so making t0 more accurate
    can REDUCE the distance overlap (benchmark mean 0.853 -> 0.838). It helps
    moderate-noise traces (sigma ~0.02) but hurts the cleanest and noisiest -- a
    net wash-to-regression. Enable only when an accurate t0 per se is the goal.

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
                  noise=0.0, n_noise=0, seed=0, percentiles=(5, 95), **kwargs):
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
    probes background/noise sensitivity, not the regularization choice. With
    `noise` > 0 and `n_noise` > 0, each background-start trial is additionally
    repeated with `n_noise` Gaussian-noise realizations of std `noise` added to V
    (estimate `noise` from the trace residual). All trials share the grid `r`.

    Returns a dict: r, P_density (the ensemble *median* -- the robust consensus
    curve, always bracketed by the band), P_mean (ensemble mean, exposed for
    reference), P_lower, P_upper (the `percentiles` band), ensemble
    (n_trials x len(r) densities), n_trials, bg_starts, alpha (the fixed value),
    peak (consensus-curve peak r), r_mean (its first moment), and base = the
    single inversion at the central bg_start (its form factor / fit / residuals
    for display).
    """
    _require_scipy()
    t = np.asarray(t, float)
    V = np.asarray(V, float)
    r = default_r_axis() if r is None else np.asarray(r, float)
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
    base = deer_invert(t, V, r=r, bg_start=bs_mid, bg_end=bg_end, dim=dim,
                       fit_dim=fit_dim, alpha=alpha, alphas=None,
                       reg_order=reg_order, nu_dd=nu_dd, method=method,
                       engine=engine, alpha_factor=af_mid, **kwargs)
    alpha_fixed = float(base['alpha'])

    def _invert(Vx, bs):
        return deer_invert(t, Vx, r=r, bg_start=bs, bg_end=bg_end, dim=dim,
                           fit_dim=fit_dim, alpha=alpha_fixed, scan_lcurve=False,
                           reg_order=reg_order, nu_dd=nu_dd, method=method,
                           engine=engine, **kwargs)

    ensemble = []
    for bs in bg_starts:
        trials = [V] + [V + noise*rng.standard_normal(V.shape)
                        for _ in range(reps)]
        for Vx in trials:
            try:
                ensemble.append(_invert(Vx, bs)['P_density'])
            except Exception:
                continue
    if not ensemble:
        raise RuntimeError('DEER validation produced no successful trials.')
    ens = np.vstack(ensemble)
    P_mean = ens.mean(axis=0)
    P_median = np.median(ens, axis=0)
    lo, hi = percentiles
    P_lower = np.percentile(ens, lo, axis=0)
    P_upper = np.percentile(ens, hi, axis=0)
    P_mass = _normalize_masses(P_median*dr)
    return {'r': r, 'P_density': P_median, 'P_mean': P_mean,
            'P_lower': P_lower, 'P_upper': P_upper, 'ensemble': ens,
            'n_trials': ens.shape[0], 'bg_starts': bg_starts,
            'alpha': alpha_fixed,
            'peak': float(r[int(np.argmax(P_median))]),
            'r_mean': float(np.sum(r*P_mass)), 'base': base,
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

    # consensus engine: clean trace gates to the single pick; a noisy copy engages
    # the marginalized median + band. Just exercise both branches and the peak.
    con_c = deer_mellin_consensus(t, V, r=r, bg_start=1.0)
    Vn2 = simulate(t, r, P_true, lam=0.35, k=0.10, dim=3.0, noise=0.08, seed=3)
    con_n = deer_mellin_consensus(t, Vn2, r=r, bg_start=1.0, n_t0=7, n_mc=4)
    consensus_ok = ((con_c['consensus'] is False) and (con_n['consensus'] is True)
                    and con_n['ensemble'] is not None
                    and abs(r[int(np.argmax(con_n['P_density']))] - r0) < 0.6)
    print(f'consensus: clean gated={not con_c["consensus"]}, '
          f'noisy n_trials {con_n["n_trials"]} peak '
          f'{r[int(np.argmax(con_n["P_density"]))]:.3f} nm, ok {consensus_ok}')

    print('SELF-TEST:', 'PASS' if (ok and smoother and band_ok and mellin_ok and
          consensus_ok and abs(val['peak'] - r0) < 0.3) else 'FAIL')
