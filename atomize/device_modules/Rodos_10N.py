#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from socket import socket, AF_INET, SOCK_DGRAM
import atomize.main.local_config as lconf
import atomize.device_modules.config.config_utils as cutil
import atomize.general_modules.general_functions as general

# IP adress is 192.168.2.25; port is 8283; default is 192.168.1.20; login is admin; password ia admin; 
# echo -n "login password kN=c" > /dev/udp/IP/port
# c = 0 - turn off;
# c = 1 - turn on;
# c = 2 - pulse;

class Rodos_10N:

    def __init(self):
        #### Inizialization
        # setting path to *.ini file
        self.path_current_directory = lconf.load_config_device()
        self.path_config_file = os.path.join(self.path_current_directory, 'Rodos_10N_config.ini')

        # configuration data
        self.config = cutil.read_conf_util(self.path_config_file)
        self.specific_parameters = cutil.read_specific_parameters(self.path_config_file)

    def relay_turn_on(self, number):
        s = socket(AF_INET, SOCK_DGRAM)
        msg = ("admin admin k" + str(number) + "=1").encode('utf-8')
        s.sendto(msg, (self.config['ethernet_address'], 8283))
        general.message(f"Channel {number} turned on")

    def relay_turn_off(self, number):
        s = socket(AF_INET, SOCK_DGRAM)
        msg = ("admin admin k" + str(number) + "=0").encode('utf-8')
        s.sendto(msg, (self.config['ethernet_address'], 8283))
        general.message(f"Channel {number} turned off")

def main():
    pass

if __name__ == "__main__":
    main()

