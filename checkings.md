# A list of checking 

- temperature controller (325, 335, 336, 340):
in tc_heater_range() check answer = int(device_query('RANGE?')) and the same in tc_heater answer = float(device_query('HTR?'))
maybe we need to indicate a loop for them
For 331, 332 there is no such problem in documentation
- check tc_set_temp() and tc_heater_range(). device.write('SETP '+ str(loop) + ', ' + str(temp)). Space here ', ' is questionable for all controllers

- SR-810
check the return of lock_in_time_constant(). 
check the return of lock_in_sensitivity().
check also other functions since they have been rewritten.

