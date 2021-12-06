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
import atomize.general_modules.csv_opener_saver as openfile

### Experimental parameters
FIELD_STEP = 2
FIELD_START = 3411
FIELD_END = 3501
AVERAGES = 10000
SCANS = 1
process = 'None'

# PULSES
REP_RATE = '10000 Hz'
PULSE_1_LENGTH = '16 ns'
PULSE_1_START = '0 ns'
PULSE_SIGNAL_START = '250 ns'

# NAMES
EXP_NAME = 'FID Trytil'
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
bh15.magnet_setup(FIELD_START, FIELD_STEP)
bh15.magnet_field(FIELD_START)
general.wait('5 s')

dig4450.digitizer_read_settings()
dig4450.digitizer_number_of_averages(AVERAGES)
time_res = int( 1000 / int(dig4450.digitizer_sample_rate().split(' ')[0]) )
# a full oscillogram will be transfered
wind = dig4450.digitizer_number_of_points()
cycle_data_x = np.zeros( (4, int(wind)) )
cycle_data_y = np.zeros( (4, int(wind)) )
POINTS = int( (FIELD_END - FIELD_START) / FIELD_STEP ) + 1
data = np.zeros( (8, int(wind), POINTS) )


# Setting pulses
pb.pulser_pulse(name = 'P0', channel = 'MW', start = PULSE_1_START, length = PULSE_1_LENGTH, phase_list = ['+x', '-x', '+y', '-y'])
pb.pulser_pulse(name = 'P1', channel = 'TRIGGER', start = PULSE_SIGNAL_START, length = '100 ns', phase_list = ['+x', '+x', '+x', '+x'])

pb.pulser_repetition_rate( REP_RATE )

# Data saving
header = 'Date: ' + str(datetime.datetime.now().strftime("%d-%m-%Y %H-%M-%S")) + '\n' + \
         'FID Trytil\n' + 'Field Start: ' + str(FIELD_START) + ' G \n' \
         + 'Field End: ' + str(FIELD_END) + ' G \n' + \
          str(mw.mw_bridge_att_prm()) + '\n' + str(mw.mw_bridge_synthesizer()) + '\n' + \
          'Repetition Rate: ' + str(pb.pulser_repetition_rate()) + '\n' + 'Number of Scans: ' + str(SCANS) + '\n' +\
          'Averages: ' + str(AVERAGES) + '\n' + 'Points: ' + str(POINTS) + '\n' + 'Window: ' + str(wind * time_res) + ' ns\n' \
          + 'Horizontal Resolution: ' + str(time_res) + ' ns\n' + 'Vertical Resolution: ' + str(FIELD_STEP) + ' G\n' \
          + 'Temperature: ' + str(ptc10.tc_temperature('2A')) + ' K\n' +\
          'Pulse List: ' + '\n' + str(pb.pulser_pulse_list()) + '2D Data'

file_data, file_param = file_handler.create_file_parameters('.param')
file_handler.save_header(file_param, header = header, mode = 'w')

# Data acquisition
for j in general.scans(SCANS):
    
    i = 0
    field = FIELD_START

    while field <= FIELD_END:

        bh15.magnet_field(field)
        general.wait('5 s')

        # phase cycle
        k = 0
        while k < 4:

            pb.pulser_next_phase()
            x_axis, cycle_data_x[k], cycle_data_y[k] = dig4450.digitizer_get_curve()

            k += 1

        # acquisition cycle [+]
        #x, y = pb.pulser_acquisition_cycle(cycle_data_x, cycle_data_y, acq_cycle = ['+'])

        data[0, :, i] = ( data[0, :, i] * (j - 1) + cycle_data_x[0] ) / j
        data[1, :, i] = ( data[1, :, i] * (j - 1) + cycle_data_y[0] ) / j

        data[2, :, i] = ( data[2, :, i] * (j - 1) + cycle_data_x[1] ) / j
        data[3, :, i] = ( data[3, :, i] * (j - 1) + cycle_data_y[1] ) / j

        data[4, :, i] = ( data[4, :, i] * (j - 1) + cycle_data_x[2] ) / j
        data[5, :, i] = ( data[5, :, i] * (j - 1) + cycle_data_y[2] ) / j

        data[6, :, i] = ( data[6, :, i] * (j - 1) + cycle_data_x[3] ) / j
        data[7, :, i] = ( data[7, :, i] * (j - 1) + cycle_data_y[3] ) / j
        
        process = general.plot_2d(EXP_NAME, data, start_step = ( (0, time_res), (FIELD_START, FIELD_STEP) ), xname = 'Time',\
            xscale = 'ns', yname = 'Field', yscale = 'G', zname = 'Intensity', zscale = 'V', pr = process, \
            text = 'Scan / Time: ' + str(j) + ' / '+ str(field))

        field = round( (FIELD_STEP + field), 3 )
        i += 1

        pb.pulser_pulse_reset()
    
    pb.pulser_pulse_reset()
    bh15.magnet_field(FIELD_START)

dig4450.digitizer_stop()
dig4450.digitizer_close()
pb.pulser_stop()

file_handler.save_data(file_data, data, header = header, mode = 'w')
