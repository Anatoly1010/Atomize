#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#####################################################################
#                                                                   #
# spinapi.py                                                        #
#                                                                   #
# Copyright 2013, Christopher Billington, Philip Starkey            #
#                                                                   #
# This file is part of the spinapi project                          #
# (see https://bitbucket.org/cbillington/spinapi )                  #
# and is licensed under the Simplified BSD License.                 #
# See the LICENSE.txt file in the root of the project               #
# for the full license.                                             #
#                                                                   #
# https://github.com/chrisjbillington/spinapi                       #
#####################################################################


import sys
import os
import time
import platform
import ctypes
from ctypes import cdll
import atomize.general_modules.general_functions as general

class SpinAPI():

    def __init__(self):

        # Defines for different pb_instr instruction types
        #self.CONTINUE = 0
        #self.STOP = 1
        #self.LOOP = 2
        #self.END_LOOP = 3
        #self.JSR = 4
        #self.RTS = 5
        #self.BRANCH = 6
        #self.LONG_DELAY = 7
        #self.WAIT = 8

        # Defines for using different units of time
        #self.ns = 1.0
        #self.us = 1000.0
        #self.ms = 1000000.0
        #self.s  = 1000000000.0

        # Defines for start_programming
        #self.PULSE_PROGRAM  = 0

        self.path_to_file = os.path.abspath(os.path.realpath(os.path.dirname(__file__)))
        # Whether or not to tell the spincore library to write debug logfiles.
        self.debug = False

    def _checkloaded(self):
        try:    
            self.spinapi
        except AttributeError:
            arch = platform.architecture()
            if arch == ('64bit', 'WindowsPE'):
                libname = 'spinapi64.dll'
            elif arch == ('32bit', 'ELF'):
                libname = os.path.join(self.path_to_file, 'libspinapi.so')
            elif arch == ('64bit', 'ELF'):
                libname = os.path.join(self.path_to_file, 'libspinapi.so')

            try:
                self.spinapi = ctypes.cdll.LoadLibrary(libname)
                # enable debugging if it's switched on by the module global:
                self.spinapi.pb_set_debug(self.debug)
            except OSError:
                assert(1 == 2), "No libspinapi is found"

    def pb_get_firmware_id(self):
        self._checkloaded()
        self.spinapi.pb_get_firmware_id.restype = ctypes.c_uint
        return self.spinapi.pb_get_firmware_id()            

    def pb_set_debug(self):
        self._checkloaded()
        self.spinapi.pb_set_debug.restype = ctypes.c_int
        return self.spinapi.pb_set_debug(ctypes.c_int(self.debug))

    def pb_get_version(self):
        self._checkloaded()
        self.spinapi.pb_get_version.restype = ctypes.c_char_p
        return self.spinapi.pb_get_version()

    def pb_get_error(self):
        self._checkloaded()
        self.spinapi.pb_get_error.restype = ctypes.c_char_p
        return self.spinapi.pb_get_error()

    def pb_status_message(self):
        self._checkloaded()
        self.spinapi.pb_status_message.restype = ctypes.c_char_p
        message = self.spinapi.pb_status_message()
        return message
      
    def pb_read_status(self):
        self._checkloaded()
        self.spinapi.pb_read_status.restype = ctypes.c_uint32
        status = self.spinapi.pb_read_status()
        
        # convert to reversed binary string
        # convert to binary string, and remove 0b
        status = bin(status)[2:]
        # reverse string
        status = status[::-1]
        # pad to make sure we have enough bits!
        status = status + "0000"
        
        return {"stopped": bool(int(status[0])), "reset": bool(int(status[1])), \
        "running": bool(int(status[2])), "waiting": bool(int(status[3]))}

    def pb_count_boards(self):
        self._checkloaded()
        self.spinapi.pb_count_boards.restype = ctypes.c_int
        result = self.spinapi.pb_count_boards()
        if result == -1: raise RuntimeError(self.pb_get_error())  
        return result

    def pb_select_board(self, board_num):
        self._checkloaded()
        self.spinapi.pb_select_board.restype = ctypes.c_int
        result = self.spinapi.pb_select_board(ctypes.c_int(board_num))
        if result < 0: raise RuntimeError(self.pb_get_error())
        return result
                                   
    def pb_init(self):
        self._checkloaded()
        self.spinapi.pb_init.restype = ctypes.c_int
        result = self.spinapi.pb_init()
        if result != 0: raise RuntimeError(self.pb_get_error())
        #if result < 0:
        #    self.pb_init()
        #    self.pb_core_clock(500)

        #    self.pb_start_programming(0)
        #    self.pb_inst(14680064, 0, 0, 16)

        #    self.pb_inst(14680064, 1, 0, 16)

        #    self.pb_stop_programming()
        #    self.pb_reset()
        #    self.pb_start()
        #    self.pb_close()

        return result

    def pb_bypass_FF_fix(self, flag):
        self._checkloaded()
        self.spinapi.pb_bypass_FF_fix( ctypes.c_int(flag) )

    def pb_core_clock(self, clock_freq):
        self._checkloaded()
        self.spinapi.pb_core_clock.restype = ctypes.c_void_p
        self.spinapi.pb_core_clock(ctypes.c_double(clock_freq)) # returns void, so ignore return value.
                    
    def pb_start_programming(self, device):
        self._checkloaded()
        self.spinapi.pb_start_programming.restype = ctypes.c_int
        result = self.spinapi.pb_start_programming(ctypes.c_int(device))
        if result != 0: raise RuntimeError(self.pb_get_error())
        return result

    def pb_inst(self, flags, inst, inst_data, length):
        self._checkloaded()
        self.spinapi.pb_inst_pbonly.restype = ctypes.c_int
        if isinstance(flags, str) or isinstance(flags, bytes):
            flags = int(flags[::-1], 2)
        result = self.spinapi.pb_inst_pbonly(ctypes.c_uint32(flags), ctypes.c_int(inst),
                                         ctypes.c_int(inst_data), ctypes.c_double(length))
        if result < 0: raise RuntimeError(self.pb_get_error())
        return result

    def pb_stop_programming(self):
        self._checkloaded()
        self.spinapi.pb_stop_programming.restype = ctypes.c_int
        result = self.spinapi.pb_stop_programming()
        if result != 0: raise RuntimeError(self.pb_get_error())
        return result
        
    def pb_start(self):
        self._checkloaded()
        self.spinapi.pb_start.restype = ctypes.c_int
        result = self.spinapi.pb_start()
        if result != 0: raise RuntimeError(self.pb_get_error())
        return result
        
    def pb_stop(self):
        self._checkloaded()
        self.spinapi.pb_stop.restype = ctypes.c_int
        result = self.spinapi.pb_stop()
        if result != 0: raise RuntimeError(self.pb_get_error())
        return result
                
    def pb_close(self):
        self._checkloaded()
        self.spinapi.pb_close.restype = ctypes.c_int
        result = self.spinapi.pb_close()
        if result != 0: raise RuntimeError(self.pb_get_error())
        return result
        
    def pb_reset(self):
        self._checkloaded()
        self.spinapi.pb_reset.restype = ctypes.c_int
        result = self.spinapi.pb_reset()
        if result != 0: raise RuntimeError(self.pb_get_error())
        return result


def main():
    pass

if __name__ == "__main__":
    main()