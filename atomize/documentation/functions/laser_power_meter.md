# Laser Power Meters

## Devices

| Device                  | Tested  | Connection |
| ----------------------- | ------- | ---------- |
| **Gentec-EO Solo2**     | 12/2025 | RS-232     |

## Functions

### laser_power_meter_name() { #laser_power_meter_name data-toc-label="laser_power_meter_name" }

```python
laser_power_meter_name()    # -> str; device name
```

The function returns device name.

---

### laser_power_meter_head_name() { #laser_power_meter_head_name data-toc-label="laser_power_meter_head_name" }

```python
laser_power_meter_head_name()    # -> str; model name of the current head
```

The function returns the model name of the current head.

---

### laser_power_meter_get_data() { #laser_power_meter_get_data data-toc-label="laser_power_meter_get_data" }

```python
laser_power_meter_get_data()    # -> float; current measured value
```

This function returns the measured value as soon as a new value appears on the device. If there is no new value, 10 consecutive attempts will be made, each of which will be repeated after the timeout specified in the configuration file has elapsed. After 10 unsuccessful attempts, a corresponding message will be displayed and the function will return 0.

---

### laser_power_meter_wavelength(*wavelength) { #laser_power_meter_wavelength data-toc-label="laser_power_meter_wavelength" }

```python
laser_power_meter_wavelength()       # -> str (query)
laser_power_meter_wavelength(532)    # set wavelength to 532 nm
```

This function queries or sets the wavelength being used on the detector. If there is no argument the function will return the current wavelength as a string: `"Wavelength for correction: xxx nm"`. If there is an argument the specified wavelength will be set.

**Range:** `193 nm` – `2100 nm`
{: .enum }

---

### laser_power_meter_zero_offset(*zero_mode) { #laser_power_meter_zero_offset data-toc-label="laser_power_meter_zero_offset" }

```python
laser_power_meter_zero_offset()        # -> str (query)
laser_power_meter_zero_offset('On')    # reset current measured value to zero
```

This function queries or sets the zero mode being used on the detector. If there is no argument the function will return the current zero mode as a string: `"Zero offset mode: ['On', 'Off']"`. The argument `'On'` resets the current measured value to zero. The argument `'Off'` disables the previousy performed reset.

**Allowed:** `'On'`, `'Off'`, `'Undo'`
{: .enum }

---

### laser_power_meter_analog_output(*analog_output) { #laser_power_meter_analog_output data-toc-label="laser_power_meter_analog_output" }

```python
laser_power_meter_analog_output()        # -> str (query)
laser_power_meter_analog_output('On')    # turn on the analog output
```

This function queries or sets the status of the analog output. If there is no argument, the function returns the current status of the analog output as a string: `"Analog output: ['On', 'Off']"`. The argument `'On'` turns on the analog output of the detector. The argument `'Off'` turns off the analog output.

**Allowed:** `'On'`, `'Off'`
{: .enum }

---

### laser_power_meter_energy_mode(*energy_mode) { #laser_power_meter_energy_mode data-toc-label="laser_power_meter_energy_mode" }

```python
laser_power_meter_energy_mode()         # -> str (query)
laser_power_meter_energy_mode('Off')    # turn off the energy mode
```

This function queries or sets the current state of the energy mode. If there is no argument, the function returns the state of the energy mode as a string: `"Energy mode: ['On', 'Off']"`. The argument `'On'` can be used to toggle energy mode when using a wattmeter. The argument `'Off'` turns off the energy mode.

**Allowed:** `'On'`, `'Off'`
{: .enum }

---

### laser_power_meter_scale(scale) { #laser_power_meter_scale data-toc-label="laser_power_meter_scale" }

```python
laser_power_meter_scale('10 mW')    # set display range to 10 mW
laser_power_meter_scale(0)          # automatic scaling
```

This function forces the display of the current data within a specific range indicated as an argument. The argument is discrete and can take values from `[1, 3, 10, 30, 100, 300]` combined with one of the scaling suffixes. If there is no scale setting corresponding to the argument, the nearest available value is used and warning is printed. Note that not all scales are available for all heads.

An argument equals to 0 has a special meaning and corresponds to automatic scaling. The auto scale mode applies the best scale for the current values in real time.

**Output format:** `'number'` + `'pW'` | `'nW'` | `'uW'` | `'mW'` | `'W'` | `'kW'`, or `0` for auto
{: .enum }

---

### laser_power_meter_command(command) { #laser_power_meter_command data-toc-label="laser_power_meter_command" }

```python
laser_power_meter_command(command)    # str -> none
```

The function for sending an arbitrary command from a programming guide to the device in a string format. No output is expected. Please note that Gentec-EO Solo2 always responds to commands, so this function cannot be used for it.

---

### laser_power_meter_query(command) { #laser_power_meter_query data-toc-label="laser_power_meter_query" }

```python
laser_power_meter_query('*SHL')    # adds significant digits to the on-screen reading
```

The function for sending an arbitrary command from a programming guide to the device in a string format. An output in a string format is expected. Please note that Gentec-EO Solo2 will respond with "ACK" if the command is successfully executed.
