import sys
import signal
import datetime
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.PB_ESR_500_pro as pb_pro
###import atomize.device_modules.Keysight_3000_Xseries as key
import atomize.device_modules.Spectrum_M4I_4450_X8 as spectrum
import atomize.device_modules.Mikran_X_band_MW_bridge as mwBridge
import atomize.device_modules.BH_15 as bh
import atomize.device_modules.SR_PTC_10 as sr
import atomize.general_modules.csv_opener_saver as openfile

### Experimental parameters
POINTS = 195
STEP = 2                  # in NS; length incremen = str(STEP) + ' ns' -> length incremen = '2 ns'
FIELD = 3473
AVERAGES = 1000
SCANS = 1
process = 'None'

# PULSES
REP_RATE = '500 Hz'
PULSE_1_LENGTH = '10 ns'
PULSE_2_LENGTH = '50 ns'
PULSE_3_LENGTH = '100 ns'
PULSE_1_START = '100 ns'
PULSE_2_START = '600 ns'
PULSE_3_START = '950 ns'
PULSE_SIGNAL_START = '1300 ns'

# NAMES
EXP_NAME = 'Nutation'
CURVE_NAME = 'exp1'

#
data_x = np.zeros(POINTS)
data_y = np.zeros(POINTS)
x_axis = np.linspace(10, (POINTS - 1)*STEP + 10, num = POINTS) # 10 is initial length of the pulse
###

# initialization of the devices
file_handler = openfile.Saver_Opener()
ptc10 = sr.SR_PTC_10()
mw = mwBridge.Mikran_X_band_MW_bridge()
pb = pb_pro.PB_ESR_500_Pro()
###t3034 = key.Keysight_3000_Xseries()
bh15 = bh.BH_15()
dig4450 = spectrum.Spectrum_M4I_4450_X8()

def cleanup(*args):
    dig4450.digitizer_stop()
    dig4450.digitizer_close()
    pb.pulser_stop()
    file_handler.save_data(file_data, np.c_[x_axis, data_x, data_y], header = header, mode = 'w')
    sys.exit(0)

signal.signal(signal.SIGTERM, cleanup)

bh15.magnet_setup(FIELD, 1)
bh15.magnet_field(FIELD)

###t3034.oscilloscope_trigger_channel('CH1')
###t3034.oscilloscope_record_length(250)
###t3034.oscilloscope_acquisition_type('Average')
###t3034.oscilloscope_number_of_averages(AVERAGES)
###t3034.oscilloscope_stop()

dig4450.digitizer_read_settings()
dig4450.digitizer_number_of_averages(AVERAGES)
#tb = dig4450.digitizer_number_of_points() * int(  1000 / float( dig4450.digitizer_sample_rate().split(' ')[0] ) )
tb = dig4450.digitizer_window()

pb.pulser_pulse(name = 'P0', channel = 'MW', start = PULSE_1_START, length = PULSE_1_LENGTH, length_increment = str(STEP) + ' ns')
pb.pulser_pulse(name = 'P1', channel = 'MW', start = PULSE_2_START, length = PULSE_2_LENGTH)
pb.pulser_pulse(name = 'P2', channel = 'MW', start = PULSE_3_START, length = PULSE_3_LENGTH)
pb.pulser_pulse(name = 'P3', channel = 'TRIGGER', start = PULSE_SIGNAL_START, length = '100 ns')

pb.pulser_repetition_rate( REP_RATE )

# Data saving
#str(t3034.oscilloscope_timebase()*1000)
header = 'Date: ' + str(datetime.datetime.now().strftime("%d-%m-%Y %H-%M-%S")) + '\n' + 'Nutation\n' + \
            'Field: ' + str(FIELD) + ' G \n' + str(mw.mw_bridge_att_prm()) + '\n' + \
            str(mw.mw_bridge_synthesizer()) + '\n' + \
           'Repetition Rate: ' + str(pb.pulser_repetition_rate()) + '\n' + 'Number of Scans: ' + str(SCANS) + '\n' +\
           'Averages: ' + str(AVERAGES) + '\n' + 'Points: ' + str(POINTS) + '\n' + 'Window: ' + str(tb) + ' ns\n' + \
           'Temperature: ' + str(ptc10.tc_temperature('2A')) + ' K\n' +\
           'Pulse List: ' + '\n' + str(pb.pulser_pulse_list()) + 'Time (pulse length_increment), X (V*s), Y (V*s) '

file_data, file_param = file_handler.create_file_parameters('.param')
file_handler.save_header(file_param, header = header, mode = 'w')

for j in general.scans(SCANS):

    for i in range(POINTS):

        pb.pulser_update()
        area_x, area_y = dig4450.digitizer_get_curve( integral = True )

        ###t3034.oscilloscope_start_acquisition()
        ###area_x = t3034.oscilloscope_area('CH4')
        ###area_y = t3034.oscilloscope_area('CH3')

        data_x[i] = ( data_x[i] * (j - 1) + area_x ) / j
        data_y[i] = ( data_y[i] * (j - 1) + area_y ) / j

        process = general.plot_1d(EXP_NAME, x_axis, ( data_x, data_y ), xname = 'Delay',\
            xscale = 'ns', yname = 'Area', yscale = 'V*s', label = CURVE_NAME, pr = process, \
            text = 'Scan / Time: ' + str(j) + ' / '+ str(i*STEP))

        pb.pulser_increment()

    pb.pulser_pulse_reset()

dig4450.digitizer_stop()
dig4450.digitizer_close()
pb.pulser_stop()

file_handler.save_data(file_data, np.c_[x_axis, data_x, data_y], header = header, mode = 'w')
