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

# PULSES
STEP = 4
REP_RATE = '500 Hz'
PULSE_1_LENGTH = '16 ns'
PULSE_2_LENGTH = '32 ns'

PULSE_AWG_1_START = '0 ns'
PULSE_AWG_2_START = '1030 ns'

# A possible use in an experimental script
awg = spectrum.Spectrum_M4I_6631_X8()

#awg.awg_pulse(name = 'P0', channel = 'CH0', func = 'SINE', frequency = '200 MHz', phase = 0, delta_phase = pi/2, length = '80 ns', sigma = '16 ns')
#awg.awg_pulse(name = 'P1', channel = 'CH0', func = 'GAUSS', frequency = '200 MHz', phase = 0, length = '64 ns', sigma = '16 ns', start = '300 ns', delta_start = '100 ns')
#awg.awg_pulse(name = 'P2', channel = 'CH0', func = 'SINE', frequency = '200 MHz', phase = 0, length = '80 ns', sigma = '16 ns', start = '7000 ns', delta_start = '200 ns')

#awg.awg_pulse(name = 'P0', channel = 'CH0', func = 'SINE', frequency = '200 MHz', phase = 0, phase_list = ['+x', '+x', '+x', '+x'], length = '16 ns', sigma = '16 ns')
#awg.awg_pulse(name = 'P1', channel = 'CH0', func = 'SINE', frequency = '200 MHz', phase = 0, phase_list = ['+x', '+y', '-x', '-y'], length = '32 ns', sigma = '32 ns', start = '300 ns', delta_start = '8 ns')


awg.awg_pulse(name = 'P4', channel = 'CH0', func = 'WURST', frequency = ('0 MHz', '100 MHz'), phase = 0, \
            length = '200 ns', sigma = '200 ns', start = PULSE_AWG_2_START, n = 10)
##awg.awg_pulse(name = 'P5', channel = 'CH0', func = 'SINE', frequency = '125 MHz', phase = 0, \
##           length = PULSE_2_LENGTH, sigma = PULSE_2_LENGTH, start = PULSE_AWG_2_START, delta_start = str(int(STEP/2)) + ' ns')

awg.awg_channel('CH0', 'CH1')
#awg.awg_trigger_mode('Negative')
awg.awg_trigger_channel('External')
#awg.awg_loop(10)
#awg.awg_trigger_delay('5000 ns')
#awg.awg_amplitude('CH0', 100, 'CH1', 100)
#awg.awg_sample_rate(1000)

awg.awg_card_mode('Single Joined')
#awg.awg_card_mode('Multi')
#awg.awg_number_of_segments(2)

awg.awg_visualize()
"""
awg.awg_setup()

######### Genereal tests
for i in range(20):

    awg.awg_update()
    #k = 0
    #while k < 4:
    #    awg.awg_next_phase()
    #    awg.awg_stop()
        
    awg.awg_visualize()
    general.wait('1000 ms')

    #    k += 1

    awg.awg_stop()
    awg.awg_shift()


    #if i == 1:
    #    awg.awg_redefine_delta_start(name = 'P1', delta_start = '300 ns')
        
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


awg.awg_stop()
awg.awg_close()
"""