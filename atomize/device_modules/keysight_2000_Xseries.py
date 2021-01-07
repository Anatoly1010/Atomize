#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import gc
import time
import pyvisa
import numpy as np

def connection():
	
	global c
	global scope
	global rm

	rm = pyvisa.ResourceManager()
	try:
		scope = rm.open_resource('TCPIP::192.168.2.22::INSTR')
		scope.timeout = 10000; # in ms
		scope.read_termination = ''  # for WORD (a kind of binary) format
		#print("Scope is found")
		c=1
	except BrokenPipeError:
		print("No connection")
		c=0
	#return c, scope
def close_connection():
	
	#scope_write(':RUN')
	rm.close()
	gc.collect()


def scope_write(command):
	#c, scope = connection()
	if c==1:
		scope.write(command)
	else:
		print("No Connection")
def scope_query(command):
	#c, scope = connection()
	if c==1:
		answer = scope.query(command)
		return answer
	else:
		print("No Connection")
def scope_query_ascii(command):
	#c, scope = connection()
	if c==1:
		answer = scope.query_ascii_values(command,converter='f',separator=',',container=np.array)
		return answer
	else:
		print("No Connection")
def scope_read_binary(command):
	#c, scope = connection()
	if c==1:
		answer = scope.query_binary_values(command,'H', is_big_endian=True, container=np.array)
		return answer
	else:
		print("No Connection")


def scope_record_length(*points):
	
	if len(points)==1:
		points = int(points[0])
		scope_write(':WAVeform:POINts '+str(points))
	elif len(points)==0:
		number_of_points = int(scope_query(':WAVeform:POINts?'))
		return number_of_points
	else:
		print("Invalid Argument")
def scope_acquisition_type(*ac_type):
	
	if  len(ac_type)==1:
		ac_type = int(ac_type[0])
		if (ac_type == 0 ):
			scope_write(":ACQuire:TYPE NORMal")
		elif (ac_type == 1):
			scope_write(":ACQuire:TYPE AVER")
		elif (ac_type == 2):
			scope_write(":ACQuire:TYPE HRES")
		elif (ac_type == 3):
			scope_write(":ACQuire:TYPE PEAK")
		else:
			print("Invalid Acquisition Type")

	elif len(ac_type)==0:

		ac_type = str(scope_query(":ACQuire:TYPE?"))
		if (ac_type == "NORM\n"):
			ac_type = 0
		elif (ac_type == "AVER\n"):
			ac_type = 1
		elif (ac_type == "HRES\n"):
			ac_type = 2
		elif (ac_type == "PEAK\n"):
			ac_type = 3
		return ac_type
	else:
		print("Invalid Argument")
def scope_number_of_averages(*number_of_averages):
	
	if len(number_of_averages)==1:
		number_of_averages = int(number_of_averages[0]);
		ac = scope_acquisition_type()
		if ac == 1:
			scope_write(":ACQuire:COUNt " + str(number_of_averages))
		elif ac == 0:
			print("Your are in NORM mode")
		elif ac == 2:
			print("Your are in HRES mode")
		elif ac == 3:
			print("Your are in PEAK mode")
	elif len(number_of_averages)==0:
		averages = int(scope_query(":ACQuire:COUNt?"))
		return averages
	else:
		print("Invalid Argument")
def scope_full_timebase(*timebase):
	
	if len(timebase)==1:
		timebase = int(timebase[0]);
		scope_write(":TIMebase:RANGe " + str(timebase/1000000))
	elif len(timebase)==0:
		timebase = float(scope_query(":TIMebase:RANGe?"))*1000000
		return timebase
	else:
		print("Invalid Argument")
def scope_timeresolution():
	points = int(scope_record_length())
	timeresolution = 1000000*float(scope_query(":TIMebase:RANGe?"))/points
	return timeresolution	
def scope_start_acquisition():

	#start_time = datetime.now()
	scope_write(':WAVeform:FORMat WORD')
	scope_query('*ESR?;:DIGitize;*OPC?') # return 1, if everything is ok; 1-binary format; 2-clearing; 3-digitizing; 4-checking of the completness
	#end_time=datetime.now()
	#print("Duration of Acquisition: {}".format(end_time - start_time))
def scope_read_preamble(channel):

	if channel=='CH1':
		scope_write(':WAVeform:SOURce CHAN1')
	elif channel=='CH2':
		scope_write(':WAVeform:SOURce CHAN2')
	elif channel=='CH3':
		scope_write(':WAVeform:SOURce CHAN3')
	elif channel=='CH4':
		scope_write(':WAVeform:SOURce CHAN4')
	else:
		print("Invalid Argument")

	preamble=scope_query_ascii(":WAVeform:PREamble?")	

	return preamble	
def scope_stop():
	scope_write(":STOP")
def scope_run():
	scope_write(":RUN")
def scope_run_stop():
	scope_write(":RUN")
	time.sleep(0.5)
	scope_write(":STOP")

def scope_get_curve(channel):

	if channel=='CH1':
		scope_write(':WAVeform:SOURce CHAN1')
	elif channel=='CH2':
		scope_write(':WAVeform:SOURce CHAN2')
	elif channel=='CH3':
		scope_write(':WAVeform:SOURce CHAN3')
	elif channel=='CH4':
		scope_write(':WAVeform:SOURce CHAN4')
	else:
		print("Invalid Argument")

	#start_time = datetime.now()
	#acq_completed = scope_start_acquisition()
	#points = int(scope_record_length())
	#resolution = scope_timeresolution()
	#scope_query('*OPC?')
	#scope_write(':WAVeform:DATA?')
	#scope.read_raw()
	#print(scope_query(":WAV:POINTS?"))
	#scope_write(":WAV:POINTS:MODE MAX, 5000")
	array_y=scope_read_binary(':WAVeform:DATA?')
	#end_time=datetime.now()
	#print("Duration of Get Curve: {}".format(end_time - start_time))
	#x_inc=float(scope_query(":WAVeform:XINC?")) # this value is incorrect
		
	#preamble=np.fromstring(scope_query(":WAVeform:PREamble?"),dtype=np.float,sep=",")
	preamble=scope_query_ascii(":WAVeform:PREamble?")
	#x_orig=preamble[5]
	y_inc=preamble[7]
	y_orig=preamble[8]
	y_ref=preamble[9]
	
	array_y=(array_y-y_ref)*y_inc + y_orig
	#array_x= list(map(lambda x: resolution*(x+1) + 1000000*x_orig, list(range(points))))
	#final_data = list(zip(array_x,array_y))
		
	return array_y


#start_time = datetime.now()
#end_time=datetime.now()
#print("Duration: {}".format(end_time - start_time))

if __name__ == "__main__":
    main()