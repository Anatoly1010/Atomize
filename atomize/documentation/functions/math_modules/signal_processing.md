# Signal Processing

Lightweight 1D signal-processing helpers used by the FFT / smoothing workflows:
apodization windows, FFT zero-fill sizing, echo-centre detection, and a small
`Signal_Processing` class for smoothing, baseline subtraction, and
normalization. Every routine takes and returns plain NumPy arrays.

```python
import numpy as np
import atomize.math_modules.signal_processing as sigproc
```

The module-level functions ([`apodization_window`](#apodization_window),
[`zerofill_length`](#zerofill_length), [`echo_center`](#echo_center)) are called
directly; the smoothing / baseline / normalization helpers live on the
[`Signal_Processing`](#class) class.

!!! note
    [`savitzky_golay()`](#savitzky_golay) requires `scipy` (the `math` extra:
    `pip install -e .[math]`); everything else is NumPy-only.

---

## apodization_window() { #apodization_window data-toc-label="apodization_window" }

```python
w = sigproc.apodization_window(n, name, param=8.6)
```

Returns an apodization window of length `n` to multiply onto a time-domain
signal before an FFT. `name` is one of:

`'None'`, `'Hann'`, `'Hamming'`, `'Blackman'`, `'Bartlett'`, `'Flat-top'`,
`'Kaiser'`, `'Gaussian'`, `'Tukey'`.

`param` is the shape parameter for the three parametric windows and is ignored
by the rest:

| Window | `param` meaning | Typical |
| ------ | --------------- | ------- |
| `Kaiser` | β | 8.6 |
| `Gaussian` | σ as a fraction of `n` | 0.15 |
| `Tukey` | α taper fraction (`0` → rectangular, `1` → Hann) | 0.5 |

```python
signal = signal*sigproc.apodization_window(len(signal), 'Kaiser', 8.6)
```

---

## zerofill_length() { #zerofill_length data-toc-label="zerofill_length" }

```python
n = sigproc.zerofill_length(length, choice)
```

Target FFT length for a zero-fill `choice`: `'None'` (returns `length`),
`'×2'` / `'×4'` / `'×8'` (or the ASCII `'x2'`…), or `'Next pow₂'` (the smallest
power of two ≥ `length`). Feed the result to `numpy.fft.fft(signal, n)`.

```python
n = sigproc.zerofill_length(len(signal), '×4')
spectrum = np.fft.fft(signal, n)
freq = np.fft.fftfreq(n, dt)
```

---

## echo_center() { #echo_center data-toc-label="echo_center" }

```python
k = sigproc.echo_center(envelope, window=0)
```

Returns the index of the echo centre in a 1D **magnitude** envelope. Pass an
offset-invariant envelope such as `sqrt(I**2 + Q**2)` so the carrier modulation
from a field/frequency offset has already cancelled and only the echo shape
remains — then the centre is the envelope peak, refined by a local
centre-of-mass and rounded to the nearest sample.

`window` is the half-width (in points) of the centre-of-mass window around the
peak. With `window <= 0` (default) it is sized automatically from the **crest
width**: walk out from the peak until the envelope drops below 70 % of the peak
height, then take the narrower of the two sides. Measuring from the crest
(rather than a baseline-relative half-maximum) keeps the result on the peak even
when the pre-echo baseline is elevated — there a half-maximum can sit at the
baseline level, the window blows up, and a slow FID decay drags the
centre-of-mass far past the true peak. A positive `window` forces that exact
half-width.

This is used to start an FFT "from the centre of the echo": find `k`, drop the
first `k` points, and the dead-time first-order phase ramp disappears.

```python
env = np.sqrt(i**2 + q**2)
k = sigproc.echo_center(env)
spectrum = np.fft.fft((i + 1j*q)[k:], n)
```

---

## Signal_Processing() { #class data-toc-label="Signal_Processing()" }

```python
sp = sigproc.Signal_Processing()
```

Creates the helper object exposing the methods below.

---

## savitzky_golay() { #savitzky_golay data-toc-label="savitzky_golay" }

```python
y_smooth = sp.savitzky_golay(y, window=11, order=3)
```

Savitzky–Golay smoothing (requires `scipy`). `window` must be odd and greater
than `order`; it is auto-corrected (forced odd, clamped to the data length) if
not. Raises `RuntimeError` when `scipy` is missing.

---

## moving_average() { #moving_average data-toc-label="moving_average" }

```python
y_smooth = sp.moving_average(y, window=5)
```

Centred moving-average smoothing; edges are padded by reflection so the output
has the same length as `y`. NumPy-only.

---

## baseline_poly() { #baseline_poly data-toc-label="baseline_poly" }

```python
y_corr = sp.baseline_poly(x, y, order=1, region='all', npts=0)
```

Fits a polynomial of the given `order` and subtracts it from the full curve.
`region` selects which points the polynomial is fitted to, so the baseline can
be estimated from signal-free regions (e.g. the trace tails):

| `region` | Points used for the fit |
| -------- | ----------------------- |
| `'all'` | every point (default) |
| `'first'` | the first `npts` points |
| `'last'` | the last `npts` points |
| `'ends'` | the first and last `npts` points |

`npts` is ignored when `region='all'` (or when it would select the whole
curve).

```python
# remove a linear baseline estimated from the first and last 50 points
y_corr = sp.baseline_poly(x, y, order=1, region='ends', npts=50)
```

---

## normalize() { #normalize data-toc-label="normalize" }

```python
y_norm = sp.normalize(y, mode='minmax')
```

Normalizes `y`. `mode`:

| `mode` | Result |
| ------ | ------ |
| `'minmax'` | rescaled to `[0, 1]` |
| `'max'` | divided by `max(|y|)` |
| `'area'` | divided by its absolute area (unit area) |
