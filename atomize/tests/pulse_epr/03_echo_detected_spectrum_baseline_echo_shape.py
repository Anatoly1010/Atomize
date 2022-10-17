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
import atomize.general_modules.csv_opener_saver_tk_kinter as openfile

### Experimental parameters
START_FIELD = 3370
END_FIELD = 3530
FIELD_STEP = 0.5
AVERAGES = 20
SCANS = 1
process = 'None'

# PULSES
REP_RATE = '500 Hz'
PULSE_1_LENGTH = '50 ns'
PULSE_2_LENGTH = '100 ns'
PULSE_1_START = '0 ns'
PULSE_2_START = '400 ns'
PULSE_SIGNAL_START = '800 ns'
PHASE_CYCLE = 2

# NAMES
EXP_NAME = 'ED Shape'

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
    file_handler.save_data(file_data, data, header = header, mode = 'w')
    sys.exit(0)

signal.signal(signal.SIGTERM, cleanup)

bh15.magnet_setup(START_FIELD, FIELD_STEP)

###t3034.oscilloscope_trigger_channel('CH1')
#tb = t3034.oscilloscope_time_resolution()
###t3034.oscilloscope_record_length(250)
###t3034.oscilloscope_acquisition_type('Average')
###t3034.oscilloscope_number_of_averages(AVERAGES)
###t3034.oscilloscope_stop()

dig4450.digitizer_read_settings()
dig4450.digitizer_number_of_averages(AVERAGES)
time_res = int( 1000 / int(dig4450.digitizer_sample_rate().split(' ')[0]) )
# a full oscillogram will be transfered
wind = dig4450.digitizer_number_of_points()

points = int( (END_FIELD - START_FIELD) / FIELD_STEP ) + 1
cycle_data_x = np.zeros( (PHASE_CYCLE, int(wind)) )
cycle_data_y = np.zeros( (PHASE_CYCLE, int(wind)) )
data = np.zeros( (2, int(wind), points) )


pb.pulser_pulse(name ='P0', channel = 'MW', start = PULSE_1_START, length = PULSE_1_LENGTH, phase_list = ['+x', '-x'])
#phase_list = ['+x','+x','+x','+x','-x','-x','-x','-x','+y','+y','+y','+y','-y','-y','-y','-y']
pb.pulser_pulse(name ='P1', channel = 'MW', start = PULSE_2_START, length = PULSE_2_LENGTH, phase_list = ['+x', '+x'])
#phase_list = ['+x','-x','+y','-y','+x','-x','+y','-y','+x','-x','+y','-y','+x','-x','+y','-y']
pb.pulser_pulse(name ='P2', channel = 'TRIGGER', start = PULSE_SIGNAL_START, length = '100 ns')

pb.pulser_repetition_rate( REP_RATE )
pb.pulser_update()

# Data saving
#str(t3034.oscilloscope_timebase()*1000)
header = 'Date: ' + str(datetime.datetime.now().strftime("%d-%m-%Y %H-%M-%S")) + '\n' + 'Echo Detected Spectrum; Echo Shape\n' + \
            'Start Field: ' + str(START_FIELD) + ' G \n' + 'End Field: ' + str(END_FIELD) + ' G \n' + \
            'Field Step: ' + str(FIELD_STEP) + ' G \n' + str(mw.mw_bridge_att_prm()) + '\n' + str(mw.mw_bridge_att1_prd()) + '\n' + \
            str(mw.mw_bridge_synthesizer()) + '\n' + \
           'Repetition Rate: ' + str(pb.pulser_repetition_rate()) + '\n' + 'Number of Scans: ' + str(SCANS) + '\n' +\
           'Averages: ' + str(AVERAGES) + '\n' + 'Points: ' + str(points) + '\n' + 'Window: ' + str(wind * time_res) + ' ns\n' + \
           'Horizontal Resolution: ' + str(time_res) + ' ns\n' + 'Vertical Resolution: ' + str(FIELD_STEP) + ' G\n' + \
           'Temperature: ' + str(ptc10.tc_temperature('2A')) + ' K\n' +\
           'Pulse List: ' + '\n' + str(pb.pulser_pulse_list()) + '2D Data'

file_data, file_param = file_handler.create_file_parameters('.param')
file_handler.save_header(file_param, header = header, mode = 'w')

for j in general.scans(SCANS):

    i = 0
    field = START_FIELD

    while field <= END_FIELD:

        bh15.magnet_field(field)

        # phase cycle
        k = 0
        while k < PHASE_CYCLE:

            pb.pulser_next_phase()
            x_axis, cycle_data_x[k], cycle_data_y[k] = dig4450.digitizer_get_curve()
            ###t3034.oscilloscope_start_acquisition()
            ###cycle_data_x[k] = t3034.oscilloscope_area('CH4')
            ###cycle_data_y[k] = t3034.oscilloscope_area('CH3')

            k += 1

        # acquisition cycle
        x, y = pb.pulser_acquisition_cycle(cycle_data_x, cycle_data_y, acq_cycle = ['+','-'])
        #acq_cycle = ['+','+','-','-','-','-','+','+','-i','-i','+i','+i','+i','+i','-i','-i']

        data[0, :, i] = ( data[0, :, i] * (j - 1) + x ) / j
        data[1, :, i] = ( data[1, :, i] * (j - 1) + y ) / j

        process = general.plot_2d(EXP_NAME, data, start_step = ( (0, time_res), (START_FIELD, FIELD_STEP) ), xname = 'Time',\
            xscale = 'ns', yname = 'Magnetic Field', yscale = 'G', zname = 'Intensity', zscale = 'V', pr = process, \
            text = 'Scan / Point: ' + str(j) + ' / '+ str(i*1))


        field = round( (FIELD_STEP + field), 3 )
        i += 1
        
        pb.pulser_pulse_reset()
    
    bh15.magnet_field(START_FIELD)


dig4450.digitizer_stop()
dig4450.digitizer_close()
pb.pulser_stop()

file_handler.save_data(file_data, data, header = header, mode = 'w')
