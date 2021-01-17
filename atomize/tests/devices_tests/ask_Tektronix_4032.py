import time
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.Tektronix_4000_Series as t4032

xs = []
ys = []
data = []

t4032 = t4032.Tektronix_4000_Series()

t4032.oscilloscope_timebase('100 us')
t4032.oscilloscope_record_length(10000)
t4032.oscilloscope_number_of_averages(4)
t4032.oscilloscope_acquisition_type('Ave')
t4032.oscilloscope_define_window(start=1,stop=10000)


#x = np.arange(5000)

for i in range(400):
    start_time = time.time()
    t4032.oscilloscope_start_acquisition()
    y = t4032.oscilloscope_get_curve('CH1')
    data.append(y)
    general.plot_z('Plot Z Test2', data, start_step=((0,1),(0.3,0.001)), xname='Time',\
        xscale='s', yname='Magnetic Field', yscale='T', zname='Intensity', zscale='V')

    general.message(str(time.time() - start_time))


#general.plot_xy('Single Oscillogramm', x, y, label='test data')


t4032.close_connection()

#general.message(str(time.time() - start_time))