import time
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.Tektronix_3000_Series as t3052c

xs = []
ys = []
data = []

t3052 = t3052c.Tektronix_3000_Series()

# Output tests
#general.message(t3052.oscilloscope_name())
#general.message(t3052.oscilloscope_define_window())
#general.message(t3052.oscilloscope_record_length())
#general.message(t3052.oscilloscope_acquisition_type())
#general.message(t3052.oscilloscope_number_of_averages())
#general.message(t3052.oscilloscope_timebase())
#general.message(t3052.oscilloscope_time_resolution())
#general.message(t3052.oscilloscope_sensitivity('CH1'))
#general.message(t3052.oscilloscope_offset('CH1'))
#general.message(t3052.oscilloscope_horizontal_offset())
#general.message(t3052.oscilloscope_coupling('CH1'))
#general.message(t3052.oscilloscope_impedance('CH1'))
#general.message(t3052.oscilloscope_trigger_mode())
#general.message(t3052.oscilloscope_trigger_channel())
#general.message(t3052.oscilloscope_trigger_low_level('CH2'))


# Input tests
#t3052.oscilloscope_define_window(start=1,stop=9000)
#general.message(t3052.oscilloscope_define_window())

#t3052.oscilloscope_record_length(10000)
#general.message(t3052.oscilloscope_record_length())

#t3052.oscilloscope_acquisition_type('Average')
#general.message(t3052.oscilloscope_acquisition_type())

#t3052.oscilloscope_number_of_averages(4)
#general.message(t3052.oscilloscope_number_of_averages())

#t3052.oscilloscope_timebase('100 us')
#general.message(t3052.oscilloscope_timebase())

#t3052.oscilloscope_sensitivity('CH1', '200 mV')
#general.message(t3052.oscilloscope_sensitivity('CH1'))

# position is in division!!! offset is in V
#t3052.oscilloscope_offset('CH1', '200 mV')
#general.message(t3052.oscilloscope_offset('CH1'))

#t3052.oscilloscope_horizontal_offset('300 us')
#general.message(t3052.oscilloscope_horizontal_offset())

#t3052.oscilloscope_coupling('CH1', 'DC')
#general.message(t3052.oscilloscope_coupling('CH1'))

#t3052.oscilloscope_impedance('CH1', '1 M')
#general.message(t3052.oscilloscope_impedance('CH1'))

#t3052.oscilloscope_trigger_mode('Auto')
#general.message(t3052.oscilloscope_trigger_mode())

#t3052.oscilloscope_trigger_channel('CH1')
#general.message(t3052.oscilloscope_trigger_channel())

#t3052.oscilloscope_trigger_low_level('CH1', '1 V')
#general.message(t3052.oscilloscope_trigger_low_level('CH1'))


#x = np.arange(5000)

#for i in range(4):
#    start_time = time.time()
#    t3052.oscilloscope_start_acquisition()
#    y = t3052.oscilloscope_get_curve('CH1')
#    data.append(y)
#    general.plot_2d('Plot Z Test2', data, start_step=((0,1),(0.3,1)), xname='Time',\
#        xscale='s', yname='Magnetic Field', yscale='T', zname='Intensity', zscale='V')

#    general.message(str(time.time() - start_time))

#t3052.close_connection()

#general.message(str(time.time() - start_time))