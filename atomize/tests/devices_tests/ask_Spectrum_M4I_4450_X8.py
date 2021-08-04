import time
import numpy as np
from math import pi
import atomize.general_modules.general_functions as general
#import atomize.device_modules.PB_ESR_500_pro as pb_pro
import atomize.device_modules.Spectrum_M4I_4450_X8 as spectrum

points = 128
data1_ave = np.zeros( points )
data2_ave = np.zeros( points )

#pb = pb_pro.PB_ESR_500_Pro()
#pb.pulser_pulse(name = 'P0', channel = 'TRIGGER_AWG', start = '0 ns', length = '100 ns')
#pb.pulser_repetition_rate('2000 Hz')
#pb.pulser_update()

# A possible use in an experimental script
dig = spectrum.Spectrum_M4I_4450_X8()

dig.digitizer_number_of_points( points )
dig.digitizer_setup()

start_time = time.time()
for i in range(4):

    xs, data1, data2 = dig.digitizer_get_curve()

    data1_ave = data1 + data1_ave
    data2_ave = data2 + data2_ave

general.message( str(time.time() - start_time) )

general.plot_1d('Buffer_test', xs, data1_ave / 4, label = 'ch0', xscale = 's', yscale = 'V')


#pb.pulser_stop()
dig.digitizer_close()