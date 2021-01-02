import os
import gc
import time
import pyvisa
import numpy as np
import device_modules.config.config_utils as cutil
import device_modules.config.messenger_socket_client as send

#### Inizialization
# setting path to *.ini file
path_current_directory = os.path.dirname(__file__)
path_config_file = os.path.join(path_current_directory, 'config','keysight_3034t_config.ini')

# configuration data
config = cutil.read_conf_util(path_config_file)

# auxilary dictionaries
points_dict = {'100': 100, '250': 250, '500': 500, '1000': 1000, '2000': 2000,
					'5000': 5000, '10000': 10000, '20000': 20000, '50000': 50000, '100000': 100000,
					'200000': 200000, '500000': 500000, '1000000': 1000000, '2000000': 2000000,
					'4000000': 4000000, '8000000': 8000000};

timebase_dict = {' s': 1, 'ms': 1000, 'us': 1000000, 'ns': 1000000000};

#### Basic interaction functions
def connection():	
	global status_flag
	global device

	rm = pyvisa.ResourceManager()
	try:
		device=rm.open_resource(config['ethernet_address'])
		device.timeout=config['timeout']; # in ms
		device.read_termination = config['read_termination']  # for WORD (a kind of binary) format
		status_flag = 1
	except BrokenPipeError:
		print("No connection")
		status_flag = 0
def close_connection():
	status_flag = 0;
	gc.collect()
def device_write(command):
	if status_flag == 1:
		command = str(command)
		device.write(command)
	else:
		print("No Connection")
def device_query(command):
	if status_flag == 1:
		answer = device.query(command)
		return answer
	else:
		print("No Connection")
def device_query_ascii(command):
	if status_flag == 1:
		answer = device.query_ascii_values(command, converter='f',separator=',',container=np.array)
		return answer
	else:
		print("No Connection")
def device_read_binary(command):
	if status_flag==1:
		answer = device.query_binary_values(command,'H', is_big_endian=True, container=np.array)
		# H for 3034T; h for 2012A
		return answer
	else:
		print("No Connection")

#### Device specific functions
def oscilloscope_name():
	answer = send.message("Hello")
	#answer = device_query('*IDN?')
	return answer
def oscilloscope_record_length(*points):
	if  len(points)==1:
		ps = str(points[0])
		if ps in points_dict:
			flag = points_dict[ps]
			device_write(":WAVeform:POINts "+ str(flag))
		else:
			print("Invalid sensitivity value")
	elif len(points)==0:
		answer = int(device_query(':WAVeform:POINts?'))
		return answer
	else:
		print("Invalid Argument")###########
def oscilloscope_acquisition_type(*ac_type):
	if  len(ac_type)==1:
		flag = int(ac_type[0])
		if (flag == 0 ):
			device_write(":ACQuire:TYPE NORMal")
		elif (flag == 1):
			device_write(":ACQuire:TYPE AVER")
		elif (flag == 2):
			device_write(":ACQuire:TYPE HRES")
		elif (flag == 3):
			device_write(":ACQuire:TYPE PEAK")
		else:
			print("Invalid acquisition type")
	elif len(ac_type)==0:
		raw_answer = str(device_query(":ACQuire:TYPE?"))
		if (raw_answer == "NORM\n"):
			answer = 0
		elif (raw_answer == "AVER\n"):
			answer = 1
		elif (raw_answer == "HRES\n"):
			answer = 2
		elif (raw_answer == "PEAK\n"):
			answer = 3
		return answer
	else:
		print("Invalid argument")
def oscilloscope_number_of_averages(*number_of_averages):
	if len(number_of_averages)==1:
		numave = int(number_of_averages[0]);
		if numave >= 2 and numave <= 65536:
			ac = oscilloscope_acquisition_type()
			if ac == 1:
				device_write(":ACQuire:COUNt " + str(numave))
			elif ac == 0:
				print("Your are in NORM mode")
			elif ac == 2:
				print("Your are in HRES mode")
			elif ac == 3:
				print("Your are in PEAK mode")
		else:
			print("Invalid number of averages")
	elif len(number_of_averages)==0:
		answer = int(device_query(":ACQuire:COUNt?"))
		return answer
	else:
		print("Invalid argument")
def oscilloscope_timebase(*timebase):
	if len(timebase)==1:
		temp = timebase[0].split(" ")
		tb = float(temp[0])
		scaling = temp[1];
		if scaling in timebase_dict:
			coef = timebase_dict[scaling]
			device_write(":TIMebase:RANGe "+ str(tb/coef))
		else:
			print ('Incorrect timebase')
	elif len(timebase)==0:
		answer = float(device_query(":TIMebase:RANGe?"))*1000000
		return answer
	else:
		print("Invalid argument")
def oscilloscope_time_resolution():
	points = int(oscilloscope_record_length())
	answer = 1000000*float(device_query(":TIMebase:RANGe?"))/points
	return answer

def scope_start_acquisition():

	#start_time = datetime.now()
	scope_write(':WAVeform:FORMat WORD')
	#scope_write(':WAVeform:POINts:MODE MAX')
	scope_query('*ESR?;:DIGitize;*OPC?') # return 1, if everything is ok; 1-binary format; 2-clearing; 3-digitizing; 4-checking of the completness
	#end_time=datetime.now()
	#print("Duration of Acquisition: {}".format(end_time - start_time))####
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

	return preamble	####
def oscilloscope_stop():
	device_write(":STOP")
def oscilloscope_run():
	device_write(":RUN")
def oscilloscope_run_stop():
	device_write(":RUN")
	time.sleep(0.5)
	device_write(":STOP")
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
	
	array_y=scope_read_binary(':WAVeform:DATA?')
	
	#end_time=datetime.now()
	#print("Duration of Get Curve: {}".format(end_time - start_time))
	#x_inc=float(scope_query(":WAVeform:XINC?")) # this value is incorrect
		
	#preamble=np.fromstring(scope_query(":WAVeform:PREamble?"),dtype=np.float,sep=",")
	preamble = scope_query_ascii(":WAVeform:PREamble?")
	#x_orig=preamble[5]
	y_inc=preamble[7]
	y_orig=preamble[8]
	y_ref=preamble[9]
	#print(y_inc)
	#print(y_orig)
	#print(y_ref)

	array_y=(array_y - y_ref)*y_inc + y_orig    # can be array_y=(array_y + y_ref)*y_inc + y_orig    for 2012A
	#array_x= list(map(lambda x: resolution*(x+1) + 1000000*x_orig, list(range(points))))
	#final_data = list(zip(array_x,array_y))
		
	return array_y####


def scope_wave_freq(*freq):
	
	if len(freq)==1:
		freq = float(freq[0]);
		scope_write(":WGEN1:FREQuency " + str(freq))
	elif len(freq)==0:
		freq = float(scope_query(":WGEN1:FREQuency?"))
		return freq
	else:
		print("Invalid Argument")
def scope_wave_width(*width):
	
	if len(width)==1:
		width = float(width[0]);
		scope_write(":WGEN1:FUNCtion:PULSe:WIDTh " + str(width))
	elif len(width)==0:
		width = 1000000*float(scope_query(":WGEN1:FUNCtion:PULSe:WIDTh?"))
		return width
	else:
		print("Invalid Argument")


#start_time = datetime.now()
#end_time=datetime.now()
#print("Duration: {}".format(end_time - start_time))
