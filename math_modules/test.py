import sys
sys.path.append("D:/Melnikov/11_Programming/05_liveplot/liveplot")
import one_exp_fit as math_modules
import numpy as np
# Add here path to liveplot
from liveplot import LivePlotClient
import time

plotter = LivePlotClient()

one_exp = math_modules.math()

y=np.array([100,30,10,3,1,0.3,0.1,0.03,0,0.01,0.01]);

data = np.asarray([[0,1,2,3,4,5,6,7,8,9,10],y/1000])
model_data, residuals, r_squared = one_exp.one_exp_fit(data,[10,1,0])

plotter.plot_xy('residuals2', data[0], data[1], label='  exp_fit6', yname='Y axis', yscale='V', scatter='False')
#plotter.plot_xy('residuals2', data[0], residuals[:,1], label='residuals', yname='Y axis', yscale='V', scatter='True')

#time.sleep(10)

