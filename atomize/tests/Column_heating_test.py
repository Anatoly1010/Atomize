import os
import sys
import time
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.Termodat_11M6 as td

tdat11m6 = td.Termodat_11M6()

if len(sys.argv) > 1:
    test_flag = sys.argv[1]
else:
    test_flag = 'None'

count = 0

xs = []
ys1 = []
ys2 = []
ys3 = []
ys4 = []

#tdat11m6.tc_setpoint('1','623.1')

tdat11m6.tc_setpoint('1','623.1')
tdat11m6.tc_setpoint('2','623.1')
tdat11m6.tc_setpoint('3','623.1')
tdat11m6.tc_setpoint('4','623.1')

# Plot_xy Test
for i in range(36000):
    xs = np.append(xs, i)
    temp1 = tdat11m6.tc_temperature('1') - 273.1
    temp2 = tdat11m6.tc_temperature('2') - 273.1
    temp3 = tdat11m6.tc_temperature('3') - 273.1
    temp4 = tdat11m6.tc_temperature('4') - 273.1

    ys1 = np.append(ys1, temp1)
    ys2 = np.append(ys2, temp2)
    ys3 = np.append(ys3, temp3)
    ys4 = np.append(ys4, temp4)

    general.plot_1d('Plot XY Test 1', xs, ys1, label='ch1')
    general.plot_1d('Plot XY Test 2', xs, ys2, label='ch2')
    general.plot_1d('Plot XY Test 3', xs, ys3, label='ch3')
    general.plot_1d('Plot XY Test 4', xs, ys4, label='ch4')

    #622
    if temp1 > 349 or temp2 > 349 or temp3 > 349 or temp4 > 349:
        count = 1 + count
        general.message(count)

    # 1800
    if count < 1800:
        pass
    else:
        count = 0
        tdat11m6.tc_setpoint('1','253')
        tdat11m6.tc_setpoint('2','253')
        tdat11m6.tc_setpoint('3','253')
        tdat11m6.tc_setpoint('4','253')
        general.message('Heating is OFF')

    if test_flag != 'test':

        path_to_file= os.path.join('D:/Melnikov/', '01_Column_heating_test' + '.csv')
        file_save = open(path_to_file, 'wb')

        head = 'Time step: ' + '1 s\n'+ \
            'Ch1 - Ch2 - Ch3 - Ch4 (deg. Celcius):' 

        np.savetxt(file_save, np.c_[xs, ys1, ys2, ys3, ys4], fmt='%.1f', delimiter=',', \
            newline='\n', header=head, footer='', comments='# ', encoding=None) #header='field: %d' % i

        file_save.close()

    elif test_flag == 'test':
        pass

    general.wait('1 s')
   
