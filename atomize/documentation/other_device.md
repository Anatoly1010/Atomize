---
title: Other devices
nav_order: 100
layout: page
permlink: /functions/other_device/
parent: Documentation
---

### Devices
- CPWplus **150**  Balance (RS-232); Tested 01/2021
- RODOS **10N** Solid-State Relay (Ethernet); Tested 01/2021
- Owen **MK110-220.4DN.4R** (RS-485) Discrete IO Module; Tested 04/2021
- Cryomagnetics **LM-510** Liquid Cryogen Monitor (TCP/IP Socket); Tested 07/2022
- Cryomech **CPA2896**, **CPA1110** Digital Panels (RS-485); Tested 07/2022
    
---

### Functions
- [balance_weight()](#balance_weight)<br/>
- [relay_turn_on(number)](#turn_onnumber)<br/>
- [relay_turn_off(number)](#turn_offnumber)<br/>
- [discrete_io_input_counter(channel)](#discrete_io_input_counterchannel)<br/>
- [discrete_io_input_counter_reset(channel)](#discrete_io_input_counter_resetchannel)<br/>
- [discrete_io_input_state()](#discrete_io_input_state)<br/>
- [discrete_io_output_state(\*state)](#discrete_io_output_statestate)<br/>
- [cryogenic_refrigerator_name()](#cryogenic_refrigerator_name)<br/>
- [cryogenic_refrigerator_state(\*state)](#cryogenic_refrigerator_statestate)<br/>
- [cryogenic_refrigerator_status_data()](#cryogenic_refrigerator_status_data)<br/>
- [cryogenic_refrigerator_warning_data()](#cryogenic_refrigerator_warning_data)<br/>
- [cryogenic_refrigerator_pressure_scale()](#cryogenic_refrigerator_pressure_scale)<br/>
- [cryogenic_refrigerator_temperature_scale()](#cryogenic_refrigerator_temperature_scale)<br/>
- [level_monitor_name()](#level_monitor_name)<br/>
- [level_monitor_select_channel(\*channel)](#level_monitor_select_channelchannel)<br/>
- [level_monitor_boost_mode(\*mode)](#level_monitor_boost_modemode)<br/>
- [level_monitor_high_level_alarm(\*level)](#level_monitor_high_level_alarmlevel)<br/>
- [level_monitor_low_level_alarm(\*level)](#level_monitor_low_level_alarmlevel)<br/>
- [level_monitor_sensor_length()](#level_monitor_sensor_length)<br/>
- [level_monitor_sample_mode(\*mode)](#level_monitor_sample_modemode)<br/>
- [level_monitor_units(\*units)](#level_monitor_unitsunits)<br/>
- [level_monitor_measure(channel)](#level_monitor_measurechannel)<br/>
- [level_monitor_sample_interval(\*interval)](#level_monitor_sample_intervalinterval)<br/>
- [level_monitor_hrc_target_pressure(\*pressure)](#level_monitor_hrc_target_pressurepressure)<br/>
- [level_monitor_hrc_heater_power_limit(\*limit)](#level_monitor_hrc_heater_power_limitlimit)<br/>
- [level_monitor_hrc_heater_enable(\*state)](#level_monitor_hrc_heater_enablestate)<br/>
- [level_monitor_command(command)](#level_monitor_commandcommand)<br/>
- [level_monitor_query(command)](#level_monitor_querycommand)<br/>

---

### Balance
### balance_weight()
```python
balance_weight() -> float
```
```
Example: balance_weight() returns the current weight of the balances.
```
This function returns the current weight of the balances and should be called with no argument.<br>

---

### Other
### Rodos 10N Solid-State Relay (Ethernet)
### relay_turn_on(number)
```python
relay_turn_on(number: int) -> none
```
```
Example: relay_turn_on(1) turns on the first channel of solid-state relay.
```
This function turns on the specified channel of the solid-state relay and should be called with one argument. Channel should be specified as integer in the range of 1 to 4.<br>

---

### relay_turn_off(number)
```python
relay_turn_off(number: int) -> none
```
```
Example: relay_turn_off(2) turns off the second channel of solid-state relay.
```
This function turns off the specified channel of the solid-state relay and should be called with one argument. Channel should be specified as integer in the range of 1 to 4.<br>

---

### Owen MK110-220.4DN.4R Discrete Input-Output Module (RS-485)
### discrete_io_input_counter(channel)
```python
discrete_io_input_counter(channel: str ['1','2','3','4']) -> int
```
```
Example: discrete_io_input_counter('1') returns the counter value of the first input.
```
This function returns the counter value of the specified input channel of the discrete IO module. The function requires one argument that should be one of the following: [1', '2', '3', '4'].<br>

---

### discrete_io_input_counter_reset(channel)
```python
discrete_io_input_counter_reset(channel: str ['1','2','3','4']) -> none
```
```
Example: discrete_io_input_counter_reset('1') resets the counter value of the first input.
```
This function resets the counter of the specified input channel. The function requires one argument that should be one of the following: [1', '2', '3', '4'].<br>

---

### discrete_io_input_state()
```python
discrete_io_input_state() -> str
```
```
Example: discrete_io_input_state()
returns the input states of the IO module in the format '1234' that means inputs 1-4 are on.
```
This function returns the input channel states of the discrete IO module and should be called without argument. The output is in the form ['0', '1', '2', ... '12', ... '1234']. The meaning is the following: '0' - all inputs are off, '12' - inputs 1 and 2 are on, and so on.<br>

---

### discrete_io_output_state(\*state)
```python
discrete_io_output_state(state: str ('1234', etc)) -> none
discrete_io_output_state() -> str
```
```
Example: discrete_io_output_state('0') turns off all the outputs of the IO module. 
```
This function sets or queries the output channel states of the discrete IO module. If an argument is specified the function sets specified state of the output channels. If there is no argument the function returns the current state of the output channels. The argument should be in the form ['0', '1', '2', ... '12', ... '1234']. The meaning is the following: '0' - all outputs are off, '12' - outputs 1 and 2 are on, and so on. The output format is the same as the described argument.<br>

---

### Cryomech CPA2896, CPA1110 Digital Panels (RS-485)
### cryogenic_refrigerator_name()
```python
cryogenic_refrigerator_name() -> str
```
This function returns device name.<br>

---

### cryogenic_refrigerator_state(\*state)
```python
cryogenic_refrigerator_state(state: str ['On','Off']) -> none
cryogenic_refrigerator_state() -> str
```
```
Example: cryogenic_refrigerator_state('On') turns on the compressor.
```
This function sets or queries the state of the cryogenic refrigerator. If there is no argument the function will return the current state. If called with an argument the specified state will be set.<br/>
The return value is one of the following: ['Idling', 'Starting', 'Running', 'Stopping', 'Error Lockout', 'Error', 'Helium Cool Down', 'Power related Error', 'Recovered from Error'].<br/>
The available states to set are ['On', 'Off'].<br>

---

### cryogenic_refrigerator_status_data()
```python
cryogenic_refrigerator_status_data() -> numpy.array(11)
```
```
Example: cryogenic_refrigerator_status_data() reads all the status data from the compressor.
```
This function queries the status data of the cryogenic refrigerator. The returned array is as follows:<br/>
array[0] = Coolant Tempeparure In<br/>
array[1] = Coolant Tempeparure Out<br/>
array[2] = Oil Tempeparure<br/>
array[3] = Helium Tempeparure<br/>
array[4] = Low Pressure<br/>
array[5] = Low Pressure Averaged<br/>
array[6] = High Pressure<br/>
array[7] = High Pressure Averaged<br/>
array[8] = Delta Pressure Averaged<br/>
array[9] = Motor Current (A)<br/>
array[10] = Operation Hours (H/1000)<br/>
The dimensions for the pressure and temperature data can be checked using [cryogenic_refrigerator_pressure_scale()](#cryogenic_refrigerator_pressure_scale) and [cryogenic_refrigerator_temperature_scale()] (#cryogenic_refrigerator_temperature_scale) functions, respectively. Note that Cryomech uses the so-called Little endian (Intel) byte order.<br>

---

### cryogenic_refrigerator_warning_data()
```python
cryogenic_refrigerator_warning_data() -> numpy.array(2)
```
```
Example: cryogenic_refrigerator_warning_data()
reads all the warning and alarm data from the compressor.
```
This function queries the warning and alarm data of the cryogenic refrigerator. The returned array is as follows:<br/>
array[0] = Warning State<br/>
array[1] = Alarm State<br/>
Possible warning states are ['No warnings', 'Coolant IN running High', 'Coolant IN running Low', 'Coolant OUT running High', 'Coolant OUT running Low', 'Oil running High', 'Oil running Low', 'Helium running High', 'Helium running Low', 'Low Pressure running High', 'Low Pressure running Low', 'High Pressure running High', 'High Pressure running Low', 'Delta Pressure running High', 'Delta Pressure running Low', 'Static Presure running High', 'Static Presure running Low', 'Cold head motor Stall'].<br/>
Possible error states are ['No Errors', 'Coolant IN High', 'Coolant IN Low', 'Coolant OUT High', 'Coolant OUT Low', 'Oil High', 'Oil Low', 'Helium High', 'Helium Low', 'Low Pressure High', 'Low Pressure Low', 'High Pressure High', 'High Pressure Low', 'Delta Pressure High', 'Delta Pressure Low', 'Motor Current Low', 'Three Phase Error', 'Power Supply Error', 'Static Presure High', 'Static Presure Low'].<br>

---

### cryogenic_refrigerator_pressure_scale()
```python
cryogenic_refrigerator_pressure_scale() -> str ['PSI','Bar','KPA']
```
```
Example: cryogenic_refrigerator_pressure_scale() reads the currently used pressure scale.
```
This function queries the current pressure scale.<br/>
The returned value is one of the following: ['PSI', 'Bar', 'KPA']. The scale cannot be changed via remote interface.<br>

---

### cryogenic_refrigerator_temperature_scale()
```python
cryogenic_refrigerator_temperature_scale() -> str ['Fahrenheit','Celsius','Kelvin']
```
```
Example: cryogenic_refrigerator_temperature_scale() reads the currently used temperature scale.
```
This function queries the current temperature scale.<br/>
The returned value is one of the following: ['Fahrenheit', 'Celsius', 'Kelvin']. The scale cannot be changed via remote interface.<br>

---

### Cryomagnetics LM-510 Liquid Cryogen Monitor (TCP/IP Socket)
### level_monitor_name()
```python
level_monitor_name() -> str
```
This function returns device name.<br>

---

### level_monitor_select_channel(\*channel)
```python
level_monitor_select_channel(channel: str) -> none
level_monitor_select_channel() -> str ['1','2']
```
```
Example: level_monitor_select_channel('1') 
sets the default channel for future computer commands to 1.
```
This function sets or queries the default channel for future computer commands. If there is no argument the function will return the current default channel. If called with an argument the specified default channel will be set.

---

### level_monitor_boost_mode(\*mode)
```python
level_monitor_boost_mode(mode: str ['On','Off','Smart']) -> none
level_monitor_boost_mode(*mode) -> str
```
```
Example: level_monitor_boost_mode('Smart') sets the boost mode to 'Smart'.
```
This function sets or queries the operating mode for the boost portion of a sensor read cycle for the [selected channel](#level_monitor_select_channelchannel). If there is no argument the function will return the boost mode. If called with an argument the specified boost mode will be set.<br/>
The available modes are ['On', 'Off', 'Smart']. Boost 'Off' will eliminate the boost portion of the read cycle, boost 'On' enables the boost portion on every read cycle, and boost 'Smart' enables a boost cycle if no readings have been taken in the previous 5 minutes. Note, that this function is not available on the second channel if it is used as HRC (Helium Recondenser Controller) channel. This setting should be specified in the configuration file in the field: hrc_second_channel.<br>

---

### level_monitor_high_level_alarm(\*level)
```python
level_monitor_high_level_alarm(level: float) -> none
level_monitor_high_level_alarm() -> str
```
```
Example: level_monitor_high_level_alarm(99.0)
sets the high level alarm to 99.0 in the present units.
```
This function sets or queries the threshold for the high alarm in the present [units](#level_monitor_unitsunits) for the [selected channel](#level_monitor_select_channelchannel). If the liquid level rises above the threshold the alarm will be activated. The alarm will be disabled if the threshold is set to 100.0. This function is not available on the second channel if it is used as HRC (Helium Recondenser Controller) channel. This setting should be specified in the configuration file in the field: hrc_second_channel.<br>

---

### level_monitor_low_level_alarm(\*level)
```python
level_monitor_low_level_alarm(level: float) -> none
level_monitor_low_level_alarm() -> str
```
```
Example: level_monitor_low_level_alarm()
queries the low level alarm in the present units.
```
This function sets or queries the threshold for the low alarm in the present [units](#level_monitor_unitsunits) for the [selected channel](#level_monitor_select_channelchannel). If the liquid level rises above the threshold the alarm will be activated. The alarm will be disabled if the threshold is set to 0.0. This function is not available on the second channel if it is used as HRC (Helium Recondenser Controller) channel. This setting should be specified in the configuration file in the field: hrc_second_channel.<br>

---

### level_monitor_sensor_length()
```python
level_monitor_sensor_length() -> str
```
```
Example: level_monitor_sensor_length()
queries the sensor length in the present units.
```
This function returns the active sensor length in the present [units](#level_monitor_unitsunits) for the [selected channel](#level_monitor_select_channelchannel). The length is returned in centimeters if percent is the present unit selection. This function is not available on the second channel if it is used as HRC (Helium Recondenser Controller) channel. This setting should be specified in the configuration file in the field: hrc_second_channel.<br>

---

### level_monitor_sample_mode(\*mode)
```python
level_monitor_sample_mode(mode: str) -> none
level_monitor_sample_mode() -> str ['Sample/Hold','Continuous','Off']
```
```
Example: level_monitor_sample_mode('Continuous') sets the continuous sampling.
```
This function sets or queries the sample mode for the [selected channel](#level_monitor_select_channelchannel). If there is no argument the function will return the sample mode. If called with an argument the specified sample mode will be set.<br/>
The available modes are ['Sample/Hold', 'Continuous', 'Off']. In the 'Sample/Hold' mode the measurements are taken when a [measure command](#level_monitor_measurechannel) is sent via the computer interface or when the delay between samples set by the [level_monitor_sample_interval()](level_monitor_sample_intervalinterval) function command expires. The interval timer is reset on each measurement, regardless of source of the measurement request. In 'Continuous' mode measurements are taken as frequently as possible. This function is not available on the second channel if it is used as HRC (Helium Recondenser Controller) channel. This setting should be specified in the configuration file in the field: hrc_second_channel.<br>

---

### level_monitor_units(\*units)
```python
level_monitor_units(units: str) -> none
level_monitor_units() -> str ['cm','in','%']
```
```
Example: level_monitor_units('cm') sets the units to centimeters.
```
This function sets or queries the units to be used for all input and display operations for the [selected channel](#level_monitor_select_channelchannel). If there is no argument the function will return the present units. If called with an argument the specified units will be set.<br/>
The available units are ['cm', 'in', '%']. This function is not available on the second channel if it is used as HRC (Helium Recondenser Controller) channel. This setting should be specified in the configuration file in the field: hrc_second_channel.<br>

---

### level_monitor_measure(channel)
```python
level_monitor_measure(channel: str ['1','2']) -> str
```
```
Example: level_monitor_measure('2') measures the data from the second channel.
```
This function starts a measurement on the [selected channel](#level_monitor_select_channelchannel) and queries the result in the present [units](#level_monitor_unitsunits). This function return two values (pressure in psi and heater power in watts) if the second channel is used as HRC (Helium Recondenser Controller).<br>

---

### level_monitor_sample_interval(\*interval)
```python
level_monitor_sample_interval(hours: int, minutes: int, seconds: int) -> none
level_monitor_sample_interval() -> str 'hours:minutes:seconds'
```
```
Example: level_monitor_sample_interval('0', '5', '0') sets the time between samples to 5 minutes.
```
This function sets or queries the time between samples for the [selected channel](#level_monitor_select_channelchannel). If there is no argument the function will return the present time between samples in the HH:MM:SS format. If called with three arguments the specified interval will be set.<br/>
The three arguments corresponds to hours (0-99), minutes (0-59), and seconds (0-59). This function is not available on the second channel if it is used as HRC (Helium Recondenser Controller) channel. This setting should be specified in the configuration file in the field: hrc_second_channel.<br/>

---

### level_monitor_hrc_target_pressure(\*pressure)
```python
level_monitor_hrc_target_pressure(pressure: float) -> none
level_monitor_hrc_target_pressure() -> str
```
```
Example: level_monitor_hrc_target_pressure('1.0') sets the target_pressure to 1.0 psi.
```
This function sets or queries the target operating pressure for the HRC (Helium Recondenser Controller) channel. If there is no argument the function will return the present target pressure in psi. If called with one argument the specified pressure will be set.<br/>
The target pressure should be between 0.15 and 14.25 psi. This function is only available for HRC (Helium Recondenser Controller) channel. This setting should be specified in the configuration file in the field: hrc_second_channel.<br>

---

### level_monitor_hrc_heater_power_limit(\*limit)
```python
level_monitor_hrc_heater_power_limit(limit: float) -> none
level_monitor_hrc_heater_power_limit() -> str
```
```
Example: level_monitor_hrc_heater_power_limit('4.0')
sets the heater power limit to 4.0 watts.
```
This function sets or queries the heater power limit for the HRC (Helium Recondenser Controller) channel. If there is no argument the function will return the present heater power limit in watts. If called with one argument the specified power limit will be set.<br/>
The heater power limit should be between 0.1 and 10 watts. Note, that this function is only available for HRC (Helium Recondenser Controller) channel. This setting should be specified in the configuration file in the field: hrc_second_channel.<br/>

---

### level_monitor_hrc_heater_enable(\*state)
```python
level_monitor_hrc_heater_enable(state: str) -> none
level_monitor_hrc_heater_enable() -> str ['On','Off']
```
```
Example: level_monitor_hrc_heater_enable('On') turns on the HRC heater.
```
This function sets or queries the state of the HRC (Helium Recondenser Controller) channel heater. If there is no argument the function will return the present state. If called with one argument the specified state will be set.<br/>
The available states are ['On', 'Off']. Note, that if the heater is turned off due to the system being above the target operating pressure when the heater is enabled, 'On' will still be returned. This function is only available for HRC (Helium Recondenser Controller) channel. This setting should be specified in the configuration file in the field: hrc_second_channel.<br/>

---

### level_monitor_command(command)
```python
level_monitor_command(command: str) -> none
```
```
Example: level_monitor_command('LOW 45.0')
This example sets low threshold for Control functions (automated refill activation).
```
This function sends an arbitrary command from a programming guide to the device in a string format. No output is expected.<br/>

---

### level_monitor_query(command)
```python
level_monitor_query(command: str) -> str
```
```
Example: level_monitor_query('CTRL?')
This example queries the status of the Control Relay (i.e., refill status).
```
This function sends an arbitrary command from a programming guide to the device in a string format. An output in a string format is expected.<br/>
