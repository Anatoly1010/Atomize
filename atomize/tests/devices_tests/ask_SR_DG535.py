import time
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.SR_DG535 as dg

dg535 = dg.SR_DG535()

dg535.delay_generator_burst_count()
#general.message( dg535.delay_generator_burst_count() )

