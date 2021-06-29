import time
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.PB_ESR_500_pro as pb_pro
import atomize.device_modules.Keysight_3000_Xseries as key
import atomize.device_modules.BH_15 as bh

### Experimental parameters
START_FIELD = 3359
END_FIELD = 3559
FIELD_STEP = 0.25
AVERAGES = 10

points = int((END_FIELD - START_FIELD)/FIELD_STEP)
data_x = np.zeros(points)
data_y = np.zeros(points)
x_axis = np.arange(START_FIELD/10000, END_FIELD/10000, FIELD_STEP/10000)
###

pb = pb_pro.PB_ESR_500_Pro()
bh15 = bh.BH_15()
t3034 = key.Keysight_3000_Xseries()

bh15.magnet_setup(START_FIELD, FIELD_STEP)

t3034.oscilloscope_trigger_channel('CH1')
#tb = t3034.oscilloscope_time_resolution()
t3034.oscilloscope_record_length(250)
t3034.oscilloscope_acquisition_type('Average')
t3034.oscilloscope_number_of_averages(AVERAGES)
t3034.oscilloscope_stop()

pb.pulser_pulse(name ='P0', channel = 'MW', start = '100 ns', length = '16 ns')
pb.pulser_pulse(name ='P1', channel = 'MW', start = '450 ns', length = '32 ns')
pb.pulser_pulse(name ='P2', channel = 'TRIGGER', start = '800 ns', length = '100 ns')

pb.pulser_repetitoin_rate('500 Hz')
pb.pulser_update()

i = 0
field = START_FIELD
while field <= END_FIELD:

    bh15.magnet_field(field)
    general.message( str(field) )

    t3034.oscilloscope_start_acquisition()
    area_x = t3034.oscilloscope_area('CH4')
    area_y = t3034.oscilloscope_area('CH3')

    data_x[i] = area_x
    data_y[i] = area_y

    general.plot_1d('Echo Detected Spectrum', x_axis, data_x, xname = 'Field',\
        xscale = 'T.', yname = 'Area', yscale = 'V*s', label = 'X')
    general.plot_1d('Echo Detected Spectrum', x_axis, data_y, xname = 'Field',\
        xscale = 'T.', yname = 'Area', yscale = 'V*s', label = 'Y')

    field += FIELD_STEP
    i += 1

bh15.magnet_field(START_FIELD)

pb.pulser_stop()
