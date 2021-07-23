import sys
import time
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.Keysight_3000_Xseries as t3034
import atomize.device_modules.Mikran_X_band_MW_bridge as mwBridge
import atomize.device_modules.PB_ESR_500_pro as pb_pro
#import atomize.general_modules.csv_opener_saver_tk_kinter as openfile

### Experimental parameters
data = []
START_FREQ = 9600
END_FREQ = 9900
STEP = 1
CYCLES = 1
AVERAGES = 400
###

#open1d = openfile.Saver_Opener()
pb = pb_pro.PB_ESR_500_Pro()
mw = mwBridge.Mikran_X_band_MW_bridge()
t3034 = t3034.Keysight_3000_Xseries()

t3034.oscilloscope_acquisition_type('Average')
t3034.oscilloscope_trigger_channel('CH1')
t3034.oscilloscope_record_length(1000)
#tb = t3034.oscilloscope_time_resolution()
t3034.oscilloscope_stop()

t3034.oscilloscope_number_of_averages(AVERAGES)

# setting pulses:
pb.pulser_pulse(name ='P0', channel = 'TRIGGER', start = '0 ns', length = '100 ns')
pb.pulser_pulse(name ='P1', channel = 'MW', start = '100 ns', length = '100 ns')

pb.pulser_repetition_rate('600 Hz')
pb.pulser_update()

# initialize the power
mw.mw_bridge_synthesizer( START_FREQ )
#path_to_file = open1d.create_file_dialog(directory = '')

start = START_FREQ
i = 0
while i < CYCLES:
    
    while start <= END_FREQ:
        
        start += STEP
        
        mw.mw_bridge_synthesizer( start )
        general.message(start)

        t3034.oscilloscope_start_acquisition()
        y = t3034.oscilloscope_get_curve('CH2')

        data.append(y)
        general.plot_2d('Tune Scan 2', data, start_step = ( (0, 1), (START_FREQ*1000000, STEP*1000000) ), xname = 'Time',\
            xscale = 's', yname = 'Frequency', yscale = 'Hz', zname = 'Intensity', zscale = 'V')

        #f = open(path_to_file,'a')
        #np.savetxt(f, y, fmt='%.10f', delimiter=' ', newline='\n', header='frequency: %d' % i, footer='', comments='#', encoding=None)
        #f.close()

    i += 1

mw.mw_bridge_synthesizer( START_FREQ )

pb.pulser_stop()