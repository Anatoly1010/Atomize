---
title: Frequency Counters
nav_order: 24
layout: page
permlink: /functions/freq_counter/
parent: Documentation
---

### Devices

- Agilent Frequency Counter (GPIB: linux-gpib, RS-232)
**53181A**; **53131A/132A**; Tested 01/2021<br/>
**5343A**; GPIB, Tested 02/2023
- Keysight Frequency Counter (GPIB: linux-gpib, RS-232, Ethernet)
**53230A/220A**; Untested

---

### Functions
- [freq_counter_name()](#freq_counter_name)<br/>
- [freq_counter_frequency(channel)](#freq_counter_frequencychannel)<br/>
- [freq_counter_impedance(\*impedance)](#freq_counter_impedanceimpedance)<br/>
- [freq_counter_coupling(\*coupling)](#freq_counter_couplingcoupling)<br/>
- [freq_counter_stop_mode(\*mode)](#freq_counter_stop_modemode)<br/>
- [freq_counter_start_mode(\*mode)](#freq_counter_start_modemode)<br/>
- [freq_counter_gate_mode(\*mode)](#freq_counter_gate_modemode)<br/>
- [freq_counter_digits(\*digits)](#freq_counter_digitsdigits)<br/>
- [freq_counter_gate_time(\*time)](#freq_counter_gate_timetime)<br/>
- [freq_counter_expected_freq(\*frequency)](#freq_counter_expected_freqfrequency)<br/>
- [freq_counter_period(channel)](#freq_counter_periodchannel)<br/>
- [freq_counter_command(command)](#freq_counter_commandcommand)<br/>
- [freq_counter_query(command)](#freq_counter_commandquery)<br/>

---

### freq_counter_name()
```python
freq_counter_name() -> str
```
This function returns device name.<br/>

---

### freq_counter_frequency(channel)
```python
freq_counter_frequency(channel: ['CH1','CH2','CH3']) -> str
```
```
Example: freq_counter_frequency('CH1') returns the measured frequency from channel 1.
```
This function returns a value with the measured frequency from the specified channel in the format 'number + ['Hz', 'kHz', 'MHz', 'GHz']'. Refer to the device manual for the frequency range of different channels. Possible channels are the following: ['CH1', 'CH2', 'CH3']. Agilent 53181a has two channels; Agielnt 53131a, Keysight 53230a - three. Agielnt 5343a has only one channel.<br/>

---

### freq_counter_impedance(\*impedance)
```python
freq_counter_impedance(channel: ['CH1','CH2','CH3'], impedance: ['1 M','50']) -> none
freq_counter_impedance(channel: ['CH1','CH2','CH3']) -> str
```
```
Examples: freq_counter_impedance('CH1', '1 M') sets the impedance of the channel 1 to 1 MOhm.
freq_counter_impedance('CH2') returns the current impedance of the channel 2.
```
This function queries (if called with one argument) or sets (if called with two arguments) the impedance of one of the channels of the frequency counter. If there is a second argument it will be set as a new impedance. If there is no second argument the current impedance for the specified channel is returned.<br/>
For Agilent 53181a impedance can be changed only for the first channel; for Agielnt 53131a, Keysight 53230a for channel 1 and 2.<br/>
Possible impedances are the following: ['1 M', '50']. Possible channels are the following: ['CH1', 'CH2', 'CH3'].<br/>
This function is not available for Agielnt 5343a.<br/>

---

### freq_counter_coupling(\*coupling)
```python
freq_counter_coupling(channel: ['CH1','CH2','CH3'], coupling: ['AC','DC']) -> none
freq_counter_coupling(channel: ['CH1','CH2','CH3']) -> str
```
```
Examples: freq_counter_coupling('CH1', 'AC') sets the coupling of the channel 1 to AC.
freq_counter_coupling('CH2') returns the current coupling of the channel 2.
```
This function queries (if called with one argument) or sets (if called with two arguments) the coupling of one of the channels of the frequency counter. If there is a second argument it will be set as a new coupling. If there is no second argument the current coupling for the specified channel is returned.<br/>
For Agilent 53181a coupling can be changed only for the first channel; for Agielnt 53131a, Keysight 53230a for channel 1 and 2.<br/>
Possible couplings are the following: ['1 M', '50']. Possible channels are the following: ['CH1', 'CH2', 'CH3'].<br/>
This function is not available for Agielnt 5343a.<br/>

---

### freq_counter_stop_mode(\*mode)
```python
freq_counter_stop_mode(mode: ['Immediate','External','Timer','Digits']) -> none
freq_counter_stop_mode() -> str
```
```
Example: freq_counter_stop_mode('Timer') sets the digits mode.
```
This function queries or sets the stop arm for frequency, frequency ratio, and period measurements.<br/>
The mode should be from the following array: ['Immediate', 'External', 'Timer', 'Digits'] for Agilent 53181a and Agilent 53131a.<br/>
In automatic ('Immediate') mode the device does the fastest possible acquisistion, in gate time mode it measures for the specified gate time, and in digits mode the time required for a measurement depends on the number of digits requested. This setting influences the resolution of the results. Use automatic mode for fast measurements or choose a desired resolution by using [freq_counter_gate_time()](#freq_counter_gate_timetime) to set the gate time for gate time ('Timer') mode or [freq_counter_digits()](#freq_counter_digitsdigits) for digits ('Digits') mode.<br/>
For Keysight 53230a possible modes are ['Immediate', 'Timer', 'Events'].<br/>
This function is not available for Agielnt 5343a.<br/>

---

### freq_counter_start_mode(\*mode)
```python
freq_counter_start_mode(mode: ['Immediate','External']) -> none
freq_counter_start_mode() -> str
```
```
Example: freq_counter_start_mode('Immediate') sets the automatic mode.
```
This function queries or sets the start arm for frequency, frequency ratio, and period measurements.<br/>
The start mode should be from the following array: ['Immediate', 'External'].<br/>
This function is not available for Agielnt 5343a.<br/>

---

### freq_counter_gate_mode(\*mode)
```python
freq_counter_gate_mode(mode: ['Timer','External']) -> none
freq_counter_gate_mode() -> str
```
```
Example: freq_counter_gate_mode('Timer') sets the 'Time' mode.
```
This function queries or sets the gate source for frequency, frequency ratio measurements.<br/>
Currently, the gate mode should be from the following array: ['Timer', 'External'], where 'Timer' coresponds to starting the measurement immediately after a trigger and trigger delay; 'External' configures the instrument to gate the measurement using the Gate In/Out BNC after a trigger and trigger delay.<br/>
This functions is available only for Keysight 53230a.<br/>

---

### freq_counter_digits(\*digits)
```python
freq_counter_digits(digits: int) -> none
freq_counter_digits() -> int
```
```
Example: freq_counter_digits(5) sets the resolution to 5 digits.
```
This function queries or sets the resolution in terms of digits used in arming frequency, period, and ratio measurements. To set this mode use [freq_counter_stop_mode()](#freq_counter_stop_modemode) function.<br/>
The argument of the function should be an integer between 3 and 15 (Agilent 53181a, 53131a,) or between 3 and 9 (Agilent 5343a). To query the number of digits call the function with no argument. A query is possible only if [freq_counter_stop_mode('Digits')](#freq_counter_stop_modemode) was called before.<br/>
This function is available for Agilent 53181a, 53131a, and 5343a.<br/>

---

### freq_counter_gate_time(\*time)
```python
freq_counter_gate_time(time: float + [' s',' ms',' us',' ns']) -> none
freq_counter_gate_time() -> float
```
```
Example: freq_counter_gate_time('100 ms') sets the gate time to 100 ms.
```
This function queries or sets the gate time used in arming frequency, period, and ratio measurements. To set this mode use [freq_counter_stop_mode()](#freq_counter_stop_modemode) function.<br/>
The argument of the function is an integer number + scaling ['ks', 's', 'ms', 'us', 'ns'] and should be from 1 ms to 1000 s (Adilent 53181a, 53131a); from 10 ns to 10 s (Keysight 53230a). To query the gate call the function with no argument. A query is possible only if [freq_counter_stop_mode('Timer')](#freq_counter_stop_modemode) was called before.<br/>
This function is not available for Agielnt 5343a.<br/>

---

### freq_counter_expected_freq(\*frequency)
```python
freq_counter_expected_freq(channel: str, frequency: int + [' GHz',' MHz',' kHz',' Hz']) -> none
freq_counter_expected_freq(channel: ['CH1','CH2','CH3']) -> str
```
```
Example: freq_counter_expected_freq('CH3', '10 GHz') 
sets the approximate frequency of a signal to 10 GHz.
```
This function queries (if called with one argument) or sets (if called with two arguments) the approximate frequency of a signal you expect to measure. Providing this value enables the device to eliminate a pre-measurement step, saving measurement time and enabling more accurate arming. Note that the actual frequency of the input signal must be within 10% of the expected frequency value you entered. Refer to the device manual for the frequency range of different channels.<br/>
If there is a second argument it will be set as a new approximate frequency of a signal. If there is no second argument the current approximate frequency of a signal for specified the channel is returned in the format 'number + [' GHz', ' MHz', ' kHz', ' Hz']'.<br/>
Possible channels are the following: ['CH1', 'CH2', 'CH3']. For Agilent 53181a the approximate frequency can be set for channels 1 and 2; for Agielnt 53131a for channels 1, 2, and 3. The frequency argument of the function is an integer number + [' GHz', ' MHz', ' kHz', ' Hz'].<br/>
This function is available only for Agilent 53181a and 53131a.<br/>

---

### freq_counter_period(channel)
```python
freq_counter_period(channel: ['CH1','CH2','CH3']) -> str
```
```
Example: freq_counter_period('CH2') returns the measured period from channel 2.
```
This function returns a floating point value with the measured period from the specified channel in the format 'number + [' s', ' ms', ' us', ' ns']'. Refer to the device manual for the frequency range of different channels. Possible channels are the following: ['CH1', 'CH2', 'CH3'].<br/>
This function is available only for Agilent 53181a and 53131a.<br/>

---

### freq_counter_command(command)
```python
freq_counter_command(command: str) -> none
```
```
Example: freq_counter_command(':EVENt1:SLOPe POSitive'). 
This command sets which edge of the input signal will be considered an event for frequency, 
period, frequency ratio, time interval, totalize, and phase measurements.
```
This function sends an arbitrary command from a programming guide to the device in a string format. No output is expected.<br/>

---

### freq_counter_query(command)
```python
freq_counter_query(command: str) -> str
```
```
Example: freq_counter_query(':MEASure:PHASe? (@1),(@2)'). 
This command queries an measurement of the phase between channel 1 and 2.
```
This function sends an arbitrary command from a programming guide to the device in a string format. An output in a string format is expected.<br/>
