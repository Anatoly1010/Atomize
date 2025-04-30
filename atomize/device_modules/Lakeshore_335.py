#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import gc
import sys
import pyvisa
from pyvisa.constants import StopBits, Parity
import atomize.device_modules.config.config_utils as cutil
import atomize.general_modules.general_functions as general

class Lakeshore_335:
    #### Basic interaction functions
    def __init__(self):

        #### Inizialization
        # setting path to *.ini file
        self.path_current_directory = os.path.dirname(__file__)
        self.path_config_file = os.path.join(self.path_current_directory, 'config','Lakeshore_335_config.ini')

        # configuration data
        self.config = cutil.read_conf_util(self.path_config_file)
        self.specific_parameters = cutil.read_specific_parameters(self.path_config_file)
        self.loop_config = int(self.specific_parameters['loop']) # information about the loop used

        # auxilary dictionaries
        self.heater_dict = {'50 W': 3, '5 W': 2, '0.5 W': 1, 'Off': 0,};
        self.lock_dict = {'Local-Locked': 0, 'Remote-Locked': 1, 'Local-Unlocked': 2, 'Remote-Unlocked': 3,}
        self.loop_list = [1, 2]
        self.sens_dict = {0: 'None', 1: 'A', 2: 'B',}

        # Ranges and limits
        self.temperature_max = 320
        self.temperature_min = 0.3

        # Test run parameters
        # These values are returned by the modules in the test run 
        if len(sys.argv) > 1:
            self.test_flag = sys.argv[1]
        else:
            self.test_flag = 'None'

        if self.test_flag != 'test':
            if self.config['interface'] == 'gpib':
                try:
                    import Gpib
                    self.status_flag = 1
                    self.device = Gpib.Gpib(self.config['board_address'], self.config['gpib_address'], \
                                            timeout = self.config['timeout'])
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
                        general.message("No connection LS335")
                        self.status_flag = 0;
                        sys.exit()
                except BrokenPipeError:        
                    general.message("No connection LS335")
                    self.status_flag = 0
                    sys.exit()

            elif self.config['interface'] == 'rs232':
                try:
                    self.status_flag = 1
                    rm = pyvisa.ResourceManager()
                    self.device = rm.open_resource(self.config['serial_address'], read_termination=self.config['read_termination'],
                    write_termination=self.config['write_termination'], baud_rate=self.config['baudrate'],
                    data_bits=self.config['databits'], parity=self.config['parity'], stop_bits=self.config['stopbits'])
                    self.device.timeout = self.config['timeout'] # in ms
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
                        general.message("No connection LS335")
                        sys.exit()
                    except BrokenPipeError:
                        general.message("No connection LS335")
                        self.status_flag = 0
                        sys.exit()
                except pyvisa.VisaIOError:
                    general.message("No connection LS335")
                    self.status_flag = 0
                    sys.exit()
                except BrokenPipeError:
                    general.message("No connection LS335")
                    self.status_flag = 0
                    sys.exit()

        elif self.test_flag == 'test':
            self.test_temperature = 200.
            self.test_set_point = 298.
            self.test_lock = 'Remote-Locked'
            self.test_heater_range = '5 W'
            self.test_heater_percentage = 1.
            self.test_sensor = 'A'

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
            general.message("No Connection LS335")
            self.status_flag = 0
            sys.exit()

    def device_query(self, command):
        if self.status_flag == 1:
            if self.config['interface'] == 'gpib':
                self.device.write(command)
                general.wait('50 ms')
                answer = self.device.read()
            elif self.config['interface'] == 'rs232':
                answer = self.device.query(command)
            return answer
        else:
            general.message("No Connection LS335")
            self.status_flag = 0
            sys.exit()

    #### device specific functions
    def tc_name(self):
        if self.test_flag != 'test':
            # check whether using rs-232 we have the same
            # b'name\r\n'
            answer = self.device_query('*IDN?')
            if self.config['interface'] == 'gpib':
                return answer.decode()
            elif self.config['interface'] == 'rs232':
                return answer
        elif self.test_flag == 'test':
            answer = self.config['name']
            return answer

    def tc_temperature(self, channel):
        if self.test_flag != 'test':
            if channel == 'A':
                answer = float(self.device_query('KRDG? A'))
                return answer
            elif channel == 'B':
                answer = float(self.device_query('KRDG? B'))
                return answer
            else:
                general.message("Invalid argument")
                sys.exit()
        
        elif self.test_flag == 'test':
            assert(channel == 'A' or channel == 'B'), "Incorrect channel"
            answer = self.test_temperature
            return answer

    def tc_setpoint(self, *temp):
        if self.test_flag != 'test':
            if int(self.loop_config) in self.loop_list:
                if len(temp) == 1:
                    temp = float(temp[0])
                    if temp <= self.temperature_max and temp >= self.temperature_min:
                        self.device.write('SETP ' + str(self.loop_config) + ',' + str(temp))
                    else:
                        general.message("Incorrect set point temperature")
                        sys.exit()
                elif len(temp) == 0:
                    answer = float(self.device_query('SETP? ' + str(self.loop_config)))
                    return answer   
                else:
                    general.message("Invalid argument")
                    sys.exit()
            else:
                general.message("Invalid loop")
                sys.exit()              

        elif self.test_flag == 'test':
            if len(temp) == 1:
                temp = float(temp[0])
                assert(temp <= self.temperature_max and temp >= self.temperature_min), 'Incorrect set point temperature is reached'
                assert(int(self.loop_config) in self.loop_list), 'Invalid loop argument'
                self.test_set_point = temp
                self.test_temperature = temp + 0.05
            elif len(temp) == 0:
                answer = self.test_set_point
                return answer

    def tc_heater_range(self, *heater):
        if self.test_flag != 'test':
            if  len(heater) == 1:
                hr = str(heater[0])
                if hr in self.heater_dict:
                    flag = self.heater_dict[hr]
                    if int(self.loop_config) in self.loop_list:
                        self.device_write("RANGE " + str(self.loop_config) + ',' + str(flag))
                    else:
                        general.message('Invalid loop')
                        sys.exit()
                else:
                    general.message("Invalid heater range")
                    sys.exit()
            elif len(heater) == 0:
                raw_answer = int(self.device_query("RANGE? " + str(self.loop_config)))
                answer = cutil.search_keys_dictionary(self.heater_dict, raw_answer)
                return answer
            else:
                general.message("Invalid argument")
                sys.exit()

        elif self.test_flag == 'test':                           
            if  len(heater) == 1:
                hr = str(heater[0])
                if hr in self.heater_dict:
                    flag = self.heater_dict[hr]
                    assert(int(self.loop_config) in self.loop_list), 'Invalid loop argument'
                else:
                    assert(1 == 2), "Invalid heater range"
            elif len(heater) == 0:
                answer = self.test_heater_range
                return answer
            else:
                assert(1 == 2), "Invalid heater range"

    def tc_heater_power(self):
        if self.test_flag != 'test':
            answer1 = self.tc_heater_range()
            if int(self.loop_config) in self.loop_list:
                answer = float(self.device_query('HTR? ' + str(self.loop_config)))
                full_answer = [answer, answer1]
                return full_answer
            else:
                general.message('Invalid loop')
                sys.exit()              

        elif self.test_flag == 'test':
            assert(int(self.loop_config) in self.loop_list), 'Invalid loop argument'
            answer1 = self.test_heater_range
            answer = self.test_heater_percentage
            full_answer = [answer, answer1]
            return full_answer

    def tc_sensor(self, *sensor): 
        if self.test_flag != 'test':
            if len(sensor) == 1:
                sens = int(sensor[0])
                if self.loop_config in self.loop_list:
                    pass
                else:
                    general.message('Invalid loop')
                    sys.exit()
                if sens in self.sens_dict:
                    self.device_write('OUTMODE '+ str(self.loop_config) + ',' + '1,' + str(sens) +',0')
                else:
                    general.message('Invalid sensor')
                    sys.exit()

            elif len(sensor) == 0:
                # check whether using rs-232 we have the same
                # b'1,2,0\r\n' - GPIB
                raw_answer1 = self.device_query('OUTMODE?' + str(self.loop_config))
                if self.config['interface'] == 'gpib':
                    raw_answer2 = int(raw_answer1.decode()[2])
                elif self.config['interface'] == 'rs232':
                    raw_answer2 = int(raw_answer1[2])
                if raw_answer2 in self.sens_dict:
                    answer = self.sens_dict[raw_answer2]
                    return answer
                else:
                    general.message('Invalid response of the device')
                    sys.exit()

        elif self.test_flag == 'test':
            if len(sensor) == 1:
                sens = int(sensor[0])
                assert(self.loop_config in self.loop_list), 'Invalid loop argument'
                assert(sens in self.sens_dict), 'Invalid sensor'
            elif len(sensor) == 0:
                answer = self.test_sensor
                return answer

    def tc_lock_keyboard(self, *lock):
        if self.test_flag != 'test':
            if len(lock) == 1:
                lk = str(lock[0])
                if lk in self.lock_dict:
                    flag = self.lock_dict[lk]
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
                # check whether using rs-232 we have the same
                # b'0,123\r\n'
                if self.config['interface'] == 'gpib':
                    answer1 = int(raw_answer1.decode()[0])
                elif self.config['interface'] == 'rs232':
                    answer1 = int(raw_answer1[0])
                answer2 = int(self.device_query('MODE?'))
                if answer1 == 1 and answer2 == 0:
                    answer_flag = 0
                    answer = cutil.search_keys_dictionary(self.lock_dict, answer_flag)
                    return answer
                elif answer1 == 1 and answer2 == 1:
                    answer_flag = 1
                    answer = cutil.search_keys_dictionary(self.lock_dict, answer_flag)
                    return answer
                elif answer1 == 0 and answer2 == 0:
                    answer_flag = 2
                    answer = cutil.search_keys_dictionary(self.lock_dict, answer_flag)
                    return answer
                elif answer1 == 0 and answer2 == 1:
                    answer_flag = 3
                    answer = cutil.search_keys_dictionary(self.lock_dict, answer_flag)
                    return answer
            else:
                general.message("Invalid argument")
                sys.exit()                      

        elif self.test_flag == 'test':
            if len(lock) == 1:
                lk = str(lock[0])
                if lk in self.lock_dict:
                    flag = self.lock_dict[lk]
                else:
                    assert(1 == 2), "Invalid lock argument"
            elif len(lock) == 0:
                answer = self.test_lock
                return answer    
            else:
                assert(1 == 2), "Invalid argument"

    def tc_command(self, command):
        if self.test_flag != 'test':
            self.device_write(command)
        elif self.test_flag == 'test':
            pass

    def tc_query(self, command):
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