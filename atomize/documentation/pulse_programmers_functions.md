# List of available functions for pulse programmers

Available devices:
- Pulse Blaster ESR 500 Pro; Tested 06/2021

The device is available via ctypes. [The original C library](http://www.spincore.com/support/spinapi/using_spin_api_pb.shtml) was written by SpinCore Technologies.

Functions:
- [pulser_name()](#pulser_name)<br/>
- [pulser_pulse(*kagrs)](#pulser_pulsekargs)<br/>
- [pulser_update()](#pulser_update)<br/>
- [pulser_next_phase()](#pulser_next_phase)<br/>
- [pulser_acquisition_cycle(data1, data2, acq_cycle = [])](#pulse_acquisition_cycledata1-data2-acq_cycle--)<br/>
- [pulser_repetition_rate(*r_rate)](#pulser_repetition_rater_rate)<br/>
- [pulser_shift(*pulses)](#pulser_shiftpulses)<br/>
- [pulser_increment(*pulses)](#pulser_incrementpulses)<br/>
- [pulser_redefine_start(*, name, start)](#pulser_redefine_start-name-start)<br/>
- [pulser_redefine_delta_start(*, name, delta_start)](#pulser_redefine_delta_start-name-delta_start)<br/>
- [pulser_redefine_length_increment(*, name, length_increment)](#pulser_redefine_length_increment-name-length_increment)<br/>
- [pulser_reset()](#pulser_reset)<br/>
- [pulser_pulse_reset(*pulses)](#pulser_pulse_resetpulses)<br/>
- [pulser_stop()](#pulser_stop)<br/>
- [pulser_state()](#pulser_state)<br/>
- [pulser_visualize()](#pulser_visualize)<br/>
- [pulser_pulse_list()](#pulser_pulse_list)<br/>

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
start = '0 ns' specifies a start time of the pulse (['ns','us','ms','s'])
length = '100 ns' specifies a length of the pulse (['ns','us','ms','s'])
delta_start = '0 ns' specifies a start time increment of the pulse (['ns','us','ms',s'])
length_increment = '0 ns' specifies a pulse length increment (['ns','us','ms','s'])
phase_list = [] specifies a phase cycling sequence (['+x', '-x', '+y', '-y'])
Output: none.
Example: pulser_pulse('name' = 'P0', channel = 'MW', start = '100 ns', length = '100 ns', delta_start = '0 ns',
length_increment = '0 ns') sets the 100 ns length microwave pulse with 100 ns start time with no phase cycling.
```
The function sets a pulse with specified parameters. The default argument is name = 'P0', channel = 'TRIGGER', start = '0 ns', length = '100 ns', delta_start = '0 ns', length_increment = '0 ns', phase_list = []. A channel should be one of the following ['TRIGGER','AMP_ON','LNA_PROTECT','MW','-X','+Y','TRIGGER_AWG', 'AWG', 'CH8' ... ,'CH20']. The scaling factor for start, length, delta_start, and length_increment key arguments should be one of the following ['ns', 'us', 'ms', 's']. The minimum available length of the pulse is 10 ns. The maximum available length of the pulse is 1900 ns. The maximum available length of the pulse sequence is 8.9 s. The pulse sequence will be checked for overlap. In the auto defence mode (default option; can be changed in the config file) channels 'AMP_ON' and 'LNA_PROTECT' will be added automatically according to the delays indicated in the config file. In this mode 'AMP_ON' and 'LNA_PROTECT' pulses will be joined in one pulse if the distance between them is less than 12 ns (can be changed in the config file).
### pulser_update()
```python3
pulser_update()
Arguments: none; Output: none.
Example: pulser_update() updates a pulse sequence and sends instructions to the pulse programmer.
```
This function updates a pulse sequence and sends instructions to the pulse programmer. It has to be called after changes have been applied to pulses either via any of the pulser functions or by changing a pulse property directly. Only by calling the function the changes are committed and the real pulses will change.
### pulser_next_phase()
```python3
pulser_next_phase()
Arguments: none; Output: none.
Example: pulser_next_phase() switches all pulses in the sequence to the next phase.
```
This function switches all pulses to the next phase. The phase sequence is declared in the [pulser_pulse()](#pulser_pulse) in the form of phase_list = ['-y', '+x', '-x', '+x', ...]. By repeatedly calling the function one can run through the complete list of phases for the pulses. The length of all phase lists specified for different MW pulses has to be the same. This function also immediately updates the pulse sequence, as it is done by calling [pulser_update()](#pulser_update). The first call of the function corresponds to the first phase in the phase_list argument of the [pulser_pulse()](#pulser_pulse).
### pulser_acquisition_cycle(data1, data2, acq_cycle = [])
```python3
pulser_acquisition_cycle(data1, data2, acq_cycle = [])
Arguments: 
data1, data2 = 1D or 2D numpy arrays;
acq_cycle = array of mathematical operations, i.e. ['+', '-', '+i', '-i'];
Output: two numpy arrays, representing phase cycled data1 and data2.
Example: pulser_acquisition_cycle(np.array([1, 0]), np.array([0, 1]), acq_cycle = ['+', '-'])
performes given mathematical operations on the arrays.
```
This function can be used to shorten the syntax for acqusition in the case of phase cycling. The arguents are (i) two numpy arrays from a quadrature detector, (ii) array of mathematical operations to perform. Data arrays can be both 2D and 1D, representing, respectively, the case of raw oscillograms or integrated data. The length of acq_cycle array and the 1D arrays or the amount of the individual oscillograms in the 2D array should be equal. The data arrays will be treated inside the function as a complex number:
```python3
answer = np.zeros( data1.shape ) + 1j*np.zeros( data2.shape )
```
The available mathematical operations are ['+', '-', '+i', '-i']. 
The sign '+' at the index J of the acq_cycle array means that the corresponding values from the data arrays will be added with a factor '+1' to the resulting array:
```python3
answer = answer + data1[J] + 1j*data2[J]
```
The sign '-' at the index J of the acq_cycle means that the corresponding values from the data arrays will be added with a factor '-1' to the resulting array:
```python3
answer = answer - data1[J] - 1j*data2[J]
```
The sign '+i' at the index J of the acq_cycle means that the corresponding values from the data arrays will be added with a factor '+1j' to the resulting array:
```python3
answer = answer + 1j*data1[J] - data2[J]
```
The sign '-i' at the index J of the acq_cycle means that the corresponding values from the data arrays will be added with a factor '-1j' to the resulting array:
```python3
answer = answer - 1j*data1[J] + data2[J]
```
The output of the function is the real ang imaginary parts of the 'answer' array after complete cycle of mathematical transformations. These can be both 1D and 2D arrays, depending on the shape of the input data arrays.
### pulser_repetition_rate(*r_rate)
```python3
pulser_repetition_rate(*r_rate)
Arguments: r_rate = string (number + scaling ['Hz','kHz','MHz']); Output: string.
Example: pulser_repetition_rate('2 Hz') sets the repetition rate to 2 Hz.
```
The function queries (if called without argument) or sets (if called with one argument) the repetition rate of the pulse sequence. If there is an argument it will be set as a repetition rate. If there is no argument the current repetition rate is returned as a string. The maximum available repetition rate depends on the total length of the pulse sequence and cannot exceed 5 MHz.<br/>
### pulser_shift(*pulses)
```python3
pulser_shift(*pulses)
Arguments: none or string of pulse names; Output: none.
Example: pulser_shift() shifts all currently active pulses by their respective delta_start.
```
This function can be called with either no argument or with a list of comma separated pulse names (i.e. 'P0', 'P1'). If no argument is given the start time of all pulses that have a nonzero delta_start and are currently active (do not have a length of 0) are shifted by their corresponding delta_start value. If there is one argument or a list of comma separated pulse names only the start time of the listed pulses are changed. Calling this function also resets the phase (if specified in the argument phase_list of the [pulser_pulse()](#pulser_pulse)) to the first phase in the phase_list.
### pulser_increment(*pulses)
```python3
pulser_increment(*pulses)
Arguments: none or string of pulse names; Output: none.
Example: pulser_increment('P0') increments the pulse named 'P0' by the corresponding length_increment value.
```
This function can be called with either no argument or with a list of comma separated pulse names (i.e. 'P0', 'P1'). If no argument is given the lengths of all pulses that have a nonzero length_increment and are currently active (do not have a length of 0) are incremented by their corresponding length_increment value. If there is one argument or a list of comma separated pulse names only the lengths of the listed pulses are changed. Calling this function also resets the phase (if specified in the argument phase_list of the [pulser_pulse()](#pulser_pulse)) to the first phase in the phase_list.
### pulser_redefine_start(*, name, start)
```python3
pulser_redefine_start(*, name, start)
Arguments: name = 'Pulse name', start = a new start time of the pulse (as a string);
Output: none.
Example: pulser_redefine_start(name = 'P0', start = '100 ns') changes start setting of the 'P0' pulse to 100 ns.
```
This function should be called with two keyword arguments, namely name and start. The first argument specifies the name of the pulse as a string. The second argument defines a new value of pulse start as a string in the format value + dimension (i.e. '100 ns'). The main purpose of the function is non-uniform sampling. Please note, that the function does not update the pulse programmer. [pulser_update()](#pulser_update) should be called to apply changes.
### pulser_redefine_delta_start(*, name, delta_start)
```python3
pulser_redefine_delta_start(*, name, delta_start)
Arguments: name = 'Pulse name', delta_start = a new start time increment (as a string);
Output: none.
Example: pulser_redefine_delta_start(name = 'P0', delta_start = '10 ns') changes delta_start setting of the 'P0' pulse to 10 ns.
```
This function should be called with two keyword arguments, namely name and delta_start. The first argument specifies the name of the pulse as a string. The second argument defines a new value of delta_start as a string in the format value + dimension (i.e. '100 ns'). The main purpose of the function is non-uniform sampling. Please note, that the function does not update the pulse programmer. [pulser_update()](#pulser_update) should be called to apply changes.
### pulser_redefine_length_increment(*, name, length_increment)
```python3
pulser_redefine_length_increment(*, name, length_increment)
Arguments: name = 'Pulse name', length_increment = a new length increment (as a string);
Output: none.
Example: pulser_redefine_length_increment(name = 'P2', length_increment = '2 ns') changes length
increment setting of the 'P2' pulse to 2 ns.
```
This function should be called with two keyword arguments, namely name and length_increment. The first argument specifies the name of the pulse as a string. The second argument defines a new value of length increment as a string in the format value + dimension (i.e. '10 ms'). The main purpose of the function is non-uniform sampling. Please note, that the function does not update the pulse programmer. [pulser_update()](#pulser_update) should be called to apply changes.
### pulser_reset()
```python3
pulser_reset()
Arguments: none; Output: none.
Example: pulser_reset() resets all the pulses to their initial state and updates the pulse programmer.
```
The function switches the pulse programmer back to the initial state (including phase) in which it was in at the start of the experiment. This function can be called only without arguments. It includes the complete functionality of [pulser_pulse_reset()](#pulser_pulse_reset), but also immediately updates the pulse programmer as it is done by calling [pulser_update()](#pulser_update).
### pulser_pulse_reset(*pulses)
```python3
pulser_pulse_reset(*pulses)
Arguments: none or string of pulse names; Output: none.
Example: pulser_pulse_reset('P1') resets the pulse named 'P1' to its initial state.
```
The function switches the pulse programmer back to the initial state in which it was in at the start of the experiment. This function can be called with either no argument or with a list of comma separated pulse names. If no argument is given all pulses are reset to their initial states (including phases). The function does not update the pulser, if you want to reset all pulses and and also update the pulser use the function [pulser_reset()](#pulser_reset) instead.
### pulser_stop()
```python3
pulser_stop()
Arguments: none; Output: none.
Example: pulser_stop() stops the pulse programmer.
```
This function stops the pulse programmer. The function should always be called at the end of an experimental script.
### pulser_state()
```python3
pulser_state()
Arguments: none; Output: string.
Example: pulser_state() queries the pulse programmer state.
```
This function queries the pulse programmer state and can be called only without arguments.
### pulser_visualize()
```python3
pulser_visualize()
Arguments: none; Output: string.
Example: pulser_visualize() visualizes the pulse sequence in a form of 2D plot.
```
This function visualizes the pulse sequence as 2D plot and can be called only without arguments.
### pulser_pulse_list()
```python3
pulser_pulse_list()
Arguments: none; Output: string.
Example: pulser_pulse_list() returns the pulse sequence in a form of array.
```
This function can be called only without arguments and it returns the declared pulse sequence as an array.


