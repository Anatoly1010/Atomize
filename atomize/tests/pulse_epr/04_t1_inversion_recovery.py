import time
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.PB_ESR_500_pro as pb_pro
import atomize.device_modules.Keysight_3000_Xseries as key
import atomize.device_modules.Mikran_X_band_MW_bridge as mwBridge
import atomize.device_modules.BH_15 as bh
import atomize.general_modules.csv_opener_saver_tk_kinter as openfile

### Experimental parameters
POINTS = 500
STEP = 2                       # delta_start for TRIGGER pulse
FIELD = 3472
AVERAGES = 200

data_x = np.zeros(POINTS)
data_y = np.zeros(POINTS)
x_axis = np.arange(0, POINTS*STEP, STEP)
###

# initialization of the devices
file_handler = openfile.Saver_Opener()
mw = mwBridge.Mikran_X_band_MW_bridge()
pb = pb_pro.PB_ESR_500_Pro()
t3034 = key.Keysight_3000_Xseries()
bh15 = bh.BH_15()

bh15.magnet_setup(FIELD, 1)
bh15.magnet_field(FIELD)

t3034.oscilloscope_trigger_channel('CH1')
t3034.oscilloscope_record_length(250)
t3034.oscilloscope_acquisition_type('Average')
t3034.oscilloscope_number_of_averages(AVERAGES)
t3034.oscilloscope_stop()

pb.pulser_pulse(name = 'P0', channel = 'MW', start = '100 ns', length = '32 ns')
pb.pulser_pulse(name = 'P1', channel = 'MW', start = '400 ns', length = '16 ns', delta_start = '2 us')
pb.pulser_pulse(name = 'P2', channel = 'MW', start = '600 ns', length = '32 ns', delta_start = '2 us')
pb.pulser_pulse(name = 'P3', channel = 'TRIGGER', start = '800 ns', length = '100 ns', delta_start = '2 us')

# lower in comparison with T2
pb.pulser_repetitoin_rate('1000 Hz')

for i in range(POINTS):

    pb.pulser_update()

    t3034.oscilloscope_start_acquisition()
    area_x = t3034.oscilloscope_area('CH4')
    area_y = t3034.oscilloscope_area('CH3')
    
    data_x[i] = area_x
    data_y[i] = area_y

    general.plot_1d('T1', x_axis, data_x, xname = 'Delay',\
        xscale = 'us', yname = 'Area', yscale = 'V*s', label = 'X')

    general.plot_1d('T1', x_axis, data_y, xname = 'Delay',\
        xscale = 'us', yname = 'Area', yscale = 'V*s', label = 'Y')

    pb.pulser_shift()

# Data saving
header = 'Date: ' + str(datetime.now().strftime('%d-%m-%Y %H:%M:%S')) + '\n' +
         'T1 Inversion Recovery Measurement' +  
         'Field: ' + str(FIELD) + ' G \n' + 
          mw.mw_bridge_att_prm() + '\n' + 
          + mw.mw_bridge_synthesizer() + '\n' + 
         'Repetition Rate: ' + pb.pulser_repetitoin_rate() + '\n' +
         'Averages: ' + str(AVERAGES) + '\n' + 'Window: ' + str(t3034.oscilloscope_timebase()*1000) + 'ns \n' +
         'Pulse List: ' + '\n' + pb.pulser_pulse_list() + 'Time (trig. delta_start), X (V*s), Y (V*s) '

file_handler.save_1D_dialog( (x_axis, data_x, data_y), header = header )

pb.pulser_stop()

