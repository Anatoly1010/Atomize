# Atomize!

##To do list:

A. Modules/Connection/Config
- Write a detailed instruction how to install gpib library on Linux. Test gpib library on windows
- Continue to write modules
- Try to get rid of QProcess in the main window

B. Liveplot
- Need a way to save data from plots without using an internal pyqtgraph widget or at least check how 2D data looks like
- Need a special widget to grab a curve from plot and move it up/down, right/left

# A list of checkings to do

- temperature controller (325, 335, 336, 340):
in tc_heater_range() check answer = int(device_query('RANGE?')) and the same in tc_heater answer = float(device_query('HTR?'))
maybe we need to indicate a loop for them
For 331, 332 there is no such a problem in documentation
- check tc_set_temp() and tc_heater_range(). device.write('SETP '+ str(loop) + ', ' + str(temp)). Space here ', ' is questionable for all controllers

- SR-810
check the return of lock_in_time_constant(). 
check the return of lock_in_sensitivity().
check also other functions since they have been rewritten.











