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
temperature_max = 320
temperature_min = 0.3

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

            pass
            #self.device_write('*CLS')
            #general.wait('30 ms')
            #answer = self.device_query('*TST?', 1)
            #general.wait('30 ms')

        elif test_flag == 'test':
            pass

    def device_write(self, command):
        # MW bridge answers every command
        try:
            self.sock = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
            # timeout
            self.sock.settimeout(10) 
            self.sock.connect( (TCP_IP, TCP_PORT) )

            command_term = str(command) + '\r\n'
            self.sock.sendto( command_term.encode(), (TCP_IP, TCP_PORT) )

            self.sock.shutdown(socket.SHUT_RDWR)
            self.sock.close()

        except socket.error:
            general.message("No Connection")
            sys.exit()

    def device_query(self, command, bytes_to_recieve):
        try:
            self.sock = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
            # timeout
            self.sock.settimeout(10) 
            self.sock.connect( (TCP_IP, TCP_PORT) )

            command_term = str(command) + '\r\n'
            self.sock.sendto( command_term.encode(), (TCP_IP, TCP_PORT) )
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
            answer = self.device_query('*IDN?', 91)
            # can be terminator
            return answer.decode()

        elif test_flag == 'test':
            answer = 'Stanford Research PTC 10'
            return answer

    def tc_temperature(self, channel):
        if test_flag != 'test':
            ch = str(channel) + '.value?'
            try:
                answer = float(self.device_query(ch, 6))    
                return answer
            except ValueError:
                general.message('Incorrect channel name. Please, check')

        elif test_flag == 'test':
            #assert(channel == 'A' or channel == 'B'), "Incorrect channel"
            answer = test_temperature
            return answer

    def tc_setpoint(self, *temperature):
        if test_flag != 'test':
            if len(temperature) == 2:
                ch = str(temperature[0])
                temp = round(float(temperature[1]), 1)
                if temp <= temperature_max and temp >= temperature_min:
                    chan1 = str(ch) + '.PID.Mode On'
                    chan2 = str(ch) + '.PID.Setpoint ' + str(temp)
                    # turn on PID on channel 2A
                    self.device_write(chan1)
                    self.device_write(chan2)
                else:
                    general.message("Incorrect set point temperature")
                    sys.exit()
            elif len(temperature) == 1:
                ch = str(temperature[0])
                chan1 = str(ch) + '.PID.Setpoint?'
                # terminator
                # bytes?
                answer = float(self.device_query(chan1, 8))
                return answer   
            else:
                general.message("Invalid argument")
                sys.exit()
           
        elif test_flag == 'test':
            if len(temperature) == 2:
                ch = str(temperature[0])
                temp = float(temperature[1])
                assert(temp <= temperature_max and temp >= temperature_min), 'Incorrect set point temperature is reached'
            elif len(temperature) == 1:
                ch = str(temperature[0])
                answer = test_set_point
                return answer

    def tc_heater_power(self, channel):
        if test_flag != 'test':
            ch = str(channel) + '.value?'
            try:
                raw_answer = float(self.device_query(ch, 4))    
                return str(raw_answer) + ' W'
            except ValueError:
                general.message('Incorrect output channel name. Please, check')
          
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