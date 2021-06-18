import time
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.PB_ESR_500_pro as pb_pro
import atomize.device_modules.Keysight_3000_Xseries as key

data = []

pb = pb_pro.PB_ESR_500_Pro()
t3034 = key.Keysight_3000_Xseries()
t3034.oscilloscope_stop()

pb.pulser_pulse(name = 'P0', channel = 'MW', start = '100 ns', length = '16 ns')

pb.pulser_pulse(name = 'P1', channel = 'MW', start = '400 ns', length = '16 ns')
pb.pulser_pulse(name = 'P2', channel = 'MW', start = '520 ns', length = '32 ns', delta_start = '100 ns')
pb.pulser_pulse(name = 'P3', channel = 'TRIGGER', start = '640 ns', length = '500 ns', delta_start = '200 ns')

pb.pulser_repetitoin_rate('300 Hz')
t3034.oscilloscope_acquisition_type('Average')
t3034.oscilloscope_number_of_averages('300')

#t3034.oscilloscope_run()

tb = t3034.oscilloscope_time_resolution()

#general.message(tb)
#pb.pulser_update()
#pb.pulser_visualize()
#general.wait('10 s')
#pb.pulser_stop()

for i in range(40):
    start_time = time.time()
    pb.pulser_update()
    
    t3034.oscilloscope_start_acquisition()
    y = t3034.oscilloscope_get_curve('CH3')

    data.append(y)

    general.plot_2d('Plot Z', data, start_step = ( (0, tb/1000000), (1, 1) ), xname = 'Time',\
        xscale = 's', yname = 'Magnetic Field', yscale = 'T', zname = 'Intensity', zscale = 'V')

    pb.pulser_shift()
    general.message(str(time.time() - start_time))

#pb.pulser_reset()
pb.pulser_stop()


#j = 0 
#while j < 3:
#    i = 0
#    while i < 25:

        ###pb.pulser_increment()
#        pb.pulser_visualize()
#        general.wait('1 s')
#        i += 1
    
#    pb.pulser_reset()
    #print(pb.pulse_array_init)
#    general.wait('1 s')
#    j += 1



