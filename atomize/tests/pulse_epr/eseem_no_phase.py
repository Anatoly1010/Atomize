import time
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.PB_ESR_500_pro as pb_pro
import atomize.device_modules.Keysight_3000_Xseries as key

data = []

pb = pb_pro.PB_ESR_500_Pro()
t3034 = key.Keysight_3000_Xseries()

t3034.oscilloscope_trigger_channel('Line')
t3034.oscilloscope_run()

tb = t3034.oscilloscope_time_resolution()

POINTS_T = 400
POINTS_O = t3034.oscilloscope_record_length()

t3034.oscilloscope_acquisition_type('Average')
t3034.oscilloscope_number_of_averages('10')
t3034.oscilloscope_trigger_channel('CH1')

t3034.oscilloscope_stop()

t3034.oscilloscope_number_of_averages('100')

pb.pulser_pulse(name = 'P0', channel = 'MW', start = '100 ns', length = '16 ns')
pb.pulser_pulse(name = 'P1', channel = 'MW', start = '220 ns', length = '16 ns')
pb.pulser_pulse(name = 'P2', channel = 'MW', start = '420 ns', length = '16 ns', delta_start = '100 ns')
pb.pulser_pulse(name = 'P3', channel = 'TRIGGER', start = '540 ns', length = '100 ns', delta_start = '100 ns')

pb.pulser_repetitoin_rate('200 Hz')

for i in range(400):
    start_time = time.time()
    pb.pulser_update()
    
    t3034.oscilloscope_start_acquisition()
    data.append(t3034.oscilloscope_get_curve('CH4'))

    general.plot_2d('ESEEM', data, start_step = ( (0, tb/1000000), (0, 100/1000000000) ), xname = 'Time',\
        xscale = 's', yname = 'Delay Time', yscale = 's', zname = 'Intensity', zscale = 'V')

    pb.pulser_shift()
    general.message(str(time.time() - start_time))

pb.pulser_stop()

