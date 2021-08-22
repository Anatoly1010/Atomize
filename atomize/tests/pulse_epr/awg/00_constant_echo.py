import time
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.PB_ESR_500_pro as pb_pro
import atomize.device_modules.Spectrum_M4I_6631_X8 as spectrum
import atomize.device_modules.BH_15 as bh

# initialization of the devices
pb = pb_pro.PB_ESR_500_Pro()
bh15 = bh.BH_15()
awg = spectrum.Spectrum_M4I_6631_X8()

FIELD = 3400

# PULSES
REP_RATE = '1000 Hz'
PULSE_1_LENGTH = '16 ns'
PULSE_2_LENGTH = '32 ns'
# 412 ns is delay from AWG trigger
PULSE_1_START = '412 ns'
PULSE_2_START = '712 ns'
PULSE_SIGNAL_START = '1012 ns'

# Setting pulses
# trigger awg is always 412 ns before the actual AWG pulse
pb.pulser_pulse(name = 'P0', channel = 'TRIGGER_AWG', start = '0 ns', length = '30 ns')

# For each awg_pulse; length should be longer than in awg_pulse
pb.pulser_pulse(name = 'P1', channel = 'AWG', start = PULSE_1_START, length = '30 ns')
pb.pulser_pulse(name = 'P2', channel = 'AWG', start = PULSE_2_START, length = '60 ns', delta_start = str(int(STEP/2)) + ' ns')

pb.pulser_pulse(name = 'P3', channel = 'TRIGGER', start = PULSE_SIGNAL_START, length = '100 ns', delta_start = str(STEP) + ' ns')
awg.awg_pulse(name = 'P4', channel = 'CH0', func = 'SINE', frequency = '200 MHz', phase = 0, \
            length = PULSE_1_LENGTH, sigma = PULSE_1_LENGTH, start = PULSE_1_START)
awg.awg_pulse(name = 'P5', channel = 'CH0', func = 'SINE', frequency = '200 MHz', phase = 0, \
            length = PULSE_2_LENGTH, sigma = PULSE_2_LENGTH, start = PULSE_2_START, delta_start = str(int(STEP/2)) + ' ns')


pb.pulser_repetition_rate( REP_RATE )
awg.awg_channel('CH0', 'CH1')
awg.awg_card_mode('Single Joined')
awg.awg_setup()

awg.awg_update()
pb.pulser_update()

# Setting magnetic field
bh15.magnet_setup(FIELD, 1)
bh15.magnet_field(FIELD)

i = 0
for i in general.to_infinity():

    ##pb.pulser_update()
    general.wait('1000 ms')

    if i > 1000:
        break
        awg.awg_stop()
        awg.awg_close()
        pb.pulser_stop()

awg.awg_stop()
awg.awg_close()
pb.pulser_stop()
