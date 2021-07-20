#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import configparser
from pyvisa.constants import StopBits, Parity

# read config data
def read_conf_util(path_config_file):
    # getting config data
    config = configparser.ConfigParser()
    config.read(path_config_file)

    # loading configuration parameters
    name = config['DEFAULT']['name']
    interface = config['DEFAULT']['type']
    timeout = int(config['DEFAULT']['timeout'])

    board_address = int(config['GPIB']['board'])
    gpib_address = int(config['GPIB']['address'])

    serial_address = config['SERIAL']['address']
    baudrate = int(config['SERIAL']['baudrate'])
    databits = int(config['SERIAL']['databits'])

    parity = config['SERIAL']['parity']
    if interface != 'rs485':
        if parity == 'odd':
            parity = Parity.odd
        elif parity == 'even':
            parity = Parity.even
        elif parity == 'none':
            parity = Parity.none
    else:
        import minimalmodbus

        if parity == 'even':
            parity = minimalmodbus.serial.PARITY_EVEN
        elif parity == 'odd':
            parity = minimalmodbus.serial.PARITY_ODD
        elif parity == 'none':
            parity = minimalmodbus.serial.PARITY_NONE   

    stopbits = config['SERIAL']['stopbits']
    if interface != 'rs485':
        if stopbits == 'one':
            stopbits = StopBits.one
        elif stopbits == 'onehalf':
            stopbits = StopBits.one_and_a_half
        elif stopbits == 'two':
            stopbits = StopBits.two
    else:
        import minimalmodbus
        if stopbits == 'one':
            stopbits = 1
        elif stopbits == 'two':
            stopbits = 2       

    if config['SERIAL']['write_termination'] == 'r':
        write_termination = '\r'
    elif config['SERIAL']['write_termination'] == 'n':
        write_termination = '\n'
    elif config['SERIAL']['write_termination'] == 'rn':
        write_termination = '\r\n'
    elif config['SERIAL']['write_termination'] == 'nr':
        write_termination = '\n\r'
    else:
        write_termination = '\n'

    if config['SERIAL']['read_termination'] == 'r':
        read_termination = '\r'
    elif config['SERIAL']['read_termination'] == 'n':
        read_termination = '\n'
    elif config['SERIAL']['read_termination'] == 'rn':
        read_termination = '\r\n'
    elif config['SERIAL']['read_termination'] == 'nr':
        read_termination = '\n\r'
    else:
        read_termination = '\n'

    ethernet_address = config['ETHERNET']['address'];

    return {'name': name, 'interface': interface, 'timeout': timeout,
    'board_address': board_address, 'gpib_address': gpib_address, 'serial_address': serial_address,
    'baudrate': baudrate, 'databits': databits, 'parity': parity, 'stopbits': stopbits,
    'write_termination': write_termination, 'read_termination': read_termination,
    'ethernet_address': ethernet_address}

def read_specific_parameters(path_config_file):
    config = configparser.ConfigParser()
    config.read(path_config_file)

    # loading configuration parameters
    specific_parameters = dict(config.items('SPECIFIC'))
    return specific_parameters

def read_modbus_parameters(path_config_file):
    import minimalmodbus

    config = configparser.ConfigParser()
    config.read(path_config_file)

    # loading configuration parameters
    mode = config['MODBUS']['mode']
    if mode == 'ascii':
        mode = minimalmodbus.MODE_ASCII
    elif mode == 'rtu':
        mode = minimalmodbus.MODE_RTU
    else:
        mode = minimalmodbus.MODE_RTU

    slave_address = int(config['MODBUS']['slave_address'])
    list_parameters = [mode, slave_address]
    return list_parameters

# search a key for a given value in dictionary
def search_keys_dictionary(dictionary, search_value):
    for key, value in dictionary.items():
        if value == search_value:
            return key

if __name__ == "__main__":
    main()
