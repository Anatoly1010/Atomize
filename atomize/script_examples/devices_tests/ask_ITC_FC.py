import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.ITC_FC as itc


itc_fc = itc.ITC_FC()

itc_fc.magnet_setup(100, 1)
#itc_fc.magnet_field(1000.0)

i = 0
while i < 50:

    a = float(itc_fc.magnet_field(0 + 100*i))
    general.message(itc_fc.magnet_field())
    i = i + 1

