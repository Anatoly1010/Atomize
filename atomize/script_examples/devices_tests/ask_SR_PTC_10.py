import time
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.SR_PTC_10 as sr

xs = []
ys = []

ptc10 = sr.SR_PTC_10()

general.message(ptc10.tc_temperature('2A'))
general.message(ptc10.tc_temperature('3A'))
general.message( ptc10.tc_heater_power('Heater').split(' ')[0] )
