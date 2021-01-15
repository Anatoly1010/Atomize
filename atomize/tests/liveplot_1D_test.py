import time
import numpy as np
from liveplot import LivePlotClient
import atomize.device_modules.config.messenger_socket_client as send

plotter = LivePlotClient()
start_time=time.time()

xs=np.arange(5000);
#ys=np.zeros(15000);
#ys=np.random.rand(1,5000)

# Plot_xy Test
for i in range(100):
	ys=np.random.rand(1,5000)
	#xs = np.append(xs, i);
	#ys = np.append(ys, np.random.randint(0, 10 + 1));
	#ys[i] = np.random.randint(0, 10 + 1);
	plotter.plot_xy('Plot XY Test', xs, ys[0], label='test data')
	#time.sleep(0.002)
	

#plotter.remove('Plot XY Test')

# Append_y Test
#xs = np.linspace(0, 5, 1000)
#for i in range(1000):
#	start_time=time.time()
#	val = np.random.randint(0,10+1)
#	plotter.append_y('Append Y Test', val, start_step=(xs[0], xs[1]-xs[0]), label='test data')
#	time.sleep(0.1)
#	send.message(str(time.time() - start_time))

send.message(str(time.time() - start_time))