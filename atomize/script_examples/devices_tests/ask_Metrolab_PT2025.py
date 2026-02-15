import time
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.Metrolab_PT2025 as pt

pt2025 = pt.Metrolab_PT2025()

# Output tests
general.message(pt2025.gaussmeter_name())

general.message(pt2025.gaussmeter_status())
#general.message(itc503.tc_setpoint())

pt2025.close_connection()