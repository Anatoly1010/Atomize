import os
import gc
import time
import Gpib
import config.config_utils as cutil

#### Inizialization
# setting path to *.ini file
path_current_directory = os.path.dirname(__file__)
path_config_file = os.path.join(path_current_directory, 'config','agilent53181a_config.ini')

# configuration data
config = cutil.read_conf_util(path_config_file)

# auxilary dictionaries

#### Basic interaction functions
def connection():
	global status_flag
	global device
	if config['interface'] == 'gpib':
		try:
			device = Gpib.Gpib(config['board_address'], config['gpib_address'])
			try:
				# test should be here
				device_query('*IDN?')
				status_flag = 1;
			except:
				status_flag = 0;	
		except:
			print("No connection")
			status_flag = 0
	else:
		print('Incorrect interface')
def close_connection():
	status_flag = 0;
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
			return answer
		else:
			print('Incorrect interface')
			status_flag = 0
	else:
		print("No Connection")

#### Device specific functions
def freq_counter_name():
	answer = device_query('*IDN?')
	return answer
def freq_counter_get_frequency(channel):
	ch = str(channel[0])
	try:
		answer = float(device_query(':MEASURE:FREQ? '+ str(ch)))
		return answer
	except:
		print('Invalid argument')


	

