#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import gc
import time
import Gpib
import atomize.device_modules.config.config_utils as cutil
import atomize.device_modules.config.messenger_socket_client as send

#### Inizialization
# setting path to *.ini file
path_current_directory = os.path.dirname(__file__)
path_config_file = os.path.join(path_current_directory, 'config','keysight53230a_config.ini')

# configuration data
config = cutil.read_conf_util(path_config_file)

# auxilary dictionaries
startarm_dic = {'Im': 'IMMediate', 'Ext': 'EXTernal',};
stoparm_dic = {'Im': 'IMMediate', 'Tim': 'TIME', 'Event': 'EVENts',};
gate_dic = {'Ext': 'EXTernal', 'Tim': 'TIME',};
scale_dict = {' s': 1, 'ms': 0.001, 'us': 0.000001, 'ns': 0.000000001,};

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

def freq_counter_frequency(channel):
	if channel == 'CH1':
		answer = float(device_query('MEAS:FREQ? (@1)'))
		return answer
	elif channel=='CH2':
		answer = float(device_query('MEAS:FREQ? (@2)'))
		return answer
	elif channel=='CH3':
		answer = float(device_query('MEAS:FREQ? (@3)'))
		return answer
	else:
		send.message('Invalid argument')

def freq_counter_impedance(*impedance):
	if len(impedance)==2:
		ch = str(impedance[0])
		imp = str(impedance[1])
		if imp == '1 M':
			imp = '1.0E6';
		elif imp == '50':
			imp = '50';

		if ch == 'CH1':
			device_write("INPut1:IMPedance " + str(imp))
		elif ch == 'CH2':
			device_write("INPut2:IMPedance " + str(imp))
			#send.message('The impedance for CH2 is only 50 Ohm')
		elif ch == 'CH3':
			send.message('The impedance for CH3 is only 50 Ohm')
			#send.message('Invalid channel')
	elif len(impedance)==1:
		ch = str(impedance[0])
		if ch == 'CH1':
			answer = float(device_query("INPut1:IMPedance?"))
			return answer
		elif ch == 'CH2':
			answer = float(device_query("INPut2:IMPedance?"))
			return answer
		elif ch == 'CH3':
			answer = float(device_query("INPut3:IMPedance?"))
			#send.message('Invalid channel')
			return answer
	else:
		send.message('Invalid argument')

def freq_counter_coupling(*coupling):
	if len(coupling)==2:
		ch = str(coupling[0])
		cpl = str(coupling[1])
		if ch == 'CH1':
			device_write("INPut1:COUPling " + str(cpl))
		elif ch == 'CH2':
			device_write("INPut2:COUPling " + str(cpl))
			#send.message('The coupling for CH2 is only AC')
		elif ch == 'CH3':
			send.message('The impedance for CH3 is only AC')
			#send.message('Invalid channel')
	elif len(impedance)==1:
		ch = str(coupling[0])
		if ch == 'CH1':
			answer = str(device_query("INPut1:COUPling?"))
			return answer
		elif ch == 'CH2':
			answer = str(device_query("INPut2:COUPling?"))
			return answer
		elif ch == 'CH3':
			#answer = str(device_query(":INPut3:COUPling?"))
			send.message('Invalid channel')
			#return answer
	else:
		send.message('Invalid argument')

def freq_counter_stop_mode(*mode):
	if  len(mode)==1:
		md = str(mode[0])
		if md in stoparm_dic:
			flag = stoparm_dic[md]
			device_write("GATE:STARt:DELay:SOURce "+ str(flag))
		else:
			send.message("Invalid gate open mode")
	elif len(mode)==0:
		answer = str(device_query('GATE:STARt:DELay:SOURce?'))
		return answer
	else:
		send.message("Invalid argument")

def freq_counter_start_mode(*mode):
	if  len(mode)==1:
		md = str(mode[0])
		if md in startarm_dic:
			flag = startarm_dic[md]
			device_write("GATE:STARt:SOURce "+ str(flag))
		else:
			send.message("Invalid start arm mode")
	elif len(mode)==0:
		answer = str(device_query('GATE:STARt:SOURce?'))
		return answer
	else:
		send.message("Invalid argument")

def freq_counter_gate_mode(*mode):
	if  len(mode)==1:
		md = str(mode[0])
		if md in gate_dic:
			flag = gate_dic[md]
			device_write("FREQuency:GATE:SOURce "+ str(flag))
		else:
			send.message("Invalid gate mode")
	elif len(mode)==0:
		answer = str(device_query('FREQuency:GATE:SOURce?'))
		return answer
	else:
		send.message("Invalid argument")

def freq_counter_gate_time(*time):
	if len(time)==1:
		temp = time[0].split(" ")
		tb = float(temp[0])
		scaling = temp[1];
		if scaling in scale_dict:
			coef = scale_dict[scaling]
			device_write("GATE:STARt:DELay:TIME "+ str(tb*coef))
		else:
			send.message("Incorrect gate time")
	elif len(time)==0:
		answer = float(device_query("GATE:STARt:DELay:TIME?"))
		return answer
	else:
		send.message("Invalid argument")

def freq_counter_ratio(channel1, channel2):
	if channel1 == 'CH1' and channel2 =='CH2':
		answer = float(device_query('MEAS:FREQ:RAT? (@1),(@2)'))
		return answer
	elif channel1 == 'CH2' and channel2 =='CH1':
		answer = float(device_query('MEAS:FREQ:RAT? (@2),(@1)'))
		return answer
	elif channel1 == 'CH1' and channel2 =='CH3':
		answer = float(device_query('MEAS:FREQ:RAT? (@1),(@3)'))
		return answer
	elif channel1 == 'CH3' and channel2 =='CH1':
		answer = float(device_query('MEAS:FREQ:RAT? (@3),(@1)'))
		return answer
	elif channel1 == 'CH2' and channel2 =='CH3':
		answer = float(device_query('MEAS:FREQ:RAT? (@2),(@3)'))
		return answer
	elif channel1 == 'CH3' and channel2 =='CH2':
		answer = float(device_query('MEAS:FREQ:RAT? (@3),(@2)'))
		return answer
	else:
		send.message('Invalid argument')

def freq_counter_command(command):
	device_write(command)

def freq_counter_query(command):
	answer = device_query(command)
	return answer


if __name__ == "__main__":
    main()