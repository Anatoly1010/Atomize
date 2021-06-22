import time
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.PB_ESR_500_pro as pb_pro

pb = pb_pro.PB_ESR_500_Pro()


pb.pulser_pulse(name ='P0', channel = 'AWG', start = '346 ns', length = '16 ns')
pb.pulser_pulse(name ='P1', channel = 'MW', start = '100 ns', length = '32 ns')
pb.pulser_pulse(name ='P2', channel = 'TRIGGER_AWG', start = '700 ns', length = '100 ns')

pb.pulser_repetitoin_rate('10 Hz')

pb.pulser_update()
pb.pulser_visualize()


#i = 0
#for i in general.to_infinity():

#	pb.update()
#	pb.pulser_visualize()
#	general.wait('100 ms')
#	if i > 1000:
#		break
#		pb.pulser_stop()

pb.pulser_stop()
