import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.Owen_MK110_220_4DN_4R as owen

owen110 = owen.Owen_MK110_220_4DN_4R()

#general.message(tdat11m6.tc_proportional('2'))
#general.message(tdat11m6.tc_derivative('2'))
owen110.discrete_io_output_state('1', 0)
general.message(owen110.discrete_io_input_counter('1'))

