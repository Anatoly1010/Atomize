import time
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.Agilent_53131a as ag

xs = []
ys = []

ag53131a = ag.Agilent_53131a()


#ag53131a.freq_counter_digits(8)
ag53131a.freq_counter_gate_time('10 s')
#ag53131a.freq_counter_stop_mode('Dig')
#general.message(ag53131a.freq_counter_stop_mode())
general.message(ag53131a.freq_counter_gate_time())
#general.message(ag53131a.freq_counter_digits())
#general.message(ag53131a.freq_counter_frequency('CH3'))
