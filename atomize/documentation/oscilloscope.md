---
title: Oscilloscopes
nav_order: 32
layout: page
permlink: /functions/oscilloscope/
parent: Documentation
---

### Devices

- Keysight InfiniiVision 2000 X-Series (Ethernet); Tested 07/2021
- Keysight InfiniiVision 3000 X-Series (Ethernet); Tested 06/2021
- Keysight InfiniiVision 4000 X-Series (Ethernet); Untested
- Tektronix 3000 Series (Ethernet); Tested 09/2022
- Tektronix 4000 Series (Ethernet); Tested 01/2021
- Tektronix 5 Series MSO (Ethernet); Tested 12/2023
- Rigol MSO8000 Series (Ethernet); Tested 01/2026

---

### Functions
- [oscilloscope_name()](#oscilloscope_name)<br/>
- [oscilloscope_record_length(\*points)](#oscilloscope_record_lengthpoints)<br/>
- [oscilloscope_acquisition_type(\*ac_type)](#oscilloscope_acquisition_typeac_type)<br/>
- [oscilloscope_number_of_averages(\*number_of_averages)](#oscilloscope_number_of_averagesnumber_of_averages)<br/>
- [oscilloscope_timebase(\*timebase)](#oscilloscope_timebasetimebase)<br/>
- [oscilloscope_define_window(\*\*kargs)](#oscilloscope_define_windowkargs)<br/>
- [oscilloscope_time_resolution()](#oscilloscope_time_resolution)<br/>
- [oscilloscope_start_acquisition()](#oscilloscope_start_acquisition)<br/>
- [oscilloscope_preamble(channel)](#oscilloscope_preamblechannel)<br/>
- [oscilloscope_stop()](#oscilloscope_stop)<br/>
- [oscilloscope_run()](#oscilloscope_run)<br/>
- [oscilloscope_get_curve(channel)](#oscilloscope_get_curvechannel)<br/>
- [oscilloscope_get_curve(channel, mode = 'Normal')](#oscilloscope_get_curvechannel-mode--normal)<br>
- [oscilloscope_get_curve(channel, integral = False)](#oscilloscope_get_curvechannel-integral--false)<br/>
- [oscilloscope_area(channel)](#oscilloscope_areachannel)<br/>
- [oscilloscope_sensitivity(\*channel)](#oscilloscope_sensitivitychannel)<br/>
- [oscilloscope_offset(\*channel)](#oscilloscope_offsetchannel)<br/>
- [oscilloscope_horizontal_offset(\*h_offset)](#oscilloscope_horizontal_offseth_offset)<br/>
- [oscilloscope_coupling(\*coupling)](#oscilloscope_couplingcoupling)<br/>
- [oscilloscope_impedance(\*impedance)](#oscilloscope_impedanceimpedance)<br/>
- [oscilloscope_trigger_mode(\*mode)](#oscilloscope_trigger_modemode)<br/>
- [oscilloscope_trigger_channel(\*channel)](#oscilloscope_trigger_channelchannel)<br/>
- [oscilloscope_trigger_low_level(\*level)](#oscilloscope_trigger_low_levellevel)<br/>
- [oscilloscope_window()](#oscilloscope_window)<br/>
- [oscilloscope_read_settings()](#oscilloscope_read_settings)<br/>
- [oscilloscope_command(command)](#oscilloscope_commandcommand)<br/>
- [oscilloscope_query(command)](#oscilloscope_querycommand)<br/>

---

### oscilloscope_name()
```python
oscilloscope_name() -> str
```
This function returns device name.<br/>

---

### oscilloscope_record_length(\*points)
```python
oscilloscope_record_length(points: int) -> none
oscilloscope_record_length() -> int
```
```
Example: oscilloscope_record_length(4000) sets the number of waveform points to 4000.
```
This function queries or sets the number of waveform points to be transferred using [oscilloscope_get_curve()](#oscilloscope_get_curvechannel) function. If there is no number of points setting fitting the argument the nearest available value is used and warning is printed.<br/>
If one would like to use Keysight oscilloscopes without [averaging](#oscilloscope_acquisition_typeac_type) (in normal, peak or high-resolution mode), the number of points in the waveform is usually [100, 250, 500, 1000, 2000, 5000, 10000].<br/>
As stated in the programming manual, the number of points acquired cannot be directly controlled. For Keysight 3000 X-series the number of points are usually from the following array: [100, 250, 500, 1000, 2000, 4000, 8000]. For Keysight 2000 X-series: [99, 247, 479, 959, 1919, 3839, 7679]. For Keysight 4000 X-series the number of points should be checked. There is also a known bug in older firmware versions that causes an incorrect number of points to be returned during the first data collection after changing the data collection settings. Please update the oscilloscope [firmware](#https://www.keysight.com/us/en/assets/9922-03906/release-notes/Keysight-3000T-X-Series-Oscilloscope-Release-Notes-07-56.pdf).<br>
For Rigol MSO8000 Series the number of points in the waveform for normal, peak or high-resolution [mode](#oscilloscope_acquisition_typeac_type) is [1000, 10000, 1e5, 1e6, 1e7, 2.5e7, 5e7, 1e8, 1.25e8]. For the average [mode](#oscilloscope_acquisition_typeac_type) the number of points is [1000, 10000, 1e5, 1e6, 1e7, 2.5e7]. To use this feature effectively, one should disable the Auto ROLL option.<br/>
For Tektronix 3000 Series the available number of points is [500, 10000].<br/>
For Tektronix 4000 Series the available number of points is [1000, 10000, 100000, 1000000, 10000000].<br/>

---

### oscilloscope_acquisition_type(\*ac_type)
```python
oscilloscope_acquisition_type(ac_type: ['Normal','Average','Hres','Peak']) -> none
oscilloscope_acquisition_type() -> str 
```
```
Example: oscilloscope_acquisition_type('Average') sets the acquisition type to the average mode.
```
This function queries or sets the acquisition type. If there is no argument the function will return the current acquisition type. The type should be from the following array: ['Normal', 'Average', 'Hres', 'Peak']<br/>
High-resolution (also known as smoothing) mode is used to reduce noise at slower sweep speeds where the digitizer samples faster than needed to fill memory for the displayed time range.<br/>
Fot Tektronix 3000 Series 'Hres' option is not available.<br/>

---

### oscilloscope_number_of_averages(\*number_of_averages)
```python
oscilloscope_number_of_averages(number_of_averages: int) -> none
oscilloscope_number_of_averages() -> int
```
```
Example: oscilloscope_number_of_averages('2') sets the number of averages to 2.
```
This function queries or sets the number of averages. If there is no argument the function will return the current number of averages. If there is an argument the specified number of averages type will be set. If the oscilloscopes is not in the averaging acquisition mode the error message will be printed.<br/>
For Keysight oscilloscopes the number of averages should be in the range of 2 to 65536.<br/>
For Tektronix 4000 Series the number of averages should be from 2 to 512 in powers of two. Please note, that for some models the maximum number of averages is limited to 128.<br/>
For Rigol MSO8000 Series the number of averages should be from 2 to 65536 in powers of two.<br/>

---

### oscilloscope_timebase(\*timebase)
```python
oscilloscope_timebase(timebase: float + [' s',' ms',' us',' ns']) -> none
oscilloscope_timebase() -> str
```
```
Example: oscilloscope_timebase('20 us') 
sets the full-scale horizontal time to 20 us (2 us per divison).
```
This function queries or sets the full-scale horizontal time for the main window. The range is 10 times the current time-per-division setting. If there is no argument the function will return the full-scale horizontal time in the format 'number + ['ns', 'us', 'ms', 's']'. If there is an argument the specified full-scale horizontal time will be set.<br/>
For Tektronix 3000 X-series the horizontal scale is discrete and can take on a value in the range of 10 s to 1, 2, or 4 ns (depending on model), in a 1-2-4 sequence, see the array below.<br/>
For Tektronix 4000 X-series (at least for the device used for testing), the horizontal scale is discrete and can take on a value from the following array: [1, 2, 4, 10, 20, 40, 100, 200, 400] for ns, us, ms, and s scaling. In addtition timescale equals to 800 ns also can be set. If there is no timebase setting fitting the argument the nearest available value is used and warning is printed.<br/>

---

### oscilloscope_define_window(\*\*kargs)
```python
oscilloscope_define_window(start: int, stop: int) -> none
oscilloscope_define_window() -> int, int
```
```
Example: oscilloscope_define_window(start=1, stop=1000) 
the function oscilloscope_get_curve() will return the first 1000 points of the waveform.
```
This function queries or sets the starting data and ending points for waveform transfer. The function should be called with two key arguments, namely start and stop. Start is the first data point that will be transferred, which ranges from 1 to the record length. Stop is the last data point that will be transferred, which ranges from 1 to the record length.<br/>
This function is avaliable only for Tektronix 3000 Series, 4000 Series, 5 Series MSO.<br/>

---

### oscilloscope_time_resolution()
```python
oscilloscope_time_resolution() -> str
```
```
Example: oscilloscope_time_resolution() returs the current time resolution per point.
```
This function takes no arguments and returns the time resolution per point in the format 'number + ['ns', 'us', 'ms', 's']'.<br/>

---

### oscilloscope_start_acquisition()
```python
oscilloscope_start_acquisition() -> none
```
This function starts an acquisition sequence.<br/>
For Keysight and Tektronix oscilloscopes previously measured curves are discarded and new data are sampled until the desired number of averages has been reached. This function acquires all the channels currently displayed on the screen of oscilloscopes and should be called before [oscilloscope_get_curve()](#oscilloscope_get_curvechannel) function.<br>
For Rigol MSO8000 Series this function clears all the waveforms on the screen and [runs](#oscilloscope_run the oscilloscope. Note also that for Rigol MSO8000 Series, it is not possible to control the number of averages in the waveform for the 'Average' [acquisition type](#oscilloscope_acquisition_typeac_type). More details are given in the [oscilloscope_get_curve()](#oscilloscope_get_curvechannel) function.<br>

---

### oscilloscope_preamble(channel)
```python
oscilloscope_preamble(channel: ['CH1','CH2','CH3','CH4']) -> list(10-21)
```
```
Example: oscilloscope_preamble('CH3') returs the preamble for the channel 3.
```
This function requests the preamble information for the selected waveform source. The preamble data contains information concerning the vertical and horizontal scaling of the data of the corresponding channel.<br/>
Preamble format (Keysight): [format, type, points, count, xincrement, xorigin, xreference, yincrement, yorigin, yreference]<br/>
Preamble format (Tektronix): [data width, bits per point, encoding, format of the binary data, byte order, channel, coupling,
vert scale, horiz scale, record length, acq mode, number of points in waveform, point format, horiz units,
xincrement, xorigin, displayed?, vert units, vert scale mult factor, yoff, yorigin]<br/>
Preamble format (Rigol): [format, type, points, count, xincrement, xorigin, xreference, yincrement, yorigin, yreference]<br/>

---

### oscilloscope_stop()
```python
oscilloscope_stop() -> none
```
This function stops the acquisition. This is the same as pressing the stop key on the front panel.<br/>

---

### oscilloscope_run()
```python
oscilloscope_run() -> none
```
This function starts repetitive acquisitions. This is the same as pressing the run key on the front panel.<br/>

---

### oscilloscope_get_curve(channel)
```python
oscilloscope_get_curve(channel: ['CH1','CH2','CH3','CH4']) -> np.array
```
```
Example: oscilloscope_get_curve('CH2') returs the data from the channel 2.
```
This function returns a waveform (y-axis values only) from specified channel of the oscilloscope. Values are given in volts. At the moment, it expects one argument, namely the channel from which the data should be transferred. The data from two channels can be transferred sequentially.<br>
If you need to get both the x- and y-axis, consider using the [oscilloscope_get_curve(integral = False)](#oscilloscope_get_curvechannel-integral--false)) function.<br>
For Rigol MSO8000 Series, it is not possible to control the number of averages in the waveform for the 'Average' [acquisition type](#oscilloscope_acquisition_typeac_type). This function [returns](#oscilloscope_get_curvechannel-mode--normal) the waveform data on the screen or from the internal memory.<br>

---

### oscilloscope_get_curve(channel, mode = 'Normal')
```python
oscilloscope_get_curve(channel: ['CH1','CH2','CH3','CH4'], mode = ['Normal','Raw']) -> np.array
```
```
Example: oscilloscope_get_curve('CH2', mode = 'Normal') returs the data from the channel 2
currently displayed on the screen.
```
For Rigol MSO8000 Series, there is an additional keyword 'mode' = ['Normal', 'Raw'], which is used to specify the data return mode. The default option is 'Normal'. In 'Normal' mode, the oscilloscope returns the waveform data currently displayed on the screen. In 'Raw' mode, the oscilloscpe returns the waveform data from the internal memory.<br>

---

### oscilloscope_get_curve(channel, integral = False)
```python
oscilloscope_get_curve(channel: ['CH1','CH2','CH3','CH4'], integral = [True, False]) -> float
```
```
Example: oscilloscope_get_curve('CH1', integral = True) 
runs acquisition and returns the integrated data from the channel 1.
```
This function runs acquisition and returns the data, integrated over a window in the oscillogram for the indicated channel. The window can be indicated by the [oscilloscope_window](#oscilloscope_window) function. The integral is returned in volt-seconds. The default option is False.<br>
For Rigol MSO8000 Series, it is not possible to control the number of averages in the waveform for the 'Average' [acquisition type](#oscilloscope_acquisition_typeac_type). This function returns the waveform data on the screen or from the internal memory. There is an additional keyword 'mode' = ['Normal', 'Raw'], which is used to specify the data return [mode](#oscilloscope_get_curvechannel-mode--normal).<br>
This function is only available for Keysight 2000, 3000, 4000 X-Series and Rigol MSO8000 Series oscilloscopes.<br>

---

### oscilloscope_area(channel)
```python
oscilloscope_area(channel: ['CH1','CH2','CH3','CH4']) -> float
```
```
Example: oscilloscope_area('CH2') returs the result of an area measurement for channel 2.
```
This function returns a value of area in volt-seconds between the waveform and the ground level for specified channel of the oscilloscope. It expects one argument, namely the channel for which the area should be measured. This function is available for Keysight 2000, 3000, 4000 X-Series and Rigol MSO8000 Series oscilloscopes.<br/>

---

### oscilloscope_sensitivity(\*channel)
```python
oscilloscope_sensitivity(channel: str, sensitivity: int + [' V',' mV']) -> none
oscilloscope_sensitivity(channel: ['CH1','CH2','CH3','CH4']) -> str
```
```
Examples: oscilloscope_sensitivity('CH2', '100 mV') sets the sensitivity 
per division of the channel 2 to 100 mV. 
oscilloscope_sensitivity('CH2') returns the current sensitivity of the channel 2.
```
This function queries (if called with one argument) or sets (if called with two arguments) the sensitivity per division of one of the channels of the oscilloscope. If there is a second argument it will be set as a new sensitivity. If there is no second argument the current sensitivity for specified the channel is returned in the format 'number + ['mV', 'V']'.<br/>

---

### oscilloscope_offset(\*channel)
```python
oscilloscope_offset(*channel)
oscilloscope_offset(channel: str, offset: float + [' V',' mV']) -> none
oscilloscope_offset(channel: ['CH1','CH2','CH3','CH4']) -> str
```
```
Examples: oscilloscope_offset('CH2', '100 mV') sets the offset setting of the channel 2 to 100 mV. 
oscilloscope_offset('CH2') returns the current offset of the channel 2.
```
This function queries (if called with one argument) or sets (if called with two arguments) the offset setting of one of the channels of the oscilloscope. If there is a second argument it will be set as a new offset setting. If there is no second argument the current offset setting for the specified channel is returned in the format 'number + ['mV', 'V']'. The offset range depends on the type of oscilliscope, the vertical scale factor for used channel, and the impedance. Please, refer to device manuals.<br/>

---

### oscilloscope_horizontal_offset(\*h_offset)
```python
oscilloscope_horizontal_offset(h_offset: float + [' s',' ms',' us',' ns']) -> none
oscilloscope_horizontal_offset() -> str
```
```
Example: oscilloscope_horizontal_offset('100 ms') sets the time base delay to 100 ms.
```
This function queries or sets the horizontal delay time (position). This delay is the time between the trigger event and the delay reference point on the screen. If there is no argument the function will return the current delay mode in the format 'number + ['s', 'ms', 'us', 'ns']'. If there is an argument the specified delay mode will be set. The valid range for delay settings depends on the time/division setting for the main time base.<br/>

---

### oscilloscope_coupling(\*coupling)
```python
oscilloscope_coupling(channel: str, coupling: str ['AC','DC']) -> none
oscilloscope_coupling(channel: ['CH1','CH2','CH3','CH4']) -> str
```
```
Examples: oscilloscope_coupling('CH2', 'AC') sets the coupling of the channel 2 to AC.
oscilloscope_coupling('CH2') returns the current coupling of the channel 2.
```
This function queries (if called with one argument) or sets (if called with two arguments) the coupling of one of the channels of the oscilloscope. If there is a second argument it will be set as a new coupling. If there is no second argument the current coupling for the specified channel is returned.<br/>
Possible coupling settings are the following: ['AC', 'DC'].<br/>
For Rigol MSO8000 Series 'AC' option is only available for '1 M' [impedance](#oscilloscope_impedanceimpedance) setting.<br/>

---

### oscilloscope_impedance(\*impedance)
```python
oscilloscope_impedance(*impedance)
oscilloscope_impedance(channel: str, impedance: str ['1 M','50']) -> none
oscilloscope_impedance(channel: ['CH1','CH2','CH3','CH4']) -> str
```
```
Examples: oscilloscope_impedance('CH2', '1 M') sets the impedance of the channel 2 to 1 MOhm.
oscilloscope_impedance('CH2') returns the current impedance of the channel 2.
```
This function queries (if called with one argument) or sets (if called with two arguments) the impedance of one of the channels of the oscilloscope. If there is a second argument it will be set as a new impedance. If there is no second argument the current impedance for the specified channel is returned. Possible impedance settings are the following: ['1 M', '50'].<br/>
For Keysight 2000 X-Series the only available option is '1 M'.<br/>

---

### oscilloscope_trigger_mode(\*mode)
```python
oscilloscope_trigger_mode(mode: ['Auto','Normal']) -> str
oscilloscope_trigger_mode() -> str
```
```
Examples: oscilloscope_trigger_mode('Auto') sets the trigger mode to Auto.
```
This function queries or sets the trigger mode of the oscilloscope. If there is no argument the function will return the current trigger mode. If there is an argument the specified trigger mode will be set.<br/>
Possible trigger mode settings are the following: ['Auto', 'Normal']. When 'Auto' sweep mode is selected, a baseline is displayed in the absence of a signal. If a signal is present but the oscilloscope is not triggered, the unsynchronized signal is displayed instead of a baseline. When 'Normal' sweep mode is selected and no trigger is present, the instrument does not sweep, and the data acquired on the previous trigger remains on the screen.<br/>

---

### oscilloscope_trigger_channel(\*channel)
```python
oscilloscope_trigger_channel(channel: ['CH1','CH2','CH3','CH4','Ext','Line','WGen']) -> none
oscilloscope_trigger_channel() -> str
```
```
Examples: oscilloscope_trigger_channel('CH3') sets the trigger channel to 3.
```
This function queries or sets the trigger channel of the oscilloscope. If there is no argument the function will return the current trigger channel (CHANn, EXT, LINE, WGEN, NONE). If all channels are off, the query returns NONE. If there is an argument the specified trigger channel will be set.<br/>
The 'Ext' option triggers the oscilloscope using the EXT TRIG IN signal on the rear panel. The 'Line' option triggers the oscilloscope at 50% of the rising or falling edge of the AC power source signal. The 'WGen' argument triggers the oscilloscope at the 50% level of the rising edge of the waveform generator output signal. This option is not available when the DC, NOISe, or CARDiac waveforms of the waveform generator are selected.<br/>
For Keysight 4000 X-series arguments 'WGen1' and 'WGen2' can be used.<br/>
For Tektronix 3000 Series argument 'WGen' is not available, whereas there is an additional option of the external trigger mode: 'Ext10'. The 'Ext' option sets the trigger source to the regular external trigger input connector with a signal input range of -0.8 V to +0.8 V. Please, note that 'Ext' is not available in 4 channel TDS3000 Series instruments. The 'Ext10' option sets the trigger source to the reduced external trigger with a signal input range of -8 V to +8 V. It is also not available in 4 channel TDS3000 Series instruments.<br/>
For Tektronix 4000 Series arguments 'Ext' and 'WGen' are not available.<br/>
For Rigol MSO8000 Series arguments 'WGen' is not available.<br/>

---

### oscilloscope_trigger_low_level(\*level)
```python
oscilloscope_trigger_low_level(channel: ['CH1','CH2','CH3','CH4'], level: float) -> none
oscilloscope_trigger_low_level(channel: str) -> str
```
```
Examples: oscilloscope_trigger_low_level('CH2', 0.5) sets the low trigger voltage level 
of the channel 2 to 500 mV. 
oscilloscope_trigger_low_level('CH2') returns the current low trigger level of the channel 2 in V.
```
This function queries (if called with one argument) or sets (if called with two arguments) the low trigger voltage level voltage of one of the channels of the oscilloscope. If there is a second argument it will be set as a new low trigger voltage level. If there is no second argument the current low trigger voltage level for the specified channel is returned in the format 'number + ['mV', 'V']'.<br/>
For Tektronix 3000 Series and Rigol MSO8000 Series the 'channel string' has no meaning and is kept only for consistency.<br/>
For Tektronix 3000 and 4000 Series also presets 'ECL' and 'TTL' can be used as the first argument. ECL sets the threshold level to a preset ECL high level of -1.3 V. TTL sets the threshold level to a preset TTL high level of 1.4 V.<br/>

---

### oscilloscope_read_settings()
```python
oscilloscope_read_settings() -> none
```
```
Examples: oscilloscope_read_settings() reads all the settings of the oscilloscope.
```
This function reads all the settings from a special text file [digitizer.param](https://github.com/Anatoly1010/Atomize_ITC/tree/master/atomize/control_center).<br>
This function is only available for Keysight 2000, 3000, 4000 X-Series and Rigol MSO8000 Series oscilloscopes.<br>

---

### oscilloscope_window()
```python
oscilloscope_window() -> float
```
```
Examples: oscilloscope_window() returns the integration window of the oscilloscope.
```
This function returns the integration window of the oscilloscope. The integration window is used in the [oscilloscope_get_curve()](#oscilloscope_get_curvechannel-integral--false) function and is set via a special text file [digitizer.param](https://github.com/Anatoly1010/Atomize_ITC/tree/master/atomize/control_center).<br>
This function is only available for Keysight 2000, 3000, 4000 X-Series and Rigol MSO8000 Series oscilloscopes.<br>

---

### oscilloscope_command(command)
```python
oscilloscope_command(command: str) -> none
```
```
Example: oscilloscope_command(':TRIGger:FORCe'). This command causes an acquisition
to be captured even though the trigger condition has not been met.
```
This function sends an arbitrary command from a programming guide to the device in a string format. No output is expected.<br/>

---

### oscilloscope_query(command)
```python
oscilloscope_query(command: str) -> str
```
```
Example: oscilloscope_query(':MEASure:FREQuency?'). This command queries an measurement
and outputs the frequency of the cycle on the screen closest to the trigger reference.
```
This function sends an arbitrary command from a programming guide to the device in a string format. An output in a string format is expected.<br/>
