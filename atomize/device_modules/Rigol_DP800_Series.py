#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import gc
import sys
import pyvisa
from pyvisa.constants import StopBits, Parity
import atomize.device_modules.config.config_utils as cutil
import atomize.general_modules.general_functions as general

class Rigol_DP800_Series:
    #### Basic interaction functions
    def __init__(self):

        #### Inizialization
        # setting path to *.ini file
        self.path_current_directory = os.path.dirname(__file__)
        self.path_config_file = os.path.join(self.path_current_directory, 'config','Rigol_DP832_config.ini')

        # configuration data
        self.config = cutil.read_conf_util(self.path_config_file)
        self.specific_parameters = cutil.read_specific_parameters(self.path_config_file)

        # auxilary dictionaries
        self.voltage_dict = {'V': 1, 'mV': 1000,}
        self.current_dict = {'A': 1, 'mA': 1000,}
        self.channel_dict = {'CH1': 1, 'CH2': 2, 'CH3': 3,}
        self.state_dict = {'On': 'ON', 'Off': 'OFF',}
        self.preset_dict = {'Default': 'DEFAULT', 'User1': 'USER1', 'User2': 'USER2', \
                        'User3': 'USER3', 'User4': 'USER4',}

        # Ranges and limits
        self.channels = int(self.specific_parameters['channels'])
        self.voltage_min = 0.
        self.current_min = 0.
        self.voltage_max_dict = {'CH1': int(self.specific_parameters['ch1_voltage_max']), \
                'CH2': int(self.specific_parameters['ch2_voltage_max']), 'CH3': int(self.specific_parameters['ch3_voltage_max']),}
        self.current_max_dict = {'CH1': int(self.specific_parameters['ch1_current_max']), \
                'CH2': int(self.specific_parameters['ch2_current_max']), 'CH3': int(self.specific_parameters['ch3_current_max']),}

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
                        general.wait('50 ms')
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

            elif self.config['interface'] == 'ethernet':
                try:
                    self.status_flag = 1
                    rm = pyvisa.ResourceManager()
                    self.device = rm.open_resource(self.config['ethernet_address'])
                    self.device.timeout = self.config['timeout'] # in ms
                    try:
                        # test should be here
                        self.device_write('*CLS')
                    except pyvisa.VisaIOError:
                        general.message("No connection")
                        self.status_flag = 0
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
        elif self.test_flag == 'test':
            self.test_voltage = 1.
            self.test_current = 0.2
            self.test_state = 'Off'
            self.test_measure = [2.0, 0.05, 0.10]

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
                # device is quite slow
                general.wait('10 ms')
            elif self.config['interface'] == 'ethernet':
                answer = self.device.query(command)
                # device is quite slow
                general.wait('10 ms')
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
                        vtg_max = self.voltage_max_dict[ch]
                        if scaling in self.voltage_dict:
                            coef = self.voltage_dict[scaling]
                            if vtg/coef >= self.voltage_min and vtg/coef <= vtg_max:
                                self.device_write(':SOURce' + str(flag) + ':VOLTage ' + str(vtg/coef))
                            else:
                                general.message("Incorrect voltage range")
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
                        answer = float(self.device_query(':SOURce' + str(flag) + ':VOLTage?'))
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
                vtg_max = self.voltage_max_dict[ch]
                coef = self.voltage_dict[scaling]
                assert(vtg/coef >= self.voltage_min and vtg/coef <= vtg_max), "Incorrect voltage range"
            elif len(voltage) == 1:
                ch = str(voltage[0])
                assert(ch in self.channel_dict), 'Invalid channel argument'
                flag = self.channel_dict[ch]
                assert(flag <= self.channels), "Invalid channel"
                answer = self.test_voltage
                return answer

    def power_supply_current(self, *current):
        if self.test_flag != 'test':
            if len(current) == 2:
                ch = str(current[0])
                temp = current[1].split(" ")
                curr = float(temp[0])
                scaling = temp[1]

                if ch in self.channel_dict:
                    flag = self.channel_dict[ch]
                    if flag <= self.channels:
                        curr_max = self.current_max_dict[ch]
                        if scaling in self.current_dict:
                            coef = self.current_dict[scaling]
                            if curr/coef >= self.current_min and curr/coef <= curr_max:
                                self.device_write(':SOURce' + str(flag) + ':CURRent ' + str(curr/coef))
                            else:
                                general.message("Incorrect current range")
                                sys.exit()
                        else:
                            general.message("Incorrect current scaling")
                            sys.exit()
                    else:
                        general.message("Invalid channel")
                        sys.exit()
                else:
                    general.message("Invalid channel")
                    sys.exit()

            elif len(current) == 1:
                ch = str(current[0])
                if ch in self.channel_dict:
                    flag = self.channel_dict[ch]
                    if flag <= self.channels:
                        answer = float(self.device_query(':SOURce' + str(flag) + ':CURRent?'))
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
            if len(current) == 2:
                ch = str(current[0])
                temp = current[1].split(" ")
                curr = float(temp[0])
                scaling = temp[1]
                assert(ch in self.channel_dict), 'Invalid channel argument'
                flag = self.channel_dict[ch]
                assert(flag <= self.channels), "Invalid channel"
                assert(scaling in self.current_dict), 'Invalid scaling argument'
                curr_max = self.current_max_dict[ch]
                coef = self.current_dict[scaling]
                assert(curr/coef >= self.current_min and curr/coef <= curr_max), "Incorrect current range"
            elif len(current) == 1:
                ch = str(current[0])
                assert(ch in self.channel_dict), 'Invalid channel argument'
                flag = self.channel_dict[ch]
                assert(flag <= self.channels), "Invalid channel"
                answer = self.test_current
                return answer

    def power_supply_overvoltage(self, *voltage):
        if self.test_flag != 'test':
            if len(voltage) == 2:
                ch = str(voltage[0])
                temp = voltage[1].split(" ")
                vtg = float(temp[0])
                scaling = temp[1]

                if ch in self.channel_dict:
                    flag = self.channel_dict[ch]
                    if flag <= self.channels:
                        vtg_max = self.voltage_max_dict[ch]
                        if scaling in self.voltage_dict:
                            coef = self.voltage_dict[scaling]
                            if vtg/coef >= self.voltage_min and vtg/coef <= vtg_max + 3:
                                self.device_write(':SOURce' + str(flag) + ':VOLTage:PROTection ' + str(vtg/coef))
                            else:
                                general.message("Incorrect overvoltage protection range")
                                sys.exit()
                        else:
                            general.message("Incorrect overvoltage protection scaling")
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
                        answer = float(self.device_query(':SOURce' + str(flag) + ':VOLTage:PROTection?'))
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
                vtg_max = self.voltage_max_dict[ch]
                coef = self.voltage_dict[scaling]
                assert(vtg/coef >= self.voltage_min and vtg/coef <= vtg_max), "Incorrect overvoltage protection range"
            elif len(voltage) == 1:
                ch = str(voltage[0])
                assert(ch in self.channel_dict), 'Invalid channel argument'
                flag = self.channel_dict[ch]
                assert(flag <= self.channels), "Invalid channel"
                answer = self.test_voltage
                return answer

    def power_supply_overcurrent(self, *current):
        if self.test_flag != 'test':
            if len(current) == 2:
                ch = str(current[0])
                temp = current[1].split(" ")
                curr = float(temp[0])
                scaling = temp[1]

                if ch in self.channel_dict:
                    flag = self.channel_dict[ch]
                    if flag <= self.channels:
                        curr_max = self.current_max_dict[ch]
                        if scaling in self.current_dict:
                            coef = self.current_dict[scaling]
                            if curr/coef >= self.current_min and curr/coef <= curr_max + 0.3:
                                self.device_write(':SOURce' + str(flag) + ':CURRent:PROTection ' + str(curr/coef))
                            else:
                                general.message("Incorrect overcurrent protection range")
                                sys.exit()                           
                        else:
                            general.message("Incorrect overcurrent protection scaling")
                            sys.exit()
                    else:
                        general.message("Invalid channel")
                        sys.exit()
                else:
                    general.message("Invalid channel")
                    sys.exit()

            elif len(current) == 1:
                ch = str(current[0])
                if ch in self.channel_dict:
                    flag = self.channel_dict[ch]
                    if flag <= self.channels:
                        answer = float(self.device_query(':SOURce' + str(flag) + ':CURRent:PROTection?'))
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
            if len(current) == 2:
                ch = str(current[0])
                temp = current[1].split(" ")
                curr = float(temp[0])
                scaling = temp[1]
                assert(ch in self.channel_dict), 'Invalid channel argument'
                flag = self.channel_dict[ch]
                assert(flag <= self.channels), "Invalid channel"
                assert(scaling in self.current_dict), 'Invalid overcurrent protection scaling'
                curr_max = self.current_max_dict[ch]
                coef = self.current_dict[scaling]
                assert(curr/coef >= self.current_min and curr/coef <= curr_max), "Incorrect overcurrent protection range"
            elif len(current) == 1:
                ch = str(current[0])
                assert(ch in self.channel_dict), 'Invalid channel argument'
                flag = self.channel_dict[ch]
                assert(flag <= self.channels), "Invalid channel"
                answer = self.test_current
                return answer

    def power_supply_channel_state(self, *state):
        if self.test_flag != 'test':
            if len(state) == 2:
                ch = str(state[0])
                st = str(state[1])
                if ch in self.channel_dict:
                    flag = self.channel_dict[ch]
                    if flag <= self.channels:
                        if st in self.state_dict:
                            self.device_write(':OUTPut CH' + str(flag) + ',' + str(self.state_dict[st]))
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
                        raw_answer = self.device_query(':OUTPut? CH' + str(flag))
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

    def power_supply_measure(self, channel):
        if self.test_flag != 'test':
            ch = str(channel)
            if ch in self.channel_dict:
                flag = self.channel_dict[ch]
                if flag <= self.channels:
                    raw_answer = self.device_query(':MEASure:ALL? CH' + str(flag)).split(',')
                    answer = [float(raw_answer[0]), float(raw_answer[1]), float(raw_answer[2])]
                    return answer
                else:
                    general.message('Invalid channel')
                    sys.exit()
            else:
                general.message('Invalid channel')
                sys.exit()

        elif self.test_flag == 'test':
            ch = str(channel)
            assert(ch in self.channel_dict), 'Invalid channel'
            flag = self.channel_dict[ch]
            assert(flag <= self.channels), 'Invalid channel'
            answer = self.test_measure
            return answer

    def power_supply_set_preset(self, preset):
        if self.test_flag != 'test':
            prst = str(preset)
            if prst in self.preset_dict:
                flag = self.preset_dict[prst]
                self.device_write(':PRESet:KEY ' + str(flag))
                self.device_write(':PRESet:APPLy')
            else:
                general.message('Invalid preset argument')
                sys.exit()

        elif self.test_flag == 'test':
            prst = str(preset)
            assert(prst in self.preset_dict), 'Invalid preset argument'

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
