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
path_config_file = os.path.join(path_current_directory, 'config','SR_DC205_config.ini')

# configuration data
config = cutil.read_conf_util(path_config_file)
specific_parameters = cutil.read_specific_parameters(path_config_file)

# auxilary dictionaries
voltage_dict = {'V': 1, 'mV': 1000,}
channel_dict = {'CH1': 1,}
state_dict = {'On': 1, 'Off': 0,}
range_dict = {'1 V': 0, '10 V': 1, '100 V': 2,}
lock_dict = {'On': 0, 'Off': 1,}

# Ranges and limits
channels = int(specific_parameters['channels'])
voltage_min_range1 = -1.01
voltage_max_range1 = 1.01
voltage_min_range2 = -10.1
voltage_max_range2 = 10.1
voltage_min_range3 = -101
voltage_max_range3 = 101

# Test run parameters
# These values are returned by the modules in the test run 
if len(sys.argv) > 1:
    test_flag = sys.argv[1]
else:
    test_flag = 'None'

test_voltage = 1.
test_state = 'Off'
test_range = '1 V'
test_lock = 'On'

class SR_DC205:
    #### Basic interaction functions
    def __init__(self):
        if test_flag != 'test':
            if config['interface'] == 'rs232':
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

            elif config['interface'] != 'rs232':
                general.message('Invalid interface')
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
            if config['interface'] == 'rs232':
                answer = self.device.query(command)
                return answer
        else:
            general.message("No Connection")
            self.status_flag = 0
            sys.exit()

    #### device specific functions
    def power_supply_name(self):
        if test_flag != 'test':
            answer = self.device_query('*IDN?')
            return answer
        elif test_flag == 'test':
            answer = config['name']
            return answer

    def power_supply_voltage(self, *voltage):
        if test_flag != 'test':
            if len(voltage) == 2:
                ch = str(voltage[0])
                temp = voltage[1].split(" ")
                vtg = float(temp[0])
                scaling = temp[1]

                if ch in channel_dict:
                    flag = channel_dict[ch]
                    if flag <= channels:
                        vtg_max = voltage_max_dict[ch]
                        if scaling in voltage_dict:
                            coef = voltage_dict[scaling]
                            rng_check = int(self.device_query('RNGE?'))
                            if rng_check == 0:
                                if vtg/coef >= voltage_min_range1 and vtg/coef <= voltage_max_range1:
                                    self.device_write('VOLT ' + str(vtg/coef))
                                else:
                                    general.message("Incorrect voltage for range 1 V")
                                    sys.exit()
                            elif rng_check == 1:
                                if vtg/coef >= voltage_min_range2 and vtg/coef <= voltage_max_range2:
                                    self.device_write('VOLT ' + str(vtg/coef))
                                else:
                                    general.message("Incorrect voltage for range 10 V")
                                    sys.exit()
                            elif rng_check == 2:
                                if vtg/coef >= voltage_min_range3 and vtg/coef <= voltage_max_range3:
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
                if ch in channel_dict:
                    flag = channel_dict[ch]
                    if flag <= channels:
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

        elif test_flag == 'test':
            if len(voltage) == 2:
                ch = str(voltage[0])
                temp = voltage[1].split(" ")
                vtg = float(temp[0])
                scaling = temp[1]
                assert(ch in channel_dict), 'Invalid channel argument'
                flag = channel_dict[ch]
                assert(flag <= channels), "Invalid channel"
                assert(scaling in voltage_dict), 'Invalid scaling argument'
                assert(vtg/coef >= voltage_min_range3 and vtg/coef <= voltage_max_range3), "Incorrect voltage range"
            elif len(voltage) == 1:
                ch = str(voltage[0])
                assert(ch in channel_dict), 'Invalid channel argument'
                flag = channel_dict[ch]
                assert(flag <= channels), "Invalid channel"
                answer = test_voltage
                return answer

    def power_supply_range(self, *range):
        if test_flag != 'test':
            if len(range) == 1:
                rng = str(range[0])
                if rng in range_dict:
                    flag = range_dict[rng]
                    self.device_write('RNGE ' + str(flag))                       
                else:
                    general.message("Incorrect range")
                    sys.exit()

            elif len(range) == 0:
                raw_answer = int(self.device_query('RNGE?'))
                answer = cutil.search_keys_dictionary(range_dict, raw_answer)
                return answer
            else:
                general.message("Invalid argument")
                sys.exit()

        elif test_flag == 'test':
            if len(range) == 1:
                rng = str(range[0])
                assert(rng in range_dict), "Incorrect range"

            elif len(range) == 0:
                answer = test_range
                return answer
            else:
                assert(1 == 2), "Invalid argument"
    
    def power_supply_interlock(self, *interlock):
        if test_flag != 'test':
            if len(interlock) == 0:
                raw_answer = int(self.device_query('ILOC?'))
                answer = cutil.search_keys_dictionary(lock_dict, raw_answer)
                return answer
            else:
                general.message("Invalid argument")
                sys.exit()

        elif test_flag == 'test':
            if len(interlock) == 0:
                answer = test_lock
                return answer
            else:
                assert(1 == 2), "Invalid argument"

    def power_supply_channel_state(self, *state):
        if test_flag != 'test':
            if len(state) == 2:
                ch = str(state[0])
                st = str(state[1])
                if ch in channel_dict:
                    flag = channel_dict[ch]
                    if flag <= channels:
                        if st in state_dict:
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
                if ch in channel_dict:
                    flag = channel_dict[ch]
                    if flag <= channels:
                        raw_answer = int(self.device_query('SOUT?'))
                        answer = cutil.search_keys_dictionary(state_dict, raw_answer)
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

        elif test_flag == 'test':
            if len(state) == 2:
                ch = str(state[0])
                st = str(state[1])
                assert(ch in channel_dict), 'Invalid channel argument'
                flag = channel_dict[ch]
                assert(flag <= channels), "Invalid channel"
                assert(st in state_dict), 'Invalid state argument'
            elif len(state) == 1:
                ch = str(state[0])
                assert(ch in channel_dict), 'Invalid channel argument'
                flag = channel_dict[ch]
                assert(flag <= channels), "Invalid channel"
                answer = test_state
                return answer        

    def power_supply_command(self, command):
        if test_flag != 'test':
            self.device_write(command)
        elif test_flag == 'test':
            pass

    def power_supply_query(self, command):
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
