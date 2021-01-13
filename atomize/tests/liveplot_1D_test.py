import time
import numpy as np
from liveplot import LivePlotClient
import atomize.device_modules.config.messenger_socket_client as send

plotter = LivePlotClient()


xs=np.arange(50);
ys=np.zeros(50);

# Plot_xy Test
for i in range(50):
	start_time=time.time()
	#xs = np.append(xs, i);
	#ys = np.append(ys, np.random.randint(0, 10 + 1));
	ys[i] = np.random.randint(0, 10 + 1);
	plotter.plot_xy('Plot XY Test', xs, ys, label='test data')
	time.sleep(0.1)
	send.message(str(time.time() - start_time))

plotter.remove('Plot XY Test')

# Append_y Test
xs = np.linspace(0, 5, 1000)
#for i in range(1000):
#	start_time=time.time()
#	val = np.random.randint(0,10+1)
#	plotter.append_y('Append Y Test', val, start_step=(xs[0], xs[1]-xs[0]), label='test data')
#	time.sleep(0.1)
#	send.message(str(time.time() - start_time))
