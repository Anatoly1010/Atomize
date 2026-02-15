import time
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.Tektronix_4000_Series as t4032

xs = []
ys = []
data = []

t4032 = t4032.Tektronix_4000_Series()

# Output tests
#general.message(t4032.oscilloscope_name())
#general.message(t4032.oscilloscope_define_window())
#general.message(t4032.oscilloscope_record_length())
#general.message(t4032.oscilloscope_acquisition_type())
#general.message(t4032.oscilloscope_number_of_averages())
#general.message(t4032.oscilloscope_timebase())
#general.message(t4032.oscilloscope_time_resolution())
#general.message(t4032.oscilloscope_sensitivity('CH1'))
#general.message(t4032.oscilloscope_offset('CH1'))
#general.message(t4032.oscilloscope_horizontal_offset())
#general.message(t4032.oscilloscope_coupling('CH1'))
#general.message(t4032.oscilloscope_impedance('CH1'))
#general.message(t4032.oscilloscope_trigger_mode())
#general.message(t4032.oscilloscope_trigger_channel())
#general.message(t4032.oscilloscope_trigger_low_level())


# Input tests
#t4032.oscilloscope_define_window(start=1,stop=10000)
#general.message(t4032.oscilloscope_define_window())

#t4032.oscilloscope_record_length(10000)
#general.message(t4032.oscilloscope_record_length())

#t4032.oscilloscope_acquisition_type('Average')
#general.message(t4032.oscilloscope_acquisition_type())

#t4032.oscilloscope_number_of_averages(16)
#general.message(t4032.oscilloscope_number_of_averages())

#t4032.oscilloscope_timebase('100 us')
#general.message(t4032.oscilloscope_timebase())

#t4032.oscilloscope_sensitivity('CH1', '200 mV')
#general.message(t4032.oscilloscope_sensitivity('CH1'))

#t4032.oscilloscope_offset('CH1', '100 mV')
#general.message(t4032.oscilloscope_offset('CH1'))

#t4032.oscilloscope_horizontal_offset('300 us')
#general.message(t4032.oscilloscope_horizontal_offset())

#t4032.oscilloscope_coupling('CH1', 'DC')
#general.message(t4032.oscilloscope_coupling('CH1'))

#t4032.oscilloscope_impedance('CH1', '50')
#general.message(t4032.oscilloscope_impedance('CH1'))

#t4032.oscilloscope_trigger_mode('Normal')
#general.message(t4032.oscilloscope_trigger_mode())

#t4032.oscilloscope_trigger_channel('CH2')
#general.message(t4032.oscilloscope_trigger_channel())

#t4032.oscilloscope_trigger_low_level('CH2' , '1 V')
#general.message(t4032.oscilloscope_trigger_low_level('CH2'))


#x = np.arange(5000)

#for i in range(4):
#    start_time = time.time()
#    t4032.oscilloscope_start_acquisition()
#    y = t4032.oscilloscope_get_curve('CH1')
#    data.append(y)
#    general.plot_2d('Plot Z Test2', data, start_step=((0,1),(0.3,1)), xname='Time',\
#        xscale='s', yname='Magnetic Field', yscale='T', zname='Intensity', zscale='V')

#    general.message(str(time.time() - start_time))

#t4032.close_connection()

#general.message(str(time.time() - start_time))