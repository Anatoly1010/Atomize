import time
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.general_modules.csv_opener_saver_tk_kinter as openfile

#start_time = time.time()
#open1d = openfile.Saver_Opener()

data = np.zeros( (4, 10000, 10) )
#data = np.zeros( (10, 10000) )
step = 10
i = 0
#general.message('Test of 2D experiment')
#path_to_file = open1d.create_file_dialog(directory='')


#f = open(patfile:///home/anatoly/Atomize/atomize/tests/liveplot_2D_test.pyh_to_file,'a')
## 2D Plot tests
while i < 10:

    axis_x = np.arange(10000)
    ch_time = np.random.randint(250, 500, 1)
    zs1 = 1 + 100*np.exp(-axis_x/ch_time) + 7*np.random.normal(size = (10000))
    zs2 = 1 + 100*np.exp(-axis_x/ch_time) + 7*np.random.normal(size = (10000))

    data[0, :, i] = zs1
    data[1, :, i] = zs2

    #general.wait('100 ms')
    #np.savetxt(f, zs, fmt='%.10f', delimiter=' ', newline='\n', header='field: %d' % i, footer='', comments='#', encoding=None)
    start_time = time.time()
    # Plot_z Test
    general.plot_2d('Plot Z Test', data,  xname='Time', start_step=( (0, 1), (0.3, 0.001) ),\
        xscale='s', yname='Magnetic Field', yscale='T', zname='Intensity', zscale='V')
    general.message(str(time.time() - start_time))
    #start_step=( (0, 1), (0.3, 0.001) ),
    # Append_z Test
    #general.append_2d('Append Z Test', data[i-1], start_step=((0,1),(0.3,0.001)), xname='Time', 
    #xscale='s', yname='Magnetic Field', yscale='T', zname='Intensity', zscale='V')

    # Label Test
    #general.text_label('Plot Z Test', 'step:', i)

    i += 1

#general.plot_remove('Plot Z Test')

#open(path_to_file, "w").close()
#f = open(path_to_file,'a')
#np.savetxt(f, data, fmt='%.10f', delimiter=',', newline='\n', header='field: %d' % i, footer='', comments='#', encoding=None)
#f.close()

#general.message(str(time.time() - start_time))