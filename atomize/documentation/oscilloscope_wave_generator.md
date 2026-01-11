---
title: Oscilloscope Wave Generators
nav_order: 33
layout: page
permlink: /functions/oscilloscope_wave_generator/
parent: Documentation
---

### Devices
- Wave Generator of Keysight InfiniiVision 2000 X-Series (Ethernet)
Available via corresponding oscilloscope module.
- Wave Generator of Keysight InfiniiVision 3000 X-Series (Ethernet)
Available via corresponding oscilloscope module.
- Wave Generator of Keysight InfiniiVision 4000 X-Series (Ethernet)
Available via corresponding oscilloscope module.
- Wave Generator of Rigol MSO8000 Series (Ethernet)
Available via corresponding oscilloscope module.

---

### Functions
- [wave_gen_name()](#wave_gen_name)<br/>
- [wave_gen_frequency(*frequency)](#wave_gen_frequencyfrequency)<br/>
- [wave_gen_pulse_width(*width)](#wave_gen_pulse_widthwidth)<br/>
- [wave_gen_function(*function)](#wave_gen_functionfunction)<br/>
- [wave_gen_amplitude(*amplitude)](#wave_gen_amplitudeamplitude)<br/>
- [wave_gen_offset(*offset)](#wave_gen_offsetoffset)<br/>
- [wave_gen_impedance(*impedance)](#wave_gen_impedanceimpedance)<br/>
- [wave_gen_start()](#wave_gen_start)<br/>
- [wave_gen_stop()](#wave_gen_stop)<br/>
- [wave_gen_phase(*phase)](#wave_gen_phasephase)<br/>
- [wave_gen_arbitrary_function_data(p_list)](#wave_gen_arbitrary_function_datap_list)<br/>
- [wave_gen_arbitrary_clear()](#wave_gen_arbitrary_clear)<br/>
- [wave_gen_arbitrary_interpolation(*mode)](#wave_gen_arbitrary_interpolationmode)<br/>
- [wave_gen_arbitrary_number_of_points()](#wave_gen_arbitrary_number_of_points)<br/>
- [wave_gen_command(command)](#wave_gen_commandcommand)<br/>
- [wave_gen_query(command)](#wave_gen_querycommand)<br/>

---

### wave_gen_name()
```python
wave_gen_name() -> str
```
The function returns device name.<br/>

---

### wave_gen_frequency(*frequency)
```python
wave_gen_frequency(frequency: float + [' MHz',' kHz',' Hz',' mHz']) -> none
wave_gen_frequency(frequency: str, channel = '1') -> none
wave_gen_frequency() -> str
wave_gen_frequency(channel = '1') -> str
```
```
Examples: wave_gen_frequency('20 kHz', channel = '2') 
sets the frequency of the waveform of the second channel of the wave generator to 20 kHz.
wave_gen_frequency('20 kHz') sets the frequency of the wave generator to 20 kHz.
```
This function queries or sets the frequency of the waveform of the wave generator. If there is no argument the function will return the current frequency in the format 'number + ['MHz', 'kHz', 'Hz', 'mHz']'. If there is an argument the specified frequency will be set. If the oscilloscope has several wave generator, the number of the generator used should be specified by corresponding keyword argument 'channel': ['1', '2']. Keysight 4000 X-series and Rigol MSO8000 Series can have up to two wave generators. If there is only one wave generator channel keyword argument is absent. The function works for all waveforms except Noise and DC.<br/>
Please, refer to the device manual for available frequency range.<br/>

---

### wave_gen_pulse_width(*width)
```python
wave_gen_pulse_width(width: float + [' s',' ms',' us',' ns']) -> none
wave_gen_pulse_width(width: str, channel = '1') -> none
wave_gen_pulse_width() -> str
wave_gen_pulse_width(channel = '1') -> str
```
```
Example: wave_gen_pulse_width('20 ms')
sets the width of the waveform of the wave generator to 20 ms.
```
This function queries or sets the width of the pulse of the wave generator. If there is no argument the function will return the current width in the format 'number + ['s', 'ms', 'us', 'ns']'. If there is an argument the specified width will be set. If the oscilloscope has several wave generator, the number of the generator used should be specified by corresponding keyword argument 'channel': ['1', '2']. Keysight 4000 X-series and Rigol MSO8000 Series can have up to two wave generators. If there is only one wave generator channel keyword argument is absent. The pulse width can be adjusted from 20 ns to the period minus 20 ns. The function available only for pulse waveforms. This function works only for the [pulsed function](#wave_gen_functionfunction).<br/>
For Rigol MSO8000 Series this function sets or queries the duty cycle of the pulse output from the specified wave generator channel. Duty cycle is defined as the percentage that the high level takes up in the whole pulse period: (width: int, channel = ['1', '2']). The available range is from 10 to 90.<br/>

---

### wave_gen_function(*function)
```python
wave_gen_function(function: str) -> none
wave_gen_function(function: str, channel = '1') -> none
wave_gen_function() -> str
wave_gen_function(channel = '1') -> str
```
```
Example: wave_gen_function('Sq') sets the sqare waveform.
```
This function queries or sets the type of waveform of the wave generator. If the oscilloscope has several wave generator, the number of the generator used should be specified by corresponding keyword argument 'channel': ['1', '2']. Keysight 4000 X-series and Rigol MSO8000 Series can have up to two wave generators. If there is only one wave generator channel keyword argument is absent.<br/>
The function type for Keysight 2000, 3000, 4000 X-series should be from the following array: ['Sin', 'Sq', 'Ramp', 'Pulse', 'DC', 'Noise', 'Sinc', 'ERise', 'EFall', 'Card', 'Gauss', 'Arb'].<br/>
The function type for Rigol MSO8000 Series should be from the following array: ['Sin', 'Sq', 'Ramp', 'Pulse', 'DC', 'Noise', 'Sinc', 'ERise', 'EFall', 'ECG', 'Gauss', 'Lorentz', 'Haversine'].<br/>

---

### wave_gen_amplitude(*amplitude)
```python
wave_gen_amplitude(amplitude: float + [' V',' mV']) -> none
wave_gen_amplitude(amplitude: str, channel = '1') -> none
wave_gen_amplitude() -> str
wave_gen_amplitude(channel = '1') -> str
```
```
Example: wave_gen_amplitude('200 mV', channel = '1') 
sets the waveform's amplitude for the first channel to 200 mV.
```
This function queries or sets the waveform amplitude. If there is no argument the function will return the current amplitude in the format 'number + ['V', 'mV']'. If there is an argument the specified amplitude will be set. If the oscilloscope has several wave generator, the number of the generator used should be specified by corresponding keyword argument 'channel': ['1', '2']. Keysight 4000 X-series and Rigol MSO8000 Series can have up to two wave generators. If there is only one wave generator channel keyword argument is absent.<br/>
Please, refer to the device manual for available amplitude range, since it depends on the impedance. Usually the range is 20 mVpp to 2.5 Vpp ('50') or to 5 Vpp ('1 M').<br/>

---

### wave_gen_offset(*offset)
```python
wave_gen_offset(offset: float + [' V',' mV']) -> none
wave_gen_offset(offset: str, channel = '1') -> none
wave_gen_offset() -> str
wave_gen_offset(channel = '1') -> str
```
```
Example: wave_gen_offset('0.5 V') sets the waveform offset voltage to 500 mV.
```
This function queries or sets the waveform offset voltage or the DC level. If there is no argument the function will return the current offset voltage in the format 'number + ['V', 'mV']'. If there is an argument the specified offset will be set. If the oscilloscope has several wave generator, the number of the generator used should be specified by corresponding keyword argument 'channel': ['1', '2']. Keysight 4000 X-series and Rigol MSO8000 Series can have up to two wave generators. If there is only one wave generator channel keyword argument is absent.<br/>

---

### wave_gen_impedance(*impedance)
```python
wave_gen_impedance(impedance: ['1 M','50']) -> none
wave_gen_impedance(impedance: str, channel = '1') -> none
wave_gen_impedance() -> str
wave_gen_impedance(channel = '1') -> str
```
```
Example: wave_gen_impedance('50') 
sets the output load impedance of the wave generator to 50 Ohm.
```
This function queries or sets the output load impedance of the wave generator. If there is no argument the function will return the current impedance. If there is an argument the specified impedance will be set. If the oscilloscope has several wave generator, the number of the generator used should be specified by corresponding keyword argument 'channel': ['1', '2']. Keysight 4000 X-series and Rigol MSO8000 Series can have up to two wave generators. If there is only one wave generator channel keyword argument is absent. The available impedance options are ['1 M', '50'].<br/>

---

### wave_gen_start()
```python
wave_gen_start() -> none
wave_gen_start(channel = '1') -> none
```
This function runs the waveform generator. This is the same as pressing the Wave Gen key on the front panel. If the oscilloscope has several wave generator, the number of the generator used should be specified by corresponding keyword argument 'channel': ['1', '2']. Keysight 4000 X-series and Rigol MSO8000 Series can have up to two wave generators. If there is only one wave generator channel keyword argument is absent.<br/>

---

### wave_gen_stop()
```python
wave_gen_stop() -> none
wave_gen_stop(channel = '1') -> none
```
This function stops the waveform generator. This is the same as pressing the Wave Gen key on the front panel. If the oscilloscope has several wave generator, the number of the generator used should be specified by corresponding keyword argument 'channel': ['1', '2']. Keysight 4000 X-series and Rigol MSO8000 Series can have up to two wave generators. If there is only one wave generator channel keyword argument is absent.<br/>

---

### wave_gen_phase(*phase)
```python
wave_gen_phase(phase: int ) -> none
wave_gen_phase(phase: int, channel = '1') -> none
wave_gen_phase() -> str
wave_gen_impedance(channel = '1') -> str
```
```
Example: wave_gen_phase(50) sets the start phase of the signal to 50 degrees.
```
This function queries or sets the start phase of the signalin degrees. If there is no argument the function will return the current start phase in the format 'number + deg'. If there is an argument the specified start phase will be set. If the oscilloscope has several wave generator, the number of the generator used should be specified by corresponding keyword argument 'channel': ['1', '2']. Keysight 4000 X-series and Rigol MSO8000 Series can have up to two wave generators. If there is only one wave generator channel keyword argument is absent. This function is available only for Keysight 4000 X-series and Rigol MSO8000 Series oscilloscopes. The available range is from 0 to 360 degrees for Rigol MSO8000 Series and from -360 to 360 for Keysight 4000 X-series. In the case of Keysight 4000 X-series oscilloscopes this funtion also swithes on 'TRACK' option. The 'TRACK' option causes frequency, amplitude, offset, and duty cycle adjustments to this wave generator output signal to be tracked by
the other wave generator output. Please note, that not all waveform shapes can be frequency tracked.<br/>

---

### wave_gen_arbitrary_function_data(p_list)
```python
wave_gen_arbitrary_function_data(p_list: list of floats) -> none
wave_gen_arbitrary_function_data(p_list: list of floats, channel = '1') -> none
```
```
Example: wave_gen_arbitrary_function_data([0, 0.5, 1, 0.5, 0, -0.5, -1, -0.5, 0])
sets the specified arbitrary waveform.
```
This function downloads an arbitrary waveform in floating-point values format. The values have to be between -1.0 to +1.0. The value -1.0 represents the minimum value, +1.0 is the maximum value, and 0.0 is equal to [the offset](#wave_gen_offsetoffset). The minimum and maximum values are determined by the [amplitude](#wave_gen_amplitudeamplitude).<br/>
The setting of an arbitrary function can be done as follow:<br/>
- [wave_gen_frequency()](#wave_gen_frequencyfrequency) gives the repetition rate of an arbitrary function.
- All available time interval (depends on the used repetition rate) is splitted by amount of points you indicate as an argument. It gives time per point. For instance, suppose the frequency is 10 Hz and we use 10 points: wave_gen_arbitrary_function_data([-1, -1, -1, 1, 1, 1, 1, -1, -1, -1]). It means the time step for one point will be (100 ms) / (10 points) = 10 ms.
- If you have the offset equals to 2 V and the amplitude 4 V as a result of wave_gen_arbitrary_function_data([-1, -1, -1, 1, 1, 1, 1, -1, -1, -1]) for 10 Hz frequency one will have a pulse 40 ms long with the low level equals to 0 V and the high level equals to 4 V.<br/>
<br/>
Function is not available for Keysight 2000 X-series and Rigol MSO8000 Series oscilloscopes. If the oscilloscope has several wave generator, the number of the generator used should be specified by corresponding keyword argument 'channel': ['1', '2']. Keysight 4000 X-series can have up to two wave generators. If there is only one wave generator channel keyword argument is absent.<br/>

---

### wave_gen_arbitrary_clear()
```python
wave_gen_arbitrary_clear() -> none
wave_gen_arbitrary_clear(channel = '1') -> none
```
This function clears the arbitrary waveform memory and loads it with the default waveform. Function is not available for Keysight 2000 X-series and Rigol MSO8000 oscilloscopes. If the oscilloscope has several wave generator, the number of the generator used should be specified by corresponding keyword argument 'channel': ['1', '2']. Keysight 4000 X-series can have up to two wave generators. If there is only one wave generator channel keyword argument is absent.<br/>

---

### wave_gen_arbitrary_interpolation(*mode)
```python
wave_gen_arbitrary_interpolation(mode: ['On','Off']) -> none
wave_gen_arbitrary_interpolation(mode: ['On','Off'], channel = '1') -> none
wave_gen_arbitrary_interpolation() -> str
wave_gen_arbitrary_interpolation(channel = '1') -> str
```
```
Example: wave_gen_arbitrary_interpolation('On') turns on the interpolation control.
```
This function enables or disables the interpolation control. If there is no argument the function will return the current interpolation setting. If there is an argument the specified interpolation setting will be set. Function is not available for Keysight 2000 X-series and Rigol MSO8000 oscilloscopes. If the oscilloscope has several wave generator, the number of the generator used should be specified by corresponding keyword argument 'channel': ['1', '2']. Keysight 4000 X-series can have up to two wave generators. If there is only one wave generator channel keyword argument is absent.<br/>
Interpolation specifies how lines are drawn between arbitrary waveform points:<br/>
When 'On', lines are drawn between points in the arbitrary waveform. Voltage levels change linearly between one point and the next.<br/>
When 'Off', all line segments in the arbitrary waveform are horizontal. The voltage level of one point remains until the next point.<br/>

---

### wave_gen_arbitrary_number_of_points()
```python
wave_gen_arbitrary_number_of_points() -> int
wave_gen_arbitrary_number_of_points(channel = '1') -> int
```
This function returns the number of points used by the current arbitrary waveform. Function is not available for Keysight 2000 X-series and Rigol MSO8000 Series oscilloscopes. If the oscilloscope has several wave generator, the number of the generator used should be specified by corresponding keyword argument 'channel': ['1', '2']. Keysight 4000 X-series can have up to two wave generators. If there is only one wave generator channel keyword argument is absent.<br/>

---

### wave_gen_command(command)
```python
wave_gen_command(command: str) -> none
```
This function sends an arbitrary command from a programming guide to the device in a string format. No output is expected.<br/>

---

### wave_gen_query(command)
```python
wave_gen_query(command: str) -> str
```
This function sends an arbitrary command from a programming guide to the device in a string format. An output in a string format is expected.<br/>