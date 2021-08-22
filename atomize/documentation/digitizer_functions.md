# List of available functions for digitizers

Available devices:
- Spectrum M4I 4450 X8; Tested 08/2021
The original [library](https://spectrum-instrumentation.com/en/m4i4450-x8) was written by Spectrum. The library header files (pyspcm.py, spcm_tools.py) should be added to the path directly in the module file: 
```python3
sys.path.append('/path/to/python/header/of/Spectrum/library')
from pyspcm import *
from spcm_tools import *
```

Functions:
- [digitizer_name()](#digitizer_name)<br/>
- [digitizer_setup()](#digitizer_setup)<br/>
- [digitizer_get_curve()](#digitizer_get_curve)<br/>
- [digitizer_get_curve(integral = True)](#digitizer_get_curveintegral--true)<br/>
- [digitizer_close()](#digitizer_close)<br/>
- [digitizer_stop()](#digitizer_stop)<br/>
- [digitizer_number_of_points(*points)](#digitizer_number_of_pointspoints)<br/>
- [digitizer_posttrigger(*post_points)](#digitizer_posttriggerpost_points)<br/>
- [digitizer_channel(*channel)](#digitizer_channelchannel)<br/>
- [digitizer_sample_rate(*s_rate)](#digitizer_sample_rates_rate)<br/>
- [digitizer_clock_mode(*mode)](#digitizer_clock_modemode)<br/>
- [digitizer_reference_clock(*ref_clock)](#digitizer_reference_clockref_clock)<br/>
- [digitizer_card_mode(*mode)](#digitizer_card_modemode)<br/>
- [digitizer_trigger_channel(*ch)](#digitizer_trigger_channelch)<br/>
- [digitizer_trigger_mode(*mode)](#digitizer_trigger_modemode)<br/>
- [digitizer_number_of_averages(*averages)](#digitizer_number_of_averagesaverages)<br/>
- [digitizer_trigger_delay(*delay)](#digitizer_trigger_delaydelay)<br/>
- [digitizer_input_mode(*mode)](#digitizer_input_modemode)<br/>
- [digitizer_amplitude(*ampl)](#digitizer_amplitudeampl)<br/>
- [digitizer_offset(*offset)](#digitizer_offsetoffset)<br/>
- [digitizer_coupling(*coupling)](#digitizer_couplingcoupling)<br/>
- [digitizer_impedance(*impedance)](#digitizer_impedanceimpedance)<br/>

### digitizer_name()
```python3
digitizer_name()
Arguments: none; Output: string.
```
The function returns device name.
### digitizer_setup()
```python3
digitizer_setup()
Arguments: none; Output: none.
Examples: digitizer_setup() writes all the settings into the digitizer.
```
This function writes all the settings modified by other functions to the digitizer. The function should be called only without arguments. One must initialize the settings before calling [digitizer_get_curve()](#digitizer_get_curve). The default settings (if no other function was called) are the following: Sample clock is 500 MHz; Clock mode is 'Internal'; Reference clock is 100 MHz; Card mode is 'Single'; Trigger channel is 'External'; Trigger mode is 'Positive'; Number of averages is 2; Trigger delay is 0; Enabled channels are CH0 and CH1; Input mode is 'HF'; Coupling of CH0 and CH1 is 'DC'; Impedance of CH0 and CH1 is '50'; Horizontal offset of CH0 and CH1 is 0%; Range of CH0 is '500 mV'; Range of CH1 is '500 mV'; Number of points is 128; Posttriger points is 64.<br/>
### digitizer_get_curve()
```python3
digitizer_get_curve()
Arguments: none; Output: xs, data_ch0 or xs, data_ch0, data_ch1.
Examples: digitizer_get_curve() runs acquisition and returns the data.
```
This function runs acquisition and returns the data obtained. If two channels are enabled by the function [digitizer_channel()](#digitizer_channelchannel) the output of the function is three numpy arrays (xs, data_ch0, data_ch1). If one channel is enabled the output of the function is two numpy array (xs, data_ch0). The xs array is returned in s, data arrays are returned in V. The function should be called only without arguments.<br/>
### digitizer_get_curve(integral = True)
```python3
digitizer_get_curve(integral = True)
Arguments: none; Output: xs, integral_ch0 or xs, integral_ch0, integral_ch1.
Examples: digitizer_get_curve(integral = True) runs acquisition and returns the integrated data.
```
This function runs acquisition and returns the data, integrated over all points in the oscillogram. If two channels are enabled by the function [digitizer_channel()](#digitizer_channelchannel) the output of the function is two numbers (integral_ch0, integral_ch1). If one channel is enabled the output of the function is one number (integral_ch0). The integral is returned in V*s.
### digitizer_close()
```python3
digitizer_close()
Arguments: none; Output: none.
Example: digitizer_close() closes the digitizer driver.
```
This function closes the digitizer driver and should be called only without arguments. The function should always be called at the end of an experimental script.<br/>
### digitizer_stop()
```python3
digitizer_stop()
Arguments: none; Output: none.
Example: digitizer_stop() stops the digitizer.
```
This function stops the digitizer and should be called only without arguments. The function should always be called before redefining digitizer settings by the [digitizer_setup()](#digitizer_setup) function.<br/>
###digitizer_number_of_points(*points)
```python3
digitizer_number_of_points(*points)
Arguments: points = integer (divisible by 16); Output: integer.
Example: digitizer_number_of_points(128) sets the number of points to 128.
```
This function queries or sets the number of points in samples in the returned oscillogram. The number of points should be divisible by 16 samples, the minimum available value is 32 samples. If there is no setting fitting the argument the nearest available value is used and warning is printed. Default value is 128.<br/>
###digitizer_posttrigger(*post_points)
```python3
digitizer_posttrigger(*post_points)
Arguments: post_points = integer (divisible by 16); Output: integer.
Example: digitizer_posttrigger(64) sets the number of posttrigger points to 64.
```
This function queries or sets the number of posttriger (horizontal offset) points in samples in the returned oscillogram. The number of posttriger points should be divisible by 16 samples, the minimum available value is 16 samples. In the ['Average'](#digitizer_card_modemode) card mode, the maximum available value is [the number of points](#digitizer_number_of_pointspoints) in the oscillogram minus 16 samples. If there is no setting fitting the argument the nearest available value is used and warning is printed. Default value is 64.<br/>
### digitizer_channel(*channel)
```python3
digitizer_channel(*channel)
Arguments: channel = string (['CH0','CH1']); Output: string.
Example: digitizer_channel('CH0', 'CH1') enables CH0 and CH1.
```
This function enables the specified channel or queries enabled channels. If there is no argument the function will return the currently enabled channels. If there is an argument the output from the specified channel will be enabled. The channel should be one of the following: ['CH0','CH1']. Default option is when both channels are enabled.<br/>
### digitizer_sample_rate(*s_rate)
```python3
digitizer_sample_rate(*s_rate)
Arguments: s_rate = integer (in MHz); Output: integer.
Example: digitizer_sample_rate('500') sets the digitizer sample rate to 500 MHz.
```
This function queries or sets the digitizer sample rate (in MHz). If there is no argument the function will return the current sample rate. If there is an argument the specified sample rate will be set. The minimum available sample rate is 1.907 kHz. The maximum available sample rate is 500 MHz. The available sample rate should be from the following array: [500, 250, 125, ..., 0.001907]. If there is no setting fitting the argument the nearest available value is used and warning is printed. Default value is 500 MHz.<br/>
### digitizer_clock_mode(*mode)
```python3
digitizer_clock_mode(*mode)
Arguments: mode = string (['Internal','External']); Output: string.
Example: digitizer_clock_mode(*mode) sets the digitizer clock mode.
```
This function queries or sets the digitizer clock mode. If there is no argument the function will return the current clock mode setting. If there is an argument the specified clock mode will be set. The clock mode should be one of the following: ['Internal','External']. According to the documentation, the internal sampling clock is generated in default mode by a programmable high precision quartz. The external clock input of the M3i/M4i series is fed through a PLL to the clock system. Therefore the input will act as a reference clock input thus allowing to either use a copy of the external clock or to generate any sampling clock within the allowed range from the reference clock. Due to the fact that the driver needs to know the external fed in frequency for an exact calculation of the sampling rate the reference clock should be set by the [digitizer_reference_clock()](#digitizer_reference_clockclock) function. Default setting is 'Internal'.<br/>
### digitizer_reference_clock(*ref_clock)
```python3
digitizer_reference_clock(*ref_clock)
Arguments: ref_clock = integer (10-1000 MHz); Output: integer.
Example: digitizer_reference_clock(100) sets the digitizer reference clock to 100 MHz.
```
This function queries or sets the digitizer reference clock (in MHz) for 'External' mode of the [digitizer_clock_mode()](#digitizer_clock_modemode) function. If there is no argument the function will return the current reference clock. If there is an argument the specified reference clock will be set. The minimum available reference clock is 10 MHz. The maximum available reference clock is 100 MHz. Default value is 100 MHz.<br/>
### digitizer_card_mode(*mode)
```python3
digitizer_card_mode(*mode)
Arguments: mode = string (['Single','Average']); Output: string.
Example: digitizer_card_mode('Single') sets the Single mode of the digitizer.
```
This function queries or sets the digitizer mode. If there is no argument the function will return the current digitizer mode. If there is an argument the specified mode will be set. The mode should be one of the following: ['Single','Average']. According to the documentation, in the 'Single' mode data acquisition is carried out to on-board memory for one single trigger event. In 'Average' (Multi) mode the memory is segmented and with each trigger condition one segment is acquired. After that the data is transfer to the PC memory and [averaged](#digitizer_get_curve) or [averaged and integrated](#digitizer_get_curveintergal-false). The number of segments to acquire can be set by the [digitizer_number_of_averages()](#digitizer_number_of_averagesaverages) function. Default setting is 'Single'.<br/>
### digitizer_trigger_channel(*ch)
```python3
digitizer_trigger_channel(*ch)
Arguments: channel = string (['Software','External']); Output: string.
Example: digitizer_trigger_channel('Software') sets the 'Software' trigger.
```
This function queries or sets the digitizer trigger channel. If there is no argument the function will return the current trigger channel. If there is an argument the specified channel will be used as trigger. The channel should be one of the following: ['Software','External']. Trigger channel 'External' corresponds to 'Trg0' channel of the digitizer. Default setting is 'External'.<br/>
### digitizer_trigger_mode(*mode)
```python3
digitizer_trigger_mode(*mode)
Arguments: mode = string (['Positive','Negative','High','Low']); Output: string.
Example: digitizer_trigger_mode('Positive') sets the trigger detection for positive edges.
```
This function queries or sets the digitizer trigger mode. If there is no argument the function will return the current trigger mode. If there is an argument the specified trigger mode will be set. The trigger mode should be one of the following: ['Positive','Negative','High','Low']. Mode 'Positive' corresponds to trigger detection for positive edges (crossing level 0 from below to above). 'Negative' to trigger detection for negative edges (crossing level 0 from above to below). 'High' to trigger detection for HIGH levels (signal above level 0). 'Low' to trigger detection for LOW levels (signal below level 0). Default setting is 'Positive'.<br/>
### digitizer_number_of_averages(*averages)
```python3
digitizer_number_of_averages(*averages)
Arguments: averages = integer (1-10000); Output: integer.
Example: digitizer_number_of_averages(2) sets the number of averages to 2.
```
This function queries or sets the number of averages for ['Average'](#digitizer_card_modemode) card mode. If there is no argument the function will return the current number of averages. If there is an argument the specified number of averages will be set. The maximum available number of averages is 10000. If a very large number of [points](#digitizer_number_of_pointspoints) are set, the maximum available number of averages may be limited by the digitizer memory. This limit is 1 Gs. Default value is 2.<br/>
### digitizer_trigger_delay(*delay)
```python3
digitizer_trigger_delay(*delay)
Arguments: delay = value + dimension (['ms','us','ns']); Output: string.
Example: digitizer_trigger_delay('32 ns') sets the trigger delay to 32 ns.
```
This function queries or sets the digitizer trigger delay. If there is no argument the function will return the current trigger delay. If there is an argument the specified trigger delay will be set. The delay step is 16 samples. If an input is not divisible by 16 samples the delay will be rounded and a warning message will be printed. Default value is '0 ns'.<br/>
### digitizer_input_mode(*mode)
```python3
digitizer_input_mode(*mode)
Arguments: mode = string (['HF','Buffered']); Output: string.
Example: digitizer_input_mode('HF') sets the HF input mode.
```
This function queries or sets the input mode for the channels of the digitizer. If there is no argument the function will return the current input mode. If there is an argument the specified input mode will be set. The input mode will be used for both channels. According to the documentation, HF mode allows using a high frequency 50 Ohm path to have full bandwidth and best dynamic performance. Buffered mode allows using a buffered path with all features but limited bandwidth and dynamic performance. Default value is 'HF'.<br/>
### digitizer_amplitude(*ampl)
```python3
digitizer_amplitude(*ampl)
Arguments: ampl = integer (in mV); Output: string.
Example: digitizer_amplitude(500) sets the range of the digitizer channels to ±500 mV.
```
This function queries or sets the input ranges of the digitizer channels. If there is no argument the function will return the range of the digitizer channels. If there is an argument the specified range (in mV) will be set. The given range will be used for both channels. In the ['Buffered' input mode](#digitizer_input_modemode) the range should be one of the following: [200, 500, 1000, 2000, 5000, 10000]. In the ['HF' input mode](#digitizer_input_modemode) the range should be one of the following: [500, 1000, 2500, 5000]. If there is no range setting fitting the argument the nearest available value is used and warning is printed. Default value is '500 mV'.<br/>
### digitizer_offset(*offset)
```python3
digitizer_offset(*ampl)
Arguments: offset = integer (in percentage); Output: string.
Example: digitizer_offset('CH0', '1', 'CH1', '50') sets the offset of the CH0 to 1% of 
the input range and the offset of the CH1 to 50% of the input range.
```
This function queries or sets the vertical offset of the digitizer channels. If there is no argument the function will return the offset of the both digitizer channels. If there is an argument the specified offset (as a percentage of the input range) will be set for the specified channel. The value of the offset (range * argument) is ALWAYS substracted from the signal. The step is 1%. According to the digitizer documentation, no offset can be used for 1000 mV and 10000 mV range in the ['Buffered' input mode](#digitizer_input_modemode). Default value is '0' for both channels.<br/>
### digitizer_coupling(*coupling)
```python3
digitizer_coupling(*coupling)
Arguments: coupling = string (['AC','DC']); Output: string.
Example: digitizer_coupling('CH0', 'AC', 'CH1', 'DC') sets the coupling of the CH0 to AC
and the coupling of the CH1 to DC.
```
This function queries or sets the coupling of the digitizer channels. If there is no argument the function will return the coupling of the both digitizer channels. If there is an argument the specified coupling will be set for the specified channel. The offset should be one of the following: ['AC','DC']. Default value is 'DC' for both channels.<br/>
### digitizer_impedance(*impedance)
```python3
digitizer_impedance(*impedance)
Arguments: impedance = string (['1 M','50']); Output: string.
Example: digitizer_impedance('CH0', '50', 'CH1', '1 M') sets the impedance of the CH0 to 50 Ohm
and the impedance of the CH1 to 1 MOhm.
```
This function queries or sets the impedance of the digitizer channels. If there is no argument the function will return the impedance of the both digitizer channels. If there is an argument the specified impedance will be set for the specified channel. The impedance should be one of the following: ['1 M','50']. Please note that in the [HF input mode](#digitizer_input_modemode) impedance is fixed at 50 Ohm. Default value is '50' for both channels.<br/>
