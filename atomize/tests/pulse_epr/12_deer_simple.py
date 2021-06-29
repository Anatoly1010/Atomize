import time
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.PB_ESR_500_pro as pb_pro
import atomize.device_modules.Keysight_3000_Xseries as key
import atomize.device_modules.BH_15 as bh

### Experimental parameters
POINTS = 250
STEP = 4                    # delta_start for PUMP pulse
FIELD = 3466
AVERAGES = 1000

data_x = np.zeros(POINTS)
data_y = np.zeros(POINTS)
x_axis = np.arange(0, POINTS*STEP, STEP)
###

pb = pb_pro.PB_ESR_500_Pro()
t3034 = key.Keysight_3000_Xseries()
bh15 = bh.BH_15()

bh15.magnet_setup(FIELD, 1)
bh15.magnet_field(FIELD)

t3034.oscilloscope_trigger_channel('CH1')
#tb = t3034.oscilloscope_time_resolution()
t3034.oscilloscope_record_length(250)
t3034.oscilloscope_acquisition_type('Average')
t3034.oscilloscope_number_of_averages(AVERAGES)
t3034.oscilloscope_stop()

### DEER TUNING PROCEDURE
# 0. Searching of pump and observer frequency
# A resonator dip should be scanned using a standard echo sequence. The minimum and
# two (for pump and observer) more or less symmetrical frequencies should be found. 
# At each frequency we maximize the amplitude of the echo and memorize dB. 
# Note, that the resonance field changes with changing the frequency.
# 1. Optimizing PUMP pulse length
# At the pump frequency we should find a length of Pi pulse at 0-0.5 dB. The
# length should be the minimal available for 0-0.5 dB. Length is optimized using
# a standard echo sequence by maximizing the amplitude. 
# 2. Optimizing OBSERVER pulse length
# The same as 1 at observer frequency.
# 3. Oscilloscope integration window
# For this a 'constant' DEER sequence should be used.
#
# DO NOT FORGET TO RUN AWG
#

#PROBE
pb.pulser_pulse(name = 'P0', channel = 'MW', start = '2100 ns', length = '12 ns')
pb.pulser_pulse(name = 'P1', channel = 'MW', start = '2440 ns', length = '24 ns')
pb.pulser_pulse(name = 'P2', channel = 'MW', start = '3780 ns', length = '24 ns')
#PUMP
pb.pulser_pulse(name = 'P3', channel = 'AWG', start = '2680 ns', length = '30 ns', delta_start = '4 ns')
pb.pulser_pulse(name = 'P4', channel = 'TRIGGER_AWG', start = '526 ns', length = '30 ns', delta_start = '4 ns')
#DETECTION
pb.pulser_pulse(name = 'P5', channel = 'TRIGGER', start = '4780 ns', length = '100 ns')

pb.pulser_repetitoin_rate('1000 Hz')

#pb.pulser_update()
#pb.pulser_visualize()

i = 0
while i < POINTS:

    pb.pulser_update()

    t3034.oscilloscope_start_acquisition()
    area_x = t3034.oscilloscope_area('CH4')
    area_y = t3034.oscilloscope_area('CH3')

    data_x[i] = area_x
    data_y[i] = area_y

    pb.pulser_shift()

    general.plot_1d('DEER_Simple', x_axis, data_x, xname = 'Delay',\
        xscale = 'ns', yname = 'Area', yscale = 'V*s', label = 'X')
    general.plot_1d('DEER_Simple', x_axis, data_y, xname = 'Delay',\
        xscale = 'ns', yname = 'Area', yscale = 'V*s', label = 'Y')

    i += 1

pb.pulser_stop()

