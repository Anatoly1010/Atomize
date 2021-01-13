#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket

def message(*text):
	sock = socket.socket()
	sock.connect(('localhost', 9091))
	if len(text)==1:
		sock.send(str(text[0]).encode())
		sock.close()
	else:
		sock.send(str(text).encode())
		sock.close()

if __name__ == "__main__":
    main()