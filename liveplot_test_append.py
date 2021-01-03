import sys
sys.path.append("D:/Melnikov/11_Programming/05_liveplot/liveplot")
# Add here path to liveplot
from liveplot import LivePlotClient
import numpy as np
import time

plotter = LivePlotClient()

## 1D plot check
#xs = np.linspace(0, 9, 10)
#for val in np.exp(xs):
#    plotter.append_y('appending exp', val, start_step=(xs[0], xs[1]-xs[0]), label='up')
#    time.sleep(0.1)


## 2D plot check
#plotter.clear()
data=[];
step=10;
i = 0;

while i <= 10:
	i=i+1;
	axis_x=np.arange(4000)
	ch_time=np.random.randint(50, 100, 1)
	zs = 1 + 100*np.exp(-axis_x/ch_time)+7*np.random.normal(size=(4000))
	#zs = np.random.rand(1,4000)
	data.append(zs)
	time.sleep(0.5)
	print(i+1)
	plotter.plot_z('appending sinc2', data, start_step=((3000,10),(0,1)))
	#plotter.append_z('appending sinc2', data[i-1], start_step=((3000,10),(0,1)))
	plotter.label('appending sinc2', 'step: %d' % i)
   
time.sleep(2)