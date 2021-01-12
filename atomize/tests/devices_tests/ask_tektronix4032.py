import time
import numpy as np
from liveplot import LivePlotClient
import atomize.device_modules.config.messenger_socket_client as send
import atomize.device_modules.tektronix_4000_Series as t4032

plotter = LivePlotClient()

start_time = time.time()

xs=[]
ys=[]

t4032.connection()
t4032.oscilloscope_number_of_averages(32)
#t4032.oscilloscope_acquisition_type('Ave')
t4032.oscilloscope_define_window(start=1,stop=1000)

t4032.oscilloscope_start_acquisition()
x = t4032.oscilloscope_get_curve('CH1')
#y = np.arange(len(x))
#send.message(t4032.oscilloscope_define_window())
#send.message(x)

plotter.plot_xy('SR 860', x[:,0], x[:,1], label='test data')
#plotter.plot_xy('SR 860', np.array([0]), np.array([0]), label='test data')


#Plot_xy Test
#for i in range(100):
#	xs = np.append(xs, i);
#	ys = np.append(ys, sr.lock_in_get_data());
#	ys = np.append(ys, np.random.randint(10,size=1));
#	plotter.plot_xy('SR 860', xs, ys, label='test data')
#	time.sleep(0.03)

#send.message('test')
t4032.close_connection()

#send.message(str(time.time() - start_time))