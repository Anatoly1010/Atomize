import time
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.PB_ESR_500_pro as pb_pro
#import atomize.device_modules.Keysight_3000_Xseries as key
import atomize.device_modules.BH_15 as bh

pb = pb_pro.PB_ESR_500_Pro()
#t3034 = key.Keysight_3000_Xseries()
bh15 = bh.BH_15()
# FIELD SETTING
bh15.magnet_setup(3536, 1)
bh15.magnet_field(3526)

# RESONATOR TUNING CHECK
pb.pulser_pulse(name ='P0', channel = 'MW', start = '100 ns', length = '100 ns')
pb.pulser_pulse(name ='P1', channel = 'TRIGGER', start = '0 ns', length = '100 ns')

# ECHO CHECK
#pb.pulser_pulse(name ='P0', channel = 'MW', start = '100 ns', length = '16 ns')
#pb.pulser_pulse(name ='P1', channel = 'MW', start = '400 ns', length = '32 ns')
#pb.pulser_pulse(name ='P2', channel = 'TRIGGER', start = '700 ns', length = '100 ns')

# AWG CHECK
#pb.pulser_pulse(name ='P0', channel = 'AWG', start = '2680 ns', length = '90 ns')
#pb.pulser_pulse(name ='P1', channel = 'TRIGGER_AWG', start = '526 ns', length = '90 ns')
#pb.pulser_pulse(name ='P2', channel = 'TRIGGER', start = '100 ns', length = '100 ns')

# ESEEM CHECK
#pb.pulser_pulse(name ='P0', channel = 'MW', start = '100 ns', length = '16 ns')
#pb.pulser_pulse(name ='P1', channel = 'MW', start = '420 ns', length = '16 ns')
#pb.pulser_pulse(name ='P2', channel = 'MW', start = '476 ns', length = '16 ns')
#pb.pulser_pulse(name ='P3', channel = 'TRIGGER', start = '796 ns', length = '100 ns')

# DEER CHECK
#pb.pulser_pulse(name = 'P0', channel = 'MW', start = '2100 ns', length = '12 ns')
#pb.pulser_pulse(name = 'P1', channel = 'MW', start = '2440 ns', length = '24 ns')
#pb.pulser_pulse(name = 'P2', channel = 'MW', start = '3780 ns', length = '24 ns')
#PUMP
#pb.pulser_pulse(name = 'P3', channel = 'AWG', start = '3580 ns', length = '24 ns')
#pb.pulser_pulse(name = 'P4', channel = 'TRIGGER_AWG', start = '526 ns', length = '24 ns')
#DETECTION
#pb.pulser_pulse(name = 'P5', channel = 'TRIGGER', start = '4780 ns', length = '100 ns')


pb.pulser_repetition_rate('600 Hz')

pb.pulser_update()
#pb.pulser_visualize()

i = 0
for i in general.to_infinity():

    pb.pulser_update()
    #pb.pulser_visualize()
    
    general.wait('1000 ms')

    if i > 1000:
        break
        pb.pulser_stop()

pb.pulser_stop()
