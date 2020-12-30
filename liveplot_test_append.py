import sys
sys.path.append("D:/Melnikov/11_Programming/05_liveplot/liveplot")
# Add here path to liveplot
from liveplot import LivePlotClient
import numpy as np
import time

plotter = LivePlotClient()

xs = np.linspace(0, 9, 10)
for val in np.exp(xs):
    plotter.append_y('appending exp', val, start_step=(xs[0], xs[1]-xs[0]), label='up')
    #time.sleep(0.1)