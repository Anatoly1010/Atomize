import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.Sibir_1 as nmr_gaussmeter

NMR_SIBIR = nmr_gaussmeter.Sibir_1()
general.message("start")

NMR_SIBIR.gaussmeter_sensor(3)
NMR_SIBIR.gaussmeter_gain(25)
NMR_SIBIR.gaussmeter_points(4500)
NMR_SIBIR.gaussmeter_pulse_length(6.75)
NMR_SIBIR.gaussmeter_number_of_averges(2048)
#set_b0 = NMR_SIBIR.gaussmeter_search(2900,3100,5)
G = []
set_b0 = 2999


NMR_SIBIR.gaussmeter_set_field(set_b0)
FID , FFI , field , S_n = NMR_SIBIR.gaussmeter_field()
if field == 0:
    pass
else:
    G.append(field)
    set_b0 = field 

M = []    
MM = []
for i in range(30):
    NMR_SIBIR.gaussmeter_pulse_length(3 + i/4)
    FID , FFI , field , S_n = NMR_SIBIR.gaussmeter_field()
    M.append(max(FFI))
    MM.append(3+i/4)
    general.message(i , field , S_n)
    general.plot_1d('len', np.arange(len(FID)), FID)
    general.plot_1d('len2', MM, M)
    general.plot_1d('len3', np.arange(len(FFI)), FFI)

#general.message(np.mean(np.array(G)),np.std(np.array(G)))

