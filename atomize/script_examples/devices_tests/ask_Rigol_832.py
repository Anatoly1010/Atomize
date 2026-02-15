import time
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.Rigol_DP800_Series as rigol

xs = []
ys = []

rigol832 = rigol.Rigol_DP800_Series()

# Output tests
#general.message(rigol832.power_supply_name())
#general.message(rigol832.power_supply_voltage('CH1'))
#general.message(rigol832.power_supply_current('CH1'))
#general.message(rigol832.power_supply_overvoltage('CH1'))
#general.message(rigol832.power_supply_overcurrent('CH1'))
#general.message(rigol832.power_supply_channel_state('CH1'))
#general.message(rigol832.power_supply_set_preset('User1'))
#general.message(rigol832.power_supply_measure('CH1'))

# Input tests
#rigol832.power_supply_voltage('CH1', '10 V')
#general.message(rigol832.power_supply_voltage('CH1'))

#rigol832.power_supply_current('CH1', '100 mA')
#general.message(rigol832.power_supply_current('CH1'))

#rigol832.power_supply_overvoltage('CH1', '15 V')
#general.message(rigol832.power_supply_overvoltage('CH1'))

#rigol832.power_supply_overcurrent('CH1', '200 mA')
#general.message(rigol832.power_supply_overcurrent('CH1'))

#general.message(rigol832.power_supply_channel_state('CH1', 'On'))
#general.message(rigol832.power_supply_channel_state('CH1'))

#general.message(rigol832.power_supply_measure('CH1'))

#rigol832.close_connection()

