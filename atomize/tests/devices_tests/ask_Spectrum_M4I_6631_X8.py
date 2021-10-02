import time
import numpy as np
from math import pi
import atomize.general_modules.general_functions as general
#import atomize.device_modules.PB_ESR_500_pro as pb_pro
import atomize.device_modules.Spectrum_M4I_6631_X8 as spectrum

# Phase
init_distance = 200
step = 10
x = 2*pi*(init_distance + 0.8)*200/1000
# suppose, second pulse is after 200 ns (init_distance) and pulse frequency is 200 MHz (both pulses)
# the phase of the second pulse should be 2*pi*(init_distance + 0.8)*frequency/1000
# 0.8 is sample rate (we calculate the phase for the next point); /1000 is MHz to GHz


#pb = pb_pro.PB_ESR_500_Pro()
#pb.pulser_pulse(name = 'P0', channel = 'TRIGGER_AWG', start = '0 ns', length = '100 ns')

#pb.pulser_repetition_rate('2000 Hz')
#pb.pulser_update()

# A possible use in an experimental script
awg = spectrum.Spectrum_M4I_6631_X8()

awg.awg_pulse(name = 'P0', channel = 'CH0', func = 'SINE', frequency = '200 MHz', phase = 0, delta_phase = pi/2, length = '80 ns', sigma = '16 ns', start = '0 ns', d_coef = 1.0)
awg.awg_pulse(name = 'P1', channel = 'CH0', func = 'WURST', frequency = ('0 MHz', '100 MHz'), phase = 0, length = '200 ns', sigma = '200 ns', start = '300 ns', delta_start = '2 ns')
#awg.awg_pulse(name = 'P2', channel = 'CH0', func = 'SINC', frequency = '200 MHz', phase = 0, length = '64 ns', sigma = '16 ns', start = '500 ns', increment = '2 ns')

awg.awg_pulse(name = 'P3', channel = 'CH1', func = 'GAUSS', frequency = '200 MHz', phase = pi/2, length = '64 ns', sigma = '16 ns', increment = '10 ns')
awg.awg_pulse(name = 'P4', channel = 'CH1', func = 'SINE', frequency = '200 MHz', phase = 0, delta_phase = pi/2, length = '64 ns', sigma = '16 ns')
#awg.awg_pulse(name = 'P5', channel = 'CH1', func = 'SINE', frequency = '200 MHz', phase = 0, length = '64 ns', sigma = '16 ns')

awg.awg_channel('CH0', 'CH1')
awg.awg_card_mode('Multi')
awg.awg_number_of_segments(2)
#awg.awg_channel('CH0')
#awg.awg_card_mode('Single Joined')
#awg.awg_card_mode('Single')

awg.awg_setup()

#start_time = time.time()
#awg.awg_update_test()
#general.message(str(time.time() - start_time))

######### Genereal tests
for i in range(6):
    awg.awg_update()
    #awg.awg_visualize()
    general.wait('1 s')
    awg.awg_stop()
    
    #awg.awg_shift()
    #awg.awg_increment()
    
       ##### non-uniform sampling
#    if i == 3:
#        awg.awg_redefine_delta_start(name = 'P0', delta_start = '10 ns')
#        awg.awg_redefine_increment(name = 'P1', increment = '20 ns')
    #   awg.awg_pulse_reset('P4')
        
#########


######### Phase cycling example
#for i in range(4):

    # phase cycle [+x, -x, -x, +x]
#    j = 0
#    while j < 4:
        # first cycle +x:
#        if j == 0:
#            awg.awg_update_test()
#            awg.awg_visualize()
#            general.wait('1 s')
            #t3034.oscilloscope_start_acquisition()
            #area_x = t3034.oscilloscope_area('CH4')
            #area_y = t3034.oscilloscope_area('CH3')

            #cycle_data_x.append(area_x)
            #cycle_data_y.append(area_y)

        # second cycle -x:
#        if j == 1:
#            awg.awg_add_phase(name = 'P1', add_phase = pi)
#            awg.awg_update_test()
#            awg.awg_visualize()
#            general.wait('1 s')

        # third cycle -x:
#        if j == 2:
#            awg.awg_update_test()
#            awg.awg_visualize()
#            general.wait('1 s')
        # third cycle +x:
#        if j == 3:
#            awg.awg_add_phase(name = 'P1', add_phase = -pi)
#            awg.awg_update_test()
#            awg.awg_visualize()
#            general.wait('1 s')
            
#        j += 1
    
    # acquisition cycle [+, -, -, +]
    #data_x[i] = (cycle_data_x[0] - cycle_data_x[1] - cycle_data_x[2] + cycle_data_x[3])/4
    #data_y[i] = (cycle_data_y[0] - cycle_data_y[1] - cycle_data_y[2] + cycle_data_y[3])/4

    #general.plot_1d('ESEEM', x_axis, data_x, xname = 'Delay',\
    #    xscale = 'ns', yname = 'Area', yscale = 'V*s', timeaxis = 'False', label = 'X')
    #general.plot_1d('ESEEM', x_axis, data_y, xname = 'Delay',\
    #    xscale = 'ns', yname = 'Area', yscale = 'V*s', timeaxis = 'False', label = 'Y')

#    awg.awg_shift()

    #cycle_data_x = []
    #cycle_data_y = []
#########


#awg.awg_reset()
#awg.awg_visualize()

#awg.awg_shift()

#awg.awg_stop()
#pb.pulser_stop()

awg.awg_close()