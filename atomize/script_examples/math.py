import time
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.math_modules.least_square_fitting_modules as math_modules
import atomize.general_modules.csv_opener_saver_tk_kinter as openfile

open1d = openfile.Saver_Opener()

y = np.array([100,30,10,3,1,0.3,0.1,0.03,0,0.01,0.01]);
#print(data[1:]-data[0])
data = np.asarray([[0,1,2,3,4,5,6,7,8,9,10],y/1000,y])

#open1d.open_2D_appended_dialog(directory='/home/anatoly/Atomize/atomize/tests', header=0,chunk_size=11)
one_exp = math_modules.math()

model_data, residuals, r_squared = one_exp.one_exp_fit(data,[10,1,0])
print(residuals[1])

general.plot_1d('1D Plot', data[0], model_data[1], label='line', yname='Y axis', yscale='V', scatter='False')
general.plot_1d('1D Plot', data[0], residuals[1], label='scatter', yname='Y axis', yscale='V', scatter='True')

general.wait('500 ms')

x = 0 

if x < 5:
	general.message('hi')
	general.wait('100 ms')

