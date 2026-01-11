---
title: Temperature Controllers
nav_order: 37
layout: page
permlink: /functions/temp_controller/
parent: Documentation
---

### Devices

- Lakeshore (GPIB, RS-232)
**325**; **331**; **332**; **335**; **336**; **340**; Tested 01/2021
- Oxford Instruments (RS-232)
**ITC 503**; Tested 01/2021
- Termodat (RS-485)
**11M6**; **13KX3**; Tested 04/2021
- Stanford Research (TCP/IP Socket)
**PTC10**; Tested 07/2021
- Scientific Instruments (TCP/IP Socket, RS-232)
**SCM10**; Tested 07/2022

---

### Functions
- [tc_name()](#tc_name)<br/>
- [tc_temperature(channel)](#tc_temperaturechannel)<br/>
- [tc_setpoint(*temp)](#tc_setpointtemp)<br/>
- [tc_setpoint(channel, *temp)](#tc_setpointchanneltemp)<br/>
- [tc_heater_range(*heater)](#tc_heater_rangeheater)<br/>
- [tc_heater_power()](#tc_heater_power)<br/>
- [tc_heater_power(channel)](#tc_heater_powerchannel)<br/>
- [tc_heater_power(*power_percent)](#tc_heater_powerpower_percent)<br/>
- [tc_heater_power_limit(power)](#tc_heater_power_limitpower)<br/>
- [tc_state(*mode)](#tc_statemode)<br/>
- [tc_sensor(*sensor)](#tc_sensorsensor)<br/>
- [tc_sensor(channel, *state)](#tc_sensorchannelstate)<br/>
- [tc_gas_flow(*flow)](#tc_gas_flowflow)<br/>
- [tc_lock_keyboard(*lock)](#tc_lock_keyboardlock)<br/>
- [tc_proportional(*prop)](#tc_proportionalprop)<br/>
- [tc_derivative(*der)](#tc_derivativeder)<br/>
- [tc_integral(*integ)](#tc_integralinteg)<br/>
- [tc_command(command)](#tc_commandcommand)<br/>
- [tc_query(command)](#tc_querycommand)<br/>

---

### tc_name()
```python
tc_name() -> str
```
This function returns device name.<br/>

---

### tc_temperature(channel)
```python
tc_temperature(channel: str) -> float
```
```
Example: tc_temperature('A') returns the temperature of channel A in Kelvin.
```
This function is for reading temperature from the specified channel.<br/>
Note that arguments can be devices specific. A set of ['A','B'] is used for Lakeshore 325, 331, 332, and 335, while for Lakeshore 336, 340 a set of four channel ['A','B','C','D'] is used.<br/>
For Oxford Instruments ITC 503 channel should be one from the following: ['1', '2', '3']. Only tc_temperature('1') is valid, tc_temperature(1) are not valid. Note that there are models with different numbers of channels. Please, refer to the manual and specify this setting in the configuration file.<br/>
For Termodat-11M6 channel should be one from the following: ['1', '2', '3', '4']. For Termodat-13KX3 channel should be one from the following: ['1', '2'].  Note that there are models with different numbers of channels. Please, refer to the manual and specify this setting in the configuration file.<br/>
For Stanford Research PTC10 an argument of the function tc_temperature() should have the name of the channel. For instance, if the channel name is 2A one should use tc_temperature('2A') in order to get the temperature.<br/>
For Scientific Instruments SCM10 the only available argument is '1'.<br/>

---

### tc_setpoint(*temp)
```python
tc_setpoint(temp: float) -> none
tc_setpoint() -> float
```
```
Example: tc_setpoint(100) changes the set point of the specified loop to 100 Kelvin.
```
This function queries or changes the set point, i.e. the target temperature the device will try to achieve and maintain. If an argument is specified the function sets a new temperature point. If there is no argument the function returns the current set point. A loop can be specified in the configuration file.<br/>
This function is not available for Scientific Instruments SCM10.<br/>
For Termodat-11M6, 13KX3 and Stanford Research PTC10 the channel for which the set point is to be set should be specified as an agrument of the following function: 

### tc_setpoint(channel, *temp)
```python
tc_setpoint(channel: str, temp: float) -> none
tc_setpoint(channel: str) -> float
```
```
Example: tc_setpoint('2', 100) changes the set point of the second channel to 100 Kelvin.
```
An accuracy of the set point setting is 0.1 degree. The number of available channels should be specified in the configuration file. If there is no temperature argument the function returns the current set point for specified channel. For Termodat-11M6 channel should be one from the following: ['1', '2', '3', '4']. For Termodat-13KX3 channel should be one from the following: ['1', '2']. Note that there are models with different numbers of channels. Please, refer to the manual and specify this setting in the configuration file.<br/>
For Stanford Research PTC10 a channel argument should have the name of the output channel. For instance, if the channel name is 'Heater' one should use tc_setpoint('Heater', 80) in order to set the desired temperature.<br/>

---

### tc_heater_range(*heater)
```python
tc_heater_range(heater: str) -> none
tc_heater_range() -> str
```
```
Example: tc_heater_range('50 W') changes the heater range to 50 W (High).
```
This function queries or sets the heater range. If an argument is specified the function sets a new heater range. If there is no argument the function returns the current heater range.<br/>
The function is available only for Lakeshore temperature controllers. For Oxford Instrument ITC 503 [tc_heater_power_limit()](#tc_heater_power_limitpower) fucntion should be used instead.<br/>
Note that arguments are devices specific. Currently a set of ['50 W', '5 W', '0.5 W', 'Off'] can be used for Lakeshore 331, 332, 335, while for Lakeshore 340 a set ['10 W', '1 W', 'Off'] is used.<br/>
For Lakeshore 336 a loop 1 or 2 can be used with a set of ['50 W', '5 W', '0.5 W', 'Off']. The loop 3 and 4 can be used only with ['On', 'Off'] setting.<br/>
For Lakeshore 325 a loop 1 can be used with a set of ['25 W', '2.5 W', 'Off']. The loop 2 can be used only with ['On', 'Off'] setting.<br/>
The values '50 W', '5 W', and '0.5 W' are shown as High, Medium, and Low on the device display. The exact values depends on the resistance used.<br/>
This function is not available for Termodat-11M6, 13KX3, Stanford Research PTC10, Scientific Instruments SCM10.<br/>

---

### tc_heater_power()
```python
tc_heater_power() -> [str, float]
```
```
Example: tc_heater() returns the array of the heater range and heater percent.
```
This function is for reading the current heater value in percent for the specified loop. The loop config (should be indicated in the configuration file) can be: 1, 2 for Lakeshore 325, 331, 332, 335; 1, 2, 3, 4 for Lakeshore 336, 340.<br/>
For Lakeshore 325, 331, 332, 335 loop 1 is a control loop, while loop 2 is an analog output.<br/>
For Lakeshore 336, 340 loops 1, 2 are control loops, while loops 3, 4 are analog outputs (1 and 2 (or 3 and 4 for some models), respectively).<br/>
This function is not available for Scientific Instruments SCM10.<br/>
For Termodat-11M6, 13KX3 the loop should be specified as an argument. For Stanford Research PTC10 the name of the output channel should be specified as an argument. For instance, if the channel name is 'Heater' one should use tc_heater_power('Heater'). In both cases one should use this function as follows:<br/>

---

### tc_heater_power(channel)
```python
tc_heater_power(channel: str) -> float
```
For Oxford Instruments ITC 503 the function returns only heater power as a percentage of the maximum power. In addition in the manual mode of ITC 503 this function allows to adjust the heater power by calling it with an argument between 0 and 99.9:

### tc_heater_power(*power_percent)
```python
tc_heater_power(power_percent: float) -> none
tc_heater_power() -> float
```
The argument is the percentage of the heater power limit that can be set via [tc_heater_power_limit()](#tc_heater_power_limitpower). If the device is not in the manual or gas flow control mode a warning will be shown and the heater power remains unchanged.<br/>

---

### tc_heater_power_limit(power)
```python
tc_heater_power_limit(power: int) -> none
```
```
Example: tc_heater_power_limit(10) sets the heater power to 10 V.
```
This function is available only for Oxford Instruments ITC 503 and should be called with one argument. In the manual mode or when only the gas flow is controlled this function sets the maximum heater voltage that ITC 503 may deliver. If the device is not in manual or gas flow control mode a warning will be shown and the heater power remains unchanged.<br/>
It is not possible to query the heater power limit by calling this function without argument. To check the limit one should press and hold the recessed limit button. After that the heater man button should be pressed. The display will show approximate value of the heater limit in volts.<br/>

---

### tc_state(*mode)
```python
tc_state(mode: str) -> none
tc_state() -> str
```
```
Example: tc_state('Manual-Manual') sets the device to heater manual, gas manual state.
```
This function can be used to change the state of the device and is available only for Oxford Instruments ITC 503. If an argument is specified the function sets a new state setting. If there is no argument the function returns the current state setting.<br/>
The state should be one of the following: ['Manual-Manual', 'Auto-Manual', ' Manual-Auto', 'Auto-Auto'].<br/>
The first part corresponds to the heater state setting, the second to the gas state setting.<br/>

---

### tc_sensor(*sensor)
```python
tc_sensor(sensor: int) -> none
tc_sensor() -> int
```
```
Example: tc_sensor(1) sets the sensor to 1 (or 'A').
```
This function sets or queries the sensor that is used for active control of the temperature when comparing to the setpoint (target temperature). It may differ from the sensor used when calling [tc_temperature()](#tc_temperaturechannel). If an argument is specified the function sets a new sensor setting. If there is no argument the function returns the current sensor setting.<br/>
Generally not all sensor channels may be usable, there are models with different numbers of channels. Please, refer to the device manual.<br/>
The function is not available for Stanford Research PTC10, Scientific Instruments SCM10.<br/>
For Lakeshore temperature controllers integer in the range of 1-4 corresponds respectively to the channels 'A'-'B' (or 'A'-'D' for Lakeshore 336). Also, for Lakeshore temperature controllers the control loop setting should be specified in the configuration file, since all the command use it as an internal argument. One can find more detail in the description of [tc_heater_power()](#tc_heater_power) function.<br/>
In case of Lakeshore 325, 331, 332, 340 the use of this function also sets setpoint unit to Kelvin, specifies that the control loop is off after power-up, and sets the heater output to display in power.<br/>
In case of Lakeshore 335 and 336 the use of this function also sets the control mode to closed loop PID and specifies that the control loop is off after power-up.<br/>
For Termodat-11M6, 13KX3 this function sets or queries the state of specified sensor:

### tc_sensor(channel, *state)
```python
tc_sensor(channel: str, state: ['On','Off']) -> none
tc_sensor(channel: str) -> str
```
```
Example: tc_sensor('1', 'On') changes the state of the second channel to 'On'.
The second channel will be used for the active control of the temperature.
```
If there is no state argument the function returns the current state for specified channel.<br/>

---

### tc_gas_flow(*flow)
```python
tc_gas_flow(flow: float) -> none
tc_gas_flow() -> float
```
```
Example: tc_gas_flow(10.1) sets the gas flow to 10.1 arb. u.
```
This function is available only for Oxford Instruments ITC 503. It sets or queries the gas flow. If an argument, a value between 0.0 and 99.9, is specified the function sets a new gas flow, that is the percentage of the maximum gas flow. If the device is not in manual or heater power control mode a warning will be shown and the heater power remains unchanged. If there is no argument the function returns the current gas flow.<br/>

---

### tc_lock_keyboard(*lock)
```python
tc_lock_keyboard(lock: str) -> none
tc_lock_keyboard() -> str
```
```
Example: tc_lock_keyboard('Remote-Unlocked') sets the device to remote state with 
unlocked front panel.
```
This function can be used to change the state of the device keyboard. If an argument is specified the function sets a new keyboard state setting. If there is no argument the function returns the current keyboard state setting.<br/>
The state should be one of the following: ['Local-Locked', 'Remote-Locked', 'Local-Unlocked', 'Remote-Unlocked'].<br/>
The first part corresponds to the device state, the second to the keyboard state. The default option is 'Remote-Unlocked'.<br/>
Lakeshore temperature controllers use a 3-digit keypad lock code for locking and unlocking the keypad. The factory default code is 123. To unlock the keypad manually, press and hold the Enter key for 10 seconds. Function [tc_lock_keyboard()](#tc_lock_keyboardlock) uses this code automatically.<br/>
The function is not available for Termodat-11M6, 13KX3, Stanford Research PTC10, Scientific Instruments SCM10.<br/>

---

### tc_proportional(*prop)
```python
tc_proportional(channel: str, proportional: float) -> none
tc_proportional(channel: str) -> float
```
```
Example: tc_proportional('1', 71) sets the proportional PID parameter for the first channel to 71.
```
This function is only available for Termodat-11M6, 13KX3 and can be used to set or query the proportional parameter of the PID. The function can be used with one or two arguments. The first argument specifies the channel. If there is a second argument, it will be used as a new proportional parameter. If there is no second argument, the function returns the current proportional parameter for the specified channel. The accuracy is 0.1. The available range is 0.1 - 2000. For Termodat-11M6 channel should be one from the following: ['1', '2', '3', '4']. For Termodat-13KX3 channel should be one from the following: ['1', '2'].<br/>

---

### tc_derivative(*der)
```python
tc_derivative(channel: str, derivative: float) -> none
tc_derivative(channel: str) -> float
```
```
Example: tc_derivative('2', 100) sets the derivative PID parameter for the second channel to 100.
```
This function is only available for Termodat-11M6, 13KX3 and can be used to set or query the derivative parameter of the PID. The function can be used with one or two arguments. The first argument specifies the channel. If there is a second argument, it will be used as a new derivative parameter. If there is no second argument, the function returns the current derivative parameter for the specified channel. The accuracy is 0.1. The available range is 0.1 - 2000. A zero value means that no derivative control is used. For Termodat-11M6 channel should be one from the following: ['1', '2', '3', '4']. For Termodat-13KX3 channel should be one from the following: ['1', '2'].<br/>

---

### tc_integral(*integ)
```python
tc_integral(channel: str, integral: int) -> none
tc_integral(channel: str) -> int
```
```
Example: tc_integral('1', 600) sets the integral PID parameter for the first channel to 600.
```
This function is only available for Termodat-11M6, 13KX3 and can be used to set or query the integral parameter of the PID. The function can be used with one or two arguments. The first argument specifies the channel. If there is a second argument, it will be used as a new integral parameter. If there is no second argument, the function returns the current integral parameter for the specified channel. The accuracy is 1. The available range is 1 - 9999. A zero value means that no integral control is used. For Termodat-11M6 channel should be one from the following: ['1', '2', '3', '4']. For Termodat-13KX3 channel should be one from the following: ['1', '2'].<br/>

---

### tc_command(command)
```python
tc_command(command: str) -> none
```
```
Example: tc_command('PID 1, 10, 50, 0'). Note that for some controller models the loop should not 
be specified. Check the programming guide.
```
This function sends an arbitrary command from a programming guide to the device in a string format. No output is expected. The function is not available for Termodat-11M6, 13KX3.<br/>

---

### tc_query(command)
```python
tc_query(command: str) -> str
```
```
Example: tc_query('PID? 1'). Note that for some controller models the loop should not be specified.
Check the programming guide.
```
This function sends an arbitrary command from a programming guide to the device in a string format. An output in a string format is expected. The function is not available for Termodat-11M6, 13KX3.<br/>
