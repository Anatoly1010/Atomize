#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import gc
import time
import pyvisa
import atomize.device_modules.config.config_utils as cutil
import atomize.device_modules.config.messenger_socket_client as send

#### Inizialization
# setting path to *.ini file
path_current_directory = os.path.dirname(__file__)
path_config_file = os.path.join(path_current_directory, 'config','lakeshore340_config.ini')

# configuration data
config = cutil.read_conf_util(path_config_file)
loop = config['loop'] # information about the loop used

# auxilary dictionaries
heater_dict = {'10 W': 5, '1 W': 4, 'Off': 0};

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
				answer = device_query('*TST?')
				if answer==0:
					status_flag = 1;
				elif answer==1:
					print('During test errors are found')
					status_flag = 0;
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
				answer = device_query('*TST?')
				if answer==0:
					status_flag = 1;
				elif answer==1:
					print('During test errors are found')
					status_flag = 0;
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
def tc_name():
	answer = config['name'] 
	return answer

def tc_temperature(channel):
	if channel=='A':
		try:
			answer = float(device_query('KRDG? A'))
		except TypeError:
			answer = 'No Connection';
		return answer
	elif channel=='B':
		try:
			answer = float(device_query('KRDG? B'))
		except TypeError:
			answer = 'No Connection';
		return answer
	elif channel=='C':
		try:
			answer = float(device_query('KRDG? C'))
		except TypeError:
			answer = 'No Connection';
		return answer
	elif channel=='D':
		try:
			answer = float(device_query('KRDG? D'))
		except TypeError:
			answer = 'No Connection';
		return answer
	else:
		print("Invalid Argument")

def tc_setpoint(*temp):
	if len(temp)==1:
		temp = float(temp[0]);
		if temp < 310 and temp > 0.5:
			device.write('SETP '+ str(loop) + ', ' + str(temp))
		else:
			print("Invalid Argument")
	elif len(temp)==0:
		try:
			answer = float(device_query('SETP? '+ str(loop)))
		except TypeError:
			answer = 'No Connection';
		return answer	
	else:
		print("Invalid Argument")

def tc_heater_range(*heater):
	if  len(heater)==1:
		hr = str(heater[0])
		if hr in heater_dict:
			flag = heater_dict[hr]
			device_write("RANGE " + str(loop) + ', ' + str(flag))
		else:
			print("Invalid heater range")
	elif len(heater)==0:
		raw_answer = int(device_query("RANGE?"))
		answer = cutil.search_keys_dictionary(heater_dict, raw_answer)
		return answer
	else:
		print("Invalid Argument")								

def tc_heater_state():
	answer1 = tc_heater_range()
	try:
		answer = float(device_query('HTR?'))
	except TypeError:
		answer = 'No Connection';
	full_answer = [answer, answer1]
	return full_answer

def tc_command(command):
	device_write(command)

def tc_query(command):
	answer = device_query(command)
	return answer

if __name__ == "__main__":
    main()