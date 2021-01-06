from liveplot import LivePlotClient
import numpy as np
import time
import atomize.device_modules.config.messenger_socket_client as send

start_time = time.time()
plotter = LivePlotClient()

## 1D plot check
#xs = np.linspace(0, 9, 10)
#print(xs)
#for val in np.exp(xs):
#    time.sleep(0.5)
#    plotter.append_y('appending exp', val, start_step=(xs[0], xs[1]-xs[0]), label='down', yname='Y axis', yscale='V')
#    print('hi')
    


## 2D plot check
#plotter.clear()
data=[];
step=10;
i = 0;
send.message('Test of 2D experiment')

while i <= 200:
	i=i+1;
	#f=open('test.csv','a')
	axis_x=np.arange(4000)
	ch_time=np.random.randint(250, 500, 1)
	zs = 1 + 100*np.exp(-axis_x/ch_time)+7*np.random.normal(size=(4000))
	#zs = np.random.rand(1,4000)
	data.append(zs)
	#time.sleep(0.1)
	#np.savetxt(f, zs, fmt='%.10f', delimiter=' ', newline='\n', header='field: %d' % i, footer='', comments='#', encoding=None)
	#print(data)
	plotter.plot_z('2D Plot', data, start_step=((0,1),(0.3,0.001)), xname='Time', 
	xscale='s', yname='Magnetic Field', yscale='T', zname='Intensity', zscale='V')
	#f.close()
	#plotter.append_z('appending sinc2', data[i-1], start_step=((0,1),(0.3,0.001)), xname='Time', 
	#xscale='s', yname='Magnetic Field', yscale='T', zname='Intensity', zscale='V')
#	plotter.label('appending sinc2', 'step: %d' % i)


send.message(str(time.time() - start_time))