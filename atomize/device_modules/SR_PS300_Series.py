#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import gc
import sys
import pyvisa
from pyvisa.constants import StopBits, Parity
import atomize.main.local_config as lconf
import atomize.device_modules.config.config_utils as cutil
import atomize.general_modules.general_functions as general

class SR_PS300_Series:
    #### Basic interaction functions
    def __init__(self):

        #### Inizialization
        # setting path to *.ini file
        self.path_current_directory = lconf.load_config_device()
        self.path_config_file = os.path.join(self.path_current_directory, 'SR_PS300_Series_config.ini')

        # configuration data
        self.config = cutil.read_conf_util(self.path_config_file)
        self.specific_parameters = cutil.read_specific_parameters(self.path_config_file)

        # auxilary dictionaries
        self.channel_dict = {'CH1': 1, }
        self.voltage_dict = {'V': 1, 'kV': 0.001, }
        self.current_dict = {'uA': 1000000, 'mA': 1000, }
        self.state_dict = {'Off': 'HVOF', 'On': 'HVON', }
        self.rear_mode_dict = {'Front': 0, 'Rear': 1, }

        # Ranges and limits
        self.voltage_min = float(self.specific_parameters['voltage_min'])
        self.voltage_max = float(self.specific_parameters['voltage_max'])
        self.current_max = float(self.specific_parameters['current_max'])
        self.rs232_available = str(self.specific_parameters['rs232'])

        # Test run parameters
        # These values are returned by the modules in the test run 
        if len(sys.argv) > 1:
            self.test_flag = sys.argv[1]
        else:
            self.test_flag = 'None'

        if self.test_flag != 'test':
            if self.config['interface'] == 'rs232' and self.rs232_available == 'yes':
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

                    except pyvisa.VisaIOError:
                        self.status_flag = 0
                        general.message(f"No connection {self.__class__.__name__}")
                        sys.exit()
                    except BrokenPipeError:
                        general.message(f"No connection {self.__class__.__name__}")
                        self.status_flag = 0
                        sys.exit()
                except pyvisa.VisaIOError:
                    general.message(f"No connection {self.__class__.__name__}")
                    self.status_flag = 0
                    sys.exit()
                except BrokenPipeError:
                    general.message(f"No connection {self.__class__.__name__}")
                    self.status_flag = 0
                    sys.exit()

            elif self.config['interface'] == 'rs232' and self.rs232_available == 'no':
                general.message('RS-232 is not available on this device')
                sys.exit()

            elif self.config['interface'] == 'gpib':
                try:
                    import Gpib
                    self.status_flag = 1
                    self.device = Gpib.Gpib(self.config['board_address'], self.config['gpib_address'], \
                                            timeout = self.config['timeout'])
                    try:
                        # test should be here
                        self.device_write('*CLS')

                    except BrokenPipeError:
                        general.message(f"No connection {self.__class__.__name__}")
                        self.status_flag = 0
                        sys.exit()
                except BrokenPipeError:
                    general.message(f"No connection {self.__class__.__name__}")
                    self.status_flag = 0
                    sys.exit()

        elif self.test_flag == 'test':
            self.test_measure = [100, 0.05]
            self.test_voltage = 100.
            self.test_voltage_limit = 110.
            self.test_current_limit = 0.01
            self.test_state = 'Off'
            self.test_rear_mode = 'Front'

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
                return answer
            elif self.config['interface'] == 'rs232':
                answer = self.device.query(command)
                return answer
        else:
            general.message(f"No connection {self.__class__.__name__}")
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
                    if scaling in self.voltage_dict:
                        coef = self.voltage_dict[scaling]
                        smod_check = int(self.device_query('SMOD?'))
                        general.wait('20 ms')
                        if smod_check == 0:
                            if self.voltage_min > 0 and self.voltage_max > 0:
                                if vtg/coef >= self.voltage_min and vtg/coef <= self.voltage_max:
                                    limit_check = float(self.device_query('VLIM?'))
                                    general.wait('20 ms')
                                    if vtg/coef <= limit_check:
                                        self.device_write('VSET ' + str(vtg/coef))
                                    else:
                                        general.message("Voltage setting is higher than voltage limit setting")
                                else:
                                    general.message("Incorrect voltage range")
                                    sys.exit()
                            elif self.voltage_min < 0 and self.voltage_max < 0:
                                if vtg/coef <= self.voltage_min and vtg/coef >= self.voltage_max:
                                    limit_check = float(self.device_query('VLIM?'))
                                    general.wait('20 ms')
                                    if vtg/coef >= limit_check:
                                        self.device_write('VSET ' + str(vtg/coef))
                                    else:
                                        general.message("Voltage setting is lower than voltage limit setting")
                                else:
                                    general.message("Incorrect voltage range")
                                    sys.exit()
                            else:
                                general.message("Incorrect max/min voltage in the module")
                                sys.exit()
                        elif smod_check == 1:
                            general.message("Voltage setting is controlled by the rear-panel HVSET input")
                            sys.exit()
                        else:
                            general.message("Incorrect rear_mode setting")
                            sys.exit()
                    else:
                        general.message("Incorrect voltage scaling")
                        sys.exit()
                else:
                    general.message("Incorrect channel")
                    sys.exit()

            elif len(voltage) == 1:
                ch = str(voltage[0])
                if ch in self.channel_dict:
                    smod_check = int(self.device_query('SMOD?'))
                    general.wait('20 ms')
                    if smod_check == 0:
                        answer = float(self.device_query('VSET?'))
                        return answer
                    elif smod_check == 1:
                        general.message("Voltage setting is controlled by the rear-panel HVSET input")
                        answer = float(self.device_query('VSET?'))
                        return answer
                    else:
                        general.message("Incorrect SMOD setting")
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
                assert(scaling in self.voltage_dict), 'Invalid scaling argument'
                if self.voltage_min > 0 and self.voltage_max > 0:
                    assert(vtg/coef >= self.voltage_min and vtg/coef <= self.voltage_max), "Incorrect voltage range"
                elif self.voltage_min < 0 and self.voltage_max < 0:
                    assert(vtg/coef <= self.voltage_min and vtg/coef >= self.voltage_max), "Incorrect voltage range"
                else:
                    assert(1 == 2), "Incorrect max/min voltage in the module"
            elif len(voltage) == 1:
                ch = str(voltage[0])
                assert(ch in self.channel_dict), 'Invalid channel argument'
                answer = self.test_voltage
                return answer

    def power_supply_overvoltage(self, *voltage):
        if self.test_flag != 'test':
            if len(voltage) == 2:
                ch = str(voltage[0])
                temp = voltage[1].split(" ")
                vtg = float(temp[0])
                scaling = temp[1]

                if ch in self.channel_dict:
                    if scaling in self.voltage_dict:
                        coef = self.voltage_dict[scaling]
                        if self.voltage_min > 0 and self.voltage_max > 0:
                            if vtg/coef >= self.voltage_min and vtg/coef <= self.voltage_max:
                                self.device_write('VLIM ' + str(vtg/coef))
                            else:
                                general.message("Incorrect voltage limit range")
                                sys.exit()
                        elif self.voltage_min < 0 and self.voltage_max < 0:
                            if vtg/coef <= self.voltage_min and vtg/coef >= self.voltage_max:
                                self.device_write('VLIM ' + str(vtg/coef))
                            else:
                                general.message("Incorrect voltage limit range")
                                sys.exit()
                        else:
                            general.message("Incorrect max/min voltage in the module")
                            sys.exit()
                    else:
                        general.message("Incorrect overvoltage scaling")
                        sys.exit()
                else:
                    general.message("Invalid channel")
                    sys.exit()    
            
            elif len(voltage) == 1:
                ch = str(voltage[0])
                if ch in self.channel_dict:
                    answer = float(self.device_query('VLIM?'))
                    return answer
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
                assert(scaling in self.voltage_dict), 'Invalid scaling argument'
                if self.voltage_min > 0 and self.voltage_max > 0:
                    assert(vtg/coef >= self.voltage_min and vtg/coef <= self.voltage_max), "Incorrect voltage range"
                elif self.voltage_min < 0 and self.voltage_max < 0:
                    assert(vtg/coef <= self.voltage_min and vtg/coef >= self.voltage_max), "Incorrect voltage range"
                else:
                    assert(1 == 2), "Incorrect max/min voltage in the module"
            elif len(voltage) == 1:
                ch = str(voltage[0])
                assert(ch in self.channel_dict), 'Invalid channel argument'
                answer = self.test_voltage_limit
                return answer

    def power_supply_overcurrent(self, *current):
        if self.test_flag != 'test':
            if len(current) == 2:
                ch = str(current[0])
                temp = current[1].split(" ")
                curr = float(temp[0])
                scaling = temp[1]

                if ch in self.channel_dict:
                    if scaling in self.current_dict:
                        coef = self.current_dict[scaling]
                        if curr/coef <= self.current_max*1.05:
                            self.device_write('ILIM ' + str(curr/coef))
                        else:
                            general.message("Incorrect overcurrent range")
                            sys.exit()                           
                    else:
                        general.message("Incorrect overcurrent scaling")
                        sys.exit()
                else:
                    general.message("Invalid channel")
                    sys.exit()

            elif len(current) == 1:
                ch = str(current[0])
                if ch in self.channel_dict:
                    answer = float(self.device_query('ILIM?'))*1000000
                    return answer
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
                assert(scaling in self.current_dict), 'Invalid overcurrent scaling'
                assert(curr/coef <= self.current_max*1.05), "Incorrect overcurrent range"
            elif len(current) == 1:
                ch = str(current[0])
                assert(ch in self.channel_dict), 'Invalid channel argument'
                answer = self.test_current_limit
                return answer

    def power_supply_channel_state(self, *state):
        if self.test_flag != 'test':
            if len(state) == 2:
                ch = str(state[0])
                st = str(state[1])
                if ch in self.channel_dict:
                    if st in self.state_dict:
                        self.device_write(str(self.state_dict[st]))
                    else:
                        general.message("Invalid state argument. Function cannot be queried")
                        sys.exit()
                else:
                    general.message("Invalid channel")
                    sys.exit()

            elif len(state) == 1:
                general.message("Invalid argument")
                sys.exit()
            else:
                general.message("Invalid argument")
                sys.exit()

        elif self.test_flag == 'test':
            if len(state) == 2:
                ch = str(state[0])
                st = str(state[1])
                assert(ch in self.channel_dict), 'Invalid channel argument'
                assert(st in self.state_dict), 'Invalid state argument'
            elif len(state) == 1:
                ch = str(state[0])
                assert(ch in self.channel_dict), 'Invalid channel argument'
                assert(1 == 2), 'This function cannot be queried'

    def power_supply_measure(self, channel):
        if self.test_flag != 'test':
            ch = str(channel)
            if ch in self.channel_dict:
                raw_answer_1 = self.device_query('VOUT?')
                general.wait('20 ms')
                raw_answer_2 = self.device_query('IOUT?')
                answer = [float(raw_answer_1), float(raw_answer_2)]
                return answer
            else:
                general.message('Invalid channel')
                sys.exit()

        elif self.test_flag == 'test':
            ch = str(channel)
            assert(ch in self.channel_dict), 'Invalid channel'
            answer = self.test_measure
            return answer

    def power_supply_rear_mode(self, *mode):
        if self.test_flag != 'test':
            if len(mode) == 1:
                md = str(mode[0])
                if md in self.rear_mode_dict:
                    flag = self.rear_mode_dict[md]
                    self.device_write('SMOD ' + str(flag))
                else:
                    general.message('Incorrect rear mode')
                    sys.exit()
            elif len(mode) == 0:
                raw_answer = int(self.device_query('SMOD?'))
                answer = cutil.search_keys_dictionary(self.rear_mode_dict, raw_answer)
                return answer
            else:
                general.message("Invalid argument")
                sys.exit()

        elif self.test_flag == 'test':
            if len(mode) == 1:
                md = str(mode[0])
                assert(md in self.rear_mode_dict), "Incorrect rear mode"
            elif len(mode) == 0:
                answer = self.test_rear_mode
                return answer
            else:
                assert(1 == 2), "Invalid argument"

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
