import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.Scientific_Instruments_SCM10 as scm

scm10 = scm.Scientific_Instruments_SCM10()

general.message(scm10.tc_name())
general.message(scm10.tc_temperature('1'))
