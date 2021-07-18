#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import struct
import socket
import atomize.device_modules.config.config_utils as cutil
import atomize.general_modules.general_functions as general

#### Inizialization
# setting path to *.ini file
path_current_directory = os.path.dirname(__file__)
path_config_file = os.path.join(path_current_directory, 'config','SR_PTC_10_config.ini')

# configuration data
#config = cutil.read_conf_util(path_config_file)
specific_parameters = cutil.read_specific_parameters(path_config_file)

# auxilary dictionaries
#heater_dict = {'50 W': 3, '5 W': 2, '0.5 W': 1, 'Off': 0,};
#lock_dict = {'Local-Locked': 0, 'Remote-Locked': 1, 'Local-Unlocked': 2, 'Remote-Unlocked': 3,}
#loop_list = [1, 2]
#sens_dict = {0: 'None', 1: 'A', 2: 'B',}

# Ranges and limits
UDP_IP = str(specific_parameters['udp_ip'])
UDP_PORT = int(specific_parameters['udp_port'])
TCP_IP = str(specific_parameters['tcp_ip'])
TCP_PORT = int(specific_parameters['tcp_port'])

# Test run parameters
# These values are returned by the modules in the test run 
if len(sys.argv) > 1:
    test_flag = sys.argv[1]
else:
    test_flag = 'None'

test_temperature = 200.
test_set_point = 298.
#test_lock = 'Remote-Locked'
#test_heater_range = '5 W'
test_heater = '1 W'
#test_sensor = 'A'

class SR_PTC_10:
    #### Basic interaction functions
    def __init__(self):
        if test_flag != 'test':

            self.device_write('*CLS')
            answer = self.device_query('*TST?', 20)

        elif test_flag == 'test':
            pass

    def device_write(self, command):
        # MW bridge answers every command
        try:
            self.sock = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
            # timeout
            self.sock.settimeout(10) 
            self.sock.connect( (TCP_IP, TCP_PORT) )

            command_term = command + '\r\n'
            self.sock.sendto( command_term, (TCP_IP, TCP_PORT) )

            self.sock.shutdown(socket.SHUT_RDWR)
            self.sock.close()

            return data_raw
        except socket.error:
            general.message("No Connection")
            sys.exit()

    def device_query(self, command, bytes_to_recieve):
        try:
            self.sock = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
            # timeout
            self.sock.settimeout(10) 
            self.sock.connect( (TCP_IP, TCP_PORT) )

            command_term = command + '\r\n'
            self.sock.sendto( command_term, (TCP_IP, TCP_PORT) )
            data_raw, addr = self.sock.recvfrom( int(bytes_to_recieve) )

            self.sock.shutdown(socket.SHUT_RDWR)
            self.sock.close()

            return data_raw
        except socket.error:
            general.message("No Connection")
            sys.exit()

    #### device specific functions
    def tc_name(self):
        if test_flag != 'test':
            # b'name\r\n'
            answer = self.device_query('*IDN?', 100)
                # can be terminator
                return answer.decode()
        elif test_flag == 'test':
            answer = config['name']
            return answer

    def tc_temperature(self, channel):
        if test_flag != 'test':
            if channel == 'A':
                # terminator? channel name?
                answer = float(self.device_query('2A.value?', 10))
                return answer
            elif channel == 'B':
                answer = float(self.device_query('3A.value?', 10))
                return answer
            else:
                general.message("Invalid argument")
                sys.exit()
        
        elif test_flag == 'test':
            assert(channel == 'A' or channel == 'B'), "Incorrect channel"
            answer = test_temperature
            return answer

    def tc_setpoint(self, *temp):
        if test_flag != 'test':
            if len(temp) == 1:
                temp = float(temp[0])
                if temp <= temperature_max and temp >= temperature_min:
                    # turn on PID on channel 2A
                    self.device_write('2A.PID.Mode On')
                    self.device_write('2A.PID.Setpoint ' + str(temp))
                else:
                    general.message("Incorrect set point temperature")
                    sys.exit()
            elif len(temp) == 0:
                # terminator
                answer = float(self.device_query('2A.PID.Setpoint?'))
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

    def tc_heater_range(self, *heater):
        if test_flag != 'test':
            if  len(heater) == 1:
                hr = str(heater[0])
                if hr in heater_dict:
                    flag = heater_dict[hr]
                    if int(loop_config) in loop_list:
                        self.device_write("RANGE " + str(loop_config) + ',' + str(flag))
                    else:
                        general.message('Invalid loop')
                        sys.exit()
                else:
                    general.message("Invalid heater range")
                    sys.exit()
            elif len(heater) == 0:
                raw_answer = int(self.device_query("RANGE? " + str(loop_config)))
                answer = cutil.search_keys_dictionary(heater_dict, raw_answer)
                return answer
            else:
                general.message("Invalid argument")
                sys.exit()

        elif test_flag == 'test':                           
            if  len(heater) == 1:
                hr = str(heater[0])
                if hr in heater_dict:
                    flag = heater_dict[hr]
                    assert(int(loop_config) in loop_list), 'Invalid loop argument'
                else:
                    assert(1 == 2), "Invalid heater range"
            elif len(heater) == 0:
                answer = test_heater_range
                return answer
            else:
                assert(1 == 2), "Invalid heater range"

    def tc_heater_power(self):
        if test_flag != 'test':
            raw_answer = float(self.device_query('"Out 1.value?"'))
            answer = str(raw_answer) + ' W'
            return answer
          
        elif test_flag == 'test':
            answer = test_heater
            return answer

    def tc_command(self, command):
        if test_flag != 'test':
            self.device_write(command)
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