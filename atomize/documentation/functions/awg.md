# Arbitrary Waveform Generators

## Devices

| Device                   | Tested   | Connection |
| ------------------------ | -------- | ---------- |
| **Spectrum M4I 6631 X8** | 07/2021  | PCIe       |
| **Insys FM214x3GDA**     | 03/2025  | PCIe       |

The original [library](https://spectrum-instrumentation.com/en/m4i6631-x8) for Spectrum M4I 6631 X8 was written by Spectrum. The path to the library header files (`pyspcm.py`, `spcm_tools.py`) and the card device node are read from the device configuration file (the `[SPECIFIC]` section, keys `header_dir` and `device`), so they can be set per machine without editing the module:

```ini
[SPECIFIC]
header_dir = /path/to/python/header/of/Spectrum/library
device = /dev/spcm0
```

The [Insys FM214x3GDA](https://www.insys.ru/mezzanine/fm214x3gda) device is available via `ctypes`. The original library can be found [here](https://github.com/Anatoly1010/Atomize_ITC/tree/master/libs).

## Functions

### awg_name() { #awg_name data-toc-label="awg_name" }

```python
awg_name()    # -> str; device name
```

This function returns device name.

---

### awg_setup() { #awg_setup data-toc-label="awg_setup" }

```python
awg_setup()    # write all settings into the AWG card
```

This function writes all the settings modified by other functions to the AWG card. The function should be called only without arguments. One needs to initialize the settings before calling [`awg_update()`](#awg_update). The default settings (if no other function was called) are the following: Sample clock is 1250 MHz; Clock mode is `'Internal'`; Reference clock is 100 MHz; Card mode is `'Single'`; Trigger channel is `'External'`; Trigger mode is `'Positive'`; Loop is infinity; Trigger delay is 0; Enabled channels are CH0 and CH1; Amplitude of CH0 is `'600 mV'`; Amplitude of CH1 is `'533 mV'`; Number of segments is 1; Card memory size is 64 samples; Buffer is empty.

!!! note
    This function is not available for Insys FM214x3GDA. This is done by [`pulser_open()`](pulse_programmer.md#pulser_open) function.

---

### awg_update() { #awg_update data-toc-label="awg_update" }

```python
awg_update()    # run the AWG card
```

This function redefines the buffer (in case the function like [`awg_shift()`](#awg_shift) has been called) and runs the AWG card. The function should be called only without arguments.

!!! note
    This function is not available for Insys FM214x3GDA. This is done by [`pulser_update()`](pulse_programmer.md#pulser_update) function.

---

### awg_stop() { #awg_stop data-toc-label="awg_stop" }

```python
awg_stop()    # stop the AWG card
```

This function stops the AWG card and should be called only without arguments. If an infinite number of loops is defined by the [`awg_loop()`](#awg_loop) function, the [`awg_stop()`](#awg_stop) should always be called before redefining the buffer by the [`awg_update()`](#awg_update). If a finite number of loops is defined, the card will stop automatically.

!!! note
    This function is not available for Insys FM214x3GDA. There is no need to stop this DAC.

---

### awg_close() { #awg_close data-toc-label="awg_close" }

```python
awg_close()    # close the AWG driver
```

This function closes the AWG driver and should be called only without arguments. The function should always be called at the end of an experimental script, since the AWG card driver is opened during whole experiment in order to achieve high rate of buffer updating. It is STRONGLY recommended to add a graceful closing of the card to the experimental scripts for the case of an abrupt termination of the process. As a possible option, one can use signal library:

```python
import signal
import atomize.device_modules.Spectrum_M4I_6631_X8 as spectrum

awg = spectrum.Spectrum_M4I_6631_X8()

def cleanup():
    awg.awg_stop()
    awg.awg_close()
    sys.exit(0)

signal.singal(signal.SIGTERM, cleanup)

# AWG setup and experimental script
#
#
```

!!! note
    This function is not available for Insys FM214x3GDA. This is done with [`pulser_close()`](pulse_programmer.md#pulser_close).

---

### awg_pulse(**kargs) { #awg_pulse data-toc-label="awg_pulse" }

```python
# 40 ns 200 MHz sine pulse with pi/2 phase
awg_pulse(name='P0', channel='CH0', func='SINE',
          frequency='200 MHz', phase=pi/2, length='40 ns')
```

This function sets a pulse with specified parameters for `'Single'`, `'Multi'`, and `'Single Joined'` card mode. The AWG card buffer will be filled according to key arguments of the `awg_pulse()` function.

| Keyword            | Default     | Description |
| ------------------ | ----------- | ----------- |
| `name`             | `'P0'`      | Pulse name |
| `channel`          | `'CH0'`     | Channel string |
| `func`             | `'SINE'`    | Function type |
| `frequency`        | `'200 MHz'` | Frequency of the pulse |
| `phase`            | `0`         | Phase of the pulse (in radians) |
| `phase_list`       | `[]`        | Phase cycling sequence |
| `delta_phase`      | `0`         | Phase increment of the pulse (in radians) for `'Single'` and `'Multi'` card mode |
| `length`           | `'16 ns'`   | Pulse length |
| `sigma`            | `'0 ns'`    | Sigma value for GAUSS pulses |
| `length_increment` | `'0 ns'`    | Pulse length and sigma increment |
| `start`            | `'0 ns'`    | Pulse start for the `'Single Joined'` card mode |
| `delta_start`      | `'0 ns'`    | Pulse delta start for the `'Single Joined'` card mode |
| `amplitude`        | `100`       | Additional coefficient for adjusting pulse amplitudes |
| `n`                | `1`         | Special coefficient for WURST and SECH/TANH pulses determining the steepness of the amplitude function |
| `b`                | `0.02`      | Parameter for SECH/TANH pulse determining the truncation parameter in 1/ns |

A channel should be one of the following `['CH0', 'CH1']`. The frequency should be in MHz, the minimum value is 0 MHz, maximum is 280 MHz. For WURST and SECH/TANH pulse the frequency argument should be a tuple `('center_freq MHz', 'sweep_range MHz')`, i.e. `('0 MHz', '100 MHz')`. The scaling factor for length and sigma key arguments should be one of the following `['ns','us','ms']`. The minimum available length and sigma of the pulse is 0 ns. The maximum available length and sigma of the pulse is 1900 ns. For `'SINE'`, `'BLANK'`, `'WURST'`, and `'SECH/TANH'` function parameter sigma has no meaning. For `'GAUSS'` function parameter sigma is a sigma of Gaussian. For `'SINC'` function a combination of parameters length and sigma specifies the width of the SINC pulse, i.e. `length = '40 ns'` and `sigma = '10 ns'` means that SINC pulse will be from -4pi to +4pi. Function `'BLANK'` is an empty pulse. Function `'WURST'` is a wideband, uniform rate, smooth truncation pulse. Function `'SECH/TANH'` is a wideband sech/tanh pulse. The `length_increment` keyword affects both the length and sigma of the pulse. The scaling factor for `start` and `delta_start` key arguments should be one of the following `['ns','us','ms']`. The [amplitudes](#awg_amplitude) of the AWG card channels will be set according to the value of the `amplitude` keyword argument. The amplitude keyword argument should be less than or equal to 100% and should indicate the amplitude as a percentage of the maximum available level. The `n` parameter determines the steepness of the amplitude function of the WURST and SECH/TANH pulses. For other functions it has no meaning. The `b` parameter (in 1/ns) determines the truncation parameter of the SECH/TANH pulse. For other functions it has no meaning.

It is recommended to first define all pulses and then define the settings of the AWG card. To write the settings [`awg_setup()`](#awg_setup) function should be called. To run specified pulses the [`awg_update()`](#awg_update) function should be called.

Key argument `delta_phase` defines a pulse phase shift and has no meaning for `'Single Joined'` card mode, since the phase of the pulse will be calculated automatically. Key arguments `start` and `delta_start` define a pulse position for `'Single Joined'` card mode and has no meaning for `'Single'` or `'Multi'` card mode.

!!! note
    Pulse settings for Insys FM214x3GDA correspond to `'Single'` card mode. In addition for this device arguments `'start'`, `'length'`, `'delta_start'`, and `'length_increment'` will be rounded to a multiple of 3.2 and for all AWG pulses there should be a corresponding trigger pulse, generated by [`pulser_pulse()`](pulse_programmer.md#pulser_pulse) function.

**Allowed channels:** `'CH0'`, `'CH1'`
{: .enum }

**Allowed functions:** `'SINE'`, `'GAUSS'`, `'SINC'`, `'BLANK'`, `'WURST'`, `'SECH/TANH'`
{: .enum }

**Allowed phase_list values:** `'+x'`, `'-x'`, `'+y'`, `'-y'`
{: .enum }

**Range frequency:** `0 MHz` – `280 MHz`
{: .enum }

**Range length / sigma:** `0 ns` – `1900 ns`
{: .enum }

---

### awg_pulse_sequence(**kargs) { #awg_pulse_sequence data-toc-label="awg_pulse_sequence" }

```python
# pulse train of three pulses with 10 kHz repetition rate
# and a third pulse shifting by 40 ns at each of 800 points
awg_pulse_sequence(pulse_type=['SINE', 'GAUSS', 'SINE'],
                   pulse_start=[0, 160, 320], pulse_delta_start=[0, 0, 40],
                   pulse_length=[40, 120, 40], pulse_phase=['+x', '+x', '+x'],
                   pulse_sigma=[40, 20, 40], pulse_frequency=[50, 200, 40],
                   n=[20, 20, 20], b=[0.02, 0.02, 0.02],
                   number_of_points=800, loop=10, rep_rate=10000)
```

This function sets a pulse sequence with specified parameters for `'Sequence'` card [mode](#awg_card_mode). The AWG card buffer will be filled according to key arguments of the `awg_pulse_sequence()` function. There is no default arguments, that is why all keywords must be specified.

| Keyword             | Description |
| ------------------- | ----------- |
| `pulse_type`        | List of function types per pulse |
| `pulse_start`       | List of pulse starts in ns |
| `pulse_delta_start` | List of pulse delta starts in ns |
| `pulse_length`      | List of pulse lengths in ns |
| `pulse_phase`       | List of pulse phases |
| `pulse_sigma`       | List of pulse sigmas in ns |
| `pulse_frequency`   | List of pulse frequencies in MHz |
| `number_of_points`  | Total number of points in a pulse sequence, taking into account shifting of the pulses |
| `loop`              | Number of repetitions of each point |
| `rep_rate`          | Repetition rate of the pulse sequence in Hz |
| `n`                 | List of `n` parameters in arb. u. |
| `b`                 | List of `b` parameters in 1/ns |

The minimum available length and sigma of the pulse is 0 ns. The maximum available length and sigma of the pulse is 1900 ns. For WURST and SECH/TANH pulses the frequency should be a tuple `('Center_freq MHz', 'sweep_freq MHz')`, i.e. `('0 MHz', '100 MHz')`. For `'SINE'`, `'BLANK'`, `'WURST'`, and `'SECH/TANH'` functions parameter sigma has no meaning. For `'GAUSS'` function parameter sigma is a sigma of Gaussian. For `'SINC'` function a combination of parameters length and sigma specifies the width of the SINC pulse in the same manner as the function [`awg_pulse()`](#awg_pulse). Function `'BLANK'` is an empty pulse. Function `'WURST'` is a wideband, uniform rate, smooth truncation pulse. Function `'SECH/TANH'` is a wideband sech/tanh pulse. The `n` parameter determines the steepness of the amplitude function of the WURST and SECH/TANH pulse. For other functions it has no meaning. The `b` parameter (in 1/ns) determines the truncation parameter of the SECH/TANH pulse. For other functions it has no meaning.

Please note, that each new call of the [`awg_pulse_sequence()`](#awg_pulse_sequence) function will redefine the pulse sequence. `pulse_start` array must be sorted. A number of enabled channels should be defined before [`awg_pulse_sequence()`](#awg_pulse_sequence).

To write the settings [`awg_setup()`](#awg_setup) function should be called. To run a specified pulse sequence the [`awg_update()`](#awg_update) function should be called. After going through all the buffer the AWG card will be stopped.

!!! note
    This function is not available for Insys FM214x3GDA.

**Allowed pulse_type values:** `'SINE'`, `'GAUSS'`, `'SINC'`, `'BLANK'`, `'WURST'`, `'SECH/TANH'`
{: .enum }

**Allowed pulse_phase values:** `'+x'`, `'-x'`, `'+y'`, `'-y'`
{: .enum }

---

### awg_shift(*pulses) { #awg_shift data-toc-label="awg_shift" }

```python
awg_shift()              # shift phase of all active pulses by their delta_phase
awg_shift('P0', 'P1')    # shift only specified pulses
```

This function can be called with either no argument or with a list of comma separated pulse names (i.e. `'P0'`, `'P1'`). In the `'Single'` or `'Multi'` card mode, if no argument is given the phase of all pulses that have a nonzero `delta_phase` and are currently active (do not have a length of 0) are shifted by their corresponding `delta_phase` value. If there is one argument or a list of comma separated pulse names only the phase of the listed pulses are changed.

In the `'Single Joined'` card mode, the `start` values of the specified pulses are shifted by the defined `delta_start` values. Phases of the pulses are not changed, since they are calculated from the pulse positions automatically.

For the `'Sequence'` card mode, the function has no meaning. Calling this function also resets the phase (if specified in the argument `phase_list` of the [`awg_pulse()`](#awg_pulse)) to the first phase in the `phase_list`.

---

### awg_increment(*pulses) { #awg_increment data-toc-label="awg_increment" }

```python
awg_increment()        # increment length & sigma of all active pulses by their increment
awg_increment('P0')    # increment only the pulse named 'P0'
```

This function can be called with either no argument or with a list of comma separated pulse names (i.e. `'P0'`, `'P1'`). In the `'Single'`, `'Multi'` or `'Single Joined'` card mode, if no argument is given the lengths and sigmas of all pulses that have a nonzero increment and are currently active (do not have a length of 0) are incremented by their corresponding increment value. If there is one argument or a list of comma separated pulse names only the lengths and sigmas of the listed pulses are changed.

Please, note that the function always keeps the ratio length/sigma for GAUSS and SINC pulses. For instance, if `length = '64 ns'`, `sigma = '16 ns'`, and `increment = '10 ns'` after calling `awg_increment()` once, the parameters will be `length = '104 ns'`, `sigma = '26 ns'`, and `increment = '10 ns'`.

For the `'Sequence'` card mode, the function has no meaning. Calling this function also resets the phase (if specified in the argument `phase_list` of the [`awg_pulse()`](#awg_pulse)) to the first phase in the `phase_list`.

---

### awg_next_phase() { #awg_next_phase data-toc-label="awg_next_phase" }

```python
awg_next_phase()    # switch all declared pulses to the next phase
```

This function switches all pulses to the next phase. The phase sequence is declared in the [`awg_pulse()`](#awg_pulse) in the form of `phase_list = ['-y', '+x', '-x', '+x', ...]`. Argument `'+x'` means that the phase of the pulse will be equal to `phase` declared in the [`awg_pulse()`](#awg_pulse). Argument `'-x'` corresponds to the phase shifted by pi radians in comparison with the `phase` declared in the [`awg_pulse()`](#awg_pulse). Argument `'+y'` corresponds to pi/2 radians shift. Argument `'-y'` – 3pi/2 radians. By repeatedly calling the function one can run through the complete list of phases for the pulses. The length of all phase lists specified for different pulses has to be the same. This function also immediately updates the AWG card buffer, as it is done by calling [`awg_update()`](#awg_update). The first call of the function corresponds to the first phase in the `phase_list` argument of the [`awg_pulse()`](#awg_pulse).

---

### awg_redefine_delta_phase(*, name, delta_phase) { #awg_redefine_delta_phase data-toc-label="awg_redefine_delta_phase" }

```python
# change delta_phase setting of the 'P0' pulse to pi radians
awg_redefine_delta_phase(name='P0', delta_phase=pi)
```

This function should be called with two keyword arguments, namely `name` and `delta_phase`. The first argument specifies the name of the pulse as a string. The second argument defines a new value of `delta_phase` in radians. Arguments can be either single strings or lists, for example: `name = ['P0', 'P1']`, `delta_phase = [0, np.pi]`. The main purpose of the function is non-uniform sampling. Please note, that the function does not update the AWG card. The [`awg_update()`](#awg_update) function should be called to apply changes. The function has no meaning for the `'Single Joined'` and `'Sequence'` card mode, since phases of the pulses are calculated from the pulse positions automatically.

---

### awg_redefine_phase(*, name, phase) { #awg_redefine_phase data-toc-label="awg_redefine_phase" }

```python
# change phase setting of the 'P0' pulse to pi radians
awg_redefine_phase(name='P0', phase=pi)
```

This function should be called with two keyword arguments, namely `name` and `phase`. The first argument specifies the name of the pulse as a string. The second argument defines a new value of phase in radians. Arguments can be either single strings or lists, for example: `name = ['P0', 'P1']`, `phase = [0, np.pi]`. The main purpose of the function is phase cycling. Please note, that the function does not update the AWG card. The [`awg_update()`](#awg_update) function should be called to apply changes. The function has no meaning for the `'Sequence'` card mode. One should redefine all the sequence instead.

---

### awg_redefine_amplitude(*, name, amplitude) { #awg_redefine_amplitude data-toc-label="awg_redefine_amplitude" }

```python
# change amplitude setting of the 'P0' pulse to 50%
awg_redefine_amplitude(name='P0', amplitude=50)
```

This function should be called with two keyword arguments, namely `name` and `amplitude`. The first argument specifies the name of the pulse as a string. The second argument defines a new value of the `amplitude` keyword argument of the [`awg_pulse()`](#awg_pulse) as a percentage of the maximum available level. The amplitude should be in the range of 0–100%. Arguments can be either single strings or lists, for example: `name = ['P0', 'P1']`, `amplitude = [50, 100]`. Please note, that the function does not update the AWG card. The [`awg_update()`](#awg_update) function should be called to apply changes. The function has no meaning for the `'Sequence'` card mode. One should redefine all the sequence instead.

---

### awg_redefine_frequency(*, name, freq) { #awg_redefine_frequency data-toc-label="awg_redefine_frequency" }

```python
# change frequency setting of the 'P0' pulse to '10 MHz'
awg_redefine_frequency(name='P0', freq='10 MHz')
```

This function should be called with two keyword arguments, namely `name` and `frequency`. The first argument specifies the name of the pulse as a string. The second argument defines a new value of frequency as a string, i.e. `'100 MHz'` or a list of string `('0 MHz', '100' MHz)` for WURST and SECH/TANH pulses, see [`awg_pulse()`](#awg_pulse) for more details. Arguments can be either single strings or lists, for example: `name = ['P0', 'P1']`, `freq = ['10 MHz', ('0 MHz', '50 MHz')]`. Please note, that the function does not update the AWG card. The [`awg_update()`](#awg_update) function should be called to apply changes. The function has no meaning for the `'Sequence'` card mode. One should redefine all the sequence instead.

---

### awg_redefine_delta_start(*, name, delta_start) { #awg_redefine_delta_start data-toc-label="awg_redefine_delta_start" }

```python
# change delta_start setting of the 'P0' pulse to 10 ns
awg_redefine_delta_start(name='P0', delta_start='10 ns')
```

This function should be called with two keyword arguments, namely `name` and `delta_start`. The first argument specifies the name of the pulse as a string. The second argument defines a new value of `delta_start` as a string. Arguments can be either single strings or lists, for example: `name = ['P0', 'P1']`, `delta_start = ['0 ns', '32 ns']`. The main purpose of the function is non-uniform sampling. Please note, that the function does not update the AWG card. The [`awg_update()`](#awg_update) function should be called to apply changes. The function has no meaning for the `'Single'`, `'Multi'`, and `'Sequence'` card mode, since in these modes the start of the pulse is determined by the trigger event.

**Output format:** `'number'` + `'ns'` | `'us'` | `'ms'`
{: .enum }

---

### awg_redefine_length_increment(*, name, length_increment) { #awg_redefine_length_increment data-toc-label="awg_redefine_length_increment" }

```python
# change length increment setting of the 'P2' pulse to 10 ns
awg_redefine_length_increment(name='P2', length_increment='10 ns')
```

This function should be called with two keyword arguments, namely `name` and `length_increment`. The first argument specifies the name of the pulse as a string. The second argument defines a new value of length increment as a string. Arguments can be either single strings or lists, for example: `name = ['P0', 'P1']`, `length_increment = ['0 ns', '32 ns']`. The main purpose of the function is non-uniform sampling. Please note, that the function does not update the AWG card. The [`awg_update()`](#awg_update) function should be called to apply changes. The function has no meaning for the `'Sequence'` card mode. One should redefine all the sequence instead.

**Output format:** `'number'` + `'ns'` | `'us'` | `'ms'`
{: .enum }

---

### awg_add_phase(*, name, add_phase) { #awg_add_phase data-toc-label="awg_add_phase" }

```python
# add pi radians to the 'P0' pulse
awg_add_phase(name='P0', add_phase=pi)
```

This function should be called with two keyword arguments, namely `name` and `add_phase`. The first argument specifies the name of the pulse as a string. The second argument defines a value of phase in radians to add. Arguments can be either single strings or lists, for example: `name = ['P0', 'P1']`, `add_phase = [0, np.pi]`. The main purpose of the function is phase cycling. Please note, that the function does not update the AWG card. The [`awg_update()`](#awg_update) function should be called to apply changes. The function has no meaning for the `'Sequence'` card mode. One should redefine all the sequence instead.

---

### awg_reset() { #awg_reset data-toc-label="awg_reset" }

```python
awg_reset()    # reset all pulses to initial state and update the AWG card
```

This function switches the AWG card back to the initial state in which it was in at the start of the experiment. This function can be called only without arguments. It includes the complete functionality of [`awg_pulse_reset()`](#awg_pulse_reset), but also immediately updates the AWG card as it is done by calling [`awg_update()`](#awg_update). The function has no meaning for the `'Sequence'` card mode. One should redefine all the sequence instead.

!!! note
    This function is not available for Insys FM214x3GDA. The function [`awg_pulse_reset()`](#awg_pulse_reset) can be used instead.

---

### awg_pulse_reset(*pulses) { #awg_pulse_reset data-toc-label="awg_pulse_reset" }

```python
awg_pulse_reset()        # reset all pulses to their initial state
awg_pulse_reset('P1')    # reset only the pulse named 'P1'
```

This function switches the AWG card back to the initial state in which it was in at the start of the experiment. This function can be called with either no argument or with a list of comma separated pulse names. If no argument is given all pulses are reset to their initial states (including phases). If there is one argument or a list of comma separated pulse names only the listed pulses are returned back to the initial state. The function does not update the AWG card, if you want to reset all pulses and and also update the AWG card use the function [`awg_reset()`](#awg_reset) instead. The function has no meaning for the `'Sequence'` card mode. One should redefine all the sequence instead.

---

### awg_number_of_segments(*segments) { #awg_number_of_segments data-toc-label="awg_number_of_segments" }

```python
awg_number_of_segments()     # -> int (query)
awg_number_of_segments(2)    # set number of segments to 2
```

This function queries or sets the number of segments for [`'Multi'`](#awg_card_mode) card mode. In order to set the number of segments higher than 1, the AWG card should be in [`'Multi'`](#awg_card_mode) mode. If there is no argument the function will return the current number of segments. If there is an argument the specified number of segments will be set. Default value is 1.

!!! note
    This function is not available for Insys FM214x3GDA.

**Range:** `1` – `200`
{: .enum }

---

### awg_channel(*channel) { #awg_channel data-toc-label="awg_channel" }

```python
awg_channel()                 # -> str (query)
awg_channel('CH0', 'CH1')     # enable output from CH0 and CH1
```

This function enables output from the specified channel or queries enabled channels. If there is no argument the function will return the currently enabled channels. If there is an argument the output from the specified channel will be enabled. Default option is when both channels are enabled.

!!! note
    This function is not available for Insys FM214x3GDA, only two channels are available.

**Allowed:** `'CH0'`, `'CH1'`
{: .enum }

---

### awg_sample_rate(*s_rate) { #awg_sample_rate data-toc-label="awg_sample_rate" }

```python
awg_sample_rate()        # -> int (query)
awg_sample_rate(1250)    # set sample rate to 1250 MHz
```

This function queries or sets the AWG card sample rate (in MHz). If there is no argument the function will return the current sample rate. If there is an argument the specified sample rate will be set. Default value is 1250 MHz. Please note that sample rate affects the delay between a trigger event and the AWG card output. The delay is determined in samples and can be found in the documentation.

!!! note
    This function is not available for Insys FM214x3GDA, the default sample rate is 1250 MHz.

**Range:** `50 MHz` – `1250 MHz`
{: .enum }

---

### awg_clock_mode(*mode) { #awg_clock_mode data-toc-label="awg_clock_mode" }

```python
awg_clock_mode()              # -> str (query)
awg_clock_mode('Internal')    # set internal clock mode
```

This function queries or sets the AWG card clock mode. If there is no argument the function will return the current clock mode setting. If there is an argument the specified clock mode will be set. According to the documentation, the internal sampling clock is generated in default mode by a programmable high precision quartz. The external clock input of the M3i/M4i series is fed through a PLL to the clock system. Therefore the input will act as a reference clock input thus allowing to either use a copy of the external clock or to generate any sampling clock within the allowed range from the reference clock. Due to the fact that the driver needs to know the external fed in frequency for an exact calculation of the sampling rate the reference clock should be set by the [`awg_reference_clock()`](#awg_reference_clock) function. Default setting is `'Internal'`.

!!! note
    This function is not available for Insys FM214x3GDA.

**Allowed:** `'Internal'`, `'External'`
{: .enum }

---

### awg_reference_clock(*ref_clock) { #awg_reference_clock data-toc-label="awg_reference_clock" }

```python
awg_reference_clock()       # -> int (query)
awg_reference_clock(100)    # set reference clock to 100 MHz
```

This function queries or sets the AWG card reference clock in MHz for `'External'` mode of the [`awg_clock_mode()`](#awg_clock_mode) function. If there is no argument the function will return the current reference clock. If there is an argument the specified reference clock will be set. Default value is 100 MHz.

!!! note
    This function is not available for Insys FM214x3GDA.

**Range:** `10 MHz` – `1000 MHz`
{: .enum }

---

### awg_card_mode(*mode) { #awg_card_mode data-toc-label="awg_card_mode" }

```python
awg_card_mode()           # -> str (query)
awg_card_mode('Multi')    # set 'Multi' card mode
```

This function queries or sets the AWG card mode. If there is no argument the function will return the current card mode setting. If there is an argument the specified card mode will be set. According to the documentation, in the `'Single'` mode a data from on-board memory will be replayed on every detected trigger event. The number of replays can be programmed by [loops](#awg_loop). `'Single Joined'` mode is a modification of the `'Single'` mode with a possibility of defining more than one pulse. In this mode, all defined pulses are combined into a sequence of pulses according to their start position, determined by `start` keyword of the [`awg_pulse()`](#awg_pulse) function. Please note, that if two channels are enabled the pulse sequence for the second channel will be generated automatically using a phase shifting specified in the config file. In the `'Multi'` mode every detected trigger event replays one data block (segment). Segmented memory is available only in `'External'` trigger [mode](#awg_trigger_mode). In the `'Sequence'` mode it is possible to define a whole pulse sequence by the [`awg_pulse_sequence()`](#awg_pulse_sequence) function. The pulse sequence has a specified number of points that is looped specified times. Switching between points is achieved using a trigger event. Please note, that if two channels are enabled the pulse sequence for the second channel will be generated automatically using a phase shifting specified in the config file. Default setting is `'Single'`.

!!! note
    This function is not available for Insys FM214x3GDA, it operates in the mode close to `'Single'`.

**Allowed:** `'Single'`, `'Multi'`, `'Single Joined'`, `'Sequence'`
{: .enum }

---

### awg_trigger_channel(*channel) { #awg_trigger_channel data-toc-label="awg_trigger_channel" }

```python
awg_trigger_channel()              # -> str (query)
awg_trigger_channel('Software')    # set 'Software' trigger
```

This function queries or sets the AWG card trigger channel. If there is no argument the function will return the current trigger channel. If there is an argument the specified channel will be used as trigger. Trigger channel `'External'` corresponds to `'Trg0'` channel of the AWG card. Default setting is `'External'`.

!!! note
    This function is not available for Insys FM214x3GDA.

**Allowed:** `'Software'`, `'External'`
{: .enum }

---

### awg_trigger_mode(*mode) { #awg_trigger_mode data-toc-label="awg_trigger_mode" }

```python
awg_trigger_mode()              # -> str (query)
awg_trigger_mode('Positive')    # trigger detection for positive edges
```

This function queries or sets the AWG card trigger mode. If there is no argument the function will return the current trigger mode. If there is an argument the specified trigger mode will be set. Mode `'Positive'` corresponds to trigger detection for positive edges (crossing level 0 from below to above). `'Negative'` to trigger detection for negative edges (crossing level 0 from above to below). `'High'` to trigger detection for HIGH levels (signal above level 0). `'Low'` to trigger detection for LOW levels (signal below level 0). Default setting is `'Positive'`.

!!! note
    This function is not available for Insys FM214x3GDA.

**Allowed:** `'Positive'`, `'Negative'`, `'High'`, `'Low'`
{: .enum }

---

### awg_loop(*loop) { #awg_loop data-toc-label="awg_loop" }

```python
awg_loop()     # -> int (query)
awg_loop(0)    # set infinite number of loops
```

This function queries or sets the number of loops for [`'Multi'`](#awg_card_mode) or [`'Single'`](#awg_card_mode) card mode. If there is no argument the function will return the current number of loops. If there is an argument the specified number of loops will be set. A setting `0` means an infinite number of loops. Default value is `0`.

!!! note
    This function is not available for Insys FM214x3GDA.

**Range:** `0` – `100000` (0 = infinite)
{: .enum }

---

### awg_trigger_delay(*delay) { #awg_trigger_delay data-toc-label="awg_trigger_delay" }

```python
awg_trigger_delay()             # -> str (query)
awg_trigger_delay('51.2 ns')    # set trigger delay to 51.2 ns
```

This function queries or sets the AWG card trigger delay. If there is no argument the function will return the current trigger delay. If there is an argument the specified trigger delay will be set. The delay step is 32 sample clock. If an input is not divisible by 32 sample clock the delay will be rounded and a warning message will be printed. Default value is `'0 ns'`.

!!! note
    This function is not available for Insys FM214x3GDA.

**Output format:** `'number'` + `'ns'` | `'us'` | `'ms'`
{: .enum }

---

### awg_amplitude(*amplitude) { #awg_amplitude data-toc-label="awg_amplitude" }

```python
awg_amplitude('CH0')                          # -> str (query for channel)
awg_amplitude('CH0', '600', 'CH1', '600')     # set CH0 to 600 mV and CH1 to 600 mV
```

This function queries or sets the amplitude of the specified channels in mV. If there is only channel argument the function will return the amplitude of the specified channel. If there are two or four arguments the specified amplitude in mV will be set for specified channel.

**Allowed channels:** `'CH0'`, `'CH1'`
{: .enum }

**Range (Spectrum M4I 6631 X8):** `80 mV` – `2500 mV`
{: .enum }

**Range (Insys FM214x3GDA):** `80 mV` – `260 mV`
{: .enum }

---

### awg_visualize() { #awg_visualize data-toc-label="awg_visualize" }

```python
awg_visualize()    # visualize the AWG card buffer (2D plot)
```

This function visualizes the AWG card buffer and can be called only without arguments. For the `'Single'`, `'Multi'`, and `'Single Joined'` card mode, the complete buffer will be shown. For the `'Sequence'` card mode only first two points will be shown. It is not recommended to use this function for very low repetition rate (less than 10 kHz) of [`awg_pulse_sequence()`](#awg_pulse_sequence) in the `'Sequence'` card mode.

---

### awg_pulse_list() { #awg_pulse_list data-toc-label="awg_pulse_list" }

```python
awg_pulse_list()    # -> list of str; pulse sequence
```

This function can be called only without arguments and it returns the declared pulse sequence as an array.

---

### awg_clear() { #awg_clear data-toc-label="awg_clear" }

```python
awg_clear()
```

This is a special function for clearing pulse array `{self.pulse_array}` and other status flags of the device module. The function is usually used in GUI applications that use the device module.

---

### awg_clear_pulses() { #awg_clear_pulses data-toc-label="awg_clear_pulses" }

```python
awg_clear_pulses()
```

This is a special function for clearing pulse array `{self.pulse_array}` and other status flags of the device module when the card is opened. The function is usually used in GUI applications that use the device module.

---

### awg_correction(**kargs) { #awg_correction data-toc-label="awg_correction" }

```python
# measured resonator profile, applied only to the high-amplitude (pi) pulses
awg_correction(only_pi_half = 'True', coef_array = [bl, a1, x1, w1, a2, x2, w2, a3, x3, w3], \
               low_level = 16, limit = 23)

# ideal RLC resonator, amplitude + phase, applied to every swept pulse
awg_correction(only_pi_half = 'False', model = 'ideal', f0 = 9700, q_factor = 88, \
               phase_correction = 'True', low_level = 16, limit = 23)
```

This function (Insys FM214x3GDA and Spectrum M4I 6631 X8) enables resonator-profile predistortion of the frequency-swept pulses (`'WURST'` and `'SECH/TANH'`, see [`awg_pulse()`](#awg_pulse)) so that the effective excitation B<sub>1</sub> is equalized across the swept band. Each sample of a swept pulse is mapped to its instantaneous chirp frequency (flipped high-frequency-first for an `LO − RF` bridge) and its amplitude — and optionally phase — is corrected accordingly. The correction has no effect on non-swept pulses.

There are two correction models:

- **`model = 'measured'`** (default) — the amplitude is corrected with the measured resonator magnitude profile, given as a triple-Lorentzian fit in `coef_array = [bl, a1, x1, w1, a2, x2, w2, a3, x3, w3]` (the same coefficients written to `correction.param` by the resonator-tuning tool). No phase correction is applied (the magnitude fit carries no phase information).
- **`model = 'ideal'`** — the amplitude (`1/|H|`) and, when `phase_correction = 'True'`, the phase are corrected with an ideal RLC resonator transfer function `H = 1 / (1 + i Q (ν/f0 − f0/ν))`, where `f0` is the resonator centre frequency in MHz and `q_factor` the loaded Q. The phase term is `+angle(H)`, the sign for an `LO − RF` (lower-sideband) bridge; verify it once on the bench for your setup.

The minimum effective B<sub>1</sub> is clamped by the ratio `low_level / limit` (both in MHz), which also caps the amplitude boost applied to the band edges. `only_pi_half = 'True'` restricts the correction to the high-amplitude (pi) pulses (those with `amplitude` coefficient `> 1` in [`awg_pulse()`](#awg_pulse)); `only_pi_half = 'False'` applies it to every swept pulse.

!!! note
    The amplitude clamp equalizes the band only when the sweep is centred on the resonator (i.e. the microwave sweep is symmetric about `f0`). A sweep that sits entirely off resonance is clamped to a flat correction.

**Allowed model:** `'measured'`, `'ideal'`
{: .enum }

**Default (Insys FM214x3GDA, Spectrum M4I 6631 X8):** `f0 = 9700 MHz`, `q_factor = 88`, `low_level = 16`, `limit = 23`
{: .enum }

---

### awg_correction_off() { #awg_correction_off data-toc-label="awg_correction_off" }

```python
awg_correction_off()    # disable resonator-profile correction
```

This function disables the resonator-profile correction set by [`awg_correction()`](#awg_correction); subsequent swept pulses are sent as programmed. The function is usually used in GUI applications that use the device module.

---

### awg_test_flag(flag) { #awg_test_flag data-toc-label="awg_test_flag" }

```python
awg_test_flag('test')    # change test mode
```

This is a special function for changing test mode. The function is usually used in GUI applications that use the device module.

**Allowed:** `'None'`, `'test'`
{: .enum }
