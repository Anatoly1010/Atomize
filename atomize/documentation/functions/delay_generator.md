# Delay Generators

## Devices

| Device                          | Tested   | Connection                  |
| ------------------------------- | -------- | --------------------------- |
| **Stanford Research DG535**     | Untested | GPIB (linux-gpib; pyvisa-py) |

## Functions

### delay_generator_name() { #delay_generator_name data-toc-label="delay_generator_name" }

```python
delay_generator_name()    # -> str; device name
```

This function returns device name.

---

### delay_generator_delay(*delay) { #delay_generator_delay data-toc-label="delay_generator_delay" }

```python
delay_generator_delay('A')                   # -> str (query)
delay_generator_delay('A', 'T0', '10 us')    # delay channel A by 10 us relative to T0
```

This function queries (if called with one argument) or sets (if called with three arguments) the delay of one of the specified channel relative to another channel. If there are a second and third arguments, they will be used as a channel, relative to which the delay is set, and the delay, respectively. If there is only one argument the current delay and the reference channel are returned. At least one channel should be referenced to the `'T0'`, otherwise a corresponding warning will be printed.

**Allowed channels:** `'T0'`, `'A'`, `'B'`, `'C'`, `'D'`
{: .enum }

**Output format:** `'number'` + `'s'` | `'ms'` | `'us'` | `'ns'` | `'ps'`
{: .enum }

---

### delay_generator_impedance(*impedance) { #delay_generator_impedance data-toc-label="delay_generator_impedance" }

```python
delay_generator_impedance('A')           # -> str (query)
delay_generator_impedance('A', '1 M')    # set channel A to high impedance
```

This function queries (if called with one argument) or sets (if called with two arguments) the impedance of one of the output channels of the delay generator. If there is a second argument it will be set as a new impedance. If there is no second argument the impedance for the specified channel is returned as a string.

**Allowed channels:** `'Trigger'`, `'T0'`, `'A'`, `'B'`, `'AB'`, `'C'`, `'D'`, `'CD'`
{: .enum }

**Allowed impedances:** `'50'`, `'1 M'`
{: .enum }

---

### delay_generator_output_mode(*mode) { #delay_generator_output_mode data-toc-label="delay_generator_output_mode" }

```python
delay_generator_output_mode('C')           # -> str (query)
delay_generator_output_mode('C', 'TTL')    # set channel C mode to TTL
```

This function queries (if called with one argument) or sets (if called with two arguments) the mode of one of the output channels of the delay generator. If there is a second argument it will be set as a new mode setting. If there is no second argument the mode setting for the specified channel is returned as a string.

The available modes correspond to: `'TTL'`: 0 to 4 Vdc, `'ECL'`: -1.8 to -0.8 Vdc, `'NIM'`: -0.8 to 0 Vdc, `'Variable'`: [adjustable](#delay_generator_amplitude_offset) offset and amplitude between -3 and +4 Vdc with 4 V maximum step size.

**Allowed channels:** `'T0'`, `'A'`, `'B'`, `'AB'`, `'C'`, `'D'`, `'CD'`
{: .enum }

**Allowed modes:** `'TTL'`, `'NIM'`, `'ECL'`, `'Variable'`
{: .enum }

---

### delay_generator_amplitude_offset(*amplitude_offset) { #delay_generator_amplitude_offset data-toc-label="delay_generator_amplitude_offset" }

```python
delay_generator_amplitude_offset('A')                  # -> str (query)
delay_generator_amplitude_offset('A', '2 V', '2 V')    # amplitude and offset of A to 2 V
```

This function queries (if called with one argument) or sets (if called with three arguments) the amplitude and offset for the specified output channel of the delay generator, if this channel is operated in the `'Variable'` [mode](#delay_generator_output_mode). If there are a second and third arguments they will be set as a new amplitude and offset setting, respectively. If there is only one argument the current amplitude and offset settings for the specified output channel are returned as a string.

Offset and amplitude should between -3 and +4 Vdc with 4 V maximum step size. The function is only available when the output channel is operated in `'Variable'` [mode](#delay_generator_output_mode).

**Allowed channels:** `'T0'`, `'A'`, `'B'`, `'AB'`, `'C'`, `'D'`, `'CD'`
{: .enum }

**Output format:** `'number'` + `'V'` | `'mV'`
{: .enum }

**Range:** `-3 V` – `+4 V` (4 V maximum step size)
{: .enum }

---

### delay_generator_output_polarity(*polarity) { #delay_generator_output_polarity data-toc-label="delay_generator_output_polarity" }

```python
delay_generator_output_polarity('C')              # -> str (query)
delay_generator_output_polarity('C', 'Normal')    # set channel C polarity to Normal
```

This function queries (if called with one argument) or sets (if called with two arguments) the polarity setting of logic pulses at the BNC outputs. If there is a second argument it will be set as a new polarity setting. If there is no second argument the current polarity setting for the specified output channel is returned as a string.

Normal polarity means that the output will provide a rising edge at the specified time. The function is only available when the output channel is operated in TTL, ECL, or NIM mode, see function [`delay_generator_output_mode()`](#delay_generator_output_mode).

**Allowed channels:** `'Trigger'`, `'T0'`, `'A'`, `'B'`, `'AB'`, `'C'`, `'D'`, `'CD'`
{: .enum }

**Allowed polarities:** `'Inverted'`, `'Normal'`
{: .enum }

---

### delay_generator_trigger_source(*source) { #delay_generator_trigger_source data-toc-label="delay_generator_trigger_source" }

```python
delay_generator_trigger_source()              # -> str (query)
delay_generator_trigger_source('External')    # set external trigger mode
```

This function queries (if called without arguments) or sets (if called with one argument) the trigger mode of the delay generator. If there is an argument it will be set as a new mode setting. If there is no argument the trigger mode is returned as a string.

**Allowed:** `'Internal'`, `'External'`, `'Single'`, `'Burst'`
{: .enum }

---

### delay_generator_trigger_rate(*rate) { #delay_generator_trigger_rate data-toc-label="delay_generator_trigger_rate" }

```python
delay_generator_trigger_rate()            # -> str (query); internal or burst trigger rate
delay_generator_trigger_rate('100 Hz')    # set rate
```

This function queries or sets the trigger rate for `'Internal'` and `'Burst'` trigger [mode](#delay_generator_trigger_source) of the delay generator. If there is no argument the function will return the current trigger rate. If there is an argument the specified rate will be set.

**Output format:** `'number'` + `'MHz'` | `'kHz'` | `'Hz'` | `'mHz'`
{: .enum }

**Range:** `1 mHz` – `1 MHz`
{: .enum }

---

### delay_generator_trigger() { #delay_generator_trigger data-toc-label="delay_generator_trigger" }

```python
delay_generator_trigger()    # send a single software trigger
```

This function sends a trigger for `'Single'` trigger [mode](#delay_generator_trigger_source) and should be used only without arguments. The [trigger source](#delay_generator_trigger_source) should be set to `'Single'`.

---

### delay_generator_trigger_level(*level) { #delay_generator_trigger_level data-toc-label="delay_generator_trigger_level" }

```python
delay_generator_trigger_level()         # -> str (query)
delay_generator_trigger_level('2 V')    # set external trigger level to 2 V
```

This function queries or sets the trigger level for `'External'` trigger [mode](#delay_generator_trigger_source) of the delay generator. If there is no argument the function will return the current trigger level. If there is an argument the specified level will be set. The [trigger source](#delay_generator_trigger_source) should be set to `'External'`.

**Output format:** `'number'` + `'V'` | `'mV'`
{: .enum }

---

### delay_generator_trigger_slope(*slope) { #delay_generator_trigger_slope data-toc-label="delay_generator_trigger_slope" }

```python
delay_generator_trigger_slope()             # -> str (query)
delay_generator_trigger_slope('Falling')    # set trigger slope to falling edge
```

This function queries or sets the trigger slope of the delay generator. If there is no argument the function will return the current trigger slope as a string. If there is an argument it will be set as a new trigger slope setting.

**Allowed:** `'Falling'`, `'Rising'`
{: .enum }

---

### delay_generator_trigger_impedance(*impedance) { #delay_generator_trigger_impedance data-toc-label="delay_generator_trigger_impedance" }

```python
delay_generator_trigger_impedance()         # -> str (query)
delay_generator_trigger_impedance('1 M')    # set trigger input impedance to 1 MΩ
```

This function queries or sets the trigger input impedance of the delay generator. If there is no argument the function will return the current impedance as a string. If there is an argument it will be set as a new impedance setting.

**Allowed:** `'50'`, `'1 M'`
{: .enum }

---

### delay_generator_burst_count(*count) { #delay_generator_burst_count data-toc-label="delay_generator_burst_count" }

```python
delay_generator_burst_count()      # -> int (query)
delay_generator_burst_count(10)    # set 10 pulses per burst
```

This function queries or sets the number of pulses, which will be in each burst of pulses when the delay generator is in the `'Burst'` [mode](#delay_generator_trigger_source). If there is no argument the function will return the current number of pulses in burst. If there is an argument it will be set as a new number of pulses.

**Range:** `2` – `32766`
{: .enum }

---

### delay_generator_burst_period(*period) { #delay_generator_burst_period data-toc-label="delay_generator_burst_period" }

```python
delay_generator_burst_count(10)
delay_generator_burst_period(15)    # 10 pulses/burst, skip 5 triggers between bursts
```

This function queries or sets the number of triggers between the start of each burst of pulses when the delay generator is in the `'Burst'` [mode](#delay_generator_trigger_source). If there is no argument the function will return the current number of triggers between the start of each burst of pulses. If there is an argument it will be set as a new setting. The burst period should be at least one larger than the [burst count](#delay_generator_burst_count).

**Range:** `4` – `32766`
{: .enum }

---

### delay_generator_command(command) { #delay_generator_command data-toc-label="delay_generator_command" }

```python
delay_generator_command('DL 1,0,0')    # opens the Delay Menu on the generator screen
```

This function sends an arbitrary command from a programming guide to the device in a string format. No output is expected.

---

### delay_generator_query(command) { #delay_generator_query data-toc-label="delay_generator_query" }

```python
delay_generator_query('TL')    # -> str; current external trigger level in Volts
```

This function sends an arbitrary command from a programming guide to the device in a string format. An output in a string format is expected.
