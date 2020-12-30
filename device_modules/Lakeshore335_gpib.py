import time
import serial
import gc
import pyvisa
from pyvisa.constants import StopBits, Parity
import Gpib

loop = 1;		# specify the loop used

def connection():
	
	global c
	global temp_controller
	
	try:
		temp_controller = Gpib.Gpib(0,12)
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
	#temp_controller.close()
	gc.collect()

def temp_controller_write(command):
	if c==1:
		command = str(command)
		temp_controller.write(command)
	else:
		print("No Connection")

def temp_controller_query(command):
	if c == 1:
		temp_controller.write(command)
		time.sleep(0.05)
		answer = temp_controller.read()
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
	else:
		print("Invalid Argument")
	
def set_temp(*temp):

	if len(temp)==1:
		temp = float(temp[0]);
		if temp < 330 and temp > 0.5:
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
		if heater == '50W':
			temp_controller_write('RANGE ' + str(loop) + ', ' + str(3))
		elif heater == '5W':
			temp_controller_write('RANGE ' + str(loop) + ', ' + str(2))
		elif heater == '0.5W':
			temp_controller_write('RANGE ' + str(loop) + ', ' + str(1))
		elif heater == 'Off':
			temp_controller_write('RANGE ' + str(loop) + ', ' + str(0))
	elif len(heater)==0:
		try:
			answer = int(temp_controller_query('RANGE?'))
		except TypeError:
			answer = 'No Connection';
		if answer == 3:
			answer = '50 W'
		if answer == 2:
			answer = '5 W'
		if answer == 1:
			answer = '0.5 W'
		if answer == 0:
			answer = 'Off'
		return answer
	else:
		print("Invalid Argument")								

def heater():

	answer1 = heater_range()
	answer = float(temp_controller_query('HTR?'))
	full_answer = [answer, answer1]
	return full_answer