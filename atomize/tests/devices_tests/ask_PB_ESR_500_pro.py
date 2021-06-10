import time
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.PB_ESR_500_pro as pb_pro

# A possible use in an experimental script
pb = pb_pro.PB_ESR_500_Pro()
#pb.pulser_pulse(name ='P0', channel = 'TRIGGER', start = '200 ns', length = '50 ns', delta_start = '10 ns')
pb.pulser_pulse(name ='P1',  channel = 'MW', start = '20 ns', length = '20 ns')
pb.pulser_pulse(name ='P2', channel = 'MW', start = '500 ns', length = '30 ns')

#pb.pulser_set_defense()

pb.pulser_repetitoin_rate('1 kHz')
###pb.pulser_repetitoin_rate()

###j = 0 
###while j < 3:
    #general.message('J CYCLE: ' + str(j)) 
    ###i = 0
    ###while i < 3:
        #general.message('I: ')
pb.pulser_update()
        ###pb.pulser_shift('P0')
        #pb.pulser_increment()
        
        ###i += 1
    # '2 kHz'
    
###    pb.pulser_reset()
    #print(pb.pulse_array_init)

###    j += 1

###pb.pulser_stop()

#print( convertion_to_numpy(pulse_array_init) )
#pb_close()
