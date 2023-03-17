#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import gc
import sys
import pyvisa
from pyvisa.constants import StopBits, Parity
import atomize.device_modules.config.config_utils as cutil
import atomize.general_modules.general_functions as general

class ECC_15K:
    #### Basic interaction functions
    def __init__(self):

        #### Inizialization
        # setting path to *.ini file
        self.path_current_directory = os.path.dirname(__file__)
        self.path_config_file = os.path.join(self.path_current_directory, 'config','ECC_15K_config.ini')

        # configuration data
        self.config = cutil.read_conf_util(self.path_config_file)
        self.specific_parameters = cutil.read_specific_parameters(self.path_config_file)

        # Ramges and limits
        self.min_freq = 10 # MHz
        self.max_freq = 15000 # MHz
        self.min_power_level = 0
        self.max_power_level = 15

        self.state_list = {'On', 'Off'}
        self.frequency_dict = {'GHz': 1000000000, 'MHz': 1000000, 'kHz': 1000, 'Hz': 1, }
        self.freq = 1000 # MHz
        self.power_level = 0
        self.state = 'Off'

        if len(sys.argv) > 1:
            self.test_flag = sys.argv[1]
        else:
            self.test_flag = 'None'

        if self.test_flag != 'test':
            if self.config['interface'] == 'rs232':
                try:
                    self.status_flag = 1
                    rm = pyvisa.ResourceManager()
                    self.device = rm.open_resource(self.config['serial_address'],
                    write_termination=self.config['write_termination'], read_termination=self.config['read_termination'], \
                    baud_rate=self.config['baudrate'], data_bits=self.config['databits'], parity=self.config['parity'], \
                    stop_bits=self.config['stopbits'])
                    self.device.timeout = self.config['timeout'] # in ms
                
                    try:
                        # test should be here
                        self.status_flag = 1
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
                        sys.exit()
                except BrokenPipeError:
                    general.message("No connection")
                    self.status_flag = 0
                    sys.exit()

        # Test run parameters
        # These values are returned by the modules in the test run 
        elif self.test_flag == 'test':
            self.test_freq = 1000
            self.test_power_level = 15
            self.test_state = 'Off'

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
            self.status_flag = 0
            general.message("No Connection")
            sys.exit()

    def device_query(self, command):
        if self.status_flag == 1:
            command = str(command)
            answer = self.device.query(command)
            return answer
        else:
            self.status_flag = 0
            general.message("No Connection")
            sys.exit()

    #### device specific functions
    def synthetizer_name(self):
        if self.test_flag != 'test':
            answer = self.device_query('*IDN?')
            answer = answer.split('\n')[0]
            return answer
        elif self.test_flag == 'test':
            answer = self.config['name']
            return answer

    def synthetizer_frequency(self, *freq):
        """
        Function for changing the frequency.
        The frequency is set in MHz in the range of 10 MHz to 15000 MHz in 1 MHz step.
        The ECC 15K supports a step of 0.005 Hz.
        """
        if self.test_flag != 'test':
            if len(freq) == 1:
                freq = int( freq[0] )
                if freq <= self.max_freq and freq >= self.min_freq:
                    self.device_write(f':FREQ {freq} MHz')
                    general.wait('50 ms')
                    self.freq = freq
                else:
                    general.message('Incorrect frequency')
                    sys.exit()
            elif len(freq) == 0:
                answer = int( float( self.device_query(':FREQ?') ) / 1000000)
                general.wait('50 ms')
                return f'{answer} MHz'

        elif self.test_flag == 'test':
            if len(freq) == 1:
                freq = int( freq[0] )
                assert(freq <= self.max_freq and freq >= self.min_freq), 'Incorrect frequency'
                self.freq = freq
            elif len(freq) == 0:
                answer = self.test_freq
                return answer

    def synthetizer_state(self, *state):
        """
        Function for changing the state of the power output.
        Two states are available: 'On'; 'Off'
        """
        if self.test_flag != 'test':
            if len(state) == 1:
                state = str( state[0] )
                self.device_write(f'OUTPut {state}')
                general.wait('50 ms')
                self.state = state

            elif len(state) == 0:
                raw_answer = int( self.device_query('OUTP?') )
                general.wait('50 ms')
                if raw_answer == 1:
                    return 'On'
                elif raw_answer == 0:
                    return 'Off'

        elif self.test_flag == 'test':
            if len(state) == 1:
                state = str( state[0] )
                assert(state in self.state_list), 'Incorrect state'
                self.state = state
            elif len(state) == 0:
                answer = self.test_state
                return answer

    def synthetizer_power(self, *level):
        """
        Function for changing the power level.
        The power level is set in arb. u. in the range of 0 to 15 in 1 arb. u. step.
        The value 15 corresponds to the maximum power level.
        """
        if self.test_flag != 'test':
            if len(level) == 1:
                level = int( level[0] )
                if level <= self.max_power_level and level >= self.min_power_level:
                    self.device_write(f':POW {level}')
                    general.wait('50 ms')
                    self.power_level = level
                else:
                    general.message('Incorrect power level range')
                    sys.exit()
            elif len(level) == 0:
                answer = int( float( self.device_query(':POW?') ) )
                general.wait('50 ms')
                return answer
            else:
                send.message("Invalid argument")
                sys.exit()

        elif self.test_flag == 'test':
            if len(level) == 1:
                level = int( level[0] )
                assert(level <= self.max_power_level and level >= self.min_power_level), 'Incorrect power level range'
                self.power_level = level
            elif len(level) == 0:
                answer = self.test_power_level
                return answer
            else:
                assert(1 == 2), 'Invalid argument'

    def synthetizer_command(self, command):
        if self.test_flag != 'test':
            command = str(command)
            self.device_write(command)

        elif self.test_flag == 'test':
            pass

    def synthetizer_query(self, command):
        if self.test_flag != 'test':
            command = str(command)
            return self.device_query(command)

        elif self.test_flag == 'test':
            return None

def main():
    pass

if __name__ == "__main__":
    main()