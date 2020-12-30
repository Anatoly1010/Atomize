import sys
sys.path.append("D:/Melnikov/11_Programming/05_liveplot/liveplot")
from liveplot import LivePlotClient
import threading
import numpy as np
import time

plotter = LivePlotClient()

xs=np.array([]);
ys=np.array([])

for i in range(100):
	xs = np.append(xs, i);
	ys = np.append(ys, np.random.random_integers(0,10));
	plotter.plot_xy('travelling packet2', xs, ys, label='left3')
	time.sleep(0.1)

#plotter.clear('appending sinc')
#xs, ys = np.mgrid[-100:100, -100:100]/20.
#rs = np.sqrt(xs**2 + ys**2)
#zs = np.sinc(rs)
#for i in range(200):
#    plotter.append_z('appending sinc', zs[:,i])
#    time.sleep(0.1)

# Only the first point is adding to plot
xs = np.linspace(0, 9, 10)
for val in np.sin(xs):
    time.sleep(0.1)
    print(val)
    plotter.append_y('appending exp', val, start_step=(xs[0], xs[1]-xs[0]), label='up')
    time.sleep(0.1)
