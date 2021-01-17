#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from socket import socket, AF_INET, SOCK_DGRAM

# IP adress is 192.168.2.25; port is 8283; default is 192.168.1.20; login is admin; password ia admin; 
# echo -n "login password kN=c" > /dev/udp/IP/port
# c = 0 - turn off;
# c = 1 - turn on;
# c = 2 - pulse;

def turn_on(number):
	s = socket(AF_INET, SOCK_DGRAM)
	msg = ("admin admin k"+str(number)+"=1").encode('utf-8')
	s.sendto(msg, ('192.168.2.25', 8283))

def turn_off(number):
	s = socket(AF_INET, SOCK_DGRAM)
	msg = ("admin admin k"+str(number)+"=0").encode('utf-8')
	s.sendto(msg, ('192.168.2.25', 8283))

if __name__ == "__main__":
    main()

