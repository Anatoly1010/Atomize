# Least-squares Fitting

A small registry of analytic models fitted with `scipy.optimize.curve_fit`. Each model is selected by a string key, carries its own parameter names, and ships with a heuristic initial-guess builder so the multi-parameter models (including the ESEEM decays) converge without hand-tuned start values.

To use the module, import it and create a fitter:

```python
import numpy as np
import atomize.math_modules.least_square_fitting_modules as math_modules

fitter = math_modules.math()
```

!!! note
    Fitting requires `scipy` (the `math` extra: `pip install -e .[math]`). `fit()` raises a `RuntimeError` if `scipy` is not installed.

---

## math() { #class data-toc-label="math()" }

```python
fitter = math_modules.math()
```

Creates the fitter object. All functions below are methods on it.

---

## Available models { #models data-toc-label="Models" }

[`model_names()`](#model_names) returns the keys below. Every model has a constant baseline term (`b` or `c`) that can be fixed at zero with the `no_offset` argument of [`fit()`](#fit).

**Basic models**

| Model key | Parameters | Function |
| --------- | ---------- | -------- |
| `Linear` | `a, b` | $a x + b$ |
| `Exponential` | `a, k, b` | $a\,e^{-x/k} + b$ |
| `Bi-exponential` | `a1, k1, a2, k2, b` | $a_1 e^{-x/k_1} + a_2 e^{-x/k_2} + b$ |
| `Stretched exponential` | `a, k, beta, b` | $a\,e^{-(x/k)^{\beta}} + b$ |
| <code>Stretched exponential <br>+ exponential</code> | <code>a1, k1, beta,<br>a2, k2, b</code> | $a_1 e^{-(x/k_1)^{\beta}} + a_2 e^{-x/k_2} + b$ |
| `Gaussian` | `a, x0, sigma, b` | $a\,e^{-(x-x_0)^2/2\sigma^2} + b$ |
| `Lorentzian` | `a, x0, gamma, b` | $a/(1+((x-x_0)/\gamma)^2) + b$ |
| `Damped sine` | `a, k, f, phi, b` | $a\,e^{-x/k}\sin(2\pi f x + \varphi) + b$ |

The four `Tm + ESEEM …` models have longer parameter lists and are described in the [next section](#eseem).

### ESEEM echo-decay models { #eseem data-toc-label="ESEEM models" }

For Hahn-echo $T_2/T_m$ decays carrying nuclear ESEEM modulation, the models multiply a decay envelope by one or two damped-cosine modulation terms on a constant offset:

$$
V(t) = A\,e^{-(t/T_m)^{\beta}}\Big[1 + \sum_k m_k \cos(2\pi f_k t + \varphi_k)\,e^{-t/\tau_{m,k}}\Big] + c
$$

The mono-exponential variants drop $\beta$, and the 1-frequency variants keep only the $k=1$ modulation term. The four model keys and their parameters:

- **`Tm + ESEEM (stretched, 1 freq)`**<br/>`a, Tm, beta, c, m, f, phi, tau_m`
- **`Tm + ESEEM (stretched, 2 freq)`**<br/>`a, Tm, beta, c, m1, f1, phi1, tau_m1, m2, f2, phi2, tau_m2`
- **`Tm + ESEEM (mono-exp, 1 freq)`**<br/>`a, Tm, c, m, f, phi, tau_m`
- **`Tm + ESEEM (mono-exp, 2 freq)`**<br/>`a, Tm, c, m1, f1, phi1, tau_m1, m2, f2, phi2, tau_m2`

Here `a` scales the envelope, `Tm` is the decay time, `beta` the stretch exponent, `c` the offset, and each modulation contributes a depth `m`, frequency `f`, phase `phi`, and damping time `tau_m`. The modulation frequencies are seeded automatically from the FFT peaks of the detrended data, which is what lets the 8–12 parameter fits converge. Frequency units follow the x-axis: with `x` in ns, `f` comes out in 1/ns (GHz); with `x` in µs, in 1/µs (MHz).

---

## fit() { #fit data-toc-label="fit" }

```python
result = fitter.fit(model, x, y, guess=None, no_offset=False, fixed=None)
```

Fits `(x, y)` with the named `model`.

- **`model`** — one of the keys from [`model_names()`](#model_names).
- **`guess`** — optional initial parameter list. If `None` or the wrong length, [`default_guess()`](#default_guess) is used.
- **`no_offset`** — when `True`, the constant baseline term (`b` or `c`) is fixed at `0` and removed from the free parameters, forcing the curve through the baseline instead of floating it.
- **`fixed`** — optional `{parameter name: value}` dict of parameters held constant and removed from the free parameters, e.g. `{'beta': 0.9}`. Names the model does not have are ignored.

Returns a dict:

| Key | Description |
| --- | ----------- |
| `y_fit` | Model evaluated at `x` with the best-fit parameters |
| `residuals` | `y - y_fit` |
| `popt` | Best-fit parameters |
| `perr` | 1-σ parameter errors (sqrt of the covariance diagonal) |
| `r_squared` | Coefficient of determination |
| `param_names` | Names matching the `popt` order (without `b`/`c` when `no_offset=True` and without any `fixed` parameter) |
| `stats` | Goodness-of-fit / model-selection diagnostics (see [below](#goodness)) |

```python
import numpy as np
import atomize.math_modules.least_square_fitting_modules as math_modules

fitter = math_modules.math()
x = np.linspace(0, 10, 200)
y = 5*np.exp(-x/3.0) + 0.2 + 0.05*np.random.randn(x.size)

res = fitter.fit('Exponential', x, y)
for name, val, err in zip(res['param_names'], res['popt'], res['perr']):
    print(f'{name} = {val:.4g} +/- {err:.2g}')
print('R^2 =', res['r_squared'])
print('adj R^2 =', res['stats']['adj_r_squared'])
print('AICc =', res['stats']['aicc'], ' Durbin-Watson =', res['stats']['durbin_watson'])
```

### Goodness of fit { #goodness data-toc-label="Goodness of fit" }

The `stats` entry holds diagnostics beyond `r_squared`, for judging whether a model is adequate and for comparing models on the same data. No per-point measurement errors are available, so the noise variance is estimated from the residuals themselves ($\sigma^2 = \mathrm{SS_{res}}/\nu$, with $\nu = n - p$ degrees of freedom).

| Key | Meaning |
| --- | ------- |
| `n_points`, `n_params`, `dof` | Number of points $n$, free parameters $p$, and degrees of freedom $\nu = n - p$ |
| `rmse` | Root-mean-square residual $\sqrt{\mathrm{SS_{res}}/n}$, in signal units |
| `red_chi2` | Reduced chi-square $\mathrm{SS_{res}}/\nu$ (≈ 1 by construction, since $\sigma$ is taken from the residuals) |
| `adj_r_squared` | $R^2$ penalized for parameter count: $1-(1-R^2)\frac{n-1}{\nu}$. Only rises when an added term genuinely helps |
| `aic`, `aicc`, `bic` | Information criteria (Gaussian-likelihood form). **Lower is better.** Absolute values are meaningless; the *difference* between two fits of the same data is what counts. `aicc` is the small-sample-corrected AIC; `bic` penalizes extra parameters more strongly |
| `durbin_watson` | Residual-autocorrelation statistic. **≈ 2** ⇒ random (white) residuals; well below 2 (positive correlation) or well above 2 ⇒ residuals drift systematically — the model is the wrong *shape* even if $R^2$ looks excellent |

!!! tip "Choosing a model"
    `durbin_watson` catches an inadequate model that $R^2$ alone misses: a fit can reach $R^2 = 0.999$ yet leave residuals that snake across zero. To pick between models (e.g. `Stretched exponential` vs `Stretched exponential + exponential`), compare `aicc`/`bic` — a drop greater than ≈ 10 is decisive evidence for the lower model — and check that `durbin_watson` moves toward 2.

    Entries that need $\nu > 0$ (`red_chi2`, `adj_r_squared`, `aicc`) are `NaN` for datasets too small to support the model's parameter count.

---

## model_names() { #model_names data-toc-label="model_names" }

```python
keys = fitter.model_names()
```

Returns the list of model keys (the first column of the [models table](#models)).

---

## param_names() { #param_names data-toc-label="param_names" }

```python
names = fitter.param_names(model)
```

Returns the parameter-name list of `model` (in `popt` order).

---

## default_guess() { #default_guess data-toc-label="default_guess" }

```python
guess = fitter.default_guess(model, x, y)
```

Builds a heuristic initial-guess list for `model` from the data — the largest peak for Gaussian/Lorentzian, FFT-seeded frequencies for the ESEEM models, and for the decay/recovery models (`Exponential`, `Bi-exponential`, `Stretched exponential`, `Stretched exponential + exponential`) a **characteristic decay time** measured directly from the data. Pass it (optionally edited) to [`fit()`](#fit) as `guess`.

The characteristic time is the x-distance from `x[0]` to where the signal first covers half of its total (`y[0]` → `y[-1]`) change, and the plateau/amplitude come from endpoint medians (noise-robust). Unlike a fixed fraction of the x-span, this stays correct on **log-spaced, multi-decade axes** — e.g. a saturation/inversion-recovery $T_1$ curve sampled from 10⁻⁷ to 10⁻² s — where a span-based seed would land orders of magnitude too slow and push `curve_fit` into a degenerate local minimum (a collapsed term, or `beta` going negative).

---

## one_exp_fit() { #one_exp_fit data-toc-label="one_exp_fit" }

```python
model_data, residuals, r_squared = fitter.one_exp_fit(curve, guess_array)
```

Legacy single-exponential fit kept for existing scripts. `curve` is a `[x, y]` array and `guess_array` is `[a, k, b]` for $a\,e^{-x/k}+b$. Returns the `[x, y_fit]` model, the `[x, residuals]` array, and `r_squared`. New code should prefer [`fit('Exponential', ...)`](#fit).
