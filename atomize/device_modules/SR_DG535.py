#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import gc
import sys
import pyvisa
import pyqtgrpah as pg
from pyvisa.constants import StopBits, Parity
import atomize.main.local_config as lconf
import atomize.device_modules.config.config_utils as cutil
import atomize.general_modules.general_functions as general

class SR_DG535:
    #### Basic interaction functions
    def __init__(self):

        #### Inizialization
        # setting path to *.ini file
        self.path_current_directory = lconf.load_config_device()
        self.path_config_file = os.path.join(self.path_current_directory, 'SR_DG535_config.ini')

        # configuration data
        self.config = cutil.read_conf_util(self.path_config_file)
        self.specific_parameters = cutil.read_specific_parameters(self.path_config_file)

        # auxilary dictionaries
        self.delay_channel_dict = {'T0': 1, 'A': 2, 'B': 3, 'C': 5, 'D': 6,}
        self.input_output_channel_dict = {'Trigger': 0, 'T0': 1, 'A': 2, 'B': 3, 'AB': 4, 'C': 5, 'D': 6, 'CD': 7,}
        self.output_channel_dict = {'T0': 1, 'A': 2, 'B': 3, 'AB': 4, 'C': 5, 'D': 6, 'CD': 7,}
        self.time_dict = {'s': 1, 'ms': 1000, 'us': 1000000, 'ns': 1000000000, 'ps': 1000000000000,}
        self.impedance_dict = {'50': 0, '1 M': 1,}
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
                        general.message(f"No connection {self.__class__.__name__}")
                        self.status_flag = 0
                        sys.exit()
                except BrokenPipeError:
                    general.message(f"No connection {self.__class__.__name__}")
                    self.status_flag = 0
                    sys.exit()

            else:
                general.message(f"Incorrect interface setting {self.__class__.__name__}")
                self.status_flag = 0
                sys.exit()

        elif self.test_flag == 'test':
            self.test_delay = 'B + 1.0 us'
            self.test_impedance = '1 M'
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
            general.message(f"No connection {self.__class__.__name__}")
            self.status_flag = 0
            sys.exit()

    def device_query(self, command):
        if self.status_flag == 1:
            if self.config['interface'] == 'gpib':
                self.device.write(command)
                general.wait('50 ms')
                answer = self.device.read().decode()
        else:
            general.message(f"No connection {self.__class__.__name__}")
            self.status_flag = 0
            sys.exit()

    #### device specific functions
    def delay_generator_name(self):
        if self.test_flag != 'test':
            answer = self.config['name']
            return answer
        elif self.test_flag == 'test':
            answer = self.config['name']
            return answer

    def delay_generator_delay(self, *delay):
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

            elif len(delay) == 1:
                ch_1 = str(delay[0])
                if (ch_1 in self.delay_channel_dict):
                    flag_1 = self.delay_channel_dict[ch_1]
                    raw_answer = str(self.device_query('DT ' + str(flag_1))).split(',')
                    ch_answer = cutil.search_keys_dictionary(self.delay_channel_dict, int(raw_answer[0]))
                    delay_answer = float(raw_answer[1])
                    del_answer = pg.siFormat( delay_answer, suffix = 's', precision = 5, allowUnicode = False)
                    answer = str(ch_answer) + ' + ' + str(del_answer)
                    return answer

        elif self.test_flag == 'test':
            if len(delay) == 3:
                ch_1 = str(delay[0])
                ch_2 = str(delay[1])
                temp = delay[2].split(" ")
                delay = float(temp[0])
                scaling = temp[1]
                assert(ch_1 in self.delay_channel_dict), f"Incorrect channel 1; channel: {list(self.delay_channel_dict.keys())}"
                assert(ch_2 in self.delay_channel_dict), f"Incorrect channel 2; channel: {list(self.delay_channel_dict.keys())}"
                assert(scaling in self.time_dict), f"Invalid argument; channel 1, 2: {list(self.delay_channel_dict.keys())}; delay: int + [' s', ' ms', ' us', ' ns', ' ps']"
                coef = self.time_dict[scaling]
                min_d = pg.siFormat( self.delay_min, suffix = 's', precision = 3, allowUnicode = False)
                max_d = pg.siFormat( self.delay_max, suffix = 's', precision = 3, allowUnicode = False)
                assert(delay/coef >= self.delay_min and delay/coef <= self.delay_max), \
                    f"Incorrect delay. The available range is from {min_d} to {max_d}"

            elif len(delay) == 1:
                ch_1 = str(delay[0])
                assert(ch_1 in self.delay_channel_dict), f"Incorrect channel 1; channel: {list(self.delay_channel_dict.keys())}"
                answer = self.test_delay
                return answer
            else:
                assert(1 == 2), f"Invalid argument; channel 1, 2: {list(self.delay_channel_dict.keys())}; delay: int + [' s', ' ms', ' us', ' ns', ' ps']"

    def delay_generator_impedance(self, *impedance):
        if self.test_flag != 'test':
            if len(impedance) == 2:
                ch = str(impedance[0])
                imp = str(impedance[1])
                if ch in self.input_output_channel_dict:
                    flag_1 = self.input_output_channel_dict[ch]
                    if imp in self.impedance_dict:
                        flag_2 = self.impedance_dict[imp]
                        self.device_write('TZ ' + str(flag_1) + ',' + str(flag_2))
            
            elif len(impedance) == 1:
                ch = str(impedance[0])
                if ch in self.input_output_channel_dict:
                    flag = self.input_output_channel_dict[ch]
                    raw_answer = int(self.device_query('TZ ' + str(flag)))
                    answer = cutil.search_keys_dictionary(self.impedance_dict, raw_answer)
                    return answer

        elif self.test_flag == 'test':
            if len(impedance) == 2:
                ch = str(impedance[0])
                imp = str(impedance[1])
                assert(ch in self.input_output_channel_dict), f"Incorrect channel; channel: {list(self.input_output_channel_dict.keys())}"
                assert(imp in self.impedance_dict), f'Invalid impedance; impedance: {list(self.impedance_dict.keys())}'

            elif len(impedance) == 1:
                ch = str(impedance[0])
                assert(ch in self.input_output_channel_dict), f"Incorrect channel; channel: {list(self.input_output_channel_dict.keys())}"
                answer = self.test_impedance
                return answer
            else:
                assert(1 == 2), f"Invalid argument; channel: {list(self.input_output_channel_dict.keys())}; impedance: {list(self.impedance_dict.keys())}"

    def delay_generator_output_mode(self, *mode):
        if self.test_flag != 'test':
            if len(mode) == 2:
                ch = str(mode[0])
                md = str(mode[1])
                if ch in self.output_channel_dict:
                    flag_1 = self.output_channel_dict[ch]
                    if md in self.mode_dict:
                        flag_2 = self.mode_dict[md]
                        self.device_write('OM ' + str(flag_1) + ',' + str(flag_2))
            
            elif len(mode) == 1:
                ch = str(mode[0])
                if ch in self.output_channel_dict:
                    flag = self.output_channel_dict[ch]
                    raw_answer = int(self.device_query('OM ' + str(flag)))
                    answer = cutil.search_keys_dictionary(self.mode_dict, raw_answer)
                    return answer

        elif self.test_flag == 'test':
            if len(mode) == 2:
                ch = str(mode[0])
                md = str(mode[1])
                assert(ch in self.output_channel_dict), f"Incorrect channel; channel: {list(self.output_channel_dict.keys())}"
                assert(md in self.mode_dict), f"Invalid argument; channel: {list(self.output_channel_dict.keys())}; mode: {list(self.mode_dict.keys())}"

            elif len(mode) == 1:
                ch = str(mode[0])
                assert(ch in self.output_channel_dict), f"Incorrect channel; channel: {list(self.output_channel_dict.keys())}"
                answer = self.test_mode
                return answer
            else:
                assert(1 == 2), f"Invalid argument; channel: {list(self.output_channel_dict.keys())}; mode: {list(self.mode_dict.keys())}"

    def delay_generator_amplitude_offset(self, *amplitude_offset):
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

            elif len(amplutide) == 1:
                ch = str(amplutide[0])
                if ch in self.output_channel_dict:
                    flag = self.output_channel_dict[ch]
                    answer_1 = float(self.device_query('OA ' + str(flag)))
                    answer_2 = float(self.device_query('OO ' + str(flag)))
                    answer = 'Amplitude: ' + str(answer_1) + ' V; ' + 'Offset: ' + str(answer_2) + ' V'
                    return answer

        elif self.test_flag == 'test':
            if len(amplutide) == 3:
                ch = str(amplutide[0])
                temp_1 = amplutide[1].split(" ")
                temp_2 = amplutide[2].split(" ")
                ampl = float(temp_1[0])
                scaling_1 = temp_1[1]
                ofst = float(temp_2[0])
                scaling_2 = temp_2[1]
                assert(ch in self.output_channel_dict), f"Incorrect channel; channel: {list(self.output_channel_dict.keys())}"
                assert(scaling_1 in self.ampl_dict),\
                    f"Invalid argument; channel: {list(self.output_channel_dict.keys())}; amplutide: float + [' mV', ' V']; offset: float + [' mV', ' V']"
                assert(scaling_2 in self.ampl_dict),\
                    f"Invalid argument; channel: {list(self.output_channel_dict.keys())}; amplutide: float + [' mV', ' V']; offset: float + [' mV', ' V']"
                coef_1 = self.ampl_dict[scaling_1]
                coef_2 = self.ampl_dict[scaling_2]
                min_a = pg.siFormat( self.var_ampl_min, suffix = 'V', precision = 3, allowUnicode = False)
                max_a = pg.siFormat( self.var_ampl_max, suffix = 'V', precision = 3, allowUnicode = False)
                assert(ampl/coef_1 >= self.var_ampl_min and ampl/coef_1 <= self.var_ampl_max), f"Incorrect amplitude. The available rande is from {min_a} to {max_a}"
                assert(ofst/coef_2 >= self.var_ampl_min and ofst/coef_2 <= self.var_ampl_max), f"Incorrect offset. The available rande is from {min_a} to {max_a}"
                assert(ampl/coef_1 + ofst/coef_2 >= self.var_ampl_min and ampl/coef_1 + ofst/coef_2 <= self.var_ampl_max), \
                    f"Incorrect range. The available rande is from {min_a} to {max_a}"

            elif len(amplutide) == 1:
                ch = str(amplutide[0])
                assert(ch in self.output_channel_dict), f"Incorrect channel; channel: {list(self.output_channel_dict.keys())}"
                answer = self.test_amplitude_offset
                return answer
            else:
                assert(1 == 2),\
                    f"Invalid argument; channel: {list(self.output_channel_dict.keys())}; amplutide: float + [' mV', ' V']; offset: float + [' mV', ' V']"

    def delay_generator_output_polarity(self, *polarity):
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
            
            elif len(polarity) == 1:
                ch = str(polarity[0])
                if ch in self.output_channel_dict:
                    flag = self.output_channel_dict[ch]
                    raw_answer = int(self.device_query('OP ' + str(flag)))
                    answer = cutil.search_keys_dictionary(self.polarity_dict, raw_answer)
                    return answer

        elif self.test_flag == 'test':
            if len(polarity) == 2:
                ch = str(polarity[0])
                plr = str(polarity[1])
                assert(ch in self.output_channel_dict), f"Incorrect channel; channel: {list(self.output_channel_dict.keys())}"
                assert(plr in self.polarity_dict), f"Incorrect polarity; polarity: {list(self.polarity_dict.keys())}"

            elif len(polarity) == 1:
                ch = str(polarity[0])
                assert(ch in self.output_channel_dict), f"Incorrect channel; channel: {list(self.output_channel_dict.keys())}"
                answer = self.test_polarity
                return answer
            else:
                assert(1 == 2), f"Invalid argument; channel: {list(self.output_channel_dict.keys())}; polarity: {list(self.polarity_dict.keys())}"

    # TO DO trigger commands

    def delay_generator_command(self, command):
        if self.test_flag != 'test':
            self.device_write(command)
        elif self.test_flag == 'test':
            pass

    def delay_generator_query(self, command):
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
