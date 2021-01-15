import time
import numpy as np
from liveplot import LivePlotClient
import atomize.device_modules.config.messenger_socket_client as send
import atomize.general_modules.csv_opener_saver_tk_kinter as openfile

start_time = time.time()
plotter = LivePlotClient()
#open1d = openfile.Saver_Opener()

data=[];
step=10;
i = 0;
#send.message('Test of 2D experiment')
#path_to_file = open1d.create_file_dialog(directory='')

#f = open(path_to_file,'a')
## 2D Plot tests
while i <= 100:
	i=i+1;

	
	axis_x=np.arange(10000)
	ch_time=np.random.randint(250, 500, 1)
	zs = 1 + 100*np.exp(-axis_x/ch_time)+7*np.random.normal(size=(10000))

	data.append(zs)
	#time.sleep(0.1)
	#np.savetxt(f, zs, fmt='%.10f', delimiter=' ', newline='\n', header='field: %d' % i, footer='', comments='#', encoding=None)
	
	# Plot_z Test
	plotter.plot_z('Plot Z Test', data, start_step=((0,1),(0.3,0.001)), xname='Time',\
		xscale='s', yname='Magnetic Field', yscale='T', zname='Intensity', zscale='V')
	

	# Append_z Test
	#plotter.append_z('Append Z Test', data[i-1], start_step=((0,1),(0.3,0.001)), xname='Time', 
	#xscale='s', yname='Magnetic Field', yscale='T', zname='Intensity', zscale='V')

	# Label Test
	#plotter.label('Append Z Test', 'step: %d' % i)


#open(path_to_file, "w").close()
#f=open(path_to_file,'a')
#np.savetxt(f, data, fmt='%.10f', delimiter=',', newline='\n', header='field: %d' % i, footer='', comments='#', encoding=None)
#f.close()


send.message(str(time.time() - start_time))