import time
import numpy as np
from math import pi
import atomize.general_modules.general_functions as general
import atomize.device_modules.Spectrum_M4I_6631_X8 as spectrum

# Phase
init_distance = 200
step = 10
x = 2*pi*(init_distance + 0.8)*200/1000
# suppose, second pulse is after 200 ns (init_distance) and pulse frequency is 200 MHz (both pulses)
# the phase of the second pulse should be 2*pi*(init_distance + 0.8)*frequency/1000
# 0.8 is sample rate (we calculate the phase for the next point); /1000 is MHz to GHz

# A possible use in an experimental script
awg = spectrum.Spectrum_M4I_6631_X8()
awg.awg_pulse(name = 'P0', channel = 'CH0', func = 'SINE', frequency = '200 MHz', phase = 0, length = '64 ns', sigma = '16 ns')
awg.awg_pulse(name = 'P1', channel = 'CH0', func = 'SINE', frequency = '200 MHz', phase = x, length = '32 ns', sigma = '16 ns')
#awg.awg_pulse(name = 'P2', channel = 'CH0', func = 'SINE', frequency = '200 MHz', phase = 0, length = '64 ns', sigma = '16 ns')

awg.awg_pulse(name = 'P3', channel = 'CH1', func = 'SINE', frequency = '200 MHz', phase = pi/2, length = '16 ns', sigma = '16 ns')
awg.awg_pulse(name = 'P4', channel = 'CH1', func = 'SINE', frequency = '200 MHz', phase = 0, length = '32 ns', sigma = '16 ns')
#awg.awg_pulse(name = 'P5', channel = 'CH1', func = 'SINE', frequency = '200 MHz', phase = 0, length = '64 ns', sigma = '16 ns')


awg.awg_channel('CH0', 'CH1')
#awg.awg_channel('CH0')
awg.awg_card_mode('Multi')
awg.awg_number_of_segments(2)
#awg.awg_card_mode('Single')
#awg.awg_number_of_segments(1)


#awg.awg_start()

buf = ( 32000*awg.define_buffer_multi()).astype('int64')


xs = 0.8*np.arange( len( buf )/2 )
general.plot_1d('SINE_SINGLE', xs, buf[0::2], label = 'CH0')
general.plot_1d('SINE_SINGLE', xs, 64000 + buf[1::2], label = 'CH1')
