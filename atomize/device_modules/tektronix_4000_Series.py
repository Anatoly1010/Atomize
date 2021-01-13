#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import gc
import time
import pyvisa
import numpy as np 
import atomize.device_modules.config.config_utils as cutil
import atomize.device_modules.config.messenger_socket_client as send

#### Inizialization
# setting path to *.ini file
path_current_directory = os.path.dirname(__file__)
path_config_file = os.path.join(path_current_directory, 'config','tektronix_4032_config.ini')

# configuration data
config = cutil.read_conf_util(path_config_file)

# auxilary dictionaries
number_averag_list = [2, 4, 8, 16, 32, 64, 128, 256, 512]
points_list = [1000, 10000, 100000, 1000000, 10000000];
timebase_dict = {' s': 1, 'ms': 1000, 'us': 1000000, 'ns': 1000000000,};
timebase_helper_list = [1, 2, 4, 10, 20, 40, 100, 200, 400]
scale_dict = {' V': 1, 'mV': 1000,};
ac_type_dic = {'Norm': "SAMple", 'Ave': "AVErage", 'Hres': "HIRes",'Peak': "PEAKdetect"}

#### Basic interaction functions
def connection():
	global status_flag
	global device

	if config['interface'] == 'ethernet':
		rm = pyvisa.ResourceManager()
		try:
			status_flag = 1
			device=rm.open_resource(config['ethernet_address'])
			device.timeout=config['timeout']; # in ms
			device.read_termination = config['read_termination']
			try:
				# test should be here
				answer = int(device_query('*TST?'))
				if answer==0:
					status_flag = 1;
				else:
					send.message('During test errors are found')
					status_flag = 0;
					sys.exit()
			except pyvisa.VisaIOError:
				send.message("No connection")
				status_flag = 0;
				device.close()
				sys.exit()
		except pyvisa.VisaIOError:
			send.message("No connection")
			device.close()
			status_flag = 0
			sys.exit()

def close_connection():
	status_flag = 0;
	gc.collect()
	device.close()

def device_write(command):
	if status_flag == 1:
		command = str(command)
		device.write(command)
	else:
		send.message("No connection")
		sys.exit()

def device_query(command):
	if status_flag == 1:
		answer = device.query(command)
		return answer
	else:
		send.message("No connection")
		sys.exit()

def device_query_ascii(command):
	if status_flag == 1:
		answer = device.query_ascii_values(command, converter='f',separator=',',container=np.array)
		return answer
	else:
		send.message("No connection")
		sys.exit()

def device_read_binary(command):
	if status_flag==1:
		answer = device.query_binary_values(command,'b', is_big_endian=True, container=np.array)
		# RPBinary, value from 0 to 255. 'b'
		# Endianness is primarily expressed as big-endian (BE) or little-endian (LE).
		# A big-endian system stores the most significant byte of a word at the smallest memory address 
		# and the least significant byte at the largest. A little-endian system, in contrast, stores 
		# the least-significant byte at the smallest address.
		return answer
	else:
		send.message("No connection")
		sys.exit()

#### Device specific functions
def oscilloscope_name():
	answer = device_query('*IDN?')
	return answer

def oscilloscope_define_window(**kargs):
	try:
		st = int(kargs['start']);
		stop = int(kargs['stop']);
		points = oscilloscope_record_length()
		if stop > points or st > points:
			send.message('Invalid arguments')
		else:
			device_write("DATa:STARt "+ str(st))
			device_write("DATa:STOP "+ str(stop))
	except KeyError:
		answer1 = int(device_query('DATa:STARt?'))
		answer2 = int(device_query('DATa:STOP?'))
		return answer1, answer2

def oscilloscope_record_length(*points):
	if len(points)==1:
		temp = int(points[0]);
		poi = min(points_list, key=lambda x: abs(x - temp))
		if int(poi) != temp:
			send.message("Desired record length cannot be set, the nearest available value is used")
		device_write("HORizontal:RECOrdlength "+ str(poi))
	elif len(points)==0:
		answer = int(device_query('HORizontal:RECOrdlength?'))
		return answer
	else:
		send.message("Invalid argument")

def oscilloscope_acquisition_type(*ac_type):
	if  len(ac_type)==1:
		at = str(ac_type[0])
		if at in ac_type_dic:
			flag = ac_type_dic[at]
			device_write("ACQuire:MODe "+ str(flag))
		else:
			send.message("Invalid acquisition type")
	elif len(ac_type)==0:
		answer = str(device_query("ACQuire:MODe?"))
		return answer
	else:
		send.message("Invalid argumnet")

def oscilloscope_number_of_averages(*number_of_averages):
	if len(number_of_averages)==1:
		temp = int(number_of_averages[0]);
		numave = min(number_averag_list, key=lambda x: abs(x - temp))
		if int(numave) != temp:
			send.message("Desired number of averages cannot be set, the nearest available value is used")
		ac = oscilloscope_acquisition_type()
		if ac == 'AVE':
			device_write("ACQuire:NUMAVg " + str(numave))
		elif ac == 'SAM':
			send.message("Your are in SAMple mode")
		elif ac == 'HIR':
			send.message("Your are in HRES mode")
		elif ac == 'PEAK':
			send.message("Your are in PEAK mode")
	elif len(number_of_averages)==0:
		answer = int(device_query("ACQuire:NUMAVg?"))
		return answer
	else:
		send.message("Invalid argument")

def oscilloscope_timebase(*timebase):
	if  len(timebase)==1:
		temp = timebase[0].split(' ')
		if temp[1] == 'ns' and float(temp[0])>=60 and float(temp[0])<=90:
			if timebase!='80 ns':
				device_write("HORizontal:SCAle "+ str(80/1000000000))
				send.message("Desired time constant cannot be set, the nearest available value is used")
			else:
				device_write("HORizontal:SCAle "+ str(80/1000000000))				
		else:
			number_tb = min(timebase_helper_list, key=lambda x: abs(x - int(temp[0])))
			if int(number_tb) != int(temp[0]):
				send.message("Desired time constant cannot be set, the nearest available value is used")
			if temp[1] in timebase_dict:
				coef = timebase_dict[temp[1]]
				device_write("HORizontal:SCAle "+ str(number_tb/coef))
			else:
				send.message("Incorrect timebase")
	elif len(timebase)==0:
		answer = float(device_query("HORizontal:SCAle?"))*1000000
		return answer
	else:
		send.message("Invalid argument")

def oscilloscope_time_resolution():
	points = int(oscilloscope_record_length())
	answer = 1000000*float(device_query("HORizontal:SCAle?"))/points
	return answer

def oscilloscope_start_acquisition():
	#start_time = time.time()
	device_query('*ESR?')
	device_write('ACQuire:STATE RUN;:ACQuire:STOPAfter SEQ')
	device_query('*OPC?') # return 1, if everything is ok;
	# the whole sequence is the following 1-clearing; 2-3-digitizing; 4-checking of the completness
	#end_time=time.time()
	send.message('Acquisition completed') 
	#send.message("Duration of Acquisition: {}".format(end_time - start_time))

def oscilloscope_preamble(channel):
	if channel=='CH1':
		device_write('DATa:SOUrce CH1')
		preamble = device_query("WFMOutpre?")
	elif channel=='CH2':
		device_write('DATa:SOUrce CH2')
		preamble = device_query("WFMOutpre?")
	elif channel=='CH3':
		device_write('DATa:SOUrce CH3')
		preamble = device_query("WFMOutpre?")
	elif channel=='CH4':
		device_write('DATa:SOUrce CH4')
		preamble = device_query("WFMOutpre?")
	else:
		send.message("Invalid channel is given")	
	return preamble

def oscilloscope_stop():
	device_write("ACQuire:STATE STOP")

def oscilloscope_run():
	device_write("ACQuire:STATE RUN")

def oscilloscope_get_curve(channel):
	if channel=='CH1':
		device_write('DATa:SOUrce CH1')
	elif channel=='CH2':
		device_write('DATa:SOUrce CH2')
	elif channel=='CH3':
		device_write('DATa:SOUrce CH3')
	elif channel=='CH4':
		device_write('DATa:SOUrce CH4')
	else:
		send.message("Invalid channel is given")
		
	device_write('DATa:ENCdg RIBinary')

	array_y = device_read_binary('CURVe?')
	#x_orig=float(device_query("WFMOutpre:XZEro?"))
	#x_inc=float(device_query("WFMOutpre:XINcr?"))
	#send.message(preamble)
	y_ref=float(device_query("WFMOutpre:YOFf?"))
	y_inc=float(device_query("WFMOutpre:YMUlt?"))
	y_orig=float(device_query("WFMOutpre:YZEro?"))
	#send.message(y_inc)
	#send.message(y_orig)
	#send.message(y_ref)
	array_y = (array_y - y_ref)*y_inc + y_orig
	#array_x= list(map(lambda x: x_inc*(x+1) + x_orig, list(range(len(array_y)))))
	#final_data = np.asarray(list(zip(array_x,array_y)))

	return array_y

def oscilloscope_sensitivity(*channel):
	if len(channel)==2:
		temp = channel[1].split(" ")
		ch = str(channel[0])
		val = float(temp[0])
		scaling = str(temp[1]);
		if scaling in scale_dict:
			coef = scale_dict[scaling]
			if ch == 'CH1':
				device_write("CH1:SCAle "+str(val/coef))
			elif ch == 'CH2':
				device_write("CH2:SCAle "+str(val/coef))
			elif ch == 'CH3':
				device_write("CH3:SCAle "+str(val/coef))
			elif ch == 'CH4':
				device_write("CH4:SCAle "+str(val/coef))
			else:
				send.message("Incorrect channel is given")
		else:
			send.message("Incorrect scaling factor")
	elif len(channel)==1:
		ch = str(channel[0])
		if ch == 'CH1':
			answer = float(device_query("CH1:SCAle?"))*1000
			return answer
		elif ch == 'CH2':
			answer = float(device_query("CH2:SCAle?"))*1000
			return answer
		elif ch == 'CH3':
			answer = float(device_query("CH3:SCAle?"))*1000
			return answer
		elif ch == 'CH4':
			answer = float(device_query("CH4:SCAle?"))*1000
			return answer
		else:
			send.message("Incorrect channel is given")
	else:
		send.message("Invalid argument")

def oscilloscope_offset(*channel):
	if len(channel)==2:
		temp = channel[1].split(" ")
		ch = str(channel[0])
		val = float(temp[0])
		scaling = str(temp[1]);
		if scaling in scale_dict:
			coef = scale_dict[scaling]
			if ch == 'CH1':
				device_write("CH1:OFFSet "+str(val/coef))
			elif ch == 'CH2':
				device_write("CH2:OFFSet "+str(val/coef))
			elif ch == 'CH3':
				device_write("CH3:OFFSet "+str(val/coef))
			elif ch == 'CH4':
				device_write("CH4:OFFSet "+str(val/coef))
			else:
				send.message("Incorrect channel is given")
		else:
			send.message("Incorrect scaling factor")
	elif len(channel)==1:
		ch = str(channel[0])
		if ch == 'CH1':
			answer = float(device_query("CH1:OFFSet?"))*1000
			return answer
		elif ch == 'CH2':
			answer = float(device_query("CH2:OFFSet?"))*1000
			return answer
		elif ch == 'CH3':
			answer = float(device_query("CH3:OFFSet?"))*1000
			return answer
		elif ch == 'CH4':
			answer = float(device_query("CH4:OFFSet?"))*1000
			return answer
		else:
			send.message("Incorrect channel is given")
	else:
		send.message("Invalid argument")

def oscilloscope_trigger_delay(*delay):
	if len(delay)==1:
		temp = delay[0].split(" ")
		offset = float(temp[0])
		scaling = temp[1];
		if scaling in timebase_dict:
			coef = timebase_dict[scaling]
			device_write("HORizontal:DELay:TIMe "+ str(offset/coef))
		else:
			send.message("Incorrect trigger delay")
	elif len(delay)==0:
		answer = float(device_query("HORizontal:DELay:TIMe?"))*1000000
		return answer
	else:
		send.message("Invalid argument")

def oscilloscope_coupling(*coupling):
	if len(coupling)==2:
		ch = str(coupling[0])
		cpl = str(coupling[1])
		if ch == 'CH1':
			device_write("CH1:COUPling "+str(cpl))
		elif ch == 'CH2':
			device_write("CH2:COUPling "+str(cpl))
		elif ch == 'CH3':
			device_write("CH3:COUPling "+str(cpl))
		elif ch == 'CH4':
			device_write("CH4:COUPling "+str(cpl))
		else:
			send.message("Incorrect channel is given")
	elif len(coupling)==1:
		ch = str(coupling[0])
		if ch == 'CH1':
			answer = device_query("CH1:COUPling?")
			return answer
		elif ch == 'CH2':
			answer = device_query("CH2:COUPling?")
			return answer
		elif ch == 'CH3':
			answer = device_query("CH3:COUPling?")
			return answer
		elif ch == 'CH4':
			answer = device_query("CH4:COUPling?")
			return answer
		else:
			send.message("Incorrect channel is given")
	else:
		send.message("Invalid argument")

def oscilloscope_impedance(*impedance):
	if len(impedance)==2:
		ch = str(impedance[0])
		cpl = str(impedance[1])
		if cpl == '1 M':
			cpl = 'MEG';
		elif cpl == '50':
			cpl = 'FIFty';
		if ch == 'CH1':
			device_write("CH1:TERmination "+str(cpl))
		elif ch == 'CH2':
			device_write("CH2:TERmination "+str(cpl))
		elif ch == 'CH3':
			device_write("CH3:TERmination "+str(cpl))
		elif ch == 'CH4':
			device_write("CH4:TERmination "+str(cpl))
		else:
			send.message("Incorrect channel is given")
	elif len(impedance)==1:
		ch = str(impedance[0])
		if ch == 'CH1':
			answer = device_query("CH1:TERmination?")
			return answer
		elif ch == 'CH2':
			answer = device_query("CH2:TERmination?")
			return answer
		elif ch == 'CH3':
			answer = device_query("CH3:TERmination?")
			return answer
		elif ch == 'CH4':
			answer = device_query("CH4:TERmination?")
			return answer
		else:
			send.message("Incorrect channel is given")
	else:
		send.message("Invalid argument")

def oscilloscope_trigger_mode(*mode):
	if len(mode)==1:
		md = str(mode[0])
		if md == 'Auto':
			device_write("TRIGger:A:MODe "+'AUTO')
		elif md == 'Normal':
			device_write("TRIGger:A:MODe "+'NORMal')
		else:
			send.message("Incorrect trigger mode is given")
	elif len(mode)==0:
		answer = device_query("TRIGger:A:MODe?")
		return answer
	else:
		send.message("Invalid argument")

def oscilloscope_trigger_channel(*channel):
	if len(channel)==1:
		ch = str(channel[0])
		if ch == 'CH1':
			device_write("TRIGger:A:EDGE:SOUrce "+'CH1')
		elif ch == 'CH2':
			device_write("TRIGger:A:EDGE:SOUrce "+'CH2')
		elif ch == 'CH3':
			device_write("TRIGger:A:EDGE:SOUrce "+'CH3')
		elif ch == 'CH4':
			device_write("TRIGger:A:EDGE:SOUrce "+'CH4')
		elif ch == 'Line':
			device_write("TRIGger:A:EDGE:SOUrce "+'LINE')
		else:
			send.message("Incorrect trigger channel is given")
	elif len(channel)==0:
		answer = device_query("TRIGger:A:EDGE:SOUrce?")
		return answer
	else:
		send.message("Invalid argument")

def oscilloscope_trigger_low_level(*level):
	if len(level)==2:
		ch = str(level[0])
		lvl = level[1]
		if lvl!='ECL' and lvl!='TTL':
			lvl = float(level[1])
		if ch == 'CH1':
			device_write("TRIGger:A:LEVel:CH1"+str(lvl))
		elif ch == 'CH2':
			device_write("TRIGger:A:LEVel:CH2 "+str(lvl))
		elif ch == 'CH3':
			device_write("TRIGger:A:LEVel:CH3 "+str(lvl))
		elif ch == 'CH4':
			device_write("TRIGger:A:LEVel:CH4 "+str(lvl))
		else:
			send.message("Incorrect trigger channel is given")
	elif len(level)==1:
		ch = str(level[0])
		if ch == 'CH1':
			answer = float(device_query("TRIGger:A:LEVel:CH1?"))
			return answer
		elif ch == 'CH2':
			answer = float(device_query("TRIGger:A:LEVel:CH2?"))
			return answer
		elif ch == 'CH3':
			answer = float(device_query("TRIGger:A:LEVel:CH3?"))
			return answer
		elif ch == 'CH4':
			answer = float(device_query("TRIGger:A:LEVel:CH4?"))
			return answer
		else:
			send.message("Incorrect channel is given")
	else:
		send.message("Invalid argument")

def oscilloscope_command(command):
	device_write(command)

def oscilloscope_query(command):
	answer = device_query(command)
	return answer

if __name__ == "__main__":
    main()

