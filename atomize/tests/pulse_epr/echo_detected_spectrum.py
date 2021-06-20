import time
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.PB_ESR_500_pro as pb_pro
import atomize.device_modules.Keysight_3000_Xseries as key
import atomize.device_modules.BH_15 as bh

data = []
START_FIELD = 3000
END_FIELD = 4000
FIELD_STEP = 2

pb = pb_pro.PB_ESR_500_Pro()
bh15 = bh.BH_15()
t3034 = key.Keysight_3000_Xseries()


t3034.oscilloscope_trigger_channel('Line')
t3034.oscilloscope_run()

tb = t3034.oscilloscope_time_resolution()
t3034.oscilloscope_record_length(1000)

t3034.oscilloscope_acquisition_type('Average')
t3034.oscilloscope_number_of_averages(10)
t3034.oscilloscope_trigger_channel('CH1')

t3034.oscilloscope_stop()

t3034.oscilloscope_number_of_averages(100)

bh15.magnet_setup(START_FIELD, FIELD_STEP)


pb.pulser_pulse(name ='P0', channel = 'MW', start = '100 ns', length = '16 ns')
pb.pulser_pulse(name ='P1', channel = 'MW', start = '220 ns', length = '32 ns')
pb.pulser_pulse(name ='P2', channel = 'TRIGGER', start = '240 ns', length = '100 ns')

pb.pulser_repetitoin_rate('200 Hz')

pb.pulser_update()

field = START_FIELD
while field <= END_FIELD:

	bh15.magnet_field(field)
	
	general.message( str(field) )

	t3034.oscilloscope_start_acquisition()
    data.append( t3034.oscilloscope_get_curve('CH4') )

    general.plot_2d('Echo Detected', data, start_step = ( (0, tb/1000000), (START_FIELD/10000, FIELD_STEP/10000) ), xname = 'Time',\
        xscale = 's', yname = 'Magnetic Field', yscale = 'T', zname = 'Intensity', zscale = 'V')

    field += FIELD_STEP


bh15.magnet_field(START_FIELD)
pb.pulser_stop()