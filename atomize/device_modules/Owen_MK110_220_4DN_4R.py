#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import gc
import sys
import serial
import minimalmodbus
import atomize.device_modules.config.config_utils as cutil
import atomize.general_modules.general_functions as general

#### Inizialization
# setting path to *.ini file
path_current_directory = os.path.dirname(__file__)
path_config_file = os.path.join(path_current_directory, 'config','Owen_MK110_220_4DN_4R_config.ini')

# configuration data
config = cutil.read_conf_util(path_config_file)
modbus_parameters = cutil.read_modbus_parameters(path_config_file)

# auxilary dictionaries
channel_dict = {'1': 1, '2': 2, '3': 3, '4': 4, }
output_state_dict = {'0': '0', '1': '1', '2': '10', '3': '100', '4': '1000',\
                         '12': '11', '13': '101', '14': '1001', '23': '110', '24': '1010', '34': '1100', '123': '111',\
                         '124': '1011', '134': '1101', '234': '1110', '1234': '1111', }
input_state_dict = {'0': '0', '1': '1', '2': '10', '3': '100', '4': '1000',\
                         '12': '11', '13': '101', '14': '1001', '23': '110', '24': '1010', '34': '1100', '123': '111',\
                         '124': '1011', '134': '1101', '234': '1110', '1234': '1111', }

# Ranges and limits

# Test run parameters
# These values are returned by the modules in the test run 
if len(sys.argv) > 1:
    test_flag = sys.argv[1]
else:
    test_flag = 'None'

test_input_state = '0'
test_output_state = '0'
test_counter = 1

class Owen_MK110_220_4DN_4R:
    #### Basic interaction functions
    def __init__(self):
        if test_flag != 'test':
            if config['interface'] == 'rs485':
                try:
                    self.status_flag = 1
                    self.device = minimalmodbus.Instrument(config['serial_address'], modbus_parameters[1])
                    #self.device.mode = minimalmodbus.MODE_ASCII
                    self.device.mode = modbus_parameters[0]
                    #check there
                    self.device.serial.baudrate = config['baudrate']
                    self.device.serial.bytesize = config['databits']
                    self.device.serial.parity = config['parity']
                    #check there
                    self.device.serial.stopbits = config['stopbits']
                    self.device.serial.timeout = config['timeout']/1000
                    try:
                        pass
                        # test should be here
                        #self.device_write('*CLS')

                    except serial.serialutil.SerialException:
                        general.message("No connection")
                        self.status_flag = 0
                        sys.exit()
                except serial.serialutil.SerialException:
                    general.message("No connection")
                    self.status_flag = 0
                    sys.exit()

            else:
                general.message("Incorrect interface setting")
                self.status_flag = 0
                sys.exit()

        elif test_flag == 'test':
            pass

    def close_connection(self):
        if test_flag != 'test':
            self.status_flag = 0;
            gc.collect()
        elif test_flag == 'test':
            pass

    def device_write_unsigned(self, register, value, decimals):
        if self.status_flag == 1:
            self.device.write_register(register, value, decimals, functioncode = 16, signed = False)
        else:
            general.message("No Connection")
            self.status_flag = 0
            sys.exit()

    def device_read_unsigned(self, register, decimals):
        if self.status_flag == 1:
            answer = self.device.read_register(register, decimals, signed = False)
            return answer
        else:
            general.message("No Connection")
            self.status_flag = 0
            sys.exit()

    #### device specific functions
    def discrete_io_name(self):
        if test_flag != 'test':
            answer = config['name']
            return answer
        elif test_flag == 'test':
            answer = config['name']
            return answer

    # Argument is channel; Output - counter
    def discrete_io_input_counter(self, channel):
        if test_flag != 'test':
            if channel in channel_dict:
                ch = channel_dict[channel]
                answer = int(self.device_read_unsigned(63 + ch, 0))
                return answer
            else:
                general.message("Invalid argument")
                sys.exit()
        
        elif test_flag == 'test':
            assert(channel in channel_dict), "Incorrect channel"
            answer = test_counter
            return answer

    # Argument is channel; No output
    def discrete_io_input_counter_reset(self, channel):
        if test_flag != 'test':
            if channel in channel_dict:
                ch = channel_dict[channel]
                self.device_write_unsigned(63 + ch, 0, 0)
            else:
                general.message("Invalid argument")
                sys.exit()
        elif test_flag == 'test':
            assert(channel in channel_dict), "Incorrect channel"

    # No argument; Output in the form '1234' that means input 1-4 are on
    def discrete_io_input_state(self):
        if test_flag != 'test':
            raw_answer = bin(int(self.device_read_unsigned(51, 0))).replace("0b","")
            answer = cutil.search_keys_dictionary(input_state_dict, raw_answer)
            return answer

        elif test_flag == 'test':
            answer = test_input_state
            return answer

    # Argument in the from '1234' that means output 1-4 will be turned on
    # Answer in the form '1234' that means output 1-4 are on
    def discrete_io_output_state(self, *state):
        if test_flag != 'test':
            if len(state) == 1:
                st = state[0]
                if st in output_state_dict:
                    flag = int(output_state_dict[st], 2)
                    self.device_write_unsigned(50, flag, 0)
                else:
                    general.message("Invalid state")
                    sys.exit()
            elif len(state) == 0:
                raw_answer = bin(int(self.device_read_unsigned(50, 0))).replace("0b","")
                answer = cutil.search_keys_dictionary(output_state_dict, raw_answer)
                return answer

        elif test_flag == 'test':
            if len(state) == 1:
                st = state[0]
                assert(st in output_state_dict), "Incorrect state"
            elif len(state) == 0:
                answer = test_output_state
                return answer
            else:
                assert(1 == 2), "Incorrect argument"


def main():
    pass

if __name__ == "__main__":
    main()
