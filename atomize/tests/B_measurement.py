import sys
import time
import signal
import datetime
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.Sibir_1 as nmr_gaussmeter
import atomize.device_modules.ITC_FC as itc
import atomize.device_modules.Termodat_11M6 as td
import atomize.general_modules.csv_opener_saver as openfile

### INIZIALIZATIONS
file_handler = openfile.Saver_Opener()
NMR_SIBIR = nmr_gaussmeter.Sibir_1()
itc_fc = itc.ITC_FC()
tdat11m6 = td.Termodat_11M6()

### PARAMETERS
FIELD = 4000
AVERAGES = 32
POINTS = 500

### NAMES
EXP_NAME = 'FIELD'
EXP_NAME2 = 'TEMPERATURE'
EXP_NAME3 = 'FFT'
CURVE_NAME = 'exp'

data_field = np.zeros(POINTS)
data_temp = np.zeros(POINTS)
x_axis = np.zeros(POINTS)

def cleanup(*args):
    file_handler.save_data(file_data, np.c_[x_axis, data_field, data_temp], header = header, mode = 'w')
    sys.exit(0)

# SAVING
header = 'Date: ' + str(datetime.datetime.now().strftime("%d-%m-%Y %H-%M-%S")) + '\n' + \
         'FIELD STABILITY\n' + 'Base Field: ' + str(FIELD) + ' G \n' + \
          'Points: ' + str(POINTS) + '\n' + 'Time (s), Field (G), Temperature (K) '

file_data, file_param = file_handler.create_file_parameters('.param')
file_handler.save_header(file_param, header = header, mode = 'w')

#EXPERIMENT
itc_fc.magnet_field(FIELD)
general.wait('10 s')

NMR_SIBIR.gaussmeter_sensor_number(3)
NMR_SIBIR.gaussmeter_gain(23)
NMR_SIBIR.gaussmeter_points(10000)
NMR_SIBIR.gaussmeter_pulse_length(7.5)

#set_b0 = NMR_SIBIR.gaussmeter_search(2900,3100,5)
set_b0 = FIELD - 30
NMR_SIBIR.gaussmeter_number_of_averges(AVERAGES)

t1 = time.time()

for i in range(POINTS):
    
    NMR_SIBIR.gaussmeter_set_field(set_b0)
    FID, FFT, field, S_n = NMR_SIBIR.gaussmeter_field()

    data_field[i] = field
    data_temp[i] = tdat11m6.tc_temperature('1')
    t2 = round( time.time() - t1, 3)
    x_axis[i] = t2
    
    set_b0 = field
    #general.message(i , field , S_n)

    process1 = general.plot_1d(EXP_NAME, x_axis, data_field, xname = 'Time',\
        xscale = 's', yname = 'Field', yscale = 'G', label = CURVE_NAME, pr = process, \
        text = 'Point: ' + str(i))
    
    process2 = general.plot_1d(EXP_NAME2, x_axis, data_temp, xname = 'Time',\
        xscale = 's', yname = 'Temperature', yscale = 'K', label = CURVE_NAME, pr = process2)

    process3 = general.plot_1d(EXP_NAME3, np.arange(len(FFT)), FFT, xname = 'Points',\
        xscale = 'Arb U', yname = 'Intensity', yscale = 'Arb U', label = CURVE_NAME, pr = process3, \
        text = 'S2N: ' + str(S_n))

    #general.plot_1d('FID', np.arange(len(FID)), FID)
    #general.plot_1d('FIELD', np.arange(len(G)), G )
    #general.plot_1d('FFT', np.arange(len(FFT)), FFT)


file_handler.save_data(file_data, np.c_[x_axis, data_field, data_temp], header = header, mode = 'w')
