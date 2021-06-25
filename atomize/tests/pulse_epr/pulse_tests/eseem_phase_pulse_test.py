import time
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.PB_ESR_500_pro as pb_pro

cycle_data = []
data = []

pb = pb_pro.PB_ESR_500_Pro()

pb.pulser_pulse(name = 'P0', channel = 'MW', start = '100 ns', length = '16 ns', phase_list = ['+x', '-x', '+x', '-x'])
pb.pulser_pulse(name = 'P1', channel = 'MW', start = '220 ns', length = '16 ns', phase_list = ['+x', '+x', '-x', '-x'])
pb.pulser_pulse(name = 'P2', channel = 'MW', start = '420 ns', length = '16 ns', delta_start = '100 ns', phase_list = ['+x', '+x', '+x', '+x'])
pb.pulser_pulse(name = 'P3', channel = 'TRIGGER', start = '540 ns', length = '100 ns', delta_start = '100 ns')

pb.pulser_repetitoin_rate('200 Hz')

for i in range(40):

    # phase cycle
    j = 0
    while j < 4:

        pb.pulser_next_phase()
        pb.pulser_visualize()
        general.wait('1 s')

        j += 1

    pb.pulser_shift()
    general.wait('1 s')
    
    cycle_data = []


#pb.pulser_stop()

