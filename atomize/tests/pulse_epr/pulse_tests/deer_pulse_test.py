import time
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.PB_ESR_500_pro as pb_pro

cycle_data = np.zeros(200)
cycle_data_y = np.zeros(200)
data = np.zeros(200)
data_y = np.zeros(200)
x_axis = np.arange(0, 800, 4)
FIELD = 3473
AVERAGES = 400

pb = pb_pro.PB_ESR_500_Pro()

#PROBE
pb.pulser_pulse(name = 'P0', channel = 'MW', start = '2100 ns', length = '16 ns', phase_list = ['+x', '-x'])
pb.pulser_pulse(name = 'P1', channel = 'MW', start = '2440 ns', length = '32 ns', delta_start = '8 ns', phase_list = ['+x', '+x'])
pb.pulser_pulse(name = 'P2', channel = 'MW', start = '3780 ns', length = '32 ns', delta_start = '16 ns', phase_list = ['+x', '+x'])

#PUMP
pb.pulser_pulse(name = 'P3', channel = 'AWG', start = '2680 ns', length = '20 ns', delta_start = '4 ns')
pb.pulser_pulse(name = 'P4', channel = 'TRIGGER_AWG', start = '100 ns', length = '20 ns', delta_start = '4 ns')

#DETECTION
pb.pulser_pulse(name = 'P5', channel = 'TRIGGER', start = '4780 ns', length = '100 ns', delta_start = '16 ns')


pb.pulser_repetitoin_rate('1000 Hz')

#pb.pulser_update()
#pb.pulser_visualize()

k = 1 
while k < 9:
	
    j = 0
    while j < k:
        pb.pulser_shift('P1', 'P2', 'P3', 'P4', 'P5')
        pb.pulser_shift('P3', 'P4')
        pb.pulser_shift('P3', 'P4')
        pb.pulser_shift('P3', 'P4')

        j += 1

    general.wait('2 s')
    pb.pulser_visualize()


    if k % 2 == 1:
        general.message('HERE')
        pb.pulser_next_phase()
    elif k % 2 == 0:
        general.message('THERE')
        pb.pulser_next_phase()
        pb.pulser_next_phase()

    i = 0
    while i < 200:

        pb.pulser_update()
        pb.pulser_shift('P3','P4')
        pb.pulser_visualize()
        general.wait('200 ms')
        i += 1

    general.plot_1d('DEER_All', x_axis, data, xname = 'Delay',\
        xscale = 'ns', yname = 'Area', yscale = 'V*s', timeaxis = 'False', label = 'X')
    general.plot_1d('DEER_All', x_axis, data_y, xname = 'Delay',\
        xscale = 'ns', yname = 'Area', yscale = 'V*s', timeaxis = 'False', label = 'Y')
    
    pb.pulser_reset()


    k += 1


pb.pulser_stop()