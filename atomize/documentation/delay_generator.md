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
- [delay_generator_name()](#delay_generator_name)<br/>
- [delay_generator_delay(*delay)](#delay_generator_delaydelay)<br/>
- [delay_generator_impedance(*impedance)](#delay_generator_impedanceimpedance)<br/>
- [delay_generator_output_mode(*mode)](#delay_generator_output_modemode)<br/>
- [delay_generator_amplitude_offset(*amplitude_offset)](#delay_generator_amplitude_offsetamplitude_offset)<br/>
- [delay_generator_output_polarity(*polarity)](#delay_generator_output_polaritypolarity)<br/>
- [delay_generator_command(command)](#delay_generator_commandcommand)<br/>
- [delay_generator_query(command)](#delay_generator_querycommand)<br/>

---

### delay_generator_name()
```python
delay_generator_name() -> str
```
This function returns device name.<br/>

---

### delay_generator_delay(*delay)
```python
delay_generator_delay(ch1: str, ch2: str, delay: float + [' s',' ms',' us',' ns',' ps']) -> none
delay_generator_delay(ch1: str) -> '['T0','A','B','C','D'] + {float} [' s',' ms',' us',' ns',' ps']'
```
```
Example: delay_generator_delay('A', 'T0', '10 us')
sets the delay of the channel A relative to channel 'T0' to 10 us.
```
This function queries (if called with one argument) or sets (if called with three arguments) the delay of one of the channels relative to another channel. If there are a second and third arguments, they will be used as a channel, relative to which the delay is set, and the delay, respectively. If there is only one argument the current delay and the reference channel are returned. The delay argument has the format 'float + [' s', ' ms', ' us', ' ns', ' ps']'. The available channels are ['T0', 'A', 'B', 'C', 'D'].<br/>

---

### delay_generator_impedance(*impedance)
```python
delay_generator_impedance(ch: str, impedance: ['50','1 M']) -> none
delay_generator_impedance(ch: str) -> str
```
```
Example: delay_generator_impedance('A', '1 M')
sets the impedance of the channel A to high impedance load.
```
This function queries (if called with one argument) or sets (if called with two arguments) the impedance of one of the output channels of the delay generator. If there is a second argument it will be set as a new impedance. If there is no second argument the impedance for specified the channel is returned as a string.<br/>
The available channels are ['Trigger', 'T0', 'A', 'B', 'AB', 'C', 'D', 'CD']. The available impedancies are ['50', '1 M'].<br>

---

### delay_generator_output_mode(*mode)
```python
delay_generator_output_mode(ch: str, mode: ['TTL','NIM','ECL','Variable']) -> none
delay_generator_output_mode(ch: str) -> str
```
```
Example: delay_generator_output_mode('C', 'TTL') sets the mode of the channel C to TTL.
```
This function queries (if called with one argument) or sets (if called with two arguments) the mode of one of the output channels of the delay generator. If there is a second argument it will be set as a new mode setting. If there is no second argument the mode setting for specified the channel is returned as a string.<br/>
The available channels are [T0', 'A', 'B', 'AB', 'C', 'D', 'CD']. The available modes are ['TTL', 'NIM', 'ECL', 'Variable'], where 'TTL': 0 to 4 Vdc, 'ECL': -1.8 to -0.8 Vdc, 'NIM': -0.8 to 0 Vdc, 'Variable': Adjustable offset and amplitude between -3 and +4 Vdc with 4 V maximum step size.<br>

---

### delay_generator_amplitude_offset(*amplitude_offset)
```python
delay_generator_amplitude_offset(ch: str, amplitude: float + [' V',' mV'], 
			   offset: float + [' V',' mV']) -> none
delay_generator_amplitude_offset(ch: str) -> 
			   'Amplitude: ' + {float} + ' V; ' + 'Offset: ' + {float} + ' V'
```
```
Example: delay_generator_amplitude_offset('A', '2 V', '2 V')
sets the amplitude and offset of the channel A to 2 V, if the channel is operated in Variable mode.
```
This function queries (if called with one argument) or sets (if called with three arguments) the amplitude and offset for the specified output channel of the delay generator, if this channel is operated in Variable mode (see function [delay_generator_output_mode()](#delay_generator_output_modemode)). If there are are a second and third arguments they will be set as a new amplitude and offset setting, respectively. If there is only one argument the current amplitude and offset settings for the specified output channel are returned as a string.<br/>
Offset and amplitude should between -3 and +4 Vdc with 4 V maximum step size. The function is only available when the output channel is operated in Variable mode, see function [delay_generator_output_mode()](#delay_generator_output_modemode).<br/>
The available channels are [T0', 'A', 'B', 'AB', 'C', 'D', 'CD']. The amplitude and offset arguments have the format of 'float + [' V',' mV']'. The output has the format of 'Amplitude: ' + {float} + ' V; ' + 'Offset: ' + {float} + ' V'.<br/>

---

### delay_generator_output_polarity(*polarity)
```python
delay_generator_output_polarity(ch: str, polarity: ['Inverted','Normal']) -> none
delay_generator_output_polarity() -> str
```
```
Example: delay_generator_output_polarity('C', 'Normal') 
sets the polarity for the channel C to Normal, if the channel is operated in TTL, ECL, or NIM mode.
```
This function queries (if called with one argument) or sets (if called with two arguments) the polarity setting of logic pulses at the BNC outputs. If there is a second argument it will be set as a new polarity setting. If there is no second argument the current polarity setting for the specified output channel is returned as a string.<br/>
Normal polarity means that the output will provide a rising edge at the specified time. The function is only available when the output channel is operated in TTL, ECL, or NIM mode, see function [delay_generator_output_mode()](#delay_generator_output_modemode).<br/>
The available channels are ['Trigger', 'T0', 'A', 'B', 'AB', 'C', 'D', 'CD']. The available polarities are ['Inverted','Normal'].<br>

---

### delay_generator_command(command)
```python
delay_generator_command(command: str) -> none
```
```
Example: delay_generator_command('DL 1,0,0')
This example opens the Delay Menu of the generator on its screen.
```
This function sends an arbitrary command from a programming guide to the device in a string format. No output is expected.<br/>

---

### delay_generator_query(command)
```python
delay_generator_query(command: str) -> str
```
```
Example: delay_generator_query('TL')
This example queries the current external trigger level value in Volts.
```
This function sends an arbitrary command from a programming guide to the device in a string format. An output in a string format is expected.<br/>
