import pyvisa
import numpy as np
from datetime import datetime
import gc
from pyvisa.constants import StopBits, Parity

def connection():
	
	global c
	global lock_in
	global rm

	rm = pyvisa.ResourceManager()
	#print (rm.list_resources())
	try:
		lock_in = rm.open_resource('ASRL/dev/ttyUSB1::INSTR',read_termination='\r', write_termination='\n\r', baud_rate = 9600, data_bits = 8, parity=Parity.none, stop_bits=StopBits.one)
		#print(lock_in)
		lock_in.timeout = 1000; # in ms
		c=1
	except BrokenPipeError:
		print("No connection")
		c=0

def close_connection():
	
	rm.close()
	gc.collect()


def lock_in_write(command):
	#c, scope = connection()
	if c==1:
		lock_in.write(command)
	else:
		print("No Connection")
def lock_in_query(command):
	#c, scope = connection()
	if c==1:
		answer = lock_in.query(command)
		return answer
	else:
		print("No Connection")
def lock_in_read():
	#c, scope = connection()
	if c==1:
		answer = lock_in.read()
		return answer
	else:
		print("No Connection")


def lock_in_modulation_frequency(*freq):
	
	if len(freq)==1:
		freq = float(freq[0])
		lock_in_write('FREQ '+str(freq))
	elif len(freq)==0:
		modulation_frequency = float(lock_in_query('FREQ?'))				##########
		return modulation_frequency
	else:
		print("Invalid Argument")
def lock_in_phase(*degs):
	
	if len(degs)==1:
		degs = int(degs[0])
		lock_in_write('PHAS '+str(degs))
	elif len(degs)==0:
		phase = float(lock_in_query('PHAS?'))								##########
		return phase
	else:
		print("Invalid Argument")
def lock_in_time_constant(*tc):
	
	if  len(tc)==1:
		tc = float(tc[0])
		if (tc == 0.01 ):
			lock_in_write("OFLT 0")
		elif (tc == 0.03):
			lock_in_write("OFLT 1")
		elif (tc == 0.1):
			lock_in_write("OFLT 2")
		elif (tc == 0.3):
			lock_in_write("OFLT 3")
		elif (tc == 1.):
			lock_in_write("OFLT 4")
		elif (tc == 3.):
			lock_in_write("OFLT 5")
		elif (tc == 10.):
			lock_in_write("OFLT 6")
		elif (tc == 30.):
			lock_in_write("OFLT 7")
		elif (tc == 100.):
			lock_in_write("OFLT 8")
		elif (tc == 300.):
			lock_in_write("OFLT 9")
		elif (tc == 1000.):
			lock_in_write("OFLT 10")
		elif (tc == 3000.):
			lock_in_write("OFLT 11")
		elif (tc == 10000.):
			lock_in_write("OFLT 12")
		elif (tc == 30000.):
			lock_in_write("OFLT 13")
		elif (tc == 100000.):
			lock_in_write("OFLT 14")
		elif (tc == 300000.):
			lock_in_write("OFLT 15")
		else:
			print("Invalid Acquisition Type")

	elif len(tc)==0:
		tc = float(lock_in_query("OFLT?"))									##########
		return tc
	else:
		print("Invalid Argument")
def lock_in_amplitude(*ampl):
	
	if len(ampl)==1:
		ampl = float(ampl[0]);
		lock_in_write('SLVL '+str(ampl))
	elif len(ampl)==0:
		amplitude = lock_in_query("SLVL?")									##########
		return amplitude
	else:
		print("Invalid Argument")

def lock_in_signal():

	x = 1000000*float(lock_in_query('OUTP? 3'))									##########
	#lock_in_read()
	return x

def lock_in_signal_x_y_r():

	a_string = lock_in_query('SNAP? 1,2,3')									##########
	a_list = a_string.split(',')
	list_of_floats = [float(item) for item in a_list]
	x = 1000000*list_of_floats[0]
	y = 1000000*list_of_floats[1]
	r = 1000000*list_of_floats[2]
	return x, y, r

def lock_in_noise_y():

	y_noise = 1000000*float(lock_in_query('OUTR? 2'))									##########
	#a_list = a_string.split(',')
	#list_of_floats = [float(item) for item in a_list]
	#x = 1000000*list_of_floats[0]
	#y = 1000000*list_of_floats[1]
	#r = 1000000*list_of_floats[2]
	return y_noise

def lock_in_sample_rate():

	sample_rate = lock_in_query('SRAT?')										##########
	return sample_rate