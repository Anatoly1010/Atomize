# List of available functions for temperature controllers

## tc_name()
### Arguments: none; Output: string(name).
The function returns device name.
## tc_temperature(channel)
### Arguments: channel = 'A' or 'B' (shown as ['A','B'] further); Output: float.
The function for reading temperature from specified channel.<br/>
Note that arguments can be devices specific. A set of ['A','B'] is used for LakeShore 325, 331, 332, and 335, while for LakeShore 336, 340 a set of four channel ['A','B','C','D'] is used.<br/>
Example: tc_temperature('A') returns the temperature of channel A in Kelvin.
## tc_setpoint(\*temp)
### Arguments: temp = float; Output: float or none.
The function queries or changes the set point. If an argument is specified the function sets a new temperature point. If there is no argument the function returns the current set point. A loop can be specified in configuration file.<br/>
Example: tc_setpoint('100') changes the set point of the specified loop to 100 Kelvin.
## tc_heater_range(\*heater)
### Arguments: heater = string; Output: string or none. 
The function queries or sets the heater range. If an argument is specified the function sets a new heater range. If there is no argument the function returns the current heater range.<br/> 
Note that arguments are devices specific. Currently a set of ['50 W','5 W','0.5 W','Off'] can be used for LakeShore 331, 332, 335, while for LakeShore 340 a set ['10 W','1 W','Off'] is used.<br/>
For LakeShore 336 a loop 1 or 2 can be used with a set of ['50 W','5 W','0.5 W','Off']. The loop 3 and 4 can be used only with ['On','Off'] set.<br/>
For LakeShore 325 a loop 1 can be used with a set of ['25 W','2.5 W','Off']. The loop 2 can be used only with ['On','Off'] set.<br/>
The values '50 W','5 W', and'0.5 W' are shown as High, Medium, and Low on the device display.<br/>
Example: tc_heater_range('50 W') changes the heater range to 50 W (High). 
## tc_heater_state()
### Arguments: none; Output: array([string(heater_range), float(heater_percent)])
The function for reading the current heater value in percent.<br/>
Example: tc_heater() returns the array of the heater range and heater percent. 
## tc_command(command)
### Arguments: string(command); Output: none.
The function for sending an arbitrary command from a programming guide to the device in a string format. No output is expected.<br/>
Example: tc_command('PID 1,10,50,0'). Note that for some controller models the loop should not be specified. Check the programming guide.
## tc_query(command)
### Arguments: string(command); Output: string(answer).
The function for sending an arbitrary command from a programming guide to the device in a string format. An output in a string format is expected.<br/>
Example: tc_command('PID? 1'). Note that for some controller models the loop should not be specified. Check the programming guide.
