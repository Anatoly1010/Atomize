#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import gc
import sys
import serial
import minimalmodbus
import atomize.device_modules.config.config_utils as cutil
import atomize.general_modules.general_functions as general

#### Inizialization
# setting path to *.ini file
path_current_directory = os.path.dirname(__file__)
path_config_file = os.path.join(path_current_directory, 'config','Termodat_13KX3_config.ini')

# configuration data
config = cutil.read_conf_util(path_config_file)
modbus_parameters = cutil.read_modbus_parameters(path_config_file)
specific_parameters = cutil.read_specific_parameters(path_config_file)

# auxilary dictionaries
channel_dict = {'1': 1, '2': 2, }
state_dict = {'On': 1, 'Off': 0, }

# Ranges and limits
channels = int(specific_parameters['channels'])
temperature_max = 750
temperature_min = 0.3
proportional_min = 0.1
proportional_max = 2000
derivative_min = 0.0
derivative_max = 999.9
integral_min = 0
integral_max = 9999

# Test run parameters
# These values are returned by the modules in the test run 
if len(sys.argv) > 1:
    test_flag = sys.argv[1]
else:
    test_flag = 'None'

test_temperature = 300
test_set_point = 273
test_power = 0
test_loop_state = 'Off'
test_proportional = 70
test_derivative = 50
test_integral = 600

class Termodat_13KX3:
    #### Basic interaction functions
    def __init__(self):
        if test_flag != 'test':
            if config['interface'] == 'rs485':
                try:
                    self.status_flag = 1
                    self.device = minimalmodbus.Instrument(config['serial_address'], modbus_parameters[1])
                    #self.device.mode = minimalmodbus.MODE_ASCII
                    self.device.mode = modbus_parameters[0]
                    #check there
                    self.device.serial.baudrate = config['baudrate']
                    self.device.serial.bytesize = config['databits']
                    self.device.serial.parity = config['parity']
                    #check there
                    self.device.serial.stopbits = config['stopbits']
                    self.device.serial.timeout = config['timeout']/1000
                    try:
                        pass
                        # test should be here
                        #self.device_write('*CLS')

                    except serial.serialutil.SerialException:
                        general.message("No connection")
                        self.status_flag = 0
                        sys.exit()
                except serial.serialutil.SerialException:
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

    def device_write_signed(self, register, value, decimals):
        if self.status_flag == 1:
            self.device.write_register(register, value, decimals, functioncode = 6, signed = True)
        else:
            general.message("No Connection")
            self.status_flag = 0
            sys.exit()

    def device_write_unsigned(self, register, value, decimals):
        if self.status_flag == 1:
            self.device.write_register(register, value, decimals, functioncode = 6, signed = False)
        else:
            general.message("No Connection")
            self.status_flag = 0
            sys.exit()

    def device_read_signed(self, register, decimals):
        if self.status_flag == 1:
            answer = self.device.read_register(register, decimals, signed = True)
            return answer
        else:
            general.message("No Connection")
            self.status_flag = 0
            sys.exit()

    def device_read_unsigned(self, register, decimals):
        if self.status_flag == 1:
            answer = self.device.read_register(register, decimals, signed = False)
            return answer
        else:
            general.message("No Connection")
            self.status_flag = 0
            sys.exit()

    #### device specific functions
    def tc_name(self):
        if test_flag != 'test':
            answer = config['name']
            return answer
        elif test_flag == 'test':
            answer = config['name']
            return answer

    def tc_temperature(self, channel):
        if test_flag != 'test':
            if channel == '1':
                answer = round(float(self.device_read_signed(368, 1)) + 273.15, 1)
                return answer
            elif channel == '2':
                answer = round(float(self.device_read_signed(1392, 1)) + 273.1, 1)
                return answer
            else:
                general.message("Invalid argument")
                sys.exit()
        
        elif test_flag == 'test':
            assert(channel == '1' or channel == '2'), "Incorrect channel"
            answer = test_temperature
            return answer

    def tc_setpoint(self, *temperature):
        if test_flag != 'test':
            if len(temperature) == 2:
                ch = str(temperature[0])
                temp = round(float(temperature[1]), 1)
                if temp <= temperature_max and temp >= temperature_min:
                    if ch in channel_dict:
                        flag = channel_dict[ch]
                        if flag <= channels:
                            if ch == '1':
                                self.device_write_signed(369, temp - 273.1, 1)
                            elif ch == '2':
                                self.device_write_signed(1393, temp - 273.1, 1)
                            else:
                                general.message("Incorrect channel")
                        else:
                            general.message("Invalid channel")
                            sys.exit()
                    else:
                        general.message("Invalid channel")
                        sys.exit()
                else:
                    general.message("Incorrect set point temperature")
                    sys.exit()
            elif len(temperature) == 1:
                ch = str(temperature[0])
                if ch in channel_dict:
                    flag = channel_dict[ch]
                    if flag <= channels:
                        if ch == '1':
                            answer = round(float(self.device_read_signed(369, 1)) + 273.15, 1)
                            return answer
                        elif ch == '2':
                            answer = round(float(self.device_read_signed(1393, 1)) + 273.15, 1)
                            return answer
                        else:
                            general.message("Incorrect channel")
                            sys.exit()
                    else:
                        general.message("Incorrect channel")
                        sys.exit()
                else:
                    general.message("Incorrect channel")
                    sys.exit()
            else:
                general.message("Invalid argument")
                sys.exit()

        elif test_flag == 'test':
            if len(temperature) == 2:
                ch = str(temperature[0])
                temp = float(temperature[1])
                assert(ch in channel_dict), 'Invalid channel argument'
                flag = channel_dict[ch]
                assert(flag <= channels), "Invalid channel"
                assert(temp <= temperature_max and temp >= temperature_min), 'Incorrect set point temperature is reached'
            elif len(temperature) == 1:
                ch = str(temperature[0])
                assert(ch in channel_dict), 'Invalid channel argument'
                flag = channel_dict[ch]
                assert(flag <= channels), "Invalid channel"
                answer = test_set_point
                return answer

    def tc_heater_power(self, channel):
        if test_flag != 'test':
            if channel == '1':
                answer = round(float(self.device_read_unsigned(370, 1)), 1)
                return answer
            elif channel == '2':
                answer = round(float(self.device_read_unsigned(1394, 1)), 1)
                return answer
            else:
                general.message("Invalid argument")
                sys.exit()
        
        elif test_flag == 'test':
            assert(channel == '1' or channel == '2'), "Incorrect channel"
            answer = test_power
            return answer

    def tc_sensor(self, *sensor): 
        if test_flag != 'test':
            if len(sensor) == 2:
                sens = str(sensor[0])
                state = str(sensor[1])
                if state in state_dict:
                    flag = state_dict[state]
                else:
                    general.message('Incorrect state')
                    sys.exit()                    
                if sens in channel_dict:
                    if sens == '1':
                        self.device_write_unsigned(384, flag, 0)
                    elif sens == '2':
                        self.device_write_unsigned(1408, flag, 0)
                else:
                    general.message('Incorrect loop')
                    sys.exit()
            elif len(sensor) == 1:
                sens = str(sensor[0])
                if sens in channel_dict:
                    if sens == '1':
                        raw_answer = int(self.device_read_unsigned(384, 0))
                        answer = cutil.search_keys_dictionary(state_dict, raw_answer)
                        return answer
                    elif sens == '2':
                        raw_answer = int(self.device_read_unsigned(1408, 0))
                        answer = cutil.search_keys_dictionary(state_dict, raw_answer)
                        return answer
                else:
                    general.message('Incorrect loop')
                    sys.exit()
            else:
                general.message('Invalid argument')
                sys.exit()

        elif test_flag == 'test':
            if len(sensor) == 2:
                sens = str(sensor[0])
                state = str(sensor[1])
                assert(sens in channel_dict), 'Invalid loop'
                assert(state in state_dict), 'Invalid state'
            elif len(sensor) == 1:
                sens = str(sensor[0])
                assert(sens in channel_dict), 'Invalid loop'
                answer = test_loop_state
                return answer

    def tc_proportional(self, *prop):
        if test_flag != 'test':
            if len(prop) == 2:
                ch = str(prop[0])
                value = round(float(prop[1]), 1)*10
                if ch in channel_dict:
                    if value >= proportional_min and value <= proportional_max:
                        if ch == '1':
                            self.device_write_unsigned(386, value, 0)
                        elif ch == '2':
                            self.device_write_unsigned(1410, value, 0)
                    else:
                        general.message('Incorrect proportional coefficient')
                        sys.exit()
                else:
                    general.message('Incorrect channel')
                    sys.exit()
            elif len(prop) == 1:
                ch = str(prop[0])
                if ch in channel_dict:
                    if ch == '1':
                        answer = int(self.device_read_unsigned(386, 0))/10
                        return answer
                    elif ch == '2':
                        answer = int(self.device_read_unsigned(1410, 0))/10
                        return answer
                else:
                    general.message('Incorrect channel')
                    sys.exit()
            else:
                general.message('Invalid argument')
                sys.exit()
        elif test_flag != 'test':
            if len(prop) == 2:
                ch = str(prop[0])
                value = round(float(prop[1]), 1)*10
                assert(ch in channel_dict), 'Invalid channel'
                assert(value <= proportional_min and value >= proportional_max), 'Invalid proportional coefficient'
            elif len(prop) == 1:
                ch = str(prop[0])
                assert(ch in channel_dict), 'Invalid channel'
                answer = test_proportional
                return answer                         
            else:
                general.message('Invalid argument')
                sys.exit()

    def tc_derivative(self, *der):
        if test_flag != 'test':
            if len(der) == 2:
                ch = str(der[0])
                value = round(float(der[1]), 1)*10
                if ch in channel_dict:
                    if value >= derivative_min and value <= derivative_max:
                        if ch == '1':
                            self.device_write_unsigned(388, value, 0)
                        elif ch == '2':
                            self.device_write_unsigned(1412, value, 0)
                    else:
                        general.message('Incorrect derivative coefficient')
                        sys.exit()
                else:
                    general.message('Incorrect channel')
                    sys.exit()
            elif len(der) == 1:
                ch = str(der[0])
                if ch in channel_dict:
                    if ch == '1':
                        answer = int(self.device_read_unsigned(388, 0))/10
                        return answer
                    elif ch == '2':
                        answer = int(self.device_read_unsigned(1412, 0))/10
                        return answer
                else:
                    general.message('Incorrect channel')
                    sys.exit()
            else:
                general.message('Invalid argument')
                sys.exit()
        elif test_flag != 'test':
            if len(der) == 2:
                ch = str(der[0])
                value = round(float(der[1]), 1)*10
                assert(ch in channel_dict), 'Invalid channel'
                assert(value <= derivative_min and value >= derivative_max), 'Invalid derivative coefficient'
            elif len(der) == 1:
                ch = str(der[0])
                assert(ch in channel_dict), 'Invalid channel'
                answer = test_derivative
                return answer                         
            else:
                general.message('Invalid argument')
                sys.exit()

    def tc_integral(self, *integ):
        if test_flag != 'test':
            if len(integ) == 2:
                ch = str(integ[0])
                value = round(float(integ[1]), 0)
                if ch in channel_dict:
                    if value >= integral_min and value <= integral_max:
                        if ch == '1':
                            self.device_write_unsigned(387, value, 0)
                        elif ch == '2':
                            self.device_write_unsigned(1411, value, 0)
                    else:
                        general.message('Incorrect integral coefficient')
                        sys.exit()
                else:
                    general.message('Incorrect channel')
                    sys.exit()
            elif len(integ) == 1:
                ch = str(integ[0])
                if ch in channel_dict:
                    if ch == '1':
                        answer = int(self.device_read_unsigned(387, 0))
                        return answer
                    elif ch == '2':
                        answer = int(self.device_read_unsigned(1411, 0))
                        return answer
                else:
                    general.message('Incorrect channel')
                    sys.exit()
            else:
                general.message('Invalid argument')
                sys.exit()
        elif test_flag != 'test':
            if len(integ) == 2:
                ch = str(integ[0])
                value = round(float(integ[1]), 1)
                assert(ch in channel_dict), 'Invalid channel'
                assert(value <= integral_min and value >= integral_max), 'Invalid integral coefficient'
            elif len(integ) == 1:
                ch = str(integ[0])
                assert(ch in channel_dict), 'Invalid channel'
                answer = test_integral
                return answer                         
            else:
                general.message('Invalid argument')
                sys.exit()

def main():
    pass

if __name__ == "__main__":
    main()
