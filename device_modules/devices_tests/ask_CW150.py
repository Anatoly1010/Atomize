import CWplus150 as cw150
import numpy as np
import matplotlib.pyplot as plt
import serial
import time

fig, ax = plt.subplots ()


# INITIALIZATION

#balance = serial.Serial("/dev/ttyUSB0", 9600, timeout=0.5, bytesize=8, parity='N')
#balance.write(b"G\r\n")
#time.sleep(0.1)
#ser_bytes = balance.readline()
#print(ser_bytes)
#decoded_bytes = ser_bytes[0:len(ser_bytes)-2].decode("utf-8")
#print(decoded_bytes)

cw150.connection()

test = cw150.balance_weight();
print(test)

cw150.close_connection()

