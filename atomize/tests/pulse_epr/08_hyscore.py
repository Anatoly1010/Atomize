import time
import datetime
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.PB_ESR_500_pro as pb_pro
import atomize.device_modules.Keysight_3000_Xseries as key
import atomize.device_modules.Mikran_X_band_MW_bridge as mwBridge
import atomize.device_modules.BH_15 as bh
import atomize.device_modules.SR_PTC_10 as sr
import atomize.general_modules.csv_opener_saver_tk_kinter as openfile

### Experimental parameters
POINTS = 100
data = []
STEP = 100                  # in NS; delta_start = str(STEP) + ' ns' -> delta_start = '100 ns'
FIELD = 3473
AVERAGES = 200
###

# initialization of the devices
file_handler = openfile.Saver_Opener()
ptc10 = sr.SR_PTC_10()
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

pb.pulser_pulse(name = 'P0', channel = 'MW', start = '100 ns', length = '16 ns')
pb.pulser_pulse(name = 'P1', channel = 'MW', start = '220 ns', length = '16 ns')
pb.pulser_pulse(name = 'P2', channel = 'MW', start = '420 ns', length = '32 ns', delta_start = str(STEP) + ' ns')
pb.pulser_pulse(name = 'P3', channel = 'MW', start = '620 ns', length = '16 ns', delta_start = str(STEP) + ' ns')
pb.pulser_pulse(name = 'P4', channel = 'TRIGGER', start = '740 ns', length = '100 ns', delta_start = str(STEP) + ' ns')

pb.pulser_repetition_rate('200 Hz')

j = 0
while j < POINTS:

    i = 0
    while i < POINTS:

        pb.pulser_update()
        
        t3034.oscilloscope_start_acquisition()
        area = t3034.oscilloscope_area('CH4')
        data.append(area)

        pb.pulser_shift('P2', 'P3', 'P4')

        i += 1

    general.plot_2d('HYSCORE', data, start_step = ( (0, STEP/1000000000), (0, STEP/1000000000) ), xname = 'Time',\
        xscale = 's', yname = 'Delay Time', yscale = 's', zname = 'Intensity', zscale = 'V')

    pb.pulser_pulse_reset('P2', 'P3', 'P4')
    
    k = 0
    while k < (j + 1):
        pb.pulser_shift('P3', 'P4')

        k += 1

    j += 1

pb.pulser_stop()

# Data saving
header = 'Date: ' + str(datetime.datetime.now().strftime("%d-%m-%Y %H-%M-%S")) + '\n' + 'HYSCORE\n' + \
            'Field: ' + str(FIELD) + ' G \n' + str(mw.mw_bridge_att_prm()) + '\n' + \
            str(mw.mw_bridge_synthesizer()) + '\n' + \
           'Repetition Rate: ' + str(pb.pulser_repetition_rate()) + '\n' +\
           'Averages: ' + str(AVERAGES) + '\n' + 'Window: ' + str(t3034.oscilloscope_timebase()*1000) + ' ns\n' + \
           'Temperature: ' + str(ptc10.tc_temperature('2A')) + ' K\n' +\
           'Pulse List: ' + '\n' + str(pb.pulser_pulse_list()) + '2D Array of X '

file_handler.save_2D_dialog( data, header = header )

