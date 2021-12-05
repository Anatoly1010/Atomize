import time
import numpy as np
from datetime import datetime
from threading import Thread
from multiprocessing import Process
import atomize.general_modules.general_functions as general
#import atomize.general_modules.csv_opener_saver_tk_kinter as openfile
import atomize.general_modules.csv_opener_saver as openfile

file_handler = openfile.Saver_Opener()

a = 'None'
POINTS = 50
STEP = 2
j = 1
wind = 50

data_x = np.zeros(POINTS)
data_y = np.zeros(POINTS)
x_axis = np.linspace(0, (POINTS - 1)*STEP, num = POINTS) 

data = np.zeros( (2, int(wind), POINTS) )

# Plot_xy Test
for i in range(POINTS):

    # 1D
    #x, y = np.random.rand(1)[0], np.random.rand(1)[0]
    #data_x[i] = ( data_x[i] * (j - 1) + x ) / j
    #data_y[i] = ( data_y[i] * (j - 1) + y ) / j

    # 2D
    x, y = np.random.rand(wind), np.random.rand(wind)

    data[0, :, i] = ( data[0, :, i] * (j - 1) + x ) / j
    data[1, :, i] = ( data[0, :, i] * (j - 1) + y ) / j

    start_time = time.time()
    general.wait('100 ms')

    ##p1 = Thread(target=general.plot_1d, args=('Plot XY Test', xs, ys, ), kwargs={'label': 'test data2', 'timeaxis': 'False',} )
    #a = general.plot_1d('EXP_NAME', x_axis, (data_x, data_y), label = 'test2', xname = 'Delay', xscale = 'ns', yname = 'Area', yscale = 'V*s', vline = (STEP*i, ), pr = a, text=str(STEP*i))
    #a = general.plot_1d('EXP_NAME', x_axis, data_x, xname = 'Delay', xscale = 'ns', yname = 'Area', yscale = 'V*s', label = 'cur2', vline = (STEP*i, ), pr = a)
    #general.plot_1d('EXP_NAME', x_axis, data_x, xname = 'Delay', xscale = 'ns', yname = 'Area', yscale = 'V*s', label = 'cur2', vline = (STEP*i, ))

    a = general.plot_2d('EXP_NAME', data, start_step = ( (0, 1), (0, 1) ), xname = 'Time',\
            xscale = 'ns', yname = 'Delay', yscale = 'ns', zname = 'Intensity', zscale = 'V', pr = a, text=str(i))
    #a = general.text_label( 'EXP_NAME', "Scan / Time: ", 'TEST', pr = a )
    
    general.message(str(time.time() - start_time))
    
#file_handler.save_1D_dialog( (xs, ys), header = 'TEST' )
