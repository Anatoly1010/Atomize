# Vector Network Analyzers

## Devices

| Device                            | Tested  | Connection |
| --------------------------------- | ------- | ---------- |
| **Planar C2220**, **S50024**      | 09/2025 | Socket     |

Planar instruments only work when running [native sofware](https://planarchel.ru/catalog/analizatory_tsepey_vektornye/vektornye_analizatory_tsepey_kobalt/analizator-tsepey-vektornyy-c2220/). In addition, the socket server must be enabled in the web server settings of the software.

## Functions

### vector_analyzer_name() { #vector_analyzer_name data-toc-label="vector_analyzer_name" }

```python
vector_analyzer_name()    # -> str; device name
```

This function returns device name.

---

### vector_analyzer_source_power(*pwr, source = 1) { #vector_analyzer_source_power data-toc-label="vector_analyzer_source_power" }

```python
vector_analyzer_source_power(source=1)             # -> float (query)
vector_analyzer_source_power('0 dBm', source=1)    # set source 1 to 0 dBm
```

This function queries or sets the power of the specified source. If there is no argument, the function returns the current power for the source specified as the keyword "source". The output of the function is a float number in dBm. If there is an argument, the specified power will be set for the indicated source. The available range is specified directly in the device configuration file. The number of available sources is also given in the configuration file.

**Output format:** `'number'` + `'dBm'`
{: .enum }

**Range:** `-60 dBm` – `20 dBm`
{: .enum }

---

### vector_analyzer_center_frequency(*freq, channel = 1) { #vector_analyzer_center_frequency data-toc-label="vector_analyzer_center_frequency" }

```python
vector_analyzer_center_frequency(channel=1)    # -> str (query)
vector_analyzer_center_frequency('9 GHz')      # set center frequency to 9 GHz
```

This function queries or sets the center frequency for measurement. If there is no argument, the function returns the current center frequency for the channel specified as the keyword "channel". If there is an argument, the specified center frequency will be set for the indicated channel. The available range is specified directly in the device configuration file. The number of available channels is also given in the configuration file.

**Output format:** `'number'` + `'Hz'` | `'kHz'` | `'MHz'` | `'GHz'`
{: .enum }

**Range:** `0.1 MHz` – `20 GHz`
{: .enum }

---

### vector_analyzer_frequency_range(*freq, channel = 1) { #vector_analyzer_frequency_range data-toc-label="vector_analyzer_frequency_range" }

```python
vector_analyzer_frequency_range(channel=1)    # -> str (query)
vector_analyzer_frequency_range('10 MHz')     # set frequency range to 10 MHz
```

This function queries or sets the frequency range for measurement. If there is no argument, the function returns the current frequency range for the channel specified as the keyword "channel". If there is an argument, the specified frequency range will be set for the indicated channel. The number of available channels is given in the configuration file.

**Output format:** `'number'` + `'Hz'` | `'kHz'` | `'MHz'` | `'GHz'`
{: .enum }

**Range:** `0 MHz` – `20 GHz`
{: .enum }

---

### vector_analyzer_points(*pnt, channel = 1) { #vector_analyzer_points data-toc-label="vector_analyzer_points" }

```python
vector_analyzer_points(channel=1)          # -> int (query)
vector_analyzer_points(1000, channel=1)    # set 1000 points for measurement
```

This function queries or sets the number of points for measurement. If there is no argument, the function returns the current number of points for the channel specified as the keyword "channel". If there is an argument, the specified number of points will be set for the indicated channel. The available number of points is specified directly in the device configuration file. The number of available channels is also given in the configuration file.

**Range:** `2` – `500001`
{: .enum }

---

### vector_analyzer_trigger_source(*src) { #vector_analyzer_trigger_source data-toc-label="vector_analyzer_trigger_source" }

```python
vector_analyzer_trigger_source()         # -> str (query)
vector_analyzer_trigger_source('INT')    # set internal trigger source
```

This function queries or sets the trigger source. If there is no argument, the function returns the current trigger source as a string. If there is an argument, the specified trigger source will be set.

**Allowed:** `'INT'`, `'EXT'`, `'MAN'`, `'BUS'`
{: .enum }

---

### vector_analyzer_send_trigger() { #vector_analyzer_send_trigger data-toc-label="vector_analyzer_send_trigger" }

```python
vector_analyzer_send_trigger()    # send a single software trigger
```

This function can only be called without arguments and is used to send a single software trigger to the device. It is usually used in combination with `'MAN'` or `'BUS'` [trigger source](#vector_analyzer_trigger_source).

---

### vector_analyzer_intermediate_freqiency_bandwith(*freq, channel = 1) { #vector_analyzer_intermediate_freqiency_bandwith data-toc-label="vector_analyzer_intermediate_freqiency_bandwith" }

```python
vector_analyzer_intermediate_freqiency_bandwith(channel=1)              # -> str (query)
vector_analyzer_intermediate_freqiency_bandwith('10 kHz', channel=1)    # set IF BW to 10 kHz
```

This function queries or sets the intermediate frequency bandwidth for measurement. If there is no argument, the function returns the current bandwidth for the channel specified as the keyword "channel". If there is an argument, the specified bandwidth will be set for the indicated channel. If there is no bandwidth setting fitting the argument the nearest available value is used and warning is printed.

**Output format:** `'number'` + `'Hz'` | `'kHz'` | `'MHz'`
{: .enum }

**Allowed numeric values:** `1`, `2`, `3`, `5`, `7`, `10`, `15`, `20`, `30`, `50`, `70`, `100`, `150`, `200`, `300`, `500`, `700`, `1000`
{: .enum }

---

### vector_analyzer_trigger_mode(*md, channel = 1) { #vector_analyzer_trigger_mode  data-toc-label="vector_analyzer_trigger_mode" }

```python
vector_analyzer_trigger_mode()         # -> str (query)
vector_analyzer_trigger_mode('REP')    # set repetitive trigger initiation mode
```

This function queries or sets the trigger initiation mode. If there is no argument, the function returns the current trigger mode as a string. If there is an argument, the specified trigger initiation mode will be set. The `'REP'` argument corresponds to repetitive mode, `'SINGLE'` to single start, and `'OFF'` stops the device.

**Allowed:** `'SINGLE'`, `'REP'`, `'OFF'`
{: .enum }

---

### vector_analyzer_get_curve(s = 'S11', type = 'IQ', channel = 1, data_type = 'COR') { #vector_analyzer_get_curve data-toc-label="vector_analyzer_get_curve" }

```python
# Perform the measurement and return two 'S11' curves
# in the form of amplitude and phase.
vector_analyzer_get_curve(s='S11', type='AP')
```

This function runs the measurement for the channel specified as the keyword "channel" and returns the result as two numpy arrays with the number of points specified in the function [`vector_analyzer_points()`](#vector_analyzer_points). The number of available channels is given in the configuration file.

The acquired curves can be returned in two different formats. The `'IQ'` format corresponds to the real and imagimary parts of the measured signal in mV. The `'AP'` format corresponds to the amplitude and phase of the measured signal. The keyword `'data_type'` indicates whether the measured signal is corrected using various calibration coefficients or not.

**Allowed s-parameters:** `'S11'`, `'S12'`, `'S21'`, `'S22'`, `'R11'`, `'R12'`, `'R21'`, `'R22'`, `'A(1)'`, `'A(2)'`, `'B(1)'`, `'B(2)'`
{: .enum }

**Allowed type:** `'IQ'`, `'AP'`
{: .enum }

**Allowed data_type:** `'COR'`, `'RAW'`
{: .enum }

---

### vector_analyzer_get_frequency_points(channel = 1) { #vector_analyzer_get_frequency_points data-toc-label="vector_analyzer_get_frequency_points" }

```python
vector_analyzer_get_frequency_points()    # -> np.array; measured frequency points
```

This function returns an array of measurement point frequencies for the channel specified as the keyword "channel". The total number of points in the array is equal to the number of points specified in the function [`vector_analyzer_points()`](#vector_analyzer_points). The number of available channels is given in the configuration file. The frequencies are given in MHz.

---

### vector_analyzer_measurement_time(channel = 1) { #vector_analyzer_measurement_time data-toc-label="vector_analyzer_measurement_time" }

```python
vector_analyzer_measurement_time()    # -> float; measurement time in seconds
```

This function returns the measurement time for the channel specified as the keyword "channel". The number of available channels is given in the configuration file. The measurement time are given in seconds.

---

### vector_analyzer_command(command) { #vector_analyzer_command data-toc-label="vector_analyzer_command" }

```python
vector_analyzer_command('DISP:WIND:TRAC:Y:AUTO')    # perform automatic graph scaling
```

This function sends an arbitrary command from a programming guide to the device in a string format. No output is expected.

---

### vector_analyzer_query(command) { #vector_analyzer_query data-toc-label="vector_analyzer_query" }

```python
vector_analyzer_query('SERV:CHAN:ACT?')    # -> str; number of the active channel
```

This function sends an arbitrary command from a programming guide to the device in a string format. An output in a string format is expected.
