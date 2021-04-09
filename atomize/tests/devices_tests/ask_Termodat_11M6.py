import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.Termodat_11M6 as td

tdat11m6 = td.Termodat_11M6()
#tdat11m6.tc_setpoint('1', '273')
#tdat11m6.tc_setpoint('1')
#tdat11m6.tc_sensor('1', 'On')
#general.message(tdat11m6.tc_sensor('1'))
tdat11m6.tc_proportional('2', 70.1)

general.message(tdat11m6.tc_proportional('2'))
general.message(tdat11m6.tc_derivative('2'))
general.message(tdat11m6.tc_integral('2'))

