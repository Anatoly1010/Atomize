---
title: Delay Generators
nav_order: 22
layout: page
permlink: /functions/delay_generator/
parent: Documentation
---


### Devices
- Stanford Research **DG535** (GPIB); Untested

---

### Functions
- [delay_gen_name()](#delay_gen_name)<br/>
- [delay_gen_delay(*delay)](#delay_gen_delaydelay)<br/>
- [delay_gen_impedance(*impedance)](#delay_gen_impedanceimpedance)<br/>
- [delay_gen_output_mode(*mode)](#delay_gen_output_modemode)<br/>
- [delay_gen_amplitude_offset(*amplitude_offset)](#delay_gen_amplitude_offsetamplitude_offset)<br/>
- [delay_gen_output_polarity(*polarity)](#delay_gen_output_polaritypolarity)<br/>
- [delay_gen_command(command)](#delay_gen_commandcommand)<br/>
- [delay_gen_query(command)](#delay_gen_querycommand)<br/>

---

### delay_gen_name()
```python
delay_gen_name() -> str
```
The function returns device name.

---

### delay_gen_delay(*delay)
```python
delay_gen_delay(ch1: str, ch2: str, delay: str) -> none
delay_gen_delay() -> str
```
```
Example: delay_gen_delay('A', 'T0', '10 us')
sets the delay of the channel A relative to channel 'T0' to 10 us.
```
The function queries (if called with one argument) or sets (if called with three arguments) the delay of one of the channels relative to another channel. If there are a second and third arguments they will be used as a channel, relative to which the delay is set, and the delay, respectively. If there is only one argument the current delay and the reference channel are returned.<br/>
The channel dictionary is ['T0', 'A', 'B', 'C', 'D'].<br/>
The delay argument has the format: 'int + scaling ['s', 'ms', 'us', 'ps']'.

---

### delay_gen_impedance(*impedance)
```python
delay_gen_impedance(ch: str, impedance: str) -> none
delay_gen_impedance(ch: str) -> str ['50','High Z']
```
```
Example: delay_gen_impedance('A', 'High Z')
sets the impedance of the channel A to high impedance load.
```
The function queries (if called with one argument) or sets (if called with two arguments) the impedance of one of the output channels of the delay generator. If there is a second argument it will be set as a new impedance. If there is no second argument the impedance for specified the channel is returned as a string.<br/>
The channel dictionary is ['Trigger', 'T0', 'A', 'B', 'AB', 'C', 'D', 'CD'].<br/>
The impedance dictionary is ['50', 'High Z'].

---

### delay_gen_output_mode(*mode)
```python
delay_gen_output_mode(ch: str, mode: str) -> none
delay_gen_output_mode(ch: str) -> str ['TTL', 'NIM', 'ECL', 'Variable']
```
```
Example: delay_gen_output_mode('C', 'TTL') sets the mode of the channel C to TTL.
```
The function queries (if called with one argument) or sets (if called with two arguments) the mode of one of the output channels of the delay generator. If there is a second argument it will be set as a new mode setting. If there is no second argument the mode setting for specified the channel is returned as a string.<br/>
The channel dictionary is [T0', 'A', 'B', 'AB', 'C', 'D', 'CD'].<br/>
The available modes are ['TTL', 'NIM', 'ECL', 'Variable'], where 'TTL': 0 to 4 Vdc, 'ECL': -1.8 to -0.8 Vdc, 'NIM': -0.8 to 0 Vdc, 'Variable': Adjustable offset and amplitude between -3 and +4 Vdc with 4 V maximum step size.

---

### delay_gen_amplitude_offset(*amplitude_offset)
```python
delay_gen_amplitude_offset(ch: str, amplitude: str, offset: str) -> none
delay_gen_amplitude_offset(ch: str) -> str
```
```
Example: delay_gen_amplitude_offset('A', '2 V', '2 V')
sets the amplitude and offset of the channel A to 2 V, if the channel is operated in Variable mode.
```
The function queries (if called with one argument) or sets (if called with three arguments) the amplitude and offset for the specified output channel of the delay generator, if this channel is operated in Variable mode (see function [delay_gen_output_mode()](#delay_gen_output_modemode)). If there are are a second and third arguments they will be set as a new amplitude and offset setting, respectively. If there is only one argument the current amplitude and offset settings for the specified output channel are returned as a string.<br/>
Offset and amplitude should between -3 and +4 Vdc with 4 V maximum step size. The function is only available when the output channel is operated in Variable mode, see function [delay_gen_output_mode()](#delay_gen_output_modemode).<br/>
The channel dictionary is [T0', 'A', 'B', 'AB', 'C', 'D', 'CD'].<br/>
The amplitude and offset arguments have the format: 'float + scaling ['V','mV']'.

---

### delay_gen_output_polarity(*polarity)
```python
delay_gen_output_polarity(ch: str, polarity: str) -> none
delay_gen_output_polarity() -> str ['Inverted','Normal']
```
```
Example: delay_gen_output_polarity('C', 'Normal') 
sets the polarity for the channel C to Normal, if the channel is operated in TTL, ECL, or NIM mode.
```
The function queries (if called with one argument) or sets (if called with two arguments) the polarity setting of logic pulses at the BNC outputs. If there is a second argument it will be set as a new polarity setting. If there is no second argument the current polarity setting for the specified output channel is returned as a string.<br/>
Normal polarity means that the output will provide a rising edge at the specified time. The function is only available when the output channel is operated in TTL, ECL, or NIM mode, see function [delay_gen_output_mode()](#delay_gen_output_modemode).<br/>
The channel dictionary is ['Trigger', 'T0', 'A', 'B', 'AB', 'C', 'D', 'CD'].<br/>
The polarity dictionary is ['Inverted','Normal'].

---

### delay_gen_command(command)
```python
delay_gen_command(command: str) -> none
```
```
Example: delay_gen_command('DL 1,0,0')
This example opens the Delay Menu of the generator on its screen.
```
The function for sending an arbitrary command from a programming guide to the device in a string format. No output is expected.<br/>

---

### delay_gen_query(command)
```python
delay_gen_query(command: str) -> str
```
```
Example: delay_gen_query('TL')
This example queries the current external trigger level value in Volts.
```
The function for sending an arbitrary command from a programming guide to the device in a string format. An output in a string format is expected.<br/>
