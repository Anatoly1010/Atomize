import sys
import signal
import datetime
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.Spectrum_M4I_6631_X8 as spectrum
import atomize.device_modules.Spectrum_M4I_4450_X8 as spectrum_dig
import atomize.device_modules.Mikran_X_band_MW_bridge as mwBridge
import atomize.device_modules.PB_ESR_500_pro as pb_pro
import atomize.device_modules.SR_PTC_10 as sr
import atomize.general_modules.csv_opener_saver_tk_kinter as openfile

# initialization of the devices
file_handler = openfile.Saver_Opener()
dig4450 = spectrum_dig.Spectrum_M4I_4450_X8()
awg = spectrum.Spectrum_M4I_6631_X8()
pb = pb_pro.PB_ESR_500_Pro()
mw = mwBridge.Mikran_X_band_MW_bridge()
ptc10 = sr.SR_PTC_10()

def cleanup(*args):
    dig4450.digitizer_stop()
    dig4450.digitizer_close()
    awg.awg_stop()
    awg.awg_close()
    pb.pulser_stop()
    sys.exit(0)

signal.signal(signal.SIGTERM, cleanup)

### Experimental parameters
START_FREQ = '0 MHz'
END_FREQ = '300 MHz'
STEP = 1
SCANS = 1
AVERAGES = 100
process = 'None'

start_freq_num = int( START_FREQ.split(" ")[0] )
end_freq_num = int( END_FREQ.split(" ")[0] )

# PULSES
REP_RATE = '2500 Hz'
PULSE_1_LENGTH = '50 ns'
# 398 ns is delay from AWG trigger 1.25 GHz
# 494 ns is delay from AWG trigger 1.00 GHz
PULSE_1_START = '494 ns'
PULSE_AWG_1_START = '0 ns'

# NAMES
EXP_NAME = 'Tune AWG'

# setting pulses:
pb.pulser_pulse(name = 'P0', channel = 'TRIGGER_AWG', start = '0 ns', length = '30 ns')
# For each awg_pulse; length should be longer than in awg_pulse
pb.pulser_pulse(name = 'P1', channel = 'AWG', start = PULSE_1_START, length = PULSE_1_LENGTH)
pb.pulser_pulse(name = 'P2', channel = 'TRIGGER', start = PULSE_1_START, length = '100 ns')

awg.awg_pulse(name = 'P3', channel = 'CH0', func = 'SINE', frequency = START_FREQ, phase = 0, \
            length = PULSE_1_LENGTH, sigma = PULSE_1_LENGTH, start = PULSE_AWG_1_START)

pb.pulser_repetition_rate( REP_RATE )
pb.pulser_update()

awg.awg_sample_rate(1000)
awg.awg_clock_mode('External')
awg.awg_reference_clock(100)
awg.awg_channel('CH0', 'CH1')
awg.awg_card_mode('Single Joined')
awg.awg_setup()

dig4450.digitizer_read_settings()
dig4450.digitizer_number_of_averages(AVERAGES)
time_res = int( 1000 / int(dig4450.digitizer_sample_rate().split(' ')[0]) )
# a full oscillogram will be transfered
wind = dig4450.digitizer_number_of_points()
points = int( (end_freq_num - start_freq_num) / STEP ) + 1
data = np.zeros( (points, wind) )

# initialize the power
###mw.mw_bridge_synthesizer( start_freq_num )

# Data saving
header = 'Date: ' + str(datetime.datetime.now().strftime("%d-%m-%Y %H-%M-%S")) + '\n' + \
         'Tune; AWG\n' + str(mw.mw_bridge_att1_prd()) + '\n' + \
          str(mw.mw_bridge_att2_prd()) + '\n' + str(mw.mw_bridge_att_prm()) + '\n' + str(mw.mw_bridge_synthesizer()) + '\n' + \
          'Repetition Rate: ' + str(pb.pulser_repetition_rate()) + '\n' + 'Number of Scans: ' + str(SCANS) + '\n' +\
          'Averages: ' + str(AVERAGES) + '\n' + 'Start Frequency of AWG Sine: ' + START_FREQ + '\n' \
          + 'End Frequency of AWG Sine: ' + END_FREQ + '\n' + 'Window: ' + str(wind * time_res) + ' ns\n' \
          + 'Horizontal Resolution: ' + str(time_res) + ' ns\n' + 'Vertical Resolution: ' + str(STEP) + ' MHz\n' + \
          'Temperature: ' + str(ptc10.tc_temperature('2A')) + ' K\n' +\
          'Pulse List: ' + '\n' + str(pb.pulser_pulse_list()) + 'AWG Pulse List: ' + '\n' +\
          str(awg.awg_pulse_list()) + '2D Data'

file_data, file_param = file_handler.create_file_parameters('.param')
file_handler.save_header(file_param, header = header, mode = 'w')

for j in general.scans(SCANS):
    i = 0
    freq = start_freq_num

    while freq <= end_freq_num:
        
        awg.awg_update()

        x_axis, x, y = dig4450.digitizer_get_curve( )

        data[i] = ( data[i] * (j - 1) + x ) / j

        process = general.plot_2d(EXP_NAME, np.transpose( data ), start_step = ( (0, time_res), (start_freq_num*1000000, STEP*1000000) ), xname = 'Time',\
            xscale = 's', yname = 'Frequency', yscale = 'Hz', zname = 'Intensity', zscale = 'V', pr = process, text = 'Scan / Frequency: ' + \
            str(j) + ' / '+ str(freq) )

        awg.awg_stop()
        freq = round( (STEP + freq), 3 )

        awg.awg_redefine_frequency(name = 'P3', freq = str( int( freq ) ) + ' MHz')
        i += 1

    awg.awg_pulse_reset()

dig4450.digitizer_stop()
dig4450.digitizer_close()
awg.awg_stop()
awg.awg_close()
pb.pulser_stop()

file_handler.save_data(file_data, data, header = header, mode = 'w')