import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.ECC_15K as ecc


ecc15k = ecc.ECC_15K()

general.message(ecc15k.synthetizer_name())
ecc15k.synthetizer_command('OUTP 1')
ecc15k.synthetizer_frequency('9700 MHz')
#general.message(bh15.device_query('LE'))
