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
path_config_file = os.path.join(path_current_directory, 'config','SR830_config.ini')

# configuration data
config = cutil.read_conf_util(path_config_file)

# auxilary dictionaries
sensitivity_dict = {'2 nV': 0, '5 nV': 1, '10 nV': 2, '20 nV': 3, '50 nV': 4,
					'100 nV': 5, '200 nV': 6, '500 nV': 7, '1 uV': 8, '2 uV': 9, '5 uV': 10,
					'10 uV': 11, '20 uV': 12, '50 uV': 13, '100 uV': 14, '200 uV': 15, '500 uV': 16, 
					'1 mV': 17, '2 mV': 18, '5 mV': 19, '10 mV': 20, '20 mV': 21, '50 mV': 22,
					'100 mV': 23, '200 mV': 24, '500 mV': 25, '1 V': 26};
helper_sens_list = [2, 5, 10, 20, 50, 100, 200, 500]
timeconstant_dict = {'10 us': 0, '30 us': 1, '100 us': 2, '300 us': 3,
					'1 ms': 4, '3 ms': 5, '10 ms': 6, '30 ms': 7, '100 ms': 8, '300 ms': 9,
					'1 s': 10, '3 s': 11, '10 s': 12, '30 s': 13, '100 s': 14, '300 s': 15, 
					'1 ks': 16, '3 ks': 17, '10 ks': 18, '30 ks': 19};
helper_tc_list = [1, 3, 10, 30, 100, 300]

# Ranges and limits
ref_freq_min = 0.001
ref_freq_max = 102000
ref_ampl_min = 0.004
ref_ampl_max = 5
harm_max = 19999
harm_min = 1

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
			send.message("No connection")
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
			send.message("No connection")
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
		send.message("No Connection")

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
		send.message("No Connection")

#### Device specific functions
def lock_in_name():
	answer = device_query('*IDN?')
	return answer

def lock_in_ref_frequency(*frequency):
	if len(frequency)==1:
		freq = float(frequency[0])
		if freq >= ref_freq_min and freq <= ref_freq_max:
			device_write('FREQ '+ str(freq))
		else:
			send.message("Incorrect frequency")
	elif len(frequency)==0:
		answer = float(device_query('FREQ?'))
		return answer
	else:
		send.message("Invalid Argument")

def lock_in_phase(*degree):
	if len(degree)==1:
		degs = float(degree[0])
		if degs >= -360 and degs <= 729:
			device_write('PHAS '+str(degs))
		else:
			send.message("Incorrect phase")
	elif len(degree)==0:
		answer = float(device_query('PHAS?'))
		return answer
	else:
		send.message("Invalid Argument")

def lock_in_time_constant(*timeconstant):
	if  len(timeconstant)==1:
		temp = timeconstant[0].split(' ')
		number_tc = min(helper_tc_list, key=lambda x: abs(x - int(temp[0])))
		if int(number_tc) != int(temp[0]):
			send.message("Desired time constant cannot be set, the nearest available value is used")
		tc = str(number_tc)+' '+temp[1]
		if tc in timeconstant_dict:
			flag = timeconstant_dict[tc]
			device_write("OFLT "+ str(flag))
		else:
			send.message("Invalid time constant value (too high/too low)")
	elif len(timeconstant)==0:
		raw_answer = int(device_query("OFLT?"))
		answer = cutil.search_keys_dictionary(timeconstant_dict, raw_answer)
		return answer
	else:
		send.message("Invalid Argument")

def lock_in_ref_amplitude(*amplitude):
	if len(amplitude)==1:
		ampl = float(amplitude[0]);
		if ampl <= ref_ampl_max and ampl >= ref_ampl_min:
			device_write('SLVL '+str(ampl))
		else:
			device_write('SLVL '+ str(ref_ampl_min))
			send.message("Invalid Argument")
	elif len(amplitude)==0:
		answer = float(device_query("SLVL?"))
		return answer
	else:
		send.message("Invalid Argument")

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
	if  len(sensitivity)==1:
		temp = sensitivity[0].split(' ')
		number_sens = min(helper_sens_list, key=lambda x: abs(x - int(temp[0])))
		sens = str(number_sens)+' '+temp[1]
		if int(number_sens) != int(temp[0]):
			send.message("Desired sensitivity cannot be set, the nearest available value is used")
		if sens in sensitivity_dict:
			flag = sensitivity_dict[sens]
			device_write("SCAL "+ str(flag))
		else:
			send.message("Invalid sensitivity value (too high/too low)")
	elif len(sensitivity)==0:
		raw_answer = int(device_query("SCAL?"))
		answer = cutil.search_keys_dictionary(sensitivity_dict, raw_answer)
		return answer
	else:
		send.message("Invalid Argument")

def lock_in_ref_mode(*mode):
	if len(mode)==1:
		flag = int(mode[0]);
		if flag==0:
			device_write('FMOD '+str(flag))
		elif flag==1:
			device_write('FMOD '+str(flag))
		else:
			send.message("Invalid Argument")
	elif len(mode)==0:
		answer = int(device_query("FMOD?"))
		return answer
	else:
		send.message("Invalid Argument")

def lock_in_ref_slope(*mode):
	if len(mode)==1:
		flag = int(mode[0]);
		if flag==0:
			device_write('RSLP '+str(flag))
		elif flag==1:
			device_write('RSLP '+str(flag))
		elif flag==2:
			device_write('RSLP '+str(flag))
		else:
			send.message("Invalid Argument")
	elif len(mode)==0:
		answer = int(device_query("RSLP?"))
		return answer
	else:
		send.message("Invalid Argument")

def lock_in_sync_filter(*mode):
	if len(mode)==1:
		flag = int(mode[0]);
		if flag==0:
			device_write('SYNC '+str(flag))
		elif flag==1:
			device_write('SYNC '+str(flag))
		else:
			send.message("Invalid Argument")
	elif len(mode)==0:
		answer = int(device_query("SYNC?"))
		return answer
	else:
		send.message("Invalid Argument")

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
			send.message("Invalid Argument")
	elif len(mode)==0:
		answer = int(device_query("OFSL?"))
		return answer
	else:
		send.message("Invalid Argument")

def lock_in_harmonic(*harmonic):
	if len(harmonic)==1:
		harm = int(harmonic[0]);
		if harm <= harm_max and harm >= harm_min:
			device_write('HARM '+ str(harm))
		else:
			device_write('HARM '+ str(harm_min))
			send.message("Invalid Argument")
	elif len(harmonic)==0:
		answer = int(device_query("HARM?"))
		return answer
	else:
		send.message("Invalid Argument")

def lock_in_command(command):
	device_write(command)

def lock_in_query(command):
	answer = device_query(command)
	return answer


if __name__ == "__main__":
    main()