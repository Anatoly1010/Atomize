import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.IVG_1_1 as ivg

ivg11 = ivg.IVG_1_1()

general.message(ivg11.moisture_meter_moisture())


