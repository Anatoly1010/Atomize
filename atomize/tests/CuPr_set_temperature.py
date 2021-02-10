import time
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.Lakeshore_335 as ls

ls335 = ls.Lakeshore_335()

ls335.tc_setpoint(25)

general.message(ls335.tc_setpoint())

