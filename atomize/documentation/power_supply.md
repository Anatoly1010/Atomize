---
title: Power Supplies
nav_order: 33
layout: page
permlink: /functions/power_suuply/
parent: Documentation
---

### Devices

Available devices:
- Rigol **DP800** Series (RS-232, Ethernet); Tested 01/2021
- Stanford Research **DC205** (RS-232); Untested
- Stanford Research **PS300** High Voltage Series (RS-232, GPIB: linux-gpib); Untested

Please note, that since SR PS310 and PS325 have only GPIB interface, while SR PS350, PS355, PS365, PS370, PS375 have both RS-232 and GPIB, this setting should be specified in the configuration file:
```python
[SPECIFIC]
rs232 = yes
```

---

### Functions
- [power_supply_name()](#power_supply_name)<br/>
- [power_supply_voltage(\*voltage)](#power_supply_voltagevoltage)<br/>
- [power_supply_current(\*current)](#power_supply_currentcurrent)<br/>
- [power_supply_overvoltage(\*voltage)](#power_supply_overvoltagevoltage)<br/>
- [power_supply_overcurrent(\*current)](#power_supply_overcurrentcurrent)<br/>
- [power_supply_channel_state(\*state)](#power_supply_channel_statestate)<br/>
- [power_supply_measure(channel)](#power_supply_measurechannel)<br/>
- [power_supply_preset(preset)](#power_supply_presetpreset)<br/>
- [power_supply_range(\*range)](#power_supply_rangerange)<br/>
- [power_supply_interlock()](#power_supply_interlock)<br/>
- [power_supply_rear_mode(\*mode)](#power_supply_rear_modemode)<br/>
- [power_supply_command(command)](#power_supply_commandcommand)<br/>
- [power_supply_query(command)](#power_supply_querycommand)<br/>

---

### power_supply_name()
```python
power_supply_name() -> str
```
This function returns device name.<br/>

---

### power_supply_voltage(\*voltage)
```python
power_supply_voltage(*voltage)
power_supply_voltage(channel: str, voltage: float + [' kV',' V',' mV']') -> none
power_supply_voltage(channel: ['CH1','CH2','CH3']) -> str
```
```
Example: power_supply_voltage('CH1', '10 V') sets the voltage of the first channel to 10 V.
```
This function queries (if called with one argument) or sets (if called with two arguments) the voltage of one of the channels of the power supply. If there is a second argument it will be set as a new voltage. If there is no second argument the current voltage for specified the channel is returned in the format 'number + [' V', ' mV']'.<br/>
Note that this function returns the voltage setting of the instrument, not actual measured voltage. The latter can be achieved with [power_supply_measure()](#power_supply_measurechannel) function.<br/>
Rigol DP800 power supply series has ['V', 'mV'] as the scaling dictionary.<br/>
Stanford Research DC205 has only one channel, however, it should be listed as the first argument for consistency. Also, the available range of SR DC205 depends on the range setting. Check function [power_supply_range()](#power_supply_rangerange). Scaling dictionary is ['V', 'mV'].<br/>
Stanford Research PC300 high voltage supply series has only one channel, however, it should be listed as the first argument for consistency. Scaling dictionary is ['kV', 'V']. The value of voltage to set must match the polarity of the power supply.<br/>

---

### power_supply_current(\*current)
```python
power_supply_current(*current)
power_supply_current(channel: str, current: float + [' A', ' mA']') -> none
power_supply_current(channel: ['CH1','CH2','CH3']) -> str
```
```
Example: power_supply_current('CH2', '100 mA')
sets the current of the second channel to 100 mA.
```
This function queries (if called with one argument) or sets (if called with two arguments) the current of one of the channels of the power supply. If there is a second argument it will be set as a new current. If there is no second argument the current for specified the channel is returned in the format 'number + [' A', ' mA']'.<br/>
This function is only supported by Rigol DP800 Series.<br/>

---

### power_supply_overvoltage(\*voltage)
```python
power_supply_overvoltage(*voltage)
power_supply_overvoltage(channel: str, voltage: float + [' kV',' V',' mV']') -> none
power_supply_overvoltage(channel: ['CH1','CH2','CH3']) -> str
```
```
Example: power_supply_overvoltage('CH1', '30 V')
sets the overvoltage protection of the first channel to 30 V.
```
This function queries (if called with one argument) or sets (if called with two arguments) the overvoltage protection of one of the channels of the power supply. If there is a second argument it will be set as a new overvoltage protection setting. If there is no second argument the current overvoltage protection setting for specified the channel is returned in the format 'number + [' kV', ' V', ' mV']'.<br/>
Stanford Research PC300 high voltage supply series has only one channel, however, it should be listed as the first argument for consistency. The value of overvoltage (the voltage limit) to set must match the polarity of the power supply. The overvoltage value must be greater than or equal to the value indicated in [power_supply_voltage()](#power_supply_voltagevoltage) function.<br/>
This function is not supported by Stanford Research DC205.<br/>

---

### power_supply_overcurrent(\*current)
```python
power_supply_overcurrent(channel: str, current: float + [' A',' mA',' uA']') -> none
power_supply_overcurrent(channel: ['CH1','CH2','CH3']) -> str
```
```
Example: power_supply_overcurrent('CH1', '3 A')
sets the overcurrent protection of the first channel to 3 A.
```
This function queries (if called with one argument) or sets (if called with two arguments) the overcurrent protection of one of the channels of the power supply. If there is a second argument it will be set as a new overcurrent protection setting. If there is no second argument the current overcurrent protection setting for specified the channel is returned in the format 'number + [' A', ' mA', ' uA']'.<br/>
Stanford Research PC300 high voltage supply series has only one channel, however, it should be listed as the first argument for consistency. The overcurrent (the current limit) value may be set from 0 to 105 % of full scale.<br/>
This function is not supported by Stanford Research DC205.<br/>

---

### power_supply_channel_state(\*state)
```python
power_supply_channel_state(channel: str, state: ['On', 'Off']) -> none
power_supply_channel_state(channel: ['CH1','CH2','CH3']) -> str
```
```
Example: power_supply_channel_state('CH1', 'On') enables the output of the first channel.
```
This function queries (if called with one argument) or sets (if called with two arguments) the state of the output of one of the channels of the power supply. If there is a second argument it will be set as a new state setting. If there is no second argument the current state setting for the specified channel is returned.<br/>
The state argument should be 'On' or 'Off', which means that the output is enabled and disabled, respectively.<br/>
Stanford Research DC205 has only one channel, however, it should be listed as the first argument for consistency. For SR DC205 in case of using '100 V' range, the channel can be turned on only while the safety interlock is closed. See [power_supply_interlock()](#power_supply_interlock) function. If the safety interlock is open a warning will be shown and the state remains unchanged.<br/>
Stanford Research PC300 high voltage supply series has only one channel, however, it should be listed as the first argument for consistency. The setting 'On' turns the high voltage ON, provided the front-panel high voltage switch is not in the OFF position. Also this function cannot query the state of the high voltage supply.<br/>

---

### power_supply_measure(channel)
```python
power_supply_measure(channel: ['CH1','CH2','CH3']) -> list(2)
power_supply_measure(channel: ['CH1','CH2','CH3']) -> list(3)
```
```
Example: power_supply_measure('CH1') 
queries the voltage, current and power (optional) measured on the output terminal of the channel 1.
```
This function can be called only with one argument and queries the voltage, current and power measured on the output terminal of the specified channel. The function returns measured values in Volts, Amperes, Watts as a python list.<br/>
Stanford Research PC300 high voltage supply series has only one channel, however, it should be listed as the first argument for consistency. For these devices the function returns measured values in Volts and Amperes as a python list.<br/>
This function is not supported by Stanford Research DC205.<br/>

---

### power_supply_preset(preset)
```python
power_supply_preset(preset: ['Default','User1','User2','User3']) -> none
```
```
Example: power_supply_preset('User1') sets the preset settings with the name 'User1'.
```
This function can be called only with one argument and allows restoring the instrument to the default setting ('Default' argument) or recall the user-defined setting ('UserN' arguments).<br/>
This function is only supported by Rigol DP800 Series.<br/>

---

### power_supply_range(\*range)
```python
power_supply_range(range: ['1 V','10 V','100 V']) -> none
power_supply_range() -> str
```
```
Example: power_supply_range('10 V') sets the voltage range setting to 10 V.
```
This function is only supported by Stanford Research DC205 and allows to set or query the voltage range setting. If there is an argument it will be set as a new voltage range setting. If there is no argument the current voltage range setting is returned as a string.<br/> 
The argument should be from the following array: ['1 V', '10 V', '100 V'] and corresponds to one of the three range settings: ±1 V, ±10 V, or ±100 V.<br/>

---

### power_supply_interlock()
```python
power_supply_interlock() -> ['On', 'Off']
```
```
Example: power_supply_interlock() returns the interlock state ('On' or 'Off').
```
This function is only supported by Stanford Research DC205 and allows to query the interlock condition. The DC205 is designed with a safety interlock circuit that must be activated for the ±100 V output range to be enabled. To close the interlock, a low impedance circuit must be established between pins 1 and 2 of the rear-panel INTERLOCK header.<br/>

---

### power_supply_rear_mode(\*mode)
```python
power_supply_rear_mode(mode: ['Front', 'Rear']) -> none
power_supply_rear_mode() -> str
```
```
Example: power_supply_rear_mode('Front') 
sets the control of the voltage value by the front-panel setting.
```
This function is only supported by Stanford Research PS300 high voltage power supply series and allows to set or query the voltage setting mode.<br/>
The argument 'Front' means that the voltage value is controlled by the front-panel setting, while 'Rear' indicates that the output is controlled by the rear-panel VSET voltage control input. Note that changing the rear_mode value while the high voltage is ON causes the high voltage to be switched OFF.<br/>

---

### power_supply_command(command)
```python
power_supply_command(command: str) -> none
```
```
Example: power_supply_command(':APPL CH1,5,1')
This example sets the voltage and current of CH1
to 5V and 1A, respectively.
```
This function sends an arbitrary command from a programming guide to the device in a string format. No output is expected.<br/>

---

### power_supply_query(command)
```python
power_supply_query(command: str) -> str
```
```
Example: power_supply_query(':APPL? CH1')
This example queries the voltage and current setting values of CH1 
and the query returns CH1:30V/5A,5.000,1.0000.
```
This function sends an arbitrary command from a programming guide to the device in a string format. An output in a string format is expected.<br/>