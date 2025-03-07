import time
import struct
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.Sibir_1 as nmr_gaussmeter
import atomize.device_modules.ITC_FC as itc

NMR_SIBIR = nmr_gaussmeter.Sibir_1()
itc_fc = itc.ITC_FC()

FIELD = 4000
itc_fc.magnet_field(FIELD)

#general.wait('10 s')
general.message("start")

NMR_SIBIR.gaussmeter_sensor_number(3)
NMR_SIBIR.gaussmeter_gain(23)
NMR_SIBIR.gaussmeter_points(10000)
NMR_SIBIR.gaussmeter_pulse_length(7.5)

#set_b0 = NMR_SIBIR.gaussmeter_search(2900,3100,5)
set_b0 = FIELD - 30

NMR_SIBIR.gaussmeter_number_of_averges(32)

G = []

t1 = time.time()
for i in range(50):
    NMR_SIBIR.gaussmeter_set_field(set_b0)
    FID , FFT , field , S_n = NMR_SIBIR.gaussmeter_field()
    if field == 0:
        pass
    else:
        G.append(field)
        set_b0 = field 
    general.message(i , field , S_n)
    general.plot_1d('FID', np.arange(len(FID)), FID)
    general.plot_1d('FIELD', np.arange(len(G)), G )
    general.plot_1d('FFT', np.arange(len(FFT)), FFT)
    

t2 = time.time()

general.message(t2 - t1)
general.message(np.mean(np.array(G)),np.std(np.array(G)))

