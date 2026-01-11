#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import gc
import sys
import time
import serial
import minimalmodbus
import atomize.main.local_config as lconf
import atomize.device_modules.config.config_utils as cutil
import atomize.general_modules.general_functions as general

class IVG_1_1:
    #### Basic interaction functions
    def __init__(self):

        #### Inizialization
        # setting path to *.ini file
        self.path_current_directory = lconf.load_config_device()
        self.path_config_file = os.path.join(self.path_current_directory, 'IVG_1_1_config.ini')

        # configuration data
        self.config = cutil.read_conf_util(self.path_config_file)
        self.modbus_parameters = cutil.read_modbus_parameters(self.path_config_file)

        # auxilary dictionaries
        #self.channel_dict = {'1': 1, '2': 2, '3': 3, '4': 4, }

        # Ranges and limits

        # Test run parameters
        # These values are returned by the modules in the test run 
        if len(sys.argv) > 1:
            self.test_flag = sys.argv[1]
        else:
            self.test_flag = 'None'

        if self.test_flag != 'test':
            if self.config['interface'] == 'rs485':
                try:
                    self.status_flag = 1
                    self.device = minimalmodbus.Instrument(self.config['serial_address'], self.modbus_parameters[1])
                    self.device.mode = self.modbus_parameters[0]
                    #check there
                    self.device.serial.baudrate = self.config['baudrate']
                    self.device.serial.bytesize = self.config['databits']
                    self.device.serial.parity = self.config['parity']
                    #check there
                    self.device.serial.stopbits = self.config['stopbits']
                    self.device.serial.timeout = self.config['timeout'] / 1000
                    try:
                        pass
                        # test should be here

                    except serial.serialutil.SerialException:
                        general.message(f"No connection: {self.__class__.__name__}")
                        self.status_flag = 0
                        sys.exit()
                except serial.serialutil.SerialException:
                    general.message(f"No connection: {self.__class__.__name__}")
                    self.status_flag = 0
                    sys.exit()

            else:
                general.message(f"Incorrect interface setting {self.__class__.__name__}")
                self.status_flag = 0
                sys.exit()

        elif self.test_flag == 'test':
            self.test_moisture = [ -49.9, 40.12, 29.1, 25.1 ]

    def close_connection(self):
        if self.test_flag != 'test':
            self.status_flag = 0
            gc.collect()
        elif self.test_flag == 'test':
            pass

    def device_read(self, register):
        if self.status_flag == 1:
            #minimalmodbus.BYTEORDER_LITTLE_SWAP
            answer = self.device.read_float(register, functioncode = 4, byteorder = 3)
            return answer
        else:
            general.message(f"No connection: {self.__class__.__name__}")
            self.status_flag = 0
            sys.exit()

    #### device specific functions
    def moisture_meter_name(self):
        if self.test_flag != 'test':
            answer = self.config['name']
            return answer
        elif self.test_flag == 'test':
            answer = self.config['name']
            return answer

    def moisture_meter_moisture(self):
        if self.test_flag != 'test':
            answer = [ round( self.device_read(0), 3 ), round( self.device_read(2), 3 ), \
                              round( self.device_read(4), 3 ), round( self.device_read(6), 3 ) ]
            return answer

        elif self.test_flag == 'test':
            return self.test_moisture

def main():
    pass

if __name__ == "__main__":
    main()
