import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.Cryomagnetics_4G as ps4g

cm4g = ps4g.Cryomagnetics_4G()

# READ
#general.message(cm4g.magnet_power_supply_name())
#Cryomagnetics,4G,7161,1.48,281

#general.message(cm4g.magnet_power_supply_units())
#kG

#general.message(cm4g.magnet_power_supply_range())
# [ 40.  60.  85.  93. 100.]

#general.message(cm4g.magnet_power_supply_sweep_rate())
# [0.01  0.01  0.007 0.005 0.005 5.   ]

#general.message(cm4g.magnet_power_supply_voltage_limit())
#2.000V

#general.message(cm4g.magnet_power_supply_units())
#kG

#general.message(cm4g.magnet_power_supply_select_channel())
#'CH1

#general.message(cm4g.magnet_power_supply_low_sweep_limit())
#0.000kG

#general.message(cm4g.magnet_power_supply_upper_sweep_limit())
#0.500kG

#general.message(cm4g.magnet_power_supply_sweep())
#Standby

#general.message(cm4g.magnet_power_supply_mode())
#Manual

#general.message(cm4g.magnet_power_supply_current())
#0.000kG

#general.message(cm4g.magnet_power_supply_voltage())
#-0.002V

#general.message(cm4g.magnet_power_supply_magnet_voltage())
#0.000V

#general.message(cm4g.magnet_power_supply_persistent_heater())
#Off

#general.message(cm4g.magnet_power_supply_persistent_current())
#0.000kG

# WRITE
cm4g.magnet_power_supply_control_mode('Remote')


#cm4g.magnet_power_supply_range(40, 60, 85, 93)
#general.message(cm4g.magnet_power_supply_range())

#cm4g.magnet_power_supply_sweep_rate(0.01, 0.01, 0.007, 0.005, 0.005, 5.0)
#general.message(cm4g.magnet_power_supply_sweep_rate())

#cm4g.magnet_power_supply_voltage_limit(1)
#general.message(cm4g.magnet_power_supply_voltage_limit())

#cm4g.magnet_power_supply_units('G') #['A, 'G']
#general.message(cm4g.magnet_power_supply_units())

#cm4g.magnet_power_supply_select_channel('CH1') #['CH1', 'CH2']
#general.message(cm4g.magnet_power_supply_select_channel())

#cm4g.magnet_power_supply_low_sweep_limit(0.0)
#general.message(cm4g.magnet_power_supply_low_sweep_limit())

#cm4g.magnet_power_supply_upper_sweep_limit(2)
#general.message(cm4g.magnet_power_supply_upper_sweep_limit())



#cm4g.magnet_power_supply_sweep('Up')
#general.message(cm4g.magnet_power_supply_sweep())
#general.message(cm4g.magnet_power_supply_current())

#cm4g.magnet_power_supply_sweep('Zero')
#general.message(cm4g.magnet_power_supply_sweep())
#general.message(cm4g.magnet_power_supply_current())


cm4g.magnet_power_supply_control_mode('Local')