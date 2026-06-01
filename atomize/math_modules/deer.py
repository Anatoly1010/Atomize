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


def l_curve(K, F, alphas, L=None):
    """L-curve scan: solution vs residual norm over `alphas`, corner picked by
    maximum Menger curvature in log-log space.

    Returns dict: alphas, rho (residual norms), eta (solution norms), curvature,
    alpha_opt, index, P (the solution at the corner).
    """
    _require_scipy()
    K = np.asarray(K, float)
    F = np.asarray(F, float)
    if L is None:
        L = regularization_matrix(K.shape[1], 2)
    alphas = np.asarray(alphas, float)
    rho = np.empty(len(alphas))
    eta = np.empty(len(alphas))
    Ps = []
    for i, al in enumerate(alphas):
        P = tikhonov_nnls(K, F, al, L)
        Ps.append(P)
        rho[i] = np.linalg.norm(K@P - F)
        eta[i] = np.linalg.norm(L@P)
    x = np.log(rho + 1e-300)
    y = np.log(eta + 1e-300)
    kappa = np.zeros(len(alphas))
    for i in range(1, len(alphas) - 1):
        kappa[i] = _menger(x[i - 1], y[i - 1], x[i], y[i], x[i + 1], y[i + 1])
    idx = int(np.argmax(kappa)) if len(alphas) > 2 else len(alphas)//2
    return {'alphas': alphas, 'rho': rho, 'eta': eta, 'curvature': kappa,
            'alpha_opt': float(alphas[idx]), 'index': idx, 'P': Ps[idx]}


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
                scan_lcurve=True):
    """Full DEER pipeline: background-correct V(t), build the kernel, invert to
    P(r) by Tikhonov + NNLS (alpha at the L-curve corner if not supplied).

    `t` in us, `r` in nm. With `scan_lcurve` (default) the L-curve is always
    computed for display, even when an explicit `alpha` is given. Returns a dict:
    t, r, form_factor F(t), F_fit = K P, residuals, P (raw masses), P_norm
    (masses, sum = 1), P_density (P_norm / dr, integrates to 1), kernel, alpha,
    l_curve (when scanned), background result, and lambda / k / dim.
    """
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
        alphas = np.logspace(-4, 1, 25)
    lc = l_curve(K, F, alphas, L) if (scan_lcurve or alpha is None) else None
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
            'k': bg['k'], 'dim': bg['dim']}


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
