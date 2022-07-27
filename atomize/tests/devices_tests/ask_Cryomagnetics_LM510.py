import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.Cryomagnetics_LM510 as lm

lm510 = lm.Cryomagnetics_LM510()

# READ
#general.message(lm510.level_monitor_name())
#general.message(lm510.level_monitor_select_channel())
#general.message(lm510.level_monitor_boost_mode())
#general.message(lm510.level_monitor_high_level_alarm())
#general.message(lm510.level_monitor_low_level_alarm())
#general.message(lm510.level_monitor_sensor_length())
#general.message(lm510.level_monitor_sample_mode())
#general.message(lm510.level_monitor_units())
#general.message(lm510.level_monitor_measure('2'))
#general.message(lm510.level_monitor_sample_interval())
#general.message(lm510.level_monitor_hrc_target_pressure())
#general.message(lm510.level_monitor_hrc_heater_power_limit())
#general.message(lm510.level_monitor_hrc_heater_enable())

# WRITE
lm510.level_monitor_select_channel('1') #['1, '2']
#general.message(lm510.level_monitor_select_channel())

#lm510.level_monitor_boost_mode('On') #['Off', 'On', 'Smart']
general.message(lm510.level_monitor_boost_mode())

#lm510.level_monitor_high_level_alarm('68.0')
#general.message(lm510.level_monitor_high_level_alarm())

#lm510.level_monitor_low_level_alarm('0.0')
#general.message(lm510.level_monitor_low_level_alarm())

#lm510.level_monitor_sample_mode('Sample/Hold') #['Sample/Hold', 'Continuous', 'Off']
#general.message(lm510.level_monitor_sample_mode())

#lm510.level_monitor_units('cm') #['cm', 'in',  '%']
#general.message(lm510.level_monitor_units())

#lm510.level_monitor_sample_interval('0', '10', '0') #[h, m ,s]
#general.message(lm510.level_monitor_sample_interval())

#lm510.level_monitor_hrc_target_pressure('0.50')
#general.message(lm510.level_monitor_hrc_target_pressure())

#lm510.level_monitor_hrc_heater_power_limit('6.0')
#general.message(lm510.level_monitor_hrc_heater_power_limit())

#lm510.level_monitor_hrc_heater_enable('On') #['On', 'Off']
#general.message(lm510.level_monitor_hrc_heater_enable())
