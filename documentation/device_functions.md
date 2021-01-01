# List of available functions for devices

## Temperature Controllers
### tc_name()
#### Arguments: None; Output: string(name).
The function returns device name.
### tc_read_temp(channel)
#### Arguments: channel = 'A' or 'B' (shown as ['A','B'] further); Output: float.
The function for reading temperature from specified channel. 
Note that arguments can be devices specific. A set of ['A','B'] is used for LakeShore 325, 331, 332, and 335, while for LakeShore 336, 340 a set of four channel ['A','B','C','D'] is used.
Example: tc_read_temp('A') returns the temperature of channel A in Kelvin.
### tc_set_temp(\*temp)
#### Arguments: temp = float; Output: float or none.
The function for controlling set point. If an argument is specified the function set a new temperature point. If there is no argument the function return the current set point. A loop can be specified in configuration file.
Example: tc_set_temp('100') changes the set point of the specified loop to 100 Kelvin.
### tc_heater_range(\*heater)
#### Arguments: heater = ['50W','5W','0.5W','Off']; Output: string or none. 
The function for conntrolling heater range. If an argument is specified the function set a new heater range. If there is no argument the function return the current heater range. 
Note that arguments are devices specific. Currently a set of ['50W','5W','0.5W','Off'] can be used for LakeShore 331, 332, 335, while for LakeShore 340 a set ['10W','1W','Off'] is used. For LakeShore 336 a loop 1 or 2 can be used with a set of ['50W','5W','0.5W','Off']. The loop 3 and 4 can be used only with ['On','Off'] set. For LakeShore 325 a loop 1 can be used with a set of ['25W','2.5W','Off']. The loop 2 can be used only with ['On','Off'] set. The values '50W','5W', and'0.5W' are shown as High, Medium, and Low on the device display.
Example: tc_heater_range('50W') changes the heater range to 50 W. 
### tc_heater()
#### Arguments: None; Output: array([string(heater_range), float(heater_percent)])
The function for reading the current heater value in percent.
Example: tc_heater() returns the array of the heater range and heater percent. 
### tc_command(command)
#### Arguments: string(command); Output: none.
The function for sending an arbitrary command from programming guide to the device in a string format. No output is expected.
Example: tc_command('PID 1,10,50,0'). Note that for some controller models the loop should not be specified. Check the programming guide.
### tc_query(command)
#### Arguments: string(command); Output: string(answer).
The function for sending an arbitrary command from programming guide to the device in a string format. An output in a string format is expected.
Example: tc_command('PID? 1'). Note that for some controller models the loop should not be specified. Check the programming guide.

## Lock-in amplifiers
### lock_in_name()
#### Arguments: None; Output: string(name).
The function returns device name.
### lock_in_ref_frequency(\*freq)
#### Arguments: freq = float; Output: float or none.
The function for querying or setting the modulation frequency in Hz. If called with no argument the current modulation frequency is returned. If called with an argument the modulation frequency is set.
Example: lock_in_ref_frequency('100000') sets the modulation frequency to 100 kHz.
### lock_in_phase(\*degs)
#### Arguments: phase = float; Output: float or none.
The function for querying or setting the phase of the lock-in in deg. If there is no argument the function will return the current phase. If called with an argument the specified phase will be set.
Example: lock_in_phase('100') sets the phase to 100 deg.
### lock_in_time_constant(\*tc)
#### Arguments: tc = integer; Output: integer or none.
The function for querying or setting the time constant of the lock-in in ms. If there is no argument the function will return the current time constant. If there is an argument the specified time constant will be set. Currently for SR-810 the specified time constant (given in ms) should be from the array: [0.01, 0.03, 0.1, 0.3, 1, 3, 10, 30, 100, 300, 1000, 3000, 10000, 30000, 100000, 300000]. If the time constant is not contained in the array, no change will occur and "Invalid time constant value" will be printed.
Example: lock_in_time_constant('100') sets the time constant to 100 ms.
### lock_in_ref_amplitude(\*amplitude)
#### Arguments: amplitude = float; Output: float or none.
This function queries or sets the level of the modulation frequency in mV. If there is no argument the function will return the current level. If there is an argument the specified level will be set. For the Stanford Research lock-ins (SR810, SR830) the allowed levels are between 4 mV and 5 V, if the argument is not within this range an error message is printed and the level of 4 mV will be set.
Example: lock_in_ref_amplitude('0.150') sets the level of the modulation frequency to 150 mV.
### lock_in_get_data(\*channel)
#### Arguments: \*channel = up to three integers (1,2,3); Output: up to three floats.
This function can be used to query measured values from the lock-in amplifier.
If no argument is specified the 'X' signal is returned. If a parameter is passed to the function the value at the corresponding channel is returned. Possible channel numbers and their meaning are the following:
'1' - X signal in Volts; '2' - Y signal in Volts; '3' - R signal in Volts; '4' - Phase 'theta' of data in degrees; ['1', '2'] - X and Y signals in Volts; ['1', '2', '3'] - X, Y, and R signals in Volts.
Example: lock_in_get_data('1', '2', '3') returns three float values for X, Y, and R signals in Volts.
### lock_in_sensitivity(\*sensitivity)
#### Arguments: \*sensitivity = one integer and one scaling string or two strings; Output: float or none.
The function queries or sets the sensitivity of the lock-in. If there is no argument the function will return the current sensitivity. If there is an argument the specified sensitivity will be set. Currently for SR-810 the specified sensitivity should be from the array: [2 nV, 5 nV, 10 nV, 20 nV, 50 nV, 100 nV, 200 nV, 500 nV, 1 uV, 2 uV, 5 uV, 10 uV, 20 uV, 50 uV, 100 uV, 200 uV, 500 uV, 2 mV, 5 mV, 10 mV, 20 mV, 50 mV, 100 mV, 200 mV, 500 mV, 1 V]. If the sensitivity is not contained in the array, no change will occur and "Invalid sensitivity value" will be printed.
Example: lock_in_sensitivity(10, 'uV') sets the sensitivity to 10 uV. Note that lock_in_sensitivity('10', 'uV') also can be used.
### lock_in_ref_mode(\*mode)
#### Arguments: \*mode = one integer (0 or 1); Output: integer or none.
This function queries or sets the modulation mode, i.e. if the internal modulation or an external modulation input is used. If there is no argument the function will return the current modulation mode. If there is an argument the specified modulation mode will be set. Possible modulation modes and their meaning are the following:
'0' - External mode; '1' - Internal mode.
Example: lock_in_ref_mode('0') sets the device to external modulation mode.
### lock_in_sync_filter(\*mode)
#### Arguments: \*mode = one integer (0 or 1); Output: integer or none.
This function queries or sets the synchronous filter status. If there is no argument the function will return the current status. If there is an argument the specified status will be set. Note that synchronous filtering is turned on only if the detection frequency is less than 200 Hz. Possible synchronous filter status and their meaning are the following:
'0' - synchronous filtering is off; '1' - synchronous filtering below 200 Hz.
Example: lock_in_sync_filter('1') turns on synchronous filtering.
### lock_in_command(command)
#### Arguments: string(command); Output: none.
The function for sending an arbitrary command from programming guide to the device in a string format. No output is expected.
Example: lock_in_command('OFSL 0'). This example sets the low pass filter slope. The parameter equals to 0 selects 6 dB/oct.
### lock_in_query(command)
#### Arguments: string(command); Output: string(answer).
The function for sending an arbitrary command from programming guide to the device in a string format. An output in a string format is expected.
Example: lock_in_command('OFSL?'). This example queries the low pass filter slope.

## Oscilloscopes
### scope_record_length(\*points)
### scope_acquisition_type(\*ac_type)
### scope_number_of_averages(\*number_of_averages)
### scope_full_timebase(\*timebase)
### scope_timeresolution()
### scope_start_acquisition()
### scope_read_preamble(channel)
### scope_stop()
### scope_run()
### scope_get_curve(channel)
### scope_wave_freq(\*freq) Keysight 3034T
### scope_wave_width(\*width) Keysight 3034T

## Magnetic Field Controller
### field_controller_set_field(\*field)
### field_controller_command(command)

## Balances
### balance_weight()

## Other
## Solid-sate Relay RODOS-10N (ethernet)
### turn_on(number)
### turn_off(number)
