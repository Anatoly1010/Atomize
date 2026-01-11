#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import gc
import sys
import time
import serial
import minimalmodbus
import atomize.main.local_config as lconf
import atomize.device_modules.config.config_utils as cutil
import atomize.general_modules.general_functions as general

class Termodat_11M6:
    #### Basic interaction functions
    def __init__(self):

        #### Inizialization
        # setting path to *.ini file
        self.path_current_directory = lconf.load_config_device()
        self.path_config_file = os.path.join(self.path_current_directory, 'Termodat_11M6_config.ini')

        # configuration data
        self.config = cutil.read_conf_util(self.path_config_file)
        self.modbus_parameters = cutil.read_modbus_parameters(self.path_config_file)
        self.specific_parameters = cutil.read_specific_parameters(self.path_config_file)

        # auxilary dictionaries
        self.channel_dict = {'1': 1, '2': 2, '3': 3, '4': 4, }
        self.state_dict = {'On': 1, 'Off': 0, }

        # Ranges and limits
        self.channels = int(self.specific_parameters['channels'])
        self.temperature_max = 750
        self.temperature_min = 0.3
        self.proportional_min = 0.1
        self.proportional_max = 2000
        self.derivative_min = 0.0
        self.derivative_max = 999.9
        self.integral_min = 0
        self.integral_max = 9999

        # Test run parameters
        # These values are returned by the modules in the test run 
        if len(sys.argv) > 1:
            self.test_flag = sys.argv[1]
        else:
            self.test_flag = 'None'

        if self.test_flag != 'test':
            if self.config['interface'] == 'rs485':
                try:
                    self.status_flag = 1
                    self.device = minimalmodbus.Instrument(self.config['serial_address'], self.modbus_parameters[1])
                    #self.device.mode = minimalmodbus.MODE_ASCII
                    self.device.mode = self.modbus_parameters[0]
                    #check there
                    self.device.serial.baudrate = self.config['baudrate']
                    self.device.serial.bytesize = self.config['databits']
                    self.device.serial.parity = self.config['parity']
                    #check there
                    self.device.serial.stopbits = self.config['stopbits']
                    self.device.serial.timeout = self.config['timeout'] / 1000
                    try:
                        pass
                        # test should be here
                        #self.device_write('*CLS')

                    except serial.serialutil.SerialException:
                        general.message(f"No connection {self.__class__.__name__}")
                        self.status_flag = 0
                        sys.exit()
                except serial.serialutil.SerialException:
                    general.message(f"No connection {self.__class__.__name__}")
                    self.status_flag = 0
                    sys.exit()

            else:
                general.message(f"Incorrect interface setting {self.__class__.__name__}")
                self.status_flag = 0
                sys.exit()

        elif self.test_flag == 'test':
            self.test_temperature = 300
            self.test_set_point = 273
            self.test_power = 0
            self.test_loop_state = 'Off'
            self.test_proportional = 70
            self.test_derivative = 50
            self.test_integral = 600

    def close_connection(self):
        if self.test_flag != 'test':
            self.status_flag = 0
            gc.collect()
        elif self.test_flag == 'test':
            pass

    def device_write_signed(self, register, value, decimals):
        if self.status_flag == 1:
            self.device.write_register(register, value, decimals, functioncode = 6, signed = True)
        else:
            general.message(f"No connection {self.__class__.__name__}")
            self.status_flag = 0
            sys.exit()

    def device_write_unsigned(self, register, value, decimals):
        if self.status_flag == 1:
            self.device.write_register(register, value, decimals, functioncode = 6, signed = False)
        else:
            general.message(f"No connection {self.__class__.__name__}")
            self.status_flag = 0
            sys.exit()

    def device_read_signed(self, register, decimals):
        if self.status_flag == 1:
            answer = self.device.read_register(register, decimals, signed = True)
            time.sleep(0.01)
            return answer
        else:
            general.message(f"No connection {self.__class__.__name__}")
            self.status_flag = 0
            sys.exit()

    def device_read_unsigned(self, register, decimals):
        if self.status_flag == 1:
            answer = self.device.read_register(register, decimals, signed = False)
            return answer
        else:
            general.message(f"No connection {self.__class__.__name__}")
            self.status_flag = 0
            sys.exit()

    #### device specific functions
    def tc_name(self):
        if self.test_flag != 'test':
            answer = self.config['name']
            return answer
        elif self.test_flag == 'test':
            answer = self.config['name']
            return answer

    def tc_temperature(self, channel):
        if self.test_flag != 'test':
            if channel == '1':
                answer = round(float(self.device_read_signed(368, 1)) + 273.16, 1)
                return answer
            elif channel == '2':
                answer = round(float(self.device_read_signed(1392, 1)) + 273.16, 1)
                return answer
            elif channel == '3':
                answer = round(float(self.device_read_signed(2416, 1)) + 273.16, 1)
                return answer
            elif channel == '4':
                answer = round(float(self.device_read_signed(3440, 1)) + 273.16, 1)
                return answer
        
        elif self.test_flag == 'test':
            assert(channel == '1' or channel == '2' or channel == '3' or channel == '4'), "Incorrect channel; channel: ['1', '2', '3', '4']"
            answer = self.test_temperature
            return answer

    def tc_setpoint(self, *temperature):
        if self.test_flag != 'test':
            if len(temperature) == 2:
                ch = str(temperature[0])
                temp = round(float(temperature[1]), 1)
                if temp <= self.temperature_max and temp >= self.temperature_min:
                    if ch in self.channel_dict:
                        flag = self.channel_dict[ch]
                        if flag <= self.channels:
                            if ch == '1':
                                self.device_write_signed(369, temp - 273.16, 1)
                            elif ch == '2':
                                self.device_write_signed(1393, temp - 273.16, 1)
                            elif ch == '3':
                                self.device_write_signed(2417, temp - 273.16, 1)
                            elif ch == '4':
                                self.device_write_signed(3441, temp - 273.16, 1)
            elif len(temperature) == 1:
                ch = str(temperature[0])
                if ch in self.channel_dict:
                    flag = self.channel_dict[ch]
                    if flag <= self.channels:
                        if ch == '1':
                            answer = round(float(self.device_read_signed(369, 1)) + 273.16, 1)
                            return answer
                        elif ch == '2':
                            answer = round(float(self.device_read_signed(1393, 1)) + 273.16, 1)
                            return answer
                        elif ch == '3':
                            answer = round(float(self.device_read_signed(2417, 1)) + 273.16, 1)
                            return answer
                        elif ch == '4':
                            answer = round(float(self.device_read_signed(3441, 1)) + 273.16, 1)
                            return answer

        elif self.test_flag == 'test':
            if len(temperature) == 2:
                ch = str(temperature[0])
                temp = float(temperature[1])
                assert(ch in self.channel_dict), "Incorrect channel; channel: ['1', '2', '3', '4']"
                flag = self.channel_dict[ch]
                assert(flag <= self.channels), "Incorrect channel; channel: ['1', '2', '3', '4']"
                assert(temp <= self.temperature_max and temp >= self.temperature_min),\
                    f'Incorrect set point temperature is reached. The available range is from {self.temperature_min} to {self.temperature_max}'
            elif len(temperature) == 1:
                ch = str(temperature[0])
                assert(ch in self.channel_dict), "Incorrect channel; channel: ['1', '2', '3', '4']"
                flag = self.channel_dict[ch]
                assert(flag <= self.channels), "Incorrect channel; channel: ['1', '2', '3', '4']"
                answer = self.test_set_point
                return answer

    def tc_heater_power(self, channel):
        if self.test_flag != 'test':
            if channel == '1':
                answer = round(float(self.device_read_unsigned(370, 1)), 1)
                return answer
            elif channel == '2':
                answer = round(float(self.device_read_unsigned(1394, 1)), 1)
                return answer
            elif channel == '3':
                answer = round(float(self.device_read_unsigned(2418, 1)), 1)
                return answer
            elif channel == '4':
                answer = round(float(self.device_read_unsigned(3442, 1)), 1)
                return answer
        
        elif self.test_flag == 'test':
            assert(channel == '1' or channel == '2' or channel == '3' or channel == '4'), "Incorrect channel; channel: ['1', '2', '3', '4']"
            answer = self.test_power
            return answer

    def tc_sensor(self, *sensor): 
        if self.test_flag != 'test':
            if len(sensor) == 2:
                sens = str(sensor[0])
                state = str(sensor[1])
                if state in self.state_dict:
                    flag = self.state_dict[state]           
                if sens in self.channel_dict:
                    if sens == '1':
                        self.device_write_unsigned(384, flag, 0)
                    elif sens == '2':
                        self.device_write_unsigned(1408, flag, 0)
                    elif sens == '3':
                        self.device_write_unsigned(2432, flag, 0)
                    elif sens == '4':
                        self.device_write_unsigned(3456, flag, 0)

            elif len(sensor) == 1:
                sens = str(sensor[0])
                if sens in self.channel_dict:
                    if sens == '1':
                        raw_answer = int(self.device_read_unsigned(384, 0))
                        answer = cutil.search_keys_dictionary(self.state_dict, raw_answer)
                        return answer
                    elif sens == '2':
                        raw_answer = int(self.device_read_unsigned(1408, 0))
                        answer = cutil.search_keys_dictionary(self.state_dict, raw_answer)
                        return answer
                    elif sens == '3':
                        raw_answer = int(self.device_read_unsigned(2432, 0))
                        answer = cutil.search_keys_dictionary(self.state_dict, raw_answer)
                        return answer
                    elif sens == '4':
                        raw_answer = int(self.device_read_unsigned(3456, 0))
                        answer = cutil.search_keys_dictionary(self.state_dict, raw_answer)
                        return answer

        elif self.test_flag == 'test':
            if len(sensor) == 2:
                sens = str(sensor[0])
                state = str(sensor[1])
                assert(sens in self.channel_dict), f'Invalid argument; channel: {list(self.channel_dict.keys())}; state: {list(self.state_dict.keys())}'
                assert(state in self.state_dict), f'Invalid argument; channel: {list(self.channel_dict.keys())}; state: {list(self.state_dict.keys())}'
            elif len(sensor) == 1:
                sens = str(sensor[0])
                assert(sens in self.channel_dict), f'Invalid argument; channel: {list(self.channel_dict.keys())}; state: {list(self.state_dict.keys())}'
                answer = self.test_loop_state
                return answer

    def tc_proportional(self, *prop):
        if self.test_flag != 'test':
            if len(prop) == 2:
                ch = str(prop[0])
                value = round(float(prop[1]), 1) * 10
                if ch in self.channel_dict:
                    if value >= self.proportional_min and value <= self.proportional_max:
                        if ch == '1':
                            self.device_write_unsigned(386, value, 0)
                        elif ch == '2':
                            self.device_write_unsigned(1410, value, 0)
                        elif ch == '3':
                            self.device_write_unsigned(2434, value, 0)
                        elif ch == '4':
                            self.device_write_unsigned(3458, value, 0)

            elif len(prop) == 1:
                ch = str(prop[0])
                if ch in self.channel_dict:
                    if ch == '1':
                        answer = int(self.device_read_unsigned(386, 0)) / 10
                        return answer
                    elif ch == '2':
                        answer = int(self.device_read_unsigned(1410, 0)) / 10
                        return answer
                    elif ch == '3':
                        answer = int(self.device_read_unsigned(2434, 0)) / 10
                        return answer
                    elif ch == '4':
                        answer = int(self.device_read_unsigned(3458, 0)) / 10
                        return answer

        elif self.test_flag != 'test':
            if len(prop) == 2:
                ch = str(prop[0])
                value = round(float(prop[1]), 1) * 10
                assert(ch in self.channel_dict), 'Invalid argument; channel: ['1', '2', '3', '4']; P: float'
                assert(value >= self.proportional_min and value <= self.proportional_max), \
                    f'Invalid proportional coefficient; The available range is from {self.proportional_min} to {self.proportional_max}'
            elif len(prop) == 1:
                ch = str(prop[0])
                assert(ch in self.channel_dict), 'Invalid argument; channel: ['1', '2', '3', '4']'
                answer = self.test_proportional
                return answer                         
            else:
                general.message('Invalid argument; channel: ['1', '2', '3', '4']; P: float')
                sys.exit()

    def tc_derivative(self, *der):
        if self.test_flag != 'test':
            if len(der) == 2:
                ch = str(der[0])
                value = round(float(der[1]), 1) * 10
                if ch in self.channel_dict:
                    if value >= self.derivative_min and value <= self.derivative_max:
                        if ch == '1':
                            self.device_write_unsigned(388, value, 0)
                        elif ch == '2':
                            self.device_write_unsigned(1412, value, 0)
                        elif ch == '3':
                            self.device_write_unsigned(2436, value, 0)
                        elif ch == '4':
                            self.device_write_unsigned(3460, value, 0)

            elif len(der) == 1:
                ch = str(der[0])
                if ch in self.channel_dict:
                    if ch == '1':
                        answer = int(self.device_read_unsigned(388, 0)) / 10
                        return answer
                    elif ch == '2':
                        answer = int(self.device_read_unsigned(1412, 0)) / 10
                        return answer
                    elif ch == '3':
                        answer = int(self.device_read_unsigned(2436, 0)) / 10
                        return answer
                    elif ch == '4':
                        answer = int(self.device_read_unsigned(3460, 0)) / 10
                        return answer

        elif self.test_flag != 'test':
            if len(der) == 2:
                ch = str(der[0])
                value = round(float(der[1]), 1) * 10
                assert(ch in self.channel_dict), 'Invalid argument; channel: ['1', '2', '3', '4']; D: float'
                assert(value >= self.derivative_min and value <= self.derivative_max),\
                    f'Invalid derivative coefficient; The available range is from {self.derivative_min} to {self.derivative_max}'
            elif len(der) == 1:
                ch = str(der[0])
                assert(ch in self.channel_dict), 'Invalid argument; channel:  ['1', '2', '3', '4']'
                answer = self.test_derivative
                return answer                         
            else:
                general.message('Invalid argument; channel: ['1', '2', '3', '4']; D: float')
                sys.exit()

    def tc_integral(self, *integ):
        if self.test_flag != 'test':
            if len(integ) == 2:
                ch = str(integ[0])
                value = round(float(integ[1]), 0)
                if ch in self.channel_dict:
                    if value >= self.integral_min and value <= self.integral_max:
                        if ch == '1':
                            self.device_write_unsigned(387, value, 0)
                        elif ch == '2':
                            self.device_write_unsigned(1411, value, 0)
                        elif ch == '3':
                            self.device_write_unsigned(2435, value, 0)
                        elif ch == '4':
                            self.device_write_unsigned(3459, value, 0)

            elif len(integ) == 1:
                ch = str(integ[0])
                if ch in self.channel_dict:
                    if ch == '1':
                        answer = int(self.device_read_unsigned(387, 0))
                        return answer
                    elif ch == '2':
                        answer = int(self.device_read_unsigned(1411, 0))
                        return answer
                    elif ch == '3':
                        answer = int(self.device_read_unsigned(2435, 0))
                        return answer
                    elif ch == '4':
                        answer = int(self.device_read_unsigned(3459, 0))
                        return answer

        elif self.test_flag != 'test':
            if len(integ) == 2:
                ch = str(integ[0])
                value = round(float(integ[1]), 1)
                assert(ch in self.channel_dict), 'Invalid argument; channel: ['1', '2', '3', '4']; I: int'
                assert(value >= self.integral_min and value <= self.integral_max),
                    f'Invalid integral coefficient; The available range is from {self.integral_min} to {self.integral_max}'
            elif len(integ) == 1:
                ch = str(integ[0])
                assert(ch in self.channel_dict), 'Invalid argument; channel: ['1', '2', '3', '4']'
                answer = self.test_integral
                return answer                         
            else:
                general.message('Invalid argument; channel: ['1', '2', '3', '4']; I: int')
                sys.exit()

def main():
    pass

if __name__ == "__main__":
    main()
