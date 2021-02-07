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
path_config_file = os.path.join(path_current_directory, 'config','SR_DG535_config.ini')

# configuration data
config = cutil.read_conf_util(path_config_file)
specific_parameters = cutil.read_specific_parameters(path_config_file)

# auxilary dictionaries
delay_channel_dict = {'T0': 1, 'A': 2, 'B': 3, 'C': 5, 'D': 6,}
input_output_channel_dict = {'Trigger': 0, 'T0': 1, 'A': 2, 'B': 3, 'AB': 4, 'C': 5, 'D': 6, 'CD': 7,}
output_channel_dict = {'T0': 1, 'A': 2, 'B': 3, 'AB': 4, 'C': 5, 'D': 6, 'CD': 7,}
time_dict = {'s': 1, 'ms': 1000, 'us': 1000000, 'ns': 1000000000, 'ps': 1000000000000,}
impedance_dict = {'50': 0, 'High Z': 1,}
mode_dict = {'TTL': 0, 'NIM': 1, 'ECL': 2, 'Variable': 3,}
ampl_dict = {'V': 1, 'mV': 1000,}
polarity_dict = {'Inverted': 0, 'Normal': 1,}

# Ranges and limits
delay_max = 999.99
delay_min = 0.
var_ampl_min = -3.
var_ampl_max = 4.

# Test run parameters
# These values are returned by the modules in the test run 
if len(sys.argv) > 1:
    test_flag = sys.argv[1]
else:
    test_flag = 'None'

test_delay = 'B + 1.0'
test_impedance = 'High Z'
test_mode = 'TTL'
test_amplitude_offset = 'Amplitude: 2. V; Offset: 0. V'
test_polarity = 'Normal'

class SR_DG535:
    #### Basic interaction functions
    def __init__(self):
        if test_flag != 'test':
            if config['interface'] == 'gpib':
                try:
                    import Gpib
                    self.status_flag = 1
                    self.device = Gpib.Gpib(config['board_address'], config['gpib_address'])
                    try:
                        pass
                        # test should be here
                        #self.device_write('*CLS')

                    except BrokenPipeError:
                        general.message("No connection")
                        self.status_flag = 0
                        sys.exit()
                except BrokenPipeError:
                    general.message("No connection")
                    self.status_flag = 0
                    sys.exit()

            else:
                general.message("Incorrect interface setting")
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
                answer = self.device.read().decode()
        else:
            general.message("No Connection")
            self.status_flag = 0
            sys.exit()

    #### device specific functions
    def delay_gen_name(self):
        if test_flag != 'test':
            answer = config['name']
            return answer
        elif test_flag == 'test':
            answer = config['name']
            return answer

    def delay_gen_delay(self, *delay):
        if test_flag != 'test':
            if len(delay) == 3:
                ch_1 = str(delay[0])
                ch_2 = str(delay[1])
                temp = delay[2].split(" ")
                delay = float(temp[0])
                scaling = temp[1]
                if (ch_1 in delay_channel_dict) and (ch_2 in delay_channel_dict):
                    flag_1 = delay_channel_dict[ch_1]
                    flag_2 = delay_channel_dict[ch_2]
                    if scaling in time_dict:
                        coef = time_dict[scaling]
                        if delay/coef >= delay_min and delay/coef <= delay_max:
                            self.device_write('DT ' + str(flag_1) + ',' + str(flag_2) + ',' + str(delay/coef))
                        else:
                            general.message("Incorrect delay range")
                            sys.exit()
                    else:
                        general.message("Incorrect delay scaling")
                        sys.exit()
                else:
                    general.message("Incorrect channel")
                    sys.exit()

            elif len(delay) == 1:
                ch_1 = str(delay[0])
                if (ch_1 in delay_channel_dict):
                    flag_1 = delay_channel_dict[ch_1]
                    raw_answer = str(self.device_query('DT ' + str(flag_1))).split(',')
                    ch_answer = cutil.search_keys_dictionary(delay_channel_dict, int(raw_answer[0]))
                    delay_answer = float(raw_answer[1])*1000000
                    answer = str(ch_answer) + ' + ' + str(delay_answer)
                    return answer
                else:
                    general.message("Incorrect channel")
                    sys.exit()

            else:
                general.message("Invalid argument")
                sys.exit()

        elif test_flag == 'test':
            if len(delay) == 3:
                ch_1 = str(delay[0])
                ch_2 = str(delay[1])
                temp = delay[2].split(" ")
                delay = float(temp[0])
                scaling = temp[1]
                assert(ch_1 in delay_channel_dict), 'Invalid channel_1 argument'
                assert(ch_2 in delay_channel_dict), 'Invalid channel_2 argument'
                assert(scaling in time_dict), 'Invalid scaling argument'
                coef = time_dict[scaling]
                assert(delay/coef >= delay_min and delay/coef <= delay_max), "Incorrect delay range"

            elif len(delay) == 1:
                ch_1 = str(delay[0])
                assert(ch_1 in delay_channel_dict), 'Incorrect channel'
                answer = test_delay
                return answer
            else:
                assert(1 == 2), 'Invalid argument'

    def delay_gen_impedance(self, *impedance):
        if test_flag != 'test':
            if len(impedance) == 2:
                ch = str(impedance[0])
                imp = str(impedance[1])
                if ch in input_output_channel_dict:
                    flag_1 = input_output_channel_dict[ch]
                    if imp in impedance_dict:
                        flag_2 = impedance_dict[imp]
                        self.device_write('TZ ' + str(flag_1) + ',' + str(flag_2))
                    else:
                        general.message("Incorrect impedance")
                        sys.exit()
                else:
                    general.message("Invalid channel")
                    sys.exit()    
            
            elif len(impedance) == 1:
                ch = str(impedance[0])
                if ch in input_output_channel_dict:
                    flag = input_output_channel_dict[ch]
                    raw_answer = int(self.device_query('TZ ' + str(flag)))
                    answer = cutil.search_keys_dictionary(impedance_dict, raw_answer)
                    return answer
                else:
                    general.message("Invalid channel")
                    sys.exit()
            else:
                general.message("Invalid argument")
                sys.exit()

        elif test_flag == 'test':
            if len(impedance) == 2:
                ch = str(impedance[0])
                imp = str(impedance[1])
                assert(ch in input_output_channel_dict), 'Invalid channel argument'
                assert(imp in impedance_dict), 'Invalid impedance argument'

            elif len(impedance) == 1:
                ch = str(impedance[0])
                assert(ch in input_output_channel_dict), 'Invalid channel argument'
                answer = test_impedance
                return answer

    def delay_gen_output_mode(self, *mode):
        if test_flag != 'test':
            if len(mode) == 2:
                ch = str(mode[0])
                md = str(mode[1])
                if ch in output_channel_dict:
                    flag_1 = output_channel_dict[ch]
                    if md in mode_dict:
                        flag_2 = mode_dict[md]
                        self.device_write('OM ' + str(flag_1) + ',' + str(flag_2))
                    else:
                        general.message("Incorrect mode")
                        sys.exit()
                else:
                    general.message("Invalid channel")
                    sys.exit()    
            
            elif len(mode) == 1:
                ch = str(mode[0])
                if ch in output_channel_dict:
                    flag = output_channel_dict[ch]
                    raw_answer = int(self.device_query('OM ' + str(flag)))
                    answer = cutil.search_keys_dictionary(mode_dict, raw_answer)
                    return answer
                else:
                    general.message("Invalid channel")
                    sys.exit()
            else:
                general.message("Invalid argument")
                sys.exit()

        elif test_flag == 'test':
            if len(mode) == 2:
                ch = str(mode[0])
                md = str(mode[1])
                assert(ch in output_channel_dict), 'Invalid channel argument'
                assert(md in mode_dict), 'Invalid mode argument'

            elif len(mode) == 1:
                ch = str(mode[0])
                assert(ch in output_channel_dict), 'Invalid channel argument'
                answer = test_mode
                return answer

    def delay_gen_amplitude_offset(self, *amplitude_offset):
        if test_flag != 'test':
            if len(amplutide) == 3:
                ch = str(amplutide[0])
                temp_1 = amplutide[1].split(" ")
                temp_2 = amplutide[2].split(" ")
                ampl = float(temp_1[0])
                scaling_1 = temp_1[1]
                ofst = float(temp_2[0])
                scaling_2 = temp_2[1]
                if ch in output_channel_dict:
                    flag_1 = output_channel_dict[ch]
                    if (scaling_1 in ampl_dict) and (scaling_2 in ampl_dict):
                        coef_1 = ampl_dict[scaling_1]
                        coef_2 = ampl_dict[scaling_2]
                        if int(self.device_query('OM ' + str(flag_1))) == 3:
                            general.wait('30 ms')
                            if (ampl/coef_1 + ofst/coef_2) >= var_ampl_min and \
                            (ampl/coef_1 + ofst/coef_2) <= var_ampl_max and (ampl/coef_1) >= var_ampl_min \
                            (ampl/coef_1) <= var_ampl_max and (ofst/coef_2) >= var_ampl_min \
                            (ofst/coef_2) <= var_ampl_max:
                                self.device_write('OA ' + str(flag_1) + ',' + str(ampl/coef_1))
                                self.device_write('OO ' + str(flag_1) + ',' + str(ofst/coef_2))
                            else:
                                general.message("Incorrect amplitude and offset range")
                                sys.exit()
                        else:
                            general.message("You are not in Variable mode")
                            pass
                    else:
                        general.message("Incorrect scaling")
                        sys.exit()
                else:
                    general.message("Invalid channel")
                    sys.exit()
            
            elif len(amplutide) == 1:
                ch = str(amplutide[0])
                if ch in output_channel_dict:
                    flag = output_channel_dict[ch]
                    answer_1 = float(self.device_query('OA ' + str(flag)))
                    answer_2 = float(self.device_query('OO ' + str(flag)))
                    answer = 'Amplitude: ' + str(answer_1) + ' V; ' + 'Offset: ' + str(answer_2) + ' V'
                    return answer
                else:
                    general.message("Invalid channel")
                    sys.exit()
            else:
                general.message("Invalid argument")
                sys.exit()

        elif test_flag == 'test':
            if len(amplutide) == 3:
                ch = str(amplutide[0])
                temp_1 = amplutide[1].split(" ")
                temp_2 = amplutide[2].split(" ")
                ampl = float(temp_1[0])
                scaling_1 = temp_1[1]
                ofst = float(temp_2[0])
                scaling_2 = temp_2[1]
                assert(ch in output_channel_dict), 'Invalid channel'
                assert(scaling_1 in ampl_dict), 'Invalid scaling of amplitude setting'
                assert(scaling_2 in ampl_dict), 'Invalid scaling of offset setting'
                coef_1 = ampl_dict[scaling_1]
                coef_2 = ampl_dict[scaling_2]
                assert(ampl/coef_1 >= var_ampl_min and ampl/coef_1 <= var_ampl_max), "Incorrect amplitude range"
                assert(ofst/coef_2 >= var_ampl_min and ofst/coef_2 <= var_ampl_max), "Incorrect offset range"
                assert(ampl/coef_1 + ofst/coef_2 >= var_ampl_min and ampl/coef_1 + ofst/coef_2 <= var_ampl_max), "Incorrect range"

            elif len(amplutide) == 1:
                ch = str(amplutide[0])
                assert(ch in output_channel_dict), 'Invalid channel argument'
                answer = test_amplitude_offset
                return answer

    def delay_gen_output_polarity(self, *polarity):
        if test_flag != 'test':
            if len(polarity) == 2:
                ch = str(polarity[0])
                plr = str(polarity[1])
                if ch in output_channel_dict:
                    flag_1 = output_channel_dict[ch]
                    if plr in polarity_dict:
                        flag_2 = polarity_dict[plr]
                        if int(self.device_query('OM ' + str(flag_1))) != 3:
                            general.wait('30 ms')
                            self.device_write('OP ' + str(flag_1) + ',' + str(flag_2))
                        else:
                            general.message("You are in Variable mode")
                    else:
                        general.message("Incorrect polarity")
                        sys.exit()
                else:
                    general.message("Invalid channel")
                    sys.exit()    
            
            elif len(polarity) == 1:
                ch = str(polarity[0])
                if ch in output_channel_dict:
                    flag = output_channel_dict[ch]
                    raw_answer = int(self.device_query('OP ' + str(flag)))
                    answer = cutil.search_keys_dictionary(polarity_dict, raw_answer)
                    return answer
                else:
                    general.message("Invalid channel")
                    sys.exit()
            else:
                general.message("Invalid argument")
                sys.exit()

        elif test_flag == 'test':
            if len(polarity) == 2:
                ch = str(polarity[0])
                plr = str(polarity[1])
                assert(ch in output_channel_dict), 'Invalid channel argument'
                assert(plr in polarity_dict), 'Invalid polarity argument'

            elif len(polarity) == 1:
                ch = str(polarity[0])
                assert(ch in output_channel_dict), 'Invalid channel argument'
                answer = test_polarity
                return answer

    # TO DO trigger commands

    def delay_gen_command(self, command):
        if test_flag != 'test':
            self.device_write(command)
        elif test_flag == 'test':
            pass

    def delay_gen_query(self, command):
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
