#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import gc
import sys
import pyvisa
from pyvisa.constants import StopBits, Parity
import atomize.main.local_config as lconf
import atomize.device_modules.config.config_utils as cutil
import atomize.general_modules.general_functions as general

class Lakeshore_455_DSP:
    #### Basic interaction functions
    def __init__(self):

        #### Inizialization
        # setting path to *.ini file
        self.path_current_directory = lconf.load_config_device()
        self.path_config_file = os.path.join(self.path_current_directory, 'Lakeshore_455_DSP_config.ini')

        # configuration data
        self.config = cutil.read_conf_util(self.path_config_file)
        self.specific_parameters = cutil.read_specific_parameters(self.path_config_file)

        # auxilary dictionaries
        self.units_dict = {'Gauss': 1, 'Tesla': 2, 'Oersted': 3, 'Amp/m': 4,};

        # Ramges and limits


        # Test run parameters
        # These values are returned by the modules in the test run 
        if len(sys.argv) > 1:
            self.test_flag = sys.argv[1]
        else:
            self.test_flag = 'None'

        if self.test_flag != 'test':
            if self.config['interface'] == 'rs232':
                try:
                    self.status_flag = 1
                    rm = pyvisa.ResourceManager()
                    self.device = rm.open_resource(self.config['serial_address'],
                    write_termination=self.config['write_termination'], baud_rate=self.config['baudrate'],
                    data_bits=self.config['databits'], parity=self.config['parity'], stop_bits=self.config['stopbits'])
                    self.device.timeout = self.config['timeout'] # in ms

                    try:
                        # test should be here
                        self.device_write('*CLS')
                        # device is slow, we need to wait a little bit
                        general.wait('50 ms')
                        answer = int(self.device_query('*TST?'))
                        if answer == 0:
                            self.status_flag = 1
                        else:
                            general.message(f'During internal device test errors were found {self.__class__.__name__}')
                            self.status_flag = 0
                            sys.exit()
                    except (pyvisa.VisaIOError, BrokenPipeError):
                        self.status_flag = 0
                        general.message(f"No connection {self.__class__.__name__}")
                        sys.exit()

                except (pyvisa.VisaIOError, BrokenPipeError):
                        general.message(f"No connection {self.__class__.__name__}")
                        sys.exit()

            # measure field in Gauss
            self.device_write('UNIT 1')
            # device is slow, we need to wait a little bit
            general.wait('50 ms')

        elif self.test_flag == 'test':
            self.test_field = 3500
            self.test_unit = 'Gauss'

    def close_connection(self):
        if self.test_flag != 'test':
            self.status_flag = 0
            gc.collect()
        elif self.test_flag == 'test':
            pass

    def device_write(self, command):
        if self.status_flag == 1:
            command = str(command)
            self.device.write(command)
        else:
            general.message(f"No connection {self.__class__.__name__}")
            self.status_flag = 0
            sys.exit()

    def device_query(self, command):
        if self.status_flag == 1:
            if self.config['interface'] == 'gpib':
                general.message(f'Invalid interface {self.__class__.__name__}')
                sys.exit()
                #self.device.write(command)
                #general.wait('50 ms')
                #answer = self.device.read()
            elif self.config['interface'] == 'rs232':
                answer = self.device.query(command)
            return answer
        else:
            general.message(f"No connection {self.__class__.__name__}")
            self.status_flag = 0
            sys.exit()

    #### device specific functions
    def gaussmeter_name(self):
        if self.test_flag != 'test':
            answer = self.device_query('*IDN?')
            return answer
        elif self.test_flag == 'test':
            answer = self.config['name']
            return answer

    def gaussmeter_field(self):
        if self.test_flag != 'test':
                answer = float(self.device_query('RDGFIELD?'))
                return answer
        elif self.test_flag == 'test':
            answer = self.test_field
            return answer

    def gaussmeter_units(self, *units):
        if self.test_flag != 'test':
            if len(units) == 1:
                un = str(units[0])
                if un in self.units_dict:
                    flag = self.units_dict[un]
                    self.device_write('UNIT ' + str(flag))
            elif len(units) == 0:
                raw_answer = int(self.device_query('UNIT?'))
                answer = cutil.search_keys_dictionary(self.units_dict, raw_answer)
                return answer               

        elif self.test_flag == 'test':
            if len(units) == 1:
                un = str(units[0])
                assert(un in self.units_dict), f'Incorrect unit; unit: {list( self.units_dict.keys() )}'
            elif len(units) == 0:
                answer = self.test_unit
                return answer
            else:
                assert( 1 == 2 ), f'Incorrect unit; unit: {list( self.units_dict.keys() )}'

    def gaussmeter_command(self, command):
        if self.test_flag != 'test':
            self.device_write(command)
        elif self.test_flag == 'test':
            pass

    def gaussmeter_query(self, command):
        if self.test_flag != 'test':
            answer = self.device_query(command)
            return answer
        elif self.test_flag == 'test':
            answer = None
            return answer

def main():
    pass

if __name__ == "__main__":
    main()
