---
title: Waveform Generators
nav_order: 38
layout: page
permlink: /functions/wave_generator/
parent: Documentation
---

### Devices
- Waveform Generator of Keysight InfiniiVision 2000 X-Series (Ethernet)
Available via corresponding oscilloscope module.
- Waveform Generator of Keysight InfiniiVision 3000 X-Series (Ethernet)
Available via corresponding oscilloscope module.
- Waveform Generator of Keysight InfiniiVision 4000 X-Series (Ethernet)
Available via corresponding oscilloscope module.
- Waveform Generator of Rigol MSO8000 Series (Ethernet)
Available via corresponding oscilloscope module.
- Stanford Research DS345 (RS-232; GPIB: linux-gpib; pyvisa-py); Tested 01/2026.

The availability of a waveform generator should be specified in the configuration file located in the ["DEVICE CONFIG DIRECTORY"](/atomize_docs/pages/usage):
```yml
wave_gen = False
wave_gen = True
```

---

### Functions
- [wave_gen_name()](#wave_gen_name)<br/>
- [wave_gen_frequency(\*frequency)](#wave_gen_frequencyfrequency)<br/>
- [wave_gen_pulse_width(\*width)](#wave_gen_pulse_widthwidth)<br/>
- [wave_gen_function(\*function)](#wave_gen_functionfunction)<br/>
- [wave_gen_amplitude(\*amplitude)](#wave_gen_amplitudeamplitude)<br/>
- [wave_gen_offset(\*offset)](#wave_gen_offsetoffset)<br/>
- [wave_gen_impedance(\*impedance)](#wave_gen_impedanceimpedance)<br/>
- [wave_gen_start()](#wave_gen_start)<br/>
- [wave_gen_stop()](#wave_gen_stop)<br/>
- [wave_gen_phase(\*phase)](#wave_gen_phasephase)<br/>
- [wave_gen_modulation_function(\*function)](#wave_gen_modulation_functionfunction)<br>
- [wave_gen_modulation_type(\*type)](#wave_gen_modulation_typetype)<br>
- [wave_gen_modulation_depth(\*depth)](#wave_gen_modulation_depthdepth)<br>
- [wave_gen_modulation_frequency_span(\*span)](#wave_gen_modulation_frequency_spanspan)<br>
- [wave_gen_modulation_phase_span(\*span)](#wave_gen_modulation_phase_spanspan)<br>
- [wave_gen_modulation_status(\*status)](#wave_gen_modulation_statusstatus)<br>
- [wave_gen_modulation_frequency_sweep(\*\*kargs)](#wave_gen_modulation_frequency_sweepkargs)<br>
- [wave_gen_modulation_rate(\*rate)](#wave_gen_modulation_raterate)<br>
- [wave_gen_modulation_trigger_source(\*tr_type)](#wave_gen_modulation_trigger_sourcetr_type)<br>
- [wave_gen_modulation_trigger_rate(\*rate)](#wave_gen_modulation_trigger_raterate)<br>
- [wave_gen_modulation_trigger()](#wave_gen_modulation_trigger)<br>
- [wave_gen_modulation_burst_count(\*count)](#wave_gen_modulation_burst_countcount)<br>
- [wave_gen_modulation_hop_frequency(\*frequency)](#wave_gen_modulation_hop_frequencyfrequency)<br> 
- [wave_gen_modulation_hop_rate(\*rate)](#wave_gen_modulation_hop_raterate)<br>
- [wave_gen_arbitrary_amplitude_modulation(p_list)](#wave_gen_arbitrary_amplitude_modulationp_list)<br>
- [wave_gen_arbitrary_frequency_modulation(p_list)](#wave_gen_arbitrary_frequency_modulationp_list)<br>
- [wave_gen_arbitrary_phase_modulation(p_list)](#wave_gen_arbitrary_phase_modulationp_list)<br>
- [wave_gen_arbitrary_modulation_rate_divider(\*rate)](#wave_gen_arbitrary_modulation_rate_dividerrate)<br>
- [wave_gen_arbitrary_function_data(p_list)](#wave_gen_arbitrary_function_datap_list)<br/>
- [wave_gen_arbitrary_frequency(\*frequency)](#wave_gen_arbitrary_frequencyfrequency)<br>
- [wave_gen_arbitrary_clear()](#wave_gen_arbitrary_clear)<br/>
- [wave_gen_arbitrary_interpolation(\*mode)](#wave_gen_arbitrary_interpolationmode)<br/>
- [wave_gen_arbitrary_number_of_points()](#wave_gen_arbitrary_number_of_points)<br>
- [wave_gen_command(command)](#wave_gen_commandcommand)<br/>
- [wave_gen_query(command)](#wave_gen_querycommand)<br/>

---

### wave_gen_name()
```python
wave_gen_name() -> str
```
The function returns device name.<br/>

---

### wave_gen_frequency(\*frequency)
```python
wave_gen_frequency(frequency: float + [' MHz',' kHz',' Hz',' mHz']) -> none
wave_gen_frequency(frequency: str, channel = '1') -> none
wave_gen_frequency() -> str
wave_gen_frequency(channel = '1') -> str
```
```
Examples: wave_gen_frequency('20 kHz', channel = '2') 
sets the frequency of the waveform of the second channel of the waveform generator to 20 kHz.
wave_gen_frequency('20 kHz') sets the frequency of the waveform generator to 20 kHz.
```
This function queries or sets the frequency of the waveform of the waveform generator. If there is no argument the function will return the current frequency in the format 'number + ['MHz', 'kHz', 'Hz', 'mHz']'. If there is an argument the specified frequency will be set. If the oscilloscope or waveform generator has several waveform generator, the number of the generator used should be specified by corresponding keyword argument 'channel': ['1', '2']. Keysight 4000 X-series and Rigol MSO8000 Series can have up to two waveform generators. If there is only one waveform generator channel keyword argument is absent. The function works for all waveforms except Noise and DC.<br/>
Please, refer to the device manual for available frequency range, since it depends on the function type.<br/>

---

### wave_gen_pulse_width(\*width)
```python
wave_gen_pulse_width(width: float + [' s',' ms',' us',' ns']) -> none
wave_gen_pulse_width(width: str, channel = '1') -> none
wave_gen_pulse_width() -> str
wave_gen_pulse_width(channel = '1') -> str
```
```
Example: wave_gen_pulse_width('20 ms')
sets the width of the waveform of the waveform generator to 20 ms.
```
This function queries or sets the width of the pulse of the waveform generator. If there is no argument the function will return the current width in the format 'number + ['s', 'ms', 'us', 'ns']'. If there is an argument the specified width will be set. If the oscilloscope or waveform generator has several waveform generator, the number of the generator used should be specified by corresponding keyword argument 'channel': ['1', '2']. Keysight 4000 X-series and Rigol MSO8000 Series can have up to two waveform generators. If there is only one waveform generator channel keyword argument is absent. The pulse width can be adjusted from 20 ns to the period minus 20 ns. The function available only for pulse waveforms. This function works only for the [pulsed function](#wave_gen_functionfunction).<br/>
For Rigol MSO8000 Series this function sets or queries the duty cycle of the pulse output from the specified waveform generator channel. Duty cycle is defined as the percentage that the high level takes up in the whole pulse period: (width: int, channel = ['1', '2']). The available range is from 10 to 90.<br/>
This function is not available for Stanford Research DS345.<br>

---

### wave_gen_function(\*function)
```python
wave_gen_function(function: str) -> none
wave_gen_function(function: str, channel = '1') -> none
wave_gen_function() -> str
wave_gen_function(channel = '1') -> str
```
```
Example: wave_gen_function('Sq') sets the sqare waveform.
```
This function queries or sets the type of waveform of the waveform generator. If the oscilloscope or waveform generator has several waveform generator, the number of the generator used should be specified by corresponding keyword argument 'channel': ['1', '2']. Keysight 4000 X-series and Rigol MSO8000 Series can have up to two waveform generators. If there is only one waveform generator channel keyword argument is absent.<br/>
The function type for Keysight 2000, 3000, 4000 X-series should be from the following array: ['Sin', 'Sq', 'Ramp', 'Pulse', 'DC', 'Noise', 'Sinc', 'ERise', 'EFall', 'Card', 'Gauss', 'Arb'].<br/>
The function type for Rigol MSO8000 Series should be from the following array: ['Sin', 'Sq', 'Ramp', 'Pulse', 'DC', 'Noise', 'Sinc', 'ERise', 'EFall', 'ECG', 'Gauss', 'Lorentz', 'Haversine'].
The function type for Stanford Research DS345 should be from the following array: ['Sin', 'Sq', 'Triangle', 'Ramp', 'Noise', 'Arb'].<br/>

---

### wave_gen_amplitude(\*amplitude)
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
This function queries or sets the waveform peak-to-peak amplitude. If there is no argument the function will return the current amplitude in the format 'number + ['V', 'mV']'. If there is an argument the specified amplitude will be set. If the oscilloscope or waveform generator has several waveform generator, the number of the generator used should be specified by corresponding keyword argument 'channel': ['1', '2']. Keysight 4000 X-series and Rigol MSO8000 Series can have up to two waveform generators. If there is only one waveform generator channel keyword argument is absent.<br/>
Please, refer to the device manual for available amplitude range, since it depends on the impedance. Usually the range is from 20 mVpp to 2.5 Vpp ('50') or to 5 Vpp ('1 M').<br/>
For Stanford Research DS345 the available range is from 0 Vpp to 5 Vpp. There are also two special presets ['TTL', 'ECL'] for setting peak-to-peak amplitude and offset to 5 V, 2.5 V and 1 V, -1.3 V, respectively for 'TTL' and 'ECL'.<br>

---

### wave_gen_offset(\*offset)
```python
wave_gen_offset(offset: float + [' V',' mV']) -> none
wave_gen_offset(offset: str, channel = '1') -> none
wave_gen_offset() -> str
wave_gen_offset(channel = '1') -> str
```
```
Example: wave_gen_offset('0.5 V') sets the waveform offset voltage to 500 mV.
```
This function queries or sets the waveform offset voltage or the DC level. If there is no argument the function will return the current offset voltage in the format 'number + ['V', 'mV']'. If there is an argument the specified offset will be set. If the oscilloscope or waveform generator has several waveform generator, the number of the generator used should be specified by corresponding keyword argument 'channel': ['1', '2']. Keysight 4000 X-series and Rigol MSO8000 Series can have up to two waveform generators. If there is only one waveform generator channel keyword argument is absent.<br/>
For Stanford Research DS345 the available range of amplitude and offset sum is from 0 Vpp to 5 Vpp.<br>


---

### wave_gen_impedance(\*impedance)
```python
wave_gen_impedance(impedance: ['1 M','50']) -> none
wave_gen_impedance(impedance: str, channel = '1') -> none
wave_gen_impedance() -> str
wave_gen_impedance(channel = '1') -> str
```
```
Example: wave_gen_impedance('50') 
sets the output load impedance of the waveform generator to 50 Ohm.
```
This function queries or sets the output load impedance of the waveform generator. If there is no argument the function will return the current impedance. If there is an argument the specified impedance will be set. If the oscilloscope or waveform generator has several waveform generator, the number of the generator used should be specified by corresponding keyword argument 'channel': ['1', '2']. Keysight 4000 X-series and Rigol MSO8000 Series can have up to two waveform generators. If there is only one waveform generator channel keyword argument is absent. The available impedance options are ['1 M', '50'].<br/>
This function is not available for Stanford Research DS345.<br>

---

### wave_gen_start()
```python
wave_gen_start() -> none
wave_gen_start(channel = '1') -> none
```
This function runs the waveform generator. This is the same as pressing the Wave Gen key on the front panel. If the oscilloscope or waveform generator has several waveform generator, the number of the generator used should be specified by corresponding keyword argument 'channel': ['1', '2']. Keysight 4000 X-series and Rigol MSO8000 Series can have up to two waveform generators. If there is only one waveform generator channel keyword argument is absent.<br/>
This function is not available for Stanford Research DS345.<br>

---

### wave_gen_stop()
```python
wave_gen_stop() -> none
wave_gen_stop(channel = '1') -> none
```
This function stops the waveform generator. This is the same as pressing the Wave Gen key on the front panel. If the oscilloscope or waveform generator has several waveform generator, the number of the generator used should be specified by corresponding keyword argument 'channel': ['1', '2']. Keysight 4000 X-series and Rigol MSO8000 Series can have up to two waveform generators. If there is only one waveform generator channel keyword argument is absent.<br/>
This function is not available for Stanford Research DS345.<br>

---

### wave_gen_phase(\*phase)
```python
wave_gen_phase(phase: int ) -> none
wave_gen_phase(phase: int, channel = '1') -> none
wave_gen_phase() -> str
wave_gen_impedance(channel = '1') -> str
```
```
Example: wave_gen_phase(50) sets the start phase of the signal to 50 degrees.
```
This function queries or sets the start phase of the signalin degrees. If there is no argument the function will return the current start phase in the format 'number + deg'. If there is an argument the specified start phase will be set. If the oscilloscope or waveform generator has several waveform generator, the number of the generator used should be specified by corresponding keyword argument 'channel': ['1', '2']. Keysight 4000 X-series and Rigol MSO8000 Series can have up to two waveform generators. If there is only one waveform generator channel keyword argument is absent.  The available range is from 0 to 360 degrees for Rigol MSO8000 Series, from -360 to 360 degrees for Keysight 4000 X-series, and from 0 to 7199.999 degrees for Stanford Research DS345. The function does not work for Noise, DC, and Arbitrary waveform. In the case of Keysight 4000 X-series oscilloscopes this funtion also swithes on 'TRACK' option. The 'TRACK' option causes frequency, amplitude, offset, and duty cycle adjustments to this waveform generator output signal to be tracked by the other waveform generator output. Please note, that not all waveform shapes can be frequency tracked.<br/>
This function is available only for Keysight 4000 X-series, Rigol MSO8000 Series oscilloscopes, and Stanford Research DS345.<br>

---

### wave_gen_modulation_function(\*function)
```python
wave_gen_modulation_function(function: ['Single','Ramp','Triangle','Sin','Sq','Arb','None']) -> none
wave_gen_modulation_function() -> str
```
```
Example: wave_gen_modulation_function('Sq') sets the sqare modulation waveform.
```
This function queries or sets the modulation waveform. If there is no argument the function will return the current modulation waveform as a string. The value 'None' will be returned for modulation types that do not have an associated waveform, such as burst [mode](#wave_gen_modulation_typetype). If there is an argument the specified waveform will be set.<br>
The available modulation waveforms for Stanford Research DS345 are ['Single', 'Ramp', 'Triangle', 'Sin', 'Sq', 'Arb', 'None']. The value 'Arb' may only be set for amplitude, frequency, and phase modulation [type](#wave_gen_modulation_typetype).<br>
The available modulation waveforms for Keysight 3000 X-Series are ['Sin', 'Sq', 'Ramp'] <br>
This function is only available for Stanford Research DS345, Keysight 3000 X-Series.<br>

---

### wave_gen_modulation_type(\*type)
```python
wave_gen_modulation_type(type: ['Lin Sweep','Log Sweep','AM','FM','PM','Burst']) -> none
wave_gen_modulation_type() -> str
```
```
Example: wave_gen_modulation_type('Lin Sweep') sets the linear sweep typy of modulation.
```
This function queries or sets the modulation type. If there is no argument the function will return the current modulation type as a string. If there is an argument the specified modulation type will be set.<br>
The available modulation types for Stanford Research DS345 are ['Lin Sweep', 'Log Sweep', 'AM', 'FM', 'PM', 'Burst'].<br>
The available modulation types for Keysight 3000 X-Series are ['AM', 'FM', 'Freq-Shift'].<br>
This function is only available for Stanford Research DS345, Keysight 3000 X-Series.<br>

---

### wave_gen_modulation_depth(\*depth)
```python
wave_gen_modulation_depth(depth: int) -> none
wave_gen_modulation_depth() -> str
```
```
Example: wave_gen_modulation_depth(50) sets the AM modulation depth to 50 percent.
```
This function queries or sets the amplitude modulation (AM) depth in percent. If there is no argument the function will return the current modulation depth as a string in the format 'number + %'. If there is an argument the specified modulation depth will be set.<br>
In the case of Stanford Research DS345 if the argument is negative the modulation is set to double sideband suppressed carrier modulation (DSBSC) with the indicated modulation percent.<br>
This function is only available for Stanford Research DS345, Keysight 3000 X-Series.<br>

---

### wave_gen_modulation_frequency_span(\*span)
```python
wave_gen_modulation_frequency_span(span: float + ['MHz','kHz','Hz','mHz','uHz']) -> none
wave_gen_modulation_frequency_span() -> str
```
```
Example: wave_gen_modulation_frequency_span('50 kHz') sets the FM modulation span to 50 kHz.
```
This function queries or sets the frequency modulation (FM) span in Hz. If there is no argument the function will return the current span as a string in the format 'number + SI suffix'. If there is an argument the specified frequency span will be set. The FM waveform will be centered at the frequency specified by the [wave_gen_frequency()](#wave_gen_frequencyfrequency) function and have a deviation of ±span/2. The maximum value of span is limited so that the frequency is never less than or equal to zero or greater than that allowed for the selected function. Otherwise the corresponding error message will be printed.<br>
This function is only available for Stanford Research DS345, Keysight 3000 X-Series.<br>

---

### wave_gen_modulation_phase_span(\*span)
```python
wave_gen_modulation_phase_span(span: float) -> none
wave_gen_modulation_phase_span() -> str
```
```
Example: wave_gen_modulation_phase_span(10) sets the span of the phase modulation span to 10 deg.
```
This function queries or sets the span of the phase modulation (PM) in degrees. If there is no argument the function will return the current phase span as a string in the format 'number + deg'. If there is an argument the specified phase span will be set. The phase shift ranges from -span/2 to span/2. The available range is from 0 deg to 7199.999 deg.<br>
This function is only available for Stanford Research DS345.<br>

---


### wave_gen_modulation_status(\*status)
```python
wave_gen_modulation_status(status: ['On','Off']) -> none
wave_gen_modulation_status() -> str
```
```
Example: wave_gen_modulation_status('On') enables the modulation.
```
This function queries or sets the modulation status. If there is no argument the function will return the current status as a string. If there is an argument the specified status will be set.<br>The available states are ['On', 'Off'].<br>
For Keysight 3000 X-Series modulation is not available for ['Pulse', 'DC', 'Noise'] function [type](#wave_gen_functionfunction).<br>
For Stanford Research DS345 modulation is not available for ['Noise'] function [type](#wave_gen_functionfunction).<br>
This function is only available for Stanford Research DS345, Keysight 3000 X-Series.<br>

---

### wave_gen_modulation_frequency_sweep(\*\*kargs)
```python
wave_gen_modulation_frequency_sweep(start, stop: float + ['MHz','kHz','Hz','mHz','uHz']) -> none
wave_gen_modulation_frequency_sweep() -> str
```
```
Example: wave_gen_modulation_frequency_sweep(start = '10 kHz', stop = '40 kHz')
sets the start and stop frequencies to 10 and 40 kHz, respectively.
```
This function queries or sets the sweep start and stop frequencies in Hz for [sweep modulation](#wave_gen_modulation_typetype) types. If there is no argument the function will return the current start and stop frequencies as a string in the foramt "START FREQ: {start}; STOP FREQ: {stop}". If there are two keyword arguments 'start' and 'stop' the specified frequencies will be set. The maximum and minimum values are limited so that the frequency is never less than or equal to zero or greater than that allowed for the selected function. Otherwise the corresponding error message will be printed. If the stop frequency is less than the start frequency a downward sweep from maximum to minimum frequency will be generated.<br>
This function is only available for Stanford Research DS345.<br>

---

### wave_gen_modulation_rate(\*rate)
```python
wave_gen_modulation_rate(rate: float + [' MHz',' kHz',' Hz',' mHz']) -> none
wave_gen_modulation_rate() -> str
```
```
Example: wave_gen_modulation_rate('5 mHz') sets the modulation rate to 5 mHz. 
```
This function queries or sets the modulation rate in Hz. If there is no argument the function will return the current modulation rate in the format 'number + SI suffix'. If there is an argument the specified rate will be set.<br/>
For Keysight 3000 X-Series this function queries or sets the frequency of the modulating signal.<br>
For Stanford Research DS345 the available range is from 1 mHz to 10 kHz.<br/>
This function is only available for Stanford Research DS345, Keysight 3000 X-Series.<br>

---

### wave_gen_modulation_trigger_source(\*tr_type)
```python
wave_gen_modulation_trigger_source(
	tr_type: ['Single','Internal','External Pos','External Neg','Line']) -> none
wave_gen_modulation_trigger_source() -> str
```
```
Example: wave_gen_modulation_trigger_source('Internal') sets the 'Internal' trigger source. 
```
This function queries or sets the trigger source for [bursts and sweeps](#wave_gen_modulation_typetype). If there is no argument the function will return the current trigger source as a string. If there is an argument the specified source will be set.<br>
The available trigger sources are ['Single', 'Internal', 'External Pos', 'External Neg', 'Line']. For single sweeps and bursts the [wave_gen_modulation_trigger()](#wave_gen_modulation_trigger) function triggers the sweep.<br/>
This function is only available for Stanford Research DS345.<br>

---

### wave_gen_modulation_trigger_rate(\*rate)
```python
wave_gen_modulation_trigger_rate(rate: float + [' kHz',' Hz',' mHz']) -> none
wave_gen_modulation_trigger_rate() -> str
```
```
Example: wave_gen_modulation_trigger_rate() queries the current internal trigger rate. 
```
This function queries or sets the trigger rate for internally triggered [single sweeps and bursts](#wave_gen_modulation_typetype) in Hz. If there is no argument the function will return the current trigger rate in the format 'number + SI suffix'. If there is an argument the specified rate will be set.<br>
The available range is from 1 mHz to 10 kHz.<br/>
This function is only available for Stanford Research DS345.<br>

---

### wave_gen_modulation_trigger()
```python
wave_gen_modulation_trigger() -> none
```
This function triggers a burst or single sweep and should be used only without arguments. The [trigger source](#wave_gen_modulation_trigger_sourcetr_type) should be set to 'Single'.<br/>
This function is only available for Stanford Research DS345.<br>

---

### wave_gen_modulation_burst_count(\*count)
```python
wave_gen_modulation_burst_count(count: int) -> none
wave_gen_modulation_burst_count() -> int
```
```
Example: wave_gen_modulation_burst_count(15) sets the modulation rate to 5 mHz. 
```
This function queries or sets the burst count. If there is no argument the function will return the current burst count as an integer. If there is an argument the specified count will be set. The available range is from 1 to 30000. The maximum value is also limited such that the burst time does not exceed 500 s. Otherwise the corresponding error message will be printed.<br/>
This function is only available for Stanford Research DS345.<br>

---

### wave_gen_modulation_hop_frequency(\*frequency)
```python
wave_gen_modulation_hop_frequency(frequency: float + [' MHz',' kHz',' Hz',' mHz']) -> none
wave_gen_modulation_hop_frequency() -> str
```
```
Example: wave_gen_modulation_hop_frequency('1 kHz') sets the current internal trigger rate. 
```
This function queries or sets the hop frequency for ['Freq-Shift'](#wave_gen_modulation_typetype) modulation type in Hz. In this modulation type the output frequency "shifts" between the original carrier frequency and this "hop frequency" with the specified in the function [wave_gen_modulation_hop_rate()](#wave_gen_modulation_hop_raterate) rate. If there is no argument the function will return the current hop frequency in the format 'number + SI suffix'. If there is an argument the specified frequency will be set.<br>
This function is only available for Keysight 3000 X-Series.<br>

---

### wave_gen_modulation_hop_rate(\*rate)
```python
wave_gen_modulation_hop_rate(rate: float + [' MHz',' kHz',' Hz',' mHz']) -> none
wave_gen_modulation_hop_rate() -> str
```
```
Example: wave_gen_modulation_hop_rate() queries the current internal trigger rate. 
```
This function queries or sets the hop rate for ['Freq-Shift'](#wave_gen_modulation_typetype) modulation type in Hz. In this modulation type the output frequency "shifts" between the original carrier frequency and ["hop frequency"](#wave_gen_modulation_hop_frequencyfrequency) with the specified rate. If there is no argument the function will return the current hop rate in the format 'number + SI suffix'. If there is an argument the specified rate will be set.<br>
This function is only available for Keysight 3000 X-Series.<br>

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
This function downloads an arbitrary waveform. The values have to be between -1.0 to +1.0. The value -1.0 represents the minimum value, +1.0 is the maximum value, and 0.0 is equal to [the offset](#wave_gen_offsetoffset). The minimum and maximum values are determined by the [amplitude](#wave_gen_amplitudeamplitude).<br/>
The setting of an arbitrary function for Keysight 2000 X-series and Keysight 3000 X-series can be done as follow:<br/>
- [wave_gen_frequency()](#wave_gen_frequencyfrequency) gives the repetition rate of an arbitrary function
- All available time interval (depends on the used repetition rate) is splitted by amount of points you indicate as an argument. It gives time per point. For instance, suppose the frequency is 10 Hz and we use 10 points: wave_gen_arbitrary_function_data([-1, -1, -1, 1, 1, 1, 1, -1, -1, -1]). It means the time step for one point will be (100 ms) / (10 points) = 10 ms
- If you have the offset equals to 2 V and the amplitude 4 V as a result of wave_gen_arbitrary_function_data([-1, -1, -1, 1, 1, 1, 1, -1, -1, -1]) for 10 Hz frequency one will have a pulse 40 ms long with the low level equals to 0 V and the high level equals to 4 V<br/>
In the case of Stanford Research DS345 the [wave_gen_arbitrary_frequency()](#wave_gen_arbitrary_frequencyfrequency) function determines the rate at which each arbitrary waveform point is output. Each point in the waveform is played for a time equal to 1/{frequency}.<br>
If the oscilloscope or waveform generator has several waveform generator, the number of the generator used should be specified by corresponding keyword argument 'channel': ['1', '2']. Keysight 4000 X-series can have up to two waveform generators. If there is only one waveform generator channel keyword argument is absent.<br/>
This function is not available for Keysight 2000 X-series, Rigol MSO8000 Series oscilloscopes.<br>

---

### wave_gen_arbitrary_frequency(\*frequency)
```python
wave_gen_arbitrary_frequency(frequency: float + [' MHz',' kHz',' Hz',' mHz']) -> none
wave_gen_arbitrary_frequency() -> str
```
```
Examples: wave_gen_arbitrary_frequency('20 kHz')
sets the arbitrary waveform sampling frequency to 20 kHz.
```
This function queries or sets the arbitrary waveform sampling frequency. If there is no argument the function will return the current sampling frequency in the format 'number + SI suffix'. If there is an argument the specified sampling frequency will be set. This frequency determines the rate at which each arbitrary waveform [point](#wave_gen_arbitrary_function_datap_list) is output. Each point in the waveform is played for a time equal to 1/{frequency}. The allowed range is from 10 mHz to 40 MHz.<br/>
This function is only available for Stanford Research DS345.<br>

---

### wave_gen_arbitrary_clear()
```python
wave_gen_arbitrary_clear() -> none
wave_gen_arbitrary_clear(channel = '1') -> none
```
This function clears the arbitrary waveform memory and loads it with the default waveform. If the oscilloscope or waveform generator has several waveform generator, the number of the generator used should be specified by corresponding keyword argument 'channel': ['1', '2']. Keysight 4000 X-series can have up to two waveform generators. If there is only one waveform generator channel keyword argument is absent.<br/>
This function is not available for Keysight 2000 X-series, Rigol MSO8000 Series oscilloscopes, and Stanford Research DS345.<br>

---

### wave_gen_arbitrary_interpolation(\*mode)
```python
wave_gen_arbitrary_interpolation(mode: ['On','Off']) -> none
wave_gen_arbitrary_interpolation(mode: ['On','Off'], channel = '1') -> none
wave_gen_arbitrary_interpolation() -> str
wave_gen_arbitrary_interpolation(channel = '1') -> str
```
```
Example: wave_gen_arbitrary_interpolation('On') turns on the interpolation control.
```
This function enables or disables the interpolation control. If there is no argument the function will return the current interpolation setting. If there is an argument the specified interpolation setting will be set. If the oscilloscope or waveform generator has several waveform generator, the number of the generator used should be specified by corresponding keyword argument 'channel': ['1', '2']. Keysight 4000 X-series can have up to two waveform generators. If there is only one waveform generator channel keyword argument is absent.<br/>
Interpolation specifies how lines are drawn between arbitrary waveform points:<br/>
When 'On', lines are drawn between points in the arbitrary waveform. Voltage levels change linearly between one point and the next.<br/>
When 'Off', all line segments in the arbitrary waveform are horizontal. The voltage level of one point remains until the next point.<br/>
This function is not available for Keysight 2000 X-series, Rigol MSO8000 Series oscilloscopes, and Stanford Research DS345.<br>

---

### wave_gen_arbitrary_number_of_points()
```python
wave_gen_arbitrary_number_of_points() -> int
wave_gen_arbitrary_number_of_points(channel = '1') -> int
```
This function returns the number of points used by the current arbitrary waveform. If the oscilloscope or waveform generator has several waveform generator, the number of the generator used should be specified by corresponding keyword argument 'channel': ['1', '2']. Keysight 4000 X-series can have up to two waveform generators. If there is only one waveform generator channel keyword argument is absent.<br/>
This function is not available for Keysight 2000 X-series and Rigol MSO8000 Series oscilloscopes.<br>

---

### wave_gen_arbitrary_amplitude_modulation(p_list)
```python
wave_gen_arbitrary_amplitude_modulation(p_list: list of floats) -> none
```
```
Example: wave_gen_arbitrary_amplitude_modulation([0, 0.5, 1, 0.5, 0, -0.5, -1, -0.5, 0])
sets the specified arbitrary amplitude modulation pattern.
```
This function downloads an arbitrary amplitude modulation pattern. The values have to be between -1.0 to +1.0. The values -1.0 and +1.0 represent the full amplitude. Negative values are used for DSBSC. The time required to execute each modulation point is controlled by the [wave_gen_arbitrary_modulation_rate_divider()](#wave_gen_arbitrary_modulation_rate_dividerrate) function. The typical procedure is as follows:<br>
- download the arbitrary waveform using the [wave_gen_arbitrary_amplitude_modulation()](#wave_gen_arbitrary_amplitude_modulationp_list) function
- set the 'Arb' modulation function by the [wave_gen_modulation_function()](#wave_gen_modulation_functionfunction) function
- enable modutation using the [wave_gen_modulation_status()](#wave_gen_modulation_statusstatus) function<br/>
This function is only available for Stanford Research DS345.<br>

---

### wave_gen_arbitrary_frequency_modulation(p_list)
```python
wave_gen_arbitrary_frequency_modulation(p_list: list of floats) -> none
```
```
Example: wave_gen_arbitrary_frequency_modulation([0, 0.1, 0.5, 0.9, 1, 0.9, 0.5, 0.1, 0])
sets the specified frequency modulation pattern.
```
This function downloads an arbitrary frequency modulation pattern. The values have to be between 0 to +1.0. The value 0 represents zero frequency, +1.0 is the maximum available frequency of 40 MHz. The time required to execute each modulation point is controlled by the [wave_gen_arbitrary_modulation_rate_divider()](#wave_gen_arbitrary_modulation_rate_dividerrate) function. The typical procedure is as follows:<br>
- download the arbitrary waveform using the [wave_gen_arbitrary_frequency_modulation()](#wave_gen_arbitrary_frequency_modulationp_list) function
- set the 'Arb' modulation function by the [wave_gen_modulation_function()](#wave_gen_modulation_functionfunction) function
- enable modutation using the [wave_gen_modulation_status()](#wave_gen_modulation_statusstatus) function<br/>
This function is only available for Stanford Research DS345.<br>

---

### wave_gen_arbitrary_phase_modulation(p_list)
```python
wave_gen_arbitrary_phase_modulation(p_list: list of floats) -> none
```
```
Example: wave_gen_arbitrary_phase_modulation([0, 0.5, 1, 0.5, 0, -0.5, -1, -0.5, 0])
sets the specified phase modulation pattern.
```
This function downloads an arbitrary phase modulation pattern. The values have to be between -1.0 to +1.0. The values -1.0 and +1.0 represent -180 and +180 degrees, respectively. The time required to execute each modulation point is controlled by the [wave_gen_arbitrary_modulation_rate_divider()](#wave_gen_arbitrary_modulation_rate_dividerrate) function. The typical procedure is as follows:<br>
- download the arbitrary waveform using the [wave_gen_arbitrary_phase_modulation()](#wave_gen_arbitrary_phase_modulationp_list) function
- set the 'Arb' modulation function by the [wave_gen_modulation_function()](#wave_gen_modulation_functionfunction) function
- enable modutation using the [wave_gen_modulation_status()](#wave_gen_modulation_statusstatus) function<br/>
This function is only available for Stanford Research DS345.<br>

---

### wave_gen_arbitrary_modulation_rate_divider(\*rate)
```python
wave_gen_arbitrary_modulation_rate_divider(rate: int) -> none
wave_gen_arbitrary_modulation_rate_divider() -> int
```
```
Example: wave_gen_arbitrary_modulation_rate_divider(2) sets the modulation rate divider to 2. 
```
This function queries or sets the arbitrary modulation rate divider. If there is no argument the function will return the current rate divider as an integer. If there is an argument the specified rate divider will be set. This controls the rate at which arbitrary modulations are generated. Arbitrary [AM](#wave_gen_arbitrary_amplitude_modulationp_list) takes 0.3 us per point, arbitrary [FM](#wave_gen_arbitrary_frequency_modulationp_list) takes 2 us per point, and arbitrary [PM](#wave_gen_arbitrary_phase_modulationp_list) takes 0.5 us per point. When modulation is enabled each modulation point takes {rate}\*[0.3 us, 2 us, 0.5 us] to execute.<br>
The available range is from 1 to (2<sup>23</sup> - 1).<br/>
This function is only available for Stanford Research DS345.<br>

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