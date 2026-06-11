# Math Modules

Helper modules for offline data analysis: least-squares curve fitting, 1D
signal processing (apodization, zero filling, smoothing, baseline subtraction,
echo-centre detection), FFT and phase correction, and DEER/PDS
distance-distribution analysis. They take
and return plain NumPy arrays, so a result can be pushed straight to LivePlot
with [`plot_1d()`](../plotting_functions/usage.md) or saved with
[`save_data()`](../general_functions/data_managment.md#save_data).

!!! note "scipy is an optional dependency"
    The fitting routines, Savitzky–Golay smoothing, and the whole DEER engine
    require `scipy`, which is part of the `math` extra:

    ```bash
    pip install -e .[math]
    ```

    The modules import `scipy` lazily, so importing them never fails on a
    minimal install — only the functions that need `scipy` raise a
    `RuntimeError` when it is missing.

## [Least-squares fitting](fitting.md)

`import atomize.math_modules.least_square_fitting_modules as math_modules`

| Function | Description |
| -------- | ----------- |
| [`math()`](fitting.md#class) | Create a fitter exposing the model registry |
| [`fit(model, x, y, guess=None, no_offset=False)`](fitting.md#fit) | Fit `(x, y)` with a named model; returns a result dict |
| [`model_names()`](fitting.md#model_names) | List the available model keys |
| [`param_names(model)`](fitting.md#param_names) | Parameter names of a model |
| [`default_guess(model, x, y)`](fitting.md#default_guess) | Heuristic initial guess for a model |
| [`one_exp_fit(curve, guess_array)`](fitting.md#one_exp_fit) | Legacy single-exponential fit |

## [Signal processing](signal_processing.md)

`import atomize.math_modules.signal_processing as sigproc`

| Function | Description |
| -------- | ----------- |
| [`apodization_window(n, name, param=8.6)`](signal_processing.md#apodization_window) | Build an apodization window of length `n` |
| [`zerofill_length(length, choice)`](signal_processing.md#zerofill_length) | Target FFT length for a zero-fill choice |
| [`echo_center(envelope, window=0)`](signal_processing.md#echo_center) | Echo-centre index from a magnitude envelope |
| [`Signal_Processing()`](signal_processing.md#class) | Smoothing / baseline / normalization helpers |
| [`savitzky_golay(y, window=11, order=3)`](signal_processing.md#savitzky_golay) | Savitzky–Golay smoothing (needs scipy) |
| [`moving_average(y, window=5)`](signal_processing.md#moving_average) | Centred moving-average smoothing |
| [`baseline_poly(x, y, order=1, region='all', npts=0)`](signal_processing.md#baseline_poly) | Subtract a polynomial baseline |
| [`normalize(y, mode='minmax')`](signal_processing.md#normalize) | Normalize a curve |

## [FFT / phase correction](fft.md)

`import atomize.math_modules.fft as fft_module`

| Function | Description |
| -------- | ----------- |
| [`Fast_Fourier()`](fft.md#class) | Create the FFT / phase-correction helper |
| [`auto_phase_zero(spectrum, threshold=0.1)`](fft.md#auto_phase_zero) | Zero-order auto-phase (degrees) maximising the magnitude-weighted real part |
| [`ph_correction(freq, data_i, data_q, cor1, cor2, cor3)`](fft.md#ph_correction) | Apply a zero/first/second-order phase polynomial to I+iQ |
| [`fft(x_axis, data_i, data_q, sample_spacing, re='False')`](fft.md#fft) | FFT of I+iQ; magnitude or real/imag parts (ns → MHz) |

## [DEER / PDS analysis](deer.md)

`import atomize.math_modules.deer as deer`

Distance-distribution analysis for pulsed-dipolar spectroscopy (DEER/PELDOR,
RIDME, DQC, SIFTER): background correction + Tikhonov/NNLS inversion of the
orientation-averaged dipolar kernel, with GCV (or L-curve) regularization and a
choice of sequential or joint (DeerLab-style) background fitting. Times in µs,
distances in nm.

| Function | Description |
| -------- | ----------- |
| [`deer_invert(t, V, …)`](deer.md#deer_invert) | One-call pipeline: background-correct → kernel → P(r) (`engine`/`method`) |
| [`deer_invert_joint(t, V, …)`](deer.md#deer_invert_joint) | Joint (separable-NLLS) fit of background + λ together with P(r) |
| [`deer_validate(t, V, …)`](deer.md#deer_validate) | Ensemble validation: background-sweep → median P(r) + uncertainty band |
| [`dipolar_kernel(t, r, …)`](deer.md#dipolar_kernel) | Orientation-averaged kernel K(t, r) (Fresnel closed form) |
| [`dipolar_frequency(r, …)`](deer.md#dipolar_frequency) | Perpendicular dipolar frequency ν⊥(r) = ν_dd/r³ |
| [`background_fit(t, V, bg_start, bg_end=None, …)`](deer.md#background_fit) | Fit intermolecular background on a tail window |
| [`tikhonov_nnls(K, F, alpha, L=None)`](deer.md#tikhonov_nnls) | Non-negative Tikhonov solve K P = F |
| [`regularization_matrix(n, order=2)`](deer.md#regularization_matrix) | Derivative operator L for smoothing |
| [`l_curve(K, F, alphas, L=None, method='gcv')`](deer.md#l_curve) | Regularization scan; α by GCV (default) or Menger L-corner |
| [`default_r_axis(rmin=1.5, rmax=8.0, n=200)`](deer.md#default_r_axis) | Default distance grid (nm) |
| [`simulate(t, r, P, …)`](deer.md#simulate) | Forward-simulate a DEER trace from P(r) |

## [Coherence pathways & phase cycling](coherence_pathways.md)

`import atomize.math_modules.coherence_pathways as coh`

Pure-Python (no scipy) bookkeeping for pulse-EPR phase cycles: expand short
phase-cycle notation, then enumerate every coherence transfer pathway and see
which the cycle **keeps** vs **phases out**, where each surviving echo lands, and
which FIDs survive. Selection rule, not amplitudes (Stoll 2008; Prisner 2016).

| Function | Description |
| -------- | ----------- |
| [`expand_phase_cycling(recv, *pulse_phases)`](coherence_pathways.md#expand_phase_cycling) | Expand short notation `(x)`/`[x]`/lists/coeffs into per-step pulse + receiver phases |
| [`analyze_pathways(recv, pulse_phases, positions, det_pos)`](coherence_pathways.md#analyze_pathways) | Enumerate pathways; classify kept/suppressed, echo positions, FIDs |
| [`pathway_report(recv, pulse_phases, positions, det_pos)`](coherence_pathways.md#pathway_report) | Ready-to-print summary table of the above |
| [`positions_from_taus(taus, base=0.0, grid=None)`](coherence_pathways.md#positions_from_taus) | Cumulative pulse positions from inter-pulse delays (optional grid snap) |

## [Pulse excitation profiles](pulse_excitation.md)

`import atomize.math_modules.pulse_excitation as pe`

Excitation/inversion profiles of shaped pulses (rectangular, gaussian, sinc,
sine, WURST, sech/tanh) across resonance offset, by full Bloch/propagator spin
dynamics of a single S=1/2 — the EasySpin `exciteprofile` approach, correct for
adiabatic pulses, not just the FFT approximation. Pure NumPy (no scipy).
Frequencies/offsets in GHz, times in ns; shape params in MHz.

| Function | Description |
| -------- | ----------- |
| [`excitation_profile(shape, tp, nu1, offsets, params, …)`](pulse_excitation.md#excitation_profile) | Single-pulse Mx/My/Mz vs offset from an initial state |
| [`waveform(shape, t, tp, params)`](pulse_excitation.md#waveform) | Amplitude envelope + instantaneous frequency of a shape |
| [`flip_angle(shape, tp, nu1, params, dt=0.5)`](pulse_excitation.md#flip_angle) | On-resonance flip angle (pulse area) |
| [`propagate_pulse(M, shape, tp, nu1, offsets, params, …)`](pulse_excitation.md#propagate_pulse) | Apply one pulse to a Bloch-vector array (chain for sequences) |
| [`free_evolution(M, offsets, tau)`](pulse_excitation.md#free_evolution) | Free precession for `tau` ns (z-rotation by offset) |
