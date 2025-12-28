import time
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.Gentec_Solo2 as solo

xs = []
ys = []

solo2 = solo.Gentec_Solo2()

#general.message(solo2.laser_power_meter_name())
#general.message(solo2.laser_power_meter_head_name())
#general.message(solo2.laser_power_meter_get_data())
#solo2.laser_power_meter_set_wavelength(1064)
#general.message(solo2.laser_power_meter_set_wavelength())
#solo2.laser_power_meter_zero_offset('Off')
#general.message(solo2.laser_power_meter_zero_offset())

solo2.laser_power_meter_scale('123 MW')

#solo2.laser_power_meter_energy_mode('Off')
#general.message(solo2.laser_power_meter_energy_mode())

#solo2.laser_power_meter_analog_output('On')
#general.message(solo2.laser_power_meter_analog_output())

#for i in range (100):
#	general.wait('1000 ms')
#	general.message(solo2.laser_power_meter_get_data())
