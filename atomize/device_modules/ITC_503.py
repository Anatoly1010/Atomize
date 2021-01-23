#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import gc
import sys
import pyvisa
from pyvisa.constants import StopBits, Parity
import atomize.device_modules.config.config_utils as cutil
import atomize.general_modules.general_functions as general

# Note that device answers on every command. 
# We should use query function even when writing data to the device.

#### Inizialization
# setting path to *.ini file
path_current_directory = os.path.dirname(__file__)
path_config_file = os.path.join(path_current_directory, 'config','ITC_503_config.ini')

# configuration data
config = cutil.read_conf_util(path_config_file)
specific_parameters = cutil.read_specific_parameters(path_config_file)

# auxilary dictionaries
state_dict = {'Manual-Manual': 0, 'Auto-Manual': 1, 'Manual-Auto': 2, 'Auto-Auto': 3,}
sensor_list = [1, 2, 3]
lock_dict = {'Local-Locked': 'C0', 'Remote-Locked': 'C1', 'Local-Unlocked': 'C2', 'Remote-Unlocked': 'C3',}

# Ranges and limits
config_channels = int(specific_parameters['channels'])
temperature_max = 320
temperature_min = 0.3
power_percent_min = 0
power_percent_max = 99.9
flow_percent_min = 0
flow_percent_max = 99.9
power_max = 40 # 40 V
power_min = 0

# Test run parameters
# These values are returned by the modules in the test run 
if len(sys.argv) > 1:
    test_flag = sys.argv[1]
else:
    test_flag = 'None'

test_temperature = 200.
test_set_point = 298.
test_flow = 1.
test_heater_percentage = 1.
test_mode = 'Manual-Manual'
test_lock = 'Local-Locked'
test_sensor = 1

class ITC_503:
    #### Basic interaction functions
    def __init__(self):
        if test_flag != 'test':
            if config['interface'] == 'gpib':
                general.message('Invalid interface')
                sys.exit()
                #try:
                #    import Gpib
                #    self.status_flag = 1
                #    self.device = Gpib.Gpib(config['board_address'], config['gpib_address'])
                #    try:
                #        # test should be here
                #        self.device_write('Q0') # \r terminator
                #        self.device_query('C3') # Remote and Unlocked; C1 - remote and locked
                #    except BrokenPipeError:
                #        general.message("No connection")
                #        self.status_flag = 0;
                #        sys.exit()  
                #except BrokenPipeError:        
                #    general.message("No connection")
                #    self.status_flag = 0
                #    sys.exit()

            elif config['interface'] == 'rs232':
                try:
                    self.status_flag = 1
                    rm = pyvisa.ResourceManager()
                    self.device = rm.open_resource(config['serial_address'], read_termination=config['read_termination'],
                    write_termination=config['write_termination'], baud_rate=config['baudrate'],
                    data_bits=config['databits'], parity=config['parity'], stop_bits=config['stopbits'])
                    self.device.timeout = config['timeout'] # in ms
                    try:
                        # test should be here
                        self.device_write('Q0') # \r terminator
                        self.device_query('C3') # Remote and Unlocked; C1 - remote and locked
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
                general.message('Invalid interface')
                sys.exit()
                #self.device.write(command)
                #general.wait('50 ms')
                #answer = self.device.read()
            elif config['interface'] == 'rs232':
                answer = self.device.query(command)
            return answer
        else:
            general.message("No Connection")
            self.status_flag = 0
            sys.exit()

    #### device specific functions
    def tc_name(self):
        if test_flag != 'test':
            answer = self.device_query('V')
            return answer
        elif test_flag == 'test':
            answer = config['name']
            return answer

    def tc_temperature(self, channel):
        if test_flag != 'test':
            channel = str(channel)
            # If the first character is a '+' or '-' the sensor is returning
            # temperatures in degree Celsius, otherwise in Kelvin
            if config_channels >= int(channel):
                if channel == '1':
                    raw_answer = str(self.device_query('R1')[1:])
                    if raw_answer[0] == '+' or raw_answer[0] == '-':
                        answer = float(raw_answer) + 273.16 # convert to Kelvin
                    else:
                        answer = float(raw_answer)
                        return answer
                elif channel == '2':
                    raw_answer = str(self.device_query('R2')[1:])
                    if raw_answer[0] == '+' or raw_answer[0] == '-':
                        answer = float(raw_answer) + 273.16 # convert to Kelvin
                    else:
                        answer = float(raw_answer)
                        return answer
                elif channel == '3':
                    raw_answer = str(self.device_query('R3')[1:])
                    if raw_answer[0] == '+' or raw_answer[0] == '-':
                        answer = float(raw_answer) + 273.16 # convert to Kelvin
                    else:
                        answer = float(raw_answer)
                        return answer
                else:
                    general.message("Invalid channel")
                    sys.exit()
            else:
                general.message("Invalid channel")
                sys.exit()
        
        elif test_flag == 'test':
            if config_channels >= int(channel):
                assert(channel == '1' or channel == '2' or channel == '3'), "Incorrect channel"
                answer = test_temperature
                return answer
            else:
                assert(1 == 2), "Incorrect channel"

    def tc_setpoint(self, *temp):
        if test_flag != 'test':
            if len(temp) == 1:
                temp = float(temp[0])
                if temp <= temperature_max and temp >= temperature_min:
                    self.device.query('T' + f'{temp:.3f}')
                else:
                    general.message("Incorrect set point temperature")
                    sys.exit()
            elif len(temp) == 0:
                answer = float(self.device_query('R0')[1:])
                return answer   
            else:
                general.message("Invalid argument")
                sys.exit()      

        elif test_flag == 'test':
            if len(temp) == 1:
                temp = float(temp[0])
                assert(temp <= temperature_max and temp >= temperature_min), 'Incorrect set point temperature is reached'
            elif len(temp) == 0:
                answer = test_set_point
                return answer

    def tc_state(self, *mode):
        if test_flag != 'test':
            if  len(mode) == 1:
                md = str(mode[0])
                if md in state_dict:
                    flag = state_dict[md]
                    if flag == 2 or flag == 3:
                        raw_answer = self.device_query('X')
                        answer = raw_answer[2:4]
                        if answer == 'A5' or answer == 'A6' or answer == 'A7' or answer == 'A8':
                            general.message('Cannot set state to GAS AUTO while in AutoGFS phase.')
                        else:
                            self.device_query("A" + str(flag))
                    else:
                        self.device_query("A" + str(flag))
                else:
                    general.message("Invalid temperature controller state")
                    sys.exit()
            elif  len(mode) == 0:
                raw_answer = self.device_query('X')
                answer_flag = int(raw_answer[3:4])
                answer = cutil.search_keys_dictionary(state_dict, answer_flag)
                return answer                    
            else:
                general.message("Invalid argument")
                sys.exit()

        elif test_flag == 'test':                           
            if len(mode) == 1:
                md = str(mode[0])
                if md in state_dict:
                    flag = state_dict[md]
                else:
                    assert(1 == 2), "Invalid heater range"
            elif  len(mode) == 0:
                answer = test_mode
                return answer                
            else:
                assert(1 == 2), "Invalid heater range"

    def tc_heater_power(self, *power_percent):
        if test_flag != 'test':
            if len(power_percent) == 0:
                answer = float(self.device_query('R5')[1:])
                return answer
            elif len(power_percent) == 1:
                pw = float(power_percent[0])
                raw_answer = self.device_query('X')
                answer = raw_answer[2:4]
                if answer[0] != 'A':
                    general.message('Device returns invalid state data.')
                    sys.exit()
                else:
                    if answer == 'A0' or answer == 'A2':
                        if pw >= power_percent_min and pw <= power_percent_max:
                            self.device_query('O' + f'{pw:.1f}')
                        else:
                            general.message("Invalid heater power percent")
                            sys.exit()
                    else:
                        general.message("Cannot change heater power while heater power is controlled by the device")

        elif test_flag == 'test':
            if len(power_percent) == 0:
                answer = test_heater_percentage
                return answer
            elif len(power_percent) == 1:
                pw = float(power_percent[0])
                assert(pw >= power_percent_min and pw <= power_percent_max), "Invalid heater power"

    def tc_heater_power_limit(self, power):
        if test_flag != 'test':
            pw = float(power)
            raw_answer = self.device_query('X')
            answer = raw_answer[2:4]
            if answer[0] != 'A':
                general.message('Device returns invalid state data.')
                sys.exit()
            else:
                if answer == 'A0' or answer == 'A2':
                    if pw >= power_min and pw <= power_max:
                        self.device_query('M' + f'{pw:.1f}')
                    else:
                        general.message("Invalid heater power")
                        sys.exit()
                else:
                    general.message("Cannot change heater power while heater power is controlled by the device")

        elif test_flag == 'test':
            pw = float(power)
            assert(pw >= power_min and pw <= power_max), "Invalid heater power range"

    def tc_sensor(self, *sensor):
        if test_flag != 'test':
            if len(sensor) == 1:
                sens = int(sensor[0])
                if sens in sensor_list and config_channels >= int(channel):
                    self.device_query('H' + str(sens))
                else:
                    general.message('Invalid sensor')
                    sys.exit()
            elif len(sensor) == 0:
                raw_answer = self.device_query('X')
                answer = raw_answer[9:11]
                if answer[0] != 'H':
                    general.message('Device returns invalid heater sensor data.')
                    sys.exit()
                else:
                    return int(answer[1])                

        elif test_flag == 'test':
            if len(sensor) == 1:
                sens = int(sensor[0])
                assert(sens in sensor_list), 'Invalid sensor argument'
                assert(config_channels >= int(channel)), 'Invalid sensor argument'
            elif len(sensor) == 0:
                answer = test_sensor
                return answer

    def tc_gas_flow(self, *flow):
        if test_flag != 'test':
            if len(flow) == 0:
                answer = float(self.device_query('R7')[1:])
                return answer
            elif len(flow) == 1:
                fl = float(flow[0])
                raw_answer = self.device_query('X')
                answer = raw_answer[2:4]
                if answer[0] != 'A':
                    general.message('Device returns invalid state data.')
                    sys.exit()
                else:
                    if answer == 'A0' or answer == 'A1':
                        if fl >= flow_percent_min and fl <= flow_percent_max:
                            self.device_query('G' + f'{fl:.1f}')
                        else:
                            general.message("Invalid gas flow percent")
                            sys.exit()
                    else:
                        general.message("Cannot gas flow percentage while flow is controlled by the device")

        elif test_flag == 'test':
            if len(flow) == 0:
                answer = test_flow
                return answer
            elif len(flow) == 1:
                fl = float(flow[0])
                assert(fl >= flow_percent_min and fl <= flow_percent_max), "Invalid gas flow percent"

    def tc_lock_keyboard(self, *lock):
        if test_flag != 'test':
            if len(lock) == 1:
                lk = str(lock[0])
                if lk in lock_dict:
                    flag = lock_dict[lk]
                    self.device_query(str(flag))
                else:
                    general.message("Invalid argument")
                    sys.exit()
            elif len(lock) == 0:
                raw_answer = self.device_query('X')
                answer_flag = raw_answer[4:6]
                answer = cutil.search_keys_dictionary(lock_dict, answer_flag)
                return answer    
            else:
                general.message("Invalid argument")
                sys.exit()                      

        elif test_flag == 'test':
            if len(lock) == 1:
                lk = str(lock[0])
                if lk in lock_dict:
                    flag = lock_dict[lk]
                else:
                    assert(1 == 2), "Invalid lock argument"
            elif len(lock) == 0:
                answer = test_lock
                return answer
            else:
                assert(1 == 2), "Invalid argument"

    def tc_command(self, command):
        if test_flag != 'test':
            self.device_query(command)
        elif test_flag == 'test':
            pass

    def tc_query(self, command):
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