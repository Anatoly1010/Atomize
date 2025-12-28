import time
import numpy as np
from datetime import datetime
import atomize.general_modules.general_functions as general
import atomize.general_modules.csv_opener_saver_tk_kinter as openfile

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

# Plot Test
for i in range(POINTS):

    # 1D
    x, y = np.random.rand(1)[0]*10e-10, np.random.rand(1)[0]*10e-10
    data_x[i] = ( data_x[i] * (j - 1) + x ) / j
    data_y[i] = ( data_y[i] * (j - 1) + y ) / j

    start_time = time.time()
    general.wait('100 ms')

    a = general.plot_1d('1D', x_axis, (data_x, data_y), label = 'test', xname = 'Delay', \
            xscale = 's', yname = 'Area', yscale = 'V*s', pr = a, text=str(STEP*i))

    general.message(str(time.time() - start_time))
    
#file_handler.save_1D_dialog( (xs, ys), header = 'TEST' )
