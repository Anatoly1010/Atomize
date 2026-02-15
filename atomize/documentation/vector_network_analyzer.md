---
title: Vector Network Analyzers
nav_order: 37
layout: page
permlink: /functions/vector_network_analyzer/
parent: Documentation
---


### Devices
- Planar **C2220**, **S50024** (Socket); Tested 09/2025
Planar instruments only work when running [native sofware](https://planarchel.ru/catalog/analizatory_tsepey_vektornye/vektornye_analizatory_tsepey_kobalt/analizator-tsepey-vektornyy-c2220/). In addition, the socket server must be enabled in the web server settings of the software.

---

### Functions
- [vector_analyzer_name()](#vector_analyzer_name)<br/>
- [vector_analyzer_source_power(\*pwr, source = 1)](#vector_analyzer_source_powerpwr-source--1)<br/>
- [vector_analyzer_center_frequency(\*freq, channel = 1)](#vector_analyzer_center_frequencyfreq-channel--1)<br/>
- [vector_analyzer_frequency_range(\*freq, channel = 1)](#vector_analyzer_frequency_rangefreq-channel--1)<br/>
- [vector_analyzer_points(\*pnt, channel = 1)](#vector_analyzer_pointspnt-channel--1)<br/>
- [vector_analyzer_trigger_source(\*src)](#vector_analyzer_trigger_sourcesrc)<br/>
- [vector_analyzer_send_trigger()](#vector_analyzer_send_trigger)<br/>
- [vector_analyzer_intermediate_freqiency_bandwith(\*freq, channel = 1)](#vector_analyzer_intermediate_freqiency_bandwithfreq-channel--1)<br/>
- [vector_analyzer_trigger_mode(\*md, channel = 1)](#vector_analyzer_trigger_modemd-channel--1)<br>
- [vector_analyzer_get_curve(s = 'S11', type = 'IQ', channel = 1, data_type = 'COR')](#vector_analyzer_get_curves--s11-type--iq-channel--1-data_type--cor)<br>
- [vector_analyzer_get_frequency_points(channel = 1)](#vector_analyzer_get_frequency_pointschannel--1)<br>
- [vector_analyzer_measurement_time(channel = 1)](#vector_analyzer_measurement_timechannel--1)<br>
- [vector_analyzer_command(command)](#vector_analyzer_commandcommand)<br>
- [vector_analyzer_query(command)](#vector_analyzer_querycommand)<br>

---

### vector_analyzer_name()
```python
vector_analyzer_name() -> str
```
This function returns device name.<br/>

---

### vector_analyzer_source_power(\*pwr, source = 1)
```python
vector_analyzer_source_power(pwr: float + ' dBm', source: int) -> none
vector_analyzer_source_power(source: int) -> float
```
```
Example: vector_analyzer_source_power('0 dBm', source = 1) sets the power of the source 1 to 0 dBm.
```
This function queries or sets the power of the specified source. If there is no argument, the function returns the current power for the source specified as the keyword "source". The output of the function is a float number in dBm. If there is an argument, the specified power will be set for the indicated source. The power argument is a string in the format 'number dBm'. The available range is from -60 dBm to 20 dBm, and is specified directly in the device configuration file. The number of available sources is also given in the configuration file.<br/>

---

### vector_analyzer_center_frequency(\*freq, channel = 1)
```python
vector_analyzer_center_frequency(freq: float + [' Hz',' kHz',' MHz',' GHz'], channel: int) -> none
vector_analyzer_center_frequency(channel: int) -> str
```
```
Example: vector_analyzer_center_frequency('9 GHz') sets the center frequency to 9 GHz.
```
This function queries or sets the center frequency for measurement. If there is no argument, the function returns the current center frequency for the channel specified as the keyword "channel". The output of the function is a string in the format 'number + ['Hz', 'kHz', 'MHz', 'GHz']. If there is an argument, the specified center frequency will be set for the indicated channel. The center frequency argument is a string in the format 'number [Hz, kHz, MHz, GHz]'. The available range is from 0.1 MHz to 20 GHz, and is specified directly in the device configuration file. The number of available channels is also given in the configuration file.<br/>

---

### vector_analyzer_frequency_range(\*freq, channel = 1)
```python
vector_analyzer_frequency_range(freq: float + [' Hz',' kHz',' MHz',' GHz'], channel: int) -> none
vector_analyzer_frequency_range(channel: int) -> str
```
```
Example: vector_analyzer_frequency_range('10 MHz') sets the frequency range to 10 MHz.
```
This function queries or sets the frequency range for measurement. If there is no argument, the function returns the current frequency range for the channel specified as the keyword "channel". The output of the function is a string in the format 'number + ['Hz', 'kHz', 'MHz', 'GHz']. If there is an argument, the specified frequency range will be set for the indicated channel. The frequency range argument is a string in the format 'number [Hz, kHz, MHz, GHz]'. The available range is from 0 MHz to 20 GHz. The number of available channels is also given in the configuration file.<br/>

---

### vector_analyzer_points(\*pnt, channel = 1)
```python
vector_analyzer_points(pnt: int, channel: int) -> none
vector_analyzer_points(channel: int) -> int
```
```
Example: vector_analyzer_points(1000, channel = 1) sets 1000 points for measurement.
```
This function queries or sets the number of points for measurement. If there is no argument, the function returns the current number of points for the channel specified as the keyword "channel". The output of the function is an integer number. If there is an argument, the specified number of points will be set for the indicated channel. The number of points argument is an integer number. The available number of points is from 2 to 500001, and is specified directly in the device configuration file. The number of available channels is also given in the configuration file.<br/>

---

### vector_analyzer_trigger_source(\*src)
```python
vector_analyzer_trigger_source(src: ['INT','EXT','MAN','BUS']) -> none
vector_analyzer_trigger_source() -> str
```
```
Example: vector_analyzer_trigger_source('INT') sets the internal trigger source.
```
This function queries or sets the trigger source. If there is no argument, the function returns the current trigger source as a string. If there is an argument, the specified trigger source will be set. The following trigger sources are available: ['INT', 'EXT', 'MAN', 'BUS'].<br/>

---

### vector_analyzer_send_trigger()
```python
vector_analyzer_send_trigger() -> none
```
```
Example: vector_analyzer_send_trigger() sends a software trigger.
```
This function can only be called without arguments and is used to send a single software trigger to the device. It is usually used in combination with 'MAN' or 'BUS' [trigger source](#vector_analyzer_trigger_sourcesrc).<br/>

---

### vector_analyzer_intermediate_freqiency_bandwith(\*freq, channel = 1)
```python
vector_analyzer_intermediate_freqiency_bandwith(freq: float + [' Hz',' kHz',' MHz',' GHz'], 
				    channel: int) -> none
vector_analyzer_intermediate_freqiency_bandwith(channel: int) -> str
```
```
Example: vector_analyzer_intermediate_freqiency_bandwith('10 kHz') sets the intermediate frequency 
bandwidth to 10 kHz.
```
This function queries or sets the intermediate frequency bandwidth for measurement. If there is no argument, the function returns the current bandwidth for the channel specified as the keyword "channel". The output of the function is a string in the format 'number + ['Hz', 'kHz', 'MHz']. If there is an argument, the specified bandwidth will be set for the indicated channel. The intermediate frequency bandwidth argument is a string in the format 'number [Hz, kHz, MHz, GHz]'. The numeric value of the bandwidth should be from the array:<br/>
[1, 2, 3, 5, 7, 10, 15, 20, 30, 50, 70, 100, 150, 200, 300, 500, 700, 1000].<br/>
If there is no bandwidth setting fitting the argument the nearest available value is used and warning is printed.<br/>

---

### vector_analyzer_trigger_mode(\*md, channel = 1)
```python
vector_analyzer_trigger_mode(md: ['SINGLE','REP','OFF'], channel: int) -> none
vector_analyzer_trigger_mode() -> str
```
```
Example: vector_analyzer_trigger_mode('REP') sets the repetitive trigger initiation mode.
```
This function queries or sets the trigger initiation mode. If there is no argument, the function returns the current trigger mode as a string. If there is an argument, the specified trigger initiation mode will be set. The following mode are available: ['SINGLE', 'REP', 'OFF']. The 'REP' argument corresponds to repetitive mode, 'SINGLE' to single start, and 'OFF' stops the device.<br/>

---

### vector_analyzer_get_curve(s = 'S11', type = 'IQ', channel = 1, data_type = 'COR')
```python
vector_analyzer_get_curve(s: ['S11','S12','S21','S22','R11','R12','R21','R22','A(1)','A(2)',
	'B(1)','B(2)'], type: ['IQ','AP'], channel: int, data_type: ['COR','RAW'])) -> np.array, np.array
```
```
Example: vector_analyzer_get_curve(s = 'S11', type = 'AP') performs the measurement and returns 
two 'S11' curves in the form of amplitude and phase.
```
This function runs the measurement for the channel specified as the keyword "channel" and returns the result as two numpy arrays with the number of points specified in the function [the vector_analyzer_points()](#vector_analyzer_pointspnt-channel--1). The number of available channels is given in the configuration file. The following s-parameters are available for measurement: ['S11', 'S12', 'S21', 'S22', 'R11', 'R12', 'R21', 'R22', 'A(1)', 'A(2)', 'B(1)', 'B(2)'].<br>
The acquired curves can be returned in two different formats: ['IQ', 'AP']. The 'IQ' format corresponds to the real and imagimary parts of the measured signal in mV. The 'AP' format corresponds to the amplitude and phase of the measured signal. The keyword 'data_type' indicates whether the measured signal is corrected using various calibration coefficients or not. The available options are ['COR', 'RAW'].<br>

---

### vector_analyzer_get_frequency_points(channel = 1)
```python
vector_analyzer_get_frequency_points(channel: int) -> np.array
```
```
Example: vector_analyzer_get_frequency_points() returns the array of measured points.
```
This function returns an array of measurement point frequencies for the channel specified as the keyword "channel". The total number of points in the array is equal to the number of points specified in the function [the vector_analyzer_points()](#vector_analyzer_pointspnt-channel--1). The number of available channels is given in the configuration file. The frequencies are given in MHz.<br>

---

### vector_analyzer_measurement_time(channel = 1)
```python
vector_analyzer_measurement_time(channel: int) -> float
```
```
Example: vector_analyzer_measurement_time() returns the measurement time.
```
This function returns the measurement time for the channel specified as the keyword "channel". The number of available channels is given in the configuration file. The measurement time are given in seconds.<br>

---

### vector_analyzer_command(command)
```python
vector_analyzer_command(command: str) -> none
```
```
Example: vector_analyzer_command('DISP:WIND:TRAC:Y:AUTO') perform automatic graph scaling.
```
This function sends an arbitrary command from a programming guide to the device in a string format. No output is expected.<br/>

---

### vector_analyzer_query(command)
```python
vector_analyzer_query(command: str) -> str
```
```
Example: vector_analyzer_query('SERV:CHAN:ACT?') returns the number of the active channel.
```
This function sends an arbitrary command from a programming guide to the device in a string format. An output in a string format is expected.<br/>
