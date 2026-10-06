# FFT / Phase Correction

Fourier-transform and phase-correction helpers for complex (I/Q) data, used by the pulse-EPR phasing tools and the Data Treatment workflows. Everything is NumPy-only (no `scipy`); every routine takes and returns plain NumPy arrays.

```python
import numpy as np
import atomize.math_modules.fft as fft_module

fft = fft_module.Fast_Fourier()
```

By project convention, `Fast_Fourier.fft` interprets `sample_spacing` in **ns** and returns frequency in **MHz**. `ph_correction` accepts phase coefficients in **radians**, radians per axis unit, and radians per axis unit squared; the caller supplies any conversion from degrees or frequency shifts.

## Axis conversion helpers

```python
fft_module.time_axis_ns(axis, unit)         # -> ndarray, time in ns
fft_module.frequency_axis_mhz(axis, unit)   # -> ndarray, frequency in MHz
```

These functions convert a scalar or array using its stated axis unit. `time_axis_ns` accepts `s`, `ms`, `us` (also `µs` or `μs`), `ns` and `ps`. `frequency_axis_mhz` accepts `Hz`, `kHz`, `MHz`, `GHz` and `THz`. Missing or unsupported units raise `ValueError`; no unit is inferred from the numerical values.

---

## Functions

### Fast_Fourier() { #class data-toc-label="Fast_Fourier()" }

```python
fft = fft_module.Fast_Fourier()
```

Create the helper. The transform/phase methods are pure array math; [`auto_phase_zero`](#auto_phase_zero) is a `@staticmethod` and can be called on the class without an instance.

---

### auto_phase_zero() { #auto_phase_zero data-toc-label="auto_phase_zero" }

```python
phi0 = fft_module.Fast_Fourier.auto_phase_zero(spectrum, threshold=0.1)
```

Zero-order auto-phase. Returns the phase **in degrees** (`[0, 360)`) that rotates a complex `spectrum` onto the real axis.

Each bin is `S_k = |S_k|·e^{iθ_k}`; we want a single `φ₀` with `θ_k + φ₀ ≈ 0` over the significant bins. The estimator is the **principal-axis** ("square-the-signal") form

```text
φ₀ = -½·angle( Σ S_k² )
```

`S_k²` has phase `2θ_k` weighted by `|S_k|²`, so halving its angle recovers the common axis the significant bins lie on. Because it is **sign-blind**, it phases **bipolar** data correctly — e.g. an inversion-recovery T₁ curve whose echo is negative at short delay and positive after recovery, or any trace that crosses zero. The older magnitude-weighted vector sum `Σ |S_k|·S_k` fails there: opposite-sign bins cancel and bias `φ₀`. For unipolar data (an FFT peak, a plain FID, a T₂ decay) the two agree exactly. The ±180° ambiguity of the axis is resolved by flipping to the orientation that makes the magnitude-weighted real part positive.

A magnitude `threshold` (default 10 % of the peak) keeps noise and baseline bins out. The value is meant to be fed back as the zero-order term of [`ph_correction`](#ph_correction) (`cor1 = φ₀·π/180`).

This handles **only** the zero-order (constant) phase. A linear phase ramp from the receiver dead time is removed separately by starting the FFT at the echo centre — see [`echo_center`](signal_processing.md#echo_center).

```python
# spectrum of an echo-centred, complex FID
env = np.sqrt(i**2 + q**2)
k = sigproc.echo_center(env)                       # kills the first-order ramp
spectrum = np.fft.fft((i + 1j*q)[k:], n)

phi0 = fft.auto_phase_zero(spectrum)               # zero-order, in degrees
real, imag = fft.ph_correction(np.fft.fftfreq(n), spectrum.real, spectrum.imag,
                               phi0*np.pi/180, 0.0, 0.0)
```

!!! warning
    The returned value belongs to the time origin the spectrum was built from. A spectral line at offset `f` carries a phase that changes by `360·f·dt` degrees **per sample** of echo-centre skip — 72°/sample for a 100 MHz carrier at `dt = 2 ns`. The `φ₀` measured on a skipped spectrum is therefore the right value for *that* spectrum, and is wrong by `360·f·skip·dt` for a correction applied to the trace from the start of the window. Phase the spectrum it was measured on, or use [`auto_phase_zero_echo`](#auto_phase_zero_echo), which does not move the origin.

---

### auto_phase_zero_echo() { #auto_phase_zero_echo data-toc-label="auto_phase_zero_echo" }

```python
auto_phase_zero_echo(signal)               # -> float; zero-order phase in degrees, [0, 360)
auto_phase_zero_echo(signal, frac=0.5)     # tighter echo window (50 % of the envelope peak)
```

This function is a zero-order auto-phase measured on the **time-domain echo**, for a correction that is applied in the time domain. It should be called with the complex signal `I + 1j*Q`, either a single trace or a 2D stack in which rows are traces and columns are the time axis. The returned value is meant to be fed back as the zero-order term of [`ph_correction`](#ph_correction) (`cor1 = φ₀·π/180`).

The echo window is the set of samples where the `|signal|` envelope, averaged over the traces, is at or above `frac` of its peak. Inside that window the estimator works in two levels: each trace is first summed coherently, `s_r = Σ z_r(t)`, and the per-trace sums are then combined by the sign-blind principal axis of [`auto_phase_zero`](#auto_phase_zero), `φ₀ = -½·angle(Σ s_r²)`.

Both levels earn their place. Summing each trace first makes the estimate track the integrated echo — the quantity the phased data is actually headed for — and the `|s_r|²` weighting of the second level all but drops traces that have decayed into noise, which a sample-by-sample estimate cannot do. Squaring the per-trace sums keeps the sign-blindness, so a set whose traces change sign, such as an inversion recovery, still phases correctly. The ±180° the axis leaves open is resolved as in [`auto_phase_zero`](#auto_phase_zero), by the orientation that makes the magnitude-weighted real part positive; for a balanced bipolar set that choice is arbitrary either way. For a single trace the whole thing collapses to `φ₀ = -angle(Σ z)` over the echo.

This function should be preferred to [`auto_phase_zero`](#auto_phase_zero) whenever the phase multiplies the trace rather than its transform. Restricting to the echo does the same job the leading-point skip does for the frequency-domain estimator — removing the dead-time ramp — without shifting the time origin that the correction is applied from.

!!! warning
    An undemodulated record — anything digitised at an intermediate frequency rather than at the video output — carries the whole signal at that offset, and **no zero-order phase can make such a trace real**: its real part just oscillates. `z²` then rotates right around the circle and the sum cancels. Check the offset with [`carrier_offset`](#carrier_offset) and remove it with the first-order term before calling this function.

```python
z = i + 1j*q                                             # 2D: rows are traces
f0 = fft.carrier_offset(z, dt)                           # cycles per unit dt
z = z*np.exp(-2j*np.pi*f0*dt*np.arange(z.shape[1]))      # demodulate

phi0 = fft.auto_phase_zero_echo(z)
real, imag = fft.ph_correction(t, z.real, z.imag, phi0*np.pi/180, 0.0, 0.0)
```

---

### carrier_offset() { #carrier_offset data-toc-label="carrier_offset" }

```python
carrier_offset(signal, dt)               # -> float; line offset in cycles per unit of dt
carrier_offset(signal, dt, frac=0.5)     # tighter echo window (50 % of the envelope peak)
```

This function returns the dominant line offset of a time-domain echo, in cycles per unit of `dt`, so that `f0*1000` is MHz when `dt` is given in ns. The `signal` and `frac` arguments are the same as for [`auto_phase_zero_echo`](#auto_phase_zero_echo). Feeding `-f0` to the first-order term of [`ph_correction`](#ph_correction) (`cor2 = -2π·f0`) brings the signal to zero frequency, which is what makes a zero-order phase meaningful in the first place.

The offset is estimated from the phase increment per sample over the echo window, `f0 = angle(Σ z(t+1)·z*(t)) / (2π·dt)`. This needs neither frequency resolution nor zero fill, and is unambiguous up to the Nyquist offset `±1/(2·dt)`.

---

### ph_correction() { #ph_correction data-toc-label="ph_correction" }

```python
out = fft.ph_correction(freq, data_i, data_q, cor1, cor2, cor3)
real, imag = out          # out has shape (2, N)
```

Multiplies the complex signal `data_i + 1j·data_q` by a phase polynomial and returns its real and imaginary parts stacked as `np.array((real, imag))`:

```text
(data_i + 1j·data_q) · exp( i·(cor1 + cor2·freq + cor3·freq²) )
```

| Argument | Role |
| -------- | ---- |
| `cor1` | zero-order phase, **radians** (e.g. `φ₀·π/180` from [`auto_phase_zero`](#auto_phase_zero)) |
| `cor2` | first-order coefficient (per unit of `freq`) — a linear ramp / group delay |
| `cor3` | second-order coefficient (per `freq²`) |
| `freq` | the abscissa the ramp is evaluated on (frequency after an FFT, or time) |

`data_i` / `data_q` may be 1-D (a single trace) or 2-D (rows = traces); the 2-D return is transposed so the two channels index as `out[0]` / `out[1]`. In the Data Treatment tools the first/second-order fields are entered as a frequency offset where `50 → 50 MHz` when `freq` is in ns, i.e. `cor = 2π·value/1000` per x-unit.

---

### fft() { #fft data-toc-label="fft" }

```python
freq, mag        = fft.fft(x_axis, data_i, data_q, sample_spacing)               # re='False'
freq, real, imag = fft.fft(x_axis, data_i, data_q, sample_spacing, re='True')    # re='True'
```

Fourier-transforms the complex signal `data_i + 1j·data_q` and returns the result sorted by frequency. `sample_spacing` is the time step in **ns**, so the returned `freq` axis is in **MHz** (`fftfreq(n, sample_spacing·10⁻³)`).

- `re='False'` (default) — returns `(freq, magnitude)`, the magnitude spectrum.
- `re='True'` — returns `(freq, real, imag)`, the complex parts separately.

`data_i` / `data_q` may be 1-D or 2-D; a 2-D input is transformed along `axis=1` (within each trace). If the input contains any `NaN`, an all-`NaN` result of the matching shape is returned.

```python
freq, mag = fft.fft(time_ns, i, q, sample_spacing=2.0)   # 2 ns step → MHz axis
```
