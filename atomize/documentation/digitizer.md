---
title: Digitizers
nav_order: 23
layout: page
permlink: /functions/digitizer/
parent: Documentation
---

### Devices
- Spectrum M4I **4450 X8**; Tested 08/2021
- Spectrum M4I **2211 X8**; Tested 01/2023
The original [library](https://spectrum-instrumentation.com/en/m4i4450-x8) was written by Spectrum. The library header files (pyspcm.py, spcm_tools.py) should be added to the path directly in the module file: 
```python
sys.path.append('/path/to/python/header/of/Spectrum/library')
from pyspcm import *
from spcm_tools import *
```
- [Insys FM214x3GDA](https://www.insys.ru/mezzanine/fm214x3gda) as ADC; Tested 03/2025
The Insys device is available via ctypes. The original library can be found [here](https://github.com/Anatoly1010/Atomize_ITC/tree/master/libs).
- L card L-502 as ADC; Tested 03/2022
The L card device is available via ctypes. The original library can be found [here](https://www.lcard.ru/products/boards/l-502?qt-ltab=6#qt-ltab). The path to the installed library should be provided directly in the device module file.

---

### Functions
- [digitizer_name()](#digitizer_name)<br/>
- [digitizer_setup()](#digitizer_setup)<br/>
- [digitizer_get_curve()](#digitizer_get_curve)<br/>
- [digitizer_get_curve(integral = True)](#digitizer_get_curveintegral--true)<br/>
- [digitizer_get_curve(points, phases, integral = False, current_scan = 1, total_scan = 1)](#digitizer_get_curvepoints-phases-integral--false-current_scan--1-total_scan--1)<br/>
- [digitizer_close()](#digitizer_close)<br/>
- [digitizer_stop()](#digitizer_stop)<br/>
- [digitizer_number_of_points(\*points)](#digitizer_number_of_pointspoints)<br/>
- [digitizer_posttrigger(\*post_points)](#digitizer_posttriggerpost_points)<br/>
- [digitizer_channel(\*channel)](#digitizer_channelchannel)<br/>
- [digitizer_sample_rate(\*s_rate)](#digitizer_sample_rates_rate)<br/>
- [digitizer_clock_mode(\*mode)](#digitizer_clock_modemode)<br/>
- [digitizer_reference_clock(\*ref_clock)](#digitizer_reference_clockref_clock)<br/>
- [digitizer_card_mode(\*mode)](#digitizer_card_modemode)<br/>
- [digitizer_trigger_channel(\*ch)](#digitizer_trigger_channelch)<br/>
- [digitizer_trigger_mode(\*mode)](#digitizer_trigger_modemode)<br/>
- [digitizer_number_of_averages(\*averages)](#digitizer_number_of_averagesaverages)<br/>
- [digitizer_trigger_delay(\*delay)](#digitizer_trigger_delaydelay)<br/>
- [digitizer_input_mode(\*mode)](#digitizer_input_modemode)<br/>
- [digitizer_amplitude(\*ampl)](#digitizer_amplitudeampl)<br/>
- [digitizer_offset(\*offset)](#digitizer_offsetoffset)<br/>
- [digitizer_coupling(\*coupling)](#digitizer_couplingcoupling)<br/>
- [digitizer_impedance(\*impedance)](#digitizer_impedanceimpedance)<br/>
- [digitizer_decimation(\*dec)](#digitizer_decimationdec)<br/>
- [digitizer_flow(\*flow)](#digitizer_flowflow)<br/>
- [digitizer_read_settings()](#digitizer_read_settings)<br/>
- [digitizer_window()](#digitizer_window)<br/>
- [digitizer_window_points()](#digitizer_window_points)<br/>

---

### digitizer_name()
```python
digitizer_name() -> str
```
This function returns device name.<br>

---

### digitizer_setup()
```python
digitizer_setup() -> none
```
```
Example: digitizer_setup() writes all the settings into the digitizer.
```
This function writes all the settings modified by other functions to the digitizer. The function should be called only without arguments. One must initialize the settings before calling [digitizer_get_curve()](#digitizer_get_curve).<br/>
The default settings (if no other function was called) are the following: Sample clock is 500 MHz (M4I 4450 X8) or 1250 MHz (M4I 2211 X8); Clock mode is 'Internal'; Reference clock is 100 MHz; Card mode is 'Single'; Trigger channel is 'External'; Trigger mode is 'Positive'; Number of averages is 2; Trigger delay is 0; Enabled channels are CH0 and CH1; Input mode is 'HF' (M4I 4450 X8); Coupling of CH0 and CH1 is 'DC'; Impedance of CH0 and CH1 is '50'; Horizontal offset of CH0 and CH1 is 0%; Range of CH0 is '500 mV'; Range of CH1 is '500 mV'; Number of points is 128 (M4I 4450 X8) or 256 (M4I 2211 X8); Posttrigger points is 64.<br/>
This function is not available for Insys FM214x3GDA. This is done by [pulser_open()](/atomize_docs/pages/functions/pulse_programmer#pulser_open) function.<br>

---

### digitizer_get_curve()
```python
digitizer_get_curve() -> numpy.array, numpy.array
digitizer_get_curve() -> numpy.array, numpy.array, numpy.array
```
```
Example: digitizer_get_curve() runs acquisition and returns the data.
```
This function runs acquisition and returns the data obtained. If two channels are enabled by the function [digitizer_channel()](#digitizer_channelchannel) the output of the function is three numpy arrays (xs, data_ch0, data_ch1). If one channel is enabled the output of the function is two numpy array (xs, data_ch0). The xs array is returned in s, data arrays are returned in V. The function should be called only without arguments.<br/>
In the case of Insys FM214x3GDA one should use the modification of this function [digitizer_get_curve(points, phases, ...)](#digitizer_get_curvepoints-phases-integral--false-current_scan--1-total_scan--1).<br>

---

### digitizer_get_curve(integral = True)
```python
digitizer_get_curve(integral = [True, False]) -> float
digitizer_get_curve(integral = True) -> float, float
```
```
Example: digitizer_get_curve(integral = True) runs acquisition and returns the integrated data.
```
This function runs acquisition and returns the data, integrated over a window in the oscillogram, indicated by the [digitizer_window](#digitizer_window) function. If two channels are enabled by the function [digitizer_channel()](#digitizer_channelchannel) the output of the function is two numbers (integral_ch0, integral_ch1). If one channel is enabled the output of the function is one number (integral_ch0). The integral is returned in volt-seconds. The default option is False.<br/>In the case of Insys FM214x3GDA one should use the modification of this function [digitizer_get_curve(points, phases, ...)](#digitizer_get_curvepoints-phases-integral--false-current_scan--1-total_scan--1).<br>

---

### digitizer_get_curve(points, phases, integral = False, current_scan = 1, total_scan = 1)
```python
digitizer_get_curve(points: int, phases: int, 
	integral = False, current_scan = 1, total_scan = 1) -> numpy.array, numpy.array
```
```
Example: digitizer_get_curve(100, 2, integral = False, current_scan = 1, total_scan = 1)
runs acquisition and returns the phase cylced data.
```
This function starts the data acquisition and [phase cycling](/atomize_docs/pages/functions/pulse_programmer#pulser_acquisition_cycle) the data. The argument 'points' indicates the total number of points in the pulse experiment and the argument 'phases' corresponds to the total number of phases in the pulse experiment. The data will be phase cycled according to the phase list given in the [DETECTION pulse](/atomize_docs/pages/functions/pulse_programmer#pulser_pulsekargs). The details of phase cycling are given in the function [pulser_acquisition_cycle()](/atomize_docs/pages/functions/pulse_programmer#pulser_acquisition_cycle). A keyword 'integral' allows integrating the data over a given [window](#digitizer_read_settings). The keywords 'current_scan' and 'total_scan' indicate the current and total number of repetitive scans in the experiment to maximize the efficiency of the Insys FM214x3GDA. The value of the keyword 'current_scan' should increase during the experiment.<br>

---

### digitizer_close()
```python
digitizer_close() -> none
```
```
Example: digitizer_close() closes the digitizer driver.
```
This function closes the digitizer driver and should be called only without arguments. The function should always be called at the end of an experimental script.<br/>
This function is not available for Insys FM214x3GDA. This is done with [pulser_close()](/atomize_docs/pages/functions/pulse_programmer#pulser_close).<br>

---

### digitizer_stop()
```python
digitizer_stop() -> none
```
```
Example: digitizer_stop() stops the digitizer.
```
This function stops the digitizer and should be called only without arguments. The function should always be called before redefining digitizer settings by the [digitizer_setup()](#digitizer_setup) function.<br/>
This function is not available for Insys FM214x3GDA, L card L-502. There is no need to stop these ADC.<br>

---

### digitizer_number_of_points(\*points)
```python
digitizer_number_of_points(points: int) -> none
digitizer_number_of_points() -> int
```
```
Example: digitizer_number_of_points(128) sets the number of points to 128.
```
This function queries or sets the number of points in samples in the returned oscillogram. The number of points should be divisible by 16 samples (M4I 4450 X8) or by 32 samples (M4I 2211 X8), the minimum available value is 32 samples (M4I 4450 X8) or 64 samples (M4I 2211 X8). If there is no setting fitting the argument the nearest available value is used and warning is printed. Default value is 128 (M4I 4450 X8) or 256 (M4I 2211 X8). The difference between number of points and [posttrigger points](#digitizer_posttrigger) should be less than 8000. If it is not the case the nearest available number of points is used and warning is printed.<br/>
This function is not available for Insys FM214x3GDA. The number of points is controlled by the trigger pulse length.<br>

---

### digitizer_posttrigger(\*post_points)
```python
digitizer_posttrigger(post_points: int) -> none
digitizer_posttrigger() -> int
```
```
Example: digitizer_posttrigger(64) sets the number of posttrigger points to 64.
```
This function queries or sets the number of posttriger (horizontal offset) points in samples in the returned oscillogram. The number of posttriger points should be divisible by 16 samples (M4I 4450 X8) or by 32 samples (M4I 2211 X8), the minimum available value is 16 samples (M4I 4450 X8) or 32 samples (M4I 2211 X8). In the ['Average'](#digitizer_card_modemode) card mode, the maximum available value is [number of points](#digitizer_number_of_pointspoints) in the oscillogram minus 16 samples (M4I 4450 X8) or minus 32 samples (M4I 2211 X8). If there is no setting fitting the argument the nearest available value is used and warning is printed. Default value is 64. The difference between [number of points](#digitizer_number_of_pointspoints) and posttrigger points should be less than 8000. If it is not the case the nearest available value of posttrigger points is used and warning is printed.<br/>
This function is not available for Insys FM214x3GDA, L card L-502.<br>

---

### digitizer_channel(\*channel)
```python
digitizer_channel(channel: ['CH0','CH1']) -> none
digitizer_channel() -> str
```
```
Example: digitizer_channel('CH0', 'CH1') enables CH0 and CH1.
```
This function enables the specified channel or queries enabled channels. If there is no argument the function will return the currently enabled channels. If there is an argument the output from the specified channel will be enabled.<br/>
The channel should be one of the following: ['CH0','CH1']. Default option is when both channels are enabled.<br/>
This function is not available for Insys FM214x3GDA, L card L-502.<br>

---

### digitizer_sample_rate(\*s_rate)
```python
digitizer_sample_rate(sample_rate: float) -> none
digitizer_sample_rate() -> float
```
```
Example: digitizer_sample_rate('500') sets the digitizer sample rate to 500 MHz.
```
This function queries or sets the digitizer sample rate (in MHz). If there is no argument the function will return the current sample rate. If there is an argument the specified sample rate will be set. The minimum available sample rate is 1.907 kHz (M4I 4450 X8) or 9.536 kHz (M4I 2211 X8). The maximum available sample rate is 500 MHz (M4I 4450 X8) or 1250 MHz (M4I 2211 X8).<br/>
The available sample rate should be from the following array: [500, 250, 125, ..., 0.001907] for M4I 4450 X8 or [1250, 625, 312.5, ..., 0.009536] for M4I 2211 X8. If there is no setting fitting the argument the nearest available value is used and warning is printed. Default value is 500 MHz (M4I 4450 X8) or 1250 MHz (M4I 2211 X8).<br/>
This function only returns the current sample rate for Insys FM214x3GDA. See also [digitizer_decimation()](#digitizer_decimation).<br>
This function is not available for L card L-502.<br>

---

### digitizer_clock_mode(\*mode)
```python
digitizer_clock_mode(mode: ['Internal','External']) -> none
digitizer_clock_mode() -> str
```
```
Example: digitizer_clock_mode('Internal') sets the Internal clock mode.
```
This function queries or sets the digitizer clock mode. If there is no argument the function will return the current clock mode setting. If there is an argument the specified clock mode will be set.<br/>
The clock mode should be one of the following: ['Internal','External'].<br/>
According to the documentation, the internal sampling clock is generated in default mode by a programmable high precision quartz. The external clock input of the M3i/M4i series is fed through a PLL to the clock system. Therefore the input will act as a reference clock input thus allowing to either use a copy of the external clock or to generate any sampling clock within the allowed range from the reference clock. Due to the fact that the driver needs to know the external fed in frequency for an exact calculation of the sampling rate the reference clock should be set by the [digitizer_reference_clock()](#digitizer_reference_clockclock) function. Default setting is 'Internal'.<br/>
This function is not available for Insys FM214x3GDA.<br>

---

### digitizer_reference_clock(\*ref_clock)
```python
digitizer_reference_clock(ref_clock: int) -> none
digitizer_reference_clock() -> int
```
```
Example: digitizer_reference_clock(100) sets the digitizer reference clock to 100 MHz.
```
This function queries or sets the digitizer reference clock (in MHz) for 'External' mode of the [digitizer_clock_mode()](#digitizer_clock_modemode) function. If there is no argument the function will return the current reference clock. If there is an argument the specified reference clock will be set.<br/>
The minimum available reference clock is 10 MHz. The maximum available reference clock is 100 MHz. Default value is 100 MHz.<br/>
This function is not available for Insys FM214x3GDA.<br>

---

### digitizer_card_mode(\*mode)
```python
digitizer_card_mode(mode: ['Single','Average']) -> none
digitizer_card_mode() -> str
```
```
Example: digitizer_card_mode('Single') sets the Single mode of the digitizer.
```
This function queries or sets the digitizer mode. If there is no argument the function will return the current digitizer mode. If there is an argument the specified mode will be set.<br/>
The mode should be one of the following: ['Single','Average'].<br/>
According to the documentation, in the 'Single' mode data acquisition is carried out to on-board memory for one single trigger event. In 'Average' (Multi) mode the memory is segmented and with each trigger condition one segment is acquired. After that the data is transfer to the PC memory and [averaged](#digitizer_get_curve) or [averaged and integrated](#digitizer_get_curveintergal-false). The number of segments to acquire can be set by the [digitizer_number_of_averages()](#digitizer_number_of_averagesaverages) function. Default setting is 'Single'.<br/>
This function is not available for Insys FM214x3GDA, L card L-502.<br>

---

### digitizer_trigger_channel(\*ch)
```python
digitizer_trigger_channel(channel: ['Software','External']) -> none
digitizer_trigger_channel() -> str
```
```
Example: digitizer_trigger_channel('Software') sets the 'Software' trigger.
```
This function queries or sets the digitizer trigger channel. If there is no argument the function will return the current trigger channel. If there is an argument the specified channel will be used as trigger.<br/>
The channel should be one of the following: ['Software','External']. Trigger channel 'External' corresponds to 'Trg0' channel of the digitizer. Default setting is 'External'.<br/>
This function is not available for Insys FM214x3GDA, L card L-502.<br>

---

### digitizer_trigger_mode(\*mode)
```python
digitizer_trigger_mode(mode: ['Positive','Negative','High','Low']) -> none
digitizer_trigger_mode() -> str
```
```
Example: digitizer_trigger_mode('Positive') sets the trigger detection for positive edges.
```
This function queries or sets the digitizer trigger mode. If there is no argument the function will return the current trigger mode. If there is an argument the specified trigger mode will be set.<br/>
The trigger mode should be one of the following: ['Positive','Negative','High','Low']. Mode 'Positive' corresponds to trigger detection for positive edges (crossing level 0 from below to above). 'Negative' to trigger detection for negative edges (crossing level 0 from above to below). 'High' to trigger detection for HIGH levels (signal above level 0). 'Low' to trigger detection for LOW levels (signal below level 0). Default setting is 'Positive'.<br/>
This function is not available for Insys FM214x3GDA, L card L-502.<br>

---

### digitizer_number_of_averages(\*averages)
```python
digitizer_number_of_averages(averages: int) -> none
digitizer_number_of_averages() -> int
```
```
Example: digitizer_number_of_averages(2) sets the number of averages to 2.
```
This function queries or sets the number of averages for ['Average'](#digitizer_card_modemode) card mode. If there is no argument the function will return the current number of averages. If there is an argument the specified number of averages will be set.<br/>
The maximum available number of averages is 10000. If a very large number of [points](#digitizer_number_of_pointspoints) are set, the maximum available number of averages may be limited by the digitizer memory. This limit is 1 Gs. Default value is 2.<br>
This function is not available for L card L-502.<br>

---

### digitizer_trigger_delay(\*delay)
```python
digitizer_trigger_delay(delay: str) -> none
digitizer_trigger_delay() -> str
```
```
Example: digitizer_trigger_delay('32 ns') sets the trigger delay to 32 ns.
```
This function queries or sets the digitizer trigger delay. If there is no argument the function will return the current trigger delay. If there is an argument the specified trigger delay will be set. The delay step is 16 samples (M4I 4450 X8) or 32 samples (M4I 2211 X8). If an input is not divisible by 16 samples (M4I 4450 X8) or by 32 samples (M4I 2211 X8) the delay will be rounded and a warning message will be printed. Default value is '0 ns'.<br/>
This function is not available for Insys FM214x3GDA, L card L-502.<br>

---

### digitizer_input_mode(\*mode)
```python
digitizer_input_mode(mode: ['HF','Buffered']) -> none
digitizer_input_mode() -> str
```
```
Example: digitizer_input_mode('HF') sets the HF input mode.
```
This function queries or sets the input mode for the channels of the digitizer. If there is no argument the function will return the current input mode. If there is an argument the specified input mode will be set.<br/>
The input mode should be one of the following: ['HF','Buffered']. The input mode will be used for both channels. According to the documentation, HF mode allows using a high frequency 50 Ohm path to have full bandwidth and best dynamic performance. Buffered mode allows using a buffered path with all features but limited bandwidth and dynamic performance. Default value is 'HF'.<br/>
This function is not available for M4I 2211 X8, Insys FM214x3GDA, and L card L-502.<br>

---

### digitizer_amplitude(\*ampl)
```python
digitizer_amplitude(amplitude: int) -> none
digitizer_amplitude() -> str
```
```
Example: digitizer_amplitude(500) sets the range of the digitizer channels to ±500 mV.
```
This function queries or sets the input ranges of the digitizer channels. If there is no argument the function will return the range of the digitizer channels. If there is an argument the specified range (in mV) will be set. The given range will be used for both channels.<br/>
In the ['Buffered' input mode](#digitizer_input_modemode) the range for M4I 4450 X8 should be one of the following: [200, 500, 1000, 2000, 5000, 10000]. In the ['HF' input mode](#digitizer_input_modemode) the range should be one of the following: [500, 1000, 2500, 5000].<br/>
For M4I 2211 X8 the range should be one of the following: [200, 500, 1000, 2500].
If there is no range setting fitting the argument the nearest available value is used and warning is printed. Default value is '500 mV'.<br/>
This function is not available for Insys FM214x3GDA, the maximum amplitude in this case of about 1500 mV.<br>
This function is not available for L card L-502.<br>

---

### digitizer_offset(\*offset)
```python
digitizer_offset(ch0: str, offset0: int) -> none
digitizer_offset(ch0: str, offset0: int, ch1: str, offset1: int) -> none
digitizer_offset() -> str, str
```
```
Example: digitizer_offset('CH0', '1', 'CH1', '50') sets the offset of the CH0 to 1% of 
the input range and the offset of the CH1 to 50% of the input range.
```
This function queries or sets the vertical offset of the digitizer channels. If there is no argument the function will return the offset of the both digitizer channels. If there is an argument the specified offset (as a percentage of the input range) will be set for the specified channel. For M4I 4450 X8 the value of the offset (range x argument) is ALWAYS substracted from the signal. The step is 1%. According to the M4I 4450 X8 documentation, no offset can be used for 1000 mV and 10000 mV range in the ['Buffered' input mode](#digitizer_input_modemode). Default value is '0' for both channels.<br/>
This function is not available for Insys FM214x3GDA,  L card L-502.<br>

---

### digitizer_coupling(\*coupling)
```python
digitizer_coupling(ch0: str, coupling0: ['AC','DC']) -> none
digitizer_coupling(ch0: str, coupling0: str, ch1: str, coupling1: str) -> none
digitizer_coupling() -> str, str
```
```
Example: digitizer_coupling('CH0', 'AC', 'CH1', 'DC') sets the coupling of the CH0 to AC
and the coupling of the CH1 to DC.
```
This function queries or sets the coupling of the digitizer channels. If there is no argument the function will return the coupling of the both digitizer channels. If there is an argument the specified coupling will be set for the specified channel.<br/>
The offset should be one of the following: ['AC','DC']. Default value is 'DC' for both channels.<br/>
This function is not available for Insys FM214x3GDA, L card L-502.<br>

---

### digitizer_impedance(\*impedance)
```python
digitizer_impedance(ch0: str, impedance0: ['1 M','50']) -> none
digitizer_impedance(ch0: str, impedance0: str, ch1: str, impedance1: str) -> none
digitizer_impedance() -> str, str
```
```
Example: digitizer_impedance('CH0', '50', 'CH1', '1 M') sets the impedance of the CH0 to 50 Ohm
and the impedance of the CH1 to 1 MOhm.
```
This function queries or sets the impedance of the digitizer channels. If there is no argument the function will return the impedance of the both digitizer channels. If there is an argument the specified impedance will be set for the specified channel.<br/>
The impedance should be one of the following: ['1 M','50']. Please note that in the [HF input mode](#digitizer_input_modemode) impedance is fixed at 50 Ohm. Default value is '50' for both channels.<br/>
This function is not available for M4I 2211 X8, Insys FM214x3GDA, and L card L-502. For these digitizers the impedance is fixed at 50 Ohm.<br>

---

### digitizer_decimation(\*dec)
```python
digitizer_decimation(decimation: int) -> none
digitizer_decimation() -> int
```
```
Example: digitizer_decimation(4) sets the decimation coefficient to 128.
```
This function queries or sets the decimation coefficient for Insys FM214x3GDA. If there is no argument the function will return the decimation coefficient of the digitizer. If there is an argument the specified decimation will be set. It can be used instead of the function [digitizer_sample_rate()](#digitizer_sample_rates_rate).<br/>
The available range is 1-4, which corresponds to 0.4 ns/point - 1.6 ns/point. This function should be called before [pulser_open()](/atomize_docs/pages/functions/pulse_programmer#pulser_open).<br>

---

### digitizer_flow(\*flow)
```python
digitizer_flow(flow = ['ADC','DIN','DAC1','DAC2','DOUT','AIN','AOUT']) -> none
```
```
Examples: digitizer_flow() reads all the settings of the digitizer.
```
This function sets or queries enabled flows of data. If there is no argument the function will return the enabled flow of data of the digitizer. If there is an argument the specified flow will be set. The available options are ['ADC', 'DIN', 'DAC1', 'DAC2', 'DOUT', 'AIN', 'AOUT']. The default option is 'ADC'. This function is available only for L card L-502.<br>

---

### digitizer_read_settings()
```python
digitizer_read_settings() -> none
```
```
Examples: digitizer_read_settings() reads all the settings of the digitizer.
```
This function reads all the settings from a special text file [digitizer.param](https://github.com/Anatoly1010/Atomize_ITC/tree/master/atomize/control_center) and writes them to the digitizer using the [digitizer_setup()](digitizer_setup) function.<br>
This function is not available for L card L-502.<br>

---

### digitizer_window()
```python
digitizer_window() -> float
```
```
Examples: digitizer_window() returns the integration window of the digitizer.
```
This function returns the integration window of the digitizer. The integration window is used in the [digitizer_get_curve()](#digitizer_get_curveintegral--true) function and is set via a special text file [digitizer.param](https://github.com/Anatoly1010/Atomize_ITC/tree/master/atomize/control_center).<br>
This function is not available for L card L-502.<br>

---

### digitizer_window_points()
```python
digitizer_window_points() -> int
```
```
Examples: digitizer_window_points() returns the number of points in the digitizer window.
```
This function returns the number of points in the digitizer window. The window is used in the [digitizer_get_curve()](#digitizer_get_curveintegral--true) function. The number of points in the window can be set as the length of the [DETECTION pulse](/atomize_docs/pages/functions/pulse_programmer#pulser_pulsekargs).<br>
This function is not available for L card L-502.<br>
