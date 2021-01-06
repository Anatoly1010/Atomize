import os
import gc
import time
import Gpib
import config.config_utils as cutil
import config.messenger_socket_client as send

#### Inizialization
# setting path to *.ini file
path_current_directory = os.path.dirname(__file__)
path_config_file = os.path.join(path_current_directory, 'config','agilent53131a_config.ini')

# configuration data
config = cutil.read_conf_util(path_config_file)

# auxilary dictionaries
startarm_dic = {'Im': 'IMMediate', 'Ext': 'EXTernal',};
stoparm_dic = {'Im': 'IMMediate', 'Ext': 'EXTernal', 'Tim': 'TIMer', 'Dig': 'DIGits',};
scale_dict = {'ks': 1000,' s': 1, 'ms': 0.001,};
scalefreq_dict = {'GHz': 1000000000,'MHz': 1000000, 'kHz': 1000, 'Hz': 1, };

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
		answer = float(device_query(':MEASURE:FREQ? (@1)'))
		return answer
	elif channel=='CH2':
		answer = float(device_query(':MEASURE:FREQ? (@2)'))
		return answer
	elif channel=='CH3':
		answer = float(device_query(':MEASURE:FREQ? (@3)'))
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
			device_write(":INPut1:IMPedance " + str(imp))
		elif ch == 'CH2':
			device_write(":INPut2:IMPedance " + str(imp))
		elif ch == 'CH3':
			send.message('The impedance for CH3 is only 50 Ohm')
		else:
			send.message('Invalid channel')
	elif len(impedance)==1:
		ch = str(impedance[0])
		if ch == 'CH1':
			answer = float(device_query(":INPut1:IMPedance?"))
			return answer
		elif ch == 'CH2':
			answer = float(device_query(":INPut2:IMPedance?"))
			return answer
		elif ch == 'CH3':
			answer = float(device_query(":INPut3:IMPedance?"))
			return answer
	else:
		send.message('Invalid argument')
def freq_counter_coupling(*coupling):
	if len(coupling)==2:
		ch = str(coupling[0])
		cpl = str(coupling[1])
		if ch == 'CH1':
			device_write(":INPut1:COUPling " + str(cpl))
		elif ch == 'CH2':
			device_write(":INPut2:COUPling " + str(cpl))
		elif ch == 'CH3':
			send.message('The impedance for CH3 is only AC')
		else:
			send.message('Invalid channel')
	elif len(impedance)==1:
		ch = str(coupling[0])
		if ch == 'CH1':
			answer = str(device_query(":INPut1:COUPling?"))
			return answer
		elif ch == 'CH2':
			answer = str(device_query(":INPut2:COUPling?"))
			return answer
		elif ch == 'CH3':
			answer = str(device_query(":INPut3:COUPling?"))
			return answer
	else:
		send.message('Invalid argument')
def freq_counter_stop_mode(*mode):
	if  len(mode)==1:
		md = str(mode[0])
		if md in stoparm_dic:
			flag = stoparm_dic[md]
			device_write(":FREQuency:ARM:STOP:SOURce "+ str(flag))
		else:
			send.message("Invalid stop arm mode")
	elif len(mode)==0:
		answer = str(device_query(':FREQuency:ARM:STOP:SOURce?'))
		return answer
	else:
		send.message("Invalid argument")
def freq_counter_start_mode(*mode):
	if  len(mode)==1:
		md = str(mode[0])
		if md in startarm_dic:
			flag = startarm_dic[md]
			device_write(":FREQuency:ARM:START:SOURce "+ str(flag))
		else:
			send.message("Invalid start arm mode")
	elif len(mode)==0:
		answer = str(device_query(':FREQuency:ARM:START:SOURce?'))
		return answer
	else:
		send.message("Invalid argument")
def freq_counter_digits(*digits):
	if  len(digits)==1:
		val = int(digits[0])
		if val >= 3 and val <=15:
			device_write(":FREQuency:ARM:STOP:DIGits "+ str(val))
		else:
			send.message("Invalid amount of digits")
	elif len(digits)==0:
		answer = int(device_query(':FREQuency:ARM:STOP:DIGits?'))
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
			device_write(":FREQuency:ARM:STOP:TIMer "+ str(tb*coef))
		else:
			send.message("Incorrect gate time")
	elif len(time)==0:
		answer = float(device_query(":FREQuency:ARM:STOP:TIMer?"))
		return answer
	else:
		send.message("Invalid argument")
def freq_counter_expected_freq(*frequency):
	if len(frequency)==2:
		temp = frequency[1].split(" ")
		ch = str(frequency[0])
		val = float(temp[0])
		scaling = str(temp[1]);
		if scaling in scalefreq_dict:
			coef = scalefreq_dict[scaling]
			if ch == 'CH1':
				device_write(":FREQuency:EXPected1 "+str(val*coef))
			elif ch == 'CH2':
				device_write(":FREQuency:EXPected2 "+str(val*coef))
			elif ch == 'CH3':
				device_write(":FREQuency:EXPected3 "+str(val*coef))
			else:
				send.message("Incorrect channel is given")
		else:
			send.message("Incorrect argument")
	elif len(frequency)==1:
		ch = str(frequency[0])
		if ch == 'CH1':
			temp = int(evice_query(':FREQuency:EXPected1:AUTO?'))
			if temp == 0:
				answer = float(device_query(":FREQuency:EXPected1?"))
				return answer
			else:
				send.message("No expected frequency is found")
		elif ch == 'CH2':
			temp = int(evice_query(':FREQuency:EXPected2:AUTO?'))
			if temp == 0:
				answer = float(device_query(":FREQuency:EXPected2?"))
				return answer
			else:
				send.message("No expected frequency is found")
		elif ch == 'CH3':
			send.message("Incorrect channel is given")
			temp = int(evice_query(':FREQuency:EXPected3:AUTO?'))
			if temp == 0:
				answer = float(device_query(":FREQuency:EXPected3?"))
				return answer
			else:
				send.message("No expected frequency is found")
		else:
			send.message("Incorrect channel is given")
	else:
		send.message("Invalid argument")
def freq_counter_ratio(channel1, channel2):
	if channel1 == 'CH1' and channel2 =='CH2':
		answer = float(device_query(':MEASure:FREQuency:RATio? (@1),(@2)'))
		return answer
	elif channel1 == 'CH2' and channel2 =='CH1':
		answer = float(device_query(':MEASure:FREQuency:RATio? (@2),(@1)'))
		return answer
	elif channel1 == 'CH1' and channel2 =='CH3':
		answer = float(device_query(':MEASure:FREQuency:RATio? (@1),(@3)'))
		return answer
	elif channel1 == 'CH3' and channel2 =='CH1':
		answer = float(device_query(':MEASure:FREQuency:RATio? (@3),(@1)'))
		return answer
	else:
		send.message('Invalid argument')
def freq_counter_period(channel):
	if channel == 'CH1':
		answer = float(device_query(':MEASURE:PERiod? (@1)'))*1000000
		return answer
	elif channel=='CH2':
		answer = float(device_query(':MEASURE:PERiod? (@2)'))*1000000
		return answer
	elif channel=='CH3':
		answer = float(device_query(':MEASURE:PERiod? (@3)'))*1000000
		return answer
	else:
		send.message('Invalid argument')
def freq_counter_command(command):
	device_write(command)
def freq_counter_query(command):
	answer = device_query(command)
	return answer