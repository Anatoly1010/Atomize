#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import configparser
import pyqtgraph as pg
from pyvisa.constants import StopBits, Parity
import atomize.general_modules.general_functions as general

# read config data
def read_conf_util(path_config_file):
    # getting config data
    config = configparser.ConfigParser()
    config.read(path_config_file)

    gpib_timeout_list = [0.01, 0.03, 0.1, 0.3, 1, 3, 10, 30, 100, 300, 1000, 3000, 10000, 30000, 100000, 300000, 1000000]

    gpib_timeout_dict = {0.01: 1, 0.03: 2, 0.1: 3, 0.3: 4, 1: 5, 3: 6, 10: 7, 30: 8, 100: 9, 300: 10, 1000: 11, 3000: 12, 10000: 13, 30000: 14, 100000: 15, 300000: 16, 1000000: 17}

    # loading configuration parameters
    name = config['DEFAULT']['name']
    interface = config['DEFAULT']['type']
    timeout = int(config['DEFAULT']['timeout'])

    if interface != 'gpib':
        pass
    else:
        number_timeout = min(gpib_timeout_list, key=lambda x: abs(x - timeout))
        if int(number_timeout) != timeout:
            general.message(f"Desired GPIB timeout cannot be set, the nearest available value {number_timeout} ms is used")
        timeout = gpib_timeout_dict[number_timeout]


    board_address = int(config['GPIB']['board'])
    try:
        gpib_address = int(config['GPIB']['address'])
    except ValueError:
        gpib_address = str(config['GPIB']['address'])
        if gpib_address[0] == 'G':
            pass
        else:
            raise ValueError


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

def parse_pg(st, helper_list):
    fp = pg.siParse( pg.siFormat( pg.siEval(st), suffix = (pg.siParse(st))[2], allowUnicode = False) )
    close_value = min(helper_list, key=lambda x: abs(x - float(fp[0])))
    ret_string = f'{close_value} {fp[1]}{fp[2]}'
    if close_value == 1000:
        sp = pg.siFormat( pg.siEval(ret_string), suffix = (pg.siParse(ret_string))[2], allowUnicode = False)
        if sp == st:
            return sp, int( pg.siParse(sp)[0] ), 0
        else:
            return sp, int( pg.siParse(sp)[0] ), 1
    else:
        if pg.siEval(ret_string) == pg.siEval(st):
            return ret_string, int( pg.siParse(ret_string)[0] ), 0
        else:
            return ret_string, int( pg.siParse(ret_string)[0] ), 1

def search_and_limit_keys_dictionary(dictionary, search_value, min_value, max_value):
    dict_vals = dictionary.values()
    dict_keys = dictionary.keys()

    if search_value in dictionary:
        return dictionary[search_value], search_value, 0
    else:
        if pg.siEval(search_value) > max_value:
            return list( dict_vals ) [-1], list( dict_keys ) [-1], 1
        elif pg.siEval(search_value) < min_value:
            return list( dict_vals ) [0], list( dict_keys ) [0], 1
        else:
            return 0, 0, 1

def main():
    pass

if __name__ == "__main__":
    main()
