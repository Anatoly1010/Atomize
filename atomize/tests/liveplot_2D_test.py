import time
import numpy as np
from liveplot import LivePlotClient
import atomize.device_modules.config.messenger_socket_client as send

start_time = time.time()
plotter = LivePlotClient()

data=[];
step=10;
i = 0;
send.message('Test of 2D experiment')

## 2D Plot tests
while i <= 50:
	i=i+1;

	#f=open('test.csv','a')
	axis_x=np.arange(4000)
	ch_time=np.random.randint(250, 500, 1)
	zs = 1 + 100*np.exp(-axis_x/ch_time)+7*np.random.normal(size=(4000))

	data.append(zs)
	time.sleep(0.1)
	#np.savetxt(f, zs, fmt='%.10f', delimiter=' ', newline='\n', header='field: %d' % i, footer='', comments='#', encoding=None)
	
	# Plot_z Test
	plotter.plot_z('Plot Z Test', data, start_step=((0,1),(0.3,0.001)), xname='Time', 
	xscale='s', yname='Magnetic Field', yscale='T', zname='Intensity', zscale='V')
	#f.close()

	# Append_z Test
	plotter.append_z('Append Z Test', data[i-1], start_step=((0,1),(0.3,0.001)), xname='Time', 
	xscale='s', yname='Magnetic Field', yscale='T', zname='Intensity', zscale='V')

	# Label Test
	plotter.label('Append Z Test', 'step: %d' % i)


send.message(str(time.time() - start_time))