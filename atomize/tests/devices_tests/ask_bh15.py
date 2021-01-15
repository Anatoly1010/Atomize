import time
import numpy as np
from liveplot import LivePlotClient
import atomize.device_modules.config.messenger_socket_client as send
import atomize.device_modules.bh15 as bh

#plotter = LivePlotClient()

bh15 = bh.bh15()

bh15.magnet_setup(500,1)
#send.message(bh15.device_write('SS175.000'))
#send.message(bh15.device_query('LE'))

i=0;
while i<5:

	bh15.magnet_field(3500 + 50*i)
	send.message(bh15.magnet_field())
	time.sleep(2)
	i = i + 1
	

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
#for i in range(100):
#    start_time = time.time()
#    plotter.append_y('Append Y Test', sr.lock_in_get_data(), start_step=(0, 1), label='test data')
#    time.sleep(0.03)

#    send.message(str(time.time() - start_time))


#sr.close_connection()