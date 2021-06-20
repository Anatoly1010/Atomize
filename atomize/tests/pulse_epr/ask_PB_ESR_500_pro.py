import time
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.PB_ESR_500_pro as pb_pro

# A possible use in an experimental script
pb = pb_pro.PB_ESR_500_Pro()



#pb.pulser_pulse(name ='P0', channel = 'MW', start = '200 ns', length = '100 ns')
#pb.pulser_pulse(name ='P1', channel = 'AMP_ON', start = '50 ns', length = '120 ns')
pb.pulser_pulse(name ='P2', channel = 'TRIGGER', start = '50 ns', length = '220 ns')


#pb.pulser_pulse(name ='P1', channel = 'MW', start = '430 ns', length = '400 ns', length_increment = '400 ns')
#pb.pulser_pulse(name ='P3', channel = 'TRIGGER', start = '0 ns', length = '100 ns')
#pb.pulser_pulse(name ='P3', channel = 'MW', start = '550 ns', length = '30 ns', delta_start = '10 ns')

pb.pulser_update()
pb.pulser_visualize()

#j = 0
#while j < 500:
    #rep_rate = str(j + 1) + ' Hz'
    #pb.pulser_repetitoin_rate( rep_rate )
#    pb.pulser_update()
    #pb.pulser_shift()
    #pb.pulser_visualize()
#    general.wait('0.5 s')
#    j += 1


#pb.pulser_stop()
