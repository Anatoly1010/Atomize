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
path_config_file = os.path.join(path_current_directory, 'config','Lakeshore_455_DSP_config.ini')

# configuration data
config = cutil.read_conf_util(path_config_file)
specific_parameters = cutil.read_specific_parameters(path_config_file)

# auxilary dictionaries
units_dict = {'Gauss': 1, 'Tesla': 2, 'Oersted': 3, 'Amp/m': 4,};

# Ramges and limits


# Test run parameters
# These values are returned by the modules in the test run 
if len(sys.argv) > 1:
    test_flag = sys.argv[1]
else:
    test_flag = 'None'

test_field = 3500
test_unit = 'Gauss'

class Lakeshore_455_DSP:
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

                    try:
                        # test should be here
                        self.device_write('*CLS')
                        # device is slow, we need to wait a little bit
                        general.wait('50 ms')
                        answer = int(self.device_query('*TST?'))
                        if answer == 0:
                            self.status_flag = 1
                        else:
                            general.message('During internal device test errors are found')
                            self.status_flag = 0
                            sys.exit()
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

            # measure field in Gauss
            self.device_write('UNIT 1')
            # device is slow, we need to wait a little bit
            general.wait('50 ms')

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
            answer = self.device_query('*IDN?')
            return answer
        elif test_flag == 'test':
            answer = config['name']
            return answer

    def gaussmeter_field(self):
        if test_flag != 'test':
                answer = float(self.device_query('RDGFIELD?'))
                return answer
        elif test_flag == 'test':
            answer = test_field
            return answer

    def gaussmeter_units(self, *units):
        if test_flag != 'test':
            if len(units) == 1:
                un = str(units[0])
                if un in units_dict:
                    flag = units_dict[un]
                    self.device_write('UNIT ' + str(flag))
                else:
                    general.message('Incorrect unit')
                    sys.exit()
            elif len(units) == 0:
                raw_answer = int(self.device_query('UNIT?'))
                answer = cutil.search_keys_dictionary(units_dict, raw_answer)
                return answer
            else:
                general.message('Invalid argument')
                sys.exit()                

        elif test_flag == 'test':
            if len(units) == 1:
                un = str(units[0])
                assert(un in units_dict), 'Incorrect unit'
            elif len(units) == 0:
                answer = test_unit
                return answer

    def gaussmeter_command(self, command):
        if test_flag != 'test':
            self.device_write(command)
        elif test_flag == 'test':
            pass

    def gaussmeter_query(self, command):
        if test_flag != 'test':
            answer = self.device_query(command)
            return answer
        elif test_flag == 'test':
            answer = None
            return answer

def main():
    pass

if __name__ == "__main__":
    main()
