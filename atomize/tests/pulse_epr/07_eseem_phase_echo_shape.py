import sys
import signal
import datetime
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.PB_ESR_500_pro as pb_pro
import atomize.device_modules.Spectrum_M4I_4450_X8 as spectrum
import atomize.device_modules.Mikran_X_band_MW_bridge as mwBridge
import atomize.device_modules.BH_15 as bh
import atomize.device_modules.SR_PTC_10 as sr
import atomize.general_modules.csv_opener_saver as openfile

### Experimental parameters
POINTS = 401
STEP = 10                  # in NS;
FIELD = 3389
AVERAGES = 50
SCANS = 1

# PULSES
REP_RATE = '1000 Hz'
PULSE_1_LENGTH = '16 ns'
PULSE_2_LENGTH = '16 ns'
PULSE_3_LENGTH = '16 ns'
PULSE_1_START = '0 ns'
PULSE_2_START = '300 ns'
PULSE_3_START = '356 ns'
PULSE_SIGNAL_START = '656 ns'

# NAMES
EXP_NAME = 'ESEEM Echo Shape'
CURVE_NAME = 'exp1'

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
    file_handler.save_data(file_data, data, header = header, mode = 'w')
    sys.exit(0)

signal.signal(signal.SIGTERM, cleanup)

bh15.magnet_setup(FIELD, 1)
bh15.magnet_field(FIELD)

dig4450.digitizer_read_settings()
dig4450.digitizer_number_of_averages(AVERAGES)
time_res = int( 1000 / int(dig4450.digitizer_sample_rate().split(' ')[0]) )
# a full oscillogram will be transfered
wind = dig4450.digitizer_number_of_points()
cycle_data_x = np.zeros( (4, int(wind)) )
cycle_data_y = np.zeros( (4, int(wind)) )
data = np.zeros( (2, int(wind), POINTS) )

pb.pulser_pulse(name = 'P0', channel = 'MW', start = PULSE_1_START, length = PULSE_1_LENGTH, phase_list = ['+x', '-x', '+x', '-x'])
# 208 ns between P0 and P1 is set according to modulation deep in ESEEM. Can be adjust using different delays;
pb.pulser_pulse(name = 'P1', channel = 'MW', start = PULSE_2_START, length = PULSE_2_LENGTH, phase_list = ['+x', '+x', '-x', '-x'])
pb.pulser_pulse(name = 'P2', channel = 'MW', start = PULSE_3_START, length = PULSE_3_LENGTH, delta_start = str(STEP) + ' ns', phase_list = ['+x', '+x', '+x', '+x'])
pb.pulser_pulse(name = 'P3', channel = 'TRIGGER', start = PULSE_SIGNAL_START, length = '100 ns', delta_start = str(STEP) + ' ns')

pb.pulser_repetition_rate( REP_RATE )

# Data saving
#str(t3034.oscilloscope_timebase()*1000)
#str(tb)
header = 'Date: ' + str(datetime.datetime.now().strftime("%d-%m-%Y %H-%M-%S")) + '\n' + 'ESEEM Echo Shape\n' + \
            'Field: ' + str(FIELD) + ' G \n' + str(mw.mw_bridge_att_prm()) + '\n' + \
            str(mw.mw_bridge_synthesizer()) + '\n' + \
           'Repetition Rate: ' + str(pb.pulser_repetition_rate()) + '\n' + 'Number of Scans: ' + str(SCANS) + '\n' +\
           'Averages: ' + str(AVERAGES) + '\n' + 'Points: ' + str(POINTS) + '\n' + 'Window: ' + str(wind * time_res) + ' ns\n' \
           + 'Horizontal Resolution: ' + str(time_res) + ' ns\n' + 'Vertical Resolution: ' + str(STEP) + ' ns\n' \
           'Temperature: ' + str(ptc10.tc_temperature('2A')) + ' K\n' +\
           'Pulse List: ' + '\n' + str(pb.pulser_pulse_list()) + '2D Data'

file_data, file_param = file_handler.create_file_parameters('.param')
file_handler.save_header(file_param, header = header, mode = 'w')


#j = 1
for j in general.scans(SCANS):
#while j <= SCANS:

    for i in range(POINTS):

        # phase cycle
        k = 0
        while k < 4:

            pb.pulser_next_phase()
            x_axis, cycle_data_x[k], cycle_data_y[k] = dig4450.digitizer_get_curve()
            
            k += 1
        
        # acquisition cycle [+, -, -, +]
        x, y = pb.pulser_acquisition_cycle(cycle_data_x, cycle_data_y, acq_cycle = ['+', '-', '-', '+'])

        data[0, :, i] = ( data[0, :, i] * (j - 1) + x ) / j
        data[1, :, i] = ( data[0, :, i] * (j - 1) + y ) / j

        general.plot_2d(EXP_NAME, data, start_step = ( (0, time_res), (0, STEP) ), xname = 'Time',\
            xscale = 'ns', yname = 'Delay', yscale = 'ns', zname = 'Intensity', zscale = 'V')
        general.text_label( EXP_NAME, "Scan / Time: ", str(j) + ' / '+ str(i*STEP) )

        pb.pulser_shift()

    #j += 1
    pb.pulser_pulse_reset()

dig4450.digitizer_stop()
dig4450.digitizer_close()
pb.pulser_stop()

file_handler.save_data(file_data, data, header = header, mode = 'w')
