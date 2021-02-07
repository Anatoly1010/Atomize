# List of available functions for power supplies

Available devices:
- Stanford Research DG535 (GPIB); Untested

Functions:
- [delay_gen_name()](#delay_gen_name)<br/>
- [delay_gen_delay(*delay)](#delay_gen_delaydelay)<br/>
- [delay_gen_impedance(*impedance)](#delay_gen_impedanceimpedance)<br/>
- [delay_gen_output_mode(*mode)](#delay_gen_output_modemode)<br/>
- [delay_gen_amplitude_offset(*amplitude_offset)](#delay_gen_amplitude_offsetamplitude_offset)<br/>
- [delay_gen_output_polarity(*polarity)](#delay_gen_output_polaritypolarity)<br/>
- [delay_gen_command(command)](#delay_gen_commandcommand)<br/>
- [delay_gen_query(command)](#delay_gen_querycommand)<br/>

### delay_gen_name()
```python3
delay_gen_name()
Arguments: none; Output: string.
```
The function returns device name.
### delay_gen_delay(*delay)
```python3
delay_gen_delay(*delay)
Arguments: delay = three strings ('channel 1 string' ['T0','A','B','C','D'], 'channel 2 string' ['T0','A','B','C','D'],
'number + scaling ['s','ms','us','ps']',) or one string ('channel 1 string');
Output: string (channel 2 + delay (in us)).
Example: delay_gen_delay('A', 'T0', '10 us') sets the delay of the channel A relative to channel 'T0' to 10 us.
```
The function queries (if called with one argument) or sets (if called with three arguments) the delay of one of the channels relative to another channel. If there are a second and third arguments they will be used as a channel, relative to which the delay is set, and the delay, respectively. If there is only one argument the current delay and the reference channel are returned.<br/>
The channel dictionary is ['T0', 'A', 'B', 'C', 'D'].
### delay_gen_impedance(*impedance)
```python3
delay_gen_impedance(*impedance)
Arguments: impedance = two strings ('channel string' ['Trigger','T0','A','B','AB','C','D','CD'],
'impedance string ['50','High Z']') or one string ('channel string');
Output: string ('50' or 'High Z').
Example: delay_gen_impedance('A', 'High Z') sets the impedance of the channel A to high impedance loads.
```
The function queries (if called with one argument) or sets (if called with two arguments) the impedance of one of the output channels of the delay generator. If there is a second argument it will be set as a new impedance. If there is no second argument the impedance for specified the channel is returned as a string.<br/>
The channel dictionary is ['Trigger', 'T0', 'A', 'B', 'AB', 'C', 'D', 'CD'].
### delay_gen_output_mode(*mode)
```python3
delay_gen_output_mode(*mode)
Arguments: mode = two strings ('channel string' ['T0','A','B','AB','C','D','CD'], 
'mode string ['TTL','NIM','ECL','Variable']') or one string ('channel string');
Output: string ('TTL','NIM','ECL', or 'Variable').
Example: delay_gen_output_mode('C', 'TTL') sets the mode of the channel C to TTL.
```
The function queries (if called with one argument) or sets (if called with two arguments) the mode of one of the output channels of the delay generator. If there is a second argument it will be set as a new mode setting. If there is no second argument the mode setting for specified the channel is returned as a string.<br/>
The channel dictionary is [T0', 'A', 'B', 'AB', 'C', 'D', 'CD']. The available modes are ['TTL', 'NIM', 'ECL', 'Variable'], where 'TTL': 0 to 4 Vdc, 'ECL': -1.8 to -.8 Vdc, 'NIM': -.8 to 0 Vdc, 'Variable': Adjustable offset and amplitude between -3 and +4 Vdc with 4 V maximum step size.
### delay_gen_amplitude_offset(*amplitude_offset)
```python3
delay_gen_amplitude_offset(*amplitude_offset)
Arguments: amplitude_offset = three strings ('channel string' ['T0','A','B','AB','C','D','CD'],
'amplitude + scaling ['V','mV']', 'offset + scaling ['V','mV']') or one string ('channel string');
Output: string ('Amplitude: ## V; Offset: ## V').
Example: delay_gen_amplitude_offset('A', '2 V', '2 V') sets the amplitude and the offset of the output channel A
to 2 V, if the channel is operated in Variable mode.
```
The function queries (if called with one argument) or sets (if called with three arguments) the amplitude and offset for the specified output channel of the delay generator, if this channel is operated in Variable mode (see function [delay_gen_output_mode()](#delay_gen_output_modemode)). If there are are a second and third arguments they will be set as a new amplitude and offset setting, respectively. If there is only one argument the current amplitude and offset settings for the specified output channel are returned as a string.<br/>
Offset and amplitude should between -3 and +4 Vdc with 4 V maximum step size. The function is only available when the output channel is operated in Variable mode, see function [delay_gen_output_mode()](#delay_gen_output_modemode).
### delay_gen_output_polarity(*polarity)
```python3
delay_gen_output_polarity(*polarity)
Arguments: mode = two strings ('channel string' ['T0','A','B','AB','C','D','CD'], 
'polarity string ['Inverted','Normal']') or one string ('channel string'); Output: string ('Inverted', or 'Normal').
Example: delay_gen_output_polarity('C', 'Normal') sets the polarity for the channel C to Normal,
if the channel is operated in TTL, ECL, or NIM mode.
```
The function queries (if called with one argument) or sets (if called with two arguments) the polarity setting of logic pulses at the BNC outputs. If there is a second argument it will be set as a new polarity setting. If there is no second argument the current polarity setting for the specified output channel is returned as a string.<br/>
Normal polarity means that the output will provide a rising edge at the specified time. The function is only available when the output channel is operated in TTL, ECL, or NIM mode, see function [delay_gen_output_mode()](#delay_gen_output_modemode).
### delay_gen_command(command)
```python3
delay_gen_command(command)
Arguments: command = string; Output: none.
Example: delay_gen_command('DL 1,0,0'). This example opens the Delay Menu of the generator on its screen.
```
The function for sending an arbitrary command from a programming guide to the device in a string format. No output is expected.<br/>
### delay_gen_query(command)
```python3
delay_gen_query(command)
Arguments: command = string; Output: string.
Example: delay_gen_query('TL'). This example queries the current external trigger level value in Volts.
```
The function for sending an arbitrary command from a programming guide to the device in a string format. An output in a string format is expected.<br/>
