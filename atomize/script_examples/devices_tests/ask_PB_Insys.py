import time
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.PB_Insys as pb_pro
#import atomize.device_modules.PB_ESR_500_pro as pb_pro

# A possible use in an experimental script
pb = pb_pro.PB_Insys()
#pb = pb_pro.PB_ESR_500_Pro()
pb.pulser_pulse(name = 'P1', channel = 'MW', start = '0 ns', length = '16 ns')
pb.pulser_pulse(name = 'P2', channel = 'MW', start = '320 ns', length = '32 ns', delta_start = '96 ns') #, phase_list =  ['+x', '-x', '-y', '+y'])
pb.pulser_pulse(name = 'P4', channel = 'TRIGGER', start = '640 ns', length = '160 ns', delta_start = '192 ns')

pb.pulser_repetition_rate('200 Hz')
#pb.pulser_pulse(name = 'P5', channel = 'LASER_2', start = '1600 ns', length = '400 ns', delta_start = '4 ns')

pb.pulser_update()
general.wait('100 ms')
pb.pulser_visualize()

start_time = time.time()


i = 0
j = 0
k = 0
while i < 1:
    
    while j < 100:
        #rep_rate = str(j + 1) + ' Hz'
        #pb.pulser_repetition_rate( rep_rate )
        
        #pb.pulser_update()
        
        #while k < 4:
            
        #    general.wait('100 ms')
        #    pb.pulser_next_phase()
        #    pb.pulser_visualize()
        #    k += 1

        #
        pb.pulser_update()
        general.wait('20 ms')
        
        pb.pulser_visualize()
        
        #pb.pulser_update()
        #pb.pulser_visualize()
        pb.pulser_shift()
        general.wait('40 ms')
        
        j += 1
        k = 0
        #pb.pulser_reset()

    i += 1
    j = 0

    pb.pulser_reset()


general.message( str( time.time() - start_time ) )



"""
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

###pb.pulser_repetition_rate()

#general.message(str(time.time() - start_time))

#general.message( pb.pulser_pulse_list() )
#header = 'Pulse List: ' + '\n' + pb.pulser_pulse_list()  + ' Field, X, Y '
#file_handler.save_1D_dialog( ([1, 2, 3, 4], [2, 2, 2, 2], [4, 4, 4, 4]), header = header )

#j = 0 
#while j < 3:
    #general.message('J CYCLE: ' + str(j)) 
#    i = 0
#    while i < 25:
        #general.message('I: ')
#        pb.pulser_update()
#        pb.pulser_shift()
        ###pb.pulser_increment()
#        pb.pulser_visualize()
#        general.wait('1 s')
#        i += 1
    # '2 kHz'
    
#    pb.pulser_reset()
    #print(pb.pulse_array_init)
#    general.wait('1 s')
#    j += 1

###pb.pulser_stop()

#print( convertion_to_numpy(pulse_array_init) )
#pb_close()

"""