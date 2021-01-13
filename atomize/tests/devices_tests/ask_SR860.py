import time
import numpy as np
from liveplot import LivePlotClient
import atomize.device_modules.config.messenger_socket_client as send
import atomize.device_modules.SR_860 as sr

plotter = LivePlotClient()

xs=[]
ys=[]

sr.connection()
sr.lock_in_time_constant('30 ms')

#Plot_xy Test
#for i in range(1000):
#	start_time = time.time()
#	xs = np.append(xs, i);
#	ys = np.append(ys, sr.lock_in_get_data());
	#ys = np.append(ys, np.random.randint(10,size=1));
#	plotter.plot_xy('SR 860', xs, ys, label='test data')
#	time.sleep(0.03)

#	send.message(str(time.time() - start_time))


#sr.close_connection()


# Append_y Test
for i in range(100):
    start_time = time.time()
    plotter.append_y('Append Y Test', sr.lock_in_get_data(), start_step=(0, 1), label='test data')
    time.sleep(0.03)

    send.message(str(time.time() - start_time))


sr.close_connection()