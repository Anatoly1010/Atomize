import time
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.PB_ESR_500_pro as pb_pro
import atomize.device_modules.Keysight_3000_Xseries as key
import atomize.device_modules.BH_15 as bh

### Experimental parameters
POINTS = 1000
STEP = 100                  # delta_start = '100 ns' for TRIGGER pulse
FIELD = 3473
AVERAGES = 200

data_x = np.zeros(POINTS)
data_y = np.zeros(POINTS)
x_axis = np.arange(0, POINTS*STEP, STEP)
###

# initialization of the devices
pb = pb_pro.PB_ESR_500_Pro()
bh15 = bh.BH_15()
t3034 = key.Keysight_3000_Xseries()

# Setting magnetic field
bh15.magnet_setup(FIELD, 1)
bh15.magnet_field(FIELD)

# Setting oscilloscope
t3034.oscilloscope_trigger_channel('CH1')
#tb = t3034.oscilloscope_time_resolution()
t3034.oscilloscope_record_length(250)
t3034.oscilloscope_acquisition_type('Average')
t3034.oscilloscope_number_of_averages(AVERAGES)
t3034.oscilloscope_stop()

# Setting pulses
pb.pulser_pulse(name = 'P0', channel = 'MW', start = '100 ns', length = '40 ns')
pb.pulser_pulse(name = 'P1', channel = 'MW', start = '300 ns', length = '80 ns', delta_start = '50 ns')
pb.pulser_pulse(name = 'P2', channel = 'TRIGGER', start = '500 ns', length = '100 ns', delta_start = '100 ns')

pb.pulser_repetitoin_rate('500 Hz')

# Data acquisition
for i in range(POINTS):

    pb.pulser_update()

    t3034.oscilloscope_start_acquisition()  
    area_x = t3034.oscilloscope_area('CH4')
    area_y = t3034.oscilloscope_area('CH3')
    
    data_x[i] = area_x
    data_y[i] = area_y

    general.plot_1d('T2', x_axis, data_x, xname = 'Delay',\
        xscale = 'ns', yname = 'Area', yscale = 'V*s', label = 'X')
    general.plot_1d('T2', x_axis, data_y, xname = 'Delay',\
        xscale = 'ns', yname = 'Area', yscale = 'V*s', label = 'Y')

    pb.pulser_shift()

    #data.append(area)
    #x_axis.append(i*100)                # delta_start for TRIGGER pulse

    #data.append(t3034.oscilloscope_get_curve('CH2'))
    #data2.append(t3034.oscilloscope_get_curve('CH3'))
    #general.plot_2d('I', data, start_step = ( (0, tb/1000000), (0, 2/1000000000) ), xname = 'Time',\
    #    xscale = 's', yname = 'Delay Time', yscale = 's', zname = 'Intensity', zscale = 'V')
    #general.plot_2d('Q', data2, start_step = ( (0, tb/1000000), (0, 2/1000000000) ), xname = 'Time',\
    #    xscale = 's', yname = 'Delay Time', yscale = 's', zname = 'Intensity', zscale = 'V')
   

pb.pulser_stop()

