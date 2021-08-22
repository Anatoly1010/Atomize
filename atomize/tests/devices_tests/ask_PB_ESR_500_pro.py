import time
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.PB_ESR_500_pro as pb_pro
import atomize.general_modules.csv_opener_saver_tk_kinter as openfile


# A possible use in an experimental script
file_handler = openfile.Saver_Opener()
pb = pb_pro.PB_ESR_500_Pro()

#pb.pulser_pulse(name = 'P0', channel = 'MW', start = '100 ns', length = '12 ns', delta_start = '100 ns', phase_list =  ['-y', '+x', '-x', '+x'])
pb.pulser_pulse(name = 'P0', channel = 'MW', start = '0 ns', length = '16 ns', phase_list =  ['-x', '+x'])
pb.pulser_pulse(name = 'P1', channel = 'MW', start = '300 ns', length = '32 ns', phase_list =  ['+x', '+x'])
pb.pulser_pulse(name = 'P2', channel = 'TRIGGER', start = '600 ns', length = '100 ns', phase_list =  ['+x', '+x'])
#pb.pulser_pulse(name = 'P3', channel = 'MW', start = '550 ns', length = '30 ns', delta_start = '10 ns')

#pb.pulser_update()
#pb.pulser_visualize()
#general.wait('5 s')

#start_time = time.time()
i = 0
j = 0
while j < 2:
    while i < 2:
        pb.pulser_next_phase()
        #pb.pulser_update()
        pb.pulser_visualize()
        general.wait('1 s')
        i += 1
    pb.pulser_pulse_reset()
    i = 0
    j += 1



#j = 0
#while j < 10:
    #rep_rate = str(j + 1) + ' Hz'
    #pb.pulser_repetition_rate( rep_rate )
    #pb.pulser_update()
    #pb.pulser_shift()
    #pb.pulser_visualize()
    #general.wait('1 s')
    #j += 1



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
