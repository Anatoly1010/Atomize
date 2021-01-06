import device_modules.Lakeshore335 as ls335
import numpy as np
import matplotlib.pyplot as plt
import time
import pyvisa

fig, ax = plt.subplots ()


# INITIALIZATION


rm = pyvisa.ResourceManager()
print(rm.list_resources())
#my_instrument = rm.open_resource('ASRL/dev/ttyUSB0::INSTR',read_termination='', write_termination='\r\n')
#my_instrument.baud_rate = 4800
#print(my_instrument)
#print(my_instrument.query("KRDG? A"))
#print(my_instrument.query("*IDN?"))
#x = my_instrument.read()
#print(x)

ls335.connection()

time.sleep(0.5)
a = ls335.heater()
print(a)


ls335.close_connection()