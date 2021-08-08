import time
import datetime
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.PB_ESR_500_pro as pb_pro
import atomize.device_modules.Keysight_3000_Xseries as key
import atomize.device_modules.Mikran_X_band_MW_bridge as mwBridge
import atomize.device_modules.SR_PTC_10 as sr
import atomize.device_modules.BH_15 as bh
import atomize.general_modules.csv_opener_saver_tk_kinter as openfile

### Experimental parameters
POINTS = 500
STEP = 4                  # in NS; delta_start = str(STEP) + ' ns' -> delta_start = '4 ns'
FIELD = 3472
AVERAGES = 500

# PULSES
REP_RATE = '600 Hz'
PULSE_1_LENGTH = '16 ns'
PULSE_2_LENGTH = '32 ns'
PULSE_1_START = '100 ns'
PULSE_2_START = '400 ns'
PULSE_SIGNAL_START = '700 ns'

#
data_x = np.zeros(POINTS)
data_y = np.zeros(POINTS)
x_axis = np.arange(0, POINTS*STEP, STEP)
###

# initialization of the devices
file_handler = openfile.Saver_Opener()
ptc10 = sr.SR_PTC_10()
mw = mwBridge.Mikran_X_band_MW_bridge()
pb = pb_pro.PB_ESR_500_Pro()
bh15 = bh.BH_15()
t3034 = key.Keysight_3000_Xseries()

# Setting magnetic field
bh15.magnet_setup(FIELD, 1)
bh15.magnet_field(FIELD)

# Setting oscilloscope
t3034.oscilloscope_trigger_channel('CH1')
t3034.oscilloscope_record_length(250)
t3034.oscilloscope_acquisition_type('Average')
t3034.oscilloscope_number_of_averages(AVERAGES)
t3034.oscilloscope_stop()

# Setting pulses
pb.pulser_pulse(name = 'P0', channel = 'MW', start = PULSE_1_START, length = PULSE_1_LENGTH)
pb.pulser_pulse(name = 'P1', channel = 'MW', start = PULSE_2_START, length = PULSE_2_LENGTH, delta_start = str(int(STEP/2)) + ' ns')
pb.pulser_pulse(name = 'P2', channel = 'TRIGGER', start = PULSE_SIGNAL_START, length = '100 ns', delta_start = str(STEP) + ' ns')

pb.pulser_repetition_rate( REP_RATE )

# Data acquisition
for i in range(POINTS):

    pb.pulser_update()

    t3034.oscilloscope_start_acquisition()  
    area_x = t3034.oscilloscope_area('CH4')
    area_y = t3034.oscilloscope_area('CH3')
    
    data_x[i] = area_x
    data_y[i] = area_y

    general.plot_1d('T2', x_axis, data_x, xname = 'Delay',\
        xscale = 'ns', yname = 'Area', yscale = 'V*s', label = 'X')
    general.plot_1d('T2', x_axis, data_y, xname = 'Delay',\
        xscale = 'ns', yname = 'Area', yscale = 'V*s', label = 'Y')

    pb.pulser_shift()
   
pb.pulser_stop()

# Data saving
header = 'Date: ' + str(datetime.datetime.now().strftime("%d-%m-%Y %H-%M-%S")) + '\n' + \
         'T2 Measurement\n' + 'Field: ' + str(FIELD) + ' G \n' + \
          str(mw.mw_bridge_att_prm()) + '\n' + str(mw.mw_bridge_synthesizer()) + '\n' + \
          'Repetition Rate: ' + str(pb.pulser_repetition_rate()) + '\n' + \
          'Averages: ' + str(AVERAGES) + '\n' + 'Window: ' + str(t3034.oscilloscope_timebase()*1000) + ' ns\n' \
          + 'Temperature: ' + str(ptc10.tc_temperature('2A')) + ' K\n' +\
          'Pulse List: ' + '\n' + str(pb.pulser_pulse_list()) + 'Time (trig. delta_start), X (V*s), Y (V*s) '

file_handler.save_1D_dialog( (x_axis, data_x, data_y), header = header )
