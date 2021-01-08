# List of available functions for oscilloscopes
```python3
oscilloscope_name()
Arguments: none; Output: string(name).
```
The function returns device name.
```python3
oscilloscope_record_length(\*points)
Arguments: points = integer from a specified dictionary; Output: integer.
```
This function queries or sets the number of waveform points to be transferred using oscilloscope_get_curve() function. The number of points should be from the following array:<br/>
[100, 250, 500, 1000, 2000, 4000, 8000, 16000, 32000, 64000, 128000, 256000, 512000].
The maximum amount of points that can be transferred depend on the waveform points mode. Please, refer to the manual.<br/>
```python3
Example: oscilloscope_record_length(4000) sets the number of waveform points to 4000.
```
```python3
oscilloscope_acquisition_type(\*ac_type)
Arguments: ac_type = integer (0,1,2 or 3); Output: integer.
```
This function queries or sets the acquisition type for Keysight 3000 oscilloscopes. If there is no argument the function will return the current acquisition type. If there is an argument the specified acquisition type will be set. Possible acquisition types and their meaning are the following:<br/>
'0' - Normal; '1' - Average; '2' - High-resolution (also known as smoothing). This mode is used to reduce noise at slower sweep speeds where the digitizer samples faster than needed to fill memory for the displayed time range; '3' - Peak detect.<br/>
```python3
Example: oscilloscope_acquisition_type('1') sets the acquisition type to the average mode.
```
```python3
oscilloscope_number_of_averages(\*number_of_averages)
Arguments: number_of_averages = integer (2-65536); Output: integer.
```
This function queries or sets the number of averages in the range of 2 to 65536 in the averaging acquisition mode (for Keysight 3000 oscilloscopes). If there is no argument the function will return the current number of averages. If there is an argument the specified number of averages type will be set. If the oscilloscopes is not in the averaging acquisition mode the error message will be printed.<br/>
```python3
Example: oscilloscope_number_of_averages('2') sets the number of averages to 2.
```
```python3
oscilloscope_timebase(\*timebase)
Arguments: timebase = string ('number + scaling (s, ms, us, ns)'); Output: float (in us).
```
This function queries or sets the full-scale horizontal time for the main window. The range is 10 times the current time-per-division setting. If there is no argument the function will return the full-scale horizontal time in us. If there is an argument the specified full-scale horizontal time will be set.<br/>
```python3
Example: oscilloscope_timebase('20 us') sets the full-scale horizontal time to 20 us
(2 us per divison).
```
```python3
oscilloscope_time_resolution()
Arguments: none; Output: float.
```
This function takes no arguments and returns the time resolution per point in us.<br/>
```python3
Example: oscilloscope_time_resolution() returs the current time resolution per point in us.
```
```python3
oscilloscope_start_acquisition()
Arguments: none; Output: none.
```
This function starts an acquisition sequence. Previously measured curves are discarded and new data are sampled until the desired number of averages has been reached. This function acquires all the channels currently displayed on the screen of oscilloscopes and should be called before oscilloscope_get_curve() function.
```python3
oscilloscope_preamble(channel)
Arguments: channel = string (['CH1, CH2, CH3, CH4']); Output: array of the mixed types.
```
This function requests the preamble information for the selected waveform source. The preamble data contains information concerning the vertical and horizontal scaling of the data of the corresponding channel.<br/>
Preamble format (ascii): [format, type, points, count, xincrement, xorigin, xreference, yincrement, yorigin, yreference]<br/>
```python3
Example: oscilloscope_preamble('CH3') returs the preamble from channel 3.
```
```python3
oscilloscope_stop()
Arguments: none; Output: none.
```
The function stops the acquisition. This is the same as pressing the stop key on the front panel.
```python3
oscilloscope_run()
Arguments: none; Output: none.
```
The function starts repetitive acquisitions. This is the same as pressing the run key on the front panel.
```python3
oscilloscope_get_curve(channel)
Arguments: channel = string (['CH1, CH2, CH3, CH4']); Output: array of floats (in V).
```
The function returns a curve from the specified channel of the oscilloscope. At the moment, it expects one argument, namely the channel from which the data should be transferred. The data from two channels can be transferred sequentially.<br/>
```python3
Example: oscilloscope_get_curve('CH2') returs the data from channel 2.
```
```python3
oscilloscope_sensitivity(\*channel)
Arguments: channel = two strings ('channel string', 'number + scaling (V, mV)')
or one string ('channel string'); Output: float (in mV).
```
The function queries (if called with one argument) or sets (if called with two arguments) the sensitivity per division of one of the channels of the oscilloscope. If there is a second argument this will be set as a new sensitivity. If there is no second argument the current sensitivity for specified the channel is returned.<br/>
```python3
Examples: oscilloscope_sensitivity('CH2', '100 mV') sets the sensitivity 
per division of the channel 2 to 100 mV. oscilloscope_sensitivity('CH2') returns
the current sensitivity of the channel 2 in mV.
```
```python3
oscilloscope_offset(\*channel)
Arguments: channel = two strings ('channel string', 'number + scaling (V, mV)')
or one string ('channel string'); Output: float (in mV).
```
The function queries (if called with one argument) or sets (if called with two arguments) the offset setting of one of the channels of the oscilloscope. If there is a second argument this will be set as a new offset setting. If there is no second argument the current offset setting for the specified channel is returned.<br/>
```python3
Examples: oscilloscope_offset('CH2', '100 mV') sets the offset setting of the channel 2
to 100 mV. oscilloscope_offset('CH2') returns the current offset of the channel 2 in mV.
```
```python3
oscilloscope_coupling(\*coupling)
Arguments: coupling = two strings ('channel string', 'coupling string (AC, DC)')
or one string ('channel string'); Output: string.
```
The function queries (if called with one argument) or sets (if called with two arguments) the coupling of one of the channels of the oscilloscope. If there is a second argument this will be set as a new coupling. If there is no second argument the current coupling for the specified channel is returned.<br/>
```python3
Examples: oscilloscope_coupling('CH2', 'AC') sets the coupling of the channel 2 to AC.
oscilloscope_coupling('CH2') returns the current coupling of the channel 2.
```
```python3
oscilloscope_impedance(\*impedance)
Arguments: impedance = two strings ('channel string', 'impedance string (1 M, 50)')
or one string ('channel string'); Output: string.
```
The function queries (if called with one argument) or sets (if called with two arguments) the impedance of one of the channels of the oscilloscope. If there is a second argument this will be set as a new impedance. If there is no second argument the current impedance for the specified channel is returned.<br/>
```python3
Examples: oscilloscope_impedance('CH2', '1 M') sets the impedance of the channel 2 to 1 MOhm.
oscilloscope_impedance('CH2') returns the current impedance of the channel 2.
```
```python3
oscilloscope_trigger_mode(\*mode)
Arguments: mode = string ('Auto', 'Normal'); Output: string.
```
The function queries or sets the trigger mode of the oscilloscope. If there is no argument the function will return the current trigger mode (Auto or Normal). If there is an argument the specified trigger mode will be set.<br/>
When Auto sweep mode is selected, a baseline is displayed in the absence of a signal. If a signal is present but the oscilloscope is not triggered, the unsynchronized signal is displayed instead of a baseline. When Normal sweep mode is selected and no trigger is present, the instrument does not sweep, and the data acquired on the previous trigger remains on the screen.<br/>
```python3
Examples: oscilloscope_trigger_mode('Auto') sets the trigger mode to 1 Auto.
```
```python3
oscilloscope_trigger_channel(\*channel)
Arguments: channel = string (['CH1, CH2, CH3, CH4', 'Ext', 'Line', 'WGen']); Output: string.
```
The function queries or sets the trigger channel of the oscilloscope. If there is no argument the function will return the current trigger channel ( CHAN<n>, EXT, LINE, WGEN, NONE). If all channels are off, the query returns NONE. If there is an argument the specified trigger channel will be set.<br/>
Argument Ext triggers on the rear panel EXT TRIG IN signal. Argument Line triggers at the 50% level of the rising or falling edge of the AC power source signal. Argument Wgen triggers at the 50% level of the rising edge of the waveform generator output signal. This option is not available when the DC, NOISe, or CARDiac waveforms of the waveform generator are selected. <br/>
```python3
Examples: oscilloscope_trigger_channel('CH3') sets the trigger channel to 3.
```
```python3
oscilloscope_trigger_low_level(\*level)
Arguments: level = string + float ('channel string' ['CH1, CH2, CH3, CH4'],
float level in V) or one string ('channel string'); Output: float.
```
The function queries (if called with one argument) or sets (if called with two arguments) the low trigger voltage level voltage of one of the channels of the oscilloscope. If there is a second argument this will be set as a new low trigger voltage level. If there is no second argument the current low trigger voltage level for the specified channel is returned.<br/>
```python3
Examples: oscilloscope_trigger_low_level('CH2', 0.5) sets the low trigger 
voltage level of the channel 2 to 500 mV. oscilloscope_trigger_low_level('CH2')
returns the current low trigger voltage level of the channel 2.
```
```python3
oscilloscope_command(command)
Arguments: command = string; Output: none.
```
The function for sending an arbitrary command from a programming guide to the device in a string format. No output is expected.<br/>
```python3
Example: oscilloscope_command(':TRIGger:FORCe'). This command causes an acquisition
to be captured even thoughthe trigger condition has not been met.
```
```python3
oscilloscope_query(command)
Arguments: command = string; Output: string (answer).
```
The function for sending an arbitrary command from a programming guide to the device in a string format. An output in a string format is expected.<br/>
```python3
Example: oscilloscope_query(':MEASure:FREQuency?'). This command queries an measurement
and outputs the frequency of the cycle on the screen closest to the trigger reference.
```

