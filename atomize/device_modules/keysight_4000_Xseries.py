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
path_config_file = os.path.join(path_current_directory, 'config','keysight_4000_config.ini')

# configuration data
config = cutil.read_conf_util(path_config_file)

# auxilary dictionaries
points_list = [100, 250, 500, 1000, 2000, 5000, 10000, 20000, 50000, 100000, 200000, 500000, 1000000,\
				2000000, 4000000, 8000000]
# have to be checked
timebase_dict = {' s': 1, 'ms': 1000, 'us': 1000000, 'ns': 1000000000,};
scale_dict = {' V': 1, 'mV': 1000,};
frequency_dict = {'MHz': 1000000, 'kHz': 1000, 'Hz': 1, 'mHz': 0.001,};
wavefunction_dic = {'Sin': 'SINusoid', 'Sq': 'SQUare', 'Ramp': 'RAMP', 'Pulse': 'PULSe',
					'DC': 'DC', 'Noise': 'NOISe', 'Sinc': 'SINC', 'ERise': 'EXPRise',
					'EFall': 'EXPFall', 'Card': 'CARDiac', 'Gauss': 'GAUSsian',
					'Arb': 'ARBitrary'};
ac_type_dic = {'Norm': "NORMal", 'Ave': "AVER", 'Hres': "HRES",'Peak': "PEAK"}

# Limits and Ranges:
tr_delay_max = 10
tr_delay_min = 0.000000004
numave_min = 2
numave_max = 65536

class keysight_4000_Xseries:
	#### Basic interaction functions
	def __init__(self):

		if config['interface'] == 'ethernet':
			rm = pyvisa.ResourceManager()
			try:
				self.status_flag = 1
				self.device=rm.open_resource(config['ethernet_address'])
				self.device.timeout=config['timeout']; # in ms
				self.device.read_termination = config['read_termination']  # for WORD (a kind of binary) format
				try:
					answer = int(self.device_query('*TST?'))
					if answer==0:
						self.status_flag = 1;
					else:
						send.message('During self-test errors are found')
						self.status_flag = 0;
						sys.exit()
				except pyvisa.VisaIOError:
					send.message("No connection")
					self.status_flag = 0;
					self.device.close()
					sys.exit()
				except BrokenPipeError:
					send.message("No connection")
					self.status_flag = 0;
					self.device.close()
					sys.exit()
			except pyvisa.VisaIOError:
				send.message("No connection")
				self.device.close()
				self.status_flag = 0
				sys.exit()
			except BrokenPipeError:
				send.message("No connection")
				self.status_flag = 0;
				self.device.close()
				sys.exit()

	def close_connection(self):
		self.status_flag = 0;
		gc.collect()
		self.device.close()

	def device_write(self, command):
		if self.status_flag == 1:
			command = str(command)
			self.device.write(command)
		else:
			send.message("No connection")
			sys.exit()

	def device_query(self, command):
		if self.status_flag == 1:
			answer = self.device.query(command)
			return answer
		else:
			send.message("No connection")
			sys.exit()

	def device_query_ascii(self, command):
		if self.status_flag == 1:
			answer = self.device.query_ascii_values(command, converter='f',separator=',',container=np.array)
			return answer
		else:
			send.message("No connection")
			sys.exit()

	def device_read_binary(self, command):
		if self.status_flag==1:
			answer = self.device.query_binary_values(command,'H', is_big_endian=True, container=np.array)
			# H for 3034T; h for 2012A
			return answer
		else:
			send.message("No connection")
			sys.exit()

	#### device specific functions
	def oscilloscope_name():
		answer = self.device_query('*IDN?')
		return answer

	def oscilloscope_record_length(self, *points):
		if len(points)==1:
			temp = int(points[0]);
			poi = min(points_list, key=lambda x: abs(x - temp))
			self.device_write(":WAVeform:POINts "+ str(poi))
		elif len(points)==0:
			answer = int(self.device_query(':WAVeform:POINts?'))
			return answer
		else:
			send.message("Invalid argument")
			sys.exit()

	def oscilloscope_acquisition_type(self, *ac_type):
		if  len(ac_type)==1:
			at = str(ac_type[0])
			if at in ac_type_dic:
				flag = ac_type_dic[at]
				self.device_write(":ACQuire:TYPE "+ str(flag))
			else:
				send.message("Invalid acquisition type")
				sys.exit()
		elif len(ac_type)==0:
			answer = str(self.device_query(":ACQuire:TYPE?"))
			return answer
		else:
			send.message("Invalid argumnet")
			sys.exit()

	def oscilloscope_number_of_averages(self, *number_of_averages):
		if len(number_of_averages)==1:
			numave = int(number_of_averages[0]);
			if numave >= numave_min and numave <= numave_max:
				ac = self.oscilloscope_acquisition_type()
				if ac == "AVER":
					self.device_write(":ACQuire:COUNt " + str(numave))
				elif ac == 'NORM':
					send.message("Your are in NORM mode")
				elif ac == 'HRES':
					send.message("Your are in HRES mode")
				elif ac == 'PEAK':
					send.message("Your are in PEAK mode")
			else:
				send.message("Invalid number of averages")
				sys.exit()
		elif len(number_of_averages)==0:
			answer = int(self.device_query(":ACQuire:COUNt?"))
			return answer
		else:
			send.message("Invalid argument")
			sys.exit()

	def oscilloscope_timebase(self, *timebase):
		if len(timebase)==1:
			temp = timebase[0].split(" ")
			tb = float(temp[0])
			scaling = temp[1];
			if scaling in timebase_dict:
				coef = timebase_dict[scaling]
				self.device_write(":TIMebase:RANGe "+ str(tb/coef))
			else:
				send.message("Incorrect timebase")
				sys.exit()
		elif len(timebase)==0:
			answer = float(self.device_query(":TIMebase:RANGe?"))*1000000
			return answer
		else:
			send.message("Invalid argument")
			sys.exit()

	def oscilloscope_time_resolution(self):
		points = int(self.oscilloscope_record_length())
		answer = 1000000*float(self.device_query(":TIMebase:RANGe?"))/points
		return answer

	def oscilloscope_start_acquisition(self):
		#start_time = datetime.now()
		self.device_write(':WAVeform:FORMat WORD')
		self.device_query('*ESR?;:DIGitize;*OPC?') # return 1, if everything is ok;
		# the whole sequence is the following 1-binary format; 2-clearing; 3-digitizing; 4-checking of the completness
		#end_time=datetime.now()
		send.message('Acquisition completed')
		#print("Duration of Acquisition: {}".format(end_time - start_time))

	def oscilloscope_preamble(self, channel):
		if channel=='CH1':
			self.device_write(':WAVeform:SOURce CHAN1')
		elif channel=='CH2':
			self.device_write(':WAVeform:SOURce CHAN2')
		elif channel=='CH3':
			self.device_write(':WAVeform:SOURce CHAN3')
		elif channel=='CH4':
			self.device_write(':WAVeform:SOURce CHAN4')
		else:
			send.message("Invalid channel is given")
			sys.exit()
		preamble = self.device_query_ascii(":WAVeform:PREamble?")	
		return preamble

	def oscilloscope_stop(self):
		self.device_write(":STOP")

	def oscilloscope_run(self):
		self.device_write(":RUN")

	def oscilloscope_run_stop(self):
		self.device_write(":RUN")
		time.sleep(0.5)
		self.device_write(":STOP")

	def oscilloscope_get_curve(self, channel):
		if channel=='CH1':
			self.device_write(':WAVeform:SOURce CHAN1')
		elif channel=='CH2':
			self.device_write(':WAVeform:SOURce CHAN2')
		elif channel=='CH3':
			self.device_write(':WAVeform:SOURce CHAN3')
		elif channel=='CH4':
			self.device_write(':WAVeform:SOURce CHAN4')
		else:
			send.message("Invalid channel is given")
			sys.exit()
		
		array_y = self.device_read_binary(':WAVeform:DATA?')
		preamble = self.device_query_ascii(":WAVeform:PREamble?")
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

	def oscilloscope_sensitivity(self, *channel):
		if len(channel)==2:
			temp = channel[1].split(" ")
			ch = str(channel[0])
			val = float(temp[0])
			scaling = str(temp[1]);
			if scaling in scale_dict:
				coef = scale_dict[scaling]
				if ch == 'CH1':
					self.device_write(":CHAN1:SCALe "+str(val/coef))
				elif ch == 'CH2':
					self.device_write(":CHAN2:SCALe "+str(val/coef))
				elif ch == 'CH3':
					self.device_write(":CHAN3:SCALe "+str(val/coef))
				elif ch == 'CH4':
					self.device_write(":CHAN4:SCALe "+str(val/coef))
				else:
					send.message("Incorrect channel is given")
					sys.exit()
			else:
				send.message("Incorrect scaling factor")
				sys.exit()
		elif len(channel)==1:
			ch = str(channel[0])
			if ch == 'CH1':
				answer = float(self.device_query(":CHAN1:SCALe?"))*1000
				return answer
			elif ch == 'CH2':
				answer = float(self.device_query(":CHAN2:SCALe?"))*1000
				return answer
			elif ch == 'CH3':
				answer = float(self.device_query(":CHAN3:SCALe?"))*1000
				return answer
			elif ch == 'CH4':
				answer = float(self.device_query(":CHAN4:SCALe?"))*1000
				return answer
			else:
				send.message("Incorrect channel is given")
				sys.exit()
		else:
			send.message("Invalid argument")
			sys.exit()

	def oscilloscope_offset(self, *channel):
		if len(channel)==2:
			temp = channel[1].split(" ")
			ch = str(channel[0])
			val = float(temp[0])
			scaling = str(temp[1]);
			if scaling in scale_dict:
				coef = scale_dict[scaling]
				if ch == 'CH1':
					self.device_write(":CHAN1:OFFSet "+str(val/coef))
				elif ch == 'CH2':
					self.device_write(":CHAN2:OFFSet "+str(val/coef))
				elif ch == 'CH3':
					self.device_write(":CHAN3:OFFSet "+str(val/coef))
				elif ch == 'CH4':
					self.device_write(":CHAN4:OFFSet "+str(val/coef))
				else:
					send.message("Incorrect channel is given")
					sys.exit()
			else:
				send.message("Incorrect scaling factor")
				sys.exit()
		elif len(channel)==1:
			ch = str(channel[0])
			if ch == 'CH1':
				answer = float(self.device_query(":CHAN1:OFFSet?"))*1000
				return answer
			elif ch == 'CH2':
				answer = float(self.device_query(":CHAN2:OFFSet?"))*1000
				return answer
			elif ch == 'CH3':
				answer = float(self.device_query(":CHAN3:OFFSet?"))*1000
				return answer
			elif ch == 'CH4':
				answer = float(self.device_query(":CHAN4:OFFSet?"))*1000
				return answer
			else:
				send.message("Incorrect channel is given")
		else:
			send.message("Invalid argument")

	def oscilloscope_trigger_delay(self, *delay):
		if len(delay)==1:
			temp = delay[0].split(" ")
			offset = float(temp[0])
			scaling = temp[1];
			if offset <= tr_delay_max and offset >= tr_delay_min:
				if scaling in timebase_dict:
					coef = timebase_dict[scaling]
					self.device_write(":TRIGger:DELay:TDELay:TIME "+ str(offset/coef))
				else:
					send.message("Incorrect trigger delay")
					sys.exit()
			else:
				send.message("Incorrect trigger delay")
				sys.exit()
		elif len(delay)==0:
			answer = float(self.device_query(":TRIGger:DELay:TDELay:TIME?"))*1000000
			return answer
		else:
			send.message("Invalid argument")
			sys.exit()

	def oscilloscope_coupling(self, *coupling):
		if len(coupling)==2:
			ch = str(coupling[0])
			cpl = str(coupling[1])
			if ch == 'CH1':
				self.device_write(":CHAN1:COUPling "+str(cpl))
			elif ch == 'CH2':
				self.device_write(":CHAN2:COUPling "+str(cpl))
			elif ch == 'CH3':
				self.device_write(":CHAN3:COUPling "+str(cpl))
			elif ch == 'CH4':
				self.device_write(":CHAN4:COUPling "+str(cpl))
			else:
				send.message("Incorrect channel is given")
				sys.exit()
		elif len(coupling)==1:
			ch = str(coupling[0])
			if ch == 'CH1':
				answer = self.device_query(":CHAN1:COUPling?")
				return answer
			elif ch == 'CH2':
				answer = self.device_query(":CHAN2:COUPling?")
				return answer
			elif ch == 'CH3':
				answer = self.device_query(":CHAN3:COUPling?")
				return answer
			elif ch == 'CH4':
				answer = self.device_query(":CHAN4:COUPling?")
				return answer
			else:
				send.message("Incorrect channel is given")
				sys.exit()
		else:
			send.message("Invalid argument")
			sys.exit()

	def oscilloscope_impedance(self, *impedance):
		if len(impedance)==2:
			ch = str(impedance[0])
			cpl = str(impedance[1])
			if cpl == '1 M':
				cpl = 'ONEMeg';
			elif cpl == '50':
				cpl = 'FIFTy';
			if ch == 'CH1':
				self.device_write(":CHAN1:IMPedance "+str(cpl))
			elif ch == 'CH2':
				self.device_write(":CHAN2:IMPedance "+str(cpl))
			elif ch == 'CH3':
				self.device_write(":CHAN3:IMPedance "+str(cpl))
			elif ch == 'CH4':
				self.device_write(":CHAN4:IMPedance "+str(cpl))
			else:
				send.message("Incorrect channel is given")
				sys.exit()
		elif len(impedance)==1:
			ch = str(impedance[0])
			if ch == 'CH1':
				answer = self.device_query(":CHAN1:IMPedance?")
				return answer
			elif ch == 'CH2':
				answer = self.device_query(":CHAN2:IMPedance?")
				return answer
			elif ch == 'CH3':
				answer = self.device_query(":CHAN3:IMPedance?")
				return answer
			elif ch == 'CH4':
				answer = self.device_query(":CHAN4:IMPedance?")
				return answer
			else:
				send.message("Incorrect channel is given")
				sys.exit()
		else:
			send.message("Invalid argument")
			sys.exit()

	def oscilloscope_trigger_mode(self, *mode):
		if len(mode)==1:
			md = str(mode[0])
			if md == 'Auto':
				self.device_write(":TRIGger:SWEep "+'AUTO')
			elif md == 'Normal':
				self.device_write(":TRIGger:SWEep "+'NORMal')
			else:
				send.message("Incorrect trigger mode is given")
		elif len(mode)==0:
			answer = self.device_query(":TRIGger:SWEep?")
			return answer
		else:
			send.message("Invalid argument")
			sys.exit()

	def oscilloscope_trigger_channel(self, *channel):
		if len(channel)==1:
			ch = str(channel[0])
			if ch == 'CH1':
				self.device_write(":TRIGger[:EDGE]:SOURce "+'CHAN1')
			elif ch == 'CH2':
				self.device_write(":TRIGger[:EDGE]:SOURce "+'CHAN2')
			elif ch == 'CH3':
				self.device_write(":TRIGger[:EDGE]:SOURce "+'CHAN3')
			elif ch == 'CH4':
				self.device_write(":TRIGger[:EDGE]:SOURce "+'CHAN4')
			elif ch == 'Ext':
				self.device_write(":TRIGger[:EDGE]:SOURce "+'EXTernal')
			elif ch == 'Line':
				self.device_write(":TRIGger[:EDGE]:SOURce "+'LINE')
			elif ch == 'WGen1':
				self.device_write(":TRIGger[:EDGE]:SOURce "+'WGEN1')
			elif ch == 'WGen2':
				self.device_write(":TRIGger[:EDGE]:SOURce "+'WGEN2')
			else:
				send.message("Incorrect trigger channel is given")
				sys.exit()
		elif len(channel)==0:
			answer = self.device_query(":TRIGger[:EDGE]:SOURce?")
			return answer
		else:
			send.message("Invalid argument")
			sys.exit()

	def oscilloscope_trigger_low_level(eslf, *level):
		if len(level)==2:
			ch = str(level[0])
			lvl = float(level[1])
			if ch == 'CH1':
				self.device_write(":TRIGger:LEVel:LOW "+str(lvl)+', CHAN1')
			elif ch == 'CH2':
				self.device_write(":TRIGger:LEVel:LOW "+str(lvl)+', CHAN2')
			elif ch == 'CH3':
				self.device_write(":TRIGger:LEVel:LOW "+str(lvl)+', CHAN3')
			elif ch == 'CH4':
				self.device_write(":TRIGger:LEVel:LOW "+str(lvl)+', CHAN4')
			else:
				send.message("Incorrect trigger channel is given")
				sys.exit()
		elif len(level)==1:
			ch = str(level[0])
			if ch == 'CH1':
				answer = self.device_query(":TRIGger:LEVel:LOW? "+'CHAN1')
				return answer
			elif ch == 'CH2':
				answer = self.device_query(":TRIGger:LEVel:LOW? "+'CHAN2')
				return answer
			elif ch == 'CH3':
				answer = self.device_query(":TRIGger:LEVel:LOW? "+'CHAN3')
				return answer
			elif ch == 'CH4':
				answer = self.device_query(":TRIGger:LEVel:LOW? "+'CHAN4')
				return answer
			else:
				send.message("Incorrect channel is given")
				sys.exit()
		else:
			send.message("Invalid argument")
			sys.exit()

	def oscilloscope_command(self, command):
		self.device_write(command)

	def oscilloscope_query(self, command):
		answer = self.device_query(command)
		return answer

	#### Functions of wave generator
	def wave_gen_name(self):
		answer = self.device_query('*IDN?')
		return answer

	def wave_gen_frequency(self, *frequency, channel='1'):
		ch = channel
		if ch!='1' and ch!='2':
			send.message("Incorrect wave generator channel")
			sys.exit()
		if len(frequency)==1:
			temp = frequency[0].split(" ")
			freq = float(temp[0])
			scaling = temp[1];
			if scaling in frequency_dict:
				coef = frequency_dict[scaling]
				self.device_write(":WGEN"+str(ch)+":FREQuency " + str(freq*coef))
			else:
				send.message("Incorrect frequency")
				sys.exit()
		elif len(frequency)==0:
			answer = float(self.device_query(":WGEN"+str(ch)+":FREQuency?"))
			return answer
		else:
			send.message("Invalid argument")
			sys.exit()

	def wave_gen_pulse_width(self, *width, channel='1'):
		ch = channel
		if ch!='1' and ch!='2':
			send.message("Incorrect wave generator channel")
			sys.exit()
		answer = self.device_query(":WGEN:FUNCtion?")
		if answer == 'PULS':
			if len(width)==1:
				temp = width[0].split(" ")
				wid = float(temp[0])
				scaling = temp[1];
				if scaling in timebase_dict:
					coef = timebase_dict[scaling]
					self.device_write(":WGEN"+str(ch)+":FUNCtion:PULSe:WIDTh "+ str(wid/coef))
				else:
					send.message("Incorrect width")
					sys.exit()
			elif len(width)==0:
				answer = float(self.device_query(":WGEN"+str(ch)+"FUNCtion:PULSe:WIDTh?"))*1000000
				return answer
			else:
				send.message("Invalid argument")
				sys.exit()
		else:
			send.message("You are not in the pulse mode")
			sys.exit()

	def wave_gen_function(self, *function, channel='1'):
		ch = channel
		if ch!='1' and ch!='2':
			send.message("Incorrect wave generator channel")
			sys.exit()
		if  len(function)==1:
			func = str(function[0])
			if func in wavefunction_dic:
				flag = wavefunction_dic[func]
				self.device_write(":WGEN"+str(ch)+":FUNCtion "+ str(flag))
			else:
				send.message("Invalid wave generator function")
				sys.exit()
		elif len(function)==0:
			answer = str(self.device_query(':WGEN'+str(ch)+':FUNCtion?'))
			return answer
		else:
			send.message("Invalid argument")
			sys.exit()

	def wave_gen_amplitude(self, *amplitude, channel='1'):
		ch = channel
		if ch!='1' and ch!='2':
			send.message("Incorrect wave generator channel")
			sys.exit()
		if len(amplitude)==1:
			temp = amplitude[0].split(" ")
			val = float(temp[0])
			scaling = temp[1];
			if scaling in scale_dict:
				coef = scale_dict[scaling]
				self.device_write(":WGEN"+str(ch)+":VOLTage " + str(val/coef))
			else:
				send.message("Incorrect amplitude")
				sys.exit()
		elif len(amplitude)==0:
			answer = float(self.device_query(":WGEN"+str(ch)+":VOLTage?"))*1000
			return answer
		else:
			send.message("Invalid argument")
			sys.exit()

	def wave_gen_offset(self, *offset, channel='1'):
		ch = channel
		if ch!='1' and ch!='2':
			send.message("Incorrect wave generator channel")
			sys.exit()
		if len(offset)==1:
			temp = offset[0].split(" ")
			val = float(temp[0])
			scaling = temp[1];
			if scaling in scale_dict:
				coef = scale_dict[scaling]
				self.device_write(":WGEN"+str(ch)+":VOLTage:OFFSet " + str(val/coef))
			else:
				send.message("Incorrect offset voltage")
				sys.exit()
		elif len(offset)==0:
			answer = float(self.device_query(":WGEN"+str(ch)+":VOLTage:OFFSet?"))*1000
			return answer
		else:
			send.message("Invalid argument")
			sys.exit()

	def wave_gen_impedance(self, *impedance, channel='1'):
		ch = channel
		if ch!='1' and ch!='2':
			send.message("Incorrect wave generator channel")
			sys.exit()
		if len(impedance)==1:
			cpl = str(impedance[0])
			if cpl == '1 M':
				cpl = 'ONEMeg';
			elif cpl == '50':
				cpl = 'FIFTy';
			else:
				send.message("Incorrect coupling")
				sys.exit()
			self.device_write(":WGEN"+str(ch)+":OUTPut:LOAD " + str(cpl))
		elif len(impedance)==0:
			answer = str(self.device_query(":WGEN"+str(ch)+":OUTPut:LOAD?"))
			return answer
		else:
			send.message("Invalid argument")
			sys.exit()

	def wave_gen_run(self, channel='1'):
		ch = channel
		if ch!='1' and ch!='2':
			send.message("Incorrect wave generator channel")
			sys.exit()
		self.device_write(":WGEN"+str(ch)+":OUTPut 1")

	def wave_gen_stop(self, channel='1'):
		ch = channel
		if ch!='1' and ch!='2':
			send.message("Incorrect wave generator channel")
			sys.exit()
		self.device_write(":WGEN"+str(ch)+":OUTPut 0")

	def wave_gen_arbitrary_function(self, list, channel='1'):
		ch = channel
		if ch!='1' and ch!='2':
			send.message("Incorrect wave generator channel")
			sys.exit()
		if len(list) > 0:
			if all(element >= -1.0 and element <= 1.0 for element in list) ==True:
				str_to_send = ", ".join(str(x) for x in list)
				self.device_write(":WGEN"+str(ch)+":ARBitrary:DATA "+ str(str_to_send))
			else:
				send.message('Incorrect points are used')
				sys.exit()
		else:
			send.message('Incorrect points are send')
			sys.exit()

	def wave_gen_arbitrary_interpolation(self, *mode, channel='1'):
		ch = channel
		if ch!='1' and ch!='2':
			send.message("Incorrect wave generator channel")
			sys.exit()
		if len(mode)==1:
			md = str(mode[0])
			if md == 'On':
				self.device_write(":WGEN"+str(ch)+":ARBitrary:INTerpolate 1")
			elif md == 'Off':
				self.device_write(":WGEN"+str(ch)+":ARBitrary:INTerpolate 0")
			else:
				send.message("Incorrect interpolation control setting is given")
				sys.exit()
		elif len(mode)==0:
			answer = self.device_query(":WGEN"+str(ch)+":ARBitrary:INTerpolate?")
			return answer
		else:
			send.message("Invalid argument")
			sys.exit()

	def wave_gen_arbitrary_clear(self, channel='1'):
		ch = channel
		if ch!='1' and ch!='2':
			send.message("Incorrect wave generator channel")
			sys.exit()
		self.device_write(":WGEN"+str(ch)+":ARBitrary:DATA:CLEar")

	def wave_gen_arbitrary_points(self, channel='1'):
		ch = channel
		if ch!='1' and ch!='2':
			send.message("Incorrect wave generator channel")
			sys.exit()
		answer = int(self.device_query(":WGEN"+str(ch)+":ARBitrary:DATA:ATTRibute:POINts?"))
		return answer

	def wave_gen_command(self, command):
		self.device_write(command)

	def wave_gen_query(self, command):
		answer = self.device_query(command)
		return answer

def main():
	pass

if __name__ == "__main__":
	main()
