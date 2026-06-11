# Temperature Controllers

## Devices

| Device                                      | Tested  | Connection                              |
| ------------------------------------------- | ------- | --------------------------------------- |
| **Lakeshore 325 / 331 / 332 / 335 / 336 / 340** | 01/2021 | GPIB (linux-gpib), RS-232               |
| **Oxford Instruments ITC 503**              | 01/2021 | RS-232                                  |
| **Termodat 11M6 / 13KX3**                   | 04/2021 | RS-485                                  |
| **Stanford Research PTC10**                 | 07/2021 | TCP/IP Socket                           |
| **Scientific Instruments SCM10**            | 07/2022 | TCP/IP Socket, RS-232                   |

## Functions

### tc_name() { #tc_name data-toc-label="tc_name" }

```python
tc_name()    # -> str; device name
```

This function returns device name.

---

### tc_temperature(channel) { #tc_temperature data-toc-label="tc_temperature" }

```python
tc_temperature('A')    # -> float; temperature of channel A in Kelvin
```

This function is for reading temperature from the specified channel.

Note that arguments can be devices specific. For Stanford Research PTC10 an argument of the function should have the name of the channel. For instance, if the channel name is `2A` one should use `tc_temperature('2A')` in order to get the temperature.

For Scientific Instruments SCM10 the only available argument is `'1'`.

**Allowed (Lakeshore 325, 331, 332, 335):** `'A'`, `'B'`
{: .enum }

**Allowed (Lakeshore 336, 340):** `'A'`, `'B'`, `'C'`, `'D'`
{: .enum }

**Allowed (Oxford ITC 503):** `'1'`, `'2'`, `'3'`
{: .enum }

**Allowed (Termodat-11M6):** `'1'`, `'2'`, `'3'`, `'4'`
{: .enum }

**Allowed (Termodat-13KX3):** `'1'`, `'2'`
{: .enum }

---

### tc_setpoint(*temp) { #tc_setpoint data-toc-label="tc_setpoint" }

```python
tc_setpoint()       # -> float (query)
tc_setpoint(100)    # set target temperature to 100 K
```

This function queries or changes the set point, i.e. the target temperature the device will try to achieve and maintain. If an argument is specified the function sets a new temperature point. If there is no argument the function returns the current set point. A loop can be specified in the configuration file.

!!! note
    This function is not available for Scientific Instruments SCM10.

For Termodat-11M6, 13KX3 and Stanford Research PTC10 the channel for which the set point is to be set should be specified as an agrument of the following function:

### tc_setpoint(channel, *temp) { #tc_setpoint-channel }

```python
tc_setpoint('2')         # -> float (query)
tc_setpoint('2', 100)    # set setpoint of channel 2 to 100 K
```

An accuracy of the set point setting is 0.1 degree. The number of available channels should be specified in the configuration file. If there is no temperature argument the function returns the current set point for specified channel.

For Stanford Research PTC10 a channel argument should have the name of the output channel. For instance, if the channel name is `'Heater'` one should use `tc_setpoint('Heater', 80)` in order to set the desired temperature.

**Allowed channels (Termodat-11M6):** `'1'`, `'2'`, `'3'`, `'4'`
{: .enum }

**Allowed channels (Termodat-13KX3):** `'1'`, `'2'`
{: .enum }

---

### tc_heater_range(*heater) { #tc_heater_range data-toc-label="tc_heater_range" }

```python
tc_heater_range()          # -> str (query)
tc_heater_range('50 W')    # set heater range to 50 W (High)
```

This function queries or sets the heater range. If an argument is specified the function sets a new heater range. If there is no argument the function returns the current heater range. For Oxford Instrument ITC 503 [`tc_heater_power_limit()`](#tc_heater_power_limit) fucntion should be used instead.

For Lakeshore 336 a loop 1 or 2 can be used with the larger set; loops 3 and 4 can be used only with `['On', 'Off']` setting. For Lakeshore 325 a loop 1 can be used with `['25 W', '2.5 W', 'Off']`; loop 2 can be used only with `['On', 'Off']` setting. The values `'50 W'`, `'5 W'`, and `'0.5 W'` are shown as High, Medium, and Low on the device display. The exact values depends on the resistance used.

**Allowed (Lakeshore 331, 332, 335):** `'50 W'`, `'5 W'`, `'0.5 W'`, `'Off'`
{: .enum }

**Allowed (Lakeshore 340):** `'10 W'`, `'1 W'`, `'Off'`
{: .enum }

**Allowed (Lakeshore 325, loop 1):** `'25 W'`, `'2.5 W'`, `'Off'`
{: .enum }

!!! note
    This function is available only for Lakeshore temperature controllers.
    Not available for Termodat-11M6, 13KX3, Stanford Research PTC10,
    Scientific Instruments SCM10.

---

### tc_heater_power() { #tc_heater_power data-toc-label="tc_heater_power" }

```python
tc_heater_power()    # -> [str, float]; heater range and percent
```

This function is for reading the current heater value in percent for the specified loop. The loop config (should be indicated in the configuration file) can be: 1, 2 for Lakeshore 325, 331, 332, 335; 1, 2, 3, 4 for Lakeshore 336, 340.

For Lakeshore 325, 331, 332, 335 loop 1 is a control loop, while loop 2 is an analog output.

For Lakeshore 336, 340 loops 1, 2 are control loops, while loops 3, 4 are analog outputs (1 and 2 (or 3 and 4 for some models), respectively).

!!! note
    This function is not available for Scientific Instruments SCM10.

For Termodat-11M6, 13KX3 the loop should be specified as an argument. For Stanford Research PTC10 the name of the output channel should be specified as an argument. For instance, if the channel name is `'Heater'` one should use `tc_heater_power('Heater')`. In both cases one should use this function as follows:

### tc_heater_power(channel) { #tc_heater_power-channel }

```python
tc_heater_power('Heater')    # -> float
```

For Oxford Instruments ITC 503 the function returns only heater power as a percentage of the maximum power. In addition in the manual mode of ITC 503 this function allows to adjust the heater power by calling it with an argument between 0 and 99.9:

### tc_heater_power(*power_percent) { #tc_heater_power-power_percent }

```python
tc_heater_power()        # -> float (query)
tc_heater_power(50.0)    # set heater to 50 % of the power limit
```

The argument is the percentage of the heater power limit that can be set via [`tc_heater_power_limit()`](#tc_heater_power_limit). If the device is not in the manual or gas flow control mode a warning will be shown and the heater power remains unchanged.

**Range:** `0` – `99.9`
{: .enum }

---

### tc_heater_power_limit(power) { #tc_heater_power_limit data-toc-label="tc_heater_power_limit" }

```python
tc_heater_power_limit(10)    # set heater power limit to 10 V
```

This function is available only for Oxford Instruments ITC 503 and should be called with one argument. In the manual mode or when only the gas flow is controlled this function sets the maximum heater voltage that ITC 503 may deliver. If the device is not in manual or gas flow control mode a warning will be shown and the heater power remains unchanged.

It is not possible to query the heater power limit by calling this function without argument. To check the limit one should press and hold the recessed limit button. After that the heater man button should be pressed. The display will show approximate value of the heater limit in volts.

---

### tc_state(*mode) { #tc_state data-toc-label="tc_state" }

```python
tc_state()                   # -> str (query)
tc_state('Manual-Manual')    # heater manual, gas manual
```

This function can be used to change the state of the device and is available only for Oxford Instruments ITC 503. If an argument is specified the function sets a new state setting. If there is no argument the function returns the current state setting. The first part corresponds to the heater state setting, the second to the gas state setting.

**Allowed:** `'Manual-Manual'`, `'Auto-Manual'`, `'Manual-Auto'`, `'Auto-Auto'`
{: .enum }

---

### tc_sensor(*sensor) { #tc_sensor data-toc-label="tc_sensor" }

```python
tc_sensor()     # -> int (query)
tc_sensor(1)    # use sensor 1 (or 'A')
```

This function sets or queries the sensor that is used for active control of the temperature when comparing to the setpoint (target temperature). It may differ from the sensor used when calling [`tc_temperature()`](#tc_temperature). If an argument is specified the function sets a new sensor setting. If there is no argument the function returns the current sensor setting.

Generally not all sensor channels may be usable, there are models with different numbers of channels. Please, refer to the device manual.

For Lakeshore temperature controllers integer in the range of 1-4 corresponds respectively to the channels `'A'`-`'B'` (or `'A'`-`'D'` for Lakeshore 336). Also, for Lakeshore temperature controllers the control loop setting should be specified in the configuration file, since all the command use it as an internal argument. One can find more detail in the description of [`tc_heater_power()`](#tc_heater_power) function.

In case of Lakeshore 325, 331, 332, 340 the use of this function also sets setpoint unit to Kelvin, specifies that the control loop is off after power-up, and sets the heater output to display in power.

In case of Lakeshore 335 and 336 the use of this function also sets the control mode to closed loop PID and specifies that the control loop is off after power-up.

!!! note
    The function is not available for Stanford Research PTC10, Scientific
    Instruments SCM10.

For Termodat-11M6, 13KX3 this function sets or queries the state of specified sensor:

### tc_sensor(channel, *state) { #tc_sensor-channel }

```python
tc_sensor('1')          # -> str (query)
tc_sensor('1', 'On')    # enable channel 1 for active temperature control
```

If there is no state argument the function returns the current state for specified channel.

**Allowed state:** `'On'`, `'Off'`
{: .enum }

---

### tc_gas_flow(*flow) { #tc_gas_flow data-toc-label="tc_gas_flow" }

```python
tc_gas_flow()        # -> float (query)
tc_gas_flow(10.1)    # set gas flow to 10.1 arb. u.
```

This function is available only for Oxford Instruments ITC 503. It sets or queries the gas flow. If an argument is specified the function sets a new gas flow, that is the percentage of the maximum gas flow. If the device is not in manual or heater power control mode a warning will be shown and the heater power remains unchanged. If there is no argument the function returns the current gas flow.

**Range:** `0.0` – `99.9`
{: .enum }

---

### tc_lock_keyboard(*lock) { #tc_lock_keyboard data-toc-label="tc_lock_keyboard" }

```python
tc_lock_keyboard()                     # -> str (query)
tc_lock_keyboard('Remote-Unlocked')    # remote control, unlocked front panel
```

This function can be used to change the state of the device keyboard. If an argument is specified the function sets a new keyboard state setting. If there is no argument the function returns the current keyboard state setting. The first part corresponds to the device state, the second to the keyboard state. The default option is `'Remote-Unlocked'`.

Lakeshore temperature controllers use a 3-digit keypad lock code for locking and unlocking the keypad. The factory default code is 123. To unlock the keypad manually, press and hold the Enter key for 10 seconds. Function [`tc_lock_keyboard()`](#tc_lock_keyboard) uses this code automatically.

**Allowed:** `'Local-Locked'`, `'Remote-Locked'`, `'Local-Unlocked'`, `'Remote-Unlocked'`
{: .enum }

!!! note
    The function is not available for Termodat-11M6, 13KX3, Stanford
    Research PTC10, Scientific Instruments SCM10.

---

### tc_proportional(*prop) { #tc_proportional data-toc-label="tc_proportional" }

```python
tc_proportional('1')        # -> float (query)
tc_proportional('1', 71)    # set proportional PID for channel 1 to 71
```

This function is only available for Termodat-11M6, 13KX3 and can be used to set or query the proportional parameter of the PID. The function can be used with one or two arguments. The first argument specifies the channel. If there is a second argument, it will be used as a new proportional parameter. If there is no second argument, the function returns the current proportional parameter for the specified channel. The accuracy is 0.1.

**Range:** `0.1` – `2000`
{: .enum }

**Allowed channels (Termodat-11M6):** `'1'`, `'2'`, `'3'`, `'4'`
{: .enum }

**Allowed channels (Termodat-13KX3):** `'1'`, `'2'`
{: .enum }

---

### tc_derivative(*der) { #tc_derivative data-toc-label="tc_derivative" }

```python
tc_derivative('2')         # -> float (query)
tc_derivative('2', 100)    # set derivative PID for channel 2 to 100
```

This function is only available for Termodat-11M6, 13KX3 and can be used to set or query the derivative parameter of the PID. The function can be used with one or two arguments. The first argument specifies the channel. If there is a second argument, it will be used as a new derivative parameter. If there is no second argument, the function returns the current derivative parameter for the specified channel. The accuracy is 0.1. A zero value means that no derivative control is used.

**Range:** `0.1` – `2000`
{: .enum }

**Allowed channels (Termodat-11M6):** `'1'`, `'2'`, `'3'`, `'4'`
{: .enum }

**Allowed channels (Termodat-13KX3):** `'1'`, `'2'`
{: .enum }

---

### tc_integral(*integ) { #tc_integral data-toc-label="tc_integral" }

```python
tc_integral('1')         # -> int (query)
tc_integral('1', 600)    # set integral PID for channel 1 to 600
```

This function is only available for Termodat-11M6, 13KX3 and can be used to set or query the integral parameter of the PID. The function can be used with one or two arguments. The first argument specifies the channel. If there is a second argument, it will be used as a new integral parameter. If there is no second argument, the function returns the current integral parameter for the specified channel. The accuracy is 1. A zero value means that no integral control is used.

**Range:** `1` – `9999`
{: .enum }

**Allowed channels (Termodat-11M6):** `'1'`, `'2'`, `'3'`, `'4'`
{: .enum }

**Allowed channels (Termodat-13KX3):** `'1'`, `'2'`
{: .enum }

---

### tc_command(command) { #tc_command data-toc-label="tc_command" }

```python
# Note that for some controller models the loop should not be specified.
# Check the programming guide.
tc_command('PID 1, 10, 50, 0')
```

This function sends an arbitrary command from a programming guide to the device in a string format. No output is expected.

!!! note
    The function is not available for Termodat-11M6, 13KX3.

---

### tc_query(command) { #tc_query data-toc-label="tc_query" }

```python
# Note that for some controller models the loop should not be specified.
# Check the programming guide.
tc_query('PID? 1')
```

This function sends an arbitrary command from a programming guide to the device in a string format. An output in a string format is expected.

!!! note
    The function is not available for Termodat-11M6, 13KX3.
