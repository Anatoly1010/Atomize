import sys
import signal
import datetime
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.PB_ESR_500_pro as pb_pro
import atomize.device_modules.Spectrum_M4I_6631_X8 as spectrum
import atomize.device_modules.Spectrum_M4I_4450_X8 as spectrum_dig
import atomize.device_modules.Mikran_X_band_MW_bridge as mwBridge
import atomize.device_modules.SR_PTC_10 as sr
import atomize.device_modules.BH_15 as bh
import atomize.general_modules.csv_opener_saver_tk_kinter as openfile

# initialization of the devices
file_handler = openfile.Saver_Opener()
ptc10 = sr.SR_PTC_10()
mw = mwBridge.Mikran_X_band_MW_bridge()
pb = pb_pro.PB_ESR_500_Pro()
bh15 = bh.BH_15()
dig4450 = spectrum_dig.Spectrum_M4I_4450_X8()
awg = spectrum.Spectrum_M4I_6631_X8()

def cleanup(*args):
    dig4450.digitizer_stop()
    dig4450.digitizer_close()
    awg.awg_stop()
    awg.awg_close()
    pb.pulser_stop()
    file_handler.save_data(file_data, data_x, header = header, mode = 'w')
    file_handler.save_data(file_data2, data_y, header = header, mode = 'w')
    sys.exit(0)

signal.signal(signal.SIGTERM, cleanup)

### Experimental parameters
POINTS = 64
FIELD = 3400
AVERAGES = 1000

# PULSES
REP_RATE = '1000 Hz'
PULSE_1_LENGTH = '16 ns'
PULSE_2_LENGTH = '32 ns'
# 398 ns is delay from AWG trigger 1.25 GHz
# 494 ns is delay from AWG trigger 1.00 GHz
PULSE_1_START = '494 ns'
PULSE_2_START = '3494 ns'
PULSE_SIGNAL_START = '494 ns'
PULSE_AWG_1_START = '0 ns'
PULSE_AWG_2_START = '3000 ns'
process = 'None'


# NAMES
EXP_NAME = 'Amp_awg'
CURVE_NAME = 'data_x'

# Setting magnetic field
bh15.magnet_setup(FIELD, 1)
bh15.magnet_field(FIELD)

dig4450.digitizer_read_settings()
dig4450.digitizer_number_of_averages( AVERAGES )
time_res = int( 1000 / int(dig4450.digitizer_sample_rate().split(' ')[0]) )
wind = dig4450.digitizer_number_of_points()

data_x = np.zeros( (5, int(wind), POINTS) )
data_y = np.zeros( (5, int(wind), POINTS) )

# Setting pulses
pb.pulser_pulse(name = 'P0', channel = 'TRIGGER_AWG', start = '0 ns', length = '30 ns')
# For each awg_pulse; length should be longer than in awg_pulse
pb.pulser_pulse(name = 'P1', channel = 'AWG', start = PULSE_1_START, length = PULSE_1_LENGTH)
pb.pulser_pulse(name = 'P2', channel = 'AWG', start = PULSE_2_START, length = PULSE_2_LENGTH)
pb.pulser_pulse(name = 'P3', channel = 'TRIGGER', start = PULSE_SIGNAL_START, length = '100 ns')

awg.awg_pulse(name = 'P4', channel = 'CH0', func = 'SINE', frequency = '50 MHz', phase = 0, \
            length = PULSE_1_LENGTH, sigma = PULSE_1_LENGTH, start = PULSE_AWG_1_START, phase_list = ['+x', '-x', '+y', '-y'])
awg.awg_pulse(name = 'P5', channel = 'CH0', func = 'SINE', frequency = '50 MHz', phase = 0, \
            length = PULSE_2_LENGTH, sigma = PULSE_2_LENGTH, start = PULSE_AWG_2_START, phase_list = ['+x', '-x', '+y', '-y'])


pb.pulser_repetition_rate( REP_RATE )
pb.pulser_update()

awg.awg_sample_rate(1000)
awg.awg_clock_mode('External')
awg.awg_reference_clock(100)
awg.awg_channel('CH0', 'CH1')
awg.awg_card_mode('Single Joined')
awg.awg_setup()

# Data saving
header = 'Date: ' + str(datetime.datetime.now().strftime("%d-%m-%Y %H-%M-%S")) + '\n' + \
         'Amplifier Pulse Test\n' + 'Field: ' + str(FIELD) + ' G \n' + \
          str(mw.mw_bridge_att_prm()) + '\n' + str(mw.mw_bridge_att1_prd()) + '\n' + str(mw.mw_bridge_synthesizer()) + '\n' + \
          'Repetition Rate: ' + str(pb.pulser_repetition_rate()) + '\n' +\
          'Averages: ' + str(AVERAGES) + '\n' + 'Points: ' + str(POINTS) + '\n' + 'Window: ' + str(wind * time_res) + ' ns\n' \
          + 'Horizontal Resolution: ' + str(time_res) + ' ns\n' + 'Vertical Resolution: ' + '0.5' + ' dB\n' \
          + 'Temperature: ' + str(ptc10.tc_temperature('2A')) + ' K\n' +\
          'Pulse List: ' + '\n' + str(pb.pulser_pulse_list()) + 'AWG Pulse List: ' + '\n' +\
          str(awg.awg_pulse_list()) + '2D Data'

file_data, file_param = file_handler.create_file_parameters('.param')
file_data2 = file_data.split('.csv')[0] + '_y.csv'
file_handler.save_header(file_param, header = header, mode = 'w')

# Data acquisition
for i in range(POINTS):

    mw.mw_bridge_att2_prd( str( round( i*0.5, 1 ) ) )
    # phase cycle
    k = 0
    while k < 4:

        awg.awg_next_phase()
        x_axis, data_x[k, :, i], data_y[k, :, i] = dig4450.digitizer_get_curve()
        
        awg.awg_stop()
        k += 1

    data_x[4, :, i] = data_x[0, :, i] + data_x[1, :, i] + data_x[2, :, i] + data_x[3, :, i]
    data_y[4, :, i] = data_y[0, :, i] + data_y[1, :, i] + data_y[2, :, i] + data_y[3, :, i]

    process = general.plot_2d( EXP_NAME, data_x, start_step = ( (0, time_res), (0, 1) ), xname = 'Time',\
            xscale = 'ns', yname = 'Attenuation', yscale = 'dB', zname = 'Intensity', zscale = 'V', pr = process, \
            text = 'PRD1: ' + str( round( i*0.5, 1 ) ) )

    # changing range
    #if i == 22:
    #    dig4450.digitizer_stop()
    #    dig4450.digitizer_amplitude( 1000 )
    #elif i == 42:
    #    dig4450.digitizer_stop()
    #    dig4450.digitizer_amplitude( 500 )        

    awg.awg_pulse_reset()

dig4450.digitizer_stop()
dig4450.digitizer_close()
awg.awg_stop()
awg.awg_close()
pb.pulser_stop()

file_handler.save_data(file_data, data_x, header = header, mode = 'w')
file_handler.save_data(file_data2, data_y, header = header, mode = 'w')
