import time
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.PB_ESR_500_pro as pb_pro

# A possible use in an experimental script
pb = pb_pro.PB_ESR_500_Pro()

pb.pulser_pulse(name ='P0', channel = 'MW', start = '100 ns', length = '20 ns', delta_start = '10 ns')
pb.pulser_pulse(name ='P1', channel = 'MW', start = '430 ns', length = '400 ns', length_increment = '400 ns')
pb.pulser_pulse(name ='P2', channel = 'TRIGGER', start = '0 ns', length = '20 ns')
#pb.pulser_pulse(name ='P3', channel = 'MW', start = '550 ns', length = '30 ns', delta_start = '10 ns')

start_time = time.time()

j = 0
while j < 10:
    rep_rate = str(j + 1) + ' Hz'
    pb.pulser_repetitoin_rate( rep_rate )
    pb.pulser_update()
    #pb.pulser_shift()
    pb.pulser_visualize()
    general.wait('1 s')
    j += 1



###pb.pulser_repetitoin_rate()

general.message(str(time.time() - start_time))

###j = 0 
###while j < 3:
    #general.message('J CYCLE: ' + str(j)) 
    ###i = 0
    ###while i < 4:
        #general.message('I: ')
        ###pb.pulser_update()
        #pb.pulser_shift('P1')
        ###pb.pulser_increment()
        ###pb.pulser_visualize()
        ###general.wait('1 s')
        ###i += 1
    # '2 kHz'
    
    ###pb.pulser_reset()
    #print(pb.pulse_array_init)
    #general.wait('1 s')
    ###j += 1

###pb.pulser_stop()

#print( convertion_to_numpy(pulse_array_init) )
#pb_close()
