import time
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.Planar_C2220 as c2220

C2220 = c2220.Planar_C2220()

#C2220.vector_analyzer_source_power(0, source = 1)
#general.message( C2220.vector_analyzer_source_power(source = 2) )

#C2220.vector_analyzer_frequency_center(CENTER, channel = 1)
##general.message( C2220.vector_analyzer_frequency_center(channel = 1) )

#C2220.vector_analyzer_frequency_span(SPAN, channel = 1)
#general.message( C2220.vector_analyzer_frequency_span(channel = 1) )

#C2220.vector_analyzer_points(POINTS, channel = 1)
#general.message( C2220.vector_analyzer_points(channel = 1) )

#C2220.vector_analyzer_if_bandwith('3000 Hz', channel = 1)
#general.message( C2220.vector_analyzer_if_bandwith(channel = 1) )

#C2220.vector_analyzer_trigger_source('BUS')
#general.message( C2220.vector_analyzer_trigger_source() )

#C2220.vector_analyzer_trigger_mode('SINGLE', channel = 1)
#C2220.vector_analyzer_send_trigger()
#general.message( C2220.vector_analyzer_trigger_mode(channel = 1) )

#general.message( C2220.vector_analyzer_get_freq_data(channel = 1) )
#general.message( C2220.vector_analyzer_get_data(s = 'S11', type = 'AP', channel = 1) )

#general.message( C2220.vector_analyzer_query("SENSe1:SWEep:CW:TIME?") )

# wait to measure
#general.wait('500 ms')
#xs = C2220.vector_analyzer_get_freq_data(channel = 1)
#y1, y2 = C2220.vector_analyzer_get_data(s = 'S11', type = 'AP', channel = 1)

#general.plot_1d('Ampl', xs, y1, xname = 'Freq', xscale = 'MHz', yname = 'Ampl', yscale = 'dB')
#general.plot_1d('Phase', xs, y2, xname = 'Freq', xscale = 'MHz', yname = 'Ph', yscale = 'deg')
#cent = f'{xs[np.argmin(y1)]} MHz'

