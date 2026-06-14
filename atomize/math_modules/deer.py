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
    V = V/V[int(np.argmin(np.abs(t)))]                 # normalize at t = 0
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
    _require_scipy()
    t = np.asarray(t, float)
    V = np.asarray(V, float)
    r = default_r_axis() if r is None else np.asarray(r, float)
    if bg_start is None:
        bg_start = t[0] + 0.5*(t[-1] - t[0])
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
            'k': bg['k'], 'dim': bg['dim'], 'engine': 'sequential'}


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

    The background decay rate (k, and d when `fit_dim`) is the only nonlinear
    unknown. For each trial rate the modulation depth lam is *pinned* to the mean
    baseline of V/B over the background window [bg_start, bg_end] (where the
    intramolecular form factor has decayed and V ~ (1-lam) B), and the non-negative
    regularized P(r) follows from K P = (V/B - (1-lam))/lam. The rate is chosen to
    minimize the whole-trace residual ||V - B[(1-lam)+lam KP]||.

    Pinning lam to the baseline is essential: with lam free the fit is degenerate
    (a near-flat background plus extra long-r P(r) mass reproduces V equally well)
    and collapses to k -> 0; the baseline constraint removes that direction and
    recovers the correct, deeper background -- matching DeerLab's joint fit.
    `bg_start`/`bg_end` therefore set the baseline window. Same return dict as
    `deer_invert`, with engine='joint'.
    """
    _require_scipy()
    from scipy.optimize import least_squares, minimize_scalar
    t = np.asarray(t, float)
    V = np.asarray(V, float)
    r = default_r_axis() if r is None else np.asarray(r, float)
    V = V/V[int(np.argmin(np.abs(t)))]            # normalize V(0) = 1
    K = dipolar_kernel(t, r, nu_dd=nu_dd)
    L = regularization_matrix(len(r), reg_order)
    if alphas is None:
        alphas = np.logspace(-4, 3, 24)

    if bg_start is None:
        bg_start = t[0] + 0.6*(t[-1] - t[0])      # bias into the decayed tail
    hi = bg_end if (bg_end is not None and bg_end > bg_start) else float(t.max())
    mask = (t >= bg_start) & (t <= hi)
    if int(mask.sum()) < 3:
        mask = t >= bg_start

    bg0 = background_fit(t, V, bg_start, bg_end=bg_end, dim=dim, fit_dim=fit_dim)
    k0, d0 = bg0['k'], bg0['dim']

    def lam_of(B):
        return min(max(1.0 - float(np.mean((V/B)[mask])), 0.02), 0.95)

    def solve_P(k, d, al):
        B = np.exp(-(k*np.abs(t))**(d/3.0))
        lam = lam_of(B)
        F = (V/B - (1 - lam))/lam
        return B, lam, F, tikhonov_nnls(K, F, al, L)

    # select alpha once on the seed background; F is normalized (F(0)=1) so the
    # regularization weight is stable across the rate search
    B0 = np.exp(-(k0*np.abs(t))**(d0/3.0))
    lam0 = lam_of(B0)
    F0 = (V/B0 - (1 - lam0))/lam0
    lc = (l_curve(K, F0, alphas, L, method=method)
          if (scan_lcurve or alpha is None) else None)
    alpha_use = float(alpha) if alpha is not None else lc['alpha_opt']*float(alpha_factor)

    def vss(k, d):                                # whole-trace V-space residual SS
        B, lam, F, P = solve_P(k, d, alpha_use)
        return float(np.sum((V - B*((1 - lam) + lam*(K@P)))**2))

    kref = max(float(k0), 1e-4)
    if fit_dim:
        def resid(theta):
            k = abs(theta[0]); d = min(max(theta[1], 1.0), 6.0)
            B, lam, F, P = solve_P(k, d, alpha_use)
            return V - B*((1 - lam) + lam*(K@P))
        try:
            sol = least_squares(resid, [kref, d0],
                                bounds=([0.0, 1.0], [np.inf, 6.0]), max_nfev=200)
            k = abs(sol.x[0]); d = min(max(sol.x[1], 1.0), 6.0)
        except Exception:
            k, d = kref, d0
    else:
        d = d0
        try:
            sol = minimize_scalar(lambda lk: vss(np.exp(lk), d),
                                  bounds=(np.log(kref/100.0), np.log(kref*100.0)),
                                  method='bounded', options={'xatol': 3e-2})
            k = float(np.exp(sol.x))
        except Exception:
            k = kref

    # final solution at the fitted background (alpha from the seed selection is
    # reused: F is normalized to F(0)=1, so the weight transfers across the rate
    # search — re-scanning here only adds a costly GCV pass for no gain)
    B = np.exp(-(k*np.abs(t))**(d/3.0))
    lam = lam_of(B)
    F = (V/B - (1 - lam))/lam
    P_masses = tikhonov_nnls(K, F, alpha_use, L)
    P_norm = _normalize_masses(P_masses)
    dr = float(r[1] - r[0]) if len(r) > 1 else 1.0
    F_fit = K@P_norm
    P_lower, P_upper = tikhonov_ci(K, F, alpha_use, P_masses, L=L, dr=dr)
    bg = {'lambda': lam, 'k': float(k), 'dim': float(d), 'A': float(1 - lam),
          'B': B, 'form_factor': F, 'V_norm': V, 't': t,
          'bg_start': float(bg_start),
          'bg_end': (None if bg_end is None else float(bg_end)),
          'mask': mask}
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


def mellin_signal_spectrum(t, F, tau, delta, F0=1.0, du=0.02):
    """Mellin image V~(1/2 + i*tau) of the form factor F(T), via the delta-split
    of doi 10.1039/C7CP04059H. `t` in the kernel unit (us), only T > 0 used; F is
    normalized to F(0) = `F0` (~1). `delta` is the split point (same unit as t);
    the [delta, Tmax] part is integrated on a log-T grid of step `du` (chosen to
    resolve the constant post-substitution frequency tau, so du < ~pi/max|tau|).
    Vectorized over `tau`."""
    t = np.asarray(t, dtype=float)
    F = np.asarray(F, dtype=float)
    tau = np.asarray(tau, dtype=float)
    pos = t > 0
    Tp, Fp = t[pos], F[pos]
    order = np.argsort(Tp)
    Tp, Fp = Tp[order], Fp[order]
    s = 0.5 + 1j*tau
    # analytic [0, delta]: F ~ F0 constant
    analytic = F0*delta**s/s                            # delta^{1/2+i tau}/(1/2+i tau)
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
                     nu_dd=NU_DD, n_r=60, rate_alpha=1.0):
    """Joint (DeerLab-style) intermolecular background returning ONLY the
    background (same dict shape as `background_fit`). Fits the decay rate k (and d
    when `fit_dim`) together with a non-negative P(r), with the modulation depth
    lambda pinned to the tail baseline of V/B -- the same degeneracy-breaking
    strategy as `deer_invert_joint`, but stripped of the final full-resolution
    inversion / L-curve. The rate is fit on a coarse internal distance grid
    (`n_r`) at a fixed regularization (`rate_alpha`): k and lambda are insensitive
    to the P(r) resolution, so this is ~30x faster than a full joint inversion.
    Used by `deer_invert_mellin` (bg_engine='joint') and Mellin validation, where
    the background must be re-fit per background-start.

    Hardened against the short-bg_end collapse: the lambda pin uses the full
    available tail [bg_start, t_max] rather than [bg_start, bg_end], so k is
    essentially independent of bg_end and cannot slide to a spurious near-flat
    background when bg_end is pulled in (see the inline note). bg_end here only
    seeds kref via the sequential `background_fit`.
    """
    _require_scipy()
    from scipy.optimize import least_squares, minimize_scalar
    t = np.asarray(t, float)
    V = np.asarray(V, float)
    V = V/V[int(np.argmin(np.abs(t)))]                 # normalize V(0) = 1
    # Cap the coarse grid at the distance the trace length supports
    # (r_max ~ 5*(Tmax/2)^(1/3) nm). Distances beyond r_max give a dipolar decay
    # so slow it is indistinguishable from -- and trades against -- the
    # intermolecular background; including them lets the rate fit collapse to a
    # near-flat background (k -> 0) on short traces (the shallow-k branch of the
    # background/long-r degeneracy). Excluding them keeps k determined.
    Tmax = float(np.max(np.abs(t))) or 1.0
    rmax_cap = float(np.clip(5.0*(Tmax/2.0)**(1.0/3.0), 3.0, 8.0))
    rc = np.linspace(1.5, rmax_cap, int(n_r))          # coarse grid for the rate fit
    Kc = dipolar_kernel(t, rc, nu_dd=nu_dd)
    Lc = regularization_matrix(len(rc), 2)
    if bg_start is None:
        bg_start = t[0] + 0.6*(t[-1] - t[0])
    # Pin lambda over the FULL available tail [bg_start, t_max], NOT [bg_start,
    # bg_end]. lambda is the asymptotic modulation level and is best estimated
    # from the longest decayed tail. A short bg_end gives a biased pin and lets
    # the rate fit slide down the shallow-k branch of the background/long-r
    # degeneracy (k -> ~0): the background then leaves a slow residual in the form
    # factor that Tikhonov hides as long-r mass but the Mellin kernel (phi -> 0)
    # cannot represent, collapsing the Mellin fit. Using the full tail makes k
    # essentially independent of bg_end. The rate-fit residual (vss below) is
    # already whole-trace, so the two are now consistent. (bg_end still bounds the
    # sequential engine's window; here it only seeds kref via background_fit.)
    mask = t >= bg_start
    if int(mask.sum()) < 3:                            # bg_start too late: latter half
        mask = t >= (t[0] + 0.5*(t[-1] - t[0]))
    bg0 = background_fit(t, V, bg_start, bg_end=bg_end, dim=dim, fit_dim=fit_dim)
    k0, d0 = bg0['k'], bg0['dim']

    def lam_of(B):
        return min(max(1.0 - float(np.mean((V/B)[mask])), 0.02), 0.95)

    def vss(k, d):
        B = np.exp(-(k*np.abs(t))**(d/3.0))
        lam = lam_of(B)
        F = (V/B - (1 - lam))/lam
        P = tikhonov_nnls(Kc, F, rate_alpha, Lc)
        return float(np.sum((V - B*((1 - lam) + lam*(Kc@P)))**2))

    kref = max(float(k0), 1e-4)
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
            k = abs(sol.x[0]); d = min(max(sol.x[1], 1.0), 6.0)
        except Exception:
            k, d = kref, d0
    else:
        d = d0
        try:
            sol = minimize_scalar(lambda lk: vss(np.exp(lk), d),
                                  bounds=(np.log(kref/100.0), np.log(kref*100.0)),
                                  method='bounded', options={'xatol': 3e-2})
            k = float(np.exp(sol.x))
        except Exception:
            k = kref
    B = np.exp(-(k*np.abs(t))**(d/3.0))
    lam = lam_of(B)
    F = (V/B - (1 - lam))/lam
    return {'lambda': lam, 'k': float(k), 'dim': float(d), 'A': float(1 - lam),
            'B': B, 'form_factor': F, 'V_norm': V, 't': t,
            'bg_start': float(bg_start),
            'bg_end': (None if bg_end is None else float(bg_end)), 'mask': mask}


def mellin_delta(t, F, level=0.95):
    """Practical split point delta: the first T > 0 where the form factor has
    fallen to `level` of F(0) (the paper's F(delta) ~ 0.95 estimate). Falls back
    to the first positive sample if F never drops that far."""
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
    if len(below):
        return float(Tp[below[0]])
    return float(Tp[0])


def deer_invert_mellin(t, V, r=None, bg_start=None, bg_end=None, dim=3.0,
                       fit_dim=False, nu_dd=NU_DD, delta=None, tau_max=30.0,
                       n_tau=601, bg_engine='joint', n_mc=0, ci_z=1.96, seed=0,
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
    `n_tau` points. `tau_max=None` selects the cutoff automatically by the
    discrepancy principle: the cutoff is the Mellin-space regularizer, and the
    V-space forward residual sigma_fit is U-shaped in it (too small under-fits,
    too large injects the noisy high-tau spectrum into P(r)); the routine picks
    the smallest cutoff whose sigma_fit is within 3% of the minimum (the noise
    floor). `sigma_fit` and the tail `sigma_noise` are returned so the fit can be
    judged (sigma_fit ~ sigma_noise good; >> underfit; << overfit).

    With `n_mc` > 0 a Monte-Carlo confidence band is returned: since the whole
    chain is linear and noise is additive, the form factor is re-inverted n_mc
    times with Gaussian noise (sigma from the fit residual) and the 95% percentile
    envelope of P(r) is the band (P_lower / P_upper). 50-100 realizations are
    typical.

    Returns the same dict shape as `deer_invert` (so the GUI and exporters are
    shared): t, r, form_factor, F_fit (forward kernel applied to the recovered
    density), residuals, P / P_norm / P_density (clipped >= 0, area-normalized),
    kernel, background, lambda / k / dim. Mellin-specific extras: engine='mellin',
    delta, tau_max, auto_taumax, sigma_fit, sigma_noise, P_signed_density (the raw
    signed f(r), whose short-r ripples are the propagated noise), tau, V_image,
    kernel_image, n_mc. There is no covariance band when n_mc=0, and no L-curve,
    so P_lower / P_upper / l_curve are None then.
    """
    _require_scipy()
    t = np.asarray(t, float)
    V = np.asarray(V, float)
    r = default_r_axis() if r is None else np.asarray(r, float)
    if bg_start is None:
        bg_start = t[0] + 0.5*(t[-1] - t[0])
    if bg_engine == 'joint':
        # robust lambda-pinned background (clean F -> 0); the lightweight helper
        # fits only the background (no full-res NNLS / L-curve) so it is fast
        # enough to also re-run per background-start during validation
        bg = joint_background(t, V, bg_start=bg_start, bg_end=bg_end,
                              dim=dim, fit_dim=fit_dim, nu_dd=nu_dd)
    else:
        bg = background_fit(t, V, bg_start, bg_end=bg_end, dim=dim, fit_dim=fit_dim)
    F = bg['form_factor']
    if delta is None or delta <= 0:
        delta = mellin_delta(t, F)
    D = 2.0*np.pi*nu_dd                                 # w = D / r^3 (rad/us)
    w = D/r**3
    dr = float(r[1] - r[0]) if len(r) > 1 else 1.0
    K = dipolar_kernel(t, r, nu_dd=nu_dd)
    Vn, B, lam = bg['V_norm'], bg['B'], bg['lambda']
    pos = t > 0

    def _build(tm, ntau):
        """Return a Mellin core inverter (F -> signed f(r)) for cutoff tm."""
        tau_g = np.linspace(-float(tm), float(tm), int(ntau))
        Phi_g = mellin_kernel_spectrum(tau_g)
        def inv(Fx):
            Vimg = mellin_signal_spectrum(t, Fx, tau_g, delta)
            return mellin_inverse(np.conj(Vimg/Phi_g), tau_g, w)*(3.0*D/r**4), Vimg
        return tau_g, Phi_g, inv

    def _ntau_for(tm):
        return int(max(401, round(2.0*tm/0.03)))        # fixed dtau ~ 0.03

    def _sigma_fit_at(inv):
        fr, _ = inv(F)
        m = _normalize_masses(np.maximum(fr, 0.0)*dr)
        vfit = B*((1 - lam) + lam*(K@m))
        return float(np.std((Vn - vfit)[pos])) if pos.any() else np.inf

    # Auto cutoff (tau_max=None): discrepancy principle. The cutoff regularizes
    # the inversion; the V-space forward residual sigma_fit is U-shaped in tau_max
    # -- a small cutoff under-fits (sigma_fit >> noise), a large one injects the
    # noisy high-tau Mellin spectrum into P(r) and sigma_fit climbs again. The
    # minimum sits at the noise floor (sigma_fit ~ sigma_noise on clean data), so
    # pick the smallest cutoff within 3% of that minimum.
    auto_taumax = tau_max is None
    if auto_taumax:
        cands = [6.0, 9.0, 12.0, 16.0, 20.0, 25.0, 32.0, 40.0]
        sig = np.array([_sigma_fit_at(_build(tm, _ntau_for(tm))[2]) for tm in cands])
        idx = int(np.argmax(sig <= sig.min()*1.03))     # first within 3% of min
        tau_max = cands[idx]
        n_tau = _ntau_for(tau_max)

    tau, Phi, _invert_F = _build(float(tau_max), int(n_tau))
    f_r, Vimg = _invert_F(F)
    masses = _normalize_masses(np.maximum(f_r, 0.0)*dr)
    P_density = masses/dr
    F_fit = K@masses                                    # forward check (F_fit(0)=1)
    area = float(_trapz(np.maximum(f_r, 0.0), r)) or 1.0

    # discrepancy diagnostics (V space): sigma_fit over t>0 vs the noise floor
    # from the decayed tail (where the dipolar signal is gone). sigma_fit ~
    # sigma_noise => well matched; >> => underfit; << => overfit.
    vfit = B*((1 - lam) + lam*F_fit)
    sigma_fit = float(np.std((Vn - vfit)[pos])) if pos.any() else float('nan')
    tail = pos & (t > (t[pos][0] + 0.7*(t[-1] - t[pos][0]))) if pos.any() else pos
    sigma_noise = (float(np.std((Vn - vfit)[tail]))
                   if np.count_nonzero(tail) > 2 else float('nan'))

    # Monte-Carlo confidence band: the whole Mellin chain is linear, so noise on
    # the form factor maps linearly to f(r). Re-invert F + Gaussian noise (sigma
    # from the fit residual) n_mc times -- the background is held fixed, so only
    # the fast core re-runs -- and take the 95% percentile envelope of P(r).
    P_lower = P_upper = None
    if n_mc and int(n_mc) > 0:
        sigmaF = float(np.std(F - F_fit)) or 0.0
        if sigmaF > 0:
            import math
            rng = np.random.default_rng(seed)
            ens = np.empty((int(n_mc), len(r)))
            for j in range(int(n_mc)):
                fk, _ = _invert_F(F + sigmaF*rng.standard_normal(F.shape))
                mk = _normalize_masses(np.maximum(fk, 0.0)*dr)
                ens[j] = mk/dr
            p = 0.5*(1.0 + math.erf(ci_z/math.sqrt(2.0)))   # z -> upper CDF (1.96->0.975)
            P_lower = np.percentile(ens, 100.0*(1.0 - p), axis=0)
            P_upper = np.percentile(ens, 100.0*p, axis=0)
    return {'t': t, 'r': r, 'form_factor': F, 'F_fit': F_fit,
            'residuals': F - F_fit, 'P': masses, 'P_norm': masses,
            'P_density': P_density, 'P_lower': P_lower, 'P_upper': P_upper,
            'P_signed_density': f_r/area, 'kernel': K, 'alpha': float('nan'),
            'l_curve': None, 'background': bg, 'lambda': bg['lambda'],
            'k': bg['k'], 'dim': bg['dim'], 'engine': 'mellin',
            'delta': float(delta), 'tau_max': float(tau_max),
            'auto_taumax': bool(auto_taumax), 'sigma_fit': sigma_fit,
            'sigma_noise': sigma_noise, 'n_mc': int(n_mc),
            'tau': tau, 'V_image': Vimg, 'kernel_image': Phi}


# --------------------------------------------------------------------------- #
#  Zero-time (reference-time) fitting
# --------------------------------------------------------------------------- #
def fit_zero_time(t, V, bg_start=None, bg_end=None, n_grid=16, search_frac=0.15,
                  refine=True, **kwargs):
    """Find the zero-time t0 (the dipolar reference time) that best aligns the
    kernel with the data, by minimizing the V-space reconstruction residual.

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
    t0 = float(grid[i])
    # parabolic refine through the grid minimum and its two neighbours
    if refine and 0 < i < len(grid) - 1 and np.all(np.isfinite(rs[i-1:i+2])):
        y0, y1, y2 = rs[i-1], rs[i], rs[i+1]
        denom = y0 - 2*y1 + y2
        if denom > 0:
            t0 = float(grid[i] + 0.5*(y0 - y2)/denom*(grid[1] - grid[0]))
    return t0


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

    print('SELF-TEST:', 'PASS' if (ok and smoother and band_ok and mellin_ok and
          abs(val['peak'] - r0) < 0.3) else 'FAIL')
