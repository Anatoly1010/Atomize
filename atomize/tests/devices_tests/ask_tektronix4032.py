import time
import numpy as np
from liveplot import LivePlotClient
import atomize.device_modules.config.messenger_socket_client as send
import atomize.device_modules.tektronix_4000_Series as t4032

plotter = LivePlotClient()



xs=[]
ys=[]
data=[]

t4032.connection()
t4032.oscilloscope_timebase('100 us')
t4032.oscilloscope_record_length(10000)
t4032.oscilloscope_number_of_averages(4)
t4032.oscilloscope_acquisition_type('Ave')
t4032.oscilloscope_define_window(start=1,stop=10000)


#x=np.arange(5000)

for i in range(400):
	start_time = time.time()
	t4032.oscilloscope_start_acquisition()
	y = t4032.oscilloscope_get_curve('CH1')
	data.append(y)
	plotter.plot_z('Plot Z Test2', data, start_step=((0,1),(0.3,0.001)), xname='Time',\
		xscale='s', yname='Magnetic Field', yscale='T', zname='Intensity', zscale='V')

	send.message(str(time.time() - start_time))


#plotter.plot_xy('Single Oscillogramm', x, y, label='test data')


t4032.close_connection()

#send.message(str(time.time() - start_time))