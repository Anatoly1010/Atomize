#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import gc
import sys
import pyvisa
from pyvisa.constants import StopBits, Parity
import atomize.device_modules.config.config_utils as cutil
import atomize.general_modules.general_functions as general

class ER_031M:
    #### Basic interaction functions
    def __init__(self):

        #### Inizialization
        # setting path to *.ini file
        self.path_current_directory = os.path.dirname(__file__)
        self.path_config_file = os.path.join(self.path_current_directory, 'config','ER_031M_config.ini')

        # configuration data
        self.config = cutil.read_conf_util(self.path_config_file)
        self.specific_parameters = cutil.read_specific_parameters(self.path_config_file)

        # Ramges and limits
        self.min_field = -50
        self.max_field = 6000

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

        elif self.test_flag == 'test':
            self.test_field = 3500

    def close_connection(self):
        if self.test_flag != 'test':
            self.status_flag = 0;
            gc.collect()
        elif self.test_flag == 'test':
            pass

    def device_write(self, command):
        if self.status_flag == 1:
            general.wait('900 ms') # very important to have timeout here
            command = str(command)
            self.device.write(command.encode())
        else:
            self.status_flag = 0
            general.message("No Connection")
            sys.exit()

    #### device specific functions
    def magnet_name(self):
        if self.test_flag != 'test':
            answer = self.config['name']
            return answer
        elif self.test_flag == 'test':
            answer = self.config['name']
            return answer

    def magnet_setup(self, start_field, field_step):
        if self.test_flag != 'test':
            if start_field <= self.max_field and start_field >= self.min_field:
                self.field = start_field
                self.field_step = field_step
            else:
                general.message('Incorrect field range')
                sys.exit()
        elif self.test_flag == 'test':
            assert(start_field <= self.max_field and start_field >= self.min_field), 'Incorrect field range'
            self.field = start_field
            self.field_step = field_step

    def magnet_field(self, *field):
        if self.test_flag != 'test':
            if len(field) == 1:
                if field <= self.max_field and field >= self.min_field:
                    #field_controller_write('cf'+str(field)+'\r')
                    self.device_write('cf' + str(field))
                    self.field = field
                else:
                    general.message('Incorrect field range')
                    sys.exit()
            elif len(field) == 0:
                answer = self.field
                return answer
            else:
                send.message("Invalid argument")
                sys.exit()

        elif self.test_flag == 'test':
            if len(field) == 1:
                assert(field <= self.max_field and field >= self.min_field), 'Incorrect field range'
                self.field = field
            elif len(field) == 0:
                answer = self.test_field
                return answer
            else:
                assert(1 == 2), 'Invalid argument'

    def magnet_command(self, command):
        if self.test_flag != 'test':
            command = str(command)
            self.device_write(command)
            # field_controller_write(command+'\r')

        elif self.test_flag == 'test':
            pass

def main():
    pass

if __name__ == "__main__":
    main()