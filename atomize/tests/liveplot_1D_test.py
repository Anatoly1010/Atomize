import time
import numpy as np
from datetime import datetime
import atomize.general_modules.general_functions as general
#import atomize.general_modules.csv_opener_saver_tk_kinter as openfile
import atomize.general_modules.csv_opener_saver as openfile

file_handler = openfile.Saver_Opener()

xs = np.array([])
ys = np.array([])
ys2 = np.array([])
ys3 = np.array([])
ys4 = np.array([])

#xs = np.arange(50);
#ys = np.zeros(15000);
#ys = np.random.rand(1,5000)

# Plot_xy Test
for i in range(50):
    start_time = time.time()
    #ys = np.append(ys, np.random.rand(1,1))
    #ys2 = np.append(ys2, 1)
    #ys3 = np.append(ys3, np.random.rand(1,1))
    #ys4 = np.append(ys4, 0)
    #now = time.time()
    #timestamp = datetime.timestamp(now)
    #xs = np.append(xs, now)
    xs = np.append(xs, i)
    #general.message(xs)
    ys = np.append(ys, np.random.randint(0, 10 + 1));
    #ys[i] = np.random.randint(0, 10 + 1);
    general.plot_1d('Plot XY Test', xs, ys, label='test data2', timeaxis = 'False', vline = (0, i-1))
    #general.plot_1d('Plot XY Test', xs, ys2, label='test data2')
    #general.plot_1d('Plot XY Test', xs, ys3, label='test data3')
    #general.plot_1d('Plot XY Test', xs, ys4, label='test data4')
    general.wait('20 ms')
    general.message(str(time.time() - start_time))
    
file_handler.save_1D_dialog( (xs, ys), header = 'TEST' )

#general.plot_remove('Plot XY Test')

# Append_y Test
#xs = np.linspace(0, 5, 1000)
#xs = time.time()
#general.wait('1000 ms')
#xs2 = time.time()
#for i in range(1000):
#   start_time = time.time()
#    val = np.random.randint(0,10+1)
    #general.append_1d('Append Y Test', val, start_step=(xs[0], xs[1]-xs[0]), label='test data')
#    general.append_1d('Append Y Test', val, start_step=(xs, xs2 - xs), label='test data2', timeaxis = 'True')
#    general.wait('100 ms')
#   general.message(str(time.time() - start_time))
