#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import gc
import sys
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
helper_sens_list = [1, 2, 5, 10, 20, 50, 100, 200, 500]
timeconstant_dict = {'1 us': 0, '3 us': 1, '10 us': 2, '30 us': 3, '100 us': 4, '300 us': 5,
					'1 ms': 6, '3 ms': 7, '10 ms': 8, '30 ms': 9, '100 ms': 10, '300 ms': 11,
					'1 s': 12, '3 s': 13, '10 s': 14, '30 s': 15, '100 s': 16, '300 s': 17, 
					'1 ks': 18, '3 ks': 19, '10 ks': 20, '30 ks': 21};
helper_tc_list = [1, 3, 10, 30, 100, 300]
ref_mode_dict = {'Internal': 0, 'External': 1, 'Dual': 2, 'Chop': 3}
ref_slope_dict = {'Sine': 0, 'PosTTL': 1, 'NegTTL': 2}
sync_dict = {'Off': 0, 'On': 1}
lp_fil_dict = {'6 db': 0, '12 dB': 1, "18 dB": 2, "24 dB":3}

# Ranges and limits
ref_freq_min = 0.001
ref_freq_max = 500000
ref_ampl_min = 0.000000001
ref_ampl_max = 2
harm_max = 99
harm_min = 1


#### Basic interaction functions
def connection():
	global status_flag
	global device
	if config['interface'] == 'gpib':
		try:
			import Gpib
			status_flag = 1
			device = Gpib.Gpib(config['board_address'], config['gpib_address'])
			try:
				# test should be here
				answer = int(device_query('*TST?'))
				if answer==0:
					status_flag = 1;
				else:
					send.message('During test errors are found')
					status_flag = 0;
					sys.exit();
			except pyvisa.VisaIOError:
				send.message("No connection")
				status_flag = 0;
				sys.exit();
		except pyvisa.VisaIOError:
			send.message("No connection")
			device.close()
			status_flag = 0
			sys.exit();
	elif config['interface'] == 'rs232':
		try:
			status_flag = 1
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
					send.message('During test errors are found')
					status_flag = 0;
					sys.exit();
			except pyvisa.VisaIOError:
				status_flag = 0;
				device.close()
				send.message("No connection")
				sys.exit();
		except pyvisa.VisaIOError:
			send.message("No connection")
			device.close()
			status_flag = 0
			sys.exit();
	elif config['interface'] == 'ethernet':
		try:
			status_flag=1;
			rm = pyvisa.ResourceManager()
			device=rm.open_resource(config['ethernet_address'])
			device.timeout=config['timeout']; # in ms
			try:
				# test should be here
				answer = int(device_query('*TST?'))
				if answer==0:
					status_flag = 1;
				else:
					send.message('During test errors are found')
					status_flag = 0;
					sys.exit();
			except pyvisa.VisaIOError:
				send.message("No connection")
				device.close()
				status_flag = 0;
				sys.exit();
		except pyvisa.VisaIOError:
			send.message("No connection")
			device.close()
			status_flag = 0
			sys.exit();

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
		sys.exit()

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
		send.message("No Connection")
		sys.exit()

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
		if degs >= -360000 and degs <= 360000:
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
	if  len(mode)==1:
		md = str(mode[0])
		if md in ref_mode_dict:
			flag = ref_mode_dict[md]
			device_write("RSRC "+ str(flag))
		else:
			send.message("Invalid mode")
	elif len(mode)==0:
		raw_answer = int(device_query("RSRC?"))
		answer = cutil.search_keys_dictionary(ref_mode_dict, raw_answer)
		return answer
	else:
		send.message("Invalid argumnet")

def lock_in_ref_slope(*mode):
	if  len(mode)==1:
		md = str(mode[0])
		if md in ref_slope_dict:
			flag = ref_slope_dict[md]
			device_write("RTRG "+ str(flag))
		else:
			send.message("Invalid mode")
	elif len(mode)==0:
		raw_answer = int(device_query("RTRG?"))
		answer = cutil.search_keys_dictionary(ref_slope_dict, raw_answer)
		return answer
	else:
		send.message("Invalid argumnet")

def lock_in_sync_filter(*mode):
	if  len(mode)==1:
		md = str(mode[0])
		if md in sync_dict:
			flag = sync_dict[md]
			device_write("SYNC "+ str(flag))
		else:
			send.message("Invalid argument")
	elif len(mode)==0:
		raw_answer = int(device_query("SYNC?"))
		answer = cutil.search_keys_dictionary(sync_dict, raw_answer)
		return answer
	else:
		send.message("Invalid argumnet")

def lock_in_lp_filter(*mode):
	if  len(mode)==1:
		md = str(mode[0])
		if md in lp_fil_dict:
			flag = lp_fil_dict[md]
			device_write("OFSL "+ str(flag))
		else:
			send.message("Invalid mode")
	elif len(mode)==0:
		raw_answer = int(device_query("OFSL?"))
		answer = cutil.search_keys_dictionary(lp_fil_dict, raw_answer)
		return answer
	else:
		send.message("Invalid argumnet")

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

