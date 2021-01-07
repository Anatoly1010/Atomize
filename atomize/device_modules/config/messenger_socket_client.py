#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket

def message(text):
	sock = socket.socket()
	sock.connect(('localhost', 9091))
	sock.send(text.encode())
	sock.close()

if __name__ == "__main__":
    main()