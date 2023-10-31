# List of available functions for oscilloscopes

Available devices:
- Keysight InfiniiVision 2000 X-Series (Ethernet); Untested
- Keysight InfiniiVision 3000 X-Series (Ethernet); Tested 06/2021
- Keysight InfiniiVision 4000 X-Series (Ethernet); Untested
- Tektronix 3000 Series (Ethernet); Tested 09/2022
- Tektronix 4000 Series (Ethernet); Tested 01/2021
- Tektronix 5 Series MSO (Ethernet); Untested

Functions:
- [oscilloscope_name()](#oscilloscope_name)<br/>
- [oscilloscope_record_length(*points)](#oscilloscope_record_lengthpoints)<br/>
- [oscilloscope_acquisition_type(*ac_type)](#oscilloscope_acquisition_typeac_type)<br/>
- [oscilloscope_number_of_averages(*number_of_averages)](#oscilloscope_number_of_averagesnumber_of_averages)<br/>
- [oscilloscope_timebase(*timebase)](#oscilloscope_timebasetimebase)<br/>
- [oscilloscope_define_window(**kargs)](#oscilloscope_define_windowkargs)<br/>
- [oscilloscope_time_resolution()](#oscilloscope_time_resolution)<br/>
- [oscilloscope_start_acquisition()](#oscilloscope_start_acquisition)<br/>
- [oscilloscope_preamble(channel)](#oscilloscope_preamblechannel)<br/>
- [oscilloscope_stop()](#oscilloscope_stop)<br/>
- [oscilloscope_run()](#oscilloscope_run)<br/>
- [oscilloscope_get_curve(channel)](#oscilloscope_get_curvechannel)<br/>
- [oscilloscope_area(channel)](#oscilloscope_areachannel)<br/>
- [oscilloscope_sensitivity(*channel)](#oscilloscope_sensitivitychannel)<br/>
- [oscilloscope_offset(*channel)](#oscilloscope_offsetchannel)<br/>
- [oscilloscope_horizontal_offset(*h_offset)](#oscilloscope_horizontal_offseth_offset)<br/>
- [oscilloscope_coupling(*coupling)](#oscilloscope_couplingcoupling)<br/>
- [oscilloscope_impedance(*impedance)](#oscilloscope_impedanceimpedance)<br/>
- [oscilloscope_trigger_mode(*mode)](#oscilloscope_trigger_modemode)<br/>
- [oscilloscope_trigger_channel(*channel)](#oscilloscope_trigger_channelchannel)<br/>
- [oscilloscope_trigger_low_level(*level)](#oscilloscope_trigger_low_levellevel)<br/>
- [oscilloscope_command(command)](#oscilloscope_commandcommand)<br/>
- [oscilloscope_query(command)](#oscilloscope_querycommand)<br/>

### oscilloscope_name()
```python3
oscilloscope_name()
Arguments: none; Output: string.
```
The function returns device name.
### oscilloscope_record_length(*points)
```python3
oscilloscope_record_length(*points)
Arguments: points = integer from a specified dictionary; Output: integer.
Example: oscilloscope_record_length(4000) sets the number of waveform points to 4000.
```
This function queries or sets the number of waveform points to be transferred using [oscilloscope_get_curve()](#oscilloscope_get_curvechannel) function. If there is no number of points setting fitting the argument the nearest available value is used and warning is printed.<br/>
If one would like to use Keysight oscilloscopes without averaging (in normal, peak or high-resolution mode), the number of points in the waveform is usually [100, 250, 500, 1000, 2000, 5000, 10000, 20000, 50000, 100000]. The maximum available number of points depends on the timescale and can be substantially lower than 100000.<br/>
In the average mode the number of points in the waveform is not the one specified in the programming manual. For Keysight 3000 X-series the correct array is [100, 250, 500, 1000, 2000, 4000, 8000]. For Keysight 2000 X-series: [99, 247, 479, 959, 1919, 3839, 7679]. For Keysight 4000 X-series the number of points for the average mode should be checked.<br/>
To handle this situation more or less correctly, two different arrays (for average and all other modes) of available number of points are used in the modules for Keysight oscilloscopes.<br/>
Fot Tektronix 3000 Series the available number of points is [500, 10000].<br/>
Fot Tektronix 4000 Series the available number of points is [1000, 10000, 100000, 1000000, 10000000].<br/>
### oscilloscope_acquisition_type(*ac_type)
```python3
oscilloscope_acquisition_type(*ac_type)
Arguments: ac_type = string froma specified dictionary; Output: string.
Example: oscilloscope_acquisition_type('Average') sets the acquisition type to the average mode.
```
This function queries or sets the acquisition type. If there is no argument the function will return the current acquisition type. The type should be from the following array:<br/>
['Normal', 'Average', 'Hres', 'Peak']<br/>
High-resolution (also known as smoothing) mode is used to reduce noise at slower sweep speeds where the digitizer samples faster than needed to fill memory for the displayed time range.<br/>
Fot Tektronix 3000 Series 'Hres' option is not available.<br/>
### oscilloscope_number_of_averages(*number_of_averages)
```python3
oscilloscope_number_of_averages(*number_of_averages)
Arguments: number_of_averages = integer (2-65536); Output: integer.
Example: oscilloscope_number_of_averages('2') sets the number of averages to 2.
```
This function queries or sets the number of averages. If there is no argument the function will return the current number of averages. If there is an argument the specified number of averages type will be set. If the oscilloscopes is not in the averaging acquisition mode the error message will be printed. For Keysight oscilloscopes the number of averages should be in the range of 2 to 65536. For Tektronix 4000 Series the number of averages should be from 2 to 512 2 in powers of two. Please note, that for some models the maximum number of averages is limited to 128.<br/>
### oscilloscope_timebase(*timebase)
```python3
oscilloscope_timebase(*timebase)
Arguments: timebase = string ('number + scaling (s, ms, us, ns)'); Output: float (in us).
Example: oscilloscope_timebase('20 us') sets the full-scale horizontal time to 20 us
(2 us per divison).
```
This function queries or sets the full-scale horizontal time for the main window. The range is 10 times the current time-per-division setting. If there is no argument the function will return the full-scale horizontal time in us. If there is an argument the specified full-scale horizontal time will be set.<br/>
For Tektronix 3000 X-series the horizontal scale is discrete and can take on a value in the range of 10 s to 1, 2, or 4 ns (depending on model), in a 1-2-4 sequence.<br/>
For Tektronix 4000 X-series (at least for the device used for testing), the horizontal scale is discrete and can take on a value from the following array: [1, 2, 4, 10, 20, 40, 100, 200, 400] for ns, us, ms, and s scaling. In addtition timescale equals to 800 ns also can be set. If there is no timebase setting fitting the argument the nearest available value is used and warning is printed.<br/>
### oscilloscope_define_window(**kargs)
```python3
oscilloscope_define_window(**kargs)
Arguments: kargs are start = integer, stop = integer; Output: two integers.
Example: oscilloscope_define_window(start=1, stop=1000) function oscilloscope_get_curve() 
returns the first 1000 points of the waveform.
```
This function queries or sets the starting data and ending points for waveform transfer. The function should be called with two key arguments, namely start and stop. Start is the first data point that will be transferred, which ranges from 1 to the record length. Stop is the last data point that will be transferred, which ranges from 1 to the record length.<br/>
This function is avaliable only for Tektronix 4000 Series.
### oscilloscope_time_resolution()
```python3
oscilloscope_time_resolution()
Arguments: none; Output: float.
Example: oscilloscope_time_resolution() returs the current time resolution per point in us.
```
This function takes no arguments and returns the time resolution per point in us.<br/>
### oscilloscope_start_acquisition()
```python3
oscilloscope_start_acquisition()
Arguments: none; Output: none.
```
This function starts an acquisition sequence. Previously measured curves are discarded and new data are sampled until the desired number of averages has been reached. This function acquires all the channels currently displayed on the screen of oscilloscopes and should be called before [oscilloscope_get_curve()](#oscilloscope_get_curvechannel) function.
### oscilloscope_preamble(channel)
```python3
oscilloscope_preamble(channel)
Arguments: channel = string (['CH1, CH2, CH3, CH4']); Output: array of the mixed types.
Example: oscilloscope_preamble('CH3') returs the preamble from channel 3.
```
This function requests the preamble information for the selected waveform source. The preamble data contains information concerning the vertical and horizontal scaling of the data of the corresponding channel.<br/>
Preamble format (Keysight): [format, type, points, count, xincrement, xorigin, xreference, yincrement, yorigin, yreference]<br/>
Preamble format (Tektronix): [data width, bits per point, encoding, format of the binary data, byte order, channel, coupling,
vert scale, horiz scale, record length, acq mode, number of points in waveform, point format, horiz units,
xincrement, xorigin, displayed?, vert units, vert scale mult factor, yoff, yorigin]<br/>
### oscilloscope_stop()
```python3
oscilloscope_stop()
Arguments: none; Output: none.
```
The function stops the acquisition. This is the same as pressing the stop key on the front panel.
### oscilloscope_run()
```python3
oscilloscope_run()
Arguments: none; Output: none.
```
The function starts repetitive acquisitions. This is the same as pressing the run key on the front panel.
### oscilloscope_get_curve(channel)
```python3
oscilloscope_get_curve(channel)
Arguments: channel = string (['CH1, CH2, CH3, CH4']); Output: two arrays of floats (in s and V).
Example: oscilloscope_get_curve('CH2') returs the data from channel 2.
```
The function returns a curve (x and y axis independently) from specified channel of the oscilloscope. At the moment, it expects one argument, namely the channel from which the data should be transferred. The data from two channels can be transferred sequentially.<br/>
### oscilloscope_area(channel)
```python3
oscilloscope_area(channel)
Arguments: channel = string (['CH1, CH2, CH3, CH4']); Output: area value (in V*s).
Example: oscilloscope_area('CH2') returs the result of an area measurement for channel 2.
```
The function returns a value of area (in V*s) between the waveform and the ground level for specified channel of the oscilloscope. It expects one argument, namely the channel for which the area should be measured. This function is available only for Keysight oscilloscopes.<br/>
### oscilloscope_sensitivity(*channel)
```python3
oscilloscope_sensitivity(*channel)
Arguments: channel = two strings ('channel string', 'number + scaling (V, mV)')
or one string ('channel string'); Output: float (in mV).
Examples: oscilloscope_sensitivity('CH2', '100 mV') sets the sensitivity 
per division of the channel 2 to 100 mV. oscilloscope_sensitivity('CH2') returns
the current sensitivity of the channel 2 in mV.
```
The function queries (if called with one argument) or sets (if called with two arguments) the sensitivity per division of one of the channels of the oscilloscope. If there is a second argument it will be set as a new sensitivity. If there is no second argument the current sensitivity for specified the channel is returned.<br/>
### oscilloscope_offset(*channel)
```python3
oscilloscope_offset(*channel)
Arguments: channel = two strings ('channel string', 'number + scaling (V, mV)')
or one string ('channel string'); Output: float (in mV).
Examples: oscilloscope_offset('CH2', '100 mV') sets the offset setting of the channel 2
to 100 mV. oscilloscope_offset('CH2') returns the current offset of the channel 2 in mV.
```
The function queries (if called with one argument) or sets (if called with two arguments) the offset setting of one of the channels of the oscilloscope. If there is a second argument it will be set as a new offset setting. If there is no second argument the current offset setting for the specified channel is returned. The offset range depends on the type of oscilliscope and the vertical scale factor for used channel. Please, refer to device manual.<br/>
### oscilloscope_horizontal_offset(*h_offset)
```python3
oscilloscope_horizontal_offset(*h_offset)
Arguments: h_offset = string ('number + scaling (s, ms, us, ns)'); Output: float (in us).
Examples: oscilloscope_horizontal_offset('100 ms') sets the time base delay to 100 ms.
```
The function queries or sets the horizontal delay time (position). This delay is the time between the trigger event and the delay reference point on the screen. If there is no argument the function will return the current delay mode in us. If there is an argument the specified delay mode will be set. The valid range for delay settings depends on the time/division
setting for the main time base.<br/>
### oscilloscope_coupling(*coupling)
```python3
oscilloscope_coupling(*coupling)
Arguments: coupling = two strings ('channel string', 'coupling string (AC, DC)')
or one string ('channel string'); Output: string.
Examples: oscilloscope_coupling('CH2', 'AC') sets the coupling of the channel 2 to AC.
oscilloscope_coupling('CH2') returns the current coupling of the channel 2.
```
The function queries (if called with one argument) or sets (if called with two arguments) the coupling of one of the channels of the oscilloscope. If there is a second argument it will be set as a new coupling. If there is no second argument the current coupling for the specified channel is returned.<br/>
### oscilloscope_impedance(*impedance)
```python3
oscilloscope_impedance(*impedance)
Arguments: impedance = two strings ('channel string', 'impedance string (1 M, 50)')
or one string ('channel string'); Output: string.
Examples: oscilloscope_impedance('CH2', '1 M') sets the impedance of the channel 2 to 1 MOhm.
oscilloscope_impedance('CH2') returns the current impedance of the channel 2.
```
The function queries (if called with one argument) or sets (if called with two arguments) the impedance of one of the channels of the oscilloscope. If there is a second argument it will be set as a new impedance. If there is no second argument the current impedance for the specified channel is returned. For Keysight 2000 X-Series the only available option is 1 MOhm.<br/>
### oscilloscope_trigger_mode(*mode)
```python3
oscilloscope_trigger_mode(*mode)
Arguments: mode = string ('Auto', 'Normal'); Output: string.
Examples: oscilloscope_trigger_mode('Auto') sets the trigger mode to 1 Auto.
```
The function queries or sets the trigger mode of the oscilloscope. If there is no argument the function will return the current trigger mode (Auto or Normal). If there is an argument the specified trigger mode will be set.<br/>
When Auto sweep mode is selected, a baseline is displayed in the absence of a signal. If a signal is present but the oscilloscope is not triggered, the unsynchronized signal is displayed instead of a baseline. When Normal sweep mode is selected and no trigger is present, the instrument does not sweep, and the data acquired on the previous trigger remains on the screen.<br/>
### oscilloscope_trigger_channel(*channel)
```python3
oscilloscope_trigger_channel(*channel)
Arguments: channel = string (['CH1, CH2, CH3, CH4', 'Ext', 'Line', 'WGen']); Output: string.
Examples: oscilloscope_trigger_channel('CH3') sets the trigger channel to 3.
```
The function queries or sets the trigger channel of the oscilloscope. If there is no argument the function will return the current trigger channel ( CHAN<n>, EXT, LINE, WGEN, NONE). If all channels are off, the query returns NONE. If there is an argument the specified trigger channel will be set.<br/>
Argument Ext triggers on the rear panel EXT TRIG IN signal. Argument Line triggers at the 50% level of the rising or falling edge of the AC power source signal. Argument Wgen triggers at the 50% level of the rising edge of the waveform generator output signal. This option is not available when the DC, NOISe, or CARDiac waveforms of the waveform generator are selected.<br/>
For Keysight 4000 X-series arguments 'WGen1' and 'WGen2' can be used.<br/>
For Tektronix 3000 Series argument 'WGen' is not available, whereas there is an additional option of the external trigger mode: 'Ext10'. The 'Ext' option sets the trigger source to the regular external trigger input connector with a signal input range of -0.8 V to +0.8 V. Please, note that 'Ext' is not available in 4 channel TDS3000 Series instruments. The 'Ext10' option sets the trigger source to the reduced external trigger with a signal input range of -8 V to +8 V. It is also not available in 4 channel TDS3000 Series instruments.<br/>
For Tektronix 4000 Series arguments 'Ext' and 'WGen' are not available.<br/>
### oscilloscope_trigger_low_level(*level)
```python3
oscilloscope_trigger_low_level(*level)
Arguments: level = string + float ('channel string' ['CH1, CH2, CH3, CH4'],
float level in V) or one string ('channel string'); Output: float.
Examples: oscilloscope_trigger_low_level('CH2', 0.5) sets the low trigger 
voltage level of the channel 2 to 500 mV. oscilloscope_trigger_low_level('CH2')
returns the current low trigger voltage level of the channel 2 in V.
```
The function queries (if called with one argument) or sets (if called with two arguments) the low trigger voltage level voltage of one of the channels of the oscilloscope. If there is a second argument it will be set as a new low trigger voltage level. If there is no second argument the current low trigger voltage level for the specified channel is returned in Volts.<br/>
For Tektronix 3000 Series the 'channel string' has no meaning and is kept only for consistency.<br/>
For Tektronix 3000 and 4000 Series also presets 'ECL' and 'TTL' can be used as the first argument. ECL sets the threshold level to a preset ECL high level of -1.3 V. TTL sets the threshold level to a preset TTL high level of 1.4 V.<br/>
### oscilloscope_command(command)
```python3
oscilloscope_command(command)
Arguments: command = string; Output: none.
Example: oscilloscope_command(':TRIGger:FORCe'). This command causes an acquisition
to be captured even thoughthe trigger condition has not been met.
```
The function for sending an arbitrary command from a programming guide to the device in a string format. No output is expected.<br/>
### oscilloscope_query(command)
```python3
oscilloscope_query(command)
Arguments: command = string; Output: string.
Example: oscilloscope_query(':MEASure:FREQuency?'). This command queries an measurement
and outputs the frequency of the cycle on the screen closest to the trigger reference.
```
The function for sending an arbitrary command from a programming guide to the device in a string format. An output in a string format is expected.<br/>
