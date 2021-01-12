import time
import numpy as np
from liveplot import LivePlotClient
import atomize.device_modules.config.messenger_socket_client as send
import atomize.device_modules.SR_860 as sr

plotter = LivePlotClient()

start_time = time.time()

xs=[]
ys=[]

sr.connection()
sr.lock_in_time_constant('10 ms')

#Plot_xy Test
for i in range(100):
	xs = np.append(xs, i);
	ys = np.append(ys, sr.lock_in_get_data());
	#ys = np.append(ys, np.random.randint(10,size=1));
	plotter.plot_xy('SR 860', xs, ys, label='test data')
	time.sleep(0.03)

send.message('test')

sr.close_connection()

send.message(str(time.time() - start_time))