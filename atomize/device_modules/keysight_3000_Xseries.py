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
path_config_file = os.path.join(path_current_directory, 'config','keysight_3034t_config.ini')

# configuration data
config = cutil.read_conf_util(path_config_file)

# auxilary dictionaries
points_dict = {'100': 100, '250': 250, '500': 500, '1000': 1000, '2000': 2000,
					'4000': 4000, '8000': 8000, '16000': 16000, '32000': 32000, '64000': 64000,
					'128000': 128000, '256000': 256000, '512000': 512000,};
timebase_dict = {' s': 1, 'ms': 1000, 'us': 1000000, 'ns': 1000000000,};
scale_dict = {' V': 1, 'mV': 1000,};
frequency_dict = {'MHz': 1000000, 'kHz': 1000, 'Hz': 1, 'mHz': 0.001,};
wavefunction_dic = {'Sin': 'SINusoid', 'Sq': 'SQUare', 'Ramp': 'RAMP', 'Pulse': 'PULSe',
					'DC': 'DC', 'Noise': 'NOISe', 'Sinc': 'SINC', 'ERise': 'EXPRise',
					'EFall': 'EXPFall', 'Card': 'CARDiac', 'Gauss': 'GAUSsian',
					'Arb': 'ARBitrary'};

#### Basic interaction functions
def connection():
	global status_flag
	global device

	if config['interface'] == 'ethernet':
		rm = pyvisa.ResourceManager()
		try:
			device=rm.open_resource(config['ethernet_address'])
			device.timeout=config['timeout']; # in ms
			device.read_termination = config['read_termination']  # for WORD (a kind of binary) format
			try:
				answer = int(device_query('*TST?'))
				if answer==0:
					status_flag = 1;
				else:
					send.message('During self-test errors are found')
					status_flag = 0;
			except BrokenPipeError:
				send.message("No connection")
				status_flag = 0;	
		except BrokenPipeError:
			send.message("No connection")
			status_flag = 0
def close_connection():
	status_flag = 0;
	gc.collect()
def device_write(command):
	if status_flag == 1:
		command = str(command)
		device.write(command)
	else:
		send.message("No connection")
def device_query(command):
	if status_flag == 1:
		answer = device.query(command)
		return answer
	else:
		send.message("No connection")
def device_query_ascii(command):
	if status_flag == 1:
		answer = device.query_ascii_values(command, converter='f',separator=',',container=np.array)
		return answer
	else:
		send.message("No connection")
def device_read_binary(command):
	if status_flag==1:
		answer = device.query_binary_values(command,'H', is_big_endian=True, container=np.array)
		# H for 3034T; h for 2012A
		return answer
	else:
		send.message("No connection")

#### Device specific functions
def oscilloscope_name():
	answer = send.message("Hello")
	#print('test')
	#answer = device_query('*IDN?')
	#return answer
def oscilloscope_record_length(*points):
	if  len(points)==1:
		ps = str(points[0])
		if ps in points_dict:
			flag = points_dict[ps]
			device_write(":WAVeform:POINts "+ str(flag))
		else:
			send.message("Invalid sensitivity value")
	elif len(points)==0:
		answer = int(device_query(':WAVeform:POINts?'))
		return answer
	else:
		send.message("Invalid argument")
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
			send.message("Invalid acquisition type")
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
		send.message("Invalid argumnet")
def oscilloscope_number_of_averages(*number_of_averages):
	if len(number_of_averages)==1:
		numave = int(number_of_averages[0]);
		if numave >= 2 and numave <= 65536:
			ac = oscilloscope_acquisition_type()
			if ac == 1:
				device_write(":ACQuire:COUNt " + str(numave))
			elif ac == 0:
				send.message("Your are in NORM mode")
			elif ac == 2:
				send.message("Your are in HRES mode")
			elif ac == 3:
				send.message("Your are in PEAK mode")
		else:
			send.message("Invalid number of averages")
	elif len(number_of_averages)==0:
		answer = int(device_query(":ACQuire:COUNt?"))
		return answer
	else:
		send.message("Invalid argument")
def oscilloscope_timebase(*timebase):
	if len(timebase)==1:
		temp = timebase[0].split(" ")
		tb = float(temp[0])
		scaling = temp[1];
		if scaling in timebase_dict:
			coef = timebase_dict[scaling]
			device_write(":TIMebase:RANGe "+ str(tb/coef))
		else:
			send.message("Incorrect timebase")
	elif len(timebase)==0:
		answer = float(device_query(":TIMebase:RANGe?"))*1000000
		return answer
	else:
		send.message("Invalid argument")
def oscilloscope_time_resolution():
	points = int(oscilloscope_record_length())
	answer = 1000000*float(device_query(":TIMebase:RANGe?"))/points
	return answer
def oscilloscope_start_acquisition():
	#start_time = datetime.now()
	device_write(':WAVeform:FORMat WORD')
	device_query('*ESR?;:DIGitize;*OPC?') # return 1, if everything is ok;
	# the whole sequence is the following 1-binary format; 2-clearing; 3-digitizing; 4-checking of the completness
	#end_time=datetime.now()
	send.message('Acquisition completed')
	#print("Duration of Acquisition: {}".format(end_time - start_time))
def oscilloscope_preamble(channel):
	if channel=='CH1':
		scope_write(':WAVeform:SOURce CHAN1')
	elif channel=='CH2':
		scope_write(':WAVeform:SOURce CHAN2')
	elif channel=='CH3':
		scope_write(':WAVeform:SOURce CHAN3')
	elif channel=='CH4':
		scope_write(':WAVeform:SOURce CHAN4')
	else:
		send.message("Invalid channel is given")
	preamble = scope_query_ascii(":WAVeform:PREamble?")	
	return preamble
def oscilloscope_stop():
	device_write(":STOP")
def oscilloscope_run():
	device_write(":RUN")
def oscilloscope_run_stop():
	device_write(":RUN")
	time.sleep(0.5)
	device_write(":STOP")
def oscilloscope_get_curve(channel):
	if channel=='CH1':
		device_write(':WAVeform:SOURce CHAN1')
	elif channel=='CH2':
		device_write(':WAVeform:SOURce CHAN2')
	elif channel=='CH3':
		device_write(':WAVeform:SOURce CHAN3')
	elif channel=='CH4':
		device_write(':WAVeform:SOURce CHAN4')
	else:
		send.message("Invalid channel is given")
	
	array_y = device_read_binary(':WAVeform:DATA?')
	preamble = device_query_ascii(":WAVeform:PREamble?")
	#x_orig=preamble[5]
	y_inc=preamble[7]
	y_orig=preamble[8]
	y_ref=preamble[9]
	#print(y_inc)
	#print(y_orig)
	#print(y_ref)
	array_y = (array_y - y_ref)*y_inc + y_orig
	#array_x= list(map(lambda x: resolution*(x+1) + 1000000*x_orig, list(range(points))))
	#final_data = list(zip(array_x,array_y))

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
				device_write(":CHAN1:SCALe "+str(val/coef))
			elif ch == 'CH2':
				device_write(":CHAN2:SCALe "+str(val/coef))
			elif ch == 'CH3':
				device_write(":CHAN3:SCALe "+str(val/coef))
			elif ch == 'CH4':
				device_write(":CHAN4:SCALe "+str(val/coef))
			else:
				send.message("Incorrect channel is given")
		else:
			send.message("Incorrect scaling factor")
	elif len(channel)==1:
		ch = str(channel[0])
		if ch == 'CH1':
			answer = float(device_query(":CHAN1:SCALe?"))*1000
			return answer
		elif ch == 'CH2':
			answer = float(device_query(":CHAN2:SCALe?"))*1000
			return answer
		elif ch == 'CH3':
			answer = float(device_query(":CHAN3:SCALe?"))*1000
			return answer
		elif ch == 'CH4':
			answer = float(device_query(":CHAN4:SCALe?"))*1000
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
				device_write(":CHAN1:OFFSet "+str(val/coef))
			elif ch == 'CH2':
				device_write(":CHAN2:OFFSet "+str(val/coef))
			elif ch == 'CH3':
				device_write(":CHAN3:OFFSet "+str(val/coef))
			elif ch == 'CH4':
				device_write(":CHAN4:OFFSet "+str(val/coef))
			else:
				send.message("Incorrect channel is given")
		else:
			send.message("Incorrect scaling factor")
	elif len(channel)==1:
		ch = str(channel[0])
		if ch == 'CH1':
			answer = float(device_query(":CHAN1:OFFSet?"))*1000
			return answer
		elif ch == 'CH2':
			answer = float(device_query(":CHAN2:OFFSet?"))*1000
			return answer
		elif ch == 'CH3':
			answer = float(device_query(":CHAN3:OFFSet?"))*1000
			return answer
		elif ch == 'CH4':
			answer = float(device_query(":CHAN4:OFFSet?"))*1000
			return answer
		else:
			send.message("Incorrect channel is given")
	else:
		send.message("Invalid argument")
def oscilloscope_coupling(*coupling):
	if len(coupling)==2:
		ch = str(coupling[0])
		cpl = str(coupling[1])
		if ch == 'CH1':
			device_write(":CHAN1:COUPling "+str(cpl))
		elif ch == 'CH2':
			device_write(":CHAN2:COUPling "+str(cpl))
		elif ch == 'CH3':
			device_write(":CHAN3:COUPling "+str(cpl))
		elif ch == 'CH4':
			device_write(":CHAN4:COUPling "+str(cpl))
		else:
			send.message("Incorrect channel is given")
	elif len(coupling)==1:
		ch = str(coupling[0])
		if ch == 'CH1':
			answer = device_query(":CHAN1:COUPling?")
			return answer
		elif ch == 'CH2':
			answer = device_query(":CHAN2:COUPling?")
			return answer
		elif ch == 'CH3':
			answer = device_query(":CHAN3:COUPling?")
			return answer
		elif ch == 'CH4':
			answer = device_query(":CHAN4:COUPling?")
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
			cpl = 'ONEMeg';
		elif cpl == '50':
			cpl = 'FIFTy';
		if ch == 'CH1':
			device_write(":CHAN1:IMPedance "+str(cpl))
		elif ch == 'CH2':
			device_write(":CHAN2:COUPling "+str(cpl))
		elif ch == 'CH3':
			device_write(":CHAN3:IMPedance "+str(cpl))
		elif ch == 'CH4':
			device_write(":CHAN4:IMPedance "+str(cpl))
		else:
			send.message("Incorrect channel is given")
	elif len(impedance)==1:
		ch = str(impedance[0])
		if ch == 'CH1':
			answer = device_query(":CHAN1:IMPedance?")
			return answer
		elif ch == 'CH2':
			answer = device_query(":CHAN2:IMPedance?")
			return answer
		elif ch == 'CH3':
			answer = device_query(":CHAN3:IMPedance?")
			return answer
		elif ch == 'CH4':
			answer = device_query(":CHAN4:IMPedance?")
			return answer
		else:
			send.message("Incorrect channel is given")
	else:
		send.message("Invalid argument")
def oscilloscope_trigger_mode(*mode):
	if len(mode)==1:
		md = str(mode[0])
		if md == 'Auto':
			device_write(":TRIGger:SWEep "+'AUTO')
		elif md == 'Normal':
			device_write(":TRIGger:SWEep "+'NORMal')
		else:
			send.message("Incorrect trigger mode is given")
	elif len(mode)==0:
		answer = device_query(":TRIGger:SWEep?")
		return answer
	else:
		send.message("Invalid argument")
def oscilloscope_trigger_channel(*channel):
	if len(channel)==1:
		ch = str(channel[0])
		if ch == 'CH1':
			device_write(":TRIGger[:EDGE]:SOURce "+'CHAN1')
		elif ch == 'CH2':
			device_write(":TRIGger[:EDGE]:SOURce "+'CHAN2')
		elif ch == 'CH3':
			device_write(":TRIGger[:EDGE]:SOURce "+'CHAN3')
		elif ch == 'CH4':
			device_write(":TRIGger[:EDGE]:SOURce "+'CHAN4')
		elif ch == 'Ext':
			device_write(":TRIGger[:EDGE]:SOURce "+'EXTernal')
		elif ch == 'Line':
			device_write(":TRIGger[:EDGE]:SOURce "+'LINE')
		elif ch == 'WGen':
			device_write(":TRIGger[:EDGE]:SOURce "+'WGEN')
		else:
			send.message("Incorrect trigger channel is given")
	elif len(channel)==0:
		answer = device_query(":TRIGger[:EDGE]:SOURce?")
		return answer
	else:
		send.message("Invalid argument")
def oscilloscope_trigger_low_level(*level):
	if len(level)==2:
		ch = str(level[0])
		lvl = float(level[1])
		if ch == 'CH1':
			device_write(":TRIGger:LEVel:LOW "+str(lvl)+', CHAN1')
		elif ch == 'CH2':
			device_write(":TRIGger:LEVel:LOW "+str(lvl)+', CHAN2')
		elif ch == 'CH3':
			device_write(":TRIGger:LEVel:LOW "+str(lvl)+', CHAN3')
		elif ch == 'CH4':
			device_write(":TRIGger:LEVel:LOW "+str(lvl)+', CHAN4')
		else:
			send.message("Incorrect trigger channel is given")
	elif len(level)==1:
		ch = str(level[0])
		if ch == 'CH1':
			answer = device_query(":TRIGger:LEVel:LOW? "+'CHAN1')
			return answer
		elif ch == 'CH2':
			answer = device_query(":TRIGger:LEVel:LOW? "+'CHAN2')
			return answer
		elif ch == 'CH3':
			answer = device_query(":TRIGger:LEVel:LOW? "+'CHAN3')
			return answer
		elif ch == 'CH4':
			answer = device_query(":TRIGger:LEVel:LOW? "+'CHAN4')
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

#### Functions of wave generator
def wave_gen_name():
	answer = device_query('*IDN?')
	return answer
def wave_gen_frequency(*frequency):
	if len(frequency)==1:
		temp = frequency[0].split(" ")
		freq = float(temp[0])
		scaling = temp[1];
		if scaling in frequency_dict:
			coef = frequency_dict[scaling]
			device_write(":WGEN1:FREQuency " + str(freq*coef))
		else:
			send.message("Incorrect frequency")
	elif len(frequency)==0:
		answer = float(device_query(":WGEN1:FREQuency?"))
		return answer
	else:
		send.message("Invalid argument")
def wave_gen_pulse_width(*width):
	answer = device_query(":WGEN:FUNCtion?")
	if answer == 'PULS':
		if len(width)==1:
			temp = width[0].split(" ")
			wid = float(temp[0])
			scaling = temp[1];
			if scaling in timebase_dict:
				coef = timebase_dict[scaling]
				device_write(":WGEN1:FUNCtion:PULSe:WIDTh "+ str(wid/coef))
			else:
				send.message("Incorrect width")
		elif len(width)==0:
			answer = float(device_query(":WGEN1:FUNCtion:PULSe:WIDTh?"))*1000000
			return answer
		else:
			send.message("Invalid argument")
	else:
		send.message("You are not in the pulse mode")
def wave_gen_function(*function):
	if  len(function)==1:
		func = str(function[0])
		if func in wavefunction_dic:
			flag = wavefunction_dic[func]
			device_write(":WGEN:FUNCtion "+ str(flag))
		else:
			send.message("Invalid wave generator function")
	elif len(function)==0:
		answer = str(device_query(':WGEN:FUNCtion?'))
		return answer
	else:
		send.message("Invalid argument")
def wave_gen_amplitude(*amplitude):
	if len(amplitude)==1:
		temp = amplitude[0].split(" ")
		val = float(temp[0])
		scaling = temp[1];
		if scaling in scale_dict:
			coef = scale_dict[scaling]
			device_write(":WGEN:VOLTage " + str(val/coef))
		else:
			send.message("Incorrect amplitude")
	elif len(amplitude)==0:
		answer = float(device_query(":WGEN:VOLTage?"))*1000
		return answer
	else:
		send.message("Invalid argument")
def wave_gen_offset(*offset):
	if len(offset)==1:
		temp = offset[0].split(" ")
		val = float(temp[0])
		scaling = temp[1];
		if scaling in scale_dict:
			coef = scale_dict[scaling]
			device_write(":WGEN:VOLTage:OFFSet " + str(val/coef))
		else:
			send.message("Incorrect offset voltage")
	elif len(offset)==0:
		answer = float(device_query(":WGEN:VOLTage:OFFSet?"))*1000
		return answer
	else:
		send.message("Invalid argument")
def wave_gen_impedance(*impedance):
	if len(impedance)==1:
		cpl = str(impedance[0])
		if cpl == '1 M':
			cpl = 'ONEMeg';
		elif cpl == '50':
			cpl = 'FIFTy';
		else:
			send.message("Incorrect coupling")
		device_write(":WGEN:OUTPut:LOAD " + str(cpl))
	elif len(impedance)==0:
		answer = str(device_query(":WGEN:OUTPut:LOAD?"))
		return answer
	else:
		send.message("Invalid argument")
def wave_gen_run():
	device_write(":WGEN:OUTPut 1")
def wave_gen_stop():
	device_write(":WGEN:OUTPut 0")
def wave_gen_arbitrary_function(list):
	if len(list) > 0:
		if all(element >= -1.0 and element <= 1.0 for element in list) ==True:
			str_to_send = ", ".join(str(x) for x in list)
			device_write(":WGEN:ARBitrary:DATA "+ str(str_to_send))
		else:
			send.message('Incorrect points are used')
	else:
		send.message('Incorrect points are send')
def wave_gen_arbitrary_interpolation(*mode):
	if len(mode)==1:
		md = str(mode[0])
		if md == 'On':
			device_write(":WGEN:ARBitrary:INTerpolate 1")
		elif md == 'Off':
			device_write(":WGEN:ARBitrary:INTerpolate 0")
		else:
			send.message("Incorrect interpolation control setting is given")
	elif len(mode)==0:
		answer = device_query(":WGEN:ARBitrary:INTerpolate?")
		return answer
	else:
		send.message("Invalid argument")
def wave_gen_arbitrary_clear():
	device_write(":WGEN:ARBitrary:DATA:CLEar")
def wave_gen_arbitrary_points():
	answer = int(device_query(":WGEN:ARBitrary:DATA:ATTRibute:POINts?"))
	return answer

def wave_gen_command(command):
	device_write(command)
def wave_gen_query(command):
	answer = device_query(command)
	return answer

if __name__ == "__main__":
    main()