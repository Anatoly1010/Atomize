import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.Owen_MK110_220_4DN_4R as owen

owen110 = owen.Owen_MK110_220_4DN_4R()

#owen110.discrete_io_input_counter('1')
#owen110.discrete_io_input_counter_reset('2')
#owen110.discrete_io_input_state()
#owen110.discrete_io_output_state()
owen110.discrete_io_output_state('1')

general.message(owen110.discrete_io_output_state())

