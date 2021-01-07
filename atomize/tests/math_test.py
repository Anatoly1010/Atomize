import time
import numpy as np
from liveplot import LivePlotClient
import atomize.math_modules.least_square_fitting_modules as math_modules
import atomize.general_modules.csv_opener_saver as openfile

plotter = LivePlotClient()
open1d =openfile.csv()

#y=np.array([100,30,10,3,1,0.3,0.1,0.03,0,0.01,0.01]);
#print(data[1:]-data[0])
#data = np.asarray([[0,1,2,3,4,5,6,7,8,9,10],y/1000,y])

head, dat = open1d.open_2D_appended('b', header=1,chunk_size=11)
one_exp = math_modules.math()

print(head)

#model_data, residuals, r_squared = one_exp.one_exp_fit(data,[10,1,0])

#plotter.plot_xy('1D Plot', dat[0], dat[1], label='line', yname='Y axis', yscale='V', scatter='False')
#plotter.plot_xy('1D Plot', dat[0], dat[2], label='scatter', yname='Y axis', yscale='V', scatter='False')

#residuals[:,1]

plotter.plot_z('Plot Z2 Test', dat, start_step=((0,1),(0.3,0.001)), xname='Time', 
	xscale='s', yname='Magnetic Field', yscale='T', zname='Intensity', zscale='V')

#time.sleep(10)

