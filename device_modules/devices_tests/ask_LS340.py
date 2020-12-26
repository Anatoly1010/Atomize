import Lakeshore340 as ls340
import numpy as np
import time
import pyvisa


# INITIALIZATION


#rm = pyvisa.ResourceManager()
#print(rm.list_resources())
#my_instrument = rm.open_resource('ASRL/dev/ttyUSB0::INSTR',read_termination='', write_termination='\r\n')
#my_instrument.baud_rate = 4800
#print(my_instrument)
#print(my_instrument.query("KRDG? A"))
#print(my_instrument.query("*IDN?"))
#x = my_instrument.read()
#print(x)

ls340.connection()

#a =ls340.heater_range()
#time.sleep(0.5)
a = ls340.heater()
print(a)


ls340.close_connection()