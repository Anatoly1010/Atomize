import sys
import time
import signal
import datetime
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.PB_ESR_500_pro as pb_pro
import atomize.device_modules.Keysight_3000_Xseries as key
import atomize.device_modules.Spectrum_M4I_6631_X8 as spectrum
###import atomize.device_modules.Spectrum_M4I_4450_X8 as spectrum
import atomize.device_modules.Mikran_X_band_MW_bridge as mwBridge
import atomize.device_modules.SR_PTC_10 as sr
import atomize.device_modules.BH_15 as bh
import atomize.general_modules.csv_opener_saver as openfile

# initialization of the devices
file_handler = openfile.Saver_Opener()
ptc10 = sr.SR_PTC_10()
mw = mwBridge.Mikran_X_band_MW_bridge()
pb = pb_pro.PB_ESR_500_Pro()
bh15 = bh.BH_15()
t3034 = key.Keysight_3000_Xseries()
###dig4450 = spectrum.Spectrum_M4I_4450_X8()
awg = spectrum.Spectrum_M4I_6631_X8()

def cleanup(*args):
    awg.awg_stop()
    awg.awg_close()
    pb.pulser_stop()
    sys.exit(0)

signal.signal(signal.SIGTERM, cleanup)

### Experimental parameters
POINTS = 501
STEP = 8                  # in NS; delta_start = str(STEP) + ' ns' -> delta_start = '4 ns'
FIELD = 3388
AVERAGES = 10
SCANS = 1

# PULSES
REP_RATE = '500 Hz'
PULSE_1_LENGTH = '16 ns'
PULSE_2_LENGTH = '32 ns'
# 412 ns is delay from AWG trigger
PULSE_1_START = '398 ns'
PULSE_2_START = '698 ns'
PULSE_SIGNAL_START = '998 ns'
PULSE_AWG_1_START = '0 ns'
PULSE_AWG_2_START = '300 ns'

# NAMES
EXP_NAME = 'T2_AWG'

# Setting pulses
# trigger awg is always 412 ns before the actual AWG pulse
pb.pulser_pulse(name = 'P0', channel = 'TRIGGER_AWG', start = '0 ns', length = '30 ns')

# For each awg_pulse; length should be longer than in awg_pulse
pb.pulser_pulse(name = 'P1', channel = 'AWG', start = PULSE_1_START, length = '16 ns')
pb.pulser_pulse(name = 'P2', channel = 'AWG', start = PULSE_2_START, length = '32 ns', delta_start = str(int(STEP/2)) + ' ns')

pb.pulser_pulse(name = 'P3', channel = 'TRIGGER', start = PULSE_SIGNAL_START, length = '100 ns', delta_start = str(STEP) + ' ns')
awg.awg_pulse(name = 'P4', channel = 'CH0', func = 'SINE', frequency = '155 MHz', phase = 0, \
            length = PULSE_1_LENGTH, sigma = PULSE_1_LENGTH, start = PULSE_AWG_1_START)
awg.awg_pulse(name = 'P5', channel = 'CH0', func = 'SINE', frequency = '155 MHz', phase = 0, \
            length = PULSE_2_LENGTH, sigma = PULSE_2_LENGTH, start = PULSE_AWG_2_START, delta_start = str(int(STEP/2)) + ' ns')


pb.pulser_repetition_rate( REP_RATE )
pb.pulser_update()

#
t3034.oscilloscope_record_length( 1000 )
real_length = t3034.oscilloscope_record_length( )
tb = t3034.oscilloscope_timebase() * 1000
#x_axis = np.linspace(0, (POINTS - 1)*STEP, num = POINTS)
data = np.zeros( (2, real_length, POINTS) )
###

#awg.awg_clock_mode('External')
#awg.awg_reference_clock(100)
awg.awg_channel('CH0', 'CH1')
awg.awg_card_mode('Single Joined')
awg.awg_setup()

# Setting magnetic field
bh15.magnet_setup(FIELD, 1)
bh15.magnet_field(FIELD)

# Setting oscilloscope
t3034.oscilloscope_trigger_channel('CH1')
t3034.oscilloscope_acquisition_type('Average')
t3034.oscilloscope_number_of_averages(AVERAGES)
#t3034.oscilloscope_stop()

###dig4450.digitizer_read_settings()
###dig4450.digitizer_number_of_averages(AVERAGES)
###real_length = int (dig4450.digitizer_number_of_points( ) )
###tb = dig4450.digitizer_number_of_points() * int(  1000 / float( dig4450.digitizer_sample_rate().split(' ')[0] ) )

# Data saving
#str(tb)
header = 'Date: ' + str(datetime.datetime.now().strftime("%d-%m-%Y %H-%M-%S")) + '\n' + \
         'T2 Measurement; AWG\n' + 'Field: ' + str(FIELD) + ' G \n' + \
          str(mw.mw_bridge_att_prm()) + '\n' + str(mw.mw_bridge_synthesizer()) + '\n' + \
          'Repetition Rate: ' + str(pb.pulser_repetition_rate()) + '\n' + 'Number of Scans: ' + str(SCANS) + '\n' +\
          'Averages: ' + str(AVERAGES) + '\n' + 'Window: ' + str(tb) + ' ns\n' \
          + 'Temperature: ' + str(ptc10.tc_temperature('2A')) + ' K\n' +\
          'Pulse List: ' + '\n' + str(pb.pulser_pulse_list()) + 'AWG Pulse List: ' + '\n' +\
          str(awg.awg_pulse_list()) + 'Time (trig. delta_start), X (V*s), Y (V*s) '

file_data, file_param = file_handler.create_file_parameters('.param')
file_handler.save_header(file_param, header = header, mode = 'w')

##### phase cycling
# awg.awg_redefine_phase(name = 'P0', phase = pi/2)

# Data acquisition
j = 1
while j <= SCANS:

    for i in range(POINTS):

    	pb.pulser_update()
        awg.awg_update()
        
        ###x_axis, x, y = dig4450.digitizer_get_curve( )
        t3034.oscilloscope_start_acquisition()  
        x = t3034.oscilloscope_get_curve('CH4')
        y = t3034.oscilloscope_get_curve('CH3')
        
        data[0, :, i] = ( data[0, :, i] * (j - 1) + x ) / j
        data[1, :, i] = ( data[0, :, i] * (j - 1) + y ) / j

        general.plot_2d(EXP_NAME, data, start_step = ( (0, tb / real_length), (0, STEP) ), xname = 'Time',\
            xscale = 'ns', yname = 'Delay', yscale = 'ns', zname = 'Intensity', zscale = 'V')
        general.text_label( EXP_NAME, "Scan / Time: ", str(j) + ' / '+ str(i*STEP) )

        awg.awg_stop()
        awg.awg_shift()
        pb.pulser_shift()

    j += 1
    awg.awg_pulse_reset()
    pb.pulser_pulse_reset()

###dig4450.digitizer_stop()
###dig4450.digitizer_close()
awg.awg_stop()
awg.awg_close()
pb.pulser_stop()

file_handler.save_data(file_data, data, header = header, mode = 'w')
