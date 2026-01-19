import time
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.SR_DS345 as ds

ds345 = ds.SR_DS345()

general.message( ds345.wave_gen_name() )

#ds345.wave_gen_frequency('29 kHz')
#general.message( ds345.wave_gen_frequency() )

ds345.wave_gen_function('Arb')
#general.message( ds345.wave_gen_function() )

#ds345.wave_gen_amplitude('ECL')
#general.message( ds345.wave_gen_amplitude() )

#ds345.wave_gen_modulation_type('Burst')
#general.message( ds345.wave_gen_modulation_type() )

#ds345.wave_gen_modulation_function('Ramp')
#general.message( ds345.wave_gen_modulation_function() )

a_func = [0, 0, 0.5, 0.5, 1, 0.5, 0.5, 0, 0]
ds345.wave_gen_arbitrary_function_data(a_func)

