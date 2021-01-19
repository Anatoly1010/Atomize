import time
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.Keysight_3000_Xseries as key

xs = []
ys = []

t3034 = key.Keysight_3000_Xseries()

#t3034.oscilloscope_record_length(16000)
t3034.oscilloscope_trigger_delay('10 us')
general.message(t3034.oscilloscope_trigger_delay())