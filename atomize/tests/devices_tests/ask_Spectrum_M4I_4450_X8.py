import time
import numpy as np
from math import pi
import atomize.general_modules.general_functions as general
#import atomize.device_modules.PB_ESR_500_pro as pb_pro
import atomize.device_modules.Spectrum_M4I_4450_X8 as spectrum
import atomize.math_modules.fft as FFT

fast_ft = FFT.Fast_Fourier()

POINTS = general.round_to_closest( 256, 16 )

#data1 = np.zeros( 10 )
#data2 = np.zeros( 10 )

data1 = np.zeros( POINTS )
data2 = np.zeros( POINTS )

ys = np.arange(0, POINTS, 1)
#pb = pb_pro.PB_ESR_500_Pro()
#pb.pulser_pulse(name = 'P0', channel = 'TRIGGER_AWG', start = '0 ns', length = '100 ns')
#pb.pulser_repetition_rate('2000 Hz')
#pb.pulser_update()

# A possible use in an experimental script
dig = spectrum.Spectrum_M4I_4450_X8()

dig.digitizer_number_of_points( POINTS )
dig.digitizer_card_mode('Average')
dig.digitizer_posttrigger( 16 )
dig.digitizer_number_of_averages(100)
#dig.digitizer_offset('CH0', 100)
#dig.digitizer_channel('CH0')
#dig.digitizer_sample_rate(320)
#dig.digitizer_trigger_channel('Software')
#dig.digitizer_trigger_mode('Negative')
#dig.digitizer_trigger_delay('100 ns')
#dig.digitizer_input_mode('Buffered')
#dig.digitizer_coupling('CH0', 'AC', 'CH1', 'AC')
#dig.digitizer_impedance('CH0', '1 M', 'CH1', '1 M')
#dig.digitizer_amplitude(200)

dig.digitizer_setup()


for i in range(100):
    start_time = time.time()

    #data1[i], data2[i] = dig.digitizer_get_curve(integral = True)
    xs, data1, data2 = dig.digitizer_get_curve()
    
    freq, data_real, data_im = fast_ft.fft( ys, data1, 5 )

    #xs, data1 = dig.digitizer_get_curve()
    general.message( str(time.time() - start_time) )

    general.plot_1d('Buffer_test', xs, data1 / 1, label = 'ch0', xscale = 's', yscale = 'V')
    general.plot_1d('FFT of buffer', np.sort( freq ), data_real / 1, label = 'ch1', xscale = 's', yscale = 'V')

    #data1_ave = data1 + data1_ave
    #data2_ave = data2 + data2_ave

    #dig.digitizer_stop()

#general.plot_1d('Buffer_test', xs, data2 / 1, label = 'ch0', xscale = 's', yscale = 'V')
#general.plot_1d('Buffer_test', xs, data1 / 1, label = 'ch1', xscale = 's', yscale = 'V')

#pb.pulser_stop()
dig.digitizer_close()