import sys
import time
import socket
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.Tektronix_4000_Series as t4032
import atomize.device_modules.Mikran_X_band_MW_bridge as mwBridge
import atomize.device_modules.PB_ESR_500_pro as pb_pro
#import atomize.general_modules.csv_opener_saver_tk_kinter as openfile

#open1d = openfile.Saver_Opener()
pb = pb_pro.PB_ESR_500_Pro()
mw = mwBridge.Mikran_X_band_MW_bridge()
t4032 = t4032.Tektronix_4000_Series()

# setting pulses:
pb.pulser_pulse(name ='P0', channel = 'TRIGGER', start = '0 ns', length = '100 ns')
pb.pulser_pulse(name ='P1', channel = 'MW', start = '100 ns', length = '100 ns')


pb.pulser_repetitoin_rate('500 Hz')
pb.pulser_update()

data = []
start_freq = 9632
end_freq = 9732
step = 1
cycles = 1

# initialize the power
mw.mw_bridge_synthesizer( str(start_freq) )

#path_to_file = open1d.create_file_dialog(directory = '')

#t4032.oscilloscope_record_length(1000)
t4032.oscilloscope_number_of_averages(20)

i = 0
while i < cycles:
    
    while start_freq <= end_freq:
        start_freq += 1

        mw.mw_bridge_synthesizer( str(start_freq) )
        general.message(str(start_freq))

        #general.wait('40 ms')
        t4032.oscilloscope_start_acquisition()

        y = t4032.oscilloscope_get_curve('CH2')
        data.append(y)

        general.plot_2d('Tune Scan', data, start_step = ( (0, 0.2), (start_freq, 0.001) ), xname = 'Time',\
            xscale = 'ns', yname = 'Frequency', yscale = 'GHz', zname = 'Intensity', zscale = 'V')

        #f = open(path_to_file,'a')
        #np.savetxt(f, y, fmt='%.10f', delimiter=' ', newline='\n', header='frequency: %d' % i, footer='', comments='#', encoding=None)
        #f.close()

    i += 1

pb.pulser_stop()