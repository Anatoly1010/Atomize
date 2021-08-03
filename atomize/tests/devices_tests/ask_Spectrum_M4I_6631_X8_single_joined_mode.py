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

awg.awg_pulse(name = 'P0', channel = 'CH0', func = 'SINE', frequency = '200 MHz', phase = 0, delta_phase = pi/2, length = '80 ns', sigma = '16 ns')
awg.awg_pulse(name = 'P1', channel = 'CH0', func = 'GAUSS', frequency = '200 MHz', phase = 0, length = '64 ns', sigma = '16 ns', start = '300 ns', delta_start = '100 ns')
awg.awg_pulse(name = 'P2', channel = 'CH0', func = 'SINE', frequency = '200 MHz', phase = 0, length = '80 ns', sigma = '16 ns', start = '1000 ns')
awg.awg_pulse(name = 'P3', channel = 'CH0', func = 'SINE', frequency = '200 MHz', phase = 0, length = '80 ns', sigma = '16 ns', start = '1200 ns')
awg.awg_pulse(name = 'P4', channel = 'CH0', func = 'SINE', frequency = '200 MHz', phase = 0, length = '80 ns', sigma = '16 ns', start = '1400 ns')

#awg.awg_pulse(name = 'P1', channel = 'CH1', func = 'GAUSS', frequency = '200 MHz', phase = pi/2, length = '64 ns', sigma = '16 ns', increment = '10 ns')
#awg.awg_pulse(name = 'P4', channel = 'CH1', func = 'SINE', frequency = '200 MHz', phase = 0, delta_phase = pi/2, length = '64 ns', sigma = '16 ns')
#awg.awg_pulse(name = 'P5', channel = 'CH1', func = 'SINE', frequency = '200 MHz', phase = 0, length = '64 ns', sigma = '16 ns')

awg.awg_channel('CH0', 'CH1')
#awg.awg_channel('CH0')
awg.awg_card_mode('Single Joined')
#awg.awg_card_mode('Multi')
#awg.awg_number_of_segments(2)


awg.awg_setup()


######### Genereal tests
for i in range(5):
    start_time = time.time()
    awg.awg_update()
    general.message(str(time.time() - start_time))

#    awg.awg_visualize()
#    general.message(str(start_time2 - start_time))
    general.wait('1000 ms')
    

    awg.awg_stop()

    awg.awg_shift()
#    awg.awg_increment()
    
       ##### non-uniform sampling
#    if i == 3:
#        awg.awg_redefine_delta_start(name = 'P0', delta_start = '10 ns')
#        awg.awg_redefine_increment(name = 'P1', increment = '20 ns')
    #   awg.awg_pulse_reset('P4')

       ##### phase cycling
#    if i == 3:
#        awg.awg_redefine_phase(name = 'P0', phase = pi/2)
    #    awg.awg_redefine_increment(name = 'P1', increment = '20 ns')
    #    awg.awg_pulse_reset('P4')
        
#########

