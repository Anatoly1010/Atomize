import time
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.PB_ESR_500_pro as pb_pro
import atomize.device_modules.Keysight_3000_Xseries as key
import atomize.device_modules.BH_15 as bh

### Experimental parameters
POINTS = 200
STEP = 20                  # delta_start = '20 ns' for TRIGGER pulse
FIELD = 3473
AVERAGES = 1600

data_x = np.zeros(POINTS)
data_y = np.zeros(POINTS)
x_axis = np.arange(0, POINTS*STEP, STEP)
###

pb = pb_pro.PB_ESR_500_Pro()
t3034 = key.Keysight_3000_Xseries()
bh15 = bh.BH_15()

bh15.magnet_setup(FIELD, 1)
bh15.magnet_field(FIELD)

t3034.oscilloscope_trigger_channel('CH1')
#tb = t3034.oscilloscope_time_resolution()
t3034.oscilloscope_record_length(250)
t3034.oscilloscope_acquisition_type('Average')
t3034.oscilloscope_number_of_averages(AVERAGES)
t3034.oscilloscope_stop()

pb.pulser_pulse(name = 'P0', channel = 'MW', start = '100 ns', length = '16 ns')
# according to modulation deep in ESEEM. Can be adjust using different delays;
# a thin acquisition window
pb.pulser_pulse(name = 'P1', channel = 'MW', start = '470 ns', length = '16 ns')
pb.pulser_pulse(name = 'P2', channel = 'MW', start = '526 ns', length = '16 ns', delta_start = '20 ns')
pb.pulser_pulse(name = 'P3', channel = 'TRIGGER', start = '896 ns', length = '100 ns', delta_start = '20 ns')

pb.pulser_repetitoin_rate('500 Hz')

for i in range(POINTS):

    pb.pulser_update()  

    t3034.oscilloscope_start_acquisition()
    area_x = t3034.oscilloscope_area('CH4')
    area_y = t3034.oscilloscope_area('CH3')
    
    data_x[i] = area_x
    data_y[i] = area_y

    general.plot_1d('ESEEM', x_axis, data_x, xname = 'Delay',\
        xscale = 'ns', yname = 'Area', yscale = 'V*s', label = 'X')
    general.plot_1d('ESEEM', x_axis, data_y, xname = 'Delay',\
        xscale = 'ns', yname = 'Area', yscale = 'V*s', label = 'Y')

    pb.pulser_shift()

pb.pulser_stop()

