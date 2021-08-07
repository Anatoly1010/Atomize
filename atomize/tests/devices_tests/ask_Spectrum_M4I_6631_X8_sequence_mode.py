import time
import numpy as np
from math import pi
import atomize.general_modules.general_functions as general
import atomize.device_modules.Spectrum_M4I_6631_X8 as spectrum

# A possible use in an experimental script
awg = spectrum.Spectrum_M4I_6631_X8()

# number of channel should be define before awg.awg_pulse_sequence()
#awg.awg_channel('CH0')
awg.awg_channel('CH0', 'CH1')

start_time = time.time()
# 3 ms per point for three pulses
awg.awg_pulse_sequence(pulse_type = ['SINE', 'GAUSS', 'SINE', 'SINE'], pulse_start = [0, 160, 320, 780], pulse_delta_start = [0, 0, 40, 0], pulse_length = [40, 120, 40, 40], \
		pulse_phase = ['+x', '+x', '+x', '+x'], pulse_sigma = [40, 20, 40, 40], pulse_frequency = [50, 200, 40, 80], number_of_points = 10, loop = 200, rep_rate = 2000)

#awg.awg_pulse_sequence(pulse_type = ['SINE'], pulse_start = [0], pulse_delta_start = [0], pulse_length = [100], \
#		pulse_phase = ['+x'], pulse_sigma = [40], pulse_frequency = [100], number_of_points = 5, loop = 100, rep_rate = 200)

# for phase cycling pulse_sequence should be redefined
# it seems that it will be more efficient than filling a large buffer
# four phase cycles will multiply a number of pulses by four!!!
general.message(str(time.time() - start_time))

awg.awg_card_mode('Sequence')
awg.awg_setup()

awg.awg_update()
awg.awg_stop()

#awg.awg_visualize()

# A possible way of phase cycling
#for i in range(2):
#    if i == 0:
#        # first cycle
#        awg.awg_pulse_sequence(pulse_type = ['SINE', 'GAUSS', 'SINE'], pulse_start = [0, 160, 320], pulse_delta_start = [0, 0, 40], pulse_length = [40, 120, 40], pulse_phase = ['+x', '+x', '+x'], \
#                        pulse_sigma = [40, 20, 40], pulse_frequency = [50, 200, 40], number_of_points = 100, loop = 10)
#        # awg.awg_update()
#    elif i == 1:
#        # second cycle
#        awg.awg_pulse_sequence(pulse_type = ['SINE', 'GAUSS', 'SINE'], pulse_start = [0, 160, 320], pulse_delta_start = [0, 0, 40], pulse_length = [40, 120, 40], pulse_phase = ['+x', '-x', '-x'], \
#                pulse_sigma = [40, 20, 40], pulse_frequency = [50, 200, 40], number_of_points = 100, loop = 10)
        # awg.awg_update()
    
#    awg.awg_visualize()
    # Do acquisition here
#    general.wait('2 s')
