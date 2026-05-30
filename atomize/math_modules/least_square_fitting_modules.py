#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import numpy as np

# scipy is an optional dependency (pip install -e .[math]); imported lazily so
# that simply importing this module never fails on a minimal install.
try:
    import scipy
    from scipy import optimize
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False


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

    def _guess_exponential(self, x, y):
        b = float(y[-1])
        a = float(y[0] - b)
        span = float(x[-1] - x[0]) or 1.0
        return [a, span/3.0, b]

    def _guess_biexponential(self, x, y):
        b = float(y[-1])
        a = float(y[0] - b)
        span = float(x[-1] - x[0]) or 1.0
        return [a/2.0, span/2.0, a/2.0, span/8.0, b]

    def _guess_stretched(self, x, y):
        b = float(y[-1])
        a = float(y[0] - b)
        span = float(x[-1] - x[0]) or 1.0
        return [a, span/3.0, 1.0, b]

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

        return {
            'y_fit': y_fit,
            'residuals': residuals,
            'popt': popt,
            'perr': perr,
            'r_squared': r_squared,
            'param_names': names,
        }

    ###############################################################
    # Backwards-compatible helper kept for existing scripts
    ###############################################################
    def one_exp_fit(self, curve, guess_array):

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
