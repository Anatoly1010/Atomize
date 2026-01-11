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

class ITC_503:
    #### Basic interaction functions
    def __init__(self):

        # Note that device answers on every command. 
        # We should use query function even when writing data to the device.

        #### Inizialization
        # setting path to *.ini file
        self.path_current_directory = lconf.load_config_device()
        self.path_config_file = os.path.join(self.path_current_directory, 'ITC_503_config.ini')

        # configuration data
        self.config = cutil.read_conf_util(self.path_config_file)
        self.specific_parameters = cutil.read_specific_parameters(self.path_config_file)

        # auxilary dictionaries
        self.state_dict = {'Manual-Manual': 0, 'Auto-Manual': 1, 'Manual-Auto': 2, 'Auto-Auto': 3,}
        self.sensor_list = [1, 2, 3]
        self.lock_dict = {'Local-Locked': 'C0', 'Remote-Locked': 'C1', 'Local-Unlocked': 'C2', 'Remote-Unlocked': 'C3',}

        # Ranges and limits
        self.config_channels = int(self.specific_parameters['channels'])
        self.temperature_max = 320
        self.temperature_min = 0.3
        self.power_percent_min = 0
        self.power_percent_max = 99.9
        self.flow_percent_min = 0
        self.flow_percent_max = 99.9
        self.power_max = 40 # 40 V
        self.power_min = 0

        # Test run parameters
        # These values are returned by the modules in the test run 
        if len(sys.argv) > 1:
            self.test_flag = sys.argv[1]
        else:
            self.test_flag = 'None'

        if self.test_flag != 'test':
            if self.config['interface'] == 'gpib':
                general.message(f'Invalid interface {self.__class__.__name__}')
                sys.exit()
                #try:
                #    import Gpib
                #    self.status_flag = 1
                #    self.device = Gpib.Gpib(self.config['board_address'], self.config['gpib_address'])
                #    try:
                #        # test should be here
                #        self.device_write('Q0') # \r terminator
                #        self.device_query('C3') # Remote and Unlocked; C1 - remote and locked
                #    except BrokenPipeError:
                #        general.message(f"No connection {self.__class__.__name__}")
                #        self.status_flag = 0;
                #        sys.exit()  
                #except BrokenPipeError:        
                #    general.message(f"No connection {self.__class__.__name__}")
                #    self.status_flag = 0
                #    sys.exit()

            elif self.config['interface'] == 'rs232':
                try:
                    self.status_flag = 1
                    rm = pyvisa.ResourceManager()
                    self.device = rm.open_resource(self.config['serial_address'], read_termination=self.config['read_termination'],
                    write_termination=self.config['write_termination'], baud_rate=self.config['baudrate'],
                    data_bits=self.config['databits'], parity=self.config['parity'], stop_bits=self.config['stopbits'])
                    self.device.timeout = self.config['timeout'] # in ms
                    try:
                        # test should be here
                        self.device_write('Q0') # \r terminator
                        self.device_query('C3') # Remote and Unlocked; C1 - remote and locked
                    except (pyvisa.VisaIOError, BrokenPipeError):
                        self.status_flag = 0
                        general.message(f"No connection {self.__class__.__name__}")
                        sys.exit()
                except (pyvisa.VisaIOError, BrokenPipeError):
                    general.message(f"No connection {self.__class__.__name__}")
                    self.status_flag = 0
                    sys.exit()

        elif self.test_flag == 'test':
            self.test_temperature = 200.
            self.self.test_set_point = 298.
            self.test_flow = 1.
            self.test_heater_percentage = 1.
            self.test_mode = 'Manual-Manual'
            self.test_lock = 'Local-Locked'
            self.test_sensor = 1

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
            general.message(f"No connection {self.__class__.__name__}")
            self.status_flag = 0
            sys.exit()

    def device_query(self, command):
        if self.status_flag == 1:
            if self.config['interface'] == 'gpib':
                general.message(f'Invalid interface {self.__class__.__name__}')
                sys.exit()
                #self.device.write(command)
                #general.wait('50 ms')
                #answer = self.device.read()
            elif self.config['interface'] == 'rs232':
                answer = self.device.query(command)
            return answer
        else:
            general.message(f"No connection {self.__class__.__name__}")
            self.status_flag = 0
            sys.exit()

    #### device specific functions
    def tc_name(self):
        if self.test_flag != 'test':
            answer = self.device_query('V')
            return answer
        elif self.test_flag == 'test':
            answer = self.config['name']
            return answer

    def tc_temperature(self, channel):
        if self.test_flag != 'test':
            channel = str(channel)
            # If the first character is a '+' or '-' the sensor is returning
            # temperatures in degree Celsius, otherwise in Kelvin
            if self.config_channels >= int(channel):
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
        
        elif self.test_flag == 'test':
            if self.config_channels >= int(channel):
                assert(channel == '1' or channel == '2' or channel == '3'), "Incorrect channel; channel: ['1', '2', '3']"
                answer = self.test_temperature
                return answer
            else:
                assert(1 == 2), "Incorrect channel; channel: ['1', '2', '3']"

    def tc_setpoint(self, *temp):
        if self.test_flag != 'test':
            if len(temp) == 1:
                temp = float(temp[0])
                if temp <= self.temperature_max and temp >= self.temperature_min:
                    self.device.query('T' + f'{temp:.3f}')
            elif len(temp) == 0:
                answer = float(self.device_query('R0')[1:])
                return answer

        elif self.test_flag == 'test':
            if len(temp) == 1:
                temp = float(temp[0])
                assert(temp <= self.temperature_max and temp >= self.temperature_min),\
                    f'Incorrect set point temperature is reached. The available range is from {self.temperature_min} to {self.temperature_max}'
            elif len(temp) == 0:
                answer = self.test_set_point
                return answer

    def tc_state(self, *mode):
        if self.test_flag != 'test':
            if  len(mode) == 1:
                md = str(mode[0])
                if md in self.state_dict:
                    flag = self.state_dict[md]
                    if flag == 2 or flag == 3:
                        raw_answer = self.device_query('X')
                        answer = raw_answer[2:4]
                        if answer == 'A5' or answer == 'A6' or answer == 'A7' or answer == 'A8':
                            general.message('Cannot set state to GAS AUTO while in AutoGFS phase')
                        else:
                            self.device_query("A" + str(flag))
                    else:
                        self.device_query("A" + str(flag))

            elif  len(mode) == 0:
                raw_answer = self.device_query('X')
                answer_flag = int(raw_answer[3:4])
                answer = cutil.search_keys_dictionary(self.state_dict, answer_flag)
                return answer                    

        elif self.test_flag == 'test':                           
            if len(mode) == 1:
                md = str(mode[0])
                if md in self.state_dict:
                    flag = self.state_dict[md]
                else:
                    assert(1 == 2), f"Invalid state; mode: {list(self.state_dict.keys())}"
            elif  len(mode) == 0:
                answer = self.test_mode
                return answer                
            else:
                assert(1 == 2), f"Invalid state; mode: {list(self.state_dict.keys())}"

    def tc_heater_power(self, *power_percent):
        if self.test_flag != 'test':
            if len(power_percent) == 0:
                answer = float(self.device_query('R5')[1:])
                return answer
            elif len(power_percent) == 1:
                pw = float(power_percent[0])
                raw_answer = self.device_query('X')
                answer = raw_answer[2:4]
                if answer[0] != 'A':
                    general.message(f'Device {self.__class__.__name__} returns invalid state data')
                else:
                    if answer == 'A0' or answer == 'A2':
                        if pw >= self.power_percent_min and pw <= self.power_percent_max:
                            self.device_query('O' + f'{pw:.1f}')
                    else:
                        general.message(f"Cannot change heater power while heater power is controlled by the device {self.__class__.__name__}")

        elif self.test_flag == 'test':
            if len(power_percent) == 0:
                answer = self.test_heater_percentage
                return answer
            elif len(power_percent) == 1:
                pw = float(power_percent[0])
                assert(pw >= self.power_percent_min and pw <= self.power_percent_max),\
                    f"Invalid heater power. The available range is from {self.power_percent_min} to {self.power_percent_max}"

    def tc_heater_power_limit(self, power):
        if self.test_flag != 'test':
            pw = float(power)
            raw_answer = self.device_query('X')
            answer = raw_answer[2:4]
            if answer[0] != 'A':
                general.message(f'Device {self.__class__.__name__} returns invalid state data')
            else:
                if answer == 'A0' or answer == 'A2':
                    if pw >= self.power_min and pw <= self.power_max:
                        self.device_query('M' + f'{pw:.1f}')
                else:
                    general.message(f"Cannot change heater power while heater power is controlled by the device {self.__class__.__name__}")

        elif self.test_flag == 'test':
            pw = float(power)
            assert(pw >= self.power_min and pw <= self.power_max),\
                f"Invalid heater power. The available range is from {self.power_percent_min} to {self.power_percent_max}"

    def tc_sensor(self, *sensor):
        if self.test_flag != 'test':
            if len(sensor) == 1:
                sens = int(sensor[0])
                if sens in self.sensor_list and self.config_channels >= int(channel):
                    self.device_query('H' + str(sens))
            elif len(sensor) == 0:
                raw_answer = self.device_query('X')
                answer = raw_answer[9:11]
                if answer[0] != 'H':
                    general.message(f'Device {self.__class__.__name__} returns invalid heater sensor data')
                    sys.exit()
                else:
                    return int(answer[1])                

        elif self.test_flag == 'test':
            if len(sensor) == 1:
                sens = int(sensor[0])
                assert(sens in self.sensor_list), f'Invalid sensor argument; sensor: {self.sensor_list}'
                assert(self.config_channels >= int(channel)), "Incorrect channel; channel: ['1', '2', '3']"
            elif len(sensor) == 0:
                answer = self.test_sensor
                return answer

    def tc_gas_flow(self, *flow):
        if self.test_flag != 'test':
            if len(flow) == 0:
                answer = float(self.device_query('R7')[1:])
                return answer
            elif len(flow) == 1:
                fl = float(flow[0])
                raw_answer = self.device_query('X')
                answer = raw_answer[2:4]
                if answer[0] != 'A':
                    general.message(f'Device {self.__class__.__name__} returns invalid state data')
                    sys.exit()
                else:
                    if answer == 'A0' or answer == 'A1':
                        if fl >= self.flow_percent_min and fl <= self.flow_percent_max:
                            self.device_query('G' + f'{fl:.1f}')
                    else:
                        general.message(f"Cannot gas flow percentage while flow is controlled by the device {self.__class__.__name__}")

        elif self.test_flag == 'test':
            if len(flow) == 0:
                answer = self.test_flow
                return answer
            elif len(flow) == 1:
                fl = float(flow[0])
                assert(fl >= self.flow_percent_min and fl <= self.flow_percent_max),\
                    f"Invalid gas flow percent. The available range is from {self.flow_percent_min} to {self.flow_percent_max}"

    def tc_lock_keyboard(self, *lock):
        if self.test_flag != 'test':
            if len(lock) == 1:
                lk = str(lock[0])
                if lk in self.lock_dict:
                    flag = self.lock_dict[lk]
                    self.device_query(str(flag))

            elif len(lock) == 0:
                raw_answer = self.device_query('X')
                answer_flag = raw_answer[4:6]
                answer = cutil.search_keys_dictionary(self.lock_dict, answer_flag)
                return answer                  

        elif self.test_flag == 'test':
            if len(lock) == 1:
                lk = str(lock[0])
                if lk in self.lock_dict:
                    flag = self.lock_dict[lk]
                else:
                    assert(1 == 2), f"Invalid lock argument; lock: {list( self.lock_dict.keys() )}"
            elif len(lock) == 0:
                answer = self.test_lock
                return answer
            else:
                assert(1 == 2), f"Invalid lock argument; lock: {list( self.lock_dict.keys() )}"

    def tc_command(self, command):
        if self.test_flag != 'test':
            self.device_query(command)
        elif self.test_flag == 'test':
            pass

    def tc_query(self, command):
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