import time
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.PB_ESR_500_pro as pb_pro

# A possible use in an experimental script
pb = pb_pro.PB_ESR_500_Pro()

#pb.pulser_pulse(name = 'P0', channel = 'MW', start = '100 ns', length = '12 ns', delta_start = '100 ns', phase_list =  ['-y', '+x', '-x', '+x'])
pb.pulser_pulse(name = 'P0', channel = 'MW', start = '100 ns', length = '12 ns')
pb.pulser_pulse(name = 'P1', channel = 'MW', start = '220 ns', length = '24 ns', delta_start = '100 ns')
pb.pulser_pulse(name = 'P2', channel = 'TRIGGER', start = '340 ns', length = '100 ns', delta_start = '200 ns')
#pb.pulser_pulse(name = 'P3', channel = 'MW', start = '550 ns', length = '30 ns', delta_start = '10 ns')

start_time = time.time()
#i = 0
#j = 0
#while j < 2:
#    while i < 4:
#        general.wait('2 s')
#        pb.pulser_next_phase()
#        #pb.pulser_update()
#        pb.pulser_visualize()
#        i += 1
#    pb.pulser_shift()
#    i = 0
#    j += 1



#j = 0
#while j < 10:
    #rep_rate = str(j + 1) + ' Hz'
    #pb.pulser_repetitoin_rate( rep_rate )
    #pb.pulser_update()
    #pb.pulser_shift()
    #pb.pulser_visualize()
    #general.wait('1 s')
    #j += 1



###pb.pulser_repetitoin_rate()

#general.message(str(time.time() - start_time))

j = 0 
while j < 3:
    #general.message('J CYCLE: ' + str(j)) 
    i = 0
    while i < 25:
        #general.message('I: ')
        pb.pulser_update()
        pb.pulser_shift()
        ###pb.pulser_increment()
        pb.pulser_visualize()
        general.wait('1 s')
        i += 1
    # '2 kHz'
    
    pb.pulser_reset()
    #print(pb.pulse_array_init)
    general.wait('1 s')
    j += 1

###pb.pulser_stop()

#print( convertion_to_numpy(pulse_array_init) )
#pb_close()