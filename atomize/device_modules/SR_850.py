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
path_config_file = os.path.join(path_current_directory, 'config','sr850_config.ini')

# configuration data
config = cutil.read_conf_util(path_config_file)

# auxilary dictionaries
sensitivity_dict = {'2 nV': 0, '5 nV': 1, '10 nV': 2, '20 nV': 3, '50 nV': 4,
					'100 nV': 5, '200 nV': 6, '500 nV': 7, '1 uV': 8, '2 uV': 9, '5 uV': 10,
					'10 uV': 11, '20 uV': 12, '50 uV': 13, '100 uV': 14, '200 uV': 15, '500 uV': 16, 
					'1 mV': 17, '2 mV': 18, '5 mV': 19, '10 mV': 20, '20 mV': 21, '50 mV': 22,
					'100 mV': 23, '200 mV': 24, '500 mV': 25, '1 V': 26};
helper_sens_list = [1, 2, 5, 10, 20, 50, 100, 200, 500]
timeconstant_dict = {'10 us': 0, '30 us': 1, '100 us': 2, '300 us': 3,
					'1 ms': 4, '3 ms': 5, '10 ms': 6, '30 ms': 7, '100 ms': 8, '300 ms': 9,
					'1 s': 10, '3 s': 11, '10 s': 12, '30 s': 13, '100 s': 14, '300 s': 15, 
					'1 ks': 16, '3 ks': 17, '10 ks': 18, '30 ks': 19};
helper_tc_list = [1, 3, 10, 30, 100, 300]
ref_mode_dict = {'Internal': 0, 'External': 1}
ref_slope_dict = {'Sine': 0, 'PosTTL': 1, 'NegTTL': 2}
sync_dict = {'Off': 0, 'On': 1}
lp_fil_dict = {'6 db': 0, '12 dB': 1, "18 dB": 2, "24 dB": 3}

# Ranges and limits
ref_freq_min = 0.001
ref_freq_max = 102000
ref_ampl_min = 0.004
ref_ampl_max = 5
harm_max = 32767
harm_min = 1

class sr_850:
	#### Basic interaction functions
	def __init__(self):
		if config['interface'] == 'gpib':
			try:
				import Gpib
				self.self.status_flag = 1
				self.device = Gpib.Gpib(config['board_address'], config['gpib_address'])
				try:
					# test should be here
					answer = int(self.device_query('*TST?'))
					if answer==0:
						self.self.status_flag = 1;
					else:
						send.message('During test errors are found')
						self.self.status_flag = 0;
						sys.exit();
				except pyvisa.VisaIOError:
					send.message("No connection")
					self.self.status_flag = 0;
					sys.exit();
				except BrokenPipeError:
					send.message("No connection")
					self.self.status_flag = 0;
					sys.exit();
			except pyvisa.VisaIOError:
				send.message("No connection")
				self.device.close()
				self.self.status_flag = 0
				sys.exit();
			except BrokenPipeError:
				send.message("No connection")
				self.self.status_flag = 0;
				sys.exit();
		elif config['interface'] == 'rs232':
			try:
				self.self.status_flag = 1
				rm = pyvisa.ResourceManager()
				self.device=rm.open_resource(config['serial_address'], read_termination=config['read_termination'],
				write_termination=config['write_termination'], baud_rate=config['baudrate'],
				data_bits=config['databits'], parity=config['parity'], stop_bits=config['stopbits'])
				self.device.timeout=config['timeout']; # in ms
				try:
					# test should be here
					answer = int(self.device_query('*TST?'))
					if answer==0:
						self.self.status_flag = 1;
					else:
						send.message('During test errors are found')
						self.self.status_flag = 0;
						sys.exit();
				except pyvisa.VisaIOError:
					self.self.status_flag = 0;
					self.device.close()
					send.message("No connection")
					sys.exit();
				except BrokenPipeError:
					send.message("No connection")
					self.self.status_flag = 0;
					sys.exit();
			except pyvisa.VisaIOError:
				send.message("No connection")
				self.device.close()
				self.self.status_flag = 0
				sys.exit();
			except BrokenPipeError:
				send.message("No connection")
				self.self.status_flag = 0;
				sys.exit();

	def close_connection(self):
		self.self.status_flag = 0;
		#self.device.close()
		gc.collect()

	def device_write(self, command):
		if self.self.status_flag==1:
			command = str(command)
			self.device.write(command)
		else:
			send.message("No Connection")
			sys.exit()

	def device_query(self, command):
		if self.self.status_flag == 1:
			if config['interface'] == 'gpib':
				self.device.write(command)
				time.sleep(0.05)
				answer = self.device.read()
			elif config['interface'] == 'rs232':
				answer = self.device.query(command)
			return answer
		else:
			send.message("No Connection")
			sys.exit()

	#### device specific functions
	def lock_in_name(self):
		answer = self.device_query('*IDN?')
		return answer

	def lock_in_ref_frequency(self, *frequency):
		if len(frequency)==1:
			freq = float(frequency[0])
			if freq >= ref_freq_min and freq <= ref_freq_max:
				self.device_write('FREQ '+ str(freq))
			else:
				send.message("Incorrect frequency")
				sys.exit()
		elif len(frequency)==0:
			answer = float(self.device_query('FREQ?'))
			return answer
		else:
			send.message("Invalid Argument")
			sys.exit()

	def lock_in_phase(self, *degree):
		if len(degree)==1:
			degs = float(degree[0])
			if degs >= -360 and degs <= 719:
				self.device_write('PHAS '+str(degs))
			else:
				send.message("Incorrect phase")
				sys.exit()
		elif len(degree)==0:
			answer = float(self.device_query('PHAS?'))
			return answer
		else:
			send.message("Invalid Argument")
			sys.exit()

	def lock_in_time_constant(self, *timeconstant):
		if  len(timeconstant)==1:
			temp = timeconstant[0].split(' ')
			if float(temp[0]) < 10 and temp[1] == 'us':
				send.message("Desired time constant cannot be set, the nearest available value is used")
				self.device_write("OFLT "+ str(0))
			elif float(temp[0]) > 30 and temp[1] == 'ks':
				send.message("Desired sensitivity cannot be set, the nearest available value is used")
				self.device_write("OFLT "+ str(19))
			else:
				number_tc = min(helper_tc_list, key=lambda x: abs(x - int(temp[0])))
				if int(number_tc) != int(temp[0]):
					send.message("Desired time constant cannot be set, the nearest available value is used")
				tc = str(number_tc)+' '+temp[1]
				if tc in timeconstant_dict:
					flag = timeconstant_dict[tc]
					self.device_write("OFLT "+ str(flag))
				else:
					send.message("Invalid time constant value (too high/too low)")
					sys.exit()
		elif len(timeconstant)==0:
			raw_answer = int(self.device_query("OFLT?"))
			answer = cutil.search_keys_dictionary(timeconstant_dict, raw_answer)
			return answer
		else:
			send.message("Invalid Argument")
			sys.exit()

	def lock_in_ref_amplitude(self, *amplitude):
		if len(amplitude)==1:
			ampl = float(amplitude[0]);
			if ampl <= ref_ampl_max and ampl >= ref_ampl_min:
				self.device_write('SLVL '+str(ampl))
			else:
				self.device_write('SLVL '+ str(ref_ampl_min))
				send.message("Invalid Argument")
				sys.exit()
		elif len(amplitude)==0:
			answer = float(self.device_query("SLVL?"))
			return answer
		else:
			send.message("Invalid Argument")
			sys.exit()

	def lock_in_get_data(self, *channel):
		if len(channel)==0:
			answer = float(self.device_query('OUTP? 0'))
			return answer
		elif len(channel)==1 and int(channel[0])==1:
			answer = float(self.device_query('OUTP? 0'))
			return answer
		elif len(channel)==1 and int(channel[0])==2:
			answer = float(self.device_query('OUTP? 1'))
			return answer
		elif len(channel)==1 and int(channel[0])==3:
			answer = float(self.device_query('OUTP? 2'))
			return answer
		elif len(channel)==1 and int(channel[0])==4:
			answer = float(self.device_query('OUTP? 3'))
			return answer
		elif len(channel)==2 and int(channel[0])==1 and int(channel[1])==2:
			answer_string = self.device_query('SNAP? 0,1')
			answer_list = answer_string.split(',')
			list_of_floats = [float(item) for item in answer_list]
			x = list_of_floats[0]
			y = list_of_floats[1]
			return x, y
		elif len(channel)==3 and int(channel[0])==1 and int(channel[1])==2 and int(channel[2])==3:
			answer_string = self.device_query('SNAP? 0,1,2')
			answer_list = answer_string.split(',')
			list_of_floats = [float(item) for item in answer_list]
			x = list_of_floats[0]
			y = list_of_floats[1]
			r = list_of_floats[2]
			return x, y, r

	def lock_in_sensitivity(self, *sensitivity):
		if  len(sensitivity)==1:
			temp = sensitivity[0].split(' ')
			if float(temp[0]) < 2 and temp[1] == 'nV':
				send.message("Desired sensitivity cannot be set, the nearest available value is used")
				self.device_write("SCAL "+ str(0))
			elif float(temp[0]) > 1 and temp[1] == 'V':
				send.message("Desired sensitivity cannot be set, the nearest available value is used")
				self.device_write("SCAL "+ str(26))
			else:
				number_sens = min(helper_sens_list, key=lambda x: abs(x - int(temp[0])))
				sens = str(number_sens)+' '+temp[1]
				if int(number_sens) != int(temp[0]):
					send.message("Desired sensitivity cannot be set, the nearest available value is used")
				if sens in sensitivity_dict:
					flag = sensitivity_dict[sens]
					self.device_write("SCAL "+ str(flag))
				else:
					send.message("Invalid sensitivity value (too high/too low)")
					sys.exit()
		elif len(sensitivity)==0:
			raw_answer = int(self.device_query("SCAL?"))
			answer = cutil.search_keys_dictionary(sensitivity_dict, raw_answer)
			return answer
		else:
			send.message("Invalid Argument")
			sys.exit()

	def lock_in_ref_mode(self, *mode):
		if  len(mode)==1:
			md = str(mode[0])
			if md in ref_mode_dict:
				flag = ref_mode_dict[md]
				self.device_write("RSRC "+ str(flag))
			else:
				send.message("Invalid mode")
				sys.exit()
		elif len(mode)==0:
			raw_answer = int(self.device_query("RSRC?"))
			answer = cutil.search_keys_dictionary(ref_mode_dict, raw_answer)
			return answer
		else:
			send.message("Invalid argumnet")
			sys.exit()

	def lock_in_ref_slope(self, *mode):
		if  len(mode)==1:
			md = str(mode[0])
			if md in ref_slope_dict:
				flag = ref_slope_dict[md]
				self.device_write("RTRG "+ str(flag))
			else:
				send.message("Invalid mode")
				sys.exit()
		elif len(mode)==0:
			raw_answer = int(self.device_query("RTRG?"))
			answer = cutil.search_keys_dictionary(ref_slope_dict, raw_answer)
			return answer
		else:
			send.message("Invalid argumnet")
			sys.exit()

	def lock_in_sync_filter(self, *mode):
		if  len(mode)==1:
			md = str(mode[0])
			if md in sync_dict:
				flag = sync_dict[md]
				self.device_write("SYNC "+ str(flag))
			else:
				send.message("Invalid argument")
				sys.exit()
		elif len(mode)==0:
			raw_answer = int(self.device_query("SYNC?"))
			answer = cutil.search_keys_dictionary(sync_dict, raw_answer)
			return answer
		else:
			send.message("Invalid argumnet")
			sys.exit()

	def lock_in_lp_filter(self, *mode):
		if  len(mode)==1:
			md = str(mode[0])
			if md in lp_fil_dict:
				flag = lp_fil_dict[md]
				self.device_write("OFSL "+ str(flag))
			else:
				send.message("Invalid mode")
				sys.exit()
		elif len(mode)==0:
			raw_answer = int(self.device_query("OFSL?"))
			answer = cutil.search_keys_dictionary(lp_fil_dict, raw_answer)
			return answer
		else:
			send.message("Invalid argumnet")
			sys.exit()

	def lock_in_harmonic(self, *harmonic):
		if len(harmonic)==1:
			harm = int(harmonic[0]);
			if harm <= harm_max and harm >= harm_min:
				self.device_write('HARM '+ str(harm))
			else:
				self.device_write('HARM '+ str(harm_min))
				send.message("Invalid Argument")
				sys.exit()
		elif len(harmonic)==0:
			answer = int(self.device_query("HARM?"))
			return answer
		else:
			send.message("Invalid Argument")
			sys.exit()

	def lock_in_command(self, command):
		self.device_write(command)

	def lock_in_query(self, command):
		answer = self.device_query(command)
		return answer

def main():
	pass

if __name__ == "__main__":
    main()

