import os
import sys
import time
import numpy as np
from scipy import integrate
from datetime import datetime
import atomize.general_modules.general_functions as general
import atomize.device_modules.Keysight_3000_Xseries as key

if len(sys.argv) > 1:
    test_flag = sys.argv[1]
else:
    test_flag = 'None'

averages = 750
freq = '1500 Hz'
width = '100 us'
repeats = 10
data2D = []
points = 4000
integral_value = 0

t3034 = key.Keysight_3000_Xseries()

t3034.wave_gen_run()
t3034.wave_gen_frequency(freq)
t3034.wave_gen_pulse_width(width)

t3034.oscilloscope_record_length(points)
t3034.oscilloscope_number_of_averages(averages)
res = t3034.oscilloscope_time_resolution()

i = 1
while i <= repeats:
    signal = []
    signal_corrected = []
    zero_level = 0

    t3034.oscilloscope_start_acquisition()
    signal = t3034.oscilloscope_get_curve('CH2')

    # Baseline correction
    zero_level = np.sum(signal[0:1000])/1000
    signal_corrected = -zero_level + signal

    data2D.append(signal_corrected)
    general.plot_2d('2D_Pulses', data2D, start_step = ((0, res), (0, 1)), xname='Time',\
        xscale='s', yname='Number of Spectrum', yscale='Arb. U.', zname='Signal Intensity', zscale='V')    

  
    #y_int = integrate.cumtrapz(y, x, initial=0)
    #numpy.trapz(y, x=None, dx=1.0, axis=-1)
    integral_value = integral_value + np.trapz(signal_corrected[1200:2801], dx = 1.0)

    i += 1

general.message(f"The integral is equal to {integral_value} arb. u.")

if test_flag != 'test':

    timenow = str(datetime.now().strftime("%d-%m-%Y_%H-%M-%S"))

    path_to_file_2D = os.path.join('/home/lmr-pc/Experimental_Data/Auto/Pulses', '2D_pulses_' + str(timenow) +'.csv')
    file_save_2D = open(path_to_file_2D, 'a')

    head = 'Date: ' + str(timenow) + '\n' + 'Averages: ' + str(averages) + '\n' + \
         'Points: ' + str(points) + '\n' + 'Resolution: ' + str(res) + 'us \n' \
         'Wave gen frequency: ' + str(freq) + '\n' + 'Pulse width: ' + str(width) + '\n' + \
         'Number of pulses: ' + str(repeats) + '\n' + 'Integral: ' + str(integral_value) + ' Arb. u.'

    np.savetxt(file_save_2D, data2D, fmt='%.10f', delimiter=',', \
        newline='\n', header=head, footer='', comments='# ', encoding=None)

    file_save_2D.close()

elif test_flag == 'test':
    pass


t3034.wave_gen_stop()
t3034.oscilloscope_run()

general.message("Done.")

