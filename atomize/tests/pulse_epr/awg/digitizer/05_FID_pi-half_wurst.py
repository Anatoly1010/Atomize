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
import atomize.general_modules.csv_opener_saver as openfile

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
    file_handler.save_data(file_data, data, header = header, mode = 'w')
    sys.exit(0)

signal.signal(signal.SIGTERM, cleanup)

### Experimental parameters
START_FIELD = 3469
END_FIELD = 3479
FIELD_STEP = 1
AVERAGES = 10
SCANS = 1

# PULSES
REP_RATE = '500 Hz'
PULSE_1_LENGTH = '160 ns'
# 398 ns is delay from AWG trigger 1.25 GHz
# 494 ns is delay from AWG trigger 1.00 GHz
PULSE_1_START = '494 ns'
PULSE_SIGNAL_START = '594 ns'
PULSE_AWG_1_START = '0 ns'

# NAMES
EXP_NAME = 'FID_AWG'

# Setting pulses
pb.pulser_pulse(name = 'P0', channel = 'TRIGGER_AWG', start = '0 ns', length = '30 ns')

# For each awg_pulse; length should be longer than in awg_pulse
pb.pulser_pulse(name = 'P1', channel = 'AWG', start = PULSE_1_START, length = PULSE_1_LENGTH)

pb.pulser_pulse(name = 'P3', channel = 'TRIGGER', start = PULSE_SIGNAL_START, length = '100 ns')
awg.awg_pulse(name = 'P4', channel = 'CH0', func = 'WURST', frequency = ('0 MHz', '270 MHz'), phase = 0, \
            length = PULSE_1_LENGTH, sigma = PULSE_1_LENGTH, start = PULSE_AWG_1_START, n = 10, d_coef = 1)

pb.pulser_repetition_rate( REP_RATE )
pb.pulser_update()

awg.awg_sample_rate(1000)
awg.awg_clock_mode('External')
awg.awg_reference_clock(100)
awg.awg_channel('CH0', 'CH1')
awg.awg_card_mode('Single Joined')
awg.awg_setup()
awg.awg_update()

# Setting magnetic field
bh15.magnet_setup(START_FIELD, FIELD_STEP)
bh15.magnet_field(START_FIELD)

dig4450.digitizer_read_settings()
dig4450.digitizer_number_of_averages(AVERAGES)
time_res = int( 1000 / int(dig4450.digitizer_sample_rate().split(' ')[0]) )
# a full oscillogram will be transfered
wind = dig4450.digitizer_number_of_points()
POINTS = int( (END_FIELD - START_FIELD) / FIELD_STEP ) + 1
area_x = np.zeros(wind)
area_y = np.zeros(wind)
data = np.zeros( (2, int(wind), POINTS) )

# Data saving
header = 'Date: ' + str(datetime.datetime.now().strftime("%d-%m-%Y %H-%M-%S")) + '\n' + \
         'FID; AWG\n' + 'Start Field: ' + str(START_FIELD) + ' G \n' + 'End Field: ' + str(END_FIELD) + ' G \n' + \
         'Field Step: ' + str(FIELD_STEP) + ' G \n' + str(mw.mw_bridge_att1_prd()) + '\n' + \
          str(mw.mw_bridge_att2_prd()) + '\n' + str(mw.mw_bridge_att_prm()) + '\n' + str(mw.mw_bridge_synthesizer()) + '\n' + \
          'Repetition Rate: ' + str(pb.pulser_repetition_rate()) + '\n' + 'Number of Scans: ' + str(SCANS) + '\n' +\
          'Averages: ' + str(AVERAGES) + '\n' + '\n' + 'Window: ' + str(wind * time_res) + ' ns\n' \
          + 'Horizontal Resolution: ' + str(time_res) + ' ns\n' + 'Vertical Resolution: ' + str(FIELD_STEP) + ' G\n' \
          + 'Temperature: ' + str(ptc10.tc_temperature('2A')) + ' K\n' +\
          'Pulse List: ' + '\n' + str(pb.pulser_pulse_list()) + 'AWG Pulse List: ' + '\n' +\
          str(awg.awg_pulse_list()) + '2D Data'

file_data, file_param = file_handler.create_file_parameters('.param')
file_handler.save_header(file_param, header = header, mode = 'w')

# Data acquisition
for j in general.scans(SCANS):

    i = 0
    field = START_FIELD

    while field <= END_FIELD:

        bh15.magnet_field(field)
        x_axis, area_x, area_y = dig4450.digitizer_get_curve()
                
        data[0, :, i] = ( data[0, :, i] * (j - 1) + area_x ) / j
        data[1, :, i] = ( data[0, :, i] * (j - 1) + area_y ) / j

        general.plot_2d(EXP_NAME, data, start_step = ( (0, time_res), (0, FIELD_STEP) ), xname = 'Time',\
            xscale = 'ns', yname = 'Magnetic Field', yscale = 'G', zname = 'Intensity', zscale = 'V')
        general.text_label( EXP_NAME, "Scan / Time: ", str(j) + ' / '+ str(field) )

        field = round( (FIELD_STEP + field), 3 )
        i += 1

    bh15.magnet_field( START_FIELD )

    #awg.awg_pulse_reset()
    #pb.pulser_pulse_reset()

dig4450.digitizer_stop()
dig4450.digitizer_close()
awg.awg_stop()
awg.awg_close()
pb.pulser_stop()

file_handler.save_data(file_data, data, header = header, mode = 'w')
