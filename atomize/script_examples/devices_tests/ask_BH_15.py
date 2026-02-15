import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.BH_15 as bh


bh15 = bh.BH_15()

bh15.magnet_setup(2000, 10)
#general.message(bh15.device_write('SS175.000'))
#general.message(bh15.device_query('LE'))

i = 0
while i < 5:

    a = float(bh15.magnet_field(0 + 10*i))
    general.message(bh15.magnet_field())
    general.wait('200 ms')
    i = i + 1
    

#Plot_xy Test
#for i in range(1000):
#   start_time = time.time()
#   xs = np.append(xs, i);
#   ys = np.append(ys, sr.lock_in_get_data());
    #ys = np.append(ys, np.random.randint(10,size=1));
#   general.plot_1d('SR 860', xs, ys, label='test data')
#   general.wait('30 ms')

#   general.message(str(time.time() - start_time))


# Append_y Test
#for i in range(100):
#    start_time = time.time()
#    general.append_1d('Append Y Test', sr.lock_in_get_data(), start_step=(0, 1), label='test data')
#    general.wait('30 ms')

#    general.message(str(time.time() - start_time))


#sr.close_connection()