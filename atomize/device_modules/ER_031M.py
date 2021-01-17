#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import gc
import time
import pyvisa
from pyvisa.constants import StopBits, Parity
import atomize.device_modules.config.config_utils as cutil
import atomize.device_modules.config.messenger_socket_client as send

#### Inizialization
# setting path to *.ini file
path_current_directory = os.path.dirname(__file__)
path_config_file = os.path.join(path_current_directory, 'config','ER_031M_config.ini')

# configuration data
config = cutil.read_conf_util(path_config_file)

#### Basic interaction functions
def connection():
	global status_flag
	global device

	if config['interface'] == 'rs232':
		try:
			rm = pyvisa.ResourceManager()
			device=rm.open_resource(config['serial_address'],
			write_termination=config['write_termination'], baud_rate=config['baudrate'],
			data_bits=config['databits'], parity=config['parity'], stop_bits=config['stopbits'])
			device.timeout=config['timeout']; # in ms
			try:
				# test should be here
				status_flag = 1;
			except pyvisa.VisaIOError:
				status_flag = 0;	
		except pyvisa.VisaIOError:
			send.message("No connection")
			device.close()
			status_flag = 0

def close_connection():
	status_flag=0;
	devie.close()
	gc.collect()

def device_write(command):
	if status_flag == 1:
		time.sleep(1)		# very important to have timeout here
		device.write(command.encode())
	else:
		status_flag = 0;
		send.message("No Connection")

#### Device specific functions
def magnet_name():
	answer = config['name']
	return answer

def magnet_field(*field):
	if len(field)==1:
		#field_controller_write('cf'+str(field)+'\r')
		device_write('cf'+str(field))
	else:
		send.message("Invalid argument")

def magnet_command(command):
	device_write(command)
	#field_controller_write(command+'\r')


if __name__ == "__main__":
    main()