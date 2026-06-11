# Pulse Excitation Profiles

Compute how a shaped microwave pulse acts on spins across resonance offset, by
full Bloch/propagator spin dynamics of a single $S=1/2$ — the EasySpin
`exciteprofile` approach. Because it propagates the actual dynamics (not the
linear-response / FFT approximation), it is correct for **adiabatic** pulses
(WURST, sech/tanh) as well as weak ones.

```python
import atomize.math_modules.pulse_excitation as pe
```

Pure NumPy, no hardware. Use it to design pulses (bandwidth, inversion quality),
estimate where two pulses at different carriers overlap, or build small two-pulse
sequences.

## Background

In the rotating frame of the microwave carrier a spin at resonance offset
$\Delta\omega$ sees

$$ H(t) = \Delta\omega\, S_z + \omega_1(t)\,[\cos\phi(t)\,S_x + \sin\phi(t)\,S_y], $$

with $\omega_1(t) = 2\pi\,\nu_1\,a(t)$ the instantaneous nutation (B<sub>1</sub>)
drive, $a(t)\in[0,1]$ the amplitude envelope and $\phi(t)$ the running RF phase
(carrier + chirp). The pulse is propagated **piecewise-constant**: over each short
step $dt$ the Hamiltonian is held at its mid-step value and

$$ \rho \to U\rho U^\dagger, \qquad U = \exp(-i\,2\pi\,dt\,H). $$

For a two-level system $U$ is an $SU(2)$ rotation, so instead of a matrix
exponential per (offset, step) the Bloch vector $\mathbf{M}=(M_x,M_y,M_z)$ is
rotated directly with Rodrigues' formula. This vectorises over the **whole offset
axis** at once, so a microsecond WURST profile computes in well under 0.1 s.

!!! info "Units"
    Internally everything is **GHz** (frequencies) and **ns** (time) — a product
    GHz·ns is a number of cycles. The offset axis, `nu1` and the result are in
    these base units; shape parameters in the `params` dict (`bw`, `center`, …)
    are in **MHz**. Convert MHz→GHz with `/1000` on the way in.

!!! warning "What is and isn't modelled"
    A single isolated $S=1/2$, coherent dynamics only — **no relaxation**
    (T<sub>1</sub>/T<sub>2</sub>), no B<sub>1</sub> inhomogeneity, no
    coupled/nuclear spins. A finite **resonator bandwidth** *can* be included via
    the optional `resonator` argument (see
    [Non-ideal pulses](#resonator)). The on-resonance flip angle from
    [`flip_angle`](#flip_angle) is the pulse *area*; for swept/adiabatic pulses
    the effective rotation is offset-dependent and not a single number — use
    [`adiabaticity_profile`](#adiabaticity_profile) to check whether a chirped
    pulse actually inverts across its band.

## Pulse shapes

`pe.SHAPES` lists the supported shapes. Parameter names and units follow the
common AWG (arbitrary-waveform generator) convention, so a pulse designed here
reproduces the one the hardware emits. Widths are in **ns**, frequencies in
**MHz**, `b` in **1/ns**. Every shape also reads `center` — the pulse **carrier**
frequency (MHz), which shifts the whole excitation band along the offset axis
(for WURST/sech it is the sweep centre).

| Shape | Extra `params` | Notes |
| ----- | -------------- | ----- |
| `rectangular` | `center` | constant envelope |
| `gaussian` | `sigma` (ns), `center` | $\exp[-\tfrac12((t-t_p/2)/\sigma)^2]$ — `sigma` is the Gaussian std (not FWHM) |
| `sinc` | `sigma` (ns), `center` | $\mathrm{sinc}(2(t-t_p/2)/\sigma)$, first zero at $\pm\sigma/2$ |
| `half-sine` | `center` | $\sin(\pi t/t_p)$ |
| `quartersine` | `edge` (ns), `center` | flat top, quarter-sine rise/fall over `edge` |
| `WURST` | `n`, `bw` (MHz), `center` | $1-\lvert\sin\rvert^{\,n}$ envelope, linear chirp across `bw` |
| `sech/tanh` | `b` (1/ns), `n`, `bw` (MHz), `center` | HS$n$ hyperbolic-secant adiabatic inversion; `b` truncation, `n` order |

!!! note "Sample-grid convention"
    The sech/tanh envelope and sweep are defined on a sample grid (the module
    constant `SAMPLE_RATE`, default 1.25 samples/ns = 1250 MHz), matching how an
    AWG builds the waveform; `b` is therefore tied to that sample rate. The other
    shapes are sample-rate-independent.

## `excitation_profile(shape, tp, nu1, offsets, params, dt=0.5, phi0=0.0, init=(0,0,1), resonator=None)` { #excitation_profile }

The excitation/inversion profile of a **single** pulse from an initial state
(default equilibrium $+z$).

| Argument | Description |
| -------- | ----------- |
| `shape` | one of `pe.SHAPES` |
| `tp` | pulse length (ns) |
| `nu1` | peak nutation / B<sub>1</sub> frequency (**GHz**); rectangular flip $=2\pi\,\nu_1 t_p$ |
| `offsets` | array of resonance offsets (**GHz**) |
| `params` | shape parameters (MHz units), see table above |
| `dt` | propagation step (ns); smaller = more accurate / slower |
| `phi0` | constant pulse phase (rad) — x/y/… |
| `init` | initial magnetization `(Mx, My, Mz)` |
| `resonator` | optional dict applying a finite-bandwidth resonator to the pulse, see [Non-ideal pulses](#resonator); `None` = ideal transmitter |

Returns `Mx, My, Mz` arrays over `offsets`. `Mz` is the inversion profile;
`hypot(Mx, My)` is the transverse excitation.

```python
import numpy as np
import atomize.math_modules.pulse_excitation as pe
import atomize.general_modules.general_functions as general

offsets = np.linspace(-0.25, 0.25, 401)               # GHz  (-250..250 MHz)
Mx, My, Mz = pe.excitation_profile(
    'WURST', tp=200, nu1=0.031, offsets=offsets,       # 31 MHz B1
    params={'n': 20, 'bw': 200, 'center': 0})
general.plot_1d('WURST inversion', offsets*1e3, Mz, xname='Offset', xscale='MHz',
                yname='Mz/M0')
general.message('inversion band reaches Mz = %.2f' % Mz.min())
```

A rectangular $\pi$ pulse for comparison (carrier shifted to +60 MHz so the band
sits there):

```python
Mx, My, Mz = pe.excitation_profile('rectangular', tp=16, nu1=1/(2*16),
                                   offsets=offsets, params={'center': 60})
```

## `waveform(shape, t, tp, params)` { #waveform }

The building block: amplitude envelope and instantaneous frequency of a shape.

Returns `(a, nu)` — `a` the normalised envelope in $[0,1]$, `nu` the instantaneous
frequency (GHz) relative to the reference (constant `center` plus, for swept
shapes, the chirp). Use it to plot the pulse or feed a custom propagation.

```python
t = np.linspace(0, 200, 400)
a, nu = pe.waveform('WURST', t, 200, {'n': 20, 'bw': 200, 'center': 0})
I, Q = a*np.cos(2*np.pi*np.cumsum(nu)*(t[1]-t[0])), a*np.sin(2*np.pi*np.cumsum(nu)*(t[1]-t[0]))
```

## `flip_angle(shape, tp, nu1, params, dt=0.5)` { #flip_angle }

On-resonance flip angle (rad) — the integral of the envelope, $2\pi\,\nu_1\!\int a\,dt$.
Exact for non-swept shapes; the nominal area for chirp/adiabatic pulses.

```python
fa = pe.flip_angle('gaussian', tp=40, nu1=0.02, params={'sigma': 10})
general.message('flip = %.1f deg' % np.degrees(fa))
```

## `adiabaticity_profile(shape, tp, nu1, offsets, params, dt=0.5, phi0=0.0, resonator=None)` { #adiabaticity_profile }

Adiabaticity factor $Q(\Delta\omega)$ of a **frequency-swept** pulse (WURST,
sech/tanh) versus resonance offset. In the frame following the instantaneous RF
frequency the effective field has transverse part $\omega_1(t)=2\pi\nu_1 a(t)$
and longitudinal part $\Delta\Omega(t)=2\pi[\Delta\omega-\nu_\text{inst}(t)]$;
adiabatic passage needs the field to reorient slowly compared with its own
magnitude,

$$ Q=\frac{|\Omega_\text{eff}|}{|\dot\alpha|},\qquad \alpha=\operatorname{atan2}(\omega_1,\Delta\Omega), $$

evaluated at each spin's resonance crossing ($\Delta\Omega=0$). $Q\gg1$ (rule of
thumb $\gtrsim5$) means the spin is cleanly inverted; at the sweep centre this is
the textbook $Q=2\pi\nu_1^2\,t_p/\Delta\nu$. Passing a `resonator` dict
([Non-ideal pulses](#resonator)) filters the waveform first, so a `compensate`d
pulse can be compared with a `simulate`d (distorted) one to see whether the AWG
pre-distortion restores adiabaticity at the band edges (it counts the
resonator's amplitude roll-off across the sweep — the dominant effect on
adiabaticity — while keeping the programmed sweep as the instantaneous
frequency, which avoids the phase-derivative spikes a filtered waveform would
otherwise produce). Returns $Q$ for every offset. **Read it only inside the
swept band** ($|\Delta\omega - \text{centre}| < \Delta\nu/2$): there $Q$ is flat
in the interior and dips toward zero at the sweep edges (where the crossing
falls on the near-zero tail of the envelope — the genuine reason adiabatic
inversion rolls off there). Outside the band a spin is never swept through, so
the returned $Q$ is large but meaningless (it does *not* imply inversion). Only
meaningful for swept shapes.

```python
offsets = np.linspace(-0.15, 0.15, 401)                 # GHz
params = {'n': 20, 'bw': 200, 'center': 0}              # 200 MHz WURST sweep
Q = pe.adiabaticity_profile('WURST', tp=400, nu1=0.03, offsets=offsets, params=params)
general.plot_1d('adiabaticity', offsets*1e3, Q, xname='Offset', xscale='MHz',
                yname='Q', yscale='')                   # log-y; Q >~ 5 inverts
```

## Building sequences

Two lower-level helpers let you chain pulses for multi-pulse experiments.
`excitation_profile` is just `propagate_pulse` on a tiled equilibrium state.

### `propagate_pulse(M, shape, tp, nu1, offsets, params, dt=0.5, phi0=0.0, resonator=None)` { #propagate_pulse }

Apply one pulse to an existing Bloch-vector array `M` of shape
`(len(offsets), 3)`; returns the new array (input not mutated). The optional
`resonator` dict ([Non-ideal pulses](#resonator)) filters the pulse through a
finite-bandwidth resonator before it acts on `M`.

### `free_evolution(M, offsets, tau)` { #free_evolution }

Free precession for `tau` ns: rotate each offset about $+z$ by
$2\pi\,\Delta\omega\,\tau$ (same sign convention as a zero-amplitude pulse).

```python
# Hahn echo: pi/2_x  --  tau  --  pi_y  --  tau, transverse magnetization vs offset
offsets = np.linspace(-0.05, 0.05, 401)
M = np.tile([0., 0., 1.], (offsets.size, 1))                       # equilibrium +z
M = pe.propagate_pulse(M, 'rectangular', 16, 1/(4*16), offsets, {'center': 0})   # pi/2 x
M = pe.free_evolution(M, offsets, 200.0)
M = pe.propagate_pulse(M, 'rectangular', 16, 1/(2*16), offsets, {'center': 0},
                       phi0=np.pi/2)                                # pi y
M = pe.free_evolution(M, offsets, 200.0)
general.plot_1d('echo profile', offsets*1e3, np.hypot(M[:, 0], M[:, 1]),
                xname='Offset', xscale='MHz', yname='|Mxy|')
```

!!! note "Carrier phase across a delay"
    Each pulse's phase is referenced to its **own** start. For a continuous-LO
    instrument where pulse $k$ at carrier $\nu_{0k}$ keeps accumulating phase
    during the delay, add the absolute-time term yourself:
    `phi0 += 2*pi*nu0_k*(t_start_k)` (in GHz·ns). This only matters when a later
    pulse sits at a **non-zero carrier** (e.g. a DEER pump).

## Non-ideal pulses: resonator transfer function { #resonator }

A real resonator has a finite bandwidth, so the spins do not see the programmed
waveform but its filtered version. Pass a `resonator` dict to
[`excitation_profile`](#excitation_profile) or [`propagate_pulse`](#propagate_pulse)
to model this with an ideal RLC transfer function

$$ H(\nu) = \frac{1}{1 + iQ\left(\dfrac{\nu}{\nu_0} - \dfrac{\nu_0}{\nu}\right)}, $$

the same form the AWG hardware correction uses (see
[`awg_correction()`](../awg.md#awg_correction)). `|H|` peaks at the resonator
centre $\nu_0$ and the power bandwidth (FWHM) is $\nu_0/Q$.

| Key | Description |
| --- | ----------- |
| `nu0` | resonator centre frequency (**GHz**, absolute) |
| `Q` | loaded quality factor (power bandwidth $=\nu_0/Q$) |
| `detuning` | resonator centre minus carrier (**GHz**); `0` = carrier on resonance |
| `mode` | `'simulate'` (multiply by $H$ — the distorted, uncorrected pulse) or `'compensate'` (multiply by $1/H$ — the pre-distorted pulse the hardware sends) |
| `ringdown` | `simulate` only: ns of post-pulse ring-down to propagate (see below); `0` = none |
| `measured` | optional `(freq_GHz, H_complex)` measured transfer function (e.g. VNA S21); replaces the ideal RLC $H$ (see [`measured_transfer`](#measured_transfer)). `nu0`/`detuning` then only set the carrier and `nu0`/`Q` the ring-down clock |

```python
offsets = np.linspace(-0.25, 0.25, 401)               # GHz
res = {'nu0': 9.7, 'Q': 88, 'detuning': 0.0, 'mode': 'simulate'}
# uncorrected WURST through the resonator
Mx, My, Mz = pe.excitation_profile('WURST', tp=200, nu1=0.031, offsets=offsets,
                                   params={'n': 20, 'bw': 200, 'center': 0},
                                   resonator=res)
# the same pulse pre-distorted (compensate) — recovers the ideal profile
res_c = dict(res, mode='compensate')
Mxc, Myc, Mzc = pe.excitation_profile('WURST', tp=200, nu1=0.031, offsets=offsets,
                                      params={'n': 20, 'bw': 200, 'center': 0},
                                      resonator=res_c)
```

The filtering is done in the frequency domain (zero-padded FFT, so a rectangular
pulse's edges ring up/down rather than wrapping around). In `compensate` mode the
$1/H$ boost is capped (far off resonance $H\to0$), mirroring the hardware clamp.

### `resonator_transfer(freqs, nu0, Q, detuning=0.0)` { #resonator_transfer }

The complex transfer function $H$ evaluated at rotating-frame frequencies `freqs`
(**GHz**). A component at `f` sits at the absolute frequency
`nu0 - detuning + f`.

### `measured_transfer(freqs, freq_meas, H_meas, carrier)` { #measured_transfer }

A drop-in replacement for [`resonator_transfer`](#resonator_transfer) that uses a
**measured** complex transfer function (e.g. a VNA $S_{21}$ sweep) instead of the
ideal RLC, so the real non-Lorentzian magnitude ripple and phase are modelled.
`freq_meas` is the absolute microwave frequency (**GHz**) of the measurement,
`H_meas` the complex transfer there, and `carrier` (**GHz**) maps a rotating-frame
component at `f` to the absolute frequency `carrier + f`. Magnitude and *unwrapped*
phase are interpolated separately and the result is normalised to **unit peak
magnitude and zero phase at the carrier** — the same convention as
`resonator_transfer` ($|H|=1$ at centre, phase referenced to the pulse start), so
only the relative across-band distortion is applied. Out-of-band frequencies clamp
to the nearest measured point. Drive it through the `resonator` dict's `measured`
key (see the table above).

### `apply_resonator(w, dt, nu0, Q, detuning=0.0, mode='simulate', max_gain=10.0, ringdown=0.0, measured=None)` { #apply_resonator }

Filter a complex baseband waveform `w` (sampled every `dt` ns) through the
resonator and return the distorted waveform. `max_gain` caps the `compensate`
boost. Pass `measured=(freq_GHz, H_complex)` to filter through a measured transfer
function instead of the ideal RLC. This is the low-level routine the `resonator`
dict drives.

### `ringdown_time(nu0, Q)` { #ringdown_time }

The resonator amplitude ring-down time constant $\tau = Q/(\pi\nu_0)$ (ns with
`nu0` in GHz); the stored field decays as $e^{-t/\tau}$. With
`mode='simulate'`, setting `ringdown` (e.g. $5\tau$) appends the post-pulse
ring-down so the spins keep nutating under the decaying field — this restores the
flip angle a finite-bandwidth resonator otherwise steals from a short hard pulse.

```python
res = {'nu0': 9.7, 'Q': 88, 'detuning': 0.0, 'mode': 'simulate',
       'ringdown': 5 * pe.ringdown_time(9.7, 88)}      # ~14 ns tail
Mx, My, Mz = pe.excitation_profile('rectangular', tp=8, nu1=1/(4*8),
                                   offsets=offsets, params={'center': 0},
                                   resonator=res)
```
