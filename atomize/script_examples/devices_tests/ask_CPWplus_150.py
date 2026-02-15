import time
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.CPWplus_150 as cw

cpw150 = cw.CPWplus_150()

i = 0

while i < 1000:
   sign, weight, dimension = cpw150.balance_weight()
   general.message(sign, weight, dimension)
   general.append_1d('CPW 150', weight, label='test data')
   general.wait('1000 ms')
   i += 1


cpw150.close_connection()
