import time
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.ITC_503 as itc

xs = []
ys = []

itc503 = itc.ITC_503()

# Output tests
general.message(itc503.tc_name())
general.message(itc503.tc_setpoint())
general.message(itc503.tc_heater_power())
general.message(itc503.tc_state())
general.message(itc503.tc_sensor())
general.message(itc503.tc_gas_flow())
general.message(itc503.tc_lock_keyboard())

# Input tests
#general.message(itc503.tc_temperature(1))

#itc503.tc_setpoint(200)
#general.message(itc503.tc_setpoint())

#itc503.tc_heater_power(1.)
#general.message(itc503.tc_heater_power())

#itc503.tc_heater_power_limit(power)

#itc503.tc_state('Auto-Manual')
#general.message(itc503.tc_state())

#itc503.tc_sensor(2)
#general.message(itc503.tc_sensor())

#itc503.tc_lock_keyboard('Remote-Unlocked')
#general.message(itc503.tc_lock_keyboard())

#itc503.close_connection()