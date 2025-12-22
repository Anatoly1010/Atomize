import time
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.Gentec_Solo2 as solo

xs = []
ys = []

solo2 = solo.Gentec_Solo2()

general.message(solo2.laser_power_meter_name())

