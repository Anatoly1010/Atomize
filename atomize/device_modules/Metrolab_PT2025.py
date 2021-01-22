#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import gc
import sys
import pyvisa
from pyvisa.constants import StopBits, Parity
import atomize.device_modules.config.config_utils as cutil
import atomize.general_modules.general_functions as general

#### Inizialization
# setting path to *.ini file
path_current_directory = os.path.dirname(__file__)
path_config_file = os.path.join(path_current_directory, 'config','Metrolab_PT2025_config.ini')

# configuration data
config = cutil.read_conf_util(path_config_file)

# Ramges and limits


# Test run parameters
# These values are returned by the modules in the test run 
if len(sys.argv) > 1:
    test_flag = sys.argv[1]
else:
    test_flag = 'None'

test_field = 3500

class Metrolab_PT2025:
    #### Basic interaction functions
    def __init__(self):
        if test_flag != 'test':
            if config['interface'] == 'rs232':
                try:
                    self.status_flag = 1
                    rm = pyvisa.ResourceManager()
                    self.device = rm.open_resource(config['serial_address'],
                    write_termination=config['write_termination'], baud_rate=config['baudrate'],
                    data_bits=config['databits'], parity=config['parity'], stop_bits=config['stopbits'])
                    self.device.timeout = config['timeout'] # in ms

                    self.field = 0.
                    self.field_step = 0.

                    try:
                        # test should be here
                        self.status_flag = 1
                    except pyvisa.VisaIOError:
                        self.status_flag = 0
                        general.message("No connection")
                        sys.exit()
                    except BrokenPipeError:
                        general.message("No connection")
                        self.status_flag = 0
                        sys.exit()
                except pyvisa.VisaIOError:
                        general.message("No connection")
                        sys.exit()
                except BrokenPipeError:
                    general.message("No connection")
                    self.status_flag = 0
                    sys.exit()

            # measure field in Tesla
            self.device_write('D1')
            # switch to multiplexer A
            self.device_write('PA')            
            # switch to AUTO mode
            self.device_write('A1')
            # activate the search, starting at about 3.5 T
            self.device_write('H3500')

        elif test_flag == 'test':
            pass

    def close_connection(self):
        if test_flag != 'test':
            self.status_flag = 0;
            gc.collect()
        elif test_flag == 'test':
            pass

    def device_write(self, command):
        if self.status_flag == 1:
            command = str(command)
            self.device.write(command)
        else:
            general.message("No Connection")
            self.status_flag = 0
            sys.exit()

    def device_query(self, command):
        if self.status_flag == 1:
            if config['interface'] == 'gpib':
                general.message('Invalid interface')
                sys.exit()
                #self.device.write(command)
                #general.wait('50 ms')
                #answer = self.device.read()
            elif config['interface'] == 'rs232':
                answer = self.device.query(command)
            return answer
        else:
            general.message("No Connection")
            self.status_flag = 0
            sys.exit()

    #### device specific functions
    def gaussmeter_name(self):
        if test_flag != 'test':
            answer = config['name']
            return answer
        elif test_flag == 'test':
            answer = config['name']
            return answer

    def gaussmeter_field(self):
        if test_flag != 'test':
                answer = self.device_query('ENQ')
                return answer
        elif test_flag == 'test':
            answer = test_field
            return answer

    def gaussmeter_status(self):
        if test_flag != 'test':
                answer = self.device_query('S3')
                return answer
        elif test_flag == 'test':
            answer = test_field
            return answer

    def gaussmeter_command(self, command):
        if test_flag != 'test':
            command = str(command)
            self.device_write(command)
            # field_controller_write(command+'\r')

        elif test_flag == 'test':
            pass

def main():
    pass

if __name__ == "__main__":
    main()