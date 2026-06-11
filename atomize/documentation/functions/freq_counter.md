# Frequency Counters

## Devices

| Device                            | Tested   | Connection                              |
| --------------------------------- | -------- | --------------------------------------- |
| **Agilent 53181A**                | 01/2021  | GPIB (linux-gpib), RS-232               |
| **Agilent 53131A / 53132A**       | 01/2021  | GPIB (linux-gpib), RS-232               |
| **Agilent 5343A**                 | 02/2023  | GPIB                                    |
| **Keysight 53230A / 53220A**      | Untested | GPIB (linux-gpib), RS-232, Ethernet     |

## Functions

### freq_counter_name() { #freq_counter_name data-toc-label="freq_counter_name" }

```python
freq_counter_name()    # -> str; device name
```

This function returns device name.

---

### freq_counter_frequency(channel) { #freq_counter_frequency data-toc-label="freq_counter_frequency" }

```python
freq_counter_frequency('CH1')    # -> str; measured frequency from channel 1
```

This function returns a value with the measured frequency from the specified channel. Refer to the device manual for the frequency range of different channels. Agilent 53181a has two channels; Agielnt 53131a, Keysight 53230a - three. Agielnt 5343a has only one channel.

**Allowed channels:** `'CH1'`, `'CH2'`, `'CH3'`
{: .enum }

**Output format:** `'number'` + `'Hz'` | `'kHz'` | `'MHz'` | `'GHz'`
{: .enum }

---

### freq_counter_impedance(*impedance) { #freq_counter_impedance data-toc-label="freq_counter_impedance" }

```python
freq_counter_impedance('CH1', '1 M')    # set channel 1 impedance to 1 MOhm
freq_counter_impedance('CH2')           # -> str; current impedance of channel 2
```

This function queries (if called with one argument) or sets (if called with two arguments) the impedance of one of the channels of the frequency counter. If there is a second argument it will be set as a new impedance. If there is no second argument the current impedance for the specified channel is returned.

For Agilent 53181a impedance can be changed only for the first channel; for Agielnt 53131a, Keysight 53230a for channel 1 and 2.

**Allowed channels:** `'CH1'`, `'CH2'`, `'CH3'`
{: .enum }

**Allowed impedances:** `'1 M'`, `'50'`
{: .enum }

!!! note
    This function is not available for Agielnt 5343a.

---

### freq_counter_coupling(*coupling) { #freq_counter_coupling data-toc-label="freq_counter_coupling" }

```python
freq_counter_coupling('CH1', 'AC')    # set channel 1 coupling to AC
freq_counter_coupling('CH2')          # -> str; current coupling of channel 2
```

This function queries (if called with one argument) or sets (if called with two arguments) the coupling of one of the channels of the frequency counter. If there is a second argument it will be set as a new coupling. If there is no second argument the current coupling for the specified channel is returned.

For Agilent 53181a coupling can be changed only for the first channel; for Agielnt 53131a, Keysight 53230a for channel 1 and 2.

**Allowed channels:** `'CH1'`, `'CH2'`, `'CH3'`
{: .enum }

**Allowed couplings:** `'AC'`, `'DC'`
{: .enum }

!!! note
    This function is not available for Agielnt 5343a.

---

### freq_counter_stop_mode(*mode) { #freq_counter_stop_mode data-toc-label="freq_counter_stop_mode" }

```python
freq_counter_stop_mode()           # -> str (query)
freq_counter_stop_mode('Timer')    # set the gate time mode
```

This function queries or sets the stop arm for frequency, frequency ratio, and period measurements.

In automatic (`'Immediate'`) mode the device does the fastest possible acquisistion, in gate time mode it measures for the specified gate time, and in digits mode the time required for a measurement depends on the number of digits requested. This setting influences the resolution of the results. Use automatic mode for fast measurements or choose a desired resolution by using [`freq_counter_gate_time()`](#freq_counter_gate_time) to set the gate time for gate time (`'Timer'`) mode or [`freq_counter_digits()`](#freq_counter_digits) for digits (`'Digits'`) mode.

**Allowed (Agilent 53181a, 53131a):** `'Immediate'`, `'External'`, `'Timer'`, `'Digits'`
{: .enum }

**Allowed (Keysight 53230a):** `'Immediate'`, `'Timer'`, `'Events'`
{: .enum }

!!! note
    This function is not available for Agielnt 5343a.

---

### freq_counter_start_mode(*mode) { #freq_counter_start_mode data-toc-label="freq_counter_start_mode" }

```python
freq_counter_start_mode()               # -> str (query)
freq_counter_start_mode('Immediate')    # set automatic mode
```

This function queries or sets the start arm for frequency, frequency ratio, and period measurements.

**Allowed:** `'Immediate'`, `'External'`
{: .enum }

!!! note
    This function is not available for Agielnt 5343a.

---

### freq_counter_gate_mode(*mode) { #freq_counter_gate_mode data-toc-label="freq_counter_gate_mode" }

```python
freq_counter_gate_mode()           # -> str (query)
freq_counter_gate_mode('Timer')    # set 'Timer' mode
```

This function queries or sets the gate source for frequency, frequency ratio measurements. `'Timer'` coresponds to starting the measurement immediately after a trigger and trigger delay; `'External'` configures the instrument to gate the measurement using the Gate In/Out BNC after a trigger and trigger delay.

**Allowed:** `'Timer'`, `'External'`
{: .enum }

!!! note
    This function is available only for Keysight 53230a.

---

### freq_counter_digits(*digits) { #freq_counter_digits data-toc-label="freq_counter_digits" }

```python
freq_counter_digits()     # -> int (query)
freq_counter_digits(5)    # set resolution to 5 digits
```

This function queries or sets the resolution in terms of digits used in arming frequency, period, and ratio measurements. To set this mode use [`freq_counter_stop_mode()`](#freq_counter_stop_mode) function. To query the number of digits call the function with no argument. A query is possible only if [`freq_counter_stop_mode('Digits')`](#freq_counter_stop_mode) was called before.

**Range (Agilent 53181a, 53131a):** `3` – `15`
{: .enum }

**Range (Agilent 5343a):** `3` – `9`
{: .enum }

!!! note
    This function is available for Agilent 53181a, 53131a, and 5343a.

---

### freq_counter_gate_time(*time) { #freq_counter_gate_time data-toc-label="freq_counter_gate_time" }

```python
freq_counter_gate_time()            # -> float (query)
freq_counter_gate_time('100 ms')    # set gate time to 100 ms
```

This function queries or sets the gate time used in arming frequency, period, and ratio measurements. To set this mode use [`freq_counter_stop_mode()`](#freq_counter_stop_mode) function. To query the gate call the function with no argument. A query is possible only if [`freq_counter_stop_mode('Timer')`](#freq_counter_stop_mode) was called before.

**Output format:** `'number'` + `'ks'` | `'s'` | `'ms'` | `'us'` | `'ns'`
{: .enum }

**Range (Agilent 53181a, 53131a):** `1 ms` – `1000 s`
{: .enum }

**Range (Keysight 53230a):** `10 ns` – `10 s`
{: .enum }

!!! note
    This function is not available for Agielnt 5343a.

---

### freq_counter_expected_freq(*frequency) { #freq_counter_expected_freq data-toc-label="freq_counter_expected_freq" }

```python
freq_counter_expected_freq('CH3', '10 GHz')    # set approximate signal frequency to 10 GHz
freq_counter_expected_freq('CH3')              # -> str; query approximate frequency
```

This function queries (if called with one argument) or sets (if called with two arguments) the approximate frequency of a signal you expect to measure. Providing this value enables the device to eliminate a pre-measurement step, saving measurement time and enabling more accurate arming. Note that the actual frequency of the input signal must be within 10% of the expected frequency value you entered. Refer to the device manual for the frequency range of different channels.

If there is a second argument it will be set as a new approximate frequency of a signal. If there is no second argument the current approximate frequency of a signal for specified the channel is returned. For Agilent 53181a the approximate frequency can be set for channels 1 and 2; for Agielnt 53131a for channels 1, 2, and 3.

**Allowed channels:** `'CH1'`, `'CH2'`, `'CH3'`
{: .enum }

**Output format:** `'number'` + `'Hz'` | `'kHz'` | `'MHz'` | `'GHz'`
{: .enum }

!!! note
    This function is available only for Agilent 53181a and 53131a.

---

### freq_counter_period(channel) { #freq_counter_period data-toc-label="freq_counter_period" }

```python
freq_counter_period('CH2')    # -> str; measured period from channel 2
```

This function returns a floating point value with the measured period from the specified channel. Refer to the device manual for the frequency range of different channels.

**Allowed channels:** `'CH1'`, `'CH2'`, `'CH3'`
{: .enum }

**Output format:** `'number'` + `'s'` | `'ms'` | `'us'` | `'ns'`
{: .enum }

!!! note
    This function is available only for Agilent 53181a and 53131a.

---

### freq_counter_command(command) { #freq_counter_command data-toc-label="freq_counter_command" }

```python
# Set which edge of the input signal will be considered an event for frequency,
# period, frequency ratio, time interval, totalize, and phase measurements.
freq_counter_command(':EVENt1:SLOPe POSitive')
```

This function sends an arbitrary command from a programming guide to the device in a string format. No output is expected.

---

### freq_counter_query(command) { #freq_counter_query data-toc-label="freq_counter_query" }

```python
# Query a measurement of the phase between channel 1 and 2.
freq_counter_query(':MEASure:PHASe? (@1),(@2)')
```

This function sends an arbitrary command from a programming guide to the device in a string format. An output in a string format is expected.
