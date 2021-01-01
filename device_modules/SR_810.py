import os
import gc
import pyvisa
import numpy as np
from datetime import datetime
from pyvisa.constants import StopBits, Parity
import config.config_utils as cutil

#### Inizialization
# setting path to *.ini file
path_current_directory = os.path.dirname(__file__)
path_config_file = os.path.join(path_current_directory, 'config','SR810_config.ini')

# configuration data
config = cutil.read_conf_util(path_config_file)

#### Basic interaction functions
def connection():
	global status_flag
	global device
	
	if config['interface'] == 'gpib':
		try:
			import Gpib
			device = Gpib.Gpib(config['board_address'], config['gpib_address'])
			try:
				# test should be here
				device_query('*IDN?')
				status_flag = 1;
			except pyvisa.VisaIOError:
				status_flag = 0;	
		except pyvisa.VisaIOError:
			print("No connection")
			device.close()
			status_flag = 0

	elif config['interface'] == 'rs232':
		try:
			rm = pyvisa.ResourceManager()
			device=rm.open_resource(config['serial_address'], read_termination=config['read_termination'],
			write_termination=config['write_termination'], baud_rate=config['baudrate'],
			data_bits=config['databits'], parity=config['parity'], stop_bits=config['stopbits'])
			device.timeout=config['timeout']; # in ms
			try:
				# test should be here
				device_query('*IDN?')
				status_flag = 1;
			except pyvisa.VisaIOError:
				status_flag = 0;	
		except pyvisa.VisaIOError:
			print("No connection")
			device.close()
			status_flag = 0
def close_connection():
	status_flag = 0;
	#device.close()
	gc.collect()
def device_write(command):
	if status_flag==1:
		command = str(command)
		device.write(command)
	else:
		print("No Connection")
def device_query(command):
	if status_flag == 1:
		if config['interface'] == 'gpib':
			device.write(command)
			time.sleep(0.05)
			answer = device.read()
		elif config['interface'] == 'rs232':
			answer = device.query(command)
		return answer
	else:
		print("No Connection")

#### Device specific functions
def lock_in_name():
	answer = config['name'] 
	return answer
def lock_in_ref_frequency(*freq):
	if len(freq)==1:
		freq = float(freq[0])
		device_write('FREQ '+ str(freq))
	elif len(freq)==0:
		answer = float(device_query('FREQ?'))
		return answer
	else:
		print("Invalid Argument")
def lock_in_phase(*degs):
	if len(degs)==1:
		degs = int(degs[0])
		device_write('PHAS '+str(degs))
	elif len(degs)==0:
		answer = float(device_query('PHAS?'))
		return answer
	else:
		print("Invalid Argument")
def lock_in_time_constant(*tc):
	if  len(tc)==1:
		tc = float(tc[0])
		if (tc == 0.01 ):
			device_write("OFLT 0")
		elif (tc == 0.03):
			device_write("OFLT 1")
		elif (tc == 0.1):
			device_write("OFLT 2")
		elif (tc == 0.3):
			device_write("OFLT 3")
		elif (tc == 1.):
			device_write("OFLT 4")
		elif (tc == 3.):
			device_write("OFLT 5")
		elif (tc == 10.):
			device_write("OFLT 6")
		elif (tc == 30.):
			device_write("OFLT 7")
		elif (tc == 100.):
			device_write("OFLT 8")
		elif (tc == 300.):
			device_write("OFLT 9")
		elif (tc == 1000.):
			device_write("OFLT 10")
		elif (tc == 3000.):
			device_write("OFLT 11")
		elif (tc == 10000.):
			device_write("OFLT 12")
		elif (tc == 30000.):
			device_write("OFLT 13")
		elif (tc == 100000.):
			device_write("OFLT 14")
		elif (tc == 300000.):
			device_write("OFLT 15")
		else:
			print("Invalid time constant value")
	elif len(tc)==0:
		answer = float(device_query("OFLT?"))
		return answer
	else:
		print("Invalid Argument")
def lock_in_ref_amplitude(*amplitude):
	if len(amplitude)==1:
		ampl = float(amplitude[0]);
		if ampl < 5 and ampl > 0.004:
			device_write('SLVL '+str(ampl))
		else:
			device_write('SLVL '+'0.004')
			print("Invalid Argument")
	elif len(amplitude)==0:
		answer = float(device_query("SLVL?"))
		return answer
	else:
		print("Invalid Argument")
def lock_in_get_data(*channel):
	if len(channel)==0:
		answer = float(device_query('OUTP? 1'))
		return answer
	elif len(channel)==1 and int(channel[0])==1:
		answer = float(device_query('OUTP? 1'))
		return answer
	elif len(channel)==1 and int(channel[0])==2:
		answer = float(device_query('OUTP? 2'))
		return answer
	elif len(channel)==1 and int(channel[0])==3:
		answer = float(device_query('OUTP? 3'))
		return answer
	elif len(channel)==1 and int(channel[0])==4:
		answer = float(device_query('OUTP? 4'))
		return answer
	elif len(channel)==2 and int(channel[0])==1 and int(channel[1])==2:
		answer_string = device_query('SNAP? 1,2')
		answer_list = answer_string.split(',')
		list_of_floats = [float(item) for item in answer_list]
		x = list_of_floats[0]
		y = list_of_floats[1]
		return x, y
	elif len(channel)==3 and int(channel[0])==1 and int(channel[1])==2 and int(channel[2])==3:
		answer_string = device_query('SNAP? 1,2,3')
		answer_list = answer_string.split(',')
		list_of_floats = [float(item) for item in answer_list]
		x = list_of_floats[0]
		y = list_of_floats[1]
		r = list_of_floats[2]
		return x, y, r
def lock_in_sensitivity(*sensitivity):
	if  len(sensitivity)==2:
		sens = float(sensitivity[0])
		scaling = str(sensitivity[1])
		if sens == 2 and scaling == 'nV':
			device_write("SENS 0")
		elif sens == 5 and scaling == 'nV':
			device_write("SENS 1")
		elif sens == 10 and scaling == 'nV':
			device_write("SENS 2")
		elif sens == 20 and scaling == 'nV':
			device_write("SENS 3")
		elif sens == 50 and scaling == 'nV':
			device_write("SENS 4")
		elif sens == 100 and scaling == 'nV':
			device_write("SENS 5")
		elif sens == 200 and scaling == 'nV':
			device_write("SENS 6")
		elif sens == 500 and scaling == 'nV':
			device_write("SENS 7")
		elif sens == 1 and scaling == 'uV':
			device_write("SENS 8")
		elif sens == 2 and scaling == 'uV':
			device_write("SENS 9")
		elif sens == 5 and scaling == 'uV':
			device_write("SENS 10")
		elif sens == 10 and scaling == 'uV':
			device_write("SENS 11")
		elif sens == 20 and scaling == 'uV':
			device_write("SENS 12")
		elif sens == 50 and scaling == 'uV':
			device_write("SENS 13")
		elif sens == 100 and scaling == 'uV':
			device_write("SENS 14")
		elif sens == 200 and scaling == 'uV':
			device_write("SENS 15")
		elif sens == 500 and scaling == 'uV':
			device_write("SENS 16")
		elif sens == 1 and scaling == 'mV':
			device_write("SENS 17")
		elif sens == 2 and scaling == 'mV':
			device_write("SENS 18")
		elif sens == 5 and scaling == 'mV':
			device_write("SENS 19")
		elif sens == 10 and scaling == 'mV':
			device_write("SENS 20")
		elif sens == 20 and scaling == 'mV':
			device_write("SENS 21")
		elif sens == 50 and scaling == 'mV':
			device_write("SENS 22")
		elif sens == 100 and scaling == 'mV':
			device_write("SENS 23")
		elif sens == 200 and scaling == 'mV':
			device_write("SENS 24")
		elif sens == 500 and scaling == 'mV':
			device_write("SENS 25")
		elif sens == 1 and scaling == 'V':
			device_write("SENS 26")
		else:
			print("Invalid sensitivity value")
	elif len(sensitivity)==0:
		answer = float(device_query("SENS?"))
		return answer
	else:
		print("Invalid Argument")
def lock_in_ref_mode(*mode):
	if len(mode)==1:
		flag = int(mode[0]);
		if flag==0:
			device_write('FMOD '+str(flag))
		elif flag==1:
			device_write('FMOD '+str(flag))
		else:
			print("Invalid Argument")
	elif len(mode)==0:
		answer = float(device_query("FMOD?"))
		return answer
	else:
		print("Invalid Argument")
def lock_in_sync_filter(*mode):
	if len(mode)==1:
		flag = int(mode[0]);
		if flag==0:
			device_write('SYNC '+str(flag))
		elif flag==1:
			device_write('SYNC '+str(flag))
		else:
			print("Invalid Argument")
	elif len(mode)==0:
		answer = float(device_query("SYNC?"))
		return answer
	else:
		print("Invalid Argument")



def lock_in_command(command):
	device_write(command)
def lock_in_query(command):
	answer = device_query(command)
	return answer