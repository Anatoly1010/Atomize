import time
import struct
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.Sibir_1 as nmr_gaussmeter

NMR_SIBIR = nmr_gaussmeter.Sibir_1()
general.message("start")

NMR_SIBIR.gaussmeter_sensor(3)
NMR_SIBIR.gaussmeter_gain(31)
NMR_SIBIR.gaussmeter_points(4500)
NMR_SIBIR.gaussmeter_pulse_length(6.5)
NMR_SIBIR.gaussmeter_number_of_averges(64)

set_b0 = NMR_SIBIR.gaussmeter_search(2900,3100,5)

NMR_SIBIR.gaussmeter_number_of_averges(256)

G = []
#set_b0 = 3000

t1 = time.time()
for i in range(500):
    NMR_SIBIR.gaussmeter_set_field(set_b0)
    FID , FFI , field , S_n = NMR_SIBIR.gaussmeter_field()
    if field == 0:
        pass
    else:
        G.append(field)
        set_b0 = field 
    general.message(i , field , S_n)
    general.plot_1d('pp', np.arange(len(FID)), FID)
    general.plot_1d('ppP', np.arange(len(G)), G)
    general.plot_1d('ppp', np.arange(len(FFI)), FFI)
    

t2 = time.time()

general.message(t2 - t1)
#general.message(G)

general.message(np.mean(np.array(G)),np.std(np.array(G)))

