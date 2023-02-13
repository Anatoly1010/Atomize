#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import gc
import sys
import atomize.device_modules.config.config_utils as cutil
import atomize.general_modules.general_functions as general

class Agilent_5343a:
    #### Basic interaction functions
    def __init__(self):

        #### Inizialization
        # setting path to *.ini file
        self.path_current_directory = os.path.dirname(__file__)
        self.path_config_file = os.path.join(self.path_current_directory, 'config','Agilent_5343a_config.ini')

        # configuration data
        self.config = cutil.read_conf_util(self.path_config_file)
        self.specific_parameters = cutil.read_specific_parameters(self.path_config_file)

        # auxilary dictionaries
        self.digits = 9
        
        # Ranges and limits
        self.min_digits = 3
        self.min_digits = 9

        # Test run parameters
        self.test_digits = 9
        self.test_frequency = 10000

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
                    # gpib timeout:
                    # 0 - never
                    # 1 - 10 us
                    # 2 - 30 us
                    # 3 - 100 us
                    # 4 - 300 us
                    # 5 - 1 ms
                    # 6 - 3 ms
                    # 7 - 10 ms
                    # 8 - 30 ms
                    # 9 - 100 ms
                    # 10 - 300 ms
                    # 11 - 1 s
                    # 12 - 3 s
                    # 13 - 10 s
                    # 14 - 30 s
                    # 15 - 100 s
                    # 16 - 300 s
                    # 17 - 1000 s
                    try:
                        # test should be here
                        
                        """
                        Tell device to use internal sample rate and to output data only if
                        addressed as talker (don't lock the keyboard, the user is supposed
                        to do settings at the front panel)
                        """
                        self.device_write('ST1')
                        self.device_write('T2')

                        # resolution SR3 - 1 Hz; SR9 - 1 MHz
                        self.device_write('SR3')
                        self.status_flag = 1

                    except BrokenPipeError:
                        general.message("No connection")
                        self.status_flag = 0
                        sys.exit()
                except BrokenPipeError:
                    general.message("No connection")
                    self.status_flag = 0
                    sys.exit()
            else:
                general.message("Such interface: " + str(self.config['interface']) + " is not available")
                self.status_flag = 0
                sys.exit()      
            
        elif self.test_flag == 'test':
            self.test_frequency = 10000


    def close_connection(self):
        if self.test_flag != 'test':
            self.status_flag = 0;
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
                return answer
            else:
                general.message('Incorrect interface setting')
                self.status_flag = 0
        else:
            general.message("No Connection")
            self.status_flag = 0
            sys.exit()

    def device_read(self):
        if self.status_flag == 1:
            if self.config['interface'] == 'gpib':
                # read first 22 bytes
                raw_answer = self.device.read(22).decode()
                try:
                    answer = float( raw_answer[4:19] ) * 10 ** 6
                    #' F  09114.636333E+06\r\n'
                except ValueError:
                    answer = 0.
                
                return answer
            else:
                general.message('Incorrect interface setting')
                self.status_flag = 0
        else:
            general.message("No Connection")
            self.status_flag = 0
            sys.exit()

    #### Device specific functions
    def freq_counter_name(self):
        answer = self.config['name']
        return answer

    def freq_counter_frequency(self, channel):
        if self.test_flag != 'test':
            if channel == 'CH1':
                answer = float(self.device_read())
                return answer
            else:
                general.message('Invalid argument')
                sys.exit()

        elif self.test_flag == 'test':
            assert( channel == 'CH1' ), 'Invalid channel'
            answer = self.test_frequency
            return answer

    def freq_counter_digits(self, *digits):
        if self.test_flag != 'test':
            if  len(digits) == 1:
                val = int(digits[0])
                if val >= self.min_digits and val <= self.max_digits:
                    self.device_write("SR" + str(12 - val))
                    self.digits = 12 - val
                else:
                    general.message("Invalid amount of digits")
                    sys.exit()
            elif len(digits) == 0:
                answer = self.digits
                return answer
            else:
                general.message("Invalid argument")
                sys.exit()

        elif self.test_flag == 'test':
            if  len(digits) == 1:
                val = int(digits[0])
                assert(val >= self.min_digits and val <= self.max_digits), "Invalid amount of digits"
                self.test_digits = 12 - val
            elif len(digits) == 0:
                answer = self.test_digits
                return answer
            else:
                assert(1 == 2), "Invalid argument"

    def freq_counter_command(self, command):
        if self.test_flag != 'test':
            self.device_write(command)
        elif self.test_flag == 'test':
            pass

    def freq_counter_query(self, command):
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