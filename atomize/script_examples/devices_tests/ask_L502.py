import time
import numpy as np
import atomize.device_modules.L_card_L502 as l502_api
import atomize.general_modules.general_functions as general

l502 = l502_api.L_card_L502()

proc = 'None'
POINTS2 = 10000
POINTS = 6 * POINTS2
STEP = 0.5
x_axis = np.linspace(0, (POINTS - 1)*STEP, num = POINTS)
data_1 = np.zeros(POINTS)

l502.digitizer_clock_mode('Internal')
l502.digitizer_reference_clock(2)
l502.digitizer_flow('ADC')
l502.digitizer_number_of_points(POINTS2)

l502.digitizer_setup()

for j in range(1000):

	for i in range(6):
		
		#start_time = time.time()
		data_1[(POINTS2*i):POINTS2*(i+1)] = l502.digitizer_get_curve()
		#general.message(str(time.time() - start_time))

	proc = general.plot_1d('L502', x_axis, data_1, xname = 'Time', xscale = 'us', yname = 'Intensity', yscale = 'V', label = 'test', pr = proc)

	data_1 = np.zeros(POINTS)


l502.digitizer_close()

