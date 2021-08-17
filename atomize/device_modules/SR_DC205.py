#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import gc
import sys
import pyvisa
from pyvisa.constants import StopBits, Parity
import atomize.device_modules.config.config_utils as cutil
import atomize.general_modules.general_functions as general

class SR_DC205:
    #### Basic interaction functions
    def __init__(self):

        #### Inizialization
        # setting path to *.ini file
        self.path_current_directory = os.path.dirname(__file__)
        self.path_config_file = os.path.join(self.path_current_directory, 'config','SR_DC205_config.ini')

        # configuration data
        self.config = cutil.read_conf_util(self.path_config_file)
        self.specific_parameters = cutil.read_specific_parameters(self.path_config_file)

        # auxilary dictionaries
        self.voltage_dict = {'V': 1, 'mV': 1000, }
        self.channel_dict = {'CH1': 1, }
        self.state_dict = {'On': 1, 'Off': 0, }
        self.range_dict = {'1 V': 0, '10 V': 1, '100 V': 2, }
        self.lock_dict = {'On': 0, 'Off': 1, }

        # Ranges and limits
        self.channels = int(self.specific_parameters['channels'])
        self.voltage_min_range1 = -1.01
        self.voltage_max_range1 = 1.01
        self.voltage_min_range2 = -10.1
        self.voltage_max_range2 = 10.1
        self.voltage_min_range3 = -101
        self.voltage_max_range3 = 101

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
                    self.device = rm.open_resource(self.config['serial_address'], read_termination=self.config['read_termination'],
                    write_termination=self.config['write_termination'], baud_rate=self.config['baudrate'],
                    data_bits=self.config['databits'], parity=self.config['parity'], stop_bits=self.config['stopbits'])
                    self.device.timeout = self.config['timeout'] # in ms
                    try:
                        # test should be here
                        self.device_write('*CLS')
                        # better to have a pause here
                        general.wait('30 ms')
                        # When TOKN OFF, the DC205 responds with
                        # the numeric version  of the token quantity
                        self.device_write('TOKN 0')

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

            elif self.config['interface'] != 'rs232':
                general.message('Invalid interface')
                sys.exit()

        elif self.test_flag == 'test':  
            self.test_voltage = 1.
            self.test_state = 'Off'
            self.test_range = '1 V'
            self.test_lock = 'On'

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
            general.message("No Connection")
            self.status_flag = 0
            sys.exit()

    def device_query(self, command):
        if self.status_flag == 1:
            if self.config['interface'] == 'rs232':
                answer = self.device.query(command)
                return answer
        else:
            general.message("No Connection")
            self.status_flag = 0
            sys.exit()

    #### device specific functions
    def power_supply_name(self):
        if self.test_flag != 'test':
            answer = self.device_query('*IDN?')
            return answer
        elif self.test_flag == 'test':
            answer = self.config['name']
            return answer

    def power_supply_voltage(self, *voltage):
        if self.test_flag != 'test':
            if len(voltage) == 2:
                ch = str(voltage[0])
                temp = voltage[1].split(" ")
                vtg = float(temp[0])
                scaling = temp[1]

                if ch in self.channel_dict:
                    flag = self.channel_dict[ch]
                    if flag <= self.channels:
                        vtg_max = voltage_max_dict[ch]
                        if scaling in self.voltage_dict:
                            coef = self.voltage_dict[scaling]
                            rng_check = int(self.device_query('RNGE?'))
                            if rng_check == 0:
                                if vtg/coef >= self.voltage_min_range1 and vtg/coef <= self.voltage_max_range1:
                                    self.device_write('VOLT ' + str(vtg/coef))
                                else:
                                    general.message("Incorrect voltage for range 1 V")
                                    sys.exit()
                            elif rng_check == 1:
                                if vtg/coef >= self.voltage_min_range2 and vtg/coef <= self.voltage_max_range2:
                                    self.device_write('VOLT ' + str(vtg/coef))
                                else:
                                    general.message("Incorrect voltage for range 10 V")
                                    sys.exit()
                            elif rng_check == 2:
                                if vtg/coef >= self.voltage_min_range3 and vtg/coef <= self.voltage_max_range3:
                                    self.device_write('VOLT ' + str(vtg/coef))
                                else:
                                    general.message("Incorrect voltage for range 100 V")
                                    sys.exit()                                                            
                        else:
                            general.message("Incorrect voltage scaling")
                            sys.exit()
                    else:
                        general.message("Invalid channel")
                        sys.exit()
                else:
                    general.message("Invalid channel")
                    sys.exit()

            elif len(voltage) == 1:
                ch = str(voltage[0])
                if ch in self.channel_dict:
                    flag = self.channel_dict[ch]
                    if flag <= self.channels:
                        answer = float(self.device_query('VOLT?'))
                        return answer
                    else:
                        general.message("Invalid channel")
                        sys.exit()
                else:
                    general.message("Invalid channel")
                    sys.exit()
            else:
                general.message("Invalid argument")
                sys.exit()

        elif self.test_flag == 'test':
            if len(voltage) == 2:
                ch = str(voltage[0])
                temp = voltage[1].split(" ")
                vtg = float(temp[0])
                scaling = temp[1]
                assert(ch in self.channel_dict), 'Invalid channel argument'
                flag = self.channel_dict[ch]
                assert(flag <= self.channels), "Invalid channel"
                assert(scaling in self.voltage_dict), 'Invalid scaling argument'
                assert(vtg/coef >= self.voltage_min_range3 and vtg/coef <= self.voltage_max_range3), "Incorrect voltage range"
            elif len(voltage) == 1:
                ch = str(voltage[0])
                assert(ch in self.channel_dict), 'Invalid channel argument'
                flag = self.channel_dict[ch]
                assert(flag <= self.channels), "Invalid channel"
                answer = self.test_voltage
                return answer

    def power_supply_range(self, *range):
        if self.test_flag != 'test':
            if len(range) == 1:
                rng = str(range[0])
                if rng in self.range_dict:
                    flag = self.range_dict[rng]
                    self.device_write('RNGE ' + str(flag))                       
                else:
                    general.message("Incorrect range")
                    sys.exit()

            elif len(range) == 0:
                raw_answer = int(self.device_query('RNGE?'))
                answer = cutil.search_keys_dictionary(self.range_dict, raw_answer)
                return answer
            else:
                general.message("Invalid argument")
                sys.exit()

        elif self.test_flag == 'test':
            if len(range) == 1:
                rng = str(range[0])
                assert(rng in self.range_dict), "Incorrect range"

            elif len(range) == 0:
                answer = self.test_range
                return answer
            else:
                assert(1 == 2), "Invalid argument"
    
    def power_supply_interlock(self, *interlock):
        if self.test_flag != 'test':
            if len(interlock) == 0:
                raw_answer = int(self.device_query('ILOC?'))
                answer = cutil.search_keys_dictionary(self.lock_dict, raw_answer)
                return answer
            else:
                general.message("Invalid argument")
                sys.exit()

        elif self.test_flag == 'test':
            if len(interlock) == 0:
                answer = self.test_lock
                return answer
            else:
                assert(1 == 2), "Invalid argument"

    def power_supply_channel_state(self, *state):
        if self.test_flag != 'test':
            if len(state) == 2:
                ch = str(state[0])
                st = str(state[1])
                if ch in self.channel_dict:
                    flag = self.channel_dict[ch]
                    if flag <= self.channels:
                        if st in self.state_dict:
                            rng = int(self.device_query('RNGE?'))
                            general.wait('20 ms')
                            iloc = int(self.device_query('ILOC?'))
                            if iloc != 1 and rng == 2:
                                general.message('Safety interlock is open')
                                sys.exit()
                            else:
                                self.device_write('SOUT ' + str(flag))
                        else:
                            general.message("Invalid state argument")
                            sys.exit()
                    else:
                        general.message("Invalid channel")
                        sys.exit()
                else:
                    general.message("Invalid channel")
                    sys.exit()

            elif len(state) == 1:
                ch = str(state[0])
                if ch in self.channel_dict:
                    flag = self.channel_dict[ch]
                    if flag <= self.channels:
                        raw_answer = int(self.device_query('SOUT?'))
                        answer = cutil.search_keys_dictionary(self.state_dict, raw_answer)
                        return answer
                    else:
                        general.message("Invalid channel")
                        sys.exit()
                else:
                    general.message("Invalid channel")
                    sys.exit()
            else:
                general.message("Invalid argument")
                sys.exit()

        elif self.test_flag == 'test':
            if len(state) == 2:
                ch = str(state[0])
                st = str(state[1])
                assert(ch in self.channel_dict), 'Invalid channel argument'
                flag = self.channel_dict[ch]
                assert(flag <= self.channels), "Invalid channel"
                assert(st in self.state_dict), 'Invalid state argument'
            elif len(state) == 1:
                ch = str(state[0])
                assert(ch in self.channel_dict), 'Invalid channel argument'
                flag = self.channel_dict[ch]
                assert(flag <= self.channels), "Invalid channel"
                answer = self.test_state
                return answer        

    def power_supply_command(self, command):
        if self.test_flag != 'test':
            self.device_write(command)
        elif self.test_flag == 'test':
            pass

    def power_supply_query(self, command):
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
