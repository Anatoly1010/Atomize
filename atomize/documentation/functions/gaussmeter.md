# Gaussmeters

## Devices

| Device                          | Tested  | Connection         |
| ------------------------------- | ------- | ------------------ |
| **Lakeshore 455 DSP**           | 01/2021 | RS-232             |
| **NMR Gaussmeter Sibir 1**      | 04/2024 | UDP/IP Socket      |

## Functions

### gaussmeter_name() { #gaussmeter_name data-toc-label="gaussmeter_name" }

```python
gaussmeter_name()    # -> str; device name
```

This function returns device name.

---

### gaussmeter_field() { #gaussmeter_field data-toc-label="gaussmeter_field" }

```python
gaussmeter_field()    # Lakeshore: -> float; field reading in Gauss
gaussmeter_field()    # Sibir 1:   -> numpy.array, numpy.array, float, float
```

This function is for reading field and should be called with no argument. The default unit is Gauss. By using [`gaussmeter_units()`](#gaussmeter_units) function unit setting can be changed.

In the case of Sibir 1 Gaussmeter, this function returns (i) numpy.array of the measured FID, (ii) numpy.array of the measured NMR spectrum, (iii) float of the measured magnetic field in Gauss, (iv) float of the measured signal-to-noise ratio.

---

### gaussmeter_units(*units) { #gaussmeter_units data-toc-label="gaussmeter_units" }

```python
gaussmeter_units()           # -> str (query)
gaussmeter_units('Tesla')    # change unit of gaussmeter_field() to Tesla
```

This function queries or changes the unit in which [`gaussmeter_field()`](#gaussmeter_field) function returns the result. If called with no argument the current unit is returned. If called with an argument the specified unit is set.

**Allowed:** `'Gauss'`, `'Tesla'`, `'Oersted'`, `'Amp/m'`
{: .enum }

!!! note
    This function is not available for Sibir 1 Gaussmeter.

---

### gaussmeter_points(*points) { #gaussmeter_points data-toc-label="gaussmeter_points" }

```python
gaussmeter_points()        # -> int (query)
gaussmeter_points(8192)    # set FID points to 8192
```

This function queries or sets the number of FID points that will be measured after applying pi/2 pulse. If called with no argument the current number of points is returned. If called with an argument the specified number of points is set. If there is no number of points setting fitting the argument the nearest available value is used and warning is printed.

**Allowed:** `8192`, `16384`, `32768`, `53248`
{: .enum }

!!! note
    This function is only available for Sibir 1 Gaussmeter.

---

### gaussmeter_number_of_averages(*number) { #gaussmeter_number_of_averages data-toc-label="gaussmeter_number_of_averages" }

```python
gaussmeter_number_of_averages()      # -> int (query)
gaussmeter_number_of_averages(64)    # set number of averages to 64
```

This function queries or sets the number of averages for FID of NMR signal from the probe. If called with no argument the current number of averages is returned. If called with an argument the specified  number of averages is set. If there is no number of averages setting fitting the argument the nearest available value is used and warning is printed.

**Allowed:** `1`, `8`, `16`, `32`, `64`, `128`, `256`, `512`, `1024`, `2048`
{: .enum }

!!! note
    This function is only available for Sibir 1 Gaussmeter.

---

### gaussmeter_search(start, end, step) { #gaussmeter_search data-toc-label="gaussmeter_search" }

```python
gaussmeter_search(1000, 1500, 10)    # -> float; search the field with best SNR
```

This function performs repeated measurements of the FID decay from the probe with a synthetizer frequency corresponding to the current field. The latter is varied during the function exectuion, starting from 'start' value with a step of 'step'. The function returns the value of magnetic field with the best measured signal-to-noise ratio.

!!! note
    This function is only available for Sibir 1 Gaussmeter.

---

### gaussmeter_set_field(*B) { #gaussmeter_set_field data-toc-label="gaussmeter_set_field" }

```python
gaussmeter_set_field()        # -> float (query)
gaussmeter_set_field(1234)    # set synthetizer frequency matching B = 1234 G
```

This function queries or sets the synthetizer frequency. Instead of the frequency a corresponding magnetic field is used as an argument. To increase the signal-to-noise ratio the value of magnetic field, indicated as an argument of this function, should be as closer as possible to the real value to be measured. If called with no argument the current value of magnetic field is returned. If called with an argument the specified value of magnetic field is set.

!!! note
    This function is only available for Sibir 1 Gaussmeter.

---

### gaussmeter_gain(*gain) { #gaussmeter_gain data-toc-label="gaussmeter_gain" }

```python
gaussmeter_gain()      # -> int (query)
gaussmeter_gain(10)    # set preamplifier gain to 10 arb. u.
```

This function queries or sets the preamplifier gain for the detection of NMR signal from the probe. If called with no argument the current gain is returned. If called with an argument the specified gain is set.

**Range:** `0` – `31`
{: .enum }

!!! note
    This function is only available for Sibir 1 Gaussmeter.

---

### gaussmeter_pulse_length(*length) { #gaussmeter_pulse_length data-toc-label="gaussmeter_pulse_length" }

```python
gaussmeter_pulse_length()      # -> int (query)
gaussmeter_pulse_length(10)    # set pi/2 pulse length to 10 us
```

This function queries or sets the pi/2 pulse length in us. If called with no argument the current pulse length is returned. If called with an argument the specified pulse length is set.

**Range:** `0 us` – `40 us`
{: .enum }

!!! note
    This function is only available for Sibir 1 Gaussmeter.

---

### gaussmeter_sensor_number(*number) { #gaussmeter_sensor_number data-toc-label="gaussmeter_sensor_number" }

```python
gaussmeter_sensor_number()     # -> int (query)
gaussmeter_sensor_number(1)    # use sensor 1
```

This function queries or sets the number of sensor that will be used for magnetic field measurement. If called with no argument the current sensor number is returned. If called with an argument the specified sensor number is set. Each sensor is optimized for different magnetic field range. Sensors 1 and 2 are optimized for the range of 25 mT - 200 mT.  Sensors 3 and 4 are optimized for the range of 90 mT - 2000 mT.

**Allowed:** `1`, `2`, `3`, `4`
{: .enum }

!!! note
    This function is only available for Sibir 1 Gaussmeter.

---

### gaussmeter_command(command) { #gaussmeter_command data-toc-label="gaussmeter_command" }

```python
# Configure Lakeshore 455 for DC field measurement, DC resolution of 5 digits,
# wide band rms filter mode, peak measurement mode is periodic, and positive
# peak readings will be shown if the measurement mode is changed to peak.
gaussmeter_command('RDGMODE 1,3,1,1,1')
```

This function sends an arbitrary command from a programming guide to the device in a string format. No output is expected.

!!! note
    This function is not available for Sibir 1 Gaussmeter.

---

### gaussmeter_query(command) { #gaussmeter_query data-toc-label="gaussmeter_query" }

```python
gaussmeter_query('TYPE? ')    # -> str; returns probe type
```

This function sends an arbitrary command from a programming guide to the device in a string format. An output in a string format is expected.

!!! note
    This function is not available for Sibir 1 Gaussmeter.
