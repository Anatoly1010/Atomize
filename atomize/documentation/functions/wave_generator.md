# Waveform Generators

## Devices

| Device                                                     | Tested  | Connection                            |
| ---------------------------------------------------------- | ------- | ------------------------------------- |
| **Waveform Generator of Keysight InfiniiVision 2000 X-Series** | — | Via corresponding oscilloscope module |
| **Waveform Generator of Keysight InfiniiVision 3000 X-Series** | — | Via corresponding oscilloscope module |
| **Waveform Generator of Keysight InfiniiVision 4000 X-Series** | — | Via corresponding oscilloscope module |
| **Waveform Generator of Rigol MSO8000 Series**             | —       | Via corresponding oscilloscope module |
| **Stanford Research DS345**                                | 01/2026 | RS-232; GPIB (linux-gpib; pyvisa-py)  |

The availability of a waveform generator should be specified in the configuration file located in the [DEVICE CONFIG DIRECTORY](../usage.md):

```yml
wave_gen = False
wave_gen = True
```

## Functions

### wave_gen_name() { #wave_gen_name data-toc-label="wave_gen_name" }

```python
wave_gen_name()    # -> str; device name
```

The function returns device name.

---

### wave_gen_frequency(*frequency) { #wave_gen_frequency data-toc-label="wave_gen_frequency" }

```python
wave_gen_frequency()                          # -> str (query)
wave_gen_frequency('20 kHz')                  # set generator frequency to 20 kHz
wave_gen_frequency('20 kHz', channel='2')     # set channel 2 frequency to 20 kHz
```

This function queries or sets the frequency of the waveform of the waveform generator. If there is no argument the function will return the current frequency. If there is an argument the specified frequency will be set. If the oscilloscope or waveform generator has several waveform generator, the number of the generator used should be specified by corresponding keyword argument `'channel': ['1', '2']`. Keysight 4000 X-series and Rigol MSO8000 Series can have up to two waveform generators. If there is only one waveform generator channel keyword argument is absent. The function works for all waveforms except Noise and DC.

Please, refer to the device manual for available frequency range, since it depends on the function type.

**Output format:** `'number'` + `'MHz'` | `'kHz'` | `'Hz'` | `'mHz'`
{: .enum }

---

### wave_gen_pulse_width(*width) { #wave_gen_pulse_width data-toc-label="wave_gen_pulse_width" }

```python
wave_gen_pulse_width()           # -> str (query)
wave_gen_pulse_width('20 ms')    # set pulse width to 20 ms
```

This function queries or sets the width of the pulse of the waveform generator. If there is no argument the function will return the current width. If there is an argument the specified width will be set. If the oscilloscope or waveform generator has several waveform generator, the number of the generator used should be specified by corresponding keyword argument `'channel': ['1', '2']`. Keysight 4000 X-series and Rigol MSO8000 Series can have up to two waveform generators. If there is only one waveform generator channel keyword argument is absent. The pulse width can be adjusted from 20 ns to the period minus 20 ns. The function available only for pulse waveforms. This function works only for the [pulsed function](#wave_gen_function).

!!! note
    For Rigol MSO8000 Series this function sets or queries the duty cycle of the pulse output from the specified waveform generator channel. Duty cycle is defined as the percentage that the high level takes up in the whole pulse period: `(width: int, channel = ['1', '2'])`. The available range is from `10` to `90`.

    This function is not available for Stanford Research DS345.

**Output format:** `'number'` + `'s'` | `'ms'` | `'us'` | `'ns'`
{: .enum }

---

### wave_gen_function(*function) { #wave_gen_function data-toc-label="wave_gen_function" }

```python
wave_gen_function()        # -> str (query)
wave_gen_function('Sq')    # set square waveform
```

This function queries or sets the type of waveform of the waveform generator. If the oscilloscope or waveform generator has several waveform generator, the number of the generator used should be specified by corresponding keyword argument `'channel': ['1', '2']`. Keysight 4000 X-series and Rigol MSO8000 Series can have up to two waveform generators. If there is only one waveform generator channel keyword argument is absent.

**Allowed (Keysight 2000, 3000, 4000 X-series):** `'Sin'`, `'Sq'`, `'Ramp'`, `'Pulse'`, `'DC'`, `'Noise'`, `'Sinc'`, `'ERise'`, `'EFall'`, `'Card'`, `'Gauss'`, `'Arb'`
{: .enum }

**Allowed (Rigol MSO8000 Series):** `'Sin'`, `'Sq'`, `'Ramp'`, `'Pulse'`, `'DC'`, `'Noise'`, `'Sinc'`, `'ERise'`, `'EFall'`, `'ECG'`, `'Gauss'`, `'Lorentz'`, `'Haversine'`
{: .enum }

**Allowed (Stanford Research DS345):** `'Sin'`, `'Sq'`, `'Triangle'`, `'Ramp'`, `'Noise'`, `'Arb'`
{: .enum }

---

### wave_gen_amplitude(*amplitude) { #wave_gen_amplitude data-toc-label="wave_gen_amplitude" }

```python
wave_gen_amplitude()                            # -> str (query)
wave_gen_amplitude('200 mV', channel='1')       # set channel 1 amplitude to 200 mV
```

This function queries or sets the waveform peak-to-peak amplitude. If there is no argument the function will return the current amplitude. If there is an argument the specified amplitude will be set. If the oscilloscope or waveform generator has several waveform generator, the number of the generator used should be specified by corresponding keyword argument `'channel': ['1', '2']`. Keysight 4000 X-series and Rigol MSO8000 Series can have up to two waveform generators. If there is only one waveform generator channel keyword argument is absent.

Please, refer to the device manual for available amplitude range, since it depends on the impedance. Usually the range is from 20 mVpp to 2.5 Vpp (`'50'`) or to 5 Vpp (`'1 M'`).

!!! note
    For Stanford Research DS345 the available range is from 0 Vpp to 5 Vpp. There are also two special presets `['TTL', 'ECL']` for setting peak-to-peak amplitude and offset to 5 V, 2.5 V and 1 V, -1.3 V, respectively for `'TTL'` and `'ECL'`.

**Output format:** `'number'` + `'V'` | `'mV'`
{: .enum }

---

### wave_gen_offset(*offset) { #wave_gen_offset data-toc-label="wave_gen_offset" }

```python
wave_gen_offset()           # -> str (query)
wave_gen_offset('0.5 V')    # set offset voltage to 500 mV
```

This function queries or sets the waveform offset voltage or the DC level. If there is no argument the function will return the current offset voltage. If there is an argument the specified offset will be set. If the oscilloscope or waveform generator has several waveform generator, the number of the generator used should be specified by corresponding keyword argument `'channel': ['1', '2']`. Keysight 4000 X-series and Rigol MSO8000 Series can have up to two waveform generators. If there is only one waveform generator channel keyword argument is absent.

!!! note
    For Stanford Research DS345 the available range of amplitude and offset sum is from 0 Vpp to 5 Vpp.

**Output format:** `'number'` + `'V'` | `'mV'`
{: .enum }

---

### wave_gen_impedance(*impedance) { #wave_gen_impedance data-toc-label="wave_gen_impedance" }

```python
wave_gen_impedance()        # -> str (query)
wave_gen_impedance('50')    # set output load impedance to 50 Ohm
```

This function queries or sets the output load impedance of the waveform generator. If there is no argument the function will return the current impedance. If there is an argument the specified impedance will be set. If the oscilloscope or waveform generator has several waveform generator, the number of the generator used should be specified by corresponding keyword argument `'channel': ['1', '2']`. Keysight 4000 X-series and Rigol MSO8000 Series can have up to two waveform generators. If there is only one waveform generator channel keyword argument is absent.

!!! note
    This function is not available for Stanford Research DS345.

**Allowed:** `'1 M'`, `'50'`
{: .enum }

---

### wave_gen_start() { #wave_gen_start data-toc-label="wave_gen_start" }

```python
wave_gen_start()    # run the waveform generator
```

This function runs the waveform generator. This is the same as pressing the Wave Gen key on the front panel. If the oscilloscope or waveform generator has several waveform generator, the number of the generator used should be specified by corresponding keyword argument `'channel': ['1', '2']`. Keysight 4000 X-series and Rigol MSO8000 Series can have up to two waveform generators. If there is only one waveform generator channel keyword argument is absent.

!!! note
    This function is not available for Stanford Research DS345.

---

### wave_gen_stop() { #wave_gen_stop data-toc-label="wave_gen_stop" }

```python
wave_gen_stop()    # stop the waveform generator
```

This function stops the waveform generator. This is the same as pressing the Wave Gen key on the front panel. If the oscilloscope or waveform generator has several waveform generator, the number of the generator used should be specified by corresponding keyword argument `'channel': ['1', '2']`. Keysight 4000 X-series and Rigol MSO8000 Series can have up to two waveform generators. If there is only one waveform generator channel keyword argument is absent.

!!! note
    This function is not available for Stanford Research DS345.

---

### wave_gen_phase(*phase) { #wave_gen_phase data-toc-label="wave_gen_phase" }

```python
wave_gen_phase()      # -> str (query)
wave_gen_phase(50)    # set start phase to 50 degrees
```

This function queries or sets the start phase of the signal in degrees. If there is no argument the function will return the current start phase. If there is an argument the specified start phase will be set. If the oscilloscope or waveform generator has several waveform generator, the number of the generator used should be specified by corresponding keyword argument `'channel': ['1', '2']`. Keysight 4000 X-series and Rigol MSO8000 Series can have up to two waveform generators. If there is only one waveform generator channel keyword argument is absent. The function does not work for Noise, DC, and Arbitrary waveform. In the case of Keysight 4000 X-series oscilloscopes this function also switches on `'TRACK'` option. The `'TRACK'` option causes frequency, amplitude, offset, and duty cycle adjustments to this waveform generator output signal to be tracked by the other waveform generator output. Please note, that not all waveform shapes can be frequency tracked.

!!! note
    This function is available only for Keysight 4000 X-series, Rigol MSO8000 Series oscilloscopes, and Stanford Research DS345.

**Range (Rigol MSO8000 Series):** `0 deg` – `360 deg`
{: .enum }

**Range (Keysight 4000 X-series):** `-360 deg` – `360 deg`
{: .enum }

**Range (Stanford Research DS345):** `0 deg` – `7199.999 deg`
{: .enum }

---

### wave_gen_modulation_function(*function) { #wave_gen_modulation_function data-toc-label="wave_gen_modulation_function" }

```python
wave_gen_modulation_function()        # -> str (query)
wave_gen_modulation_function('Sq')    # set square modulation waveform
```

This function queries or sets the modulation waveform. If there is no argument the function will return the current modulation waveform as a string. The value `'None'` will be returned for modulation types that do not have an associated waveform, such as burst [mode](#wave_gen_modulation_type). If there is an argument the specified waveform will be set.

!!! note
    The value `'Arb'` may only be set for amplitude, frequency, and phase modulation [type](#wave_gen_modulation_type).

    This function is only available for Stanford Research DS345, Keysight 3000 X-Series.

**Allowed (Stanford Research DS345):** `'Single'`, `'Ramp'`, `'Triangle'`, `'Sin'`, `'Sq'`, `'Arb'`, `'None'`
{: .enum }

**Allowed (Keysight 3000 X-Series):** `'Sin'`, `'Sq'`, `'Ramp'`
{: .enum }

---

### wave_gen_modulation_type(*type) { #wave_gen_modulation_type data-toc-label="wave_gen_modulation_type" }

```python
wave_gen_modulation_type()               # -> str (query)
wave_gen_modulation_type('Lin Sweep')    # set linear sweep modulation type
```

This function queries or sets the modulation type. If there is no argument the function will return the current modulation type as a string. If there is an argument the specified modulation type will be set.

!!! note
    This function is only available for Stanford Research DS345, Keysight 3000 X-Series.

**Allowed (Stanford Research DS345):** `'Lin Sweep'`, `'Log Sweep'`, `'AM'`, `'FM'`, `'PM'`, `'Burst'`
{: .enum }

**Allowed (Keysight 3000 X-Series):** `'AM'`, `'FM'`, `'Freq-Shift'`
{: .enum }

---

### wave_gen_modulation_depth(*depth) { #wave_gen_modulation_depth data-toc-label="wave_gen_modulation_depth" }

```python
wave_gen_modulation_depth()      # -> str (query)
wave_gen_modulation_depth(50)    # set AM depth to 50 percent
```

This function queries or sets the amplitude modulation (AM) depth in percent. If there is no argument the function will return the current modulation depth as a string. If there is an argument the specified modulation depth will be set.

!!! note
    In the case of Stanford Research DS345 if the argument is negative the modulation is set to double sideband suppressed carrier modulation (DSBSC) with the indicated modulation percent.

    This function is only available for Stanford Research DS345, Keysight 3000 X-Series.

**Output format:** `'number'` + `'%'`
{: .enum }

---

### wave_gen_modulation_frequency_span(*span) { #wave_gen_modulation_frequency_span data-toc-label="wave_gen_modulation_frequency_span" }

```python
wave_gen_modulation_frequency_span()             # -> str (query)
wave_gen_modulation_frequency_span('50 kHz')     # set FM span to 50 kHz
```

This function queries or sets the frequency modulation (FM) span in Hz. If there is no argument the function will return the current span as a string. If there is an argument the specified frequency span will be set. The FM waveform will be centered at the frequency specified by the [`wave_gen_frequency()`](#wave_gen_frequency) function and have a deviation of ±span/2. The maximum value of span is limited so that the frequency is never less than or equal to zero or greater than that allowed for the selected function. Otherwise the corresponding error message will be printed.

!!! note
    This function is only available for Stanford Research DS345, Keysight 3000 X-Series.

**Output format:** `'number'` + `'MHz'` | `'kHz'` | `'Hz'` | `'mHz'` | `'uHz'`
{: .enum }

---

### wave_gen_modulation_phase_span(*span) { #wave_gen_modulation_phase_span data-toc-label="wave_gen_modulation_phase_span" }

```python
wave_gen_modulation_phase_span()      # -> str (query)
wave_gen_modulation_phase_span(10)    # set PM span to 10 deg
```

This function queries or sets the span of the phase modulation (PM) in degrees. If there is no argument the function will return the current phase span as a string. If there is an argument the specified phase span will be set. The phase shift ranges from -span/2 to span/2.

!!! note
    This function is only available for Stanford Research DS345.

**Range:** `0 deg` – `7199.999 deg`
{: .enum }

---

### wave_gen_modulation_status(*status) { #wave_gen_modulation_status data-toc-label="wave_gen_modulation_status" }

```python
wave_gen_modulation_status()        # -> str (query)
wave_gen_modulation_status('On')    # enable modulation
```

This function queries or sets the modulation status. If there is no argument the function will return the current status as a string. If there is an argument the specified status will be set.

!!! note
    For Keysight 3000 X-Series modulation is not available for `['Pulse', 'DC', 'Noise']` function [type](#wave_gen_function).

    For Stanford Research DS345 modulation is not available for `['Noise']` function [type](#wave_gen_function).

    This function is only available for Stanford Research DS345, Keysight 3000 X-Series.

**Allowed:** `'On'`, `'Off'`
{: .enum }

---

### wave_gen_modulation_frequency_sweep(**kargs) { #wave_gen_modulation_frequency_sweep data-toc-label="wave_gen_modulation_frequency_sweep" }

```python
wave_gen_modulation_frequency_sweep()                                 # -> str (query)
wave_gen_modulation_frequency_sweep(start='10 kHz', stop='40 kHz')    # set sweep 10–40 kHz
```

This function queries or sets the sweep start and stop frequencies in Hz for [sweep modulation](#wave_gen_modulation_type) types. If there is no argument the function will return the current start and stop frequencies as a string in the format `"START FREQ: {start}; STOP FREQ: {stop}"`. If there are two keyword arguments `start` and `stop` the specified frequencies will be set. The maximum and minimum values are limited so that the frequency is never less than or equal to zero or greater than that allowed for the selected function. Otherwise the corresponding error message will be printed. If the stop frequency is less than the start frequency a downward sweep from maximum to minimum frequency will be generated.

!!! note
    This function is only available for Stanford Research DS345.

**Output format:** `'number'` + `'MHz'` | `'kHz'` | `'Hz'` | `'mHz'` | `'uHz'`
{: .enum }

---

### wave_gen_modulation_rate(*rate) { #wave_gen_modulation_rate data-toc-label="wave_gen_modulation_rate" }

```python
wave_gen_modulation_rate()           # -> str (query)
wave_gen_modulation_rate('5 mHz')    # set modulation rate to 5 mHz
```

This function queries or sets the modulation rate in Hz. If there is no argument the function will return the current modulation rate. If there is an argument the specified rate will be set.

!!! note
    For Keysight 3000 X-Series this function queries or sets the frequency of the modulating signal.

    This function is only available for Stanford Research DS345, Keysight 3000 X-Series.

**Output format:** `'number'` + `'MHz'` | `'kHz'` | `'Hz'` | `'mHz'`
{: .enum }

**Range (Stanford Research DS345):** `1 mHz` – `10 kHz`
{: .enum }

---

### wave_gen_modulation_trigger_source(*tr_type) { #wave_gen_modulation_trigger_source data-toc-label="wave_gen_modulation_trigger_source" }

```python
wave_gen_modulation_trigger_source()              # -> str (query)
wave_gen_modulation_trigger_source('Internal')    # set 'Internal' trigger source
```

This function queries or sets the trigger source for [bursts and sweeps](#wave_gen_modulation_type). If there is no argument the function will return the current trigger source as a string. If there is an argument the specified source will be set. For single sweeps and bursts the [`wave_gen_modulation_trigger()`](#wave_gen_modulation_trigger) function triggers the sweep.

!!! note
    This function is only available for Stanford Research DS345.

**Allowed:** `'Single'`, `'Internal'`, `'External Pos'`, `'External Neg'`, `'Line'`
{: .enum }

---

### wave_gen_modulation_trigger_rate(*rate) { #wave_gen_modulation_trigger_rate data-toc-label="wave_gen_modulation_trigger_rate" }

```python
wave_gen_modulation_trigger_rate()    # -> str (query)
```

This function queries or sets the trigger rate for internally triggered [single sweeps and bursts](#wave_gen_modulation_type) in Hz. If there is no argument the function will return the current trigger rate. If there is an argument the specified rate will be set.

!!! note
    This function is only available for Stanford Research DS345.

**Output format:** `'number'` + `'kHz'` | `'Hz'` | `'mHz'`
{: .enum }

**Range:** `1 mHz` – `10 kHz`
{: .enum }

---

### wave_gen_modulation_trigger() { #wave_gen_modulation_trigger data-toc-label="wave_gen_modulation_trigger" }

```python
wave_gen_modulation_trigger()    # trigger a burst or single sweep
```

This function triggers a burst or single sweep and should be used only without arguments. The [trigger source](#wave_gen_modulation_trigger_source) should be set to `'Single'`.

!!! note
    This function is only available for Stanford Research DS345.

---

### wave_gen_modulation_burst_count(*count) { #wave_gen_modulation_burst_count data-toc-label="wave_gen_modulation_burst_count" }

```python
wave_gen_modulation_burst_count()      # -> int (query)
wave_gen_modulation_burst_count(15)    # set burst count to 15
```

This function queries or sets the burst count. If there is no argument the function will return the current burst count as an integer. If there is an argument the specified count will be set. The maximum value is also limited such that the burst time does not exceed 500 s. Otherwise the corresponding error message will be printed.

!!! note
    This function is only available for Stanford Research DS345.

**Range:** `1` – `30000`
{: .enum }

---

### wave_gen_modulation_hop_frequency(*frequency) { #wave_gen_modulation_hop_frequency data-toc-label="wave_gen_modulation_hop_frequency" }

```python
wave_gen_modulation_hop_frequency()           # -> str (query)
wave_gen_modulation_hop_frequency('1 kHz')    # set hop frequency to 1 kHz
```

This function queries or sets the hop frequency for [`'Freq-Shift'`](#wave_gen_modulation_type) modulation type in Hz. In this modulation type the output frequency "shifts" between the original carrier frequency and this "hop frequency" with the specified in the function [`wave_gen_modulation_hop_rate()`](#wave_gen_modulation_hop_rate) rate. If there is no argument the function will return the current hop frequency. If there is an argument the specified frequency will be set.

!!! note
    This function is only available for Keysight 3000 X-Series.

**Output format:** `'number'` + `'MHz'` | `'kHz'` | `'Hz'` | `'mHz'`
{: .enum }

---

### wave_gen_modulation_hop_rate(*rate) { #wave_gen_modulation_hop_rate data-toc-label="wave_gen_modulation_hop_rate" }

```python
wave_gen_modulation_hop_rate()    # -> str (query)
```

This function queries or sets the hop rate for [`'Freq-Shift'`](#wave_gen_modulation_type) modulation type in Hz. In this modulation type the output frequency "shifts" between the original carrier frequency and ["hop frequency"](#wave_gen_modulation_hop_frequency) with the specified rate. If there is no argument the function will return the current hop rate. If there is an argument the specified rate will be set.

!!! note
    This function is only available for Keysight 3000 X-Series.

**Output format:** `'number'` + `'MHz'` | `'kHz'` | `'Hz'` | `'mHz'`
{: .enum }

---

### wave_gen_arbitrary_amplitude_modulation(p_list) { #wave_gen_arbitrary_amplitude_modulation data-toc-label="wave_gen_arbitrary_amplitude_modulation" }

```python
# set the specified arbitrary amplitude modulation pattern
wave_gen_arbitrary_amplitude_modulation([0, 0.5, 1, 0.5, 0, -0.5, -1, -0.5, 0])
```

This function downloads an arbitrary amplitude modulation pattern. The values have to be between -1.0 to +1.0. The values -1.0 and +1.0 represent the full amplitude. Negative values are used for DSBSC. The time required to execute each modulation point is controlled by the [`wave_gen_arbitrary_modulation_rate_divider()`](#wave_gen_arbitrary_modulation_rate_divider) function. The typical procedure is as follows:

- download the arbitrary waveform using the [`wave_gen_arbitrary_amplitude_modulation()`](#wave_gen_arbitrary_amplitude_modulation) function
- set the `'Arb'` modulation function by the [`wave_gen_modulation_function()`](#wave_gen_modulation_function) function
- enable modulation using the [`wave_gen_modulation_status()`](#wave_gen_modulation_status) function

!!! note
    This function is only available for Stanford Research DS345.

---

### wave_gen_arbitrary_frequency_modulation(p_list) { #wave_gen_arbitrary_frequency_modulation data-toc-label="wave_gen_arbitrary_frequency_modulation" }

```python
# set the specified frequency modulation pattern
wave_gen_arbitrary_frequency_modulation([0, 0.1, 0.5, 0.9, 1, 0.9, 0.5, 0.1, 0])
```

This function downloads an arbitrary frequency modulation pattern. The values have to be between 0 to +1.0. The value 0 represents zero frequency, +1.0 is the maximum available frequency of 40 MHz. The time required to execute each modulation point is controlled by the [`wave_gen_arbitrary_modulation_rate_divider()`](#wave_gen_arbitrary_modulation_rate_divider) function. The typical procedure is as follows:

- download the arbitrary waveform using the [`wave_gen_arbitrary_frequency_modulation()`](#wave_gen_arbitrary_frequency_modulation) function
- set the `'Arb'` modulation function by the [`wave_gen_modulation_function()`](#wave_gen_modulation_function) function
- enable modulation using the [`wave_gen_modulation_status()`](#wave_gen_modulation_status) function

!!! note
    This function is only available for Stanford Research DS345.

---

### wave_gen_arbitrary_phase_modulation(p_list) { #wave_gen_arbitrary_phase_modulation data-toc-label="wave_gen_arbitrary_phase_modulation" }

```python
# set the specified phase modulation pattern
wave_gen_arbitrary_phase_modulation([0, 0.5, 1, 0.5, 0, -0.5, -1, -0.5, 0])
```

This function downloads an arbitrary phase modulation pattern. The values have to be between -1.0 to +1.0. The values -1.0 and +1.0 represent -180 and +180 degrees, respectively. The time required to execute each modulation point is controlled by the [`wave_gen_arbitrary_modulation_rate_divider()`](#wave_gen_arbitrary_modulation_rate_divider) function. The typical procedure is as follows:

- download the arbitrary waveform using the [`wave_gen_arbitrary_phase_modulation()`](#wave_gen_arbitrary_phase_modulation) function
- set the `'Arb'` modulation function by the [`wave_gen_modulation_function()`](#wave_gen_modulation_function) function
- enable modulation using the [`wave_gen_modulation_status()`](#wave_gen_modulation_status) function

!!! note
    This function is only available for Stanford Research DS345.

---

### wave_gen_arbitrary_modulation_rate_divider(*rate) { #wave_gen_arbitrary_modulation_rate_divider data-toc-label="wave_gen_arbitrary_modulation_rate_divider" }

```python
wave_gen_arbitrary_modulation_rate_divider()     # -> int (query)
wave_gen_arbitrary_modulation_rate_divider(2)    # set modulation rate divider to 2
```

This function queries or sets the arbitrary modulation rate divider. If there is no argument the function will return the current rate divider as an integer. If there is an argument the specified rate divider will be set. This controls the rate at which arbitrary modulations are generated. Arbitrary [AM](#wave_gen_arbitrary_amplitude_modulation) takes 0.3 us per point, arbitrary [FM](#wave_gen_arbitrary_frequency_modulation) takes 2 us per point, and arbitrary [PM](#wave_gen_arbitrary_phase_modulation) takes 0.5 us per point. When modulation is enabled each modulation point takes `{rate}*[0.3 us, 2 us, 0.5 us]` to execute.

!!! note
    This function is only available for Stanford Research DS345.

**Range:** `1` – `2^23 − 1`
{: .enum }

---

### wave_gen_arbitrary_function_data(p_list) { #wave_gen_arbitrary_function_data data-toc-label="wave_gen_arbitrary_function_data" }

```python
# set the specified arbitrary waveform
wave_gen_arbitrary_function_data([0, 0.5, 1, 0.5, 0, -0.5, -1, -0.5, 0])
```

This function downloads an arbitrary waveform. The values have to be between -1.0 to +1.0. The value -1.0 represents the minimum value, +1.0 is the maximum value, and 0.0 is equal to [the offset](#wave_gen_offset). The minimum and maximum values are determined by the [amplitude](#wave_gen_amplitude).

The setting of an arbitrary function for Keysight 2000 X-series and Keysight 3000 X-series can be done as follow:

- [`wave_gen_frequency()`](#wave_gen_frequency) gives the repetition rate of an arbitrary function
- All available time interval (depends on the used repetition rate) is splitted by amount of points you indicate as an argument. It gives time per point. For instance, suppose the frequency is 10 Hz and we use 10 points: `wave_gen_arbitrary_function_data([-1, -1, -1, 1, 1, 1, 1, -1, -1, -1])`. It means the time step for one point will be (100 ms) / (10 points) = 10 ms
- If you have the offset equals to 2 V and the amplitude 4 V as a result of `wave_gen_arbitrary_function_data([-1, -1, -1, 1, 1, 1, 1, -1, -1, -1])` for 10 Hz frequency one will have a pulse 40 ms long with the low level equals to 0 V and the high level equals to 4 V

In the case of Stanford Research DS345 the [`wave_gen_arbitrary_frequency()`](#wave_gen_arbitrary_frequency) function determines the rate at which each arbitrary waveform point is output. Each point in the waveform is played for a time equal to 1/{frequency}.

If the oscilloscope or waveform generator has several waveform generator, the number of the generator used should be specified by corresponding keyword argument `'channel': ['1', '2']`. Keysight 4000 X-series can have up to two waveform generators. If there is only one waveform generator channel keyword argument is absent.

!!! note
    This function is not available for Keysight 2000 X-series, Rigol MSO8000 Series oscilloscopes.

---

### wave_gen_arbitrary_frequency(*frequency) { #wave_gen_arbitrary_frequency data-toc-label="wave_gen_arbitrary_frequency" }

```python
wave_gen_arbitrary_frequency()             # -> str (query)
wave_gen_arbitrary_frequency('20 kHz')     # set sampling frequency to 20 kHz
```

This function queries or sets the arbitrary waveform sampling frequency. If there is no argument the function will return the current sampling frequency. If there is an argument the specified sampling frequency will be set. This frequency determines the rate at which each arbitrary waveform [point](#wave_gen_arbitrary_function_data) is output. Each point in the waveform is played for a time equal to 1/{frequency}.

!!! note
    This function is only available for Stanford Research DS345.

**Output format:** `'number'` + `'MHz'` | `'kHz'` | `'Hz'` | `'mHz'`
{: .enum }

**Range:** `10 mHz` – `40 MHz`
{: .enum }

---

### wave_gen_arbitrary_clear() { #wave_gen_arbitrary_clear data-toc-label="wave_gen_arbitrary_clear" }

```python
wave_gen_arbitrary_clear()    # clear arbitrary waveform memory and load default
```

This function clears the arbitrary waveform memory and loads it with the default waveform. If the oscilloscope or waveform generator has several waveform generator, the number of the generator used should be specified by corresponding keyword argument `'channel': ['1', '2']`. Keysight 4000 X-series can have up to two waveform generators. If there is only one waveform generator channel keyword argument is absent.

!!! note
    This function is not available for Keysight 2000 X-series, Rigol MSO8000 Series oscilloscopes, and Stanford Research DS345.

---

### wave_gen_arbitrary_interpolation(*mode) { #wave_gen_arbitrary_interpolation data-toc-label="wave_gen_arbitrary_interpolation" }

```python
wave_gen_arbitrary_interpolation()        # -> str (query)
wave_gen_arbitrary_interpolation('On')    # turn on interpolation control
```

This function enables or disables the interpolation control. If there is no argument the function will return the current interpolation setting. If there is an argument the specified interpolation setting will be set. If the oscilloscope or waveform generator has several waveform generator, the number of the generator used should be specified by corresponding keyword argument `'channel': ['1', '2']`. Keysight 4000 X-series can have up to two waveform generators. If there is only one waveform generator channel keyword argument is absent.

Interpolation specifies how lines are drawn between arbitrary waveform points:

- When `'On'`, lines are drawn between points in the arbitrary waveform. Voltage levels change linearly between one point and the next.
- When `'Off'`, all line segments in the arbitrary waveform are horizontal. The voltage level of one point remains until the next point.

!!! note
    This function is not available for Keysight 2000 X-series, Rigol MSO8000 Series oscilloscopes, and Stanford Research DS345.

**Allowed:** `'On'`, `'Off'`
{: .enum }

---

### wave_gen_arbitrary_number_of_points() { #wave_gen_arbitrary_number_of_points data-toc-label="wave_gen_arbitrary_number_of_points" }

```python
wave_gen_arbitrary_number_of_points()    # -> int; number of points in current arbitrary waveform
```

This function returns the number of points used by the current arbitrary waveform. If the oscilloscope or waveform generator has several waveform generator, the number of the generator used should be specified by corresponding keyword argument `'channel': ['1', '2']`. Keysight 4000 X-series can have up to two waveform generators. If there is only one waveform generator channel keyword argument is absent.

!!! note
    This function is not available for Keysight 2000 X-series and Rigol MSO8000 Series oscilloscopes.

---

### wave_gen_command(command) { #wave_gen_command data-toc-label="wave_gen_command" }

```python
wave_gen_command(command)    # str -> none
```

This function sends an arbitrary command from a programming guide to the device in a string format. No output is expected.

---

### wave_gen_query(command) { #wave_gen_query data-toc-label="wave_gen_query" }

```python
wave_gen_query(command)    # str -> str
```

This function sends an arbitrary command from a programming guide to the device in a string format. An output in a string format is expected.
