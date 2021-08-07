import time
import numpy as np
from math import pi
import atomize.general_modules.general_functions as general
#import atomize.device_modules.PB_ESR_500_pro as pb_pro
import atomize.device_modules.Spectrum_M4I_6631_X8 as spectrum

#pb = pb_pro.PB_ESR_500_Pro()
#pb.pulser_pulse(name = 'P0', channel = 'TRIGGER_AWG', start = '0 ns', length = '100 ns')

#pb.pulser_repetition_rate('2000 Hz')
#pb.pulser_update()

# A possible use in an experimental script
awg = spectrum.Spectrum_M4I_6631_X8()

awg.awg_pulse(name = 'P0', channel = 'CH0', func = 'SINE', frequency = '200 MHz', phase = 0, delta_phase = pi/2, length = '80 ns', sigma = '16 ns')
awg.awg_pulse(name = 'P1', channel = 'CH0', func = 'GAUSS', frequency = '200 MHz', phase = 0, length = '64 ns', sigma = '16 ns', start = '300 ns', delta_start = '100 ns')
awg.awg_pulse(name = 'P2', channel = 'CH0', func = 'SINE', frequency = '200 MHz', phase = 0, length = '80 ns', sigma = '16 ns', start = '7000 ns', delta_start = '200 ns')

awg.awg_channel('CH0', 'CH1')
#awg.awg_trigger_mode('Negative')
#awg.awg_trigger_channel('Software')
#awg.awg_loop(10)
#awg.awg_trigger_delay('5000 ns')
#awg.awg_amplitude('CH0', 100, 'CH1', 100)
#awg.awg_sample_rate(1000)

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
    general.wait('200 ms')
    
    awg.awg_stop()
    awg.awg_shift()

    if i == 1:
        awg.awg_redefine_delta_start(name = 'P1', delta_start = '300 ns')
        
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


test = awg.awg_pulse_list()

general.message( test )