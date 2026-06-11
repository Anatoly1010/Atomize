# Other Devices

## Devices

| Device                                                | Tested  | Connection     |
| ----------------------------------------------------- | ------- | -------------- |
| **CPWplus 150** Balance                               | 01/2021 | RS-232         |
| **RODOS 10N** Solid-State Relay                       | 01/2021 | Ethernet       |
| **Owen MK110-220.4DN.4R** Discrete IO Module          | 04/2021 | RS-485         |
| **Cryomagnetics LM-510** Liquid Cryogen Monitor       | 07/2022 | TCP/IP Socket  |
| **Cryomech CPA2896**, **CPA1110** Digital Panels      | 07/2022 | RS-485         |

## Balance

### balance_weight() { #balance_weight data-toc-label="balance_weight" }

```python
balance_weight()    # -> float; current weight of the balances
```

This function returns the current weight of the balances and should be called with no argument.

---

## Rodos 10N Solid-State Relay

### relay_turn_on(number) { #relay_turn_on data-toc-label="relay_turn_on" }

```python
relay_turn_on(1)    # turn on channel 1 of solid-state relay
```

This function turns on the specified channel of the solid-state relay and should be called with one argument. Channel should be specified as integer in the range of 1 to 4.

---

### relay_turn_off(number) { #relay_turn_off data-toc-label="relay_turn_off" }

```python
relay_turn_off(2)    # turn off channel 2 of solid-state relay
```

This function turns off the specified channel of the solid-state relay and should be called with one argument. Channel should be specified as integer in the range of 1 to 4.

---

## Owen MK110-220.4DN.4R Discrete IO Module

### discrete_io_input_counter(channel) { #discrete_io_input_counter data-toc-label="discrete_io_input_counter" }

```python
discrete_io_input_counter('1')    # -> int; counter value of input 1
```

This function returns the counter value of the specified input channel of the discrete IO module.

**Allowed channels:** `'1'`, `'2'`, `'3'`, `'4'`
{: .enum }

---

### discrete_io_input_counter_reset(channel) { #discrete_io_input_counter_reset data-toc-label="discrete_io_input_counter_reset" }

```python
discrete_io_input_counter_reset('1')    # reset counter of input 1
```

This function resets the counter of the specified input channel.

**Allowed channels:** `'1'`, `'2'`, `'3'`, `'4'`
{: .enum }

---

### discrete_io_input_state() { #discrete_io_input_state data-toc-label="discrete_io_input_state" }

```python
discrete_io_input_state()    # -> str; e.g. '1234' = inputs 1–4 are on
```

This function returns the input channel states of the discrete IO module and should be called without argument. The output is in the form `['0', '1', '2', ... '12', ... '1234']`. The meaning is the following: `'0'` – all inputs are off, `'12'` – inputs 1 and 2 are on, and so on.

---

### discrete_io_output_state(*state) { #discrete_io_output_state data-toc-label="discrete_io_output_state" }

```python
discrete_io_output_state()       # -> str (query)
discrete_io_output_state('0')    # turn off all outputs of the IO module
```

This function sets or queries the output channel states of the discrete IO module. If an argument is specified the function sets specified state of the output channels. If there is no argument the function returns the current state of the output channels. The argument should be in the form `['0', '1', '2', ... '12', ... '1234']`. The meaning is the following: `'0'` – all outputs are off, `'12'` – outputs 1 and 2 are on, and so on. The output format is the same as the described argument.

---

## Cryomech CPA2896 / CPA1110 Digital Panels

### cryogenic_refrigerator_name() { #cryogenic_refrigerator_name data-toc-label="cryogenic_refrigerator_name" }

```python
cryogenic_refrigerator_name()    # -> str; device name
```

This function returns device name.

---

### cryogenic_refrigerator_state(*state) { #cryogenic_refrigerator_state data-toc-label="cryogenic_refrigerator_state" }

```python
cryogenic_refrigerator_state()        # -> str (query)
cryogenic_refrigerator_state('On')    # turn on the compressor
```

This function sets or queries the state of the cryogenic refrigerator. If there is no argument the function will return the current state. If called with an argument the specified state will be set.

**Allowed (set):** `'On'`, `'Off'`
{: .enum }

**Returned (query):** `'Idling'`, `'Starting'`, `'Running'`, `'Stopping'`, `'Error Lockout'`, `'Error'`, `'Helium Cool Down'`, `'Power related Error'`, `'Recovered from Error'`
{: .enum }

---

### cryogenic_refrigerator_status_data() { #cryogenic_refrigerator_status_data data-toc-label="cryogenic_refrigerator_status_data" }

```python
cryogenic_refrigerator_status_data()    # -> numpy.array(11); all status data
```

This function queries the status data of the cryogenic refrigerator. The returned array is as follows:

| Index | Field                       |
| ----- | --------------------------- |
| 0     | Coolant Tempeparure In      |
| 1     | Coolant Tempeparure Out     |
| 2     | Oil Tempeparure             |
| 3     | Helium Tempeparure          |
| 4     | Low Pressure                |
| 5     | Low Pressure Averaged       |
| 6     | High Pressure               |
| 7     | High Pressure Averaged      |
| 8     | Delta Pressure Averaged     |
| 9     | Motor Current (A)           |
| 10    | Operation Hours (H/1000)    |

The dimensions for the pressure and temperature data can be checked using [`cryogenic_refrigerator_pressure_scale()`](#cryogenic_refrigerator_pressure_scale) and [`cryogenic_refrigerator_temperature_scale()`](#cryogenic_refrigerator_temperature_scale) functions, respectively. Note that Cryomech uses the so-called Little endian (Intel) byte order.

---

### cryogenic_refrigerator_warning_data() { #cryogenic_refrigerator_warning_data data-toc-label="cryogenic_refrigerator_warning_data" }

```python
cryogenic_refrigerator_warning_data()    # -> numpy.array(2); [warning, alarm]
```

This function queries the warning and alarm data of the cryogenic refrigerator. The returned array is as follows:

| Index | Field         |
| ----- | ------------- |
| 0     | Warning State |
| 1     | Alarm State   |

**Possible warning states:** `'No warnings'`, `'Coolant IN running High'`, `'Coolant IN running Low'`, `'Coolant OUT running High'`, `'Coolant OUT running Low'`, `'Oil running High'`, `'Oil running Low'`, `'Helium running High'`, `'Helium running Low'`, `'Low Pressure running High'`, `'Low Pressure running Low'`, `'High Pressure running High'`, `'High Pressure running Low'`, `'Delta Pressure running High'`, `'Delta Pressure running Low'`, `'Static Presure running High'`, `'Static Presure running Low'`, `'Cold head motor Stall'`
{: .enum }

**Possible error states:** `'No Errors'`, `'Coolant IN High'`, `'Coolant IN Low'`, `'Coolant OUT High'`, `'Coolant OUT Low'`, `'Oil High'`, `'Oil Low'`, `'Helium High'`, `'Helium Low'`, `'Low Pressure High'`, `'Low Pressure Low'`, `'High Pressure High'`, `'High Pressure Low'`, `'Delta Pressure High'`, `'Delta Pressure Low'`, `'Motor Current Low'`, `'Three Phase Error'`, `'Power Supply Error'`, `'Static Presure High'`, `'Static Presure Low'`
{: .enum }

---

### cryogenic_refrigerator_pressure_scale() { #cryogenic_refrigerator_pressure_scale data-toc-label="cryogenic_refrigerator_pressure_scale" }

```python
cryogenic_refrigerator_pressure_scale()    # -> str; current pressure scale
```

This function queries the current pressure scale. The scale cannot be changed via remote interface.

**Allowed:** `'PSI'`, `'Bar'`, `'KPA'`
{: .enum }

---

### cryogenic_refrigerator_temperature_scale() { #cryogenic_refrigerator_temperature_scale data-toc-label="cryogenic_refrigerator_temperature_scale" }

```python
cryogenic_refrigerator_temperature_scale()    # -> str; current temperature scale
```

This function queries the current temperature scale. The scale cannot be changed via remote interface.

**Allowed:** `'Fahrenheit'`, `'Celsius'`, `'Kelvin'`
{: .enum }

---

## Cryomagnetics LM-510 Liquid Cryogen Monitor

### level_monitor_name() { #level_monitor_name data-toc-label="level_monitor_name" }

```python
level_monitor_name()    # -> str; device name
```

This function returns device name.

---

### level_monitor_select_channel(*channel) { #level_monitor_select_channel data-toc-label="level_monitor_select_channel" }

```python
level_monitor_select_channel()       # -> str (query)
level_monitor_select_channel('1')    # set default channel to 1 for future commands
```

This function sets or queries the default channel for future computer commands. If there is no argument the function will return the current default channel. If called with an argument the specified default channel will be set.

**Allowed:** `'1'`, `'2'`
{: .enum }

---

### level_monitor_boost_mode(*mode) { #level_monitor_boost_mode data-toc-label="level_monitor_boost_mode" }

```python
level_monitor_boost_mode()           # -> str (query)
level_monitor_boost_mode('Smart')    # set boost mode to 'Smart'
```

This function sets or queries the operating mode for the boost portion of a sensor read cycle for the [selected channel](#level_monitor_select_channel). If there is no argument the function will return the boost mode. If called with an argument the specified boost mode will be set. Boost `'Off'` will eliminate the boost portion of the read cycle, boost `'On'` enables the boost portion on every read cycle, and boost `'Smart'` enables a boost cycle if no readings have been taken in the previous 5 minutes.

!!! note
    This function is not available on the second channel if it is used as HRC (Helium Recondenser Controller) channel. This setting should be specified in the configuration file in the field: `hrc_second_channel`.

**Allowed:** `'On'`, `'Off'`, `'Smart'`
{: .enum }

---

### level_monitor_high_level_alarm(*level) { #level_monitor_high_level_alarm data-toc-label="level_monitor_high_level_alarm" }

```python
level_monitor_high_level_alarm()        # -> str (query)
level_monitor_high_level_alarm(99.0)    # set high level alarm to 99.0 in present units
```

This function sets or queries the threshold for the high alarm in the present [units](#level_monitor_units) for the [selected channel](#level_monitor_select_channel). If the liquid level rises above the threshold the alarm will be activated. The alarm will be disabled if the threshold is set to `100.0`.

!!! note
    This function is not available on the second channel if it is used as HRC (Helium Recondenser Controller) channel. This setting should be specified in the configuration file in the field: `hrc_second_channel`.

---

### level_monitor_low_level_alarm(*level) { #level_monitor_low_level_alarm data-toc-label="level_monitor_low_level_alarm" }

```python
level_monitor_low_level_alarm()    # -> str; low level alarm in present units
```

This function sets or queries the threshold for the low alarm in the present [units](#level_monitor_units) for the [selected channel](#level_monitor_select_channel). If the liquid level rises above the threshold the alarm will be activated. The alarm will be disabled if the threshold is set to `0.0`.

!!! note
    This function is not available on the second channel if it is used as HRC (Helium Recondenser Controller) channel. This setting should be specified in the configuration file in the field: `hrc_second_channel`.

---

### level_monitor_sensor_length() { #level_monitor_sensor_length data-toc-label="level_monitor_sensor_length" }

```python
level_monitor_sensor_length()    # -> str; sensor length in present units
```

This function returns the active sensor length in the present [units](#level_monitor_units) for the [selected channel](#level_monitor_select_channel). The length is returned in centimeters if percent is the present unit selection.

!!! note
    This function is not available on the second channel if it is used as HRC (Helium Recondenser Controller) channel. This setting should be specified in the configuration file in the field: `hrc_second_channel`.

---

### level_monitor_sample_mode(*mode) { #level_monitor_sample_mode data-toc-label="level_monitor_sample_mode" }

```python
level_monitor_sample_mode()                # -> str (query)
level_monitor_sample_mode('Continuous')    # set continuous sampling
```

This function sets or queries the sample mode for the [selected channel](#level_monitor_select_channel). If there is no argument the function will return the sample mode. If called with an argument the specified sample mode will be set. In the `'Sample/Hold'` mode the measurements are taken when a [measure command](#level_monitor_measure) is sent via the computer interface or when the delay between samples set by the [`level_monitor_sample_interval()`](#level_monitor_sample_interval) function command expires. The interval timer is reset on each measurement, regardless of source of the measurement request. In `'Continuous'` mode measurements are taken as frequently as possible.

!!! note
    This function is not available on the second channel if it is used as HRC (Helium Recondenser Controller) channel. This setting should be specified in the configuration file in the field: `hrc_second_channel`.

**Allowed:** `'Sample/Hold'`, `'Continuous'`, `'Off'`
{: .enum }

---

### level_monitor_units(*units) { #level_monitor_units data-toc-label="level_monitor_units" }

```python
level_monitor_units()        # -> str (query)
level_monitor_units('cm')    # set units to centimeters
```

This function sets or queries the units to be used for all input and display operations for the [selected channel](#level_monitor_select_channel). If there is no argument the function will return the present units. If called with an argument the specified units will be set.

!!! note
    This function is not available on the second channel if it is used as HRC (Helium Recondenser Controller) channel. This setting should be specified in the configuration file in the field: `hrc_second_channel`.

**Allowed:** `'cm'`, `'in'`, `'%'`
{: .enum }

---

### level_monitor_measure(channel) { #level_monitor_measure data-toc-label="level_monitor_measure" }

```python
level_monitor_measure('2')    # -> str; measure from channel 2 in present units
```

This function starts a measurement on the [selected channel](#level_monitor_select_channel) and queries the result in the present [units](#level_monitor_units). This function return two values (pressure in psi and heater power in watts) if the second channel is used as HRC (Helium Recondenser Controller).

**Allowed channels:** `'1'`, `'2'`
{: .enum }

---

### level_monitor_sample_interval(*interval) { #level_monitor_sample_interval data-toc-label="level_monitor_sample_interval" }

```python
level_monitor_sample_interval()                # -> str (query, HH:MM:SS)
level_monitor_sample_interval('0', '5', '0')   # set 5-minute interval between samples
```

This function sets or queries the time between samples for the [selected channel](#level_monitor_select_channel). If there is no argument the function will return the present time between samples in the HH:MM:SS format. If called with three arguments the specified interval will be set. The three arguments correspond to hours, minutes, and seconds.

!!! note
    This function is not available on the second channel if it is used as HRC (Helium Recondenser Controller) channel. This setting should be specified in the configuration file in the field: `hrc_second_channel`.

**Range hours:** `0` – `99`
{: .enum }

**Range minutes:** `0` – `59`
{: .enum }

**Range seconds:** `0` – `59`
{: .enum }

---

### level_monitor_hrc_target_pressure(*pressure) { #level_monitor_hrc_target_pressure data-toc-label="level_monitor_hrc_target_pressure" }

```python
level_monitor_hrc_target_pressure()         # -> str (query)
level_monitor_hrc_target_pressure('1.0')    # set target pressure to 1.0 psi
```

This function sets or queries the target operating pressure for the HRC (Helium Recondenser Controller) channel. If there is no argument the function will return the present target pressure in psi. If called with one argument the specified pressure will be set.

!!! note
    This function is only available for HRC (Helium Recondenser Controller) channel. This setting should be specified in the configuration file in the field: `hrc_second_channel`.

**Range:** `0.15 psi` – `14.25 psi`
{: .enum }

---

### level_monitor_hrc_heater_power_limit(*limit) { #level_monitor_hrc_heater_power_limit data-toc-label="level_monitor_hrc_heater_power_limit" }

```python
level_monitor_hrc_heater_power_limit()         # -> str (query)
level_monitor_hrc_heater_power_limit('4.0')    # set heater power limit to 4.0 watts
```

This function sets or queries the heater power limit for the HRC (Helium Recondenser Controller) channel. If there is no argument the function will return the present heater power limit in watts. If called with one argument the specified power limit will be set.

!!! note
    This function is only available for HRC (Helium Recondenser Controller) channel. This setting should be specified in the configuration file in the field: `hrc_second_channel`.

**Range:** `0.1 W` – `10 W`
{: .enum }

---

### level_monitor_hrc_heater_enable(*state) { #level_monitor_hrc_heater_enable data-toc-label="level_monitor_hrc_heater_enable" }

```python
level_monitor_hrc_heater_enable()        # -> str (query)
level_monitor_hrc_heater_enable('On')    # turn on the HRC heater
```

This function sets or queries the state of the HRC (Helium Recondenser Controller) channel heater. If there is no argument the function will return the present state. If called with one argument the specified state will be set. Note, that if the heater is turned off due to the system being above the target operating pressure when the heater is enabled, `'On'` will still be returned.

!!! note
    This function is only available for HRC (Helium Recondenser Controller) channel. This setting should be specified in the configuration file in the field: `hrc_second_channel`.

**Allowed:** `'On'`, `'Off'`
{: .enum }

---

### level_monitor_command(command) { #level_monitor_command data-toc-label="level_monitor_command" }

```python
# set low threshold for Control functions (automated refill activation)
level_monitor_command('LOW 45.0')
```

This function sends an arbitrary command from a programming guide to the device in a string format. No output is expected.

---

### level_monitor_query(command) { #level_monitor_query data-toc-label="level_monitor_query" }

```python
# query the status of the Control Relay (i.e., refill status)
level_monitor_query('CTRL?')    # -> str
```

This function sends an arbitrary command from a programming guide to the device in a string format. An output in a string format is expected.
