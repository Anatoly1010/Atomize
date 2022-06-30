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
POINTS = 501
STEP = 4           # in NS
FIELD = 3390
AVERAGES = 10
SCANS = 1
process = 'None'

# PULSES
REP_RATE = '10 Hz'
PULSE_1_LENGTH = '16 ns'
PULSE_2_LENGTH = '32 ns'
PULSE_1_START = '0 ns'
# 165000 is a constant shift between LASER TRIGGER 
# and the LASER output
PULSE_2_START = '165200 ns'
PULSE_3_START = '165500 ns'
PULSE_SIGNAL_START = '165800 ns'

# NAMES
EXP_NAME = 'ED Kinetics'
CURVE_NAME = 'exp1'

#
cycle_data_x = np.zeros( 2 )
cycle_data_y = np.zeros( 2 )
data_x = np.zeros(POINTS)
data_y = np.zeros(POINTS)
x_axis = np.linspace(0, (POINTS - 1)*STEP, num = POINTS)
###

file_handler = openfile.Saver_Opener()
ptc10 = sr.SR_PTC_10()
mw = mwBridge.Mikran_X_band_MW_bridge()
pb = pb_pro.PB_ESR_500_Pro()
bh15 = bh.BH_15()
###t3034 = key.Keysight_3000_Xseries()
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

dig4450.digitizer_read_settings()
dig4450.digitizer_number_of_averages(AVERAGES)
#tb = dig4450.digitizer_number_of_points() * int(  1000 / float( dig4450.digitizer_sample_rate().split(' ')[0] ) )
tb = dig4450.digitizer_window()

pb.pulser_pulse(name ='P0', channel = 'LASER', start = PULSE_1_START, length = '50 ns')
pb.pulser_pulse(name ='P1', channel = 'MW', start = PULSE_2_START, length = PULSE_1_LENGTH, phase_list = ['+x', '-x'], delta_start = str(int(STEP)) + ' ns')
pb.pulser_pulse(name ='P2', channel = 'MW', start = PULSE_3_START, length = PULSE_2_LENGTH, phase_list = ['+x', '+x'], delta_start = str(int(STEP)) + ' ns')
pb.pulser_pulse(name ='P3', channel = 'TRIGGER', start = PULSE_SIGNAL_START, length = '100 ns', delta_start = str(int(STEP)) + ' ns')

pb.pulser_repetition_rate( REP_RATE )
pb.pulser_update()

# Data saving
header = 'Date: ' + str(datetime.datetime.now().strftime("%d-%m-%Y %H-%M-%S")) + '\n' + \
         'Laser ED Kinetics; Phase Cycling\n' + 'Field: ' + str(FIELD) + ' G \n' + \
          str(mw.mw_bridge_att_prm()) + '\n' + str(mw.mw_bridge_att1_prd()) + '\n' + str(mw.mw_bridge_synthesizer()) + '\n' + \
          'Repetition Rate: ' + str(pb.pulser_repetition_rate()) + '\n' + 'Number of Scans: ' + str(SCANS) + '\n' +\
          'Averages: ' + str(AVERAGES) + '\n' + 'Points: ' + str(POINTS) + '\n' + 'Window: ' + str(tb) + ' ns\n' \
          + 'Temperature: ' + str(ptc10.tc_temperature('2A')) + ' K\n' +\
          'Pulse List: ' + '\n' + str(pb.pulser_pulse_list()) + 'Time (trig. delta_start), X (V*s), Y (V*s) '

file_data, file_param = file_handler.create_file_parameters('.param')
file_handler.save_header(file_param, header = header, mode = 'w')

# Data acquisition
for j in general.scans(SCANS):

    for i in range(POINTS):

        # phase cycle
        k = 0
        while k < 2:

            pb.pulser_next_phase()
            cycle_data_x[k], cycle_data_y[k] = dig4450.digitizer_get_curve( integral = True )
            k += 1

        # acquisition cycle [+, -]
        x, y = pb.pulser_acquisition_cycle(cycle_data_x, cycle_data_y, acq_cycle = ['+', '-'])
        data_x[i] = ( data_x[i] * (j - 1) + x ) / j
        data_y[i] = ( data_y[i] * (j - 1) + y ) / j

        process = general.plot_1d(EXP_NAME, x_axis, ( data_x, data_y ), xname = 'Delay',\
            xscale = 'ns', yname = 'Area', yscale = 'V*s', label = CURVE_NAME, pr = process, \
            text = 'Scan / Time: ' + str(j) + ' / '+ str(i*STEP))

        pb.pulser_shift()

    pb.pulser_pulse_reset()


dig4450.digitizer_stop()
dig4450.digitizer_close()
pb.pulser_stop()

file_handler.save_data(file_data, np.c_[x_axis, data_x, data_y], header = header, mode = 'w')
