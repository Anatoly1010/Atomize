import time
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.PB_ESR_500_pro as pb_pro
import atomize.device_modules.Keysight_3000_Xseries as key
import atomize.device_modules.BH_15 as bh

data = []
data2 = []
x_axis = []
FIELD = 3473
AVERAGES = 200

pb = pb_pro.PB_ESR_500_Pro()
bh15 = bh.BH_15()
t3034 = key.Keysight_3000_Xseries()

bh15.magnet_setup(FIELD, 1)
bh15.magnet_field(FIELD)

t3034.oscilloscope_trigger_channel('Line')
t3034.oscilloscope_run()
tb = t3034.oscilloscope_time_resolution()
t3034.oscilloscope_record_length(250)
t3034.oscilloscope_acquisition_type('Average')
t3034.oscilloscope_number_of_averages('10')
t3034.oscilloscope_trigger_channel('CH1')
t3034.oscilloscope_stop()

t3034.oscilloscope_number_of_averages(AVERAGES)


pb.pulser_pulse(name = 'P0', channel = 'MW', start = '100 ns', length = '40 ns')
pb.pulser_pulse(name = 'P1', channel = 'MW', start = '450 ns', length = '80 ns', delta_start = '50 ns')
pb.pulser_pulse(name = 'P3', channel = 'TRIGGER', start = '800 ns', length = '100 ns', delta_start = '100 ns')

pb.pulser_repetitoin_rate('500 Hz')


for i in range(1000):

    pb.pulser_update()
    #pb.pulser_visualize()

    t3034.oscilloscope_start_acquisition()  
    area = t3034.oscilloscope_area('CH4')
    data.append(area)
    x_axis.append(i*100)                # delta_start for TRIGGER pulse

    general.plot_1d('T2', x_axis, data, xname = 'Delay',\
        xscale = 'ns', yname = 'Area', yscale = 'V*s', timeaxis = 'False', label = '16-32ns')

    #data.append(t3034.oscilloscope_get_curve('CH2'))
    #data2.append(t3034.oscilloscope_get_curve('CH3'))

    #general.plot_2d('I', data, start_step = ( (0, tb/1000000), (0, 2/1000000000) ), xname = 'Time',\
    #    xscale = 's', yname = 'Delay Time', yscale = 's', zname = 'Intensity', zscale = 'V')
    #general.plot_2d('Q', data2, start_step = ( (0, tb/1000000), (0, 2/1000000000) ), xname = 'Time',\
    #    xscale = 's', yname = 'Delay Time', yscale = 's', zname = 'Intensity', zscale = 'V')

    pb.pulser_shift()

pb.pulser_stop()

