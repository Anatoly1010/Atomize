import time
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.SR_DS345 as ds

ds345 = ds.SR_DS345()

general.message( ds345.wave_gen_name() )
