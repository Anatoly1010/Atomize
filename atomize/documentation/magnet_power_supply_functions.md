# List of available functions for magnet power supplies

Available devices:
- Cryomagnetics 4G (Ethernet); Untested

Please note, that there are several default settings for working with the Cryomagnetics 4G power supply. All of them must be specified in the configuration file. The parameters [range](#magnet_power_supply_rangerange), [rate](#magnet_power_supply_sweep_raterate), [rate_fast](#magnet_power_supply_sweep_raterate),  [voltage_limit](#magnet_power_supply_voltage_limitlimit), [units](#magnet_power_supply_unitsunits), [channel](#magnet_power_supply_select_channelchannel) are discussed in details in the corresponding functions. Field/current conversion parameter 'field/current' is given in Gauss/Amps. The default configuration file is as follows:
```python3
[SPECIFIC]
max_current = 100
min_current = -100
range = 40 60 85 93
rate = 0.01 0.01 0.007 0.005 0.005
rate_fast = 5.0
voltage_limit = 1
units = G
max_channels = 2
channel = CH1
field/current = 1258
```
The following functions are used in the device initialization process:
```python3
magnet_power_supply_control_mode( 'Remote' )
magnet_power_supply_range( range )
magnet_power_supply_sweep_rate( rate, rate_fast )
magnet_power_supply_voltage_limit( voltage_limit )
magnet_power_supply_units( units )
magnet_power_supply_select_channel( channel )
magnet_power_supply_low_sweep_limit( low_sweep_limit )
magnet_power_supply_upper_sweep_limit( upper_sweep_limit )
magnet_power_supply_sweep('Zero', 'Slow')
```

Functions:
- [magnet_power_supply_name()](#magnet_power_supply_name)<br/>
- [magnet_power_supply_select_channel(*channel)](#magnet_power_supply_select_channelchannel)<br/>
- [magnet_power_supply_low_sweep_limit(*limit)](#magnet_power_supply_low_sweep_limitlimit)<br/>
- [magnet_power_supply_upper_sweep_limit(*limit)](#magnet_power_supply_upper_sweep_limitlimit)<br/>
- [magnet_power_supply_voltage_limit(*limit)](#magnet_power_supply_voltage_limitlimit)<br/>
- [magnet_power_supply_sweep_rate(*rate)](#magnet_power_supply_sweep_raterate)<br/>
- [magnet_power_supply_range(*range)](#magnet_power_supply_rangerange)<br/>
- [magnet_power_supply_sweep(*sweep)](#magnet_power_supply_sweepsweep)<br/>
- [magnet_power_supply_units(*units)](#magnet_power_supply_unitsunits)<br/>
- [magnet_power_supply_persistent_current(*current)](#magnet_power_supply_persistent_currentcurrent)<br/>
- [magnet_power_supply_mode()](#magnet_power_supply_mode)<br/>
- [magnet_power_supply_control_mode(mode)](#magnet_power_supply_modemode)<br/>
- [magnet_power_supply_current()](#magnet_power_supply_current)<br/>
- [magnet_power_supply_voltage()](#magnet_power_supply_voltage)<br/>
- [magnet_power_supply_magnet_voltage()](#magnet_power_supply_magnet_voltage)<br/>
- [magnet_power_supply_persistent_heater(*state)](#magnet_power_supply_persistent_heaterstate)<br/>
- [magnet_power_supply_command(command)](#magnet_power_supply_commandcommand)<br/>
- [magnet_power_supply_query(command)](#magnet_power_supply_querycommand)<br/>

### magnet_power_supply_name()
```python3
magnet_power_supply_name()
Arguments: none; Output: string.
```
The function returns device name.
### magnet_power_supply_select_channel(*channel)
```python3
magnet_power_supply_select_channel(*channel)
Arguments: channel= ['CH1','CH2']; Output: currently selected channel ('CH1' or 'CH2').
Example: magnet_power_supply_select_channel('CH1') selects the first channel for remote commands.
```
The function queries (if called without argument) or selects (if called with one argument) the module (channel) for subsequent remote commands. The argument should be from the following array: ['CH1', 'CH2']. When a second channel is selected on a device with only one module installed, an error is returned. The output is returned as a string 'CH1' or 'CH2'.
### magnet_power_supply_low_sweep_limit(*limit)
```python3
magnet_power_supply_low_sweep_limit(*limit)
Arguments: limit = float; Output: string (number + 'A' or 'kG').
Example: magnet_power_supply_low_sweep_limit(10) sets the current limit to 10 for the next sweep down.
```
The function queries (if called without argument) or sets (if called with one argument) the current limit used for the next sweep down by the [magnet_power_supply_sweep()](#magnet_power_supply_sweep) function. The value must be supplied in the selected [units](#magnet_power_supply_units) – Amperes or Field (kG). An error will be returned if this value is greater than the [upper sweep limit](#magnet_power_supply_upper_sweep_limitlimit). The output as a string is also returned in the selected units – Amperes or Field (kG), e.g. '0.000kG'. 
### magnet_power_supply_upper_sweep_limit(*limit)
```python3
magnet_power_supply_upper_sweep_limit(*limit)
Arguments: limit = float; Output: string (number + 'A' or 'kG').
Example: magnet_power_supply_upper_sweep_limit(10) sets the current limit to 10 for the next sweep up.
```
The function queries (if called without argument) or sets (if called with one argument) the current limit used for the next sweep up by the [magnet_power_supply_sweep()](#magnet_power_supply_sweep) function. The value must be supplied in the selected [units](#magnet_power_supply_units) – Amps or Field (kG). An error will be returned if this value is lower than the [low sweep limit](#magnet_power_supply_low_sweep_limitlimit). The output as a string is also returned in the selected [units](#magnet_power_supply_units)  – Amperes or Field (kG), e.g. '0.500kG'. 
### magnet_power_supply_voltage_limit(*limit)
```python3
magnet_power_supply_voltage_limit(*limit)
Arguments: limit = float; Output: string(number + 'V').
Example: magnet_power_supply_voltage_limit(1) sets the power supply output voltage limit to 1 V.
```
The function queries (if called without argument) or sets (if called with one argument) the power supply output voltage limit. For Cryomagnetics 4G, the available range is 0 to 10 Volts. The output is returned as a string, e.g. '4.750V'.
### magnet_power_supply_sweep_rate(*rate)
```python3
magnet_power_supply_sweep_rate(*rate)
Arguments: rate = six floats (R1, R2, R3, R4, R5, R_Fast); Output: array of six elements.
Example: magnet_power_supply_sweep_rate(0.01, 0.01, 0.007, 0.005, 0.005, 5.0) sets the charge rates 
in Amps/second for the different ranges of the power supply.
```
The function queries (if called without argument) or sets (if called with six arguments) the charge rates in Amps/second for the [different ranges](#magnet_power_supply_rangerange) of the power supply. The first argument corresponds to the first range, the second argument to the second range, etc. The last argument sets the Fast mode sweep rate. The output is returned as a numpy array of six elements corresponding to the different ranges.
### magnet_power_supply_range(*range)
```python3
magnet_power_supply_range(*range)
Arguments: rate = four floats (RL1, RL2, RL3, RL4); Output: array of five elements.
Example: magnet_power_supply_sweep_rate(40, 60, 85, 93) sets the upper limits for a charge rate ranges
in Amps.
```
The function queries (if called without argument) or sets (if called with four arguments) the upper limits for a [charge rate](#magnet_power_supply_sweep_raterate) ranges in Amperes. The first argument corresponds to the Range 0 that starts at zero and ends at the limit provided. Range 1 starts at the Range 0 limit and ends at the Range 1 limit provided. The same for Range 2 and 3. Range 4 starts at the Range 3 limit and ends at the maximum output power of the power supply. The output is returned as a numpy array of five elements corresponding to the different ranges, including the maximum output power of the power supply as the last element.
### magnet_power_supply_sweep(*sweep)
```python3
magnet_power_supply_sweep(*sweep)
Arguments: sweep = string (['Up','Down','Pause','Zero']) or
sweep = two strings (['Up','Down','Pause','Zero'], ['Fast', 'Slow']); Output: string.
Example: magnet_power_supply_sweep('Up', 'Fast') causes the power supply to sweep the output current 
from the present current to the specified limit at the fast mode.
```
The function causes (if called with one argument) the power supply to sweep the output current from the present current to  the specified limit at the applicable charge rate set by the [range](#magnet_power_supply_rangerange) and [rate](#magnet_power_supply_sweep_raterate) commands. If the second argument 'Fast' is given, the fast mode [rate](#magnet_power_supply_sweep_raterate) will be used  instead of a rate selected from the output current range.  The second argument 'Slow' is required to change from fast sweep. The first argument 'Up' sweeps to the Upper limit; 'Down' sweeps to  the Lower limit; 'Zero' discharges the supply. If the function is called without arguments, it returns the present sweep mode as a string. If sweep is not active then 'Standby' is returned.
### magnet_power_supply_units(*units)
```python3
magnet_power_supply_units(*units)
Arguments: units = string (['A','G']); Output: string.
Example: magnet_power_supply_units('A') sets the units to Amps.
```
The function queries (if called without argument) or sets (if called with four arguments) the units to be used for all input and display operations. Units may be set to Amps ('A') or Gauss ('G'). The unit will autorange to display Gauss, Kilogauss or Tesla. The output is returned as a string, e.g. 'A'.
### magnet_power_supply_persistent_current(*current)
```python3
magnet_power_supply_persistent_current(*current)
Arguments: current = float; Output: string.
Example: magnet_power_supply_persistent_current(17.93) sets the magnet current shown on the display.
```
The function queries (if called without argument) or sets (if called with four arguments) the magnet current shown on the display. The supply must be in standby or a command error will be returned. The value must be supplied in the selected 
[units](#magnet_power_supply_units) – Amperes or Field (kG). The output is returned as a string, e.g. '17.13A'. If the [persistent switch heater](#magnet_power_supply_persistent_heaterstate) is 'On' the magnet current returned will be the same as the power supply output current. If the [persistent switch heater](#magnet_power_supply_persistent_heaterstate) is 'Off', the magnet current will be the value of the power supply output current when the [persistent switch heater](#magnet_power_supply_persistent_heaterstate) was last turned off.
### magnet_power_supply_mode()
```python3
magnet_power_supply_mode()
Arguments: none; Output: string.
Example: magnet_power_supply_mode() returns the present operating mode, e.g. 'Manual'.
```
This function returns the present operating mode ('Shim' or 'Manual') of the power supply as a string, e.g. 'Manual'.
### magnet_power_supply_control_mode(mode)
```python3
magnet_power_supply_control_mode(mode)
Arguments: mode = string (['Remote', 'Local']); Output: none.
Example: magnet_power_supply_control_mode('Remote') takes control of the power supply via 
the remote interface.
```
This function sets the control mode of the power supply. The available mode is from the array: ['Remote', 'Local']. Please note that the Cryomagnetics 4G must be switched to 'Remote' mode to change the default settings. 

### magnet_power_supply_current()
```python3
magnet_power_supply_current()
Arguments: none; Output: string (number + 'A' or 'kG').
Example: magnet_power_supply_current() returns the power supply output current in the present units.
```
This function returns the power supply output current (or magnetic field strength) in the present [units](#magnet_power_supply_units) as a string, e.g. '5A'.
### magnet_power_supply_voltage()
```python3
magnet_power_supply_voltage()
Arguments: none; Output: string (number + 'V').
Example: magnet_power_supply_voltage() returns the present power supply output voltage, e.g. '10.000V'.
```
This function returns the present power supply output voltage as a string, e.g. '10.0V'. Response range is from –12.80 to +12.80 Volts.
### magnet_power_supply_magnet_voltage()
```python3
magnet_power_supply_magnet_voltage()
Arguments: none; Output: string (number + 'V').
Example: magnet_power_supply_magnet_voltage() returns the present magnet voltage, e.g. '3.0 V'.
```
This function returns the present magnet voltage as a string, e.g. '3.0V'. Response range is from –10 to +10 Volts.
### magnet_power_supply_persistent_heater(*state)
```python3
magnet_power_supply_persistent_heater(*state)
Arguments: state = string (['On','Off']); Output: string.
Example: magnet_power_supply_persistent_heater('Off') turns off the persistent_heater.
```
The function queries (if called without argument) or sets (if called with four arguments) the state of the persistent switch heater. The available state is from the array: ['On', 'Off']. Note that the switch heater current can only be set in the Magnet Menu using the keypad. This command should normally be used only when the supply output is stable and matched to the magnet current. The output is either 'On' or 'Off'.
### magnet_power_supply_command(command)
```python3
magnet_power_supply_command(command)
Arguments: command = string; Output: none.
```
The function for sending an arbitrary command from a programming guide to the device in a string format. No output is expected.
### magnet_power_supply_query(command)
```python3
magnet_power_supply_query(command)
Arguments: command = string; Output: string.
```
The function for sending an arbitrary command from a programming guide to the device in a string format. An output in a string format is expected.<br/>