# List of available functions for power supplies

Available devices:
- Rigol DP800 Series (RS-232, Ethernet); Tested 01/2021
- Stanford Research DC205 (RS-232); Untested
- Stanford Research PS300 High Voltage Series (RS-232, GPIB); Untested

Please note, that since SR PS310 and PS325 have only GPIB interface, while SR PS350, PS355, PS365, PS370, PS375 have both RS-232 and GPIB, this setting should be specified in the configuration file:
```python3
[SPECIFIC]
rs232 = yes
```

Functions:
- [power_supply_name()](#power_supply_name)<br/>
- [power_supply_voltage(*voltage)](#power_supply_voltagevoltage)<br/>
- [power_supply_current(*current)](#power_supply_currentcurrent)<br/>
- [power_supply_overvoltage(*voltage)](#power_supply_overvoltagevoltage)<br/>
- [power_supply_overcurrent(*current)](#power_supply_overcurrentcurrent)<br/>
- [power_supply_channel_state(*state)](#power_supply_channel_statestate)<br/>
- [power_supply_measure(channel)](#power_supply_measurechannel)<br/>
- [power_supply_preset(preset)](#power_supply_presetpreset)<br/>
- [power_supply_range(*range)](#power_supply_rangerange)<br/>
- [power_supply_interlock()](#power_supply_interlock)<br/>
- [power_supply_rear_mode(*mode)](#power_supply_rear_modemode)<br/>
- [power_supply_command(command)](#power_supply_commandcommand)<br/>
- [power_supply_query(command)](#power_supply_querycommand)<br/>

### power_supply_name()
```python3
power_supply_name()
Arguments: none; Output: string.
```
The function returns device name.
### power_supply_voltage(*voltage)
```python3
power_supply_voltage(*voltage)
Arguments: voltage = two strings ('channel string' ['CH1','CH2','CH3'], 'number + scaling ['kV', 'V', 'mV']')
or one string ('channel string'); Output: float (in V).
Example: power_supply_voltage('CH1', '10 V') sets the voltage of the first channel to 10 V.
```
The function queries (if called with one argument) or sets (if called with two arguments) the voltage of one of the channels of the power supply. If there is a second argument it will be set as a new voltage. If there is no second argument the current voltage for specified the channel is returned in Volts.<br/>
Note that this function returns the voltage setting of the instrument, not actual measured voltage. The latter can be achieved with [power_supply_measure()](#power_supply_measurechannel) function.<br/>
Rigol DP800 power supply series has ['V', 'mV'] as the scaling dictionary.<br/>
Stanford Research DC205 has only one channel, however, it should be listed as the first argument for consistency. Also, the available range of SR DC205 depends on the range setting. Check function [power_supply_range()](#power_supply_rangerange). Scaling dictionary is ['V', 'mV'].<br/>
Stanford Research PC300 high voltage supply series has only one channel, however, it should be listed as the first argument for consistency. Scaling dictionary is ['kV', 'V']. The value of voltage to set must match the polarity of the power supply.
### power_supply_current(*current)
```python3
power_supply_current(*current)
Arguments: current = two strings ('channel string' ['CH1','CH2','CH3'], 'number + scaling ['A', 'mA']')
or one string ('channel string'); Output: float (in A).
Example: power_supply_current('CH2', '100 mA') sets the current of the second channel to 100 mA.
```
The function queries (if called with one argument) or sets (if called with two arguments) the current of one of the channels of the power supply. If there is a second argument it will be set as a new current. If there is no second argument the current for specified the channel is returned in Ampers.<br/>
This function is only supported by Rigol DP800 Series.
### power_supply_overvoltage(*voltage)
```python3
power_supply_overvoltage(*voltage)
Arguments: voltage = two strings ('channel string' ['CH1','CH2','CH3'], 'number + scaling ['kV', 'V', 'mV']')
or one string ('channel string'); Output: float (in V).
Example: power_supply_overvoltage('CH1', '30 V') sets the overvoltage protection of the first channel to 30 V.
```
The function queries (if called with one argument) or sets (if called with two arguments) the overvoltage protection of one of the channels of the power supply. If there is a second argument it will be set as a new overvoltage protection setting. If there is no second argument the current overvoltage protection setting for specified the channel is returned in Volts.<br/>
Rigol DP800 power supply series has ['V', 'mV'] as the scaling dictionary.<br/>
Stanford Research PC300 high voltage supply series has only one channel, however, it should be listed as the first argument for consistency. The value of overvoltage (the voltage limit) to set must match the polarity of the power supply. The overvoltage value must be greater than or equal to the value indicated in [power_supply_voltage()](#power_supply_voltagevoltage) function. Scaling dictionary is ['kV', 'V'].<br/>
This function is not supported by Stanford Research DC205.
### power_supply_overcurrent(*current)
```python3
power_supply_overcurrent(*current)
Arguments: voltage = two strings ('channel string' ['CH1','CH2','CH3'], 'number + scaling ['A', 'mA', 'uA']')
or one string ('channel string'); Output: float (in A).
Example: power_supply_overcurrent('CH1', '3 A') sets the overcurrent protection of the first channel to 3 A.
```
The function queries (if called with one argument) or sets (if called with two arguments) the overcurrent protection of one of the channels of the power supply. If there is a second argument it will be set as a new overcurrent protection setting. If there is no second argument the current overcurrent protection setting for specified the channel is returned.<br/>
Rigol DP800 power supply series has ['A', 'mA'] as the scaling dictionary. The function returns the overcurrent setting in A.<br/>
Stanford Research PC300 high voltage supply series has only one channel, however, it should be listed as the first argument for consistency. The overcurrent (the current limit) value may be set from 0 to 105 % of full scale. Scaling dictionary is ['mA', 'uA']. The function returns the overcurrent setting in uA.<br/>
This function is not supported by Stanford Research DC205.
### power_supply_channel_state(*state)
```python3
power_supply_channel_state(*state)
Arguments: state = two strings ('channel string' ['CH1','CH2','CH3'], 'state ['On', 'Off']')
or one string ('channel string'); Output: string.
Example: power_supply_channel_state('CH1', 'On') enables the output of the first channel.
```
The function queries (if called with one argument) or sets (if called with two arguments) the state of the output of one of the channels of the power supply. If there is a second argument it will be set as a new state setting. If there is no second argument the current state setting for the specified channel is returned.<br/>
The state argument should be 'On' or 'Off', which means that the output is enabled and disabled, respectively.<br/>
Stanford Research DC205 has only one channel, however, it should be listed as the first argument for consistency. For SR DC205 in case of using '100 V' range, the channel can be turned on only while the safety interlock is closed. See [power_supply_interlock()](#power_supply_interlock) function. If the safety interlock is open a warning will be shown and the state remains unchanged.<br/>
Stanford Research PC300 high voltage supply series has only one channel, however, it should be listed as the first argument for consistency. The setting 'On'  turns the high voltage ON, provided the front-panel high voltage switch is not in the OFF position. Also this function cannot query the state of the high voltage supply.
### power_supply_measure(channel)
```python3
power_supply_measure(channel)
Arguments: channel = string ('channel string' ['CH1','CH2','CH3']); Output: array of values.
Example: power_supply_measure('CH1') queries the voltage, current and power (optional) measured on the output 
terminal of the channel 1.
```
The function can be called only with one argument and queries the voltage, current and power measured on the output terminal of the specified channel. The function returns measured values in Volts, Ampers, Watts separeted by commas.<br/>
Stanford Research PC300 high voltage supply series has only one channel, however, it should be listed as the first argument for consistency. For these devices the function returns measured values in Volts and Ampers separeted by commas.<br/>
This function is not supported by Stanford Research DC205.
### power_supply_preset(preset)
```python3
power_supply_preset(preset)
Arguments: preset = string ('preset string' ['Default','User1','User2','User3']); Output: none.
Example: power_supply_preset('User1') sets the preset settings with the name 'User1'.
```
The function can be called only with one argument and allows restoring the instrument to the default setting ('Default' argument) or recall the user-defined setting ('UserN' arguments).<br/>
This function is only supported by Rigol DP800 Series.
### power_supply_range(*range)
```python3
power_supply_range(*range)
Arguments: range = string ('range string' ['1 V','10 V','100 V']); Output: string.
Example: power_supply_range('10 V') sets the voltage range setting to 10 V.
```
This function is only supported by Stanford Research DC205 and allows to set or query the voltage range setting. If there is an argument it will be set as a new voltage range setting. If there is no argument the current voltage range setting is returned as a string.<br/> 
The argument should be from the following array: ['1 V', '10 V', '100 V'] and 
corredponds to one of the three range settings: ±1 V, ±10 V, or ±100 V.
### power_supply_interlock()
```python3
power_supply_interlock()
Arguments: none; Output: string.
Example: power_supply_interlock() returns the interlock state ('On' or 'Off').
```
This function is only supported by Stanford Research DC205 and allows to query the interlock condition. The DC205 is designed with a safety interlock circuit that must be activated for the ±100 V output range to be enabled. To close the interlock, a low impedance circuit must be established between pins 1 and 2 of the rear-panel INTERLOCK header.
### power_supply_rear_mode(*mode)
```python3
power_supply_rear_mode(*mode)
Arguments: string (['Front', 'Rear']); Output: string.
Example: power_supply_rear_mode('Front') sets the control of the voltage value by
the front-panel setting.
```
This function is only supported by Stanford Research PS300 high voltage power supply series and allows to set or query the voltage setting mode. 
The argument 'Front' means that the voltage value is controlled by the front-panel setting, while 'Rear' indicates that the output is controlled by the rear-panel VSET voltage control input. Note that changing the rear_mode value while the high voltage is ON causes the high voltage to be switched OFF.
### power_supply_command(command)
```python3
power_supply_command(command)
Arguments: command = string; Output: none.
Example: power_supply_command(':APPL CH1,5,1'). This example sets the voltage and current of CH1
to 5V and 1A, respectively.
```
The function for sending an arbitrary command from a programming guide to the device in a string format. No output is expected.<br/>
### power_supply_query(command)
```python3
power_supply_query(command)
Arguments: command = string; Output: string.
Example: power_supply_query(':APPL? CH1'). This example queries the voltage and current setting values of CH1 
and the query returns CH1:30V/5A,5.000,1.0000.
```
The function for sending an arbitrary command from a programming guide to the device in a string format. An output in a string format is expected.<br/>
