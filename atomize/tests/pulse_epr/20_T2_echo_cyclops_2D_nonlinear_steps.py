import sys
import signal
import datetime
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.PB_ESR_500_pro as pb_pro
import atomize.device_modules.Spectrum_M4I_4450_X8 as spectrum
import atomize.device_modules.Mikran_X_band_MW_bridge as mwBridge
import atomize.device_modules.SR_PTC_10 as sr
import atomize.device_modules.BH_15 as bh
import atomize.general_modules.csv_opener_saver_tk_kinter as openfile

### Experimental parameters
POINTS = 101                                                   # 1 point
# create a nonlinear time axis
# the last delay is 72288 ns for 4.3; Please, note that the last element
# from the nonlinear_time array will not be used in the main cycle
# time axis used is goven by (2*np.insert(0 , 0, nonlinear_time))[:-1]
nonlinear_time_raw = 2 * 10 ** np.linspace( 0, 4.3, POINTS )
nonlinear_time = np.unique( general.numpy_round( nonlinear_time_raw, 2 ) ).astype(np.int64)
# the real number of points after rounding to 2 ns and removing repeated values
POINTS = len( nonlinear_time )

FIELD = 3440
AVERAGES = 4096
SCANS = 2
process = 'None'

# PULSES
REP_RATE = '1000 Hz'
PULSE_1_LENGTH = '22 ns'
PULSE_2_LENGTH = '44 ns'
PULSE_1_START = '0 ns'
PULSE_2_START = '130 ns'
PULSE_SIGNAL_START = '260 ns'
PHASE_CYCLE = 16

# NAMES
EXP_NAME = 'T2'
CURVE_NAME = 'exp1'

# initialization of the devices
file_handler = openfile.Saver_Opener()

def cleanup(*args):
    dig4450.digitizer_stop()
    dig4450.digitizer_close()
    pb.pulser_stop()
    file_handler.save_data(file_data, data, header = header, mode = 'w')
    sys.exit(0)

signal.signal(signal.SIGTERM, cleanup)

ptc10 = sr.SR_PTC_10()
mw = mwBridge.Mikran_X_band_MW_bridge()
pb = pb_pro.PB_ESR_500_Pro()
bh15 = bh.BH_15()
dig4450 = spectrum.Spectrum_M4I_4450_X8()

# Setting magnetic field
bh15.magnet_setup(FIELD, 0.01)
bh15.magnet_field(FIELD)

dig4450.digitizer_read_settings()
dig4450.digitizer_number_of_averages(AVERAGES)
time_res = int( 1000 / int(dig4450.digitizer_sample_rate().split(' ')[0]) )
# a full oscillogram will be transfered
wind = dig4450.digitizer_number_of_points()
cycle_data_x = np.zeros( (PHASE_CYCLE, int(wind)) )
cycle_data_y = np.zeros( (PHASE_CYCLE, int(wind)) )
data = np.zeros( (2, int(wind), POINTS) )

# Setting pulses
pb.pulser_pulse(name = 'P0', channel = 'MW', start = PULSE_1_START, length = PULSE_1_LENGTH, \
                phase_list = ['+x','+x','+x','+x','-x','-x','-x','-x','+y','+y','+y','+y','-y','-y','-y','-y'])
pb.pulser_pulse(name = 'P1', channel = 'MW', start = PULSE_2_START, length = PULSE_2_LENGTH, delta_start = str( nonlinear_time[0] ) + ' ns', \
                phase_list = ['+x','-x','+y','-y','+x','-x','+y','-y','+x','-x','+y','-y','+x','-x','+y','-y'])
pb.pulser_pulse(name = 'P2', channel = 'TRIGGER', start = PULSE_SIGNAL_START, length = '100 ns', delta_start = str( int(2 * nonlinear_time[0]) ) + ' ns')

pb.pulser_repetition_rate( REP_RATE )

# Data saving
header = 'Date: ' + str(datetime.datetime.now().strftime("%d-%m-%Y %H-%M-%S")) + '\n' + \
         'T2 Nonlinear Timescale\n' + 'Field: ' + str(FIELD) + ' G \n' +  \
          str(mw.mw_bridge_att_prm()) + '\n' + str(mw.mw_bridge_att1_prd()) + '\n' + str(mw.mw_bridge_synthesizer()) + '\n' + \
          'Repetition Rate: ' + str(pb.pulser_repetition_rate()) + '\n' + 'Number of Scans: ' + str(SCANS) + '\n' +\
          'Averages: ' + str(AVERAGES) + '\n' + 'Points: ' + str(POINTS) + '\n' + 'Window: ' + str(wind * time_res) + ' ns\n' \
          + 'Horizontal Resolution: ' + str(time_res) + ' ns\n' + 'Vertical Resolution: ' + str( (2*np.insert(nonlinear_time , 0, 0))[:-1] ) + ' ns\n' \
          + 'Temperature: ' + str(ptc10.tc_temperature('2A')) + ' K\n' +\
          'Pulse List: ' + '\n' + str(pb.pulser_pulse_list()) + '2D Data'

file_data, file_param = file_handler.create_file_parameters('.param')
file_handler.save_header(file_param, header = header, mode = 'w')

# Data acquisition
for j in general.scans(SCANS):

    for i in range(POINTS):

        # phase cycle
        k = 0
        while k < PHASE_CYCLE:

            pb.pulser_next_phase()
            x_axis, cycle_data_x[k], cycle_data_y[k] = dig4450.digitizer_get_curve()

            k += 1

        # acquisition cycle [+, -]
        x, y = pb.pulser_acquisition_cycle(cycle_data_x, cycle_data_y, acq_cycle = ['+','+','-','-','-','-','+','+','-i','-i','+i','+i','+i','+i','-i','-i'])

        data[0, :, i] = ( data[0, :, i] * (j - 1) + x ) / j
        data[1, :, i] = ( data[1, :, i] * (j - 1) + y ) / j

        process = general.plot_2d(EXP_NAME, data, start_step = ( (0, time_res), (0, 1) ), xname = 'Time',\
            xscale = 'ns', yname = 'Delay', yscale = 'ns', zname = 'Intensity', zscale = 'V', pr = process, \
            text = 'Scan / Point: ' + str(j) + ' / '+ str(i*1))

        # nonlinear_time_shift is calculated from the initial position of the pulses
        pb.pulser_pulse_reset()
        pb.pulser_redefine_delta_start(name = 'P1', delta_start = str( nonlinear_time[i] ) + ' ns')
        pb.pulser_redefine_delta_start(name = 'P2', delta_start = str( int(2 * nonlinear_time[i]) ) + ' ns')

        pb.pulser_shift()

    pb.pulser_pulse_reset()

dig4450.digitizer_stop()
dig4450.digitizer_close()
pb.pulser_stop()

file_handler.save_data(file_data, data, header = header, mode = 'w')
