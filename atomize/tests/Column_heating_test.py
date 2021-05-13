import os
import sys
import time
from datetime import datetime
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.Termodat_11M6 as td

if len(sys.argv) > 1:
    test_flag = sys.argv[1]
else:
    test_flag = 'None'

tdat11m6 = td.Termodat_11M6()
timenow = str(datetime.now().strftime("%d-%m-%Y_%H-%M-%S"))
path_to_file = os.path.join('D:/Melnikov/', str(timenow) + '_Column_heating_test' + '.csv')

# Event handling flags
flag1 = 0
flag2 = 0

xs = []
ys1 = []
ys2 = []
ys3 = []
ys4 = []

tdat11m6.tc_setpoint('1','623.1')
tdat11m6.tc_setpoint('2','623.1')
tdat11m6.tc_setpoint('3','623.1')
tdat11m6.tc_setpoint('4','623.1')

# Parameters
heat_time = 3600 # in seconds

# Main loop
for i in range(36000):

    # for heating the indicated amount of time
    now = round(time.time())

    xs = np.append(xs, i)
    temp1 = tdat11m6.tc_temperature('1') - 273.1
    temp2 = tdat11m6.tc_temperature('2') - 273.1
    temp3 = tdat11m6.tc_temperature('3') - 273.1
    temp4 = tdat11m6.tc_temperature('4') - 273.1
    
    ys1 = np.append(ys1, temp1)
    ys2 = np.append(ys2, temp2)
    ys3 = np.append(ys3, temp3)
    ys4 = np.append(ys4, temp4)

    general.plot_1d('Plot 1', xs, ys1, label='ch1')
    general.plot_1d('Plot 2', xs, ys2, label='ch2')
    general.plot_1d('Plot 3', xs, ys3, label='ch3')
    general.plot_1d('Plot 4', xs, ys4, label='ch4')

    if flag1 == 0 and (temp1 > 350 or temp2 > 350 or temp3 > 350 or temp4 > 350):
        temp_reached = round(time.time())
        flag1 = 1
        general.message('Target temperature has been reached')

    if flag2 == 0 and flag1 == 0:
        pass
    elif flag2 == 0 and flag1 == 1:
        if abs(now - temp_reached) > heat_time:
            flag2 = 1
            tdat11m6.tc_setpoint('1','253')
            tdat11m6.tc_setpoint('2','253')
            tdat11m6.tc_setpoint('3','253')
            tdat11m6.tc_setpoint('4','253')
            general.message('Heating is OFF')
    else:
        pass

    if test_flag != 'test':
        
        head = '' # set empty header
        if not os.path.isfile(path_to_file): # checks if the file exists
            head = 'Time step: ' + '1 s\n'+ \
            'Ch1 - Ch2 - Ch3 - Ch4 (deg. Celcius):'  # if it doesn't then add the header
        file_save = open(path_to_file, 'a')

        np.savetxt(file_save, np.c_[xs[i], ys1[i], ys2[i], ys3[i], ys4[i]], fmt='%.1f', delimiter=',', \
            newline='\n', footer='', header=head, comments='# ', encoding=None)

        file_save.close()

    elif test_flag == 'test':
        pass

    general.wait('1 s')
   
