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
path_config_file = os.path.join(path_current_directory, 'config','Lakeshore_325_config.ini')

# configuration data
config = cutil.read_conf_util(path_config_file)
specific_parameters = cutil.read_specific_parameters(path_config_file)
loop_config = int(specific_parameters['loop']) # information about the loop used

# auxilary dictionaries
heater_dict = {'25 W': 2, '2.5 W': 1, 'Off': 0,};
lock_dict = {'Local-Locked': 0, 'Remote-Locked': 1, 'Local-Unlocked': 2, 'Remote-Unlocked': 3,}
loop_list = [1, 2]
sens_dict = {1: 'A', 2: 'B',}

# Ranges and limits
temperature_max = 320
temperature_min = 1.4

# Test run parameters
# These values are returned by the modules in the test run 
if len(sys.argv) > 1:
    test_flag = sys.argv[1]
else:
    test_flag = 'None'

test_temperature = 200.
test_set_point = 298.
test_lock = 'Local-Locked'
test_heater_range = '2.5 W'
test_heater_percentage = 1.
test_sensor = 'A'

class Lakeshore_325:
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
            if config['interface'] == 'gpib':
                return answer.decode()
            elif config['interface'] == 'rs232':
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
            else:
                general.message("Invalid argument")
                sys.exit()
        
        elif test_flag == 'test':
            assert(channel == 'A' or channel == 'B'), "Incorrect channel"
            answer = test_temperature
            return answer

    def tc_setpoint(self, *temp):
        if test_flag != 'test':
            if int(loop_config) in loop_list:
                if len(temp) == 1:
                    temp = float(temp[0])
                    if temp <= temperature_max and temp >= temperature_min:
                        self.device.write('SETP ' + str(loop_config) + ',' + str(temp))
                    else:
                        general.message("Incorrect set point temperature")
                        sys.exit()
                elif len(temp) == 0:
                    answer = float(self.device_query('SETP? ' + str(loop_config)))
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
                assert(int(loop_config) in loop_list), 'Invalid loop argument'
            elif len(temp) == 0:
                answer = test_set_point
                return answer

    def tc_heater_range(self, *heater):
        if test_flag != 'test':
            if  len(heater) == 1:
                hr = str(heater[0])
                if hr in heater_dict:
                    flag = heater_dict[hr]
                    if int(loop_config) in loop_list:
                        self.device_write("RANGE " + str(loop_config) + ',' + str(flag))
                    else:
                        general.message('Invalid loop')
                        sys.exit()
                else:
                    general.message("Invalid heater range")
                    sys.exit()
            elif len(heater) == 0:
                raw_answer = int(self.device_query("RANGE? " + str(loop_config)))
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
                    assert(int(loop_config) in loop_list), 'Invalid loop argument'
                else:
                    assert(1 == 2), "Invalid heater range"
            elif len(heater) == 0:
                answer = test_heater_range
                return answer
            else:
                assert(1 == 2), "Invalid heater range"

    def tc_heater_power(self):
        if test_flag != 'test':
            answer1 = self.tc_heater_range()
            if int(loop_config) in loop_list:
                answer = float(self.device_query('HTR? ' + str(loop_config)))
                full_answer = [answer, answer1]
                return full_answer
            else:
                general.message('Invalid loop')
                sys.exit()              

        elif test_flag == 'test':
            assert(int(loop_config) in loop_list), 'Invalid loop argument'
            answer1 = test_heater_range
            answer = test_heater_percentage
            full_answer = [answer, answer1]
            return full_answer

    def tc_sensor(self, *sensor):
        if test_flag != 'test':
            if len(sensor) == 1:
                sens = int(sensor[0])
                if loop_config in loop_list:
                    pass
                else:
                    general.message('Invalid loop')
                    sys.exit()
                    if sens in sens_dict:
                        flag = sens_dict[sens]
                        self.device_write('CSET '+ str(loop_config) + ',' + str(flag) +',0,2')
                    else:
                        general.message('Invalid sensor')
                        sys.exit()

            elif len(sensor) == 0:
                raw_answer1 = self.device_query('CSET?' + str(loop_config))
                if config['interface'] == 'gpib':
                    raw_answer2 = str(raw_answer1.decode()[0])
                elif config['interface'] == 'rs232':
                    raw_answer2 = str(raw_answer1[0])
                answer = raw_answer2
                return answer

        elif test_flag == 'test':
            if len(sensor) == 1:
                sens = int(sensor[0])
                assert(loop_config in loop_list), 'Invalid loop argument'
                assert(sens in sens_dict), 'Invalid sensor'
            elif len(sensor) == 0:
                answer = test_sensor
                return answer

    def tc_lock_keyboard(self, *lock):
        if test_flag != 'test':
            if len(lock) == 1:
                lk = str(lock[0])
                if lk in lock_dict:
                    flag = lock_dict[lk]
                    if flag == 0:
                        self.device_write('LOCK 1,123')
                        self.device_write('MODE 0')
                    elif flag == 1:
                        self.device_write('LOCK 1,123')
                        self.device_write('MODE 1')
                    elif flag == 2:
                        self.device_write('LOCK 0,123')
                        self.device_write('MODE 0')
                    elif flag == 3:
                        self.device_write('LOCK 0,123')
                        self.device_write('MODE 1')
                else:
                    general.message("Invalid argument")
                    sys.exit()
            elif len(lock) == 0:
                raw_answer1 = self.device_query('LOCK?')
                if config['interface'] == 'gpib':
                    answer1 = int(raw_answer1.decode()[0])
                elif config['interface'] == 'rs232':
                    answer1 = int(raw_answer1[0])
                answer2 = int(self.device_query('MODE?'))
                if answer1 == 1 and answer2 == 0:
                    answer_flag = 0
                    answer = cutil.search_keys_dictionary(lock_dict, answer_flag)
                    return answer
                elif answer1 == 1 and answer2 == 1:
                    answer_flag = 1
                    answer = cutil.search_keys_dictionary(lock_dict, answer_flag)
                    return answer
                elif answer1 == 0 and answer2 == 0:
                    answer_flag = 2
                    answer = cutil.search_keys_dictionary(lock_dict, answer_flag)
                    return answer
                elif answer1 == 0 and answer2 == 1:
                    answer_flag = 3
                    answer = cutil.search_keys_dictionary(lock_dict, answer_flag)
                    return answer
            else:
                general.message("Invalid argument")
                sys.exit()                      

        elif test_flag == 'test':
            if len(lock) == 1:
                lk = str(lock[0])
                if lk in lock_dict:
                    flag = lock_dict[lk]
                else:
                    assert(1 == 2), "Invalid lock argument"
            elif len(lock) == 0:
                answer = test_lock
                return answer    
            else:
                assert(1 == 2), "Invalid argument"

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