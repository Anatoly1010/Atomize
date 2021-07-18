# List of available functions for arbitrary wave generators

Available devices:
- Spectrum M4I 6631 X8; Untested
The original [library] (https://spectrum-instrumentation.com/en/m4i6631-x8) was written by Spectrum. The library header files (pyspcm.py, spcm_tools.py) should be added to the path directly in the module file: 
```python3
sys.path.append('/path/to/python/header/of/Spectrum/library')
from pyspcm import *
from spcm_tools import *
```

Functions:
- [awg_name()](#awg_name)<br/>
- [awg_start()](#awg_start)<br/>
- [awg_stop()](#awg_stop)<br/>
- [awg_pulse(*kargs)](#awg_pulsekargs)<br/>
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
- [awg_pulse_list()](#awg_pulse_list)<br/>

### awg_name()
```python3
awg_name()
Arguments: none; Output: string.
```
The function returns device name.
### awg_start()
```python3
awg_start()
Arguments: none; Output: none.
Examples: awg_start() runs the AWG card.
```
This function writes all the setting modified by other functions to the AWG card and runs it. The function should be called only without arguments. The default settings (if no other function was called) are the following: Sample clock is 1250 MHz; Clock mode is 'Internal'; Reference clock is 100 MHz; Card mode is 'Single'; Trigger channel is 'External'; Trigger mode is 'Positive'; Loop is infinity; Trigger delay is 0; Enabled channels is CH0 and CH1; Amplitude of CH0 is '600 mV'; Amplitude of CH1 is '533 mV'; Number of segments is 1; Card memory size is 64 samples; Buffer is empty.<br/>
### awg_stop()
```python3
awg_stop()
Arguments: none; Output: none.
Example: awg_stop() stops the AWG card.
```
This function stops the AWG card and should be called only without arguments. The function should always be called at the end of an experimental script.<br/>
### awg_pulse(*kargs)
```python3
awg_pulse(*kagrs)
Arguments:
name = 'P0' specifies a name of the pulse
channel = 'CH0' specifies a channel string (['CH0','CH1'])
func = 'SINE' specifies a type of the function for a pulse (['SINE','GAUSS','SINC'])
frequency = '200 MHz' specifies a frequency of the pulse (['1-280 MHz'])
phase = 0 specifies a phase of the pulse (in radians)
length = '16 ns' specifies a pulse length (['ns','us','ms']);
sigma = '16 ns' specifies a sigma value for GAUSS pulses (['ns','us','ms'])
Output: none.
Example: awg_pulse(name = 'P0', channel = 'CH0', func = 'SINE', frequency =
'200 MHz', phase = pi/2, length = '40 ns', sigma = '16 ns') sets the 40 ns length
200 MHz sine pulse with pi/2 phase.
```
The function sets a pulse with specified parameters. The AWG card buffer will be filled according to key arguments of the awg_pulse() function. The default argument is the following: 
name = 'P0', channel = 'CH0', func = 'SINE', frequency = '200 MHz', phase = 0, length = '16 ns', sigma = '16 ns'.
A channel should be one of the following ['CH0','CH1']. The frequency should be in MHz, the minimum value is 1 MHz, maximum is 280 MHz. The scaling factor for length and sigma key arguments should be one of the following ['ns','us','ms']. The minimum available length and sigma of the pulse is 0 ns. The maximum available length and sigma of the pulse is 1900 ns. The available functions are ['SINE','GAUSS','SINC']. For 'SINE' function parameter sigma has no meaning. For 'GAUSS' function parameter sigma is a sigma of Gaussian. For 'SINC' function a combination of parameters length and sigma specifies the width of the SINC pulse, i.e. length = '40 ns' and sigma = '10 ns' means that SINC pulse will be from -4pi to +4pi.
### awg_number_of_segments(*segments)
```python3
awg_number_of_segments(*segments)
Arguments: segments = integer (1-200); Output: integer.
Example: awg_number_of_segments(2) sets the number of segments to 2.
```
This function queries or sets the number of segments for ['Multi"](#awg_card_modemode) card mode. In order to set the number of segments higher than 1, the AWG card should be in ['Multi"](#awg_card_modemode) mode. If there is no argument the function will return the current number of segments. If there is an argument the specified number of segmetns will be set. The maximum available number of segments is 200. Default value is 1.<br/>
### awg_channel(*channel)
```python3
awg_channel(*channel)
Arguments: channel = string (['CH0','CH1']); Output: string.
Example: awg_channel('CH0', 'CH1') enabled output from CH0 and CH1.
```
This function enables output from the specified channel or query enabled channels. If there is no argument the function will return the currently enabled channels. If there is an argument the output from the specified channel will be enabled. The channel should be one of the following: ['CH0','CH1']. Default option is when both channels are enabled.<br/>
### awg_sample_rate(*s_rate)
```python3
awg_sample_rate(*s_rate)
Arguments: s_rate = integer (50-1250 MHz); Output: integer.
Example: awg_sample_rate('1250') sets the AWG card sample rate to 1250 MHz.
```
This function queries or sets the AWG card sample rate (in MHz). If there is no argument the function will return the current sample rate. If there is an argument the specified sample rate will be set. The minimum available sample rate is 50 MHz. The maximum available sample rate is 1250 MHz. Default value is 1250 MHz.<br/>
### awg_clock_mode(*mode)
```python3
awg_clock_mode(*mode)
Arguments: mode = string (['Internal','External']); Output: string.
Example: awg_clock_mode(*mode) sets the AWG card clock mode.
```
This function queries or sets the AWG card clock mode. If there is no argument the function will return the current clock mode setting. If there is an argument the specified clock mode will be set. The clock mode should be one of the following: ['Internal','External']. The internal sampling clock is generated in default mode by a programmable high precision quartz. The external clock input of the M3i/M4i series is fed through a PLL to the clock system. Therefore the input will act as a reference clock input thus allowing to either use a copy of the external clock or to generate any sampling clock within the allowed range from the reference clock. Due to the fact that the driver needs to know the external fed in frequency for an exact calculation of the sampling rate the reference clock should be set by the [awg_reference_clock()](#awg_reference_clockclock) function. Default setting is 'Internal'.<br/>
### awg_reference_clock(*ref_clock)
```python3
awg_reference_clock(*ref_clock)
Arguments: ref_clock = integer (10-1000 MHz); Output: integer.
Example: awg_reference_clock(100) sets the AWG card reference clock to 100 MHz.
```
This function queries or sets the AWG card reference clock (in MHz) for 'External' mode of the [awg_clock_mode(*mode)](#awg_clock_modemode) function. If there is no argument the function will return the current reference clock. If there is an argument the specified reference clock will be set. The minimum available reference clock is 10 MHz. The maximum available reference clock is 1000 MHz. Default value is 100 MHz.<br/>
### awg_card_mode(*mode)
```python3
awg_card_mode(*mode)
Arguments: mode = string (['Single','Multi']); Output: string.
Example: awg_card_mode('Multi') sets the 'Multi' card mode.
```
This function queries or sets the AWG card mode. If there is no argument the function will return the current сard mode setting. If there is an argument the specified card mode will be set. The card mode should be one of the following: ['Single','Multi']. In the 'Single' mode a data from on-board memory will be replayed on every detected trigger event. The number of replays can be programmed by [loops](#awg_looploop). In the 'Multi' mode every detected trigger event replays one data block (segment). Segmented memory is available only in 'External' trigger [mode](#awg_trigger_modemode). Default setting is 'Single'.<br/>
### awg_trigger_channel(*channel)
```python3
awg_trigger_channel(*channel)
Arguments: channel = string (['Software','External']); Output: string.
Example: awg_trigger_channel('Software') sets the 'Software' trigger.
```
This function queries or sets the AWG card trigger channel. If there is no argument the function will return the current trigger channel. If there is an argument the specified channel will be used as trigger. The channel should be one of the following: ['Software','External']. Trigger channel 'External' corresponds to 'Trg0' channel of the AWG card. Default setting is 'External'.<br/>
### awg_trigger_mode(*mode)
```python3
awg_trigger_mode(*mode)
Arguments: mode = string (['Positive','Negative','High','Low']); Output: string.
Example: awg_trigger_mode('Positive') sets the trigger detection for positive edges.
```
This function queries or sets the AWG card trigger mode. If there is no argument the function will return the current trigger mode. If there is an argument the specified trigger mode will be set. The trigger mode should be one of the following: ['Positive','Negative','High','Low']. Mode 'Positive' corresponds to trigger detection for positive edges (crossing level 0 from below to above). 'Negative' to trigger detection for negative edges (crossing level 0 from above to below). 'High' to trigger detection for HIGH levels (signal above level 0). 'Low' to trigger detection for LOW levels (signal below level 0). Default setting is 'Positive'.<br/>
### awg_loop(*loop)
```python3
awg_loop(*loop)
Arguments: loop = integer (0-100000); Output: integer.
Example: awg_loop(0) sets an infinite number of loops.
```
This function queries or sets the number of loops for ['Multi"](#awg_card_modemode) or ['Single"](#awg_card_modemode) card mode. If there is no argument the function will return the current number of loops. If there is an argument the specified number of loops will be set. The maximum available number of loops is 100000. A setting '0' means an infinite number of loops. Default value is 0.<br/>
### awg_trigger_delay(*delay)
```python3
awg_trigger_delay(*delay)
Arguments: delay = value + dimension (['ms','us','ns']); Output: string.
Example: awg_trigger_delay('51.2 ns') sets the trigger delay to 51.2 ns.
```
This function queries or sets the AWG card trigger delay. If there is no argument the function will return the current trigger delay. If there is an argument the specified trigger delay will be set. The delay step is 32 sample clock. If an input is not dividable by 32 sample clock the delay will be rounded and a warning message will be printed. Default value is '0 ns'.<br/>
### awg_amplitude(*amplitude)
```python3
awg_amplitude(*amplitude)
Arguments: amplitude = channel ['CH0','CH1'] + value (in mV); Output: string.
Example: awg_amplitude('CH0', '600', 'CH1', '600') sets the amplitude of CH0 to 600 mV
 and the amplitude of CH1 to 600 mV.
```
This function queries or sets the amplitude of the specified channels (in mV). If there is one argument the function will return the amplitude of the specified channel. If there are two arguments the specified amplitude (in mV) will be set for specified channel. The channel should be one of the following: ['CH0','CH1']. The minimum available amplitude is 80 mV. The maximum available amplitude is 2500 mV. Default amplitudes are 600 and 533 mV for 'CH0' and 'CH1', respectively.<br/>
### awg_pulse_list()
```python3
awg_pulse_list()
Arguments: none; Output: string.
Example: awg_pulse_list() returns the pulse sequence in a form of array.
```
This function can be called only without arguments and it returns the declared pulse sequence as an array.