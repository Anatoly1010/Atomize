import time
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.general_modules.csv_opener_saver_tk_kinter as openfile

file_handler = openfile.Saver_Opener()

data = np.zeros( (4, 10000, 10) )
step = 10
i = 0

## 2D Plot
while i < 10:

    axis_x = np.arange(10000)
    ch_time = np.random.randint(250, 500, 1)
    zs1 = 1 + 100*np.exp(-axis_x/ch_time) + 7*np.random.normal(size = (10000))
    zs2 = 1 + 100*np.exp(-axis_x/ch_time) + 7*np.random.normal(size = (10000))

    data[0, :, i] = zs1
    data[1, :, i] = zs2

    start_time = time.time()

    # Plot_2d
    general.plot_2d('2D Multi', data,  xname='Time', start_step=( (0, 1), (0.3, 0.001) ),\
        xscale='s', yname='Magnetic Field', yscale='T', zname='Intensity', zscale='V')
    
    general.message(str(time.time() - start_time))
    
    i += 1

#file_handler.save_2D_dialog( data, header = 'TEST' )
