#need a better way here. To load a file from different folder
import sys
sys.path.append("/home/anatoly/atomize/plot_modules/")
import matplotlibplotter as plotter

import numpy as np
import time
import matplotlib.pyplot as plt


d = plotter.plot_1d();
d.initialize_1d();

xdata = []
ydata = []

for x in np.arange(0,50,0.5):
    xdata.append(x)
    ydata.append(np.exp(-x**2)+10*np.exp(-(x-7)**2))
    d.update_1d(xdata, ydata)
    time.sleep(0.01)

d.finish_1d();
