#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import atomize.device_modules.modbus_device as base
import atomize.device_modules.config.config_utils as cutil
import atomize.general_modules.general_functions as general

class Owen_MK110_220_4DN_4R(base.ModbusDevice):
    config_file = 'Owen_MK110_220_4DN_4R_config.ini'
    write_function_code = 16

    #### Basic interaction functions
    def __init__(self):
        # auxilary dictionaries
        self.channel_dict = {'1': 1, '2': 2, '3': 3, '4': 4, }
        self.output_state_dict = {'0': '0', '1': '1', '2': '10', '3': '100', '4': '1000',\
                                 '12': '11', '13': '101', '14': '1001', '23': '110', '24': '1010', '34': '1100', '123': '111',\
                                 '124': '1011', '134': '1101', '234': '1110', '1234': '1111', }
        self.input_state_dict = {'0': '0', '1': '1', '2': '10', '3': '100', '4': '1000',\
                                 '12': '11', '13': '101', '14': '1001', '23': '110', '24': '1010', '34': '1100', '123': '111',\
                                 '124': '1011', '134': '1101', '234': '1110', '1234': '1111', }

        # config loading, test_flag, and connection are handled by ModbusDevice
        super().__init__()

    def _init_test_values(self):
        # These values are returned by the module in the test run
        self.test_input_state = '0'
        self.test_output_state = '0'
        self.test_counter = 1

    #### device specific functions
    def discrete_io_name(self):
        if self.test_flag != 'test':
            answer = self.config['name']
            return answer
        elif self.test_flag == 'test':
            answer = self.config['name']
            return answer

    # Argument is channel; Output - counter
    def discrete_io_input_counter(self, channel):
        if self.test_flag != 'test':
            if channel in self.channel_dict:
                ch = self.channel_dict[channel]
                answer = int(self.device_read_unsigned(63 + ch, 0))
                return answer

        elif self.test_flag == 'test':
            assert(channel in self.channel_dict), f"Incorrect channel; channel: {list(self.channel_dict.keys())}"
            answer = self.test_counter
            return answer

    # Argument is channel; No output
    def discrete_io_input_counter_reset(self, channel):
        if self.test_flag != 'test':
            if channel in self.channel_dict:
                ch = self.channel_dict[channel]
                self.device_write_unsigned(63 + ch, 0, 0)

        elif self.test_flag == 'test':
            assert(channel in self.channel_dict), f"Incorrect channel; channel: {list(self.channel_dict.keys())}"

    # No argument; Output in the form '1234' that means input 1-4 are on
    def discrete_io_input_state(self):
        if self.test_flag != 'test':
            raw_answer = bin(int(self.device_read_unsigned(51, 0))).replace("0b","")
            answer = cutil.search_keys_dictionary(self.input_state_dict, raw_answer)
            return answer

        elif self.test_flag == 'test':
            answer = self.test_input_state
            return answer

    # Argument in the from '1234' that means output 1-4 will be turned on
    # Answer in the form '1234' that means output 1-4 are on
    def discrete_io_output_state(self, *state):
        if self.test_flag != 'test':
            if len(state) == 1:
                st = state[0]
                if st in self.output_state_dict:
                    flag = int(self.output_state_dict[st], 2)
                    self.device_write_unsigned(50, flag, 0)

            elif len(state) == 0:
                raw_answer = bin(int(self.device_read_unsigned(50, 0))).replace("0b","")
                answer = cutil.search_keys_dictionary(self.output_state_dict, raw_answer)
                return answer

        elif self.test_flag == 'test':
            if len(state) == 1:
                st = state[0]
                assert(st in self.output_state_dict), f"Incorrect state; channel: {list(self.output_state_dict.keys())}"
            elif len(state) == 0:
                answer = self.test_output_state
                return answer
            else:
                assert(1 == 2), f"Incorrect argument; state: {list(self.output_state_dict.keys())}"

def main():
    pass

if __name__ == "__main__":
    main()
