import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.Cryomagnetics_4G as ps4g

cm4g = ps4g.Cryomagnetics_4G()

# READ
#general.message(cm4g.magnet_power_supply_name())
#general.message(cm4g.magnet_power_supply_select_channel())
#general.message(cm4g.magnet_power_supply_units())
#general.message(cm4g.magnet_power_supply_range())
#general.message(cm4g.magnet_power_supply_sweep_rate())
#general.message(cm4g.magnet_power_supply_voltage_limit())
#general.message(cm4g.magnet_power_supply_low_sweep_limit())
#general.message(cm4g.magnet_power_supply_upper_sweep_limit())
#general.message(cm4g.magnet_power_supply_sweep())
#general.message(cm4g.magnet_power_supply_mode())
#general.message(cm4g.magnet_power_supply_current())
#general.message(cm4g.magnet_power_supply_voltage())
#general.message(cm4g.magnet_power_supply_magnet_voltage())
#general.message(cm4g.magnet_power_supply_persistent_heater())
#general.message(cm4g.magnet_power_supply_persistent_current())

# WRITE
#cm4g.magnet_power_supply_select_channel('CH1') #['CH1', 'CH2']
#general.message(cm4g.magnet_power_supply_select_channel())

#cm4g.magnet_power_supply_units('G') #['A, 'G']
#general.message(cm4g.magnet_power_supply_units())

#cm4g.magnet_power_supply_range(40, 60, 85, 93)
#general.message(cm4g.magnet_power_supply_range())

#cm4g.magnet_power_supply_sweep_rate(0.01, 0.01, 0.007, 0.005, 0.005, 5.0)
#general.message(cm4g.magnet_power_supply_sweep_rate())

#cm4g.magnet_power_supply_voltage_limit(1)
#general.message(cm4g.magnet_power_supply_voltage_limit())

#cm4g.magnet_power_supply_low_sweep_limit(1)
#general.message(cm4g.magnet_power_supply_low_sweep_limit())

#cm4g.magnet_power_supply_upper_sweep_limit(2)
#general.message(cm4g.magnet_power_supply_upper_sweep_limit())

#cm4g.magnet_power_supply_sweep('Up')
#general.message(cm4g.magnet_power_supply_sweep())
#general.message(cm4g.magnet_power_supply_current())

#cm4g.magnet_power_supply_sweep('Zero')
#general.message(cm4g.magnet_power_supply_sweep())
#general.message(cm4g.magnet_power_supply_current())
