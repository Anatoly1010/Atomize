# List of available functions for oscilloscope wave generators

Available devices:
- Wave Generator of Keysight InfiniiVision 2000 X-Series (Ethernet)
Available via corresponding oscilloscope module.
- Wave Generator of Keysight InfiniiVision 3000 X-Series (Ethernet)
Available via corresponding oscilloscope module.
- Wave Generator of Keysight InfiniiVision 4000 X-Series (Ethernet)
Available via corresponding oscilloscope module.

Functions:
- [wave_gen_name()](#wave_gen_name)<br/>
- [wave_gen_frequency(*frequency)](#wave_gen_frequencyfrequency)<br/>
- [wave_gen_pulse_width(*width)](#wave_gen_pulse_widthwidth)<br/>
- [wave_gen_function(*function)](#wave_gen_functionfunction)<br/>
- [wave_gen_amplitude(*amplitude)](#wave_gen_amplitudeamplitude)<br/>
- [wave_gen_offset(*offset)](#wave_gen_offsetoffset)<br/>
- [wave_gen_impedance(*impedance)](#wave_gen_impedanceimpedance)<br/>
- [wave_gen_run()](#wave_gen_run)<br/>
- [wave_gen_stop()](#wave_gen_stop)<br/>
- [wave_gen_arbitrary_function(list)](#wave_gen_arbitrary_functionlist)<br/>
- [wave_gen_arbitrary_clear()](#wave_gen_arbitrary_clear)<br/>
- [wave_gen_arbitrary_interpolation(*mode)](#wave_gen_arbitrary_interpolationmode)<br/>
- [wave_gen_arbitrary_points()](#wave_gen_arbitrary_points)<br/>
- [wave_gen_command(command)](#wave_gen_commandcommand)<br/>
- [wave_gen_query(command)](#wave_gen_querycommand)<br/>

### wave_gen_name()
```python3
wave_gen_name()
Arguments: none; Output: string.
```
The function returns device name.
### wave_gen_frequency(*frequency)
```python3
wave_gen_frequency(*frequency)
wave_gen_frequency(*frequency, channel = '1')
Arguments: frequency = string ('number + scaling (MHz, kHz, Hz, mHz)'); Key arguments: channel = ['1','2'];
Output: float (in Hz).
Keysight 4000 X-series wave generator has two channels, which should be specified by corresponding argument.
Examples: wave_gen_frequency('20 kHz', channel = '2') sets the frequency of the waveform of the second channel
of wave generator to 20 kHz; wave_gen_frequency('20 kHz') sets the frequency of the wave generator to 20 kHz
for 2000 and 3000 X-series.
```
This function queries or sets the frequency of the waveform of the wave generator. If there is no argument the function will return the current frequency in Hz. If there is an argument the specified frequency will be set. The function works for all waveforms except Noise and DC.<br/>
Please, refer to a manual of the device for available frequency range. For Keysight 2000, 3000 X-series wave generators channel key argument is absent.<br/>
### wave_gen_pulse_width(*width)
```python3
wave_gen_pulse_width(*width)
wave_gen_pulse_width(*width, channel = '1')
Arguments: width = string ('number + scaling (s, ms, us, ns)'); Key arguments: channel = ['1','2'];
Output: float (in us).
Keysight 4000 X-series wave generator has two channels, which should be specified by corresponding argument.
Example: wave_gen_pulse_width('20 ms') sets the width of the waveform of the wave
generator to 20 ms.
```
This function queries or sets the width of the pulse of the wave generator. If there is no argument the function will return the current width in us. If there is an argument the specified width will be set. The pulse width can be adjusted from 20 ns to the period minus 20 ns. The function available only for pulse waveforms. For Keysight 2000, 3000 X-series wave generators channel key argument is absent.<br/>
### wave_gen_function(*function)
```python3
wave_gen_function(*function)
wave_gen_function(*function, channel = '1')
Arguments: function = string from a specified dictionary, channel = ['1','2']; Key arguments: channel = ['1','2'];
Output: string.
Keysight 4000 X-series wave generator has two channels, which should be specified by corresponding argument.
Example: wave_gen_function('Sq') sets the sqare waveform.
```
This function queries or sets the type of waveform of the wave generator. The type should be from the following array:<br/>
['Sin', 'Sq', 'Ramp', 'Pulse', 'DC', 'Noise', 'Sinc', 'ERise', 'EFall', 'Card', 'Gauss', 'Arb']. For Keysight 2000, 3000 X-series wave generators channel key argument is absent.<br/>
### wave_gen_amplitude(*amplitude)
```python3
wave_gen_amplitude(*amplitude)
wave_gen_amplitude(*amplitude, channel = '1')
Arguments: amplitude = string ('number + scaling (V, mV)'); Key arguments: channel = ['1','2'];
Output: float (in mV).
Keysight 4000 X-series wave generator has two channels, which should be specified by corresponding argument.
Example: wave_gen_amplitude('200 mV', channel='1') sets the waveform's amplitude for the first
channel to 200 mV.
```
This function queries or sets the waveform's amplitude. If there is no argument the function will return the current amplitude in mV. If there is an argument the specified amplitude will be set. The function available for all waveforms except DC. For Keysight 2000, 3000 X-series wave generators channel key argument is absent.<br/>
### wave_gen_offset(*offset)
```python3
wave_gen_offset(*offset)
wave_gen_offset(*offset, channel = '1')
Arguments: offset = string ('number + scaling (V, mV)'); Key arguments: channel = ['1','2'];
Output: float (in mV).
Keysight 4000 X-series wave generator has two channels, which should be specified by corresponding argument.
Example: wave_gen_offset('0.5 V') sets the waveform's offset voltage to 500 mV.
```
This function queries or sets the waveform's offset voltage or the DC level. If there is no argument the function will return the current offset voltage in mV. If there is an argument the specified offset will be set. For Keysight 2000, 3000 X-series wave generators channel key argument is absent.<br/>
### wave_gen_impedance(*impedance)
```python3
wave_gen_impedance(*impedance)
wave_gen_impedance(*impedance, channel = '1')
Arguments: offset = string ('impedance string (1 M, 50)'); Key arguments: channel = ['1','2'];
Output: string.
Keysight 4000 X-series wave generator has two channels, which should be specified by corresponding argument.
Example: wave_gen_impedance('50') sets the output load impedance of the wave generator
to 50 Ohm.
```
This function queries or sets the output load impedance of the wave generator. If there is no argument the function will return the current impedance. If there is an argument the specified impedance will be set. For Keysight 2000, 3000 X-series wave generators channel key argument is absent.<br/>
### wave_gen_run()
```python3
wave_gen_run()
wave_gen_run(channel = '1')
Arguments: none; Key arguments: channel = ['1','2']; Output: none.
Keysight 4000 X-series wave generator has two channels, which should be specified by corresponding argument.
```
The function runs the waveform generator. This is the same as pressing the Wave Gen key on the front panel. For Keysight 2000, 3000 X-series wave generators channel key argument is absent.
### wave_gen_stop()
```python3
wave_gen_stop()
wave_gen_stop(channel = '1')
Arguments: none; Key arguments: channel = ['1','2']; Output: none.
Keysight 4000 X-series wave generator has two channels, which should be specified by corresponding argument.
```
The function stops the waveform generator. This is the same as pressing the Wave Gen key on the front panel. For Keysight 2000, 3000 X-series wave generators channel key argument is absent.
### wave_gen_arbitrary_function(list)
```python3
wave_gen_arbitrary_function(list)
wave_gen_arbitrary_function(list, channel = '1')
Arguments: list of floats ([first_point, second_point, ...]); Key arguments: channel = ['1','2'];
Output: none.
Keysight 4000 X-series wave generator has two channels, which should be specified by corresponding argument.
Example: wave_gen_arbitrary_function([0, 0.5, 1, 0.5, 0, -0.5, -1, -0.5, 0])
sets the specified arbitrary waveform.
```
This function downloads an arbitrary waveform in floating-point values format. The values have to be between -1.0 to +1.0. The value -1.0 represents the minimum value, +1.0 - the maximum, and 0.0 is offset. These values can be changed by functions [wave_gen_amplitude(*amplitude)](#wave_gen_amplitudeamplitude) and [wave_gen_offset().](#wave_gen_offset)<br/>
The setting of an arbitrary function can be done as follow:<br/>
- [Wave_gen_frequency()](#wave_gen_frequencyfrequency) gives the repetition rate of an arbitrary function.
- All available (depends on the used repetition rate) time interval is splitted by amount of points you indicate as an argument. It gives time per point. For instance, suppose the frequency is 10 Hz and we use 10 points: wave_gen_arbitrary_function([-1, -1, -1, 1, 1, 1, 1, -1, -1, -1]). It means the time step for one point will be (100 ms) / (10 points) = 10 ms.
- If you have the offset equals to 2 V and the amplitude 4 V as a result of wave_gen_arbitrary_function([-1, -1, -1, 1, 1, 1, 1, -1, -1, -1]) for 10 Hz frequency one will have a pulse 40 ms long with the low level equals to 0 V and the high level equals to 4 V.<br/>
Function is not available for Keysight 2000 X-series oscilloscopes. For Keysight 3000 X-series wave generator channel key argument is absent.<br/>
### wave_gen_arbitrary_clear()
```python3
wave_gen_arbitrary_clear()
wave_gen_arbitrary_clear(channel = '1')
Arguments: none; Key arguments: channel = ['1','2']; Output: none.
Keysight 4000 X-series wave generator has two channels, which should be specified by corresponding argument.
```
The function clears the arbitrary waveform memory and loads it with the default waveform. Function is not available for Keysight 2000 X-series oscilloscopes. For Keysight 3000 X-series wave generator channel key argument is absent.
### wave_gen_arbitrary_interpolation(*mode)
```python3
wave_gen_arbitrary_interpolation(*mode)
wave_gen_arbitrary_interpolation(*mode, channel = '1')
Arguments: mode = string (['On', 'Off']); Key arguments: channel = ['1','2']; Output: string.
Keysight 4000 X-series wave generator has two channels, which should be specified by corresponding argument.
Example: wave_gen_arbitrary_interpolation('On') turns on the interpolation control.
```
This function enables or disables the interpolation control. If there is no argument the function will return the current interpolation setting. If there is an argument the specified interpolation setting will be set. Function is not available for Keysight 2000 X-series oscilloscopes. For Keysight 3000 X-series wave generator channel key argument is absent.<br/>
Interpolation specifies how lines are drawn between arbitrary waveform points:<br/>
When ON (1), lines are drawn between points in the arbitrary waveform. Voltage levels change linearly between one point and the next.<br/>
When OFF (0), all line segments in the arbitrary waveform are horizontal. The voltage level of one point remains until the next point.<br/>
### wave_gen_arbitrary_points()
```python3
wave_gen_arbitrary_points()
wave_gen_arbitrary_points(channel = '1')
Arguments: none; Key arguments: channel = ['1','2']; Output: integer.
Keysight 4000 X-series wave generator has two channels, which should be specified by corresponding argument.
```
This function returns the number of points used by the current arbitrary waveform. Function is not available for Keysight 2000 X-series oscilloscopes. For Keysight 3000 X-series wave generator channel key argument is absent.
### wave_gen_command(command)
```python3
wave_gen_command(command)
Arguments: command = string; Output: none.
```
The function for sending an arbitrary command from a programming guide to the device in a string format. No output is expected.<br/>
### wave_gen_query(command)
```python3
wave_gen_query(command)
Arguments: command = string; Output: string.
```
The function for sending an arbitrary command from a programming guide to the device in a string format. An output in a string format is expected.<br/>
