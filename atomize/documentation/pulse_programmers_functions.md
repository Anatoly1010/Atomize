# List of available functions for pulse programmers

Available devices:
- Pulse Blaster ESR 500 Pro; Tested 06/2021

The device is available via ctypes. [The original C library](http://www.spincore.com/support/spinapi/using_spin_api_pb.shtml) was written by SpinCore Technologies.

Functions:
- [pulser_name()](#pulser_name)<br/>
- [pulser_pulse(*kagrs)](#pulser_pulsekargs)<br/>
- [pulser_update()](#pulser_update)<br/>
- [pulser_repetitoin_rate(*r_rate)](#pulser_repetitoin_rater_rate)<br/>
- [pulser_shift(*pulses)](#pulser_shiftpulses)<br/>
- [pulser_increment(*pulses)](#pulser_incrementpulses)<br/>
- [pulser_reset()](#pulser_reset)<br/>
- [pulser_pulse_reset(*pulses)](#pulser_pulse_resetpulses)<br/>
- [pulser_stop()](#pulser_stop)<br/>
- [pulser_state()](#pulser_state)<br/>

### pulser_name()
```python3
pulser_name()
Arguments: none; Output: string.
```
The function returns device name.
### pulser_pulse(*kagrs)
```python3
pulser_pulse(*kagrs)
Arguments:
name = 'P0' specifies a name of the pulse
channel = 'CH0' specifies a channel string (['CH0','CH1', ... ,'CH20'])
start = '0 ns' specifies a start time of the pulse (['ns', 'us', 's'])
length = '100 ns' specifies a length of the pulse (['ns', 'us', 's'])
delta_start = '0 ns' specifies a start time increment of the pulse (['ns', 'us', 's'])
length_increment = '0 ns' specifies a pulse length increment (['ns', 'us', 's']);
Output: none.
Example: pulser_pulse('channel = 'CH0', start = '100 ns', length = '100 ns', delta_start = '0 ns',
length_increment = '0 ns') sets the 100 ns length pulse with 100 ns start time at channel 0.
```
The function sets a pulse with specified parameters. The default argument is name = 'P0', channel = 'CH0', start = '0 ns', length = '100 ns', delta_start = '0 ns', length_increment = '0 ns'. A channel should be one of the following ['CH0','CH1', ... ,'CH20']. The scaling factor for start, length, delta_start, and length_increment key arguments should be one of the following ['ns', 'us', 's']. The minimum available length of the pulse is 12 ns. The maximum available length of the pulse is 2000 ns. The maximum available length of the pulse sequence is 8.9 s. The pulse sequence will be checked for overlap.
### pulser_update()
```python3
pulser_update()
Arguments: none; Output: none.
Example: pulser_update() updates a pulse sequence and sends instructions to the pulse programmer.
```
This function updates a pulse sequence and sends instructions to the pulse programmer. It has to be called after changes have been applied to pulses either via any of the pulser functions or by changing a pulse property directly. Only by calling the function the changes are committed and the real pulses will change.
### pulser_repetitoin_rate(*r_rate)
```python3
pulser_repetitoin_rate(*r_rate)
Arguments: r_rate = string (number + scaling ['Hz','kHz','MHz']); Output: string.
Example: pulser_repetitoin_rate('2 Hz') sets the repetition rate to 2 Hz.
```
The function queries (if called without argument) or sets (if called with one argument) the repetition rate of the pulse sequence. If there is an argument it will be set as a repetition rate. If there is no argument the current repetition rate is returned as a string. The maximum available repetition rate depends on the total length of the pulse sequence and cannot exceed 5 MHz.<br/>
### pulser_shift(*pulses)
```python3
pulser_shift(*pulses)
Arguments: none or string of pulse names; Output: none.
Example: pulser_shift() shifts all currently active pulses by their respective delta_start.
```
This function can be called with either no argument or with a list of comma separated pulse names (i.e. 'P0', 'P1'). If no argument is given the start time of all pulses that have a nonzero delta_start and are currently active (do not have a length of 0) are shifted by their corresponding delta_start value. If there is only one argument or a list of pulses only the start time of the listed pulses are changed.
### pulser_increment(*pulses)
```python3
pulser_increment(*pulses)
Arguments: none or string of pulse names; Output: none.
Example: pulser_increment('P0') increments the pulse named 'P0' by the corresponding length_increment value.
```
This function can be called with either no argument or with a list of comma separated pulse names (i.e. 'P0', 'P1'). If no argument is given the lengths of all pulses that have a nonzero length_increment and are currently active (do not have a length of 0) are incremented by their corresponding length_increment value. If there is only one argument or a list of pulses only the lengths of the listed pulses are changed.
### pulser_reset()
```python3
pulser_reset()
Arguments: none; Output: none.
Example: pulser_reset() resets all the pulses to their initial state and updates the pulse programmer.
```
The function switches the pulse programmer back to the initial state in which it was in at the start of the experiment. This function can be called only without arguments. It includes the complete functionality of [pulser_pulse_reset()](#pulser_pulse_reset), but also immediately updates the pulse programmer as it is done by calling [pulser_update()](#pulser_update).
### pulser_pulse_reset(*pulses)
```python3
pulser_pulse_reset(*pulses)
Arguments: none or string of pulse names; Output: none.
Example: pulser_pulse_reset('P1') resets the pulse named 'P1' to its initial state.
```
The function switches the pulse programmer back to the initial state in which it was in at the start of the experiment. This function can be called with either no argument or with a list of comma separated pulse names. If no argument is given all pulses are reset to their initial states. It does not update the pulser, if you want to reset all pulses and and also update the pulser use the function [pulser_reset()](#pulser_reset) instead.
### pulser_stop()
```python3
pulser_stop()
Arguments: none; Output: none.
Example: pulser_stop() stops the pulse programmer.
```
This functions stops the pulse programmer. This function should always be called at the end of an experimental script.
### pulser_state()
```python3
pulser_state()
Arguments: none; Output: string.
Example: pulser_state() queries the pulse programmer state.
```
This functions queries the pulse programmer state and can be called only without arguments.