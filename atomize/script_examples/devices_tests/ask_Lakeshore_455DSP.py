import time
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.Lakeshore_455_DSP as dsp

xs = []
ys = []

dsp455 = dsp.Lakeshore_455_DSP()

# Output tests
#general.message(dsp455.gaussmeter_name())
#general.message(dsp455.gaussmeter_field())
#general.message(dsp455.gaussmeter_units())

# Input tests
#dsp455.gaussmeter_units('Tesla')
#general.message(dsp455.gaussmeter_units())


#Plot_xy Test
#for i in range(100):
#   start_time = time.time()
#    xs = np.append(xs, i);
#    ys = np.append(ys, dsp455.gaussmeter_field());
#    #ys = np.append(ys, np.random.randint(10,size=1));
#    general.plot_1d('Field', xs, ys, label='test data')
#    general.wait('300 ms')

#   general.message(str(time.time() - start_time))


#dsp455.close_connection()

