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
bh15.magnet_setup(3473, 1)
bh15.magnet_field(3473)

# RESONATOR TUNING CHECK
#pb.pulser_pulse(name ='P0', channel = 'MW', start = '200 ns', length = '150 ns')
#pb.pulser_pulse(name ='P1', channel = 'TRIGGER', start = '100 ns', length = '100 ns')

# ECHO CHECK
pb.pulser_pulse(name ='P0', channel = 'MW', start = '600 ns', length = '16 ns')
pb.pulser_pulse(name ='P1', channel = 'MW', start = '800 ns', length = '32 ns')
pb.pulser_pulse(name ='P2', channel = 'TRIGGER', start = '1000 ns', length = '100 ns')

# ESEEM CHECK
#pb.pulser_pulse(name ='P0', channel = 'MW', start = '100 ns', length = '16 ns')
#pb.pulser_pulse(name ='P1', channel = 'MW', start = '470 ns', length = '16 ns')
# according to modulation deep in ESEEM. Can be adjust using different delays;
# a narrow acquisition window
#pb.pulser_pulse(name ='P2', channel = 'MW', start = '526 ns', length = '16 ns')
#pb.pulser_pulse(name ='P3', channel = 'TRIGGER', start = '896 ns', length = '100 ns')

pb.pulser_repetitoin_rate('200 Hz')

pb.pulser_update()
pb.pulser_visualize()

i = 0
for i in general.to_infinity():

    pb.pulser_update()
    #pb.pulser_visualize()
    
    general.wait('1 s')

    if i > 1000:
        break
        pb.pulser_stop()

pb.pulser_stop()
