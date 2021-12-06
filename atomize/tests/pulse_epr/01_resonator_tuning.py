import sys
import signal
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.Keysight_3000_Xseries as t3034
import atomize.device_modules.Mikran_X_band_MW_bridge as mwBridge
import atomize.device_modules.PB_ESR_500_pro as pb_pro
#import atomize.general_modules.csv_opener_saver_tk_kinter as openfile
t3034 = t3034.Keysight_3000_Xseries()
pb = pb_pro.PB_ESR_500_Pro()
mw = mwBridge.Mikran_X_band_MW_bridge()

freq_before = int(str( mw.mw_bridge_synthesizer() ).split(' ')[1])

def cleanup(*args):
    mw.mw_bridge_synthesizer( freq_before )
    pb.pulser_stop()
    sys.exit(0)

signal.signal(signal.SIGTERM, cleanup)

### Experimental parameters
START_FREQ = 9300
END_FREQ = 9600
STEP = 1
SCANS = 1
AVERAGES = 100
process = 'None'

# PULSES
REP_RATE = '500 Hz'
PULSE_1_LENGTH = '100 ns'
PULSE_1_START = '0 ns'

# NAMES
EXP_NAME = 'Tune Scan'

# setting pulses:
pb.pulser_pulse(name ='P0', channel = 'TRIGGER', start = '0 ns', length = '100 ns')
pb.pulser_pulse(name ='P1', channel = 'MW', start = PULSE_1_START, length = PULSE_1_LENGTH)

pb.pulser_repetition_rate( REP_RATE )
pb.pulser_update()

#
t3034.oscilloscope_record_length( 1000 )
real_length = t3034.oscilloscope_record_length( )

points = int( (END_FREQ - START_FREQ) / STEP ) + 1
data = np.zeros( (points, real_length) )
###

#open1d = openfile.Saver_Opener()
t3034.oscilloscope_acquisition_type('Average')
t3034.oscilloscope_trigger_channel('CH1')
#t3034.oscilloscope_record_length( osc_rec_length )
#tb = t3034.oscilloscope_time_resolution()
t3034.oscilloscope_stop()

t3034.oscilloscope_number_of_averages(AVERAGES)

# initialize the power
mw.mw_bridge_synthesizer( START_FREQ )
#path_to_file = open1d.create_file_dialog(directory = '')

for j in general.scans(SCANS):
    i = 0
    freq = START_FREQ

    while freq <= END_FREQ:
        
        mw.mw_bridge_synthesizer( freq )

        t3034.oscilloscope_start_acquisition()
        y = t3034.oscilloscope_get_curve('CH2')

        data[i] = ( data[i] * (j - 1) + y ) / j

        process = general.plot_2d(EXP_NAME, np.transpose( data ), start_step = ( (0, 1), (START_FREQ*1000000, STEP*1000000) ), xname = 'Time',\
            xscale = 's', yname = 'Frequency', yscale = 'Hz', zname = 'Intensity', zscale = 'V', pr = process, text = 'Scan / Frequency: ' + \
            str(j) + ' / '+ str(freq) )

        #f = open(path_to_file,'a')
        #np.savetxt(f, y, fmt='%.10f', delimiter=' ', newline='\n', header='frequency: %d' % i, footer='', comments='#', encoding=None)
        #f.close()

        freq = round( (STEP + freq), 3 ) 
        i += 1

    mw.mw_bridge_synthesizer( START_FREQ )

mw.mw_bridge_synthesizer( freq_before )

pb.pulser_stop()
