#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import gc
import sys
import time
import pyvisa
from pyvisa.constants import StopBits, Parity
import atomize.main.local_config as lconf
import atomize.device_modules.config.config_utils as cutil
import atomize.general_modules.general_functions as general

class Scientific_Instruments_SCM10:
    # A late reply left in the buffer after VI_ERROR_TMO desyncs every following query
    query_attempts = 2
    query_pause = 0.05          # s between attempts
    flush_timeout = 50          # ms, for the manual drain fallback
    flush_reads = 10            # cap on drain iterations

    #### Basic interaction functions
    def __init__(self):

        #### Inizialization
        # setting path to *.ini file
        self.path_current_directory = lconf.load_config_device()
        self.path_config_file = os.path.join(self.path_current_directory, 'Scientific_Instruments_SCM10_config.ini')

        # configuration data
        self.config = cutil.read_conf_util(self.path_config_file)
        #self.specific_parameters = cutil.read_specific_parameters(self.path_config_file)

        # auxilary dictionaries

        # Ranges and limits

        # Test run parameters
        # These values are returned by the modules in the test run 
        if len(sys.argv) > 1:
            self.test_flag = sys.argv[1]
        else:
            self.test_flag = 'None'

        if self.test_flag != 'test':
            if self.config['interface'] == 'rs232':
                try:
                    self.status_flag = 1
                    rm = pyvisa.ResourceManager()
                    self.device = rm.open_resource(self.config['serial_address'], read_termination=self.config['read_termination'],
                    write_termination=self.config['write_termination'], baud_rate=self.config['baudrate'],
                    data_bits=self.config['databits'], parity=self.config['parity'], stop_bits=self.config['stopbits'])
                    self.device.timeout = self.config['timeout'] # in ms
                    try:
                        # test should be here
                        answer = self.device_query('*IDN?')
                    except (pyvisa.VisaIOError, BrokenPipeError):
                        self.status_flag = 0
                        general.message(f"No connection {self.__class__.__name__}")
                        sys.exit()

                except (pyvisa.VisaIOError, BrokenPipeError):
                    general.message(f"No connection {self.__class__.__name__}")
                    self.status_flag = 0
                    sys.exit()

            elif self.config['interface'] == 'ethernet':
                try:
                    self.status_flag = 1
                    rm = pyvisa.ResourceManager()
                    self.device = rm.open_resource(self.config['ethernet_address'], read_termination=self.config['read_termination'],
                    write_termination=self.config['write_termination'])
                    self.device.timeout = self.config['timeout'] # in ms
                    try:
                        # test should be here
                        answer = self.device_query('*IDN?')
                    except (pyvisa.VisaIOError, BrokenPipeError):
                        general.message(f"No connection {self.__class__.__name__}")
                        self.status_flag = 0
                        sys.exit()

                except (pyvisa.VisaIOError, BrokenPipeError):
                    general.message(f"No connection {self.__class__.__name__}")
                    self.status_flag = 0
                    sys.exit()

            else:
                general.message(f"Incorrect interface setting {self.__class__.__name__}")
                self.status_flag = 0
                sys.exit()
            
        elif self.test_flag == 'test':
            self.test_temperature = 10.

    def close_connection(self):
        if self.test_flag != 'test':
            self.status_flag = 0;
            gc.collect()
        elif self.test_flag == 'test':
            pass

    def device_write(self, command):
        if self.status_flag == 1:
            command = str(command)
            self.device.write(command)
        else:
            general.message(f"No connection {self.__class__.__name__}")
            self.status_flag = 0
            sys.exit()

    def flush_input(self):
        # Best-effort, never raises: viClear, or a manual drain where pyvisa-py lacks it
        try:
            self.device.clear()
            return
        except Exception:
            pass

        try:
            old_timeout = self.device.timeout
        except Exception:
            return
        try:
            self.device.timeout = self.flush_timeout
            for _ in range( self.flush_reads ):
                try:
                    self.device.read_raw()
                except Exception:
                    break
        except Exception:
            pass
        finally:
            try:
                self.device.timeout = old_timeout
            except Exception:
                pass

    def device_query(self, command):
        if self.status_flag == 1:
            last_error = None
            for attempt in range( self.query_attempts ):
                try:
                    return self.device.query(command)
                except (pyvisa.VisaIOError, BrokenPipeError) as error:
                    last_error = error
                    # The last failure flushes too, so the next query starts clean
                    self.flush_input()
                    if attempt + 1 < self.query_attempts:
                        time.sleep( self.query_pause )
            raise last_error
        else:
            general.message(f"No connection {self.__class__.__name__}")
            self.status_flag = 0
            sys.exit()

    #### device specific functions
    def tc_name(self):
        if self.test_flag != 'test':
            answer = self.device_query('*IDN?')
            return answer
        elif self.test_flag == 'test':
            answer = self.config['name']
            return answer

    def tc_temperature(self, channel):
        if self.test_flag != 'test':
            if channel == '1':
                reply = self.device_query('T?')
                try:
                    answer = float(reply.split(' ')[1])
                except (IndexError, ValueError):
                    # Truncated or desynced reply; drop the rest and report what came back
                    self.flush_input()
                    raise ValueError(f"Unparsable temperature reply {reply!r} "
                                     f"from {self.__class__.__name__}")
                return answer

        elif self.test_flag == 'test':
            assert(channel == '1'), "Incorrect channel; channel: ['1']"
            answer = self.test_temperature
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