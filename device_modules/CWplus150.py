import time
import serial
import gc

def connection():

	global c
	global balance

	try:
		balance = serial.Serial("/dev/ttyUSB0", 9600, timeout=3, bytesize=8, parity='N')
		c=1
	except serial.SerialException:	
		print("No connection")
		balance.close()
		c = 0
def close_connection():
	
	balance.close()
	gc.collect()
def balance_write(command):
	#c, scope = connection()
	if c==1:
		balance.write(command)
	else:
		print("No Connection")
def balance_read():

	if c==1:
		answer = balance.readline()
		return answer
	else:
		print("No Connection")

def balance_weight():

	balance_write(b"G\r\n")
	time.sleep(0.5)
	bytes_answer = balance_read()
	#print(bytes_answer)
	decoded_bytes = bytes_answer[0:len(bytes_answer)-2].decode("utf-8")
	#print(decoded_bytes.split(" ")[1])
	if decoded_bytes.split(" ")[1] == '':
		try:
			weight = float(decoded_bytes.split(" ")[2])
		except ValueError:
			weight = -0.5
	else:
		try:
			weight = float(decoded_bytes.split(" ")[1])
		except ValueError:
			weight = -0.5	
	return weight								
	
