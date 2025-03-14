import sys
import signal
import datetime
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.Insys_FPGA as pb_pro
import atomize.device_modules.Mikran_X_band_MW_bridge_v2 as mwBridge
import atomize.device_modules.Lakeshore_335 as ls
import atomize.device_modules.ITC_FC as itc
import atomize.general_modules.csv_opener_saver_tk_kinter as openfile

### PARAMETERS
POINTS = 401
PHASES = 2
STEP = 6.4
FIELD = 3390
AVERAGES = 100
SCANS = 1

# PULSES
REP_RATE = '1000 Hz'
PULSE_1_LENGTH = '19.2 ns'
PULSE_2_LENGTH = '38.4 ns'
PULSE_1_START = '0 ns'
PULSE_2_START = '288 ns'
PULSE_SIGNAL_START = '576 ns'

# NAMES
EXP_NAME = 'T2'
CURVE_NAME = 'exp1'

# DATA
data = np.zeros( ( 2, POINTS ) )
x_axis = np.linspace(0, (POINTS - 1)*STEP, num = POINTS)
###

# INITIALIZATION
file_handler = openfile.Saver_Opener()
ls335 = ls.Lakeshore_335()
mw = mwBridge.Mikran_X_band_MW_bridge_v2()
pb = pb_pro.Insys_FPGA()
bh15 = itc.ITC_FC()

# TERMINATION
def cleanup(*args):
    pb.pulser_close()
    
    header = 'Date: ' + str(datetime.datetime.now().strftime("%d-%m-%Y %H-%M-%S")) + '\n' + \
         'T2 Measurement\n' + 'Field: ' + str(FIELD) + ' G \n' + \
          str(mw.mw_bridge_att_prm()) + '\n' + str(mw.mw_bridge_att2_prm()) + '\n' + str(mw.mw_bridge_att1_prd()) + '\n' + str(mw.mw_bridge_synthesizer()) + '\n' + \
          'Repetition Rate: ' + str(pb.pulser_repetition_rate()) + '\n' + 'Number of Scans: ' + str(j) + '\n' +\
          'Averages: ' + str(AVERAGES) + '\n' + 'Points: ' + str(POINTS) + '\n' + 'Window: ' + str(tb) + ' ns\n' \
          + 'Horizontal Resolution: ' + str(STEP) + ' ns\n' + 'Temperature: ' + str(ls335.tc_temperature('B')) + ' K\n' +\
          'Pulse List: ' + '\n' + str(pb.pulser_pulse_list()) + '2*Tau (ns), I (A.U.), Q (A.U.) '

    file_handler.save_header(file_param, header = header, mode = 'w')
    file_handler.save_data(file_data, np.c_[x_axis, data[0], data[1]], header = header, mode = 'w')

    sys.exit(0)

signal.signal(signal.SIGTERM, cleanup)

# EXPERIMENT
bh15.magnet_field(FIELD, calibration = 'True')
general.wait('4000 ms')

# read adc settings
adc_wind = pb.digitizer_read_settings()

# Setting pulses
pb.pulser_pulse(name = 'P0', channel = 'MW', start = PULSE_1_START, length = PULSE_1_LENGTH, phase_list = ['+x', '-x'])
pb.pulser_pulse(name = 'P1', channel = 'MW', start = PULSE_2_START, length = PULSE_2_LENGTH, delta_start = str(round(float(STEP / 2), 1)) + ' ns', phase_list = ['+x', '+x'])
pb.pulser_pulse(name = 'P2', channel = 'TRIGGER', start = PULSE_SIGNAL_START, length = adc_wind, delta_start = str(STEP) + ' ns')

pb.pulser_repetition_rate( REP_RATE )
pb.digitizer_number_of_averages(AVERAGES)
tb = pb.adc_window * 0.4 * pb.digitizer_decimation()

pb.pulser_open()

# Data saving
header = 'Date: ' + str(datetime.datetime.now().strftime("%d-%m-%Y %H-%M-%S")) + '\n' + \
         'T2 Measurement\n' + 'Field: ' + str(FIELD) + ' G \n' + \
          str(mw.mw_bridge_att_prm()) + '\n' + str(mw.mw_bridge_att2_prm()) + '\n' + str(mw.mw_bridge_att1_prd()) + '\n' + str(mw.mw_bridge_synthesizer()) + '\n' + \
          'Repetition Rate: ' + str(pb.pulser_repetition_rate()) + '\n' + 'Number of Scans: ' + str(SCANS) + '\n' +\
          'Averages: ' + str(AVERAGES) + '\n' + 'Points: ' + str(POINTS) + '\n' + 'Window: ' + str(tb) + ' ns\n' \
          + 'Horizontal Resolution: ' + str(STEP) + ' ns\n' + 'Temperature: ' + str(ls335.tc_temperature('B')) + ' K\n' +\
          'Pulse List: ' + '\n' + str(pb.pulser_pulse_list()) + '2*Tau (ns), I (A.U.), Q (A.U.) '

file_data, file_param = file_handler.create_file_parameters('.param')
file_handler.save_header(file_param, header = header, mode = 'w')

# Data acquisition
for j in general.scans(SCANS):

    for i in range(POINTS):

        # phase cycle
        for k in range(PHASES):

            pb.pulser_next_phase()
            data[0], data[1] = pb.digitizer_get_curve( POINTS, PHASES, acq_cycle = ['+x', '-x'], integral = True )

            general.plot_1d(EXP_NAME, x_axis, ( data[0], data[1] ), xname = '2*Tau',\
                    xscale = 'ns', yname = 'Area', yscale = 'A.U.', label = CURVE_NAME, \
                    text = 'Scan / Time: ' + str(j) + ' / ' + str(round(i*STEP, 1)))

        pb.pulser_shift()

    pb.pulser_pulse_reset()

pb.pulser_close()

file_handler.save_data(file_data, np.c_[x_axis, data[0], data[1]], header = header, mode = 'w')
