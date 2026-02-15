---
title: Pulse Programmers
nav_order: 34
layout: page
permlink: /functions/pulse_programmer/
parent: Documentation
---

### Devices

Available devices:
- Pulse Blaster ESR **500** Pro; Tested 06/2021
The device is available via ctypes. [The original C library](http://www.spincore.com/support/spinapi/using_spin_api_pb.shtml) was written by SpinCore Technologies.
- [Insys FM214x3GDA](https://www.insys.ru/mezzanine/fm214x3gda) as multichannel TTL pulse generator; Tested 03/2025
The Insys device is available via ctypes. The original library can be found [here](https://github.com/Anatoly1010/Atomize_ITC/tree/master/libs).
- Pulse Blaster Micran; Tested 12/2023

---

### Functions
- [pulser_name()](#pulser_name)<br/>
- [pulser_pulse(\*\*kargs)](#pulser_pulsekargs)<br/>
- [pulser_update()](#pulser_update)<br/>
- [pulser_next_phase()](#pulser_next_phase)<br/>
- [pulser_acquisition_cycle(data1, data2, acq_cycle)](#pulser_acquisition_cycledata1-data2-acq_cycle)<br/>
- [pulser_repetition_rate(\*r_rate)](#pulser_repetition_rater_rate)<br/>
- [pulser_shift(\*pulses)](#pulser_shiftpulses)<br/>
- [pulser_increment(\*pulses)](#pulser_incrementpulses)<br/>
- [pulser_redefine_start(\*, name, start)](#pulser_redefine_start-name-start)<br/>
- [pulser_redefine_delta_start(\*, name, delta_start)](#pulser_redefine_delta_start-name-delta_start)<br/>
- [pulser_redefine_length_increment(\*, name, length_increment)](#pulser_redefine_length_increment-name-length_increment)<br/>
- [pulser_reset()](#pulser_reset)<br/>
- [pulser_pulse_reset(\*pulses)](#pulser_pulse_resetpulses)<br/>
- [pulser_stop()](#pulser_stop)<br/>
- [pulser_state()](#pulser_state)<br/>
- [pulser_visualize()](#pulser_visualize)<br/>
- [pulser_pulse_list()](#pulser_pulse_list)<br/>
- [pulser_open()](#pulser_open)<br/>
- [pulser_close()](#pulser_close)<br/>
- [pulser_default_synt(num)](#pulser_default_syntnum)<br/>
- [pulser_phase_reset()](#pulser_phase_reset)<br>
- [pulser_instruction_from_file(flag, filename)](#pulser_instruction_from_fileflag-filename)<br>
- [pulser_clear()](#pulser_clear)<br>
- [pulser_full_stop()](#pulser_full_stop)<br>
- [pulser_test_flag(flag)](#pulser_test_flagflag)<br>

---

### pulser_name()
```python
pulser_name() -> str
```
This function returns device name.<br>

---

### pulser_pulse(\*\*kargs)
```python
pulser_pulse(\*\*kargs) -> none
```
```yml
name = 'P0' specifies a name of the pulse
channel = 'CH0' specifies a channel string (['CH0','CH1', ... ,'CH20'])
start = '0 ns' specifies a start time of the pulse (['ns','us','ms','s'])
length = '100 ns' specifies a length of the pulse (['ns','us','ms','s'])
delta_start = '0 ns' specifies a start time increment of the pulse (['ns','us','ms',s'])
length_increment = '0 ns' specifies a pulse length increment (['ns','us','ms','s'])
phase_list = [] specifies a phase cycling sequence (['+x','-x','+y','-y'])
```
```
Example: pulser_pulse('name' = 'P0', channel = 'MW', start = '100 ns', length = '100 ns', 
    delta_start = '0 ns', length_increment = '0 ns') sets the pulse with no phase cycling.
```
This function sets a pulse with specified parameters. The default argument is name = 'P0', channel = 'DETECTION', start = '0 ns', length = '100 ns', delta_start = '0 ns', length_increment = '0 ns', phase_list = []. A channel should be one of the following ['DETECTION', 'AMP_ON', 'LNA_PROTECT', 'MW', '-X', '+Y', 'TRIGGER_AWG', 'AWG', 'LASER', 'SYNT2', 'CH10', ... , 'CH20']. The scaling factor for start, length, delta_start, and length_increment key arguments should be one of the following ['ns', 'us', 'ms', 's']. The minimum available length of the pulse is 10 ns for Pulse Blaster ESR 500 Pro and 3.2 ns for Insys FM214x3GDA. The maximum available length of the pulse is 1900 ns. The maximum available length of the pulse sequence is approximately 10 s. The pulse sequence will be checked for overlap. In the auto defence mode (default option; can be changed in the config file) channels 'AMP_ON' and 'LNA_PROTECT' will be added automatically according to the delays indicated in the config file. In this mode 'AMP_ON' and 'LNA_PROTECT' pulses will be joined in one pulse if the distance between them is less than 12 ns (can be changed in the config file).<br/>
In the case of Insys FM214x3GDA start, length, delta_start, and length_increment will be rounded to a multiple of 3.2.<br/>
In the case of Pulse Blaster ESR 500 Pro DETECTION pulse should have an empty phase_list. The acquisition phases should be indicated directly in [pulser_acquisition_cycle()](#pulser_acquisition_cycledata1-data2-acq_cycle) function. In the case of Insys FM214x3GDA a phase_list of DETECTION pulse is used to [phase cycle](/atomize_docs/pages/functions/digitizer#digitizer_get_curve) the data.<br>

---

### pulser_update()
```python
pulser_update() -> none
```
```
Example: pulser_update() updates a pulse sequence and sends instructions to the pulse programmer.
```
This function updates a pulse sequence and sends instructions to the pulse programmer. It has to be called after changes have been applied to pulses either via any of the pulser functions or by changing a pulse property directly. Only by calling the function the changes are committed and the real pulses will change.<br>

---

### pulser_next_phase()
```python
pulser_next_phase() -> none
```
```
Example: pulser_next_phase() switches all pulses in the sequence to the next phase.
```
This function switches all pulses to the next phase. The phase sequence is declared in the [pulser_pulse()](#pulser_pulsekargs) in the form of phase_list = ['-y', '+x', '-x', '+x', ...]. By repeatedly calling the function one can run through the complete list of phases for the pulses. The length of all phase lists specified for different MW pulses has to be the same. This function also immediately updates the pulse sequence, as it is done by calling [pulser_update()](#pulser_update). The first call of the function corresponds to the first phase in the phase_list argument of the [pulser_pulse()](#pulser_pulsekargs).<br>

---

### pulser_acquisition_cycle(data1, data2, acq_cycle)
```python
pulser_acquisition_cycle(data1, data2, acq_cycle = []) -> numpy.array, numpy.array
```
```yml
data1, data2 = 1D or 2D numpy arrays;
acq_cycle = array of mathematical operations, i.e. ['+x', '-x', '+y', '-y'];
```                                                                                                                                                                                                            
```
Example: pulser_acquisition_cycle(np.array([1, 0]), np.array([0, 1]), acq_cycle = ['+x', '-x'])
performes given mathematical operations on the arrays.
```
This function can be used to shorten the syntax for acquisition in the case of phase cycling. The arguments are (i) two numpy arrays from a quadrature detector, (ii) array of mathematical operations to perform. Data arrays can be both 2D and 1D, representing, respectively, the case of raw oscillograms or integrated data. The length of acq_cycle array and the 1D arrays or the amount of the individual oscillograms in the 2D array should be equal. The data arrays will be treated inside the function as a complex number:
```python
answer = np.zeros( data1.shape ) + 1j*np.zeros( data2.shape )
```
The available mathematical operations are ['+x', '-x', '+y', '-x']. 
The symbol '+x' at the index J of the acq_cycle array means that the corresponding values from the data arrays will be added with a factor '+1' to the resulting array:
```python
answer = answer + data1[J] + 1j*data2[J]
```
The symbol '-x' at the index J of the acq_cycle means that the corresponding values from the data arrays will be added with a factor '-1' to the resulting array:
```python
answer = answer - data1[J] - 1j*data2[J]
```
The symbol '+y' at the index J of the acq_cycle means that the corresponding values from the data arrays will be added with a factor '+1j' to the resulting array:
```python
answer = answer + 1j*data1[J] - data2[J]
```
The symbol '-y' at the index J of the acq_cycle means that the corresponding values from the data arrays will be added with a factor '-1j' to the resulting array:
```python
answer = answer - 1j*data1[J] + data2[J]
```
The output of the function is the real ang imaginary parts of the 'answer' array after complete cycle of mathematical transformations. These can be both 1D and 2D arrays, depending on the shape of the input data arrays.
Although this function is available for Insys FM214x3GDA, it is better to use a modified version of [digitizer_get_curve()](/atomize_docs/pages/functions/digitizer#digitizer_get_curve). In this case acquisition phases should be given directly in the phase list key argument of the [DETECTION pulse](#pulser_pulsekargs).<br>

---

### pulser_repetition_rate(\*r_rate)
```python
pulser_repetition_rate(rer_rate: float + [' Hz',' kHz',' MHz']) -> none
pulser_repetition_rate() -> str
```
```
Example: pulser_repetition_rate('2 Hz') sets the repetition rate to 2 Hz.
```
This function queries (if called without argument) or sets (if called with one argument) the repetition rate of the pulse sequence. If there is an argument it will be set as a repetition rate. If there is no argument the current repetition rate is returned as a string. The maximum available repetition rate depends on the total length of the pulse sequence and cannot exceed 5 MHz.<br>

---

### pulser_shift(\*pulses)
```python
pulser_shift() -> none
pulser_shift(pulses: ['P0', 'P1', etc.]) -> none
```
```
Example: pulser_shift() shifts all currently active pulses by their respective delta_start.
```
This function can be called with either no argument or with a list of comma separated pulse names (i.e. 'P0', 'P1'). If no argument is given the start time of all pulses that have a nonzero delta_start and are currently active (do not have a length of 0) are shifted by their corresponding delta_start value. If there is one argument or a list of comma separated pulse names only the start time of the listed pulses are changed. Calling this function also resets the phase (if specified in the argument phase_list of the [pulser_pulse()](#pulser_pulse) to the first phase in the phase_list.<br>

---

### pulser_increment(\*pulses)
```python
pulser_increment() -> none
pulser_increment(pulses: ['P0', 'P1', etc.]) -> none
```
```
Example: pulser_increment('P0')
increments the pulse named 'P0' by the corresponding length_increment value.
```
This function can be called with either no argument or with a list of comma separated pulse names (i.e. 'P0', 'P1'). If no argument is given the lengths of all pulses that have a nonzero length_increment and are currently active (do not have a length of 0) are incremented by their corresponding length_increment value. If there is one argument or a list of comma separated pulse names only the lengths of the listed pulses are changed. Calling this function also resets the phase (if specified in the argument phase_list of the [pulser_pulse()](#pulser_pulsekargs) to the first phase in the phase_list.<br>

---

### pulser_redefine_start(\*, name, start)
```python
pulser_redefine_start(
    name: ['P0', 'P1', etc.], start: int/float + [' ns',' us',' ms']) -> none
```
```
Example: pulser_redefine_start(name = 'P0', start = '100 ns') changes 
the start setting of the 'P0' pulse to 100 ns.
```
This function should be called with two keyword arguments, namely name and start. The first argument specifies the name of the pulse as a string. The second argument defines a new value of pulse start as a string in the format 'number + [' ms', ' us', ' ns']'. The main purpose of the function is non-uniform sampling. Please note, that the function does not update the pulse programmer. The [pulser_update()](#pulser_update) function should be called to apply changes.<br/>
In the case of Insys FM214x3GDA start will be rounded to a multiple of 3.2.<br>

---

### pulser_redefine_delta_start(\*, name, delta_start)
```python
pulser_redefine_delta_start(
    name: ['P0', 'P1', etc.], delta_start: int/float + [' ns',' us',' ms']) -> none
```
```
Example: pulser_redefine_delta_start(name = 'P0', delta_start = '10 ns') 
changes the delta_start setting of the 'P0' pulse to 10 ns.
```
This function should be called with two keyword arguments, namely name and delta_start. The first argument specifies the name of the pulse as a string. The second argument defines a new value of delta_start as a string in the format 'number + [' ms', ' us', ' ns']'. The main purpose of the function is non-uniform sampling. Please note, that the function does not update the pulse programmer. The [pulser_update()](#pulser_update) function should be called to apply changes.<br/>
In the case of Insys FM214x3GDA delta_start will be rounded to a multiple of 3.2.<br>

---

### pulser_redefine_length_increment(\*, name, length_increment)
```python
pulser_redefine_length_increment(
    name:['P0', 'P1', etc.], length_increment: int/float + [' ns',' us',' ms']) -> none
```
```
Example: pulser_redefine_length_increment(name = 'P2', length_increment = '2 ns') 
changes the length increment setting of the 'P2' pulse to 2 ns.
```
This function should be called with two keyword arguments, namely name and length_increment. The first argument specifies the name of the pulse as a string. The second argument defines a new value of length increment as a string in the format 'number + [' ms', ' us', ' ns']'. The main purpose of the function is non-uniform sampling. Please note, that the function does not update the pulse programmer. The [pulser_update()](#pulser_update) function should be called to apply changes.<br/>
In the case of Insys FM214x3GDA length_increment will be rounded to a multiple of 3.2.<br>

---

### pulser_reset()
```python
pulser_reset() -> none
```
```
Example: pulser_reset() resets all the pulses to their initial state and updates the programmer.
```
The function switches the pulse programmer back to the initial state (including phase) in which it was in at the start of the experiment. This function can be called only without arguments. It includes the complete functionality of [pulser_pulse_reset()](#pulser_pulse_reset), but also immediately updates the pulse programmer as it is done by calling [pulser_update()](#pulser_update).<br/>
The additional keyword "internal_cycle" can be used with in combination the [pulser_instruction_from_file()](#pulser_instruction_from_fileflag-filename) function to achieve correct update of the pulse programmer. The available options are ['True', 'False']. The default option is 'False'.<br>
This function is not available for Insys FM214x3GDA. The function [pulser_pulse_reset()](#pulser_pulse_reset) can be used instead.<br>

---

### pulser_pulse_reset(\*pulses)
```python
pulser_pulse_reset() -> none
pulser_pulse_reset(pulses: ['P0', 'P1', etc.]) -> none
```
```
Example: pulser_pulse_reset('P1') resets the pulse named 'P1' to its initial state.
```
This function switches the pulse programmer back to the initial state in which it was in at the start of the experiment. This function can be called with either no argument or with a list of comma separated pulse names. If no argument is given all pulses are reset to their initial states (including phases). The function does not update the pulser, if you want to reset all pulses and and also update the pulser use the function [pulser_reset()](#pulser_reset) instead.<br>
The additional keyword "internal_cycle" can be used with in combination the [pulser_instruction_from_file()](#pulser_instruction_from_fileflag-filename) function to achieve correct update of the pulse programmer. The available options are ['True', 'False']. The default option is 'False'.<br>

---

### pulser_stop()
```python
pulser_stop() -> none
```
```
Example: pulser_stop() stops the pulse programmer.
```
This function stops the pulse programmer. The function should always be called at the end of an experimental script in the case of Pulse Blaster ESR 500 Pro.<br/>
This function is not available for Insys FM214x3GDA. The function [pulser_close()](#pulser_close) must be used instead.<br>

---

### pulser_state()
```python
pulser_state() -> str
```
```
Example: pulser_state() queries the pulse programmer state.
```
This function queries the pulse programmer state and should be called only without arguments. This function is only available for Pulse Blaster ESR 500 Pro.<br>

---

### pulser_visualize()
```python
pulser_visualize() -> 2D plot
```
```
Example: pulser_visualize() visualizes the pulse sequence in a form of 2D plot.
```
This function visualizes the pulse sequence as 2D plot and should be called only without arguments.<br>

---

### pulser_pulse_list()
```python
pulser_pulse_list() -> list of str
```
```
Example: pulser_pulse_list() returns the pulse sequence in a form of a python list.
```
This function should be called only without arguments and it returns the declared pulse sequence as an array.<br>

---

### pulser_open()
```python
pulser_open() -> none
```
```
Example: pulser_open() opens the board for use.
```
This function should be called only without arguments and is only available for Insys FM214x3GDA and Pulse Blaster Micran. In the case of Insys FM214x3GDA, the function should be used after defining pulses and repetition rate with [pulser_pulse()](#pulser_pulsekargs) and [pulser_repetition_rate()](#pulser_repetition_rater_rate).<br>

---

### pulser_close()
```python
pulser_close() -> none
```
```
Example: pulser_close() closes the board after use.
```
This function should be called only without arguments and is only available for Insys FM214x3GDA and Pulse Blaster Micran. The function must be used at the end of an experimental script to gracefully close the board.<br>

---

### pulser_default_synt(num)
```python
pulser_default_synt(num: [1, 2]) -> none
```
```
Example: pulser_default_synt(2) selects synthesizer 2 as the default source.
```
This function should be called only with one argument and selects the default sources for microwave pulse generation.<br/>
The available options are [1, 2]. This function is only available for Insys FM214x3GDA.<br>

---

### pulser_phase_reset()
```python
pulser_phase_reset() -> none
```
```
Example: pulser_phase_reset() resets the phase index to zero.
```
This function resets the phase index to zero in order to start phase cycling once again. This function is only available for Pulse Blaster ESR 500 Pro and Pulse Blaster Micran.<br>

---

### pulser_instruction_from_file(flag, filename)
```python
pulser_instruction_from_file(flag: [0, 1], filename = 'instructions.out') -> none
```
```
Example: pulser_instruction_from_file(1, filename = 'instructions.out') 
read instructions from the {instructions.out} file.
```
This special function reads the instructions for pulse programmer from the specified file. The keyword argument 'filename' corresponds to the file to read. The available options for 'flag' are [0, 1], where 1 means that the instructions will be read from the file. This function is only available for Pulse Blaster ESR 500 Pro and Pulse Blaster Micran.<br>

---

### pulser_clear()
```python
pulser_clear() -> none
```
This is a special function for clearing pulse array {self.pulse_array} and other status flags of the device module. The function is usually used in GUI applications that use the device module.<br>

---

### pulser_full_stop()
```python
pulser_full_stop() -> none
```
This is a special function for a complete stop of the pulse programmer, whichs means all the pulse instrutions will be set to zero.<br> This function is only available for Pulse Blaster Micran.<br>

---

### pulser_test_flag(flag)
```python
pulser_test_flag(flag = ['None','test']) -> none
```
This is a special function for changing test mode. The available options are ['None', 'test']. The function is usually used in GUI applications that use the device module.<br>
