# FFT / Phase Correction

Fourier-transform and phase-correction helpers for complex (I/Q) data, used by
the pulse-EPR phasing tools and the Data Treatment workflows. Everything is
NumPy-only (no `scipy`); every routine takes and returns plain NumPy arrays.

```python
import numpy as np
import atomize.math_modules.fft as fft_module

fft = fft_module.Fast_Fourier()
```

By project convention, `Fast_Fourier.fft` interprets `sample_spacing` in **ns** and returns frequency in **MHz**. `ph_correction` accepts phase coefficients in **radians**, radians per axis unit, and radians per axis unit squared; the caller supplies any conversion from degrees or frequency shifts.

## Data Treatment phase modes

The 1D and 2D Data Treatment **Phase** tabs keep independent settings for two modes. **Time-domain** applies a constant phase in **deg** and a **Frequency shift** in **MHz**. Positive shifts move the carrier toward higher frequency. **Auto** beside the frequency shift estimates the carrier-cancelling shift, refines it over the echo, and then sets the constant phase. The time-axis unit must be specified; seconds, milliseconds, microseconds, nanoseconds and picoseconds are supported.

**Frequency-domain** uses `phase(f) = zero + first*(f - pivot) + second*(f - pivot)**2`, with phase in degrees and frequency in MHz. First order is **deg/MHz**; second order is **deg/MHz²**. **Advanced** contains second order and **Pivot frequency**, which defaults to zero. **Auto** estimates zero order with the entered first and second orders already applied. This mode operates on an existing spectrum. For time-domain input, use **FFT → Result → input → Phase**; all transform settings are in the **FFT** tab. Spectral input labelled Hz, kHz, MHz, GHz or THz is converted to MHz when evaluating the phase polynomial.

The mode follows recognized units of the current input axis: time units select **Time-domain**, and frequency units select **Frequency-domain**. Loading or selecting input, promoting a result, undoing a 1D step, resetting 2D data, or editing input units updates the selection. An FFT preview alone does not replace the input; **Result → input** selects **Frequency-domain** once the spectrum becomes the input. In 2D this follows X, so a Y-only FFT leaves the Phase mode in **Time-domain**. Unknown units leave the current selection unchanged, and each mode retains its own parameter values.

The 2D **Auto shear** workflow always uses time-domain frequency shifting. It restores the raw I/Q data, reads the nominal IF from the AWG header (or the time-domain **Frequency shift** field), shifts to baseband, low-pass filters X, refines the residual shift and constant phase, and then estimates the echo centre and shear slope. Spectral phase settings are preserved. Auto shear requires X to be the echo-time axis and Y to be the dipolar-time axis, with nonzero spacing. Both time axes are converted to ns for shearing, so the slope is dimensionless and **Shear origin** and **Fit window** are in ns even when the input axes use different time units.

## Axis conversion helpers

```python
fft_module.time_axis_ns(axis, unit)         # -> ndarray, time in ns
fft_module.frequency_axis_mhz(axis, unit)   # -> ndarray, frequency in MHz
```

These functions convert a scalar or array using its stated axis unit. `time_axis_ns` accepts `s`, `ms`, `us` (also `µs` or `μs`), `ns` and `ps`. `frequency_axis_mhz` accepts `Hz`, `kHz`, `MHz`, `GHz` and `THz`. Missing or unsupported units raise `ValueError`; no unit is inferred from the numerical values.

---

## Fast_Fourier() { #class data-toc-label="Fast_Fourier()" }

```python
fft = fft_module.Fast_Fourier()
```

Create the helper. The transform/phase methods are pure array math;
[`auto_phase_zero`](#auto_phase_zero) is a `@staticmethod` and can be called on
the class without an instance.

---

## auto_phase_zero() { #auto_phase_zero data-toc-label="auto_phase_zero" }

```python
phi0 = fft_module.Fast_Fourier.auto_phase_zero(spectrum, threshold=0.1)
```

Zero-order auto-phase. Returns the phase **in degrees** (`[0, 360)`) that
maximises the magnitude-weighted real part of a complex `spectrum`.

Each bin is `S_k = |S_k|·e^{iθ_k}`; we want a single `φ₀` with `θ_k + φ₀ ≈ 0`
over the significant bins. Maximising `Σ |S_k|·Re(S_k·e^{iφ₀})` has the closed
form

```text
φ₀ = -angle( Σ |S_k|·S_k )
```

The `|S_k|` weighting, plus a magnitude `threshold` (default 10 % of the peak),
keep noise and baseline bins from biasing the result. The value is meant to be
fed back as the zero-order term of [`ph_correction`](#ph_correction)
(`cor1 = φ₀·π/180`).

This handles **only** the zero-order (constant) phase. A linear phase ramp from
the receiver dead time is removed separately by starting the FFT at the echo
centre — see [`echo_center`](signal_processing.md#echo_center).

```python
# spectrum of an echo-centred, complex FID
env = np.sqrt(i**2 + q**2)
k = sigproc.echo_center(env)                       # kills the first-order ramp
spectrum = np.fft.fft((i + 1j*q)[k:], n)

phi0 = fft.auto_phase_zero(spectrum)               # zero-order, in degrees
real, imag = fft.ph_correction(np.fft.fftfreq(n), spectrum.real, spectrum.imag,
                               phi0*np.pi/180, 0.0, 0.0)
```

!!! tip "Phase of an off-centre line couples to the sample timing"
    A spectral line at offset `f` carries a phase that changes by
    `360·f·dt` degrees per sample of echo-centre shift. For a line far from
    zero frequency, an integer echo-centre skip leaves a sub-sample residual
    that `auto_phase_zero` reports as part of `φ₀`; trim what remains with a
    small first-order term.

---

## ph_correction() { #ph_correction data-toc-label="ph_correction" }

```python
out = fft.ph_correction(freq, data_i, data_q, cor1, cor2, cor3)
real, imag = out          # out has shape (2, N)
```

Multiplies the complex signal `data_i + 1j·data_q` by a phase polynomial and
returns its real and imaginary parts stacked as `np.array((real, imag))`:

```text
(data_i + 1j·data_q) · exp( i·(cor1 + cor2·freq + cor3·freq²) )
```

| Argument | Role |
| -------- | ---- |
| `cor1` | zero-order phase, **radians** (e.g. `φ₀·π/180` from [`auto_phase_zero`](#auto_phase_zero)) |
| `cor2` | first-order coefficient (per unit of `freq`) — a linear ramp / group delay |
| `cor3` | second-order coefficient (per `freq²`) |
| `freq` | the abscissa the ramp is evaluated on (frequency after an FFT, or time) |

`data_i` / `data_q` may be 1-D (a single trace) or 2-D (rows = traces); the
2-D return is transposed so the two channels index as `out[0]` / `out[1]`. In
the Data Treatment tools the first/second-order fields are entered as a
frequency offset where `50 → 50 MHz` when `freq` is in ns, i.e.
`cor = 2π·value/1000` per x-unit.

---

## fft() { #fft data-toc-label="fft" }

```python
freq, mag        = fft.fft(x_axis, data_i, data_q, sample_spacing)               # re='False'
freq, real, imag = fft.fft(x_axis, data_i, data_q, sample_spacing, re='True')    # re='True'
```

Fourier-transforms the complex signal `data_i + 1j·data_q` and returns the
result sorted by frequency. `sample_spacing` is the time step in **ns**, so the
returned `freq` axis is in **MHz** (`fftfreq(n, sample_spacing·10⁻³)`).

- `re='False'` (default) — returns `(freq, magnitude)`, the magnitude spectrum.
- `re='True'` — returns `(freq, real, imag)`, the complex parts separately.

`data_i` / `data_q` may be 1-D or 2-D; a 2-D input is transformed along `axis=1`
(within each trace). If the input contains any `NaN`, an all-`NaN` result of the
matching shape is returned.

```python
freq, mag = fft.fft(time_ns, i, q, sample_spacing=2.0)   # 2 ns step → MHz axis
```
