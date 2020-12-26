import time
import serial
import gc

def connection():
	
	global c
	global field_controller

	try:
		field_controller = serial.Serial("/dev/ttyACM0", 19200, timeout=5, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_TWO)
		c=1
	except serial.SerialException:	
		print("No connection")
		field_controller.close()
		c=0

def close_connection():
	
	field_controller.close()
	gc.collect()

def field_controller_write(command):
	#c, scope = connection()
	if c==1:
		time.sleep(1)		# very important to have timeout here
		field_controller.write(command.encode())
	else:
		print("No Connection")

def field_controller_set_field(*field):

	if len(field)==1:
		field_controller_write('cf'+str(field)+'\r')									##########
	else:
		print("Invalid Argument")


def field_controller_command(command):

	field_controller_write(command+'\r')									##########
