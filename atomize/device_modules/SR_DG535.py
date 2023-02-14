#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import gc
import sys
import pyvisa
from pyvisa.constants import StopBits, Parity
import atomize.device_modules.config.config_utils as cutil
import atomize.general_modules.general_functions as general

class SR_DG535:
    #### Basic interaction functions
    def __init__(self):

        #### Inizialization
        # setting path to *.ini file
        self.path_current_directory = os.path.dirname(__file__)
        self.path_config_file = os.path.join(self.path_current_directory, 'config','SR_DG535_config.ini')

        # configuration data
        self.config = cutil.read_conf_util(self.path_config_file)
        self.specific_parameters = cutil.read_specific_parameters(self.path_config_file)

        # auxilary dictionaries
        self.delay_channel_dict = {'T0': 1, 'A': 2, 'B': 3, 'C': 5, 'D': 6,}
        self.input_output_channel_dict = {'Trigger': 0, 'T0': 1, 'A': 2, 'B': 3, 'AB': 4, 'C': 5, 'D': 6, 'CD': 7,}
        self.output_channel_dict = {'T0': 1, 'A': 2, 'B': 3, 'AB': 4, 'C': 5, 'D': 6, 'CD': 7,}
        self.time_dict = {'s': 1, 'ms': 1000, 'us': 1000000, 'ns': 1000000000, 'ps': 1000000000000,}
        self.impedance_dict = {'50': 0, 'High Z': 1,}
        self.mode_dict = {'TTL': 0, 'NIM': 1, 'ECL': 2, 'Variable': 3,}
        self.ampl_dict = {'V': 1, 'mV': 1000,}
        self.polarity_dict = {'Inverted': 0, 'Normal': 1,}

        # Ranges and limits
        self.delay_max = 999.99
        self.delay_min = 0.
        self.var_ampl_min = -3.
        self.var_ampl_max = 4.

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

        elif self.test_flag == 'test':
            self.test_delay = 'B + 1.0'
            self.test_impedance = 'High Z'
            self.test_mode = 'TTL'
            self.test_amplitude_offset = 'Amplitude: 2. V; Offset: 0. V'
            self.test_polarity = 'Normal'

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
            if self.config['interface'] == 'gpib':
                self.device.write(command)
                general.wait('50 ms')
                answer = self.device.read().decode()
        else:
            general.message("No Connection")
            self.status_flag = 0
            sys.exit()

    #### device specific functions
    def delay_gen_name(self):
        if self.test_flag != 'test':
            answer = self.config['name']
            return answer
        elif self.test_flag == 'test':
            answer = self.config['name']
            return answer

    def delay_gen_delay(self, *delay):
        if self.test_flag != 'test':
            if len(delay) == 3:
                ch_1 = str(delay[0])
                ch_2 = str(delay[1])
                temp = delay[2].split(" ")
                delay = float(temp[0])
                scaling = temp[1]
                if (ch_1 in self.delay_channel_dict) and (ch_2 in self.delay_channel_dict):
                    flag_1 = self.delay_channel_dict[ch_1]
                    flag_2 = self.delay_channel_dict[ch_2]
                    if scaling in self.time_dict:
                        coef = self.time_dict[scaling]
                        if delay/coef >= self.delay_min and delay/coef <= self.delay_max:
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
                if (ch_1 in self.delay_channel_dict):
                    flag_1 = self.delay_channel_dict[ch_1]
                    raw_answer = str(self.device_query('DT ' + str(flag_1))).split(',')
                    ch_answer = cutil.search_keys_dictionary(self.delay_channel_dict, int(raw_answer[0]))
                    delay_answer = float(raw_answer[1])*1000000
                    answer = str(ch_answer) + ' + ' + str(delay_answer)
                    return answer
                else:
                    general.message("Incorrect channel")
                    sys.exit()

            else:
                general.message("Invalid argument")
                sys.exit()

        elif self.test_flag == 'test':
            if len(delay) == 3:
                ch_1 = str(delay[0])
                ch_2 = str(delay[1])
                temp = delay[2].split(" ")
                delay = float(temp[0])
                scaling = temp[1]
                assert(ch_1 in self.delay_channel_dict), 'Invalid channel_1 argument'
                assert(ch_2 in self.delay_channel_dict), 'Invalid channel_2 argument'
                assert(scaling in self.time_dict), 'Invalid scaling argument'
                coef = self.time_dict[scaling]
                assert(delay/coef >= self.delay_min and delay/coef <= self.delay_max), "Incorrect delay range"

            elif len(delay) == 1:
                ch_1 = str(delay[0])
                assert(ch_1 in self.delay_channel_dict), 'Incorrect channel'
                answer = self.test_delay
                return answer
            else:
                assert(1 == 2), 'Invalid argument'

    def delay_gen_impedance(self, *impedance):
        if self.test_flag != 'test':
            if len(impedance) == 2:
                ch = str(impedance[0])
                imp = str(impedance[1])
                if ch in self.input_output_channel_dict:
                    flag_1 = self.input_output_channel_dict[ch]
                    if imp in self.impedance_dict:
                        flag_2 = self.impedance_dict[imp]
                        self.device_write('TZ ' + str(flag_1) + ',' + str(flag_2))
                    else:
                        general.message("Incorrect impedance")
                        sys.exit()
                else:
                    general.message("Invalid channel")
                    sys.exit()    
            
            elif len(impedance) == 1:
                ch = str(impedance[0])
                if ch in self.input_output_channel_dict:
                    flag = self.input_output_channel_dict[ch]
                    raw_answer = int(self.device_query('TZ ' + str(flag)))
                    answer = cutil.search_keys_dictionary(self.impedance_dict, raw_answer)
                    return answer
                else:
                    general.message("Invalid channel")
                    sys.exit()
            else:
                general.message("Invalid argument")
                sys.exit()

        elif self.test_flag == 'test':
            if len(impedance) == 2:
                ch = str(impedance[0])
                imp = str(impedance[1])
                assert(ch in self.input_output_channel_dict), 'Invalid channel argument'
                assert(imp in self.impedance_dict), 'Invalid impedance argument'

            elif len(impedance) == 1:
                ch = str(impedance[0])
                assert(ch in self.input_output_channel_dict), 'Invalid channel argument'
                answer = self.test_impedance
                return answer

    def delay_gen_output_mode(self, *mode):
        if self.test_flag != 'test':
            if len(mode) == 2:
                ch = str(mode[0])
                md = str(mode[1])
                if ch in self.output_channel_dict:
                    flag_1 = self.output_channel_dict[ch]
                    if md in self.mode_dict:
                        flag_2 = self.mode_dict[md]
                        self.device_write('OM ' + str(flag_1) + ',' + str(flag_2))
                    else:
                        general.message("Incorrect mode")
                        sys.exit()
                else:
                    general.message("Invalid channel")
                    sys.exit()    
            
            elif len(mode) == 1:
                ch = str(mode[0])
                if ch in self.output_channel_dict:
                    flag = self.output_channel_dict[ch]
                    raw_answer = int(self.device_query('OM ' + str(flag)))
                    answer = cutil.search_keys_dictionary(self.mode_dict, raw_answer)
                    return answer
                else:
                    general.message("Invalid channel")
                    sys.exit()
            else:
                general.message("Invalid argument")
                sys.exit()

        elif self.test_flag == 'test':
            if len(mode) == 2:
                ch = str(mode[0])
                md = str(mode[1])
                assert(ch in self.output_channel_dict), 'Invalid channel argument'
                assert(md in self.mode_dict), 'Invalid mode argument'

            elif len(mode) == 1:
                ch = str(mode[0])
                assert(ch in self.output_channel_dict), 'Invalid channel argument'
                answer = self.test_mode
                return answer

    def delay_gen_amplitude_offset(self, *amplitude_offset):
        if self.test_flag != 'test':
            if len(amplutide) == 3:
                ch = str(amplutide[0])
                temp_1 = amplutide[1].split(" ")
                temp_2 = amplutide[2].split(" ")
                ampl = float(temp_1[0])
                scaling_1 = temp_1[1]
                ofst = float(temp_2[0])
                scaling_2 = temp_2[1]
                if ch in self.output_channel_dict:
                    flag_1 = self.output_channel_dict[ch]
                    if (scaling_1 in self.ampl_dict) and (scaling_2 in self.ampl_dict):
                        coef_1 = self.ampl_dict[scaling_1]
                        coef_2 = self.ampl_dict[scaling_2]
                        if int(self.device_query('OM ' + str(flag_1))) == 3:
                            general.wait('30 ms')
                            if (ampl/coef_1 + ofst/coef_2) >= self.var_ampl_min and \
                            (ampl/coef_1 + ofst/coef_2) <= self.var_ampl_max and (ampl/coef_1) >= self.var_ampl_min \
                            (ampl/coef_1) <= self.var_ampl_max and (ofst/coef_2) >= self.var_ampl_min \
                            (ofst/coef_2) <= self.var_ampl_max:
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
                if ch in self.output_channel_dict:
                    flag = self.output_channel_dict[ch]
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

        elif self.test_flag == 'test':
            if len(amplutide) == 3:
                ch = str(amplutide[0])
                temp_1 = amplutide[1].split(" ")
                temp_2 = amplutide[2].split(" ")
                ampl = float(temp_1[0])
                scaling_1 = temp_1[1]
                ofst = float(temp_2[0])
                scaling_2 = temp_2[1]
                assert(ch in self.output_channel_dict), 'Invalid channel'
                assert(scaling_1 in self.ampl_dict), 'Invalid scaling of amplitude setting'
                assert(scaling_2 in self.ampl_dict), 'Invalid scaling of offset setting'
                coef_1 = self.ampl_dict[scaling_1]
                coef_2 = self.ampl_dict[scaling_2]
                assert(ampl/coef_1 >= self.var_ampl_min and ampl/coef_1 <= self.var_ampl_max), "Incorrect amplitude range"
                assert(ofst/coef_2 >= self.var_ampl_min and ofst/coef_2 <= self.var_ampl_max), "Incorrect offset range"
                assert(ampl/coef_1 + ofst/coef_2 >= self.var_ampl_min and ampl/coef_1 + ofst/coef_2 <= self.var_ampl_max), "Incorrect range"

            elif len(amplutide) == 1:
                ch = str(amplutide[0])
                assert(ch in self.output_channel_dict), 'Invalid channel argument'
                answer = self.test_amplitude_offset
                return answer

    def delay_gen_output_polarity(self, *polarity):
        if self.test_flag != 'test':
            if len(polarity) == 2:
                ch = str(polarity[0])
                plr = str(polarity[1])
                if ch in self.output_channel_dict:
                    flag_1 = self.output_channel_dict[ch]
                    if plr in self.polarity_dict:
                        flag_2 = self.polarity_dict[plr]
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
                if ch in self.output_channel_dict:
                    flag = self.output_channel_dict[ch]
                    raw_answer = int(self.device_query('OP ' + str(flag)))
                    answer = cutil.search_keys_dictionary(self.polarity_dict, raw_answer)
                    return answer
                else:
                    general.message("Invalid channel")
                    sys.exit()
            else:
                general.message("Invalid argument")
                sys.exit()

        elif self.test_flag == 'test':
            if len(polarity) == 2:
                ch = str(polarity[0])
                plr = str(polarity[1])
                assert(ch in self.output_channel_dict), 'Invalid channel argument'
                assert(plr in self.polarity_dict), 'Invalid polarity argument'

            elif len(polarity) == 1:
                ch = str(polarity[0])
                assert(ch in self.output_channel_dict), 'Invalid channel argument'
                answer = self.test_polarity
                return answer

    # TO DO trigger commands

    def delay_gen_command(self, command):
        if self.test_flag != 'test':
            self.device_write(command)
        elif self.test_flag == 'test':
            pass

    def delay_gen_query(self, command):
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
