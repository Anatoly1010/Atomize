import configparser

config = configparser.ConfigParser()
config['DEFAULT'] = {'loop': '1'}

config['GPIB'] = {}
config['GPIB']['Board'] = '12'
config['GPIB']['Address'] = '12'


config['SERIAL'] = {}
second_option = config['SERIAL']
second_option['Port'] = 'ttyUSB0'   	# mutates the parser

config['ETHERNET'] = {}
third_option = config['ETHERNET']
third_option['Address'] = '192.168.1.20'   	# mutates the parser

#config['DEFAULT']['ForwardX11'] = 'yes'

with open('lakeshore335_config.ini', 'w') as configfile:
	config.write(configfile)