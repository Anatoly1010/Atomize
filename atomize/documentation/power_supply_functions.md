# List of available functions for lock-in amplifiers
```python3
power_supply_name()
Arguments: none; Output: string.
```
The function returns device name.
```python3
power_supply_voltage(*voltage)
Arguments: voltage = two strings ('channel string' ['CH1','CH2','CH3'], 'number + scaling (V, mV)')
or one string ('channel string'); Output: float (in V).
Example: power_supply_voltage('CH1', '10 V') sets the voltage of the first channel to 10 V.
```
The function queries (if called with one argument) or sets (if called with two arguments) the voltage of one of the channels of the power supply. If there is a second argument this will be set as a new voltage. If there is no second argument the current voltage for specified the channel is returned in Volts.<br/>
```python3
power_supply_current(*current)
Arguments: current = two strings ('channel string' ['CH1','CH2','CH3'], 'number + scaling (A, mA)')
or one string ('channel string'); Output: float (in A).
Example: power_supply_current('CH2', '100 mA') sets the current of the second channel to 100 mA.
```
The function queries (if called with one argument) or sets (if called with two arguments) the current of one of the channels of the power supply. If there is a second argument this will be set as a new current. If there is no second argument the current for specified the channel is returned in Ampers.<br/>
```python3
power_supply_overvoltage(*voltage)
Arguments: voltage = two strings ('channel string' ['CH1','CH2','CH3'], 'number + scaling (V, mV)')
or one string ('channel string'); Output: float (in V).
Example: power_supply_overvoltage('CH1', '30 V') sets the overvoltage protection of the first channel to 30 V.
```
The function queries (if called with one argument) or sets (if called with two arguments) the overvoltage protection of one of the channels of the power supply. If there is a second argument this will be set as a new overvoltage protection setting. If there is no second argument the current overvoltage protection setting for specified the channel is returned in Volts.<br/>
```python3
power_supply_overcurrent(*current)
Arguments: voltage = two strings ('channel string' ['CH1','CH2','CH3'], 'number + scaling (A, mA)')
or one string ('channel string'); Output: float (in A).
Example: power_supply_overcurrent('CH1', '3 A') sets the overcurrent protection of the first channel to 3 A.
```
The function queries (if called with one argument) or sets (if called with two arguments) the overcurrent protection of one of the channels of the power supply. If there is a second argument this will be set as a new overcurrent protection setting. If there is no second argument the current overcurrent protection setting for specified the channel is returned in Ampers.<br/>
```python3
power_supply_channel_state(*state)
Arguments: state = two strings ('channel string' ['CH1','CH2','CH3'], 'state ('On', 'Off')')
or one string ('channel string'); Output: string.
Example: power_supply_channel_state('CH1', 'On') enables the output of the first channel.
```
The function queries (if called with one argument) or sets (if called with two arguments) the state of the output of one of the channels of the power supply. If there is a second argument this will be set as a new state setting. If there is no second argument the current state setting for specified the channel is returned.<br/>
The state argument should be 'On' or 'Off', which means that the output is enabled and disabled, respectively.<br/>
```python3
power_supply_measure(channel)
Arguments: channel = string ('channel string' ['CH1','CH2','CH3']); Output: array of values.
Example: power_supply_measure('CH1') queries the voltage, current and power measured on the output terminal of the channel 1.
```
The function can be called only with one argument and queries the voltage, current and power measured on the output terminal of the specified channel. The functiob returns measured values in Volts, Ampers, Watts separeted by commas.<br/>
```python3
power_supply_preset(preset)
Arguments: preset = string ('preset string' ['Default','User1','User2','User3']); Output: none.
Example: power_supply_preset('User1') sets the preset settings with the name 'User1'.
```
The function can be called only with one argument and allows restoring the instrument to the default setting ('Default' argument) or recall the user-defined setting ('User<n>' arguments).<br/>
```python3
power_supply_command(command)
Arguments: command = string; Output: none.
Example: power_supply_command(':APPL CH1,5,1'). This example sets the voltage and current of CH1 to 5V and 1A respectively.
```
The function for sending an arbitrary command from a programming guide to the device in a string format. No output is expected.<br/>
```python3
power_supply_query(command)
Arguments: command = string; Output: string.
Example: power_supply_query(':APPL? CH1'). This example queries the voltage and current setting values of CH1 and the query returns CH1:8V/5A,5.000,1.0000.
```
The function for sending an arbitrary command from a programming guide to the device in a string format. An output in a string format is expected.<br/>
