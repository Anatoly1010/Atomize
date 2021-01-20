# List of available functions for temperature controllers
```python3
tc_name()
Arguments: none; Output: string.
```
This function returns device name.
```python3
tc_temperature(channel)
Arguments: channel = 'A' or 'B' (shown as ['A','B'] further); Output: float.
Example: tc_temperature('A') returns the temperature of channel A in Kelvin.
```
This function is for reading temperature from specified channel.<br/>
Note that arguments can be devices specific. A set of ['A','B'] is used for Lakeshore 325, 331, 332, and 335, while for Lakeshore 336, 340 a set of four channel ['A','B','C','D'] is used.<br/>
For Oxford Instruments ITC 503 channel should be one from the following: ['1', '2', '3']. Only tc_temperature('1') is valid, not tc_temperature(1) are valid. Note that there are models with different numbers of channels. Please, refer to manual.<br/>
```python3
tc_setpoint(*temp)
Arguments: temp = float; Output: float or none.
Example: tc_setpoint('100') changes the set point of the specified loop to 100 Kelvin.
```
This function queries or changes the set point, i.e. the target temperature the device will try to achieve and maintain. If an argument is specified the function sets a new temperature point. If there is no argument the function returns the current set point. A loop can be specified in configuration file.<br/>
```python3
tc_heater_range(*heater)
Arguments: heater = string; Output: string or none.
Example: tc_heater_range('50 W') changes the heater range to 50 W (High).
```
This function queries or sets the heater range. If an argument is specified the function sets a new heater range. If there is no argument the function returns the current heater range.<br/>
The function is available only for Lakeshore temperature controllers. For Oxford Instrument ITC 503 tc_heater_power_limit() fucntion should be used instead.<br/>
Note that arguments are devices specific. Currently a set of ['50 W','5 W','0.5 W','Off'] can be used for Lakeshore 331, 332, 335, while for Lakeshore 340 a set ['10 W','1 W','Off'] is used.<br/>
For Lakeshore 336 a loop 1 or 2 can be used with a set of ['50 W','5 W','0.5 W','Off']. The loop 3 and 4 can be used only with ['On','Off'] set.<br/>
For Lakeshore 325 a loop 1 can be used with a set of ['25 W','2.5 W','Off']. The loop 2 can be used only with ['On','Off'] set.<br/>
The values '50 W', '5 W', and '0.5 W' are shown as High, Medium, and Low on the device display. The exact values depends on the resistance used.<br/>
```python3
tc_heater_power()
Arguments: none; Output: array([string(heater_range), float(heater_percent)]).
Example: tc_heater() returns the array of the heater range and heater percent.
```
This function is for reading the current heater value in percent for the specified loop. The loop config (should be indicated in the configuration file) can be: 1, 2 for Lakeshore 325, 331, 332, 335; 1, 2, 3, 4 for Lakeshore 336, 340.<br/>
For Lakeshore 325, 331, 332, 335  loop 1 is a control loop, while loop 2 is an analog output.<br/>
For Lakeshore 336, 340 loop 1, 2 are control loops, while loop 3, 4 are analog outputs (1 and 2 (or 3 and 4 for some models), respectively).<br/>
For Oxford Instruments ITC 503 in manual mode this function allows to adjust the heater power by calling it with an argument between 0 and 99.9:
```python3
tc_heater_power(*power_percent)
Arguments: power_percent = decimal (0 - 99.9); Output: decimal.
```
The argument is the percentage of the heater power limit that can be set via tc_heater_power_limit(). If the device isn't in manual or gas flow control mode a warning will be shown and the heater power remains unchanged.
```python3
tc_heater_power_limit(power)
Arguments: power = decimal (0 - 40 corresponds to Volts ); Output: none.
Example: tc_heater_power_limit(10) sets the heater power to 10 V.
```
This function is available only for Oxford Instruments ITC 503 and should be called with one argument. In manual mode or when only the gas flow is controlled this function sets the maximum heater voltage that ITC 503 may deliver. If the device isn't in manual or gas flow control mode a warning will be shown and the heater power remains unchanged.<br/>
It is not possible to query the heater power limit by calling this function without argument. To check the limit one should press and hold the recessed limit button. After that the heater man button shpuld be pressed. The display will show approximate value of the heater limit in volts. 
```python3
tc_state(*mode)
Arguments: mode = string; Output: string.
Example: tc_state('Manual-Manual') sets the device to heater manual, gas manual state.
```
This function can be used to change the state of the device and is available only for Oxford Instruments ITC 503. If an argument is specified the function sets a new state setting. If there is no argument the function returns the current state setting. The state should be one of the following:
['Manual-Manual', 'Auto-Manual', ' Manual-Auto', 'Auto-Auto']<br/>
The first part corresponds to the heater state setting, the second to the gas state setting.
```python3
tc_sensor(*sensor)
Arguments: sensor = integer (1 - 3); Output: integer.
Example: tc_sensor(1) sets the sensor to 1 (or 'A').
```
This function sets or queries the sensor that is used for active control of the temperature when comparing to the setpoint (target temperature). It may differ from the sensor used when calling tc_temperature(). If an argument is specified the function sets a new sensor setting. If there is no argument the function returns the current sensor setting.<br/>
Generally not all sensor channels may be usable, there are models with different numbers of channels. Please, refer to device manual.<br/>
For Lakeshore temperature controllers integers 1-4 corresponds respectively to tha channels 'A'-'B' (or 'A'-'D' for Lakeshore 336). Also, for Lakeshore temperature controllers the control loop setting should be specified in the configuration file, since all the command use it as an internal argument. One can find more detail in the description of tc_heater_power() function.<br/>
In case of Lakeshore 325, 331, 332, 340 querying of this function also sets setpoint unit to Kelvin, specifies that the control loop is off after power-up, and sets the heater output to display in power.<br/>
In case of Lakeshore 335 and 336 querying of this function also sets the control mode to closed loop PID and specifies that the control loop is off after power-up.
```python3
tc_gas_flow(*flow)
Arguments: flow = decimal (0 - 99.9); Output: decimal.
Example: tc_gas_flow(10.1) sets the gas flow to 10.1 arb. u.
```
This function is available only for Oxford Instruments ITC 503. It sets or queries the gas flow. If an argument, a value between 0.0 and 99.9, is specified the function sets a new gas flow, that is the percentage of the maximum gas flow. If the device is not in manual or heater power control mode a warning will be shown and the heater power remains unchanged. If there is no argument the function returns the current gas flow.
```python3
tc_lock_keyboard(*lock)
Arguments: lock = string; Output: string.
Example: tc_lock_keyboard('Remote-Unlocked') sets the device to remote state with unlocked front panel.
```
This function can be used to change the state of the device keyboard. If an argument is specified the function sets a new keyboard state setting. If there is no argument the function returns the current keyboard state setting. The state should be one of the following:<br/>
['Local-Locked', 'Remote-Locked', 'Local-Unlocked', 'Remote-Unlocked']<br/>
The first part corresponds to the device state, the second to the keyboard state. The default option is 'Remote-Unlocked'.<br/>
Lakeshore temperature controllers use a 3-digit keypad lock code for locking and unlocking the keypad. The factory default code is 123. To unlock the keypad manually, press and hold the Enter key for 10 seconds. Function tc_lock_keyboard uses this code automatically.
```python3
tc_command(command)
Arguments: command = string; Output: none.
Example: tc_command('PID 1,10,50,0'). Note that for some controller models
the loop should not be specified. Check the programming guide.
```
The function for sending an arbitrary command from a programming guide to the device in a string format. No output is expected.<br/>
```python3
tc_query(command)
Arguments: command = string; Output: string.
Example: tc_command('PID? 1'). Note that for some controller models the loop
should not be specified. Check the programming guide.
```
The function for sending an arbitrary command from a programming guide to the device in a string format. An output in a string format is expected.<br/>

