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
state_dict = {'On': 1, 'Off': 0, }

# Ranges and limits
temperature_max = 750

# Test run parameters
# These values are returned by the modules in the test run 
if len(sys.argv) > 1:
    test_flag = sys.argv[1]
else:
    test_flag = 'None'

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
                    self.device.serial.baudrate = 9600
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
            # may be functioncode = 16
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

    def discrete_io_input_counter(self, channel):
        if test_flag != 'test':
            if channel == '1':
                answer = int(self.device_read_unsigned(50, 0))
                return answer
            elif channel == '2':
                answer = int(self.device_read_unsigned(65, 0))
                return answer
            elif channel == '3':
                answer = int(self.device_read_unsigned(66, 0))
                return answer
            elif channel == '4':
                answer = int(self.device_read_unsigned(67, 0))
                return answer
            else:
                general.message("Invalid argument")
                sys.exit()
        
        elif test_flag == 'test':
            assert(channel == '1' or channel == '2' or channel == '3' or channel == '4'), "Incorrect channel"
            answer = test_counter
            return answer

    def discrete_io_input_counter_reset(self, channel):
        if test_flag != 'test':
            if channel == '1':
                self.device_write_unsigned(64, 0, 0)
            elif channel == '2':
                self.device_write_unsigned(65, 0, 0)
            elif channel == '3':
                self.device_write_unsigned(66, 0, 0)
            elif channel == '4':
                self.device_write_unsigned(67, 0, 0)
            else:
                general.message("Invalid argument")
                sys.exit()
        
        elif test_flag == 'test':
            assert(channel == '1' or channel == '2' or channel == '3' or channel == '4'), "Incorrect channel"

    def discrete_io_output_state(self, *channel):
        if test_flag != 'test':
            if len(channel) == 1:
                ch = channel[0]
                if channel == '1':
                    self.device_write_unsigned(64, 0, 0)
                elif channel == '2':
                    self.device_write_unsigned(65, 0, 0)
                elif channel == '3':
                    self.device_write_unsigned(66, 0, 0)
                elif channel == '4':
                    self.device_write_unsigned(67, 0, 0)
                else:
                    general.message("Invalid argument")
                    sys.exit()
            elif len(channel) == 2:
                ch = channel[0]
                st = int(channel[1])
                if ch == '1':
                    if st == 0:
                        self.device_write_unsigned(50, 0, 0)
                    elif st == 1:
                        self.device_write_unsigned(50, 1, 0)


        elif test_flag == 'test':
            if len(channel) == 2:
                ch = channel[0]
                st = int(channel[1])
                assert(ch in channel_dict), "Incorrect channel"
            elif len(channel) == 1:
                ch = channel[0]
                assert(ch in channel_dict), "Incorrect channel"
            else:
                assert(1 == 2), "Incorrect argument"

def main():
    pass

if __name__ == "__main__":
    main()
