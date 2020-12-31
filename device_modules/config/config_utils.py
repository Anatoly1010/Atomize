import configparser
from pyvisa.constants import StopBits, Parity

def read_conf_util(path_config_file):
	# getting config data
	config = configparser.ConfigParser()
	config.read(path_config_file)

	# loading configuration parameters
	loop = int(config['DEFAULT']['loop']);
	interface = config['DEFAULT']['type'];
	timeout = int(config['DEFAULT']['timeout']);

	board_address = int(config['GPIB']['board']);	
	gpib_address = int(config['GPIB']['address']);

	serial_address = config['SERIAL']['address'];
	baudrate = int(config['SERIAL']['baudrate']);
	databits = int(config['SERIAL']['databits']);

	parity = config['SERIAL']['parity'];
	if parity == 'odd':
		parity=Parity.odd
	elif parity == 'even':
		parity=Parity.even
	elif parity == 'none':
		parity=Parity.none

	stopbits = config['SERIAL']['stopbits'];
	if stopbits == 'one':
		stopbits=StopBits.one
	elif stopbits == 'onehalf':
		stopbits=StopBits.one_and_a_half
	elif stopbits == 'two':
		stopbits=StopBits.two

	write_termination = config['SERIAL']['writetermination'];
	read_termination = config['SERIAL']['readtermination'];

	return interface, timeout, loop, board_address, gpib_address, serial_address, baudrate, databits, parity, stopbits, write_termination, read_termination