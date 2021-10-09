import sys
import signal
import datetime
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.PB_ESR_500_pro as pb_pro
import atomize.device_modules.Spectrum_M4I_4450_X8 as spectrum_dig
import atomize.device_modules.Mikran_X_band_MW_bridge as mwBridge
import atomize.device_modules.BH_15 as bh
import atomize.device_modules.SR_PTC_10 as sr
import atomize.general_modules.csv_opener_saver as openfile

### Experimental parameters
POINTS = 15
STEP = 100                  # in NS; delta_start = str(STEP) + ' ns' -> delta_start = '100 ns'
FIELD = 3473
AVERAGES = 10
SCANS = 1

# PULSES
REP_RATE = '400 Hz'
PULSE_1_LENGTH = '16 ns'
PULSE_2_LENGTH = '16 ns'
PULSE_3_LENGTH = '32 ns'
PULSE_4_LENGTH = '16 ns'
PULSE_1_START = '0 ns'
PULSE_2_START = '300 ns'
PULSE_3_START = '500 ns'
PULSE_4_START = '700 ns'
PULSE_SIGNAL_START = '1000 ns'

# NAMES
EXP_NAME = 'HYSCORE'
CURVE_NAME = 'exp1'

# initialization of the devices
file_handler = openfile.Saver_Opener()
ptc10 = sr.SR_PTC_10()
mw = mwBridge.Mikran_X_band_MW_bridge()
pb = pb_pro.PB_ESR_500_Pro()
bh15 = bh.BH_15()
dig4450 = spectrum_dig.Spectrum_M4I_4450_X8()

def cleanup(*args):
    dig4450.digitizer_stop()
    dig4450.digitizer_close()
    pb.pulser_stop()
    file_handler.save_data(file_data, data, header = header, mode = 'w')
    sys.exit(0)

signal.signal(signal.SIGTERM, cleanup)

# Setting magnetic field
bh15.magnet_setup(FIELD, 1)
bh15.magnet_field(FIELD)

dig4450.digitizer_read_settings()
dig4450.digitizer_number_of_averages(AVERAGES)
wind = dig4450.digitizer_window()

#
cycle_data_x = np.zeros( 16 )
cycle_data_y = np.zeros( 16 )
data = np.zeros( (2, POINTS, POINTS) )
###

pb.pulser_pulse(name = 'P0', channel = 'MW', start = PULSE_1_START, length = PULSE_1_LENGTH, \
                phase_list = ['+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x'])
pb.pulser_pulse(name = 'P1', channel = 'MW', start = PULSE_2_START, length = PULSE_2_LENGTH, \
                phase_list = ['+x', '+x', '+x', '+x', '+y', '+y', '+y', '+y', '-x', '-x', '-x', '-x', '-y', '-y', '-y', '-y'])
pb.pulser_pulse(name = 'P2', channel = 'MW', start = PULSE_3_START, length = PULSE_3_LENGTH, \
                phase_list = ['+x', '+x', '-x', '-x', '+x', '+x', '-x', '-x', '+x', '+x', '-x', '-x', '+x', '+x', '-x', '-x'], delta_start = str(STEP) + ' ns')
pb.pulser_pulse(name = 'P3', channel = 'MW', start = PULSE_4_START, length = PULSE_4_LENGTH, \
                phase_list = ['+x', '-x', '+x', '-x', '+x', '-x', '+x', '-x', '+x', '-x', '+x', '-x', '+x', '-x', '+x', '-x'], delta_start = str(STEP) + ' ns')
pb.pulser_pulse(name = 'P4', channel = 'TRIGGER', start = PULSE_SIGNAL_START, length = '100 ns', \
                phase_list = ['+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x'], delta_start = str(STEP) + ' ns')

pb.pulser_repetition_rate( REP_RATE )

# Data saving
header = 'Date: ' + str(datetime.datetime.now().strftime("%d-%m-%Y %H-%M-%S")) + '\n' + 'HYSCORE\n' + \
            'Field: ' + str(FIELD) + ' G \n' + str(mw.mw_bridge_att_prm()) + '\n' + \
            str(mw.mw_bridge_synthesizer()) + '\n' + \
           'Repetition Rate: ' + str(pb.pulser_repetition_rate()) + '\n' + 'Number of Scans: ' + str(SCANS) + '\n' +\
           'Averages: ' + str(AVERAGES) + '\n' + 'Points: ' + str(POINTS) + '\n' + 'Window: ' + str(wind) + ' ns\n' \
           + 'Horizontal Resolution: ' + str(STEP) + ' ns\n' + 'Vertical Resolution: ' + str(STEP) + ' ns\n' + \
           'Temperature: ' + str(ptc10.tc_temperature('2A')) + ' K\n' +\
           'Pulse List: ' + '\n' + str(pb.pulser_pulse_list()) + '2D Data'

file_data, file_param = file_handler.create_file_parameters('.param')
file_handler.save_header(file_param, header = header, mode = 'w')

for j in general.scans(SCANS):

    l = 0
    for l in range(POINTS):
        for i in range(POINTS):

            # phase cycle
            k = 0        
            while k < 16:

                pb.pulser_next_phase()
                cycle_data_x[k], cycle_data_y[k] = dig4450.digitizer_get_curve( integral = True )
                k += 1
            
            # acquisition cycle
            x, y = pb.pulse_acquisition_cycle(cycle_data_x, cycle_data_y, \
                      acq_cycle = ['+', '-', '+', '-', '-i', '+i', '-i', '+i', '-', '+', '-', '+', '+i', '-i', '+i', '-i'])

            data[0, i, l] = ( data[0, i, l] * (j - 1) + x ) / j
            data[1, i, l] = ( data[0, i, l] * (j - 1) + y ) / j

            general.plot_2d(EXP_NAME, data, start_step = ( (0, STEP), (0, STEP) ), xname = 'Delay_1',\
                xscale = 'ns', yname = 'Delay_2', yscale = 'ns', zname = 'Intensity', zscale = 'V')
            general.text_label( EXP_NAME, "Scan / Time: ", str(j) + ' / '+ str(l*STEP) + ' / '+ str(i*STEP) )

            # Delay_1 scan
            pb.pulser_shift('P2', 'P3', 'P4')

        # Delay_2 change
        pb.pulser_pulse_reset('P2', 'P3', 'P4')
    
        ##pb.pulser_redefine_start(name = 'P3', start = str( int( PULSE_3_START.split(' ')[0] ) + ( l + 1 ) * STEP ) + ' ns')
        ##pb.pulser_redefine_start(name = 'P4', start = str( int( PULSE_4_START.split(' ')[0] ) + ( l + 1 ) * STEP ) + ' ns')
        d2 = 0
        while d2 < (l + 1):
            pb.pulser_shift('P3', 'P4')
            d2 += 1
    
    pb.pulser_pulse_reset()

dig4450.digitizer_stop()
dig4450.digitizer_close()
pb.pulser_stop()

file_handler.save_data(file_data, data, header = header, mode = 'w')
