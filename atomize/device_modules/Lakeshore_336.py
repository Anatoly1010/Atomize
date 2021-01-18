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
path_config_file = os.path.join(path_current_directory, 'config','Lakeshore_336_config.ini')

# configuration data
config = cutil.read_conf_util(path_config_file)
loop = config['loop'] # information about the loop used

# auxilary dictionaries
heater_dict = {'50 W': 3, '5 W': 2, '0.5 W': 1, 'Off': 0,};

# Ranges and limits
temperature_max = 320
temperature_min = 0.3
test_heater_range = '5 W'
test_heater_percentage = 1.

# Test run parameters
# These values are returned by the modules in the test run 
if len(sys.argv) > 1:
    test_flag = sys.argv[1]
else:
    test_flag = 'None'

test_temperature = 200.
test_set_point = 298.

class Lakeshore_336:
    #### Basic interaction functions
    def __init__(self):
        if test_flag != 'test':
            if config['interface'] == 'gpib':
                try:
                    import Gpib
                    self.status_flag = 1
                    self.device = Gpib.Gpib(config['board_address'], config['gpib_address'])
                    try:
                        # test should be here
                        self.device_write('*CLS')
                        answer = int(self.device_query('*TST?'))
                        if answer == 0:
                            self.status_flag = 1
                        else:
                            general.message('During internal device test errors are found')
                            self.status_flag = 0
                            sys.exit()
                    except BrokenPipeError:
                        general.message("No connection")
                        self.status_flag = 0;
                        sys.exit()
                except BrokenPipeError:
                    general.message("No connection")
                    self.status_flag = 0
                    sys.exit()

            elif config['interface'] == 'rs232':
                try:
                    self.status_flag = 1
                    rm = pyvisa.ResourceManager()
                    self.device = rm.open_resource(config['serial_address'], read_termination=config['read_termination'],
                    write_termination=config['write_termination'], baud_rate=config['baudrate'],
                    data_bits=config['databits'], parity=config['parity'], stop_bits=config['stopbits'])
                    self.device.timeout = config['timeout'] # in ms
                    try:
                        # test should be here
                        self.device_write('*CLS')
                        answer = self.device_query('*TST?')
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
                    self.status_flag = 0
                    sys.exit()
                except BrokenPipeError:
                    general.message("No connection")
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
                self.device.write(command)
                general.wait('50 ms')
                answer = self.device.read()
            elif config['interface'] == 'rs232':
                answer = self.device.query(command)
            return answer
        else:
            general.message("No Connection")
            self.status_flag = 0
            sys.exit()

    #### device specific functions
    def tc_name(self):
        if test_flag != 'test':
            answer = self.device_query('*IDN?')
            return answer
        elif test_flag == 'test':
            answer = config['name']
            return answer

    def tc_temperature(self, channel):
        if test_flag != 'test':
            if channel == 'A':
                answer = float(self.device_query('KRDG? A'))
                return answer
            elif channel == 'B':
                answer = float(self.device_query('KRDG? B'))
                return answer
            elif channel == 'C':
                answer = float(self.device_query('KRDG? C'))
                return answer
            elif channel == 'D':
                answer = float(self.device_query('KRDG? D'))
                return answer                
            else:
                general.message("Invalid argument")
                sys.exit()
        
        elif test_flag == 'test':
            assert(channel == 'A' or channel == 'B' or channel == 'C' or \
                channel == 'D'), "Incorrect channel"
            answer = test_temperature
            return answer

    def tc_setpoint(self, *temp):
        if test_flag != 'test':
            if int(loop) == 1 or int(loop) == 2 or int(loop) == 3 or \
                    int(loop) == 4:
                if len(temp) == 1:
                    temp = float(temp[0])
                    if temp <= temperature_max and temp >= temperature_min:
                        self.device.write('SETP ' + str(loop) + ',' + str(temp))
                    else:
                        general.message("Incorrect set point temperature")
                        sys.exit()
                elif len(temp) == 0:
                    answer = float(self.device_query('SETP? ' + str(loop)))
                    return answer   
                else:
                    general.message("Invalid argument")
                    sys.exit()
            else:
                general.message("Invalid loop")
                sys.exit()              

        elif test_flag == 'test':
            if len(temp) == 1:
                temp = float(temp[0])
                assert(temp <= temperature_max and temp >= temperature_min), 'Incorrect set point temperature is reached'
                assert(int(loop) == 1 or int(loop) == 2 or int(loop) == 3 or \
                    int(loop) == 4), 'Invalid loop'
            elif len(temp) == 0:
                answer = test_set_point
                return answer

    def tc_heater_range(self, *heater):
        if test_flag != 'test':
            if  len(heater) == 1:
                hr = str(heater[0])
                if hr in heater_dict:
                    flag = heater_dict[hr]
                    self.device_write("RANGE " + str(loop) + ',' + str(flag))
                else:
                    general.message("Invalid heater range")
                    sys.exit()
            elif len(heater) == 0:
                raw_answer = int(self.device_query("RANGE? " + str(loop)))
                answer = cutil.search_keys_dictionary(heater_dict, raw_answer)
                return answer
            else:
                general.message("Invalid argument")
                sys.exit()

        elif test_flag == 'test':                           
            if  len(heater) == 1:
                hr = str(heater[0])
                if hr in heater_dict:
                    flag = heater_dict[hr]
                else:
                    assert(1 == 2), "Invalid heater range"
            elif len(heater) == 0:
                answer = test_heater_range
                return answer
            else:
                assert(1 == 2), "Invalid heater range"

    def tc_heater_state(self):
        if test_flag != 'test':
            answer1 = self.tc_heater_range()
            if int(loop) == 1 or int(loop) == 2:
                answer = float(self.device_query('HTR? ' + str(loop)))
                full_answer = [answer, answer1]
                return full_answer
            elif int(loop) == 3 or int(loop) == 4:
                answer = float(self.device_query('AOUT? ' + str(loop)))
                full_answer = [answer, answer1]
                return full_answer
            else:
                general.message('Invalid loop')
                sys.exit()

        elif test_flag == 'test':
            assert(int(loop) == 1 or int(loop) == 2 or \
                int(loop) == 3 or int(loop) == 4), 'Invalid loop'
            answer1 = test_heater_range
            answer = test_heater_percentage
            full_answer = [answer, answer1]
            return full_answer

    def tc_command(self, command):
        if test_flag != 'test':
            self.device_write(command)
        elif test_flag == 'test':
            pass

    def tc_query(self, command):
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