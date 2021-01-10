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
path_config_file = os.path.join(path_current_directory, 'config','SR860_config.ini')

# configuration data
config = cutil.read_conf_util(path_config_file)

# auxilary dictionaries
sensitivity_dict = {'1 nV': 27, '2 nV': 26, '5 nV': 25, '10 nV': 24, '20 nV': 23, '50 nV': 22,
					'100 nV': 21, '200 nV': 20, '500 nV': 19, '1 uV': 18, '2 uV': 17, '5 uV': 16,
					'10 uV': 15, '20 uV': 14, '50 uV': 13, '100 uV': 12, '200 uV': 11, '500 uV': 10, 
					'1 mV': 9, '2 mV': 8, '5 mV': 7, '10 mV': 6, '20 mV': 5, '50 mV': 4,
					'100 mV': 3, '200 mV': 2, '500 mV': 1, '1 V': 0};
timeconstant_dict = {'1 us': 0, '3 us': 1, '10 us': 2, '30 us': 3, '100 us': 4, '300 us': 5,
					'1 ms': 6, '3 ms': 7, '10 ms': 8, '30 ms': 9, '100 ms': 10, '300 ms': 11,
					'1 s': 12, '3 s': 13, '10 s': 14, '30 s': 15, '100 s': 16, '300 s': 17, 
					'1 ks': 18, '3 ks': 19, '10 ks': 20, '30 ks': 21};

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
				answer = int(device_query('*TST?'))
				if answer==0:
					status_flag = 1;
				else:
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
				answer = int(device_query('*TST?'))
				if answer==0:
					status_flag = 1;
				else:
					print('During test errors are found')
					status_flag = 0;
			except pyvisa.VisaIOError:
				status_flag = 0;	
		except pyvisa.VisaIOError:
			print("No connection")
			device.close()
			status_flag = 0
	elif config['interface'] == 'ethernet':
		try:
			rm = pyvisa.ResourceManager()
			device=rm.open_resource(config['ethernet_address'], read_termination=config['read_termination'],
			write_termination=config['write_termination'])
			device.timeout=config['timeout']; # in ms
			try:
				# test should be here
				answer = int(device_query('*TST?'))
				if answer==0:
					status_flag = 1;
				else:
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
		elif config['interface'] == 'ethernet':
			answer = device.query(command)
		return answer
	else:
		print("No Connection")

#### Device specific functions
def lock_in_name():
	answer = device_query('*IDN?')
	return answer

def lock_in_ref_frequency(*frequency):
	if len(frequency)==1:
		freq = float(frequency[0])
		if freq >= 0.001 and freq <= 500000:
			device_write('FREQ '+ str(freq))
		else:
			print("Incorrect phase")
	elif len(frequency)==0:
		answer = float(device_query('FREQ?'))
		return answer
	else:
		print("Invalid Argument")

def lock_in_phase(*degree):
	if len(degree)==1:
		degs = float(degree[0])
		if degs >= -360000 and degs <= 360000:
			device_write('PHAS '+str(degs))
		else:
			print("Incorrect phase")
	elif len(degree)==0:
		answer = float(device_query('PHAS?'))
		return answer
	else:
		print("Invalid Argument")

def lock_in_time_constant(*timeconstant):
	if  len(timeconstant)==1:
		tc = str(timeconstant[0])
		if tc in timeconstant_dict:
			flag = timeconstant_dict[tc]
			device_write("OFLT "+ str(flag))
		else:
			print("Invalid sensitivity value")
	elif len(timeconstant)==0:
		raw_answer = int(device_query("OFLT?"))
		answer = cutil.search_keys_dictionary(timeconstant_dict, raw_answer)
		return answer
	else:
		print("Invalid Argument")

def lock_in_ref_amplitude(*amplitude):
	if len(amplitude)==1:
		ampl = float(amplitude[0]);
		if ampl <= 2 and ampl >= 0.000000001:
			device_write('SLVL '+str(ampl))
		else:
			device_write('SLVL '+'0.000000001')
			print("Invalid Argument")
	elif len(amplitude)==0:
		answer = float(device_query("SLVL?"))
		return answer
	else:
		print("Invalid Argument")

def lock_in_get_data(*channel):
	if len(channel)==0:
		answer = float(device_query('OUTP? 0'))
		return answer
	elif len(channel)==1 and int(channel[0])==1:
		answer = float(device_query('OUTP? 0'))
		return answer
	elif len(channel)==1 and int(channel[0])==2:
		answer = float(device_query('OUTP? 1'))
		return answer
	elif len(channel)==1 and int(channel[0])==3:
		answer = float(device_query('OUTP? 2'))
		return answer
	elif len(channel)==1 and int(channel[0])==4:
		answer = float(device_query('OUTP? 3'))
		return answer
	elif len(channel)==2 and int(channel[0])==1 and int(channel[1])==2:
		answer_string = device_query('SNAP? 0,1')
		answer_list = answer_string.split(',')
		list_of_floats = [float(item) for item in answer_list]
		x = list_of_floats[0]
		y = list_of_floats[1]
		return x, y
	elif len(channel)==3 and int(channel[0])==1 and int(channel[1])==2 and int(channel[2])==3:
		answer_string = device_query('SNAP? 0,1,2')
		answer_list = answer_string.split(',')
		list_of_floats = [float(item) for item in answer_list]
		x = list_of_floats[0]
		y = list_of_floats[1]
		r = list_of_floats[2]
		return x, y, r

def lock_in_sensitivity(*sensitivity):
	if  len(sensitivity)==1:
		sens = str(sensitivity[0])
		if sens in sensitivity_dict:
			flag = sensitivity_dict[sens]
			device_write("SCAL "+ str(flag))
		else:
			print("Invalid sensitivity value")
	elif len(sensitivity)==0:
		raw_answer = int(device_query("SCAL?"))
		answer = cutil.search_keys_dictionary(sensitivity_dict, raw_answer)
		return answer
	else:
		print("Invalid Argument")

def lock_in_ref_mode(*mode):
	if len(mode)==1:
		flag = int(mode[0]);
		if flag==0:
			device_write('RSRC '+str(flag))
		elif flag==1:
			device_write('RSRC '+str(flag))
		elif flag==2:
			device_write('RSRC '+str(flag))
		elif flag==3:
			device_write('RSRC '+str(flag))
		else:
			print("Invalid Argument")
	elif len(mode)==0:
		answer = int(device_query("RSRC?"))
		return answer
	else:
		print("Invalid Argument")

def lock_in_ref_slope(*mode):
	if len(mode)==1:
		flag = int(mode[0]);
		if flag==0:
			device_write('RTRG '+str(flag))
		elif flag==1:
			device_write('RTRG '+str(flag))
		elif flag==2:
			device_write('RTRG '+str(flag))
		else:
			print("Invalid Argument")
	elif len(mode)==0:
		answer = int(device_query("RTRG?"))
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
		answer = int(device_query("SYNC?"))
		return answer
	else:
		print("Invalid Argument")

def lock_in_lp_filter(*mode):
	if len(mode)==1:
		flag = int(mode[0]);
		if flag==0:
			device_write('OFSL '+str(flag))
		elif flag==1:
			device_write('OFSL '+str(flag))
		elif flag==2:
			device_write('OFSL '+str(flag))
		elif flag==3:
			device_write('OFSL '+str(flag))
		else:
			print("Invalid Argument")
	elif len(mode)==0:
		answer = int(device_query("OFSL?"))
		return answer
	else:
		print("Invalid Argument")

def lock_in_harmonic(*harmonic):
	if len(harmonic)==1:
		harm = int(harmonic[0]);
		if harm <= 99 and harm >= 1:
			device_write('HARM '+ str(harm))
		else:
			device_write('HARM '+'1')
			print("Invalid Argument")
	elif len(harmonic)==0:
		answer = int(device_query("HARM?"))
		return answer
	else:
		print("Invalid Argument")

def lock_in_command(command):
	device_write(command)

def lock_in_query(command):
	answer = device_query(command)
	return answer

#if __name__ == "__main__":
#    main()