import time
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.general_modules.returned_thread as returnThread

prPlot = 'None'
POINTS = 50
STEP = 2

data_x = np.zeros(POINTS)
data_y = np.zeros(POINTS)
x_axis = np.linspace(0, (POINTS - 1)*STEP, num = POINTS) 

# Plot Test
for i in range(POINTS):

    # 1D
    data_x[i], data_y[i] = np.random.rand(1)[0], np.random.rand(1)[0]
    
    start_time = time.time()
    
    prWait = returnThread.rThread(target = general.wait, args=('150 ms', ), kwargs={})
    prWait.start()
    # Does not affect elapsed time, as it is less than “150 ms” in the wait function from the prWait
    general.wait('100 ms')

    prPlot = general.plot_1d('EXP1', x_axis, (data_x, data_y), label = 'test2', xname = 'Delay', \
            xscale = 'ns', yname = 'Area', yscale = 'V*s', vline = (STEP*i, ), pr = prPlot, text=str(STEP*i))
    prWait.join()

    general.message(str(time.time() - start_time))
