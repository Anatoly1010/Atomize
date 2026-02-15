import sys
import time
import signal
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.PB_ESR_500_pro as pb_pro
import atomize.device_modules.Spectrum_M4I_6631_X8 as spectrum
import atomize.device_modules.BH_15 as bh
import atomize.device_modules.Keysight_3000_Xseries as key


##t3034 = key.Keysight_3000_Xseries()
##t3034.oscilloscope_record_length( 2500 )

# initialization of the devices
pb = pb_pro.PB_ESR_500_Pro()
bh15 = bh.BH_15()
awg = spectrum.Spectrum_M4I_6631_X8()

def cleanup(*args):
    ###dig4450.digitizer_stop()
    ###dig4450.digitizer_close()
    awg.awg_stop()
    awg.awg_close()
    pb.pulser_stop()
    sys.exit(0)

signal.signal(signal.SIGTERM, cleanup)


FIELD = 3378
STEP = 4

# PULSES
REP_RATE = '500 Hz'
PULSE_1_LENGTH = '16 ns'
PULSE_2_LENGTH = '32 ns'
# 398 ns is delay from AWG trigger 1.25 GHz
# 494 ns is delay from AWG trigger 1.00 GHz
PULSE_1_START = '494 ns'
PULSE_2_START = '794 ns'
PULSE_SIGNAL_START = '1094 ns'
PULSE_AWG_1_START = '0 ns'
PULSE_AWG_2_START = '300 ns'

# Setting pulses
pb.pulser_pulse(name = 'P0', channel = 'TRIGGER_AWG', start = '0 ns', length = '30 ns')

# For each awg_pulse; length should be longer than in awg_pulse
pb.pulser_pulse(name = 'P1', channel = 'AWG', start = PULSE_1_START, length = PULSE_1_LENGTH)
pb.pulser_pulse(name = 'P2', channel = 'AWG', start = PULSE_2_START, length = PULSE_2_LENGTH, delta_start = str(int(STEP/2)) + ' ns')

pb.pulser_pulse(name = 'P3', channel = 'TRIGGER', start = PULSE_SIGNAL_START, length = '100 ns', delta_start = str(int(STEP)) + ' ns')
awg.awg_pulse(name = 'P4', channel = 'CH0', func = 'SINE', frequency = '50 MHz', phase = 0, \
            length = PULSE_1_LENGTH, sigma = PULSE_1_LENGTH, start = PULSE_AWG_1_START)
awg.awg_pulse(name = 'P5', channel = 'CH0', func = 'SINE', frequency = '50 MHz', phase = 0, \
            length = PULSE_2_LENGTH, sigma = PULSE_2_LENGTH, start = PULSE_AWG_2_START, delta_start = str(int(STEP/2)) + ' ns')


pb.pulser_repetition_rate( REP_RATE )

awg.awg_channel('CH0', 'CH1')
awg.awg_card_mode('Single Joined')
awg.awg_clock_mode('External')
awg.awg_reference_clock(100)
awg.awg_sample_rate(1000)
awg.awg_setup()

pb.pulser_update()
awg.awg_update()

# Setting magnetic field
bh15.magnet_setup(FIELD, 1)
bh15.magnet_field(FIELD)

i = 0
for i in general.to_infinity():

    ##pb.pulser_update()
    general.wait('1000 ms')
    
    ##awg.awg_stop()
    ##awg.awg_shift()
    ##pb.pulser_shift()
    ##pb.pulser_update()
    
    ##awg.awg_update()
    
    #awg.awg_visualize()
    ##t3034.oscilloscope_start_acquisition()  
    ##x = t3034.oscilloscope_get_curve('CH2')
    ##y = t3034.oscilloscope_get_curve('CH3')
    ##general.plot_1d('EXP_NAME', np.arange(len(x)), x )
    ##general.plot_1d('ECHO', np.arange(len(x)), y )

    if i > 60:
        break
        awg.awg_stop()
        awg.awg_close()
        pb.pulser_stop()

awg.awg_stop()
awg.awg_close()
pb.pulser_stop()
