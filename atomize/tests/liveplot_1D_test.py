import time
import numpy as np
import atomize.general_modules.general_functions as general

start_time = time.time()

xs = np.arange(50);
#ys = np.zeros(15000);
#ys = np.random.rand(1,5000)

# Plot_xy Test
for i in range(3):
    ys = np.random.rand(1,50)
    #xs = np.append(xs, i);
    #ys = np.append(ys, np.random.randint(0, 10 + 1));
    #ys[i] = np.random.randint(0, 10 + 1);
    general.plot_1d('Plot XY Test', xs, ys[0], label='test data')
    #general.wait('2 ms')
    

#general.plot_remove('Plot XY Test')

# Append_y Test
#xs = np.linspace(0, 5, 1000)
#for i in range(1000):
#   start_time = time.time()
#   val = np.random.randint(0,10+1)
#   general.append_1d('Append Y Test', val, start_step=(xs[0], xs[1]-xs[0]), label='test data')
#   general.wait('100 ms')
#   general.message(str(time.time() - start_time))

general.message(str(time.time() - start_time))