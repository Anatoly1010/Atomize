import time
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.SR_830 as sr

xs = []
ys = []

sr830 = sr.SR_830()

#general.message(sr830.lock_in_sensitivity())
general.message(sr830.lock_in_sensitivity())
#general.message(sr830.lock_in_get_data())
#sr860.lock_in_time_constant('1000 ms')
#i = 0

#while i < 6:
#   sr860.lock_in_ref_frequency(100000 + i*10000)
#   general.plot_1d('SR 860', xs, ys, label='test data')
#   general.wait('300 ms')
#   i += 1

#Plot_xy Test
#for i in range(100):
#   start_time = time.time()
#    xs = np.append(xs, i);
    #ys = np.append(ys, sr860.lock_in_get_data());
#    ys = np.append(ys, np.random.randint(10,size=1));
#    general.plot_1d('SR 860', xs, ys, label='test data')
#    general.wait('300 ms')

#   general.message(str(time.time() - start_time))


#sr.close_connection()


# Append_y Test
#for i in range(100):
#    start_time = time.time()
#    general.append_1d('Append Y Test', sr.lock_in_get_data(), start_step=(0, 1), label='test data')
#    general.wait('30 ms')

#    general.message(str(time.time() - start_time))


#sr.close_connection()