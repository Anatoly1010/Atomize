#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket

def message(text):
	sock = socket.socket()
	sock.connect(('localhost', 9090))
	sock.send(text.encode())
	sock.close()
