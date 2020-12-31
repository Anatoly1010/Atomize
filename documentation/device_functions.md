# List of available functions for devices; 31/12/2020

## Temperature Controllers
### tc_read_temp(channel)
#### Arguments: channel = 'A' or 'B' (shown as ['A','B'] further); Output: float.
A function for reading temperature from specified channel. 
Note that arguments can be devices specific. A set of ['A','B'] is used for LakeShore 325, 331, 332, and 335, while for LakeShore 336, 340 a set of four channel ['A','B','C','D'] is used.
### tc_set_temp(\*temp)
#### Arguments: temp = float; Output: float or none.
A function for conntrolling set point. If an argument is specified the function set a new temperature point. If there is no argument the function return the current set point. A loop can be specified in configuration file.
### tc_heater_range(\*heater)
#### Arguments: heater = ['50W','5W','0.5W','Off']; Output: string or none. 
A function for conntrolling heater range. If an argument is specified the function set a new heater range. If there is no argument the function return the current heater range. 
Note that arguments are devices specific. Currently a set of ['50W','5W','0.5W','Off'] can be used for LakeShore 331, 332, 335, while for LakeShore 340 a set ['10W','1W','Off'] is used. For LakeShore 336 a loop 1 or 2 can be used with a set of ['50W','5W','0.5W','Off']. The loop 3 and 4 can be used only with ['On','Off'] set. For LakeShore 325 a loop 1 can be used with a set of ['25W','2.5W','Off']. The loop 2 can be used only with ['On','Off'] set. 
### tc_heater()
#### Arguments: None; Output: Array([string(heater_range), float(heater_percent)])
A function for reading the current heater value in percent.

## Lock-In detectors
### lock_in_modulation_frequency(\*freq)
### lock_in_phase(\*degs)
### lock_in_time_constant(\*tc)
### lock_in_amplitude(\*ampl)
### lock_in_signal()
### lock_in_signal_x_y_r()
### lock_in_noise_y()

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
