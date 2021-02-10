# List of available functions for lock-in amplifiers

Available devices:
- Stanford Research Lock-In Amplifier (GPIB, RS-232)
SR-810; SR-830; SR-850; Tested 02/2021
- Stanford Research Lock-In Amplifier (GPIB, RS-232, Ethernet)
SR-860; SR-865a; Tested 01/2021

Functions:
- [lock_in_name()](#lock_in_name)<br/>
- [lock_in_ref_frequency(*frequency)](#lock_in_ref_frequencyfrequency)<br/>
- [lock_in_phase(*degree)](#lock_in_phasedegree)<br/>
- [lock_in_time_constant(*timeconstant)](#lock_in_time_constanttimeconstant)<br/>
- [lock_in_ref_amplitude(*amplitude)](#lock_in_ref_amplitudeamplitude)<br/>
- [lock_in_get_data(*channel)](#lock_in_get_datachannel)<br/>
- [lock_in_sensitivity(*sensitivity)](#lock_in_sensitivitysensitivity)<br/>
- [lock_in_ref_mode(*mode)](#lock_in_ref_modemode)<br/>
- [lock_in_ref_slope(*mode)](#lock_in_ref_slopemode)<br/>
- [lock_in_sync_filter(*mode)](#lock_in_sync_filtermode)<br/>
- [lock_in_lp_filter(*mode)](#lock_in_lp_filtermode)<br/>
- [lock_in_harmonic(*harmonic)](#lock_in_harmonicharmonic)<br/>
- [lock_in_command(command)](#lock_in_commandcommand)<br/>
- [lock_in_query(command)](#lock_in_querycommand)<br/>

### lock_in_name()
```python3
lock_in_name()
Arguments: none; Output: string.
```
The function returns device name.
### lock_in_ref_frequency(*frequency)
```python3
lock_in_ref_frequency(*frequency)
Arguments: frequency = float; Output: float or none.
Example: lock_in_ref_frequency('100000') sets the modulation frequency to 100 kHz.
```
The function for querying or setting the modulation frequency in Hz. If called with no argument the current modulation frequency is returned. If called with an argument the modulation frequency is set. Frequency range is 4 mHz to 102 kHz (SR-810, 830, 850); 1 mHz - 500 kHz (SR-860); 1 mHz - 4 MHz (SR-865a).<br/>
For SR-860, 865a the query command, [lock_in_ref_frequency()](#lock_in_ref_frequencyfrequency), returns the internal reference frequency whenever the reference mode is either Internal, Dual, or Chop. The query returns the external frequency when operating in External mode.<br/>
### lock_in_phase(*degree)
```python3
lock_in_phase(*degree)
Arguments: degree = float; Output: float or none.
Example: lock_in_phase('100') sets the phase to 100°.
```
The function for querying or setting the phase of the lock-in in degrees. If there is no argument the function will return the current phase. If called with an argument the specified phase will be set. The phase may be programmed from -360.000 to 719.999 (SR-850), from -360.000 to 729.999 (SR-810, 830), from -360000 to 360000 (SR-860, 865a) and will be wrapped around at ±180°.<br/>
### lock_in_time_constant(*timeconstant)
```python3
lock_in_time_constant(*timeconstant)
Arguments: timeconstant = string; Output: string or none.
Example: lock_in_time_constant('100 ms') sets the time constant to 100 ms.
```
The function for querying or setting the time constant of the lock-in in ms. If there is no argument the function will return the current time constant. If there is an argument the specified time constant will be set.<br/>
Currently for SR-810, 830, 850 the specified time constant should be from the array:<br/>
[10 us, 30 us, 100 us, 300 us, 1 ms, 3 ms, 10 ms, 30 ms, 100 ms, 300 ms, 1 s, 3 s, 10 s, 30 s, 100 s, 300 s, 1 ks, 10 ks, 30 ks].<br/>
For SR-860, 865a 1 us and 3 us are also available. If there is no time constant setting fitting the argument the nearest available value is used and warning is printed.<br/>
### lock_in_ref_amplitude(*amplitude)
```python3
lock_in_ref_amplitude(*amplitude)
Arguments: amplitude = float; Output: float or none.
Example: lock_in_ref_amplitude('0.150') sets the level of the modulation frequency
to 150 mV.
```
This function queries or sets the level of the modulation frequency in V. If there is no argument the function will return the current level. If there is an argument the specified level will be set. For SR-810, 830, 850 the allowed levels are between 4 mV and 5 V. For SR-860, 865a the allowed levels are between 1 nV and 2 V. If the argument is not within this range an error message is printed and the level of 4 mV will be set. <br/>
### lock_in_get_data(*channel)
```python3
lock_in_get_data(*channel)
Arguments: channel = up to three integers (1,2,3); Output: up to three floats.
Example: lock_in_get_data('1', '2', '3') returns three float values for X, Y,
and R signals in Volts.
```
This function can be used to query measured values from the lock-in amplifier.
If no argument is specified the 'X' signal is returned. If a parameter is passed to the function the value at the corresponding channel is returned. Possible channel numbers and their meaning are the following:<br/>
SR-810, 830, 850, 860, 865a:<br/>
'1' - X signal in Volts; '2' - Y signal in Volts; '3' - R signal in Volts; '4' - Phase 'theta' of data in degrees; ['1', '2'] - X and Y signals in Volts; ['1', '2', '3'] - X, Y, and R signals in Volts.<br/>
### lock_in_sensitivity(*sensitivity)
```python3
lock_in_sensitivity(*sensitivity)
Arguments: sensitivity = string; Output: string or none.
Example: lock_in_sensitivity('10 uV') sets the sensitivity to 10 uV.
```
The function queries or sets the sensitivity of the lock-in. If there is no argument the function will return the current sensitivity as a string. If there is an argument the specified sensitivity will be set.<br/>
Currently for SR-810, 830, 850 the specified sensitivity should be from the array:<br/>
[2 nV, 5 nV, 10 nV, 20 nV, 50 nV, 100 nV, 200 nV, 500 nV, 1 uV, 2 uV, 5 uV, 10 uV, 20 uV, 50 uV, 100 uV, 200 uV, 500 uV, 2 mV, 5 mV, 10 mV, 20 mV, 50 mV, 100 mV, 200 mV, 500 mV, 1 V].<br/>
For SR-860, 865a 1 nV is also available. If there is no sensitivity setting fitting the argument the nearest available value is used and warning is printed.<br/>
### lock_in_ref_mode(*mode)
```python3
lock_in_ref_mode(*mode)
Arguments: mode = string (['Internal', 'External', 'Dual', 'Chop']); Output: string.
Example: lock_in_ref_mode('External') sets the device to external modulation mode.
```
This function queries or sets the modulation mode, i.e. if the internal modulation or an external modulation input is used. If there is no argument the function will return the current modulation mode. If there is an argument the specified modulation mode will be set. Possible modulation modes are the following:<br/>
SR-810, 830, 850: ['Internal', 'External']<br/>
SR-860, 865a: ['Internal', 'External', 'Dual', 'Chop']<br/>
### lock_in_ref_slope(*mode)
```python3
lock_in_ref_slope(*mode)
Arguments: mode = string (['Sine', 'PosTTL', 'NegTTL']); Output: string.
Example: lock_in_ref_slope('PosTTL') sets the reference trigger to TTL rising edge.
```
This function queries or sets the reference trigger when using the external reference mode. If there is no argument the function will return the current reference trigger. If there is an argument the specified reference trigger mode will be set. Note that at frequencies below 1 Hz, the a TTL reference must be used. Possible reference trigger modes are the following: ['Sine', 'PosTTL', 'NegTTL']. They correspond to sine zero crossing, TTL rising edge, TTL falling edge, respectively.<br/>
### lock_in_sync_filter(*mode)
```python3
lock_in_sync_filter(*mode)
Arguments: mode = string (['Off', 'On']); Output: string.
Example: lock_in_sync_filter('On') turns on synchronous filtering.
```
This function queries or sets the synchronous filter status. If there is no argument the function will return the current status. If there is an argument the specified status will be set. Note that synchronous filtering is turned on only if the detection frequency is less than 200 Hz. Possible synchronous filter status are the following: ['Off', 'On'].<br/>
### lock_in_lp_filter(*mode)
```python3
lock_in_lp_filter(*mode)
Arguments: mode = string (['6 dB', '12 dB', '18 dB', '24 dB']); Output: string.
Example: lock_in_lp_filter('12 dB') sets the low pass filter slope to 12 dB/oct.
```
This function queries or sets the low pass filter slope. If there is no argument the function will return the current slope. If there is an argument the specified slope will be set. Possible low pass filter slopes are the following: ['6 dB', '12 dB', '18 dB', '24 dB']. They correspond to 6 dB/oct, 12 dB/oct, 18 dB/oct, 24 dB/oct, respectively.<br/>
### lock_in_harmonic(*harmonic)
```python3
lock_in_harmonic(*harmonic)
Arguments: harmonic = integer (1-19999; 1-99); Output: integer or none.
Example: lock_in_harmonic('2') sets the detection harmonic of the second harmonic.
```
This function queries or sets the detection harmonic. The argument is an integer from 1 to 19999 (SR-810, 830, 850) or from 1 to 32767 (SR-850). The function will set the lock-in to detect at the specified harmonic of the reference frequency. The value of the detected frequency is limited by 102 kHz. If the argument used requires a detection frequency greater than 102 kHz, then the harmonic number will be set to the largest value available for which the frequency is less than 102 kHz.<br/>
For SR-860, 865a the value of the argument is limited to 1 ≤ i ≤ 99.<br/>
### lock_in_command(command)
```python3
lock_in_command(command)
Arguments: command = string; Output: none.
Example: lock_in_command('OFSL 0'). This example sets the low pass filter
slope. The parameter equals to 0 selects 6 dB/oct.
```
The function for sending an arbitrary command from a programming guide to the device in a string format. No output is expected.<br/>
### lock_in_query(command)
```python3
lock_in_query(command)
Arguments: command = string; Output: string.
Example: lock_in_command('OFSL?'). This example queries the low pass filter slope.
```
The function for sending an arbitrary command from a programming guide to the device in a string format. An output in a string format is expected.<br/>
