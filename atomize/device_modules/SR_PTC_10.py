#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import struct
import socket
import atomize.device_modules.config.config_utils as cutil
import atomize.general_modules.general_functions as general

class SR_PTC_10:
    #### Basic interaction functions
    def __init__(self):

        #### Inizialization
        # setting path to *.ini file
        self.path_current_directory = os.path.dirname(__file__)
        self.path_config_file = os.path.join(self.path_current_directory, 'config','SR_PTC_10_config.ini')

        # configuration data
        #config = cutil.read_conf_util(self.path_config_file)
        self.specific_parameters = cutil.read_specific_parameters(self.path_config_file)

        # auxilary dictionaries
        #heater_dict = {'50 W': 3, '5 W': 2, '0.5 W': 1, 'Off': 0,};
        #lock_dict = {'Local-Locked': 0, 'Remote-Locked': 1, 'Local-Unlocked': 2, 'Remote-Unlocked': 3,}
        #loop_list = [1, 2]
        #sens_dict = {0: 'None', 1: 'A', 2: 'B',}

        # Ranges and limits
        self.UDP_IP = str(self.specific_parameters['udp_ip'])
        self.UDP_PORT = int(self.specific_parameters['udp_port'])
        self.TCP_IP = str(self.specific_parameters['tcp_ip'])
        self.TCP_PORT = int(self.specific_parameters['tcp_port'])
        self.temperature_max = 320
        self.temperature_min = 0.3

        # Test run parameters
        # These values are returned by the modules in the test run 
        if len(sys.argv) > 1:
            self.test_flag = sys.argv[1]
        else:
            self.test_flag = 'None'

        if self.test_flag != 'test':
            
            self.device_write('*CLS')
            answer = self.device_query('*TST?', 100)

        elif self.test_flag == 'test':
            self.test_temperature = 200.
            self.test_set_point = 298.
            self.test_heater = '1 W'

    def device_write(self, command):
        # MW bridge answers every command
        try:
            self.sock = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
            # timeout
            self.sock.settimeout(2) 
            self.sock.connect( (self.TCP_IP, self.TCP_PORT) )

            command_term = str(command) + '\r\n'
            self.sock.sendto( command_term.encode(), (self.TCP_IP, self.TCP_PORT) )

            self.sock.shutdown(socket.SHUT_RDWR)
            self.sock.close()

        except socket.error:
            general.message("No Connection")
            sys.exit()

    def device_query(self, command, bytes_to_recieve):
        try:
            self.sock = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
            # timeout
            self.sock.settimeout(2) 
            self.sock.connect( (self.TCP_IP, self.TCP_PORT) )

            command_term = str(command) + '\r\n'
            self.sock.sendto( command_term.encode(), (self.TCP_IP, self.TCP_PORT) )
            data_raw, addr = self.sock.recvfrom( int(bytes_to_recieve) )

            self.sock.shutdown(socket.SHUT_RDWR)
            self.sock.close()

            return data_raw
        except socket.error:
            general.message("No Connection")
            sys.exit()

    #### device specific functions
    def tc_name(self):
        if self.test_flag != 'test':
            # b'name\r\n'
            answer = self.device_query('*IDN?', 100)
            # can be terminator
            return answer.decode()

        elif self.test_flag == 'test':
            answer = 'Stanford Research PTC 10'
            return answer

    def tc_temperature(self, channel):
        if self.test_flag != 'test':
            ch = str(channel) + '.value?'
            try:
                answer = float(self.device_query(ch, 50))
                return answer
            except ValueError:
                general.message('Incorrect channel name. Please, check')

        elif self.test_flag == 'test':
            #assert(channel == 'A' or channel == 'B'), "Incorrect channel"
            answer = self.test_temperature
            return answer

    def tc_setpoint(self, *temperature):
        if self.test_flag != 'test':
            if len(temperature) == 2:
                ch = str(temperature[0])
                temp = round(float(temperature[1]), 1)
                if temp <= self.temperature_max and temp >= self.temperature_min:
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
                answer = float(self.device_query(chan1, 50))
                return answer   
            else:
                general.message("Invalid argument")
                sys.exit()
           
        elif self.test_flag == 'test':
            if len(temperature) == 2:
                ch = str(temperature[0])
                temp = float(temperature[1])
                assert(temp <= self.temperature_max and temp >= self.temperature_min), 'Incorrect set point temperature is reached'
            elif len(temperature) == 1:
                ch = str(temperature[0])
                answer = self.test_set_point
                return answer

    def tc_heater_power(self, channel):
        if self.test_flag != 'test':
            ch = str(channel) + '.value?'
            try:
                raw_answer = float(self.device_query(ch, 50))
                return str(raw_answer) + ' W'
            except ValueError:
                general.message('Incorrect output channel name. Please, check')


        elif self.test_flag == 'test':
            answer = self.test_heater
            return answer

    def tc_command(self, command):
        if self.test_flag != 'test':
            self.device_write(command)
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