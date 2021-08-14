#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import threading
from PyQt6 import QtCore

class Socket_server():
    """
    A class for creating and listening the socket server that connect errors messages from device modules
    and a dedicated text box in the main window of the programm.
    """
    def start_messenger_server(self, helper):
        """
        A function to create a socket server.
        This function should be run in another thread in order to not
        block the execution of the main programm.
        """
        sock = socket.socket()
        sock.bind(('', 9091))
        sock.listen(2)
        while True:
            client, addr = sock.accept()
            client_handler = threading.Thread(target=self.message, args=(helper, client), daemon = True).start()
    def message(self, helper, client):
        """
        A function to read a message from clients and emit a special signal with the message 
        to a helper class and finally to a dedicated text box in the main window of the programm.
        This function should be run in another thread in order to not
        block the execution of the main programm.
        """       
        data = client.recv(1024).decode()
        helper.changedSignal.emit(data)
        #print(data)
class Helper(QtCore.QObject):
    """
    A helper class to connect an event in another thread to a function in the main thread.
    """
    changedSignal = QtCore.pyqtSignal(str)

if __name__ == "__main__":
    main()