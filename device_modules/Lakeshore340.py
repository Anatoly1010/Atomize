import time
import serial
import gc
import pyvisa

loop = 1;		# specify the loop used

def connection():
	
	global c
	global temp_controller

	rm = pyvisa.ResourceManager()

	try:
		temp_controller = rm.open_resource('COM4', read_termination='', write_termination='\r\n')
		temp_controller.baud_rate = 19200
		try:
			c = 1;
			temp_controller_query('*IDN?')
		except pyvisa.VisaIOError:
			c = 0;
	except pyvisa.VisaIOError:
		print("No connection")
		temp_controller.close()
		c = 0

def close_connection():
	c = 0;
	temp_controller.close()
	gc.collect()

def temp_controller_write(command):
	#c, scope = connection()
	if c==1:
		temp_controller.write(command)
	else:
		print("No Connection")

def temp_controller_query(command):
	#c, scope = connection()
	if c==1:
		answer = temp_controller.query(command)
		return answer
	else:
		print("No Connection")

def read_temp(channel):

	if channel=='A':
		try:
			answer = float(temp_controller_query('KRDG? A'))
		except TypeError:
			answer = 'No Connection';
		return answer
	elif channel=='B':
		try:
			answer = float(temp_controller_query('KRDG? B'))
		except TypeError:
			answer = 'No Connection';
		return answer
	elif channel=='C':
		try:
			answer = float(temp_controller_query('KRDG? C'))
		except TypeError:
			answer = 'No Connection';
		return answer
	elif channel=='D':
		try:
			answer = float(temp_controller_query('KRDG? D'))
		except TypeError:
			answer = 'No Connection';
		return answer
	else:
		print("Invalid Argument")
	
def set_temp(*temp):

	if len(temp)==1:
		temp = float(temp[0]);
		if temp < 310 and temp > 0.5:
			temp_controller.write('SETP '+ str(loop) + ', ' + str(temp))
		else:
			print("Invalid Argument")
	elif len(temp)==0:
		try:
			answer = float(temp_controller_query('SETP? '+ str(loop)))
		except TypeError:
			answer = 'No Connection';
		return answer	
	else:
		print("Invalid Argument")


def heater_range(*heater):

	if len(heater)==1:
		heater = heater[0];
		if heater == '10W':
			temp_controller_write('RANGE ' + str(5))
		elif heater == '1W':
			temp_controller_write('RANGE ' + str(4))
		elif heater == 'Off':
			temp_controller_write('RANGE ' + str(0))
	elif len(heater)==0:
		try:
			answer = int(temp_controller_query('RANGE?'))
		except TypeError:
			answer = 'No Connection';
		if answer == 5:
			answer = '10 W'
		if answer == 4:
			answer = '1 W'
		if answer == 0:
			answer = 'Off'
		return answer
	else:
		print("Invalid Argument")								

def heater():

	answer1 = heater_range()
	try:
		answer = float(temp_controller_query('HTR?'))
	except TypeError:
		answer = 'No Connection';
	full_answer = [answer, answer1]
	return full_answer