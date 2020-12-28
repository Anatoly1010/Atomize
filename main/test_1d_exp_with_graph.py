import sys
import time
import numpy as np
import matplotlib.pyplot as plt
import plot_modules.matplotlibplotter as plotter



d = plotter.plot_1d()
# d2 = plotter.plot_1d();
d.initialize_1d()
# d2.initialize_1d();

xdata = []
ydata = []
ydata2 = []

for x in np.arange(0, 50, 0.5):
    xdata.append(x)
    ydata.append(np.exp(-x ** 2) + 10 * np.exp(-(x - 7) ** 2))
    # ydata2.append(np.exp(-x**2)+10*np.exp(-(x-7)**2))
    d.update_1d(xdata, ydata, True)
    # d2.update_1d(xdata, ydata2, True)
    time.sleep(0.5)

d.finish_1d()
# d2.finish_1d();
