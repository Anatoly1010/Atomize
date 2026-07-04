#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import numpy as np

# scipy is an optional dependency (pip install -e .[math]) and the slowest
# import here (~0.6 s on Windows). Probe availability cheaply -- find_spec does
# NOT import scipy -- and defer the real import to the functions that fit, so
# that merely importing this module (e.g. for model_names()) stays numpy-only
# and GUIs that embed it start fast.
import importlib.util
SCIPY_AVAILABLE = importlib.util.find_spec('scipy') is not None


class math():

    def __init__(self):
        # Test run parameters
        if len(sys.argv) > 1:
            self.test_flag = sys.argv[1]
        else:
            self.test_flag = 'None'

    ###############################################################
    # Model functions. Each returns y(x) for a given parameter set.
    ###############################################################
    def linear(self, x, a, b):
        return a*x + b

    def exponential(self, x, a, k, b):
        return a*np.exp(-x/k) + b

    def biexponential(self, x, a1, k1, a2, k2, b):
        return a1*np.exp(-x/k1) + a2*np.exp(-x/k2) + b

    def stretched_exponential(self, x, a, k, beta, b):
        return a*np.exp(-(x/k)**beta) + b

    def stretched_plus_exponential(self, x, a1, k1, beta, a2, k2, b):
        # abs() guards curve_fit excursions into k1<0 (non-integer power of a
        # negative base -> NaN) without changing the physical (k1>0) solution
        return (a1*np.exp(-(np.abs(x)/np.abs(k1))**beta)
                + a2*np.exp(-x/k2) + b)

    def gaussian(self, x, a, x0, sigma, b):
        return a*np.exp(-(x - x0)**2/(2.0*sigma**2)) + b

    def lorentzian(self, x, a, x0, gamma, b):
        return a/(1.0 + ((x - x0)/gamma)**2) + b

    def damped_sine(self, x, a, k, f, phi, b):
        return a*np.exp(-x/k)*np.sin(2.0*np.pi*f*x + phi) + b

    # --- Hahn-echo T2/Tm decays with nuclear ESEEM modulation ----------------
    # Envelope (stretched or mono exponential) times one or two damped-cosine
    # modulation terms at the nuclear frequencies, on a constant offset.
    def _env_stretched(self, x, a, tm, beta):
        # abs() guards curve_fit excursions into tm<0 (non-integer power of a
        # negative base -> NaN) without changing the physical (tm>0) solution
        return a*np.exp(-(np.abs(x)/np.abs(tm))**beta)

    def eseem_stretched_1(self, x, a, tm, beta, c, m, f, phi, taum):
        mod = 1.0 + m*np.cos(2.0*np.pi*f*x + phi)*np.exp(-np.abs(x)/np.abs(taum))
        return self._env_stretched(x, a, tm, beta)*mod + c

    def eseem_stretched_2(self, x, a, tm, beta, c,
                          m1, f1, phi1, taum1, m2, f2, phi2, taum2):
        mod = (1.0
               + m1*np.cos(2.0*np.pi*f1*x + phi1)*np.exp(-np.abs(x)/np.abs(taum1))
               + m2*np.cos(2.0*np.pi*f2*x + phi2)*np.exp(-np.abs(x)/np.abs(taum2)))
        return self._env_stretched(x, a, tm, beta)*mod + c

    def eseem_exp_1(self, x, a, tm, c, m, f, phi, taum):
        mod = 1.0 + m*np.cos(2.0*np.pi*f*x + phi)*np.exp(-np.abs(x)/np.abs(taum))
        return a*np.exp(-np.abs(x)/np.abs(tm))*mod + c

    def eseem_exp_2(self, x, a, tm, c,
                    m1, f1, phi1, taum1, m2, f2, phi2, taum2):
        mod = (1.0
               + m1*np.cos(2.0*np.pi*f1*x + phi1)*np.exp(-np.abs(x)/np.abs(taum1))
               + m2*np.cos(2.0*np.pi*f2*x + phi2)*np.exp(-np.abs(x)/np.abs(taum2)))
        return a*np.exp(-np.abs(x)/np.abs(tm))*mod + c

    ###############################################################
    # Per-model metadata: parameter names + an initial-guess builder.
    # Keys are the strings exposed to the GUI model selector.
    ###############################################################
    def _models(self):
        return {
            'Linear':                (self.linear,               ['a', 'b'],                  self._guess_linear),
            'Exponential':           (self.exponential,          ['a', 'k', 'b'],             self._guess_exponential),
            'Bi-exponential':        (self.biexponential,        ['a1', 'k1', 'a2', 'k2', 'b'], self._guess_biexponential),
            'Stretched exponential': (self.stretched_exponential,['a', 'k', 'beta', 'b'],     self._guess_stretched),
            'Stretched exponential + exponential': (self.stretched_plus_exponential,
                ['a1', 'k1', 'beta', 'a2', 'k2', 'b'],           self._guess_stretched_plus_exp),
            'Gaussian':              (self.gaussian,             ['a', 'x0', 'sigma', 'b'],   self._guess_peak),
            'Lorentzian':            (self.lorentzian,           ['a', 'x0', 'gamma', 'b'],   self._guess_peak),
            'Damped sine':          (self.damped_sine,          ['a', 'k', 'f', 'phi', 'b'], self._guess_damped_sine),
            'Tm + ESEEM (stretched, 1 freq)': (self.eseem_stretched_1,
                ['a', 'Tm', 'beta', 'c', 'm', 'f', 'phi', 'tau_m'],
                self._guess_eseem_stretched_1),
            'Tm + ESEEM (stretched, 2 freq)': (self.eseem_stretched_2,
                ['a', 'Tm', 'beta', 'c', 'm1', 'f1', 'phi1', 'tau_m1',
                 'm2', 'f2', 'phi2', 'tau_m2'],
                self._guess_eseem_stretched_2),
            'Tm + ESEEM (mono-exp, 1 freq)': (self.eseem_exp_1,
                ['a', 'Tm', 'c', 'm', 'f', 'phi', 'tau_m'],
                self._guess_eseem_exp_1),
            'Tm + ESEEM (mono-exp, 2 freq)': (self.eseem_exp_2,
                ['a', 'Tm', 'c', 'm1', 'f1', 'phi1', 'tau_m1',
                 'm2', 'f2', 'phi2', 'tau_m2'],
                self._guess_eseem_exp_2),
        }

    def model_names(self):
        """List of model keys available to the GUI."""
        return list(self._models().keys())

    def param_names(self, model):
        return self._models()[model][1]

    # Human-readable formula for each model, as Qt rich text (HTML) so the GUI
    # can show the equation being fitted next to the parameter table. Kept here
    # (beside the model functions) so the two never drift.
    def _formulas(self):
        return {
            'Linear':                'y = a·x + b',
            'Exponential':           'y = a·exp(&minus;x/k) + b',
            'Bi-exponential':        'y = a<sub>1</sub>·exp(&minus;x/k<sub>1</sub>) '
                                     '+ a<sub>2</sub>·exp(&minus;x/k<sub>2</sub>) + b',
            'Stretched exponential': 'y = a·exp(&minus;(x/k)<sup>&beta;</sup>) + b',
            'Stretched exponential + exponential': 'y = a<sub>1</sub>·exp(&minus;(x/k<sub>1</sub>)<sup>&beta;</sup>) '
                                     '+ a<sub>2</sub>·exp(&minus;x/k<sub>2</sub>) + b',
            'Gaussian':              'y = a·exp(&minus;(x&minus;x<sub>0</sub>)<sup>2</sup>'
                                     ' / 2&sigma;<sup>2</sup>) + b',
            'Lorentzian':            'y = a / (1 + ((x&minus;x<sub>0</sub>)/&gamma;)<sup>2</sup>) + b',
            'Damped sine':           'y = a·exp(&minus;x/k)·sin(2&pi;f·x + &phi;) + b',
            'Tm + ESEEM (stretched, 1 freq)':
                'y = a·exp(&minus;(|x|/T<sub>m</sub>)<sup>&beta;</sup>)·'
                '[1 + m·cos(2&pi;f·x + &phi;)·exp(&minus;|x|/&tau;<sub>m</sub>)] + c',
            'Tm + ESEEM (stretched, 2 freq)':
                'y = a·exp(&minus;(|x|/T<sub>m</sub>)<sup>&beta;</sup>)·'
                '[1 + &Sigma;<sub>i=1,2</sub> m<sub>i</sub>·cos(2&pi;f<sub>i</sub>·x + &phi;<sub>i</sub>)'
                '·exp(&minus;|x|/&tau;<sub>m,i</sub>)] + c',
            'Tm + ESEEM (mono-exp, 1 freq)':
                'y = a·exp(&minus;|x|/T<sub>m</sub>)·'
                '[1 + m·cos(2&pi;f·x + &phi;)·exp(&minus;|x|/&tau;<sub>m</sub>)] + c',
            'Tm + ESEEM (mono-exp, 2 freq)':
                'y = a·exp(&minus;|x|/T<sub>m</sub>)·'
                '[1 + &Sigma;<sub>i=1,2</sub> m<sub>i</sub>·cos(2&pi;f<sub>i</sub>·x + &phi;<sub>i</sub>)'
                '·exp(&minus;|x|/&tau;<sub>m,i</sub>)] + c',
        }

    def model_formula(self, model):
        """Qt-rich-text equation for the named model ('' if unknown)."""
        return self._formulas().get(model, '')

    def default_guess(self, model, x, y):
        """Build a reasonable initial guess for the requested model."""
        return list(self._models()[model][2](x, y))

    ###############################################################
    # Initial-guess heuristics
    ###############################################################
    def _guess_linear(self, x, y):
        try:
            a, b = np.polyfit(x, y, 1)
        except Exception:
            a, b = 1.0, float(np.mean(y))
        return [a, b]

    # Baseline (plateau) + amplitude + characteristic decay time, estimated
    # directly from the data. The characteristic time is the x-distance from
    # x[0] to where the signal first covers half of its total (y[0] -> y[-1])
    # change. Unlike a fixed fraction of the x-span, this stays sensible on
    # LOG-spaced, multi-decade axes (e.g. saturation/inversion-recovery T1),
    # where span/3 would seed the time constant orders of magnitude too slow
    # and push curve_fit into a degenerate local minimum.
    def _decay_scale(self, x, y):
        n = len(x)
        m = max(3, n // 20)                      # endpoint window (~5% of pts)
        b = float(np.median(y[-m:]))             # plateau
        a = float(np.median(y[:m]) - b)          # amplitude (signed)
        span = float(x[-1] - x[0]) or 1.0
        dy = np.asarray(y, dtype=float) - float(y[0])
        tot = float(y[-1] - y[0])
        if tot == 0.0:
            return a, b, span/3.0
        frac = dy/tot
        idx = int(np.argmax(frac >= 0.5))        # first half-recovery crossing
        if idx <= 0:
            return a, b, span/3.0
        step = float(x[1] - x[0]) if n > 1 else 1.0
        tc = float(x[idx] - x[0])
        return a, b, max(tc, abs(step))

    def _guess_exponential(self, x, y):
        a, b, tc = self._decay_scale(x, y)
        return [a, tc, b]

    def _guess_biexponential(self, x, y):
        a, b, tc = self._decay_scale(x, y)
        return [a/2.0, tc*3.0, a/2.0, tc/3.0, b]

    def _guess_stretched(self, x, y):
        a, b, tc = self._decay_scale(x, y)
        return [a, tc, 0.8, b]

    def _guess_stretched_plus_exp(self, x, y):
        a, b, tc = self._decay_scale(x, y)
        #      a1,     k1(slow), beta, a2,     k2(fast), b
        return [a/2.0, tc*2.0,   0.7,  a/2.0, tc/3.0,    b]

    def _guess_peak(self, x, y):
        b = float(np.median(y))
        idx = int(np.argmax(np.abs(y - b)))
        a = float(y[idx] - b)
        x0 = float(x[idx])
        width = float(abs(x[-1] - x[0]))/10.0 or 1.0
        return [a, x0, width, b]

    def _guess_damped_sine(self, x, y):
        b = float(np.mean(y))
        a = float(np.max(y) - np.min(y))/2.0
        span = float(x[-1] - x[0]) or 1.0
        return [a, span/2.0, 1.0/span, 0.0, b]

    def _estimate_freqs(self, x, y, k=1):
        """Estimate the k dominant oscillation frequencies in (x, y).

        A low-order polynomial trend (≈ the decay envelope) is removed first,
        then the k largest rFFT peaks are picked. Used to seed the ESEEM
        modulation frequencies so the multi-parameter fits converge.
        """
        x = np.asarray(x, dtype=float)
        y = np.asarray(y, dtype=float)
        n = len(x)
        span = float(x[-1] - x[0]) or 1.0
        fallback = [1.0/span]*k
        if n < 8:
            return fallback
        dt = span/(n - 1)
        try:
            trend = np.poly1d(np.polyfit(x, y, 3))(x)
        except Exception:
            trend = float(np.mean(y))
        sp = np.abs(np.fft.rfft(y - trend))
        freqs = np.fft.rfftfreq(n, dt)
        sp[:2] = 0.0   # kill DC + residual trend bins
        picked = []
        df = freqs[1] if len(freqs) > 1 else 0.0
        for idx in np.argsort(sp)[::-1]:
            f = float(freqs[idx])
            if f <= 0 or sp[idx] <= 0:
                continue
            if all(abs(f - pf) > df for pf in picked):
                picked.append(f)
            if len(picked) >= k:
                break
        while len(picked) < k:
            picked.append(1.0/span)
        return picked

    def _guess_eseem_stretched_1(self, x, y):
        b = float(y[-1]); a = float(y[0] - b); span = float(x[-1] - x[0]) or 1.0
        f = self._estimate_freqs(x, y, 1)[0]
        #     a, Tm,      beta, c, m,   f, phi, tau_m
        return [a, span/3.0, 1.5, b, 0.2, f, 0.0, span/2.0]

    def _guess_eseem_stretched_2(self, x, y):
        b = float(y[-1]); a = float(y[0] - b); span = float(x[-1] - x[0]) or 1.0
        f1, f2 = self._estimate_freqs(x, y, 2)
        return [a, span/3.0, 1.5, b,
                0.2, f1, 0.0, span/2.0,
                0.1, f2, 0.0, span/2.0]

    def _guess_eseem_exp_1(self, x, y):
        b = float(y[-1]); a = float(y[0] - b); span = float(x[-1] - x[0]) or 1.0
        f = self._estimate_freqs(x, y, 1)[0]
        #     a, Tm,      c, m,   f, phi, tau_m
        return [a, span/3.0, b, 0.2, f, 0.0, span/2.0]

    def _guess_eseem_exp_2(self, x, y):
        b = float(y[-1]); a = float(y[0] - b); span = float(x[-1] - x[0]) or 1.0
        f1, f2 = self._estimate_freqs(x, y, 2)
        return [a, span/3.0, b,
                0.2, f1, 0.0, span/2.0,
                0.1, f2, 0.0, span/2.0]

    ###############################################################
    # Generic least-squares fit
    ###############################################################
    # parameter name treated as the constant baseline offset, per model
    _OFFSET_NAMES = ('b', 'c')

    def fit(self, model, x, y, guess=None, no_offset=False):
        """
        Fit (x, y) with the named model using scipy.optimize.curve_fit.

        no_offset: when True, the model's constant baseline term (the parameter
        named 'b' or 'c') is fixed at 0 and removed from the free parameters, so
        the curve is forced through the baseline instead of floating it.

        Returns a dict:
            y_fit       : model evaluated at x with the best-fit parameters
            residuals   : y - y_fit
            popt        : best-fit parameters
            perr        : 1-sigma parameter errors (sqrt of covariance diagonal)
            r_squared   : coefficient of determination
            param_names : names matching popt order
        Raises RuntimeError on a missing scipy or a failed fit.
        """
        if not SCIPY_AVAILABLE:
            raise RuntimeError("scipy is required for fitting. Install with: pip install -e .[math]")
        from scipy import optimize

        x = np.asarray(x, dtype=float)
        y = np.asarray(y, dtype=float)
        func, names, _ = self._models()[model]

        if guess is None or len(guess) != len(names):
            guess = self.default_guess(model, x, y)

        # Optionally fix the constant offset at 0: drop the 'b'/'c' parameter and
        # wrap the model so it is always called with that slot set to zero.
        offset_idx = None
        if no_offset:
            offset_idx = next((i for i, nm in enumerate(names)
                               if nm in self._OFFSET_NAMES), None)
        if offset_idx is None:
            fit_func, fit_names, fit_guess = func, names, guess
        else:
            oi = offset_idx

            def fit_func(xx, *p):
                full = list(p)
                full.insert(oi, 0.0)
                return func(xx, *full)

            fit_names = [nm for j, nm in enumerate(names) if j != oi]
            fit_guess = [g for j, g in enumerate(guess) if j != oi]

        popt, pcov = optimize.curve_fit(fit_func, x, y, p0=fit_guess, maxfev=100000)
        perr = np.sqrt(np.abs(np.diag(pcov)))
        names = fit_names

        y_fit = fit_func(x, *popt)
        residuals = y - y_fit
        ss_res = float(np.sum(residuals**2))
        ss_tot = float(np.sum((y - np.mean(y))**2)) or 1.0
        r_squared = 1.0 - ss_res/ss_tot

        stats = self._goodness_of_fit(y, residuals, ss_res, r_squared,
                                      n_params=len(popt))

        return {
            'y_fit': y_fit,
            'residuals': residuals,
            'popt': popt,
            'perr': perr,
            'r_squared': r_squared,
            'param_names': names,
            'stats': stats,
        }

    @staticmethod
    def _goodness_of_fit(y, residuals, ss_res, r_squared, n_params):
        """Goodness-of-fit / model-selection diagnostics from the residuals.

        No per-point measurement errors are available, so the noise variance is
        estimated from the residuals themselves (sigma^2 = ss_res / dof). That
        makes reduced chi-square == 1 by construction; it is reported anyway for
        completeness, while RMSE gives the scatter in signal units and AICc/BIC
        (which only compare consistently across models on the SAME data) drive
        model selection. Durbin-Watson flags serially-correlated residuals -
        the fingerprint of a wrong model shape even when R^2 looks excellent.

        Returns a dict of plain floats (dof may be <= 0 for tiny datasets, in
        which case the affected entries are NaN).
        """
        n = int(len(y))
        p = int(n_params)
        dof = n - p
        eps = ss_res if ss_res > 0 else 1e-300     # guard log(0) on a perfect fit

        rmse = float(np.sqrt(ss_res/n)) if n else float('nan')
        if dof > 0:
            red_chi2 = float(ss_res/dof)
            adj_r2 = float(1.0 - (1.0 - r_squared)*(n - 1)/dof)
        else:
            red_chi2 = float('nan')
            adj_r2 = float('nan')

        # Information criteria (Gaussian-likelihood form, up to a shared const).
        aic = float(n*np.log(eps/n) + 2*p)
        if n - p - 1 > 0:
            aicc = float(aic + 2*p*(p + 1)/(n - p - 1))
        else:
            aicc = float('nan')
        bic = float(n*np.log(eps/n) + p*np.log(n)) if n > 0 else float('nan')

        # Durbin-Watson: ~2 => uncorrelated residuals; <<2 positive, >>2 negative.
        dr = np.diff(residuals)
        dw = float(np.sum(dr*dr)/ss_res) if ss_res > 0 else float('nan')

        return {
            'n_points': n, 'n_params': p, 'dof': dof,
            'rmse': rmse, 'red_chi2': red_chi2, 'adj_r_squared': adj_r2,
            'aic': aic, 'aicc': aicc, 'bic': bic, 'durbin_watson': dw,
        }

    ###############################################################
    # Backwards-compatible helper kept for existing scripts
    ###############################################################
    def one_exp_fit(self, curve, guess_array):
        from scipy import optimize

        popt_exp, pcov_exp = optimize.curve_fit(self.exponential, curve[0], curve[1], p0=guess_array)

        axis_y_exp = self.exponential(curve[0], popt_exp[0], popt_exp[1], popt_exp[2])
        model_data = np.transpose(np.column_stack((curve[0], axis_y_exp)))

        residuals = np.transpose(np.column_stack((curve[0], curve[1] - axis_y_exp)))
        ss_res = np.sum(residuals[1]**2)
        ss_tot = np.sum((curve[1]-np.mean(curve[1]))**2)
        r_squared = 1 - (ss_res / ss_tot)

        return model_data, residuals, r_squared

if __name__ == "__main__":
    main()
