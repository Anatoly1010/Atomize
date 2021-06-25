import time
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.PB_ESR_500_pro as pb_pro

data = []

pb = pb_pro.PB_ESR_500_Pro()

pb.pulser_pulse(name = 'P0', channel = 'MW', start = '100 ns', length = '16 ns')
pb.pulser_pulse(name = 'P1', channel = 'MW', start = '156 ns', length = '32 ns', delta_start = '2 ns')
pb.pulser_pulse(name = 'P3', channel = 'TRIGGER', start = '212 ns', length = '100 ns', delta_start = '4 ns')

pb.pulser_repetitoin_rate('200 Hz')

for i in range(40):
    pb.pulser_update()
    pb.pulser_visualize()
    general.wait('1 s')

    pb.pulser_shift()

#pb.pulser_stop()

