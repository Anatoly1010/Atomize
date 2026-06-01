#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import numpy as np

# scipy.signal is an optional dependency (pip install -e .[math]) and slow to
# import (~0.5 s on Windows). Probe availability cheaply -- find_spec does NOT
# import scipy -- and defer the real import to savitzky_golay(), so importing
# this module stays numpy-only (apodization / zero-fill / echo-center need no
# scipy) and GUIs that embed it start fast.
import importlib.util
SCIPY_AVAILABLE = importlib.util.find_spec('scipy') is not None


def apodization_window(n, name, param=8.6):
    """Apodization window of length n (numpy-only, no scipy needed).

    `param` is the shape parameter for the parametric windows: Kaiser beta,
    Gaussian sigma (as a fraction of N), or Tukey alpha (taper fraction). It is
    ignored by the fixed-shape windows. Shared by the 1D and 2D Data Treatment
    windows so the two tools apply identical apodization.
    """
    n = int(n)
    if name == 'None' or n < 2:
        return np.ones(n)
    if name == 'Hann':
        return np.hanning(n)
    if name == 'Hamming':
        return np.hamming(n)
    if name == 'Blackman':
        return np.blackman(n)
    if name == 'Bartlett':
        return np.bartlett(n)
    if name == 'Kaiser':
        return np.kaiser(n, float(param))
    if name == 'Flat-top':
        k = np.arange(n)
        a = [0.21557895, 0.41663158, 0.277263158, 0.083578947, 0.006947368]
        return (a[0] - a[1]*np.cos(2*np.pi*k/(n - 1)) + a[2]*np.cos(4*np.pi*k/(n - 1))
                - a[3]*np.cos(6*np.pi*k/(n - 1)) + a[4]*np.cos(8*np.pi*k/(n - 1)))
    if name == 'Gaussian':
        std = max(float(param), 1e-6)*n
        k = np.arange(n) - (n - 1)/2.0
        return np.exp(-0.5*(k/std)**2)
    if name == 'Tukey':
        alpha = float(param)
        if alpha <= 0:
            return np.ones(n)
        if alpha >= 1:
            return np.hanning(n)
        x = np.linspace(0, 1, n)
        w = np.ones(n)
        lo = x < alpha/2.0
        hi = x >= 1 - alpha/2.0
        w[lo] = 0.5*(1 + np.cos(2*np.pi/alpha*(x[lo] - alpha/2.0)))
        w[hi] = 0.5*(1 + np.cos(2*np.pi/alpha*(x[hi] - 1 + alpha/2.0)))
        return w
    return np.ones(n)


def zerofill_length(length, choice):
    """Target FFT length for a zero-fill combo choice ('None', 'x2'..., 'Next pow2')."""
    length = int(length)
    if choice.startswith('×') or choice.startswith('x'):
        return length*int(choice[1:])
    if 'pow' in choice.lower():
        n = 1
        while n < length:
            n *= 2
        return n
    return length


def echo_center(envelope, window=0):
    """Index of the echo centre in a 1D magnitude envelope.

    The envelope should be offset-invariant (e.g. sqrt(I**2 + Q**2)), so the
    carrier modulation from a field/frequency offset has already cancelled and
    only the echo shape remains. Returns the coarse magnitude-peak index
    refined by a local centre-of-mass, rounded to the nearest integer sample.

    window: half-width (in points) of the centre-of-mass window around the
    peak; <= 0 picks ~5 % of the length (min 3).
    """
    env = np.abs(np.asarray(envelope, dtype=float))
    n = env.size
    if n < 3:
        return 0
    k = int(np.argmax(env))
    if window <= 0:
        window = max(3, int(round(0.05*n)))
    lo = max(0, k - window)
    hi = min(n, k + window + 1)
    seg = env[lo:hi]
    s = seg.sum()
    if s <= 0:
        return k
    idx = np.arange(lo, hi)
    com = float((idx*seg).sum()/s)
    return int(min(max(round(com), 0), n - 1))


class Signal_Processing():
    """Lightweight 1D signal-processing helpers (smoothing, baseline, scaling).

    Every method takes and returns plain numpy arrays so the result can be
    pushed straight to LivePlot or saved to CSV by the caller.
    """

    def __init__(self):
        if len(sys.argv) > 1:
            self.test_flag = sys.argv[1]
        else:
            self.test_flag = 'None'

    def savitzky_golay(self, y, window=11, order=3):
        """Savitzky-Golay smoothing. window must be odd and > order."""
        if not SCIPY_AVAILABLE:
            raise RuntimeError("scipy is required for Savitzky-Golay smoothing. "
                               "Install with: pip install -e .[math]")
        from scipy.signal import savgol_filter
        y = np.asarray(y, dtype=float)
        window = int(window)
        order = int(order)
        if window % 2 == 0:
            window += 1
        window = min(window, len(y) - (1 - len(y) % 2))
        if window <= order:
            window = order + 1 + (order % 2)
        return savgol_filter(y, window, order)

    def moving_average(self, y, window=5):
        """Centered moving-average smoothing; edges padded by reflection."""
        y = np.asarray(y, dtype=float)
        window = max(1, int(window))
        if window == 1:
            return y.copy()
        kernel = np.ones(window)/window
        pad = window//2
        padded = np.pad(y, pad, mode='reflect')
        smoothed = np.convolve(padded, kernel, mode='same')
        return smoothed[pad:pad + len(y)]

    def baseline_poly(self, x, y, order=1, region='all', npts=0):
        """Subtract a polynomial baseline of the given order.

        region: 'all'  -> fit the baseline to every point (default)
                'first' -> fit only the first `npts` points
                'last'  -> fit only the last `npts` points
                'ends'  -> fit only the first and last `npts` points
        The fitted polynomial is then subtracted from the full curve. This lets
        you estimate a baseline from signal-free regions (e.g. the trace tails).
        """
        x = np.asarray(x, dtype=float)
        y = np.asarray(y, dtype=float)
        n = len(x)
        npts = int(npts)
        if region == 'all' or npts <= 0 or 2*npts >= n:
            sel = np.arange(n)
        elif region == 'first':
            sel = np.arange(0, npts)
        elif region == 'last':
            sel = np.arange(n - npts, n)
        else:   # 'ends'
            sel = np.concatenate([np.arange(0, npts), np.arange(n - npts, n)])
        coeffs = np.polyfit(x[sel], y[sel], int(order))
        baseline = np.polyval(coeffs, x)
        return y - baseline

    def normalize(self, y, mode='minmax'):
        """Normalize y. mode: 'minmax' -> [0, 1], 'max' -> /max(|y|), 'area' -> unit area."""
        y = np.asarray(y, dtype=float)
        if mode == 'minmax':
            span = float(np.max(y) - np.min(y)) or 1.0
            return (y - np.min(y))/span
        elif mode == 'max':
            peak = float(np.max(np.abs(y))) or 1.0
            return y/peak
        elif mode == 'area':
            area = float(np.trapz(np.abs(y))) or 1.0
            return y/area
        return y.copy()

if __name__ == "__main__":
    main()
