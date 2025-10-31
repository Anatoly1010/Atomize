---
title: Oscilloscope Wave Generators
nav_order: 32
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

---

### Functions
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

---

### wave_gen_name()
```python
wave_gen_name() -> str
```
The function returns device name.

---

### wave_gen_frequency(*frequency)
```python
wave_gen_frequency(frequency: str (float + [' MHz', ' kHz', ' Hz', ' mHz'])) -> none
wave_gen_frequency(frequency: str, channel = '1') -> none
wave_gen_frequency() -> float
wave_gen_frequency(channel = '1') -> float
```
```
Examples: wave_gen_frequency('20 kHz', channel = '2') 
sets the frequency of the waveform of the second channel of wave generator to 20 kHz.
wave_gen_frequency('20 kHz') sets the frequency of the wave generator to 20 kHz for 2000 and 3000 X-series.
```
This function queries or sets the frequency of the waveform of the wave generator. If there is no argument the function will return the current frequency in Hz. If there is an argument the specified frequency will be set, and additionally Keysight 4000 X-series wave generator has two channels, ['1','2'], which should be specified by corresponding argument. For Keysight 2000, 3000 X-series wave generators channel key argument are absent. The function works for all waveforms except Noise and DC.<br/>
Please, refer to a manual of the device for available frequency range.

---

### wave_gen_pulse_width(*width)
```python
wave_gen_pulse_width(width: str (float + [' s', ' ms', ' us', ' ns'])) -> none
wave_gen_pulse_width(width: str, channel = '1') -> none
wave_gen_pulse_width() -> float
wave_gen_pulse_width(channel = '1') -> float
```
```
Example: wave_gen_pulse_width('20 ms')
sets the width of the waveform of the wavegenerator to 20 ms.
```
This function queries or sets the width of the pulse of the wave generator. If there is no argument the function will return the current width in us. If there is an argument the specified width will be set, and additionally Keysight 4000 X-series wave generator has two channels, ['1','2'], which should be specified by corresponding argument. For Keysight 2000, 3000 X-series wave generators channel key argument are absent. The pulse width can be adjusted from 20 ns to the period minus 20 ns. The function available only for pulse waveforms.

---

### wave_gen_function(*function)
```python
wave_gen_function(function: str ) -> none
wave_gen_function(function: str, channel = '1') -> none
wave_gen_function() -> str
wave_gen_function(channel = '1') -> str
```
Example: wave_gen_function('Sq') sets the sqare waveform.
```
This function queries or sets the type of waveform of the wave generator.<br/>
The type should be from the following array: ['Sin', 'Sq', 'Ramp', 'Pulse', 'DC', 'Noise', 'Sinc', 'ERise', 'EFall', 'Card', 'Gauss', 'Arb'].<br/>
Keysight 4000 X-series wave generator has two channels, ['1','2'], which should be specified by corresponding argument. For Keysight 2000, 3000 X-series wave generators channel key argument are absent.

---

### wave_gen_amplitude(*amplitude)
```python
wave_gen_amplitude(amplitude: (float + [' V', ' mV']) ) -> none
wave_gen_amplitude(amplitude: str, channel = '1') -> none
wave_gen_amplitude() -> float
wave_gen_amplitude(channel = '1') -> float
```
```
Example: wave_gen_amplitude('200 mV', channel='1') 
sets the waveform's amplitude for the first channel to 200 mV.
```
This function queries or sets the waveform's amplitude. If there is no argument the function will return the current amplitude in mV. If there is an argument the specified amplitude will be set, and additionally Keysight 4000 X-series wave generator has two channels, ['1','2'], which should be specified by corresponding argument. For Keysight 2000, 3000 X-series wave generators channel key argument are absent.

---

### wave_gen_offset(*offset)
```python
wave_gen_offset(offset: (float + [' V', ' mV']) ) -> none
wave_gen_offset(offset: str, channel = '1') -> none
wave_gen_offset() -> float
wave_gen_offset(channel = '1') -> float
```
```
Example: wave_gen_offset('0.5 V') sets the waveform's offset voltage to 500 mV.
```
This function queries or sets the waveform's offset voltage or the DC level. If there is no argument the function will return the current offset voltage in mV. If there is an argument the specified offset will be set, and additionally Keysight 4000 X-series wave generator has two channels, ['1','2'], which should be specified by corresponding argument. For Keysight 2000, 3000 X-series wave generators channel key argument are absent.

---

### wave_gen_impedance(*impedance)
```python
wave_gen_impedance(impedance: str ['1 M', '50'] ) -> none
wave_gen_impedance(impedance: str, channel = '1') -> none
wave_gen_impedance() -> str
wave_gen_impedance(channel = '1') -> str
```
```
Example: wave_gen_impedance('50') 
sets the output load impedance of the wave generator to 50 Ohm.
```
This function queries or sets the output load impedance of the wave generator. If there is no argument the function will return the current impedance. If there is an argument the specified impedance will be set, and additionally Keysight 4000 X-series wave generator has two channels, ['1','2'], which should be specified by corresponding argument. For Keysight 2000, 3000 X-series wave generators channel key argument are absent.

---

### wave_gen_run()
```python
wave_gen_run() -> none
wave_gen_run(channel = '1') -> none
```
The function runs the waveform generator. This is the same as pressing the Wave Gen key on the front panel. Keysight 4000 X-series wave generator has two channels, ['1','2'], which should be specified by corresponding argument. For Keysight 2000, 3000 X-series wave generators channel key argument are absent.

---

### wave_gen_stop()
```python
wave_gen_stop() -> none
wave_gen_stop(channel = '1') -> none
```
The function stops the waveform generator. This is the same as pressing the Wave Gen key on the front panel. Keysight 4000 X-series wave generator has two channels, ['1','2'], which should be specified by corresponding argument. For Keysight 2000, 3000 X-series wave generators channel key argument are absent.

---

### wave_gen_arbitrary_function(list)
```python
wave_gen_arbitrary_function(list: list of floats) -> none
wave_gen_arbitrary_function(list: list of floats, channel = '1') -> none
```
```
Example: wave_gen_arbitrary_function([0, 0.5, 1, 0.5, 0, -0.5, -1, -0.5, 0])
sets the specified arbitrary waveform.
```
This function downloads an arbitrary waveform in floating-point values format. The values have to be between -1.0 to +1.0. The value -1.0 represents the minimum value, +1.0 - the maximum, and 0.0 is offset. These values can be changed by functions [wave_gen_amplitude(*amplitude)](#wave_gen_amplitudeamplitude) and [wave_gen_offset().](#wave_gen_offset)<br/>
The setting of an arbitrary function can be done as follow:<br/>
- [Wave_gen_frequency()](#wave_gen_frequencyfrequency) gives the repetition rate of an arbitrary function.
- All available (depends on the used repetition rate) time interval is splitted by amount of points you indicate as an argument. It gives time per point. For instance, suppose the frequency is 10 Hz and we use 10 points: wave_gen_arbitrary_function([-1, -1, -1, 1, 1, 1, 1, -1, -1, -1]). It means the time step for one point will be (100 ms) / (10 points) = 10 ms.
- If you have the offset equals to 2 V and the amplitude 4 V as a result of wave_gen_arbitrary_function([-1, -1, -1, 1, 1, 1, 1, -1, -1, -1]) for 10 Hz frequency one will have a pulse 40 ms long with the low level equals to 0 V and the high level equals to 4 V.<br/>
Function is not available for Keysight 2000 X-series oscilloscopes. Keysight 4000 X-series wave generator has two channels, ['1','2'], which should be specified by corresponding argument. For Keysight 3000 X-series wave generator channel key argument is absent.

---

### wave_gen_arbitrary_clear()
```python
wave_gen_arbitrary_clear() -> none
wave_gen_arbitrary_clear(channel = '1') -> none
```
The function clears the arbitrary waveform memory and loads it with the default waveform. Function is not available for Keysight 2000 X-series oscilloscopes. Keysight 4000 X-series wave generator has two channels, ['1','2'], which should be specified by corresponding argument. For Keysight 3000 X-series wave generator channel key argument is absent.

---

### wave_gen_arbitrary_interpolation(*mode)
```python
wave_gen_arbitrary_interpolation(mode: str) -> none
wave_gen_arbitrary_interpolation(mode: str, channel = '1') -> none
wave_gen_arbitrary_interpolation() -> str ['On', 'Off']
wave_gen_arbitrary_interpolation(channel = '1') -> str ['On', 'Off']
```
```
Example: wave_gen_arbitrary_interpolation('On') turns on the interpolation control.
```
This function enables or disables the interpolation control. If there is no argument the function will return the current interpolation setting. If there is an argument the specified interpolation setting will be set. Function is not available for Keysight 2000 X-series oscilloscopes. Keysight 4000 X-series wave generator has two channels, ['1','2'], which should be specified by corresponding argument. For Keysight 3000 X-series wave generator channel key argument is absent.<br/>
Interpolation specifies how lines are drawn between arbitrary waveform points:<br/>
When ON (1), lines are drawn between points in the arbitrary waveform. Voltage levels change linearly between one point and the next.<br/>
When OFF (0), all line segments in the arbitrary waveform are horizontal. The voltage level of one point remains until the next point.

---

### wave_gen_arbitrary_points()
```python
wave_gen_arbitrary_points() -> int
wave_gen_arbitrary_points(channel = '1') -> int
```
This function returns the number of points used by the current arbitrary waveform. Function is not available for Keysight 2000 X-series oscilloscopes. Keysight 4000 X-series wave generator has two channels, ['1','2'], which should be specified by corresponding argument. For Keysight 3000 X-series wave generator channel key argument is absent.

---

### wave_gen_command(command)
```python
wave_gen_command(command: str) -> none
```
The function for sending an arbitrary command from a programming guide to the device in a string format. No output is expected.

---

### wave_gen_query(command)
```python
wave_gen_query(command: str) -> str
```
The function for sending an arbitrary command from a programming guide to the device in a string format. An output in a string format is expected.