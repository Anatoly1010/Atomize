import SR_810 as sr_810
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import time
import pyvisa
from pyvisa.constants import StopBits, Parity

#rm = pyvisa.ResourceManager()
#print(rm.list_resources())
#my_instrument = rm.open_resource('ASRL/dev/ttyUSB1::INSTR',read_termination='\r', write_termination='\n\r', baud_rate = 9600, data_bits = 8, parity=Parity.none, stop_bits=StopBits.one)
#x = my_instrument.query("*IDN?")

#print(x)


sr_810.connection()
#sr_810.lock_in_modulation_frequency(1000)
x = sr_810.lock_in_noise_y()
#y = sr_810.lock_in_signal()
print(x)
#print(y)

sr_810.close_connection()