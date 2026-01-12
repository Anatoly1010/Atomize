import time
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.Rigol_MSO8000_Series as key

r8104 = key.Rigol_MSO8000_Series()

#general.message( r8104.oscilloscope_name() )

#r8104.oscilloscope_record_length(9999)
#general.message(r8104.oscilloscope_record_length())

#r8104.oscilloscope_acquisition_type('Average')
#general.message(r8104.oscilloscope_acquisition_type())

#r8104.oscilloscope_number_of_averages(10)
#general.message(r8104.oscilloscope_number_of_averages())

#r8104.oscilloscope_timebase('990 us')
#general.message(r8104.oscilloscope_timebase())

#general.message(r8104.oscilloscope_time_resolution())

#r8104.oscilloscope_stop()

#r8104.oscilloscope_run()

#general.message(r8104.oscilloscope_preamble('CH1'))

#r8104.oscilloscope_start_acquisition()
r8104.oscilloscope_run()
general.wait('50 ms')

y = r8104.oscilloscope_get_curve('CH1')
x = np.arange( len(y) )

general.plot_1d('1D', x, y, label = 'test', xname = 'Delay', \
            xscale = 's', yname = 'Area', yscale = 'V*s')