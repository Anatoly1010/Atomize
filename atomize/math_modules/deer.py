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
this module solves it with Tikhonov regularization + non-negativity (NNLS), the
regularization weight chosen at the L-curve corner. A model-free analytic
Mellin-transform inversion (Matveeva/Maryasov, doi 10.1039/C7CP04059H) is
planned as a second engine.

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


def deer_invert(t, V, r=None, bg_start=None, bg_end=None, dim=3.0, fit_dim=False,
                alpha=None, alphas=None, reg_order=2, nu_dd=NU_DD,
                scan_lcurve=True, method='gcv', engine='sequential'):
    """Full DEER pipeline: background-correct V(t), build the kernel, invert to
    P(r) by Tikhonov + NNLS. When `alpha` is not supplied it is chosen
    automatically by `method` ('gcv' default, or 'curvature' for the classic
    L-corner) -- see `l_curve`.

    `engine` selects how the background is handled:
      'sequential' -- fit the background on the tail window, divide it out, then
                       invert the form factor (this function; fast, the default).
      'joint'      -- fit background + modulation depth together with P(r) in one
                       separable-NLLS pass (`deer_invert_joint`; DeerLab-style,
                       more robust on short/shallow backgrounds).

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
                                 method=method, scan_lcurve=scan_lcurve)
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
        alpha = lc['alpha_opt']
        P = lc['P']
    else:
        P = tikhonov_nnls(K, F, alpha, L)
    F_fit = K@P
    P_norm = _normalize_masses(P)
    dr = float(r[1] - r[0]) if len(r) > 1 else 1.0
    P_density = P_norm/dr
    return {'t': t, 'r': r, 'form_factor': F, 'F_fit': F_fit,
            'residuals': F - F_fit, 'P': P, 'P_norm': P_norm,
            'P_density': P_density, 'kernel': K, 'alpha': float(alpha),
            'l_curve': lc, 'background': bg, 'lambda': bg['lambda'],
            'k': bg['k'], 'dim': bg['dim'], 'engine': 'sequential'}


def deer_invert_joint(t, V, r=None, bg_start=None, bg_end=None, dim=3.0,
                      fit_dim=False, alpha=None, alphas=None, reg_order=2,
                      nu_dd=NU_DD, method='gcv', scan_lcurve=True):
    """DEER inversion with a *joint* (separable-NLLS / variable-projection) fit of
    the background and modulation depth together with the regularized non-negative
    P(r) -- the strategy DeerLab uses. More robust than the sequential
    'fit background, then invert' pipeline (`deer_invert`) on real traces with
    short or shallow backgrounds, where the tail fit and the inversion are coupled.

    Model:  V(t) = B(t) * [ (1 - lam) + lam * (K P)(t) ],  B(t) = exp(-(k|t|)^(d/3)).
    Substituting P~ = lam * P and K'(t, r) = K(t, r) - 1 (note K(0, r) = 1) makes
    the linear part free of lam:

        V/B - 1 = K' P~ ,     lam = sum(P~) recovered afterwards, P = P~/lam .

    So only the background (k, and d when `fit_dim`) is nonlinear. For each trial
    background the optimal P~ >= 0 is the regularized NNLS solution of the
    V-space-weighted system diag(B) K' P~ = V - B (down-weighting the noisy long-t
    tail), and the V-space residual is minimized over (k[, d]) with
    scipy.optimize.least_squares. K' is constant, so alpha (GCV by default) is
    stable across the search; it is re-selected once at the converged background.

    `bg_start`/`bg_end` only seed the initial background guess here (the joint fit
    uses the whole trace). Same return dict as `deer_invert`, with engine='joint'.
    """
    _require_scipy()
    from scipy.optimize import least_squares
    t = np.asarray(t, float)
    V = np.asarray(V, float)
    r = default_r_axis() if r is None else np.asarray(r, float)
    V = V/V[int(np.argmin(np.abs(t)))]            # normalize V(0) = 1
    K = dipolar_kernel(t, r, nu_dd=nu_dd)
    Kp = K - 1.0                                  # K'(t, r); K'(0, r) = 0
    L = regularization_matrix(len(r), reg_order)
    if alphas is None:
        alphas = np.logspace(-4, 3, 36)

    # seed (k, d) from the cheap sequential tail fit
    if bg_start is None:
        bg_start = t[0] + 0.5*(t[-1] - t[0])
    bg0 = background_fit(t, V, bg_start, bg_end=bg_end, dim=dim, fit_dim=fit_dim)
    k0, d0 = bg0['k'], bg0['dim']

    def solve_lin(k, d, al):
        B = np.exp(-(k*np.abs(t))**(d/3.0))
        A = B[:, None]*Kp                         # diag(B) K'
        return B, A, (V - B)

    # pick alpha by GCV on the initial background (K' fixed => alpha is stable)
    B0, A0, y0 = solve_lin(k0, d0, None)
    lc = (l_curve(A0, y0, alphas, L, method=method)
          if (scan_lcurve or alpha is None) else None)
    alpha_use = float(alpha) if alpha is not None else lc['alpha_opt']

    def resid(theta):
        k = abs(theta[0]); d = theta[1] if fit_dim else d0
        B, A, y = solve_lin(k, d, alpha_use)
        return A@tikhonov_nnls(A, y, alpha_use, L) - y

    theta0 = [k0, d0] if fit_dim else [k0]
    lb = [0.0, 1.0] if fit_dim else [0.0]
    ub = [np.inf, 6.0] if fit_dim else [np.inf]
    try:
        sol = least_squares(resid, theta0, bounds=(lb, ub), max_nfev=2000)
        k = abs(sol.x[0]); d = sol.x[1] if fit_dim else d0
    except Exception:
        k, d = k0, d0                             # fall back to the seed background

    # final solution at the converged background, alpha re-selected there
    B = np.exp(-(k*np.abs(t))**(d/3.0))
    A = B[:, None]*Kp
    y = V - B
    if alpha is None and scan_lcurve:
        lc = l_curve(A, y, alphas, L, method=method)
        alpha_use = lc['alpha_opt']
    Ptil = tikhonov_nnls(A, y, alpha_use, L)
    lam = float(np.sum(Ptil))
    if abs(lam) < 1e-9:
        lam = 1e-9
    P = Ptil/lam                                  # masses, sum = 1
    P_norm = _normalize_masses(P)
    dr = float(r[1] - r[0]) if len(r) > 1 else 1.0
    F = (V/B - (1 - lam))/lam                      # background-corrected form factor
    F_fit = K@P_norm
    bg = {'lambda': lam, 'k': float(k), 'dim': float(d), 'A': float(1 - lam),
          'B': B, 'form_factor': F, 'V_norm': V, 't': t,
          'bg_start': float(bg_start),
          'bg_end': (None if bg_end is None else float(bg_end)),
          'mask': (t >= bg_start)}
    return {'t': t, 'r': r, 'form_factor': F, 'F_fit': F_fit,
            'residuals': F - F_fit, 'P': Ptil, 'P_norm': P_norm,
            'P_density': P_norm/dr, 'kernel': K, 'alpha': float(alpha_use),
            'l_curve': lc, 'background': bg, 'lambda': lam,
            'k': float(k), 'dim': float(d), 'engine': 'joint'}


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
    print('SELF-TEST:', 'PASS' if ok else 'FAIL')
