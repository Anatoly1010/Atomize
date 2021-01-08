# List of available functions for frequency counters

```python3
freq_counter_name()
Arguments: none; Output: string(name).
```
The function returns device name.
```python3
freq_counter_frequency(channel)
Arguments: channel = string (['CH1', 'CH2', 'CH3']); Output: float.
```
This function returns a floating point value with the measured frequency (in Hz) from the specified channel. Refer to the device manual for the frequency range of different channels.<br/>
Agilent 53181a has two channels; Agielnt 53131a - three.<br/>
```python3
Example: freq_counter_frequency('CH1') returns the measured frequency from channel 1.
```
## freq_counter_impedance(\*impedance)
### Arguments: impedance = two strings ('channel string', 'impedance string (1 M, 50)') or one string ('channel string'); Output: string.
The function queries (if called with one argument) or sets (if called with two arguments) the impedance of one of the channels of the frequency counter. If there is a second argument this will be set as a new impedance. If there is no second argument the current impedance for the specified channel is returned.<br/>
For Agilent 53181a impedance can be changed only for the first channel; for Agielnt 53131a for channel 1 and 2.<br/>
Examples: freq_counter_impedance('CH1', '1 M') sets the impedance of the channel 1 to 1 MOhm. freq_counter_impedance('CH2') returns the current impedance of the channel 2.
## freq_counter_coupling(\*coupling)
### Arguments: coupling = two strings ('channel string', 'coupling string ('AC', 'DC')') or one string ('channel string'); Output: string.
The function queries (if called with one argument) or sets (if called with two arguments) the coupling of one of the channels of the frequency counter. If there is a second argument this will be set as a new coupling. If there is no second argument the current coupling for the specified channel is returned.<br/>
For Agilent 53181a coupling can be changed only for the first channel; for Agielnt 53131a for channel 1 and 2.<br/>
Examples: freq_counter_coupling('CH1', 'AC') sets the coupling of the channel 1 to AC. freq_counter_coupling('CH2') returns the current coupling of the channel 2.
## freq_counter_stop_mode(\*mode)
### Arguments: mode = string from a specified dictionary; Output: string.
This function queries or sets the stop arm for frequency, frequency ratio, and period measurements. The type should be from the following array:<br/>
['Im', 'Ext', 'Tim', 'Dig'] for Agilent 53181a and Agilent 53131.<br/>
In automatic (immediate or 'Im') mode the device does the fastest possible acquisistion, in gate time mode it measures for the specified gate time, and in digits mode the time required for a measurement depends on the number of digits requested. This setting influences the resolution of the results. Use automatic mode for fast measurements or choose a desired resolution by using freq_counter_gate_time() to set the gate time for gate time ('Tim') mode or freq_counter_digits() for digits ('Dig') mode.<br/>
For Keysight 53230a two possible modes can be used from an array: ['Im', 'Tim', 'Event'].<br/>
Example: freq_counter_stop_mode('Tim') sets the digits mode.
## freq_counter_start_mode(\*mode)
### Arguments: mode = string from a specified dictionary; Output: string.
This function queries or sets the start arm for frequency, frequency ratio, and period measurements. The type should be from the following array:<br/>
['Im', 'Ext'].<br/>
Example: freq_counter_start_mode('Im') sets the automatic mode.
## freq_counter_gate_mode(\*mode)
### Arguments: mode = string from a specified dictionary; Output: string.
This function queries or sets the gate source for frequency, frequency ratio measurements. Currently, the type should be from the following array:
['Tim', 'Ext'], where 'Time' coresponds to starting the measurement immediately after a trigger and trigger delay; 'Ext' configures the instrument to gate the measurement using the Gate In/Out BNC after a trigger and trigger delay.<br/>
This functions is available only for Keysight 53230a.
Example: freq_counter_gate_mode('Tim') sets the 'Time' mode.
## freq_counter_digits(\*digits)
### Arguments: digits = integer in the range of 3 to 15; Output: integer.
This function queries or sets the resolution in terms of digits used in arming frequency, period, and ratio measurements. To set this mode use freq_counter_stop_mode() function. The argument of the function should be an integer between 3 and 15. To query the number of digits call the function with no argument. A query is possible only if freq_counter_stop_mode('Dig') was called before.<br/>
This function is available only for Agilent 53181a and 53131a.<br/>
Example: freq_counter_digits(5) sets the resolution to 5 digits.
## freq_counter_gate_time(\*time)
### Arguments: time = string ('number + scaling (ks, s, ms, us, ns)'); Output: float.
This function queries or sets the gate time used in arming frequency, period, and ratio measurements. To set this mode use freq_counter_stop_mode() function. The argument of the function should be from 1 ms to 1000 s (Agilent 53181a, 53131a); from 10 us to 10 s (Keysight 53220a); from 10 ns to 10 s (Keysight 53230a). To query the gate call the function with no argument. A query is possible only if freq_counter_stop_mode('Tim') was called before.<br/>
Example: freq_counter_gate_time('100 ms') sets the gate time to 100 ms.
## freq_counter_expected_freq(\*frequency)
### Arguments: frequency = two strings ('channel string', 'number + scaling (GHz, MHz, kHz, Hz)') or one string ('channel string'); Output: float (in Hz).
The function queries (if called with one argument) or sets (if called with two arguments) the approximate frequency of a signal you expect to measure. Providing this value enables the device to eliminate a pre-measurement step, saving measurement time and enabling more accurate arming. Note that the actual frequency of the input signal must be within 10 % of the expected frequency value you entered. Refer to the device manual for the frequency range of different channels.<br/>
If there is a second argument this will be set as a new approximate frequency of a signal. If there is no second argument the current approximate frequency of a signal for specified the channel is returned.<br/>
For Agilent 53181a the approximate frequency can be set for channels 1 and 2; for Agielnt 53131a for channels 1, 2, and 3.<br/>
This function is available only for Agilent 53181a and 53131a.<br/>
Example: freq_counter_expected_freq('CH3', '10 GHz') sets the approximate frequency of a signal to 10 GHz.
## freq_counter_ratio(channel1, channel2)
### Arguments: channel1 = string (['CH1', 'CH2', 'CH3']); channel2 = string (['CH1', 'CH2', 'CH3']); Output: float.
The function measures the frequency ratio between two specified inputs.<br/>
For Agilent 53181a the ratio can be measured between channel 1 and 2; for Agielnt 53131a between channel 1 and 2 or 1 and 3; for Keysight 53230a for all available channels.<br/>
Example: freq_counter_ratio('CH2', 'CH1') measures the frequency ratio between channel 2 and channel 1.
## freq_counter_period(channel)
### Arguments: channel = string (['CH1', 'CH2', 'CH3']); Output: float (in us).
This function returns a floating point value with the measured period (in us) from the specified channel. Refer to the device manual for the frequency range of different channels.<br/>
This function is available only for Agilent 53181a and 53131a.<br/>
Example: freq_counter_period('CH2') returns the measured period from channel 2.
## freq_counter_command(command)
### Arguments: command = string; Output: none.
The function for sending an arbitrary command from a programming guide to the device in a string format. No output is expected.<br/>
Example: freq_counter_command(':EVENt1:SLOPe POSitive'). This command sets which edge of the input signal will be considered an event for frequency, period, frequency ratio, time interval, totalize, and phase measurements.
## freq_counter_query(command)
### Arguments: command = string; Output: string (answer).
The function for sending an arbitrary command from a programming guide to the device in a string format. An output in a string format is expected.<br/>
Example: freq_counter_query(':MEASure:PHASe? (@1),(@2)'). This command queries an measurement of the phase between channel 1 and 2.

