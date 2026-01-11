#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import gc
import sys
import pyvisa
import numpy as np
from pyvisa.constants import StopBits, Parity
import atomize.main.local_config as lconf
import atomize.device_modules.config.config_utils as cutil
import atomize.general_modules.general_functions as general
from scipy.interpolate import CubicSpline, PchipInterpolator

class ITC_FC:
    #### Basic interaction functions
    def __init__(self):

        #### Inizialization
        # setting path to *.ini file
        self.path_current_directory = os.path.dirname(__file__)
        self.path_current_directory_local = lconf.load_config_device()
        self.path_config_file = os.path.join(self.path_current_directory_local, 'ITC_FC_config.ini')
        path_calib_file = os.path.join(self.path_current_directory, 'config', 'Calibration_curve_08_2024_Sibir_magnet.csv')

        temp = np.genfromtxt(path_calib_file, dtype = float, delimiter = ',', skip_header = 1, comments = '#') 
        calibration_data = np.transpose(temp)
        self.cs = CubicSpline(calibration_data[0], calibration_data[1]/calibration_data[0] / 0.999826, bc_type='natural')


        # configuration data
        self.config = cutil.read_conf_util(self.path_config_file)
        self.specific_parameters = cutil.read_specific_parameters(self.path_config_file)

        # Ramges and limits
        self.min_field = -50
        self.max_field = 9000

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
                    except (pyvisa.VisaIOError, BrokenPipeError):
                        self.status_flag = 0
                        general.message(f"No connection {self.__class__.__name__}")
                        sys.exit()
                except (pyvisa.VisaIOError, BrokenPipeError):
                        general.message(f"No connection {self.__class__.__name__}")
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
            #general.wait('900 ms') # very important to have timeout here
            command = str(command)
            self.device.write(command)
        else:
            self.status_flag = 0
            general.message(f"No connection {self.__class__.__name__}")
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
                self.magnet_field(self.field)

        elif self.test_flag == 'test':
            assert(start_field <= self.max_field and start_field >= self.min_field),\
                f'Incorrect field range. The available range is from {self.min_field} to {self.max_field}'
            self.field = start_field
            self.field_step = field_step
            self.magnet_field(self.field)

    def magnet_field(self, *field, calibration = 'False'):
        if self.test_flag != 'test':
            if len(field) == 1:
                
                    field = round( field[0], 3 )
                    if field <= self.max_field and field >= self.min_field:
                        if calibration == 'False':
                            self.device_write(f'CF {field} #13 #10')
                            self.field = field
                        elif calibration == 'True':
                            if field < 300:
                                self.device_write(f'CF {round(field / self.cs(301) , 3)} #13 #10')
                                self.field = round(field / self.cs(301), 3)
                            elif field > 7800:
                                self.device_write(f'CF {round(field / self.cs(7799) , 3)} #13 #10')
                                self.field = round(field / self.cs(7799), 3)
                            else:
                                self.device_write(f'CF {round(field / self.cs(field) , 3)} #13 #10')
                                self.field = round(field / self.cs(field), 3)
                                #general.message(self.field)
                            
                        # it takes a lot to process the command
                        #general.wait('70 ms')
                        
                        return self.field

            elif len(field) == 0:
                    answer = self.field
                    return answer

        elif self.test_flag == 'test':
            if len(field) == 1:
                field = field[0]
                assert(field <= self.max_field and field >= self.min_field),\
                    f'Incorrect field range. The available range is from {self.min_field} to {self.max_field}'
                if calibration == 'False':
                    self.field = field
                elif calibration == 'True':
                    if field < 300:
                        self.field = round(field / self.cs(301), 3)
                    elif field > 7800:
                        self.field = round(field / self.cs(7799), 3)
                    else:
                        self.field = round(field / self.cs(field), 3)
                return self.field
            elif len(field) == 0:
                answer = self.test_field
                return answer
            else:
                assert(1 == 2), 'Invalid argument; field: float'

    ##### UNDOCUMENTED; FOR TEST ONLY
    def magnet_pid(self, p = 3.5, i = 0.01, d = 8.0):
        if self.test_flag != 'test':
            p_coef = round(p, 3)
            i_coef = round(i, 3)
            d_coef = round(d, 3)
            self.device_write(f'KP {p}') ##13 #10
            self.device_write(f'KI {i}')
            self.device_write(f'KD {d}')

        elif self.test_flag == 'test':
            pass

    def magnet_pid_state(self, state):
        if self.test_flag != 'test':
            p = int(state)

            self.device_write(f'pid {p}')
        elif self.test_flag == 'test':
            p = int(state)
            assert(p == 0 or p == 1), 'Incorrect PID state; state: [0, 1]'

    def magnet_shim(self, level):
        if self.test_flag != 'test':
            p = int(level)
            self.device_write(f'pwn {p}')

        elif self.test_flag == 'test':
            p = int(level)
            assert(p <= 100 and p >= 0), 'Incorrect shim value. The available range is from 0 to 100'

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