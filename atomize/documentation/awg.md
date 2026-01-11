---
title: Arbitrary Wave Generators
nav_order: 21
layout: page
permlink: /functions/awg/
parent: Documentation
---

### Devices

Available devices:
- Spectrum M4I **6631** X8; Tested 07/2021
The original [library](https://spectrum-instrumentation.com/en/m4i6631-x8) was written by Spectrum. The library header files (pyspcm.py, spcm_tools.py) should be added to the path directly in the module file: 
```python
sys.path.append('/path/to/python/header/of/Spectrum/library')
from pyspcm import *
from spcm_tools import *
```
- [Insys FM214x3GDA](https://www.insys.ru/mezzanine/fm214x3gda) as DAC; Tested 03/2025
The Insys device is available via ctypes. The original library can be found [here](https://github.com/Anatoly1010/Atomize_ITC/tree/master/libs).

---

### Functions
- [awg_name()](#awg_name)<br/>
- [awg_setup()](#awg_setup)<br/>
- [awg_update()](#awg_update)<br/>
- [awg_stop()](#awg_stop)<br/>
- [awg_close()](#awg_close)<br/>
- [awg_pulse(**kargs)](#awg_pulsekargs)<br/>
- [awg_pulse_sequence(**kargs)](#awg_pulse_sequencekargs)<br/>
- [awg_shift(*pulses)](#awg_shiftpulses)<br/>
- [awg_increment(*pulses)](#awg_incrementpulses)<br/>
- [awg_next_phase()](#awg_next_phase)<br/>
- [awg_redefine_delta_phase(*, name, delta_phase)](#awg_redefine_delta_phase-name-delta_phase)<br/>
- [awg_redefine_phase(*, name, phase)](#awg_redefine_phase-name-phase)<br/>
- [awg_redefine_frequency(*, name, freq)](#awg_redefine_frequency-name-freq)<br/>
- [awg_redefine_delta_start(*, name, delta_start)](#awg_redefine_delta_start-name-delta_start)<br/>
- [awg_redefine_length_increment(*, name, length_increment)](#awg_redefine_length_increment-name-length_increment)<br/>
- [awg_add_phase(*, name, add_phase)](#awg_add_phase-name-add_phase)<br/>
- [awg_reset()](#awg_reset)<br/>
- [awg_pulse_reset(*pulses)](#awg_pulse_resetpulses)<br/>
- [awg_number_of_segments(*segments)](#awg_number_of_segmentssegments)<br/>
- [awg_channel(*channel)](#awg_channelchannel)<br/>
- [awg_sample_rate(*s_rate)](#awg_sample_rates_rate)<br/>
- [awg_clock_mode(*mode)](#awg_clock_modemode)<br/>
- [awg_reference_clock(*ref_clock)](#awg_reference_clockref_clock)<br/>
- [awg_card_mode(*mode)](#awg_card_modemode)<br/>
- [awg_trigger_channel(*channel)](#awg_trigger_channelchannel)<br/>
- [awg_trigger_mode(*mode)](#awg_trigger_modemode)<br/>
- [awg_loop(*loop)](#awg_looploop)<br/>
- [awg_trigger_delay(*delay)](#awg_trigger_delaydelay)<br/>
- [awg_amplitude(*amplitude)](#awg_amplitudeamplitude)<br/>
- [awg_visualize()](#awg_visualize)<br/>
- [awg_pulse_list()](#awg_pulse_list)<br/>
- [awg_clear()](#awg_clear)<br>
- [awg_clear_pulses()](#awg_clear_pulses)<br>
- [awg_test_flag(flag)](#awg_test_flagflag)<br>

---

### awg_name()
```python
awg_name() -> str
```
This function returns device name.<br>

---

### awg_setup()
```python
awg_setup() -> none
```
```
Examples: awg_setup() writes all the settings into the AWG card.
```
This function writes all the settings modified by other functions to the AWG card. The function should be called only without arguments. One needs to initialize the settings before calling [awg_update()](#awg_update). The default settings (if no other function was called) are the following: Sample clock is 1250 MHz; Clock mode is 'Internal'; Reference clock is 100 MHz; Card mode is 'Single'; Trigger channel is 'External'; Trigger mode is 'Positive'; Loop is infinity; Trigger delay is 0; Enabled channels are CH0 and CH1; Amplitude of CH0 is '600 mV'; Amplitude of CH1 is '533 mV'; Number of segments is 1; Card memory size is 64 samples; Buffer is empty.<br/>
This function is not available for Insys FM214x3GDA. This is done by [pulser_open()](/atomize_docs/pages/functions/pulse_programmer#pulser_open) function.<br>

---

### awg_update()
```python
awg_update() -> none
```
```
Examples: awg_update() runs the AWG card.
```
This function redefines the buffer (in case the function like [awg_shift()](#awg_shift) has been called) and runs the AWG card. The function should be called only without arguments.<br/>
This function is not available for Insys FM214x3GDA. This is done by [pulser_update()](/atomize_docs/pages/functions/pulse_programmer#pulser_update) function.<br>

---

### awg_stop()
```python
awg_stop() -> none
```
```
Example: awg_stop() stops the AWG card.
```
This function stops the AWG card and should be called only without arguments. If an infinite number of loops is defined by the [awg_loop()](#awg_looploop) function, the [awg_stop()](#awg_stop) should always be called before redefining the buffer by the [awg_update()](#awg_update). If a finite number of loops is defined, the card will stop automatically.<br/>
This function is not available for Insys FM214x3GDA. There is no need to stop this DAC.<br>

---

### awg_close()
```python
awg_close() -> none
```
```
Example: awg_close() closes the AWG driver.
```
This function closes the AWG driver and should be called only without arguments. The function should always be called at the end of an experimental script, since the AWG card driver is opened during whole experiment in order to achieve high rate of buffer updating. It is STRONGLY recommended to add a graceful closing of the card to the experimental scripts for the case of an abrupt termination of the process. As a possible option, one can use signal library:<br>

```python
import signal
import atomize.device_modules.Spectrum_M4I_6631_X8 as spectrum

awg = spectrum.Spectrum_M4I_6631_X8()

def cleanup():
    awg.awg_stop()
    awg.awg_close()
    sys.exit(0)

signal.singal(signal.SIGTERM, cleanup)

# AWG setup and experimental script
#
#
```

This function is not available for Insys FM214x3GDA. This is done with [pulser_close()](/atomize_docs/pages/functions/pulse_programmer#pulser_close)<br>

---

### awg_pulse(**kargs)
```python
awg_pulse(**kagrs) -> none
```
```yml
name = 'P0' specifies a name of the pulse
channel = 'CH0' specifies a channel string (['CH0','CH1'])
func = 'SINE' specifies a function type (['SINE','GAUSS','SINC','BLANK','WURST','SECH/TANH'])
frequency = '200 MHz' specifies a frequency of the pulse (['0-280 MHz'])
phase = 0 specifies a phase of the pulse (in radians)
phase_list = [] specifies a phase cycling sequence (['+x','-x','+y','-y'])
delta_phase = 0 specifies a phase increment of the pulse (in radians) for
'Single' and 'Multi' card mode
length = '16 ns' specifies a pulse length (['ns','us','ms'])
sigma = '16 ns' specifies a sigma value for GAUSS pulses (['ns','us','ms'])
length_increment = '0 ns' specifies a pulse length and sigma increment (['ns','us','ms'])
start = '0 ns' specifies a pulse start (['ns','us','ms']) for the 'Single 
Joined' card mode
delta_start = '0 ns' specifies a pulse delta start (['ns','us','ms']) for the
'Single Joined' card mode
d_coef = 1 specifies an additional coefficient for adjusting pulse amplitudes
n = 1 specifies a special coefficient for WURST and SECH/TANH pulse determining the steepness
of the amplitude function
b = 0.02 specifies a parameter for SECH/TANH pulse determining the truncation parameter in 1/ns
```
```
Example: awg_pulse(name = 'P0', channel = 'CH0', func = 'SINE', frequency ='200 MHz', 
    phase = pi/2, length = '40 ns') sets the 40 ns length 200 MHz sine pulse with pi/2 phase.
```
This function sets a pulse with specified parameters for 'Single', 'Multi', and 'Single Joined' card mode. The AWG card buffer will be filled according to key arguments of the awg_pulse() function. The default argument is the following: 
name = 'P0', channel = 'CH0', func = 'SINE', frequency = '200 MHz', phase = 0, delta_phase = 0, length = '16 ns', sigma = '0 ns', length_increment = '0 ns', start = '0 ns', delta_start = '0 ns', d_coef = 1, n = 1, phase_list = []. A channel should be one of the following ['CH0', 'CH1']. The frequency should be in MHz, the minimum value is 0 MHz, maximum is 280 MHz. For WURST and SECH/TANH pulse the frequency argument should be a tuple ('center_freq MHz', 'sweep_range MHz'), i.e. ('0 MHz', '100 MHz'). The scaling factor for length and sigma key arguments should be one of the following ['ns','us','ms']. The minimum available length and sigma of the pulse is 0 ns. The maximum available length and sigma of the pulse is 1900 ns. The available functions are ['SINE','GAUSS','SINC','BLANK','WURST','SECH/TANH']. For 'SINE', 'BLANK', 'WURST', and SECH/TANH function parameter sigma has no meaning. For 'GAUSS' function parameter sigma is a sigma of Gaussian. For 'SINC' function a combination of parameters length and sigma specifies the width of the SINC pulse, i.e. length = '40 ns' and sigma = '10 ns' means that SINC pulse will be from -4pi to +4pi. Function 'BLANK' is an empty pulse. Function 'WURST' is a wideband, uniform rate, smooth truncation pulse. Function 'SECH/TANH' is a wideband sech/tanh pulse. The length_increment keyword affects both the length and sigma of the pulse. The scaling factor for start and delta_start key arguments should be one of the following ['ns','us','ms']. The [amplitudes](#awg_amplitudeamplitude) of the AWG card channels will be divided by the value of the d_coef parameter, which ultimately determines the final amplitude of each pulse. The d_coef parameter should be more or equal to 1. The n parameter determines the steepness of the amplitude function of the WURST and SECH/TANH pulses. For other functions it has no meaning. The b parameter (in 1/ns) determines the truncation parameter of the SECH/TANH pulse. For other functions it has no meaning.<br/>
It is recommended to first define all pulses and then define the settings of the AWG card. To write the settings [awg_setup()](#awg_setup) function should be called. To run specified pulses the [awg_update()](#awg_update) function should be called.<br/>
Key argument delta_phase define a pulse phase shift and has no meaning for 'Single Joined' card mode, since the phase of the pulse will be calculated automatically. Key arguments start and delta_start define a pulse position for 'Single Joined' card mode and has no meaning for 'Single' or 'Multi' card mode.<br/>
Pulse settings for Insys FM214x3GDA corresponds to 'Single' card mode. In addition for this device arguments 'start', 'length', 'delta_start', and 'length_increment' will be rounded to a multiple of 3.2 and for all AWG pulses there should be a corresponding trigger pulse, generated by [pulser_pulse()](/atomize_docs/pages/functions/pulse_programmer#pulser_pulse) function.<br>

---

### awg_pulse_sequence(**kargs)
```python
awg_pulse_sequence(**kagrs) -> none
```
```yml
pulse_type = ['SINE','GAUSS','SINC','BLANK','WURST','SECH/TANH']
pulse_start = [pulse 1 start in ns, pulse 2 start in ns, ...]
pulse_delta_start = [pulse 1 delta start in ns, pulse 2 delat start in ns, ...]
pulse_length = [pulse 1 length in ns, pulse 2 length in ns, ...]
pulse_phase = [pulse 1 phase, pulse 2 phase, ...], phase = ['+x','-x','+y','-y']
pulse_sigma = [pulse 1 sigma in ns, pulse 2 sigma in ns, ...]
pulse_frequency = [pulse 1 frequency in ns, pulse 2 frequency in ns, ...]
number_of_points = total number of points in a pulse sequence, taking into
account shifting of the pulses
loop = number of repetition of each point
rep_rate = repetition rate of the pulse sequence in Hz
n = [pulse 1 n parameter in arb. u., n parameter in arb. u., ...]
b = [pulse 1 b parameter in 1/ns, b parameter in 1/ns., ...]
```
```
Example: awg_pulse_sequence(pulse_type = ['SINE', 'GAUSS', 'SINE'],
    pulse_start = [0, 160, 320], pulse_delta_start = [0, 0, 40],
    pulse_length = [40, 120, 40], pulse_phase = ['+x', '+x', '+x'],
    pulse_sigma = [40, 20, 40], pulse_frequency = [50, 200, 40], n = [20, 20, 20], 
    b = [0.02, 0.02, 0.02], number_of_points = 800, loop = 10, rep_rate = 10000) 
sets a pulse train of three pulses with 10 kHz repetition rate and a third pulse shifting 
by 40 ns at each of 800 points.
```
This function sets a pulse sequence with specified parameters for 'Sequence' card [mode](#awg_cardmode). The AWG card buffer will be filled according to key arguments of the awg_pulse_sequence() function. There is no default arguments, that is why all keywords must be specified. The minimum available length and sigma of the pulse is 0 ns. The maximum available length and sigma of the pulse is 1900 ns. For WURST and SECH/TANH pulses the frequency should be a tuple ('Center_freq MHz', 'sweep_freq MHz'), i.e. ('0 MHz', '100 MHz'). The available functions are ['SINE', 'GAUSS', 'SINC', 'BLANK', 'WURST', 'SECH/TANH']. For 'SINE', 'BLANK', 'WURST', and 'SECH/TANH' functions parameter sigma has no meaning. For 'GAUSS' function parameter sigma is a sigma of Gaussian. For 'SINC' function a combination of parameters length and sigma specifies the width of the SINC pulse in the same manner as the function [awg_pulse()](#awg_pulsekargs). Function 'BLANK' is an empty pulse. Function 'WURST' is a wideband, uniform rate, smooth truncation pulse. Function 'SECH/TANH' is a wideband sech/tanh pulse. The n parameter determines the steepness of the amplitude function of the WURST and SECH/TANH pulse. For other functions it has no meaning. The b parameter (in 1/ns) determines the truncation parameter of the SECH/TANH pulse. For other functions it has no meaning.<br/>
Please note, that each new call of the [awg_pulse_sequence()](#awg_pulse_sequencekargs) function will redefine the pulse sequence. Pulse_start array must be sorted. A number of enabled channels should be defined before [awg_pulse_sequence()](#awg_pulse_sequencekargs).<br/>
To write the settings [awg_setup()](#awg_setup) function should be called. To run a specified pulse sequence the [awg_update()](#awg_update) function should be called. After going through all the buffer the AWG card will be stopped.<br/>
This function is not available for Insys FM214x3GDA.<br>

---

### awg_shift(*pulses)
```python
awg_shift() -> none
awg_shift(pulses: ['P0', 'P1', etc.]) -> none
```
```
Example: awg_shift() 
shifts the phase of all currently active pulses by their respective delta_phase.
```
This function can be called with either no argument or with a list of comma separated pulse names (i.e. 'P0', 'P1'). In the 'Single' or 'Multi' card mode, if no argument is given the phase of all pulses that have a nonzero delta_phase and are currently active (do not have a length of 0) are shifted by their corresponding delta_phase value. If there is one argument or a list of comma separated pulse names only the phase of the listed pulses are changed.<br/>
In the 'Single Joined' card mode, the start values of the specified pulses are shifted by the defined delta_start values. Phases of the pulses are not changed, since they are calculated from the pulse positions automatically.<br/>
For the 'Sequence' card mode, the function has no meaning. Calling this function also resets the phase (if specified in the argument phase_list of the [awg_pulse()](#awg_pulse)) to the first phase in the phase_list.<br>

---

### awg_increment(*pulses)
```python
awg_increment() -> none
awg_increment(pulses: ['P0', 'P1', etc.]) -> none
```
```
Example: awg_increment('P0')
increments the length and sigma of the pulse named 'P0' by the corresponding increment value.
```
This function can be called with either no argument or with a list of comma separated pulse names (i.e. 'P0', 'P1'). In the 'Single', 'Multi' or 'Single Joined' card mode, if no argument is given the lengths and sigmas of all pulses that have a nonzero increment and are currently active (do not have a length of 0) are incremented by their corresponding increment value. If there is one argument or a list of comma separated pulse names only the lengths and sigmas of the listed pulses are changed.<br/>
Please, note that the function always keeps the ratio length/sigma for GAUSS and SINC pulses. For instance, if length = '64 ns', sigma = '16 ns', and increment = '10 ns' after calling awg_increment() once, the parameters will be length = '104 ns', sigma = '26 ns', and increment = '10 ns'.<br/>
For the 'Sequence' card mode, the function has no meaning. Calling this function also resets the phase (if specified in the argument phase_list of the [awg_pulse()](#awg_pulse)) to the first phase in the phase_list.<br>

---

### awg_next_phase()
```python
awg_next_phase() -> none
```
```
Example: awg_next_phase() switches all declared pulses to the next phase.
```
This function switches all pulses to the next phase. The phase sequence is declared in the [awg_pulse()](#awg_pulse) in the form of phase_list = ['-y', '+x', '-x', '+x', ...]. Argument '+x' means that the phase of the pulse will be equal to 'phase' declared in the [awg_pulse()](#awg_pulse). Argument '-x' corresponds to the phase shifted by pi radians in comparison with the 'phase' declared in the [awg_pulse()](#awg_pulse). Argument '+y' corresponds to pi/2 radians shift. Argument '-y' - 3pi/2 radians. By repeatedly calling the function one can run through the complete list of phases for the pulses. The length of all phase lists specified for different pulses has to be the same. This function also immediately updates the AWG card buffer, as it is done by calling [awg_update()](#awg_update). The first call of the function corresponds to the first phase in the phase_list argument of the [awg_pulse()](#awg_pulse).<br>

---

### awg_redefine_delta_phase(*, name, delta_phase)
```python
awg_redefine_delta_phase(name: ['P0', 'P1', etc.], delta_phase: float) -> none
```
```
Example: awg_redefine_delta_phase(name = 'P0', delta_phase = pi) 
changes delta_phase setting of the 'P0' pulse to pi radians.
```
This function should be called with two keyword arguments, namely name and delta_phase. The first argument specifies the name of the pulse as a string. The second argument defines a new value of delta_phase in radians. The main purpose of the function is non-uniform sampling. Please note, that the function does not update the AWG card. The [awg_update()](#awg_update) function should be called to apply changes. The function has no meaning for the 'Single Joined' and Sequence' card mode, since phases of the pulses are calculated from the pulse positions automatically.<br>

---

### awg_redefine_phase(*, name, phase)
```python
awg_redefine_phase(*, name, phase)
awg_redefine_phase(name: ['P0', 'P1', etc.], phase: float) -> none
```
```
Example: awg_redefine_phase(name = 'P0', phase = pi) 
changes phase setting of the 'P0' pulse to pi radians.
```
This function should be called with two keyword arguments, namely name and phase. The first argument specifies the name of the pulse as a string. The second argument defines a new value of phase in radians. The main purpose of the function is phase cycling. Please note, that the function does not update the AWG card. The [awg_update()](#awg_update) function should be called to apply changes. The function has no meaning for the 'Sequence' card mode. One should redefine all the sequence instead.<br>

---

### awg_redefine_frequency(*, name, freq)
```python
awg_redefine_frequency(name: ['P0', 'P1', etc.], freq: float + [' MHz']) -> none
```
```
Example: awg_redefine_frequency(name = 'P0', freq = '10 MHz') 
changes frequency setting of the 'P0' pulse to '10 MHz'.
```
This function should be called with two keyword arguments, namely name and frequency. The first argument specifies the name of the pulse as a string. The second argument defines a new value of frequency as a string, i.e. '100 MHz' or a list of string ('0 MHz', '100' MHz) for WURST and SECH/TANH pulses, see [awg_pulse()](#awg_pulse) for more details. Please note, that the function does not update the AWG card. The [awg_update()](#awg_update) function should be called to apply changes. The function has no meaning for the 'Sequence' card mode. One should redefine all the sequence instead.<br>

---

### awg_redefine_delta_start(*, name, delta_start)
```python
awg_redefine_delta_start(
    name: ['P0', 'P1', etc.], delta_start: int/float + [' ns',' us',' ms']) -> none
```
```
Example: awg_redefine_delta_start(name = 'P0', delta_start = '10 ns') 
changes delta_start setting of the 'P0' pulse to 10 ns.
```
This function should be called with two keyword arguments, namely name and delta_start. The first argument specifies the name of the pulse as a string. The second argument defines a new value of delta_start as a string in the format 'number + [' ns', ' us', ' ms']. The main purpose of the function is non-uniform sampling. Please note, that the function does not update the AWG card. The [awg_update()](#awg_update) function should be called to apply changes. The function has no meaning for the 'Single', 'Multi', and 'Sequence' card mode, since in these modes the start of the pulse is determined by the trigger event.<br>

---

### awg_redefine_length_increment(*, name, length_increment)
```python
awg_redefine_length_increment(
    name: ['P0', 'P1', etc.], length_increment: int/float + [' ns',' us',' ms']) -> none
```
```
Example: awg_redefine_length_increment(name = 'P2', length_increment = '10 ns')
changes length increment setting of the 'P2' pulse to 10 ns.
```
This function should be called with two keyword arguments, namely name and length increment. The first argument specifies the name of the pulse as a string. The second argument defines a new value of length increment as a string in the format 'number + [' ns', ' us', ' ms']. The main purpose of the function is non-uniform sampling. Please note, that the function does not update the AWG card. The [awg_update()](#awg_update) function should be called to apply changes. The function has no meaning for the 'Sequence' card mode. One should redefine all the sequence instead.<br>

---

### awg_add_phase(*, name, add_phase)
```python
awg_add_phase(name: ['P0', 'P1', etc.], add_phase: float) -> none
```
```
Example: awg_add_phase('P0', add_phase = pi) adds pi radians to the 'P0' pulse.
```
This function should be called with two keyword arguments, namely name and add_phase. The first argument specifies the name of the pulse as a string. The second argument defines a value of phase in radians to add. The main purpose of the function is phase cycling. Please note, that the function does not update the AWG card. The [awg_update()](#awg_update) function should be called to apply changes. The function has no meaning for the 'Sequence' card mode. One should redefine all the sequence instead.<br>

---

### awg_reset()
```python
awg_reset() -> none
```
```
Example: awg_reset() resets all the pulses to their initial state and updates the AWG card.
```
This function switches the AWG card back to the initial state in which it was in at the start of the experiment. This function can be called only without arguments. It includes the complete functionality of [awg_pulse_reset()](#awg_pulse_reset), but also immediately updates the AWG card as it is done by calling [awg_update()](#awg_update). The function has no meaning for the 'Sequence' card mode. One should redefine all the sequence instead.<br/>
This function is not available for Insys FM214x3GDA. The function [awg_pulse_reset()](#pulser_pulse_reset) can be used instead.<br>

---

### awg_pulse_reset(*pulses)
```python
awg_pulse_reset() -> none
awg_pulse_reset(pulses: ['P0', 'P1', etc.]) -> none
```
```
Example: awg_pulse_reset('P1') resets the pulse named 'P1' to its initial state.
```
This function switches the AWG card back to the initial state in which it was in at the start of the experiment. This function can be called with either no argument or with a list of comma separated pulse names. If no argument is given all pulses are reset to their initial states (including phases). If there is one argument or a list of comma separated pulse names only the listed pulses are returned back to the initial state. The function does not update the AWG card, if you want to reset all pulses and and also update the AWG card use the function [awg_reset()](#awg_reset) instead. The function has no meaning for the 'Sequence' card mode. One should redefine all the sequence instead.<br>

---

### awg_number_of_segments(*segments)
```python
awg_number_of_segments(segments: int) -> none
awg_number_of_segments() -> int
```
```
Example: awg_number_of_segments(2) sets the number of segments to 2.
```
This function queries or sets the number of segments for ['Multi'](#awg_card_modemode) card mode. In order to set the number of segments higher than 1, the AWG card should be in ['Multi'](#awg_card_modemode) mode. If there is no argument the function will return the current number of segments. If there is an argument the specified number of segmetns will be set.<br/>
The maximum available number of segments is 200. Default value is 1.<br/>
This function is not available for Insys FM214x3GDA.<br>

---

### awg_channel(*channel)
```python
awg_channel(channel: ['CH0','CH1']) -> none
awg_channel() -> str
```
```
Example: awg_channel('CH0', 'CH1') enables output from CH0 and CH1.
```
This function enables output from the specified channel or queries enabled channels. If there is no argument the function will return the currently enabled channels. If there is an argument the output from the specified channel will be enabled.<br/>
The channel should be one of the following: ['CH0', 'CH1']. Default option is when both channels are enabled.<br/>
This function is not available for Insys FM214x3GDA, only two channels are available.<br>

---

### awg_sample_rate(*s_rate)
```python
awg_sample_rate(s_rate: int) -> none
awg_sample_rate() -> int
```
```
Example: awg_sample_rate(1250) sets the AWG card sample rate to 1250 MHz.
```
This function queries or sets the AWG card sample rate (in MHz). If there is no argument the function will return the current sample rate. If there is an argument the specified sample rate will be set.<br/>
The minimum available sample rate is 50 MHz. The maximum available sample rate is 1250 MHz. Default value is 1250 MHz. Please note that sample rate affects the delay between a trigger event and the AWG card output. The delay is determined in samples and can be found in the documentation.<br/>
This function is not available for Insys FM214x3GDA, the default sample rate is 1250 MHz.<br>

---

### awg_clock_mode(*mode)
```python
awg_clock_mode(mode: ['Internal','External']) -> none
awg_clock_mode() -> str
```
```
Example: awg_clock_mode('Internal') sets the Internal AWG card clock mode.
```
This function queries or sets the AWG card clock mode. If there is no argument the function will return the current clock mode setting. If there is an argument the specified clock mode will be set.<br/>
The clock mode should be one of the following: ['Internal', 'External']. According to the documentation, the internal sampling clock is generated in default mode by a programmable high precision quartz. The external clock input of the M3i/M4i series is fed through a PLL to the clock system. Therefore the input will act as a reference clock input thus allowing to either use a copy of the external clock or to generate any sampling clock within the allowed range from the reference clock. Due to the fact that the driver needs to know the external fed in frequency for an exact calculation of the sampling rate the reference clock should be set by the [awg_reference_clock()](#awg_reference_clockclock) function. Default setting is 'Internal'.<br/>
This function is not available for Insys FM214x3GDA.<br>

---

### awg_reference_clock(*ref_clock)
```python
awg_reference_clock(ref_clock: int) -> none
awg_reference_clock() -> int
```
```
Example: awg_reference_clock(100) sets the AWG card reference clock to 100 MHz.
```
This function queries or sets the AWG card reference clock in MHz for 'External' mode of the [awg_clock_mode()](#awg_clock_modemode) function. If there is no argument the function will return the current reference clock. If there is an argument the specified reference clock will be set.<br/>
The minimum available reference clock is 10 MHz. The maximum available reference clock is 1000 MHz. Default value is 100 MHz.<br/>
This function is not available for Insys FM214x3GDA.<br>

---

### awg_card_mode(*mode)
```python
awg_card_mode(mode: ['Single','Multi','Single Joined','Sequence']) -> none
awg_card_mode() -> str
```
```
Example: awg_card_mode('Multi') sets the 'Multi' card mode.
```
This function queries or sets the AWG card mode. If there is no argument the function will return the current сard mode setting. If there is an argument the specified card mode will be set.<br/>
The card mode should be one of the following: ['Single', 'Multi', 'Single Joined', 'Sequence']. According to the documentation, in the 'Single' mode a data from on-board memory will be replayed on every detected trigger event. The number of replays can be programmed by [loops](#awg_looploop). 'Single Joined' mode is a modification of the 'Single' mode with a possibility of defining more than one pulse. In this mode, all defined pulses are combined into a sequence of pulses according to the their start position, determined by start keyword of the [awg_pulse()](#awg_pulse) function. Please note, that if two channels are enabled the pulse sequence for the second channel will be generated automatically using a phase shifting specified in the config file. In the 'Multi' mode every detected trigger event replays one data block (segment). Segmented memory is available only in 'External' trigger [mode](#awg_trigger_modemode). In the 'Sequence' mode it is possible to define a whole pulse sequence by the [awg_pulse_sequence()](#awg_pulse_sequence) function. The pulse sequence has a specified number of points that is looped specified times. Switching between points is achieved using a trigger event. Please note, that if two channels are enabled the pulse sequence for the second channel will be generated automatically using a phase shifting specified in the config file. Default setting is 'Single'.<br/>
This function is not available for Insys FM214x3GDA, it operates in the mode close to 'Single'.<br>

---

### awg_trigger_channel(*channel)
```python
awg_trigger_channel(channel: ['Software','External']) -> none
awg_trigger_channel() -> str
```
```
Example: awg_trigger_channel('Software') sets the 'Software' trigger.
```
This function queries or sets the AWG card trigger channel. If there is no argument the function will return the current trigger channel. If there is an argument the specified channel will be used as trigger.<br/>
The channel should be one of the following: ['Software', 'External']. Trigger channel 'External' corresponds to 'Trg0' channel of the AWG card. Default setting is 'External'.<br/>
This function is not available for Insys FM214x3GDA.<br>

---

### awg_trigger_mode(*mode)
```python
awg_trigger_mode(mode: ['Positive','Negative','High','Low']) -> none
awg_trigger_mode() -> str
```
```
Example: awg_trigger_mode('Positive') sets the trigger detection for positive edges.
```
This function queries or sets the AWG card trigger mode. If there is no argument the function will return the current trigger mode. If there is an argument the specified trigger mode will be set.<br/>
The trigger mode should be one of the following: ['Positive', 'Negative', 'High', 'Low']. Mode 'Positive' corresponds to trigger detection for positive edges (crossing level 0 from below to above). 'Negative' to trigger detection for negative edges (crossing level 0 from above to below). 'High' to trigger detection for HIGH levels (signal above level 0). 'Low' to trigger detection for LOW levels (signal below level 0). Default setting is 'Positive'.<br/>
This function is not available for Insys FM214x3GDA.<br>

---

### awg_loop(*loop)
```python
awg_loop(loop: int) -> none
awg_loop() -> int
```
```
Example: awg_loop(0) sets an infinite number of loops.
```
This function queries or sets the number of loops for ['Multi"](#awg_card_modemode) or ['Single"](#awg_card_modemode) card mode. If there is no argument the function will return the current number of loops. If there is an argument the specified number of loops will be set.<br/>
The maximum available number of loops is 100000. A setting '0' means an infinite number of loops. Default value is 0.<br/>
This function is not available for Insys FM214x3GDA.<br>

---

### awg_trigger_delay(*delay)
```python
awg_trigger_delay(delay: float + [' ms',' us',' ns'])
awg_trigger_delay() -> str
```
```
Example: awg_trigger_delay('51.2 ns') sets the trigger delay to 51.2 ns.
```
This function queries or sets the AWG card trigger delay. If there is no argument the function will return the current trigger delay. If there is an argument the specified trigger delay will be set.<br/>
The delay step is 32 sample clock. If an input is not divisible by 32 sample clock the delay will be rounded and a warning message will be printed. Default value is '0 ns'.<br/>
This function is not available for Insys FM214x3GDA.<br>

---

### awg_amplitude(*amplitude)
```python
awg_amplitude(channel1: ['CH0','CH1'], value1: float) -> none
awg_amplitude(channel1: str, value1: float, channel2: str, value2: float) -> none
awg_amplitude(channel: ['CH0','CH1']) -> str
```
```
Example: awg_amplitude('CH0', '600', 'CH1', '600') 
sets the amplitude of CH0 to 600 mV and the amplitude of CH1 to 600 mV.
```
This function queries or sets the amplitude of the specified channels in mV. If there is only channel argument the function will return the amplitude of the specified channel. If there are two or four arguments the specified amplitude in mV will be set for specified channel.<br/>
The channel should be one of the following: ['CH0', 'CH1']. The minimum available amplitude is 80 mV. The maximum available amplitude is 2500 mV for Spectrum M4I 6631 X8 and 260 mV for Insys FM214x3GDA.<br>

---

### awg_visualize()
```python
awg_visualize() -> 2D plot
```
```
Example: awg_visualize() visualizes the AWG card buffer.
```
This function visualizes the AWG card buffer and can be called only without arguments. For the 'Single', 'Multi', and 'Single Joined' card mode, the complete buffer will be shown. For the 'Sequence' card mode only first two points will be shown. It is not recommended to use this function for very low repetition rate (less than 10 kHz) of [awg_pulse_sequence()](#awg_pulse_sequencekargs) in the 'Sequence' card mode.<br>

---

### awg_pulse_list()
```python
awg_pulse_list() -> list of str
```
```
Example: awg_pulse_list() returns the pulse sequence in a form of a python list.
```
This function can be called only without arguments and it returns the declared pulse sequence as an array.<br>

---

### awg_clear()
```python
awg_clear() -> none
```
This is a special function for clearing pulse array {self.pulse_array} and other status flags of the device module. The function is usually used in GUI applications that use the device module.<br>

---

### awg_clear_pulses()
```python
awg_clear_pulses() -> none
```
This is a special function for clearing pulse array {self.pulse_array} and other status flags of the device module when the card is opened. The function is usually used in GUI applications that use the device module.<br>

---

### awg_test_flag(flag)
```python
awg_test_flag(flag = ['None','test']) -> none
```
This is a special function for changing test mode. The available options are ['None', 'test']. The function is usually used in GUI applications that use the device module.<br>

