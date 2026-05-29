#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import gc
import sys
import pyvisa
import atomize.main.local_config as lconf
import atomize.device_modules.config.config_utils as cutil
import atomize.general_modules.general_functions as general


class BaseDevice:
    """Shared connection / transport plumbing for SCPI-style device modules.

    A subclass sets ``config_file`` and implements its device-specific
    functions; this base handles config loading, test-mode dispatch, opening
    the GPIB / RS-232 / Ethernet transport, the connection self-test, and the
    low-level ``device_write`` / ``device_query`` / ``close_connection`` calls.

    Subclass hooks:
      - ``config_file``       : name of the *_config.ini file (required)
      - ``gpib_query_wait``   : write->read settle delay for GPIB queries
      - ``_init_test_values()``: set the canned values returned in test mode
      - ``_self_test()``      : optional connection check after opening
                                (default no-op -- not every device supports one)
    """

    config_file = None
    gpib_query_wait = '50 ms'

    def __init__(self):
        # setting path to the *.ini file
        self.path_current_directory = lconf.load_config_device()
        self.path_config_file = os.path.join(self.path_current_directory, self.config_file)

        # configuration data
        self.config = cutil.read_conf_util(self.path_config_file)
        self.specific_parameters = cutil.read_specific_parameters(self.path_config_file)

        # test_flag is set from argv[1]; 'test' means no hardware is accessed
        if len(sys.argv) > 1:
            self.test_flag = sys.argv[1]
        else:
            self.test_flag = 'None'

        if self.test_flag != 'test':
            self._connect()
        elif self.test_flag == 'test':
            self._init_test_values()

    #### overridable hooks
    def _init_test_values(self):
        """Set the canned values returned by device functions in test mode."""
        pass

    def _self_test(self):
        """Optional connection check run right after the transport is opened.
        Default is a no-op: not every device supports a self-test (e.g. the
        SCPI ``*CLS`` / ``*TST?`` commands). Override it to add one -- see
        Lakeshore_335 for an example."""
        pass

    #### connection
    def _connect(self):
        self.status_flag = 1
        interface = self.config['interface']

        if interface == 'gpib':
            try:
                # Gpib driver may not be installed on the PC
                import Gpib
                self.device = Gpib.Gpib(self.config['board_address'], self.config['gpib_address'],
                                        timeout=self.config['timeout'])
                self._self_test()
            except BrokenPipeError:
                general.message(f"No connection {self.__class__.__name__}")
                self.status_flag = 0
                sys.exit()

        elif interface == 'rs232' or interface == 'ethernet':
            try:
                rm = pyvisa.ResourceManager()
                if interface == 'rs232':
                    self.device = rm.open_resource(self.config['serial_address'],
                        read_termination=self.config['read_termination'],
                        write_termination=self.config['write_termination'],
                        baud_rate=self.config['baudrate'], data_bits=self.config['databits'],
                        parity=self.config['parity'], stop_bits=self.config['stopbits'])
                else:
                    self.device = rm.open_resource(self.config['ethernet_address'])
                self.device.timeout = self.config['timeout']  # in ms
                self._self_test()
            except (pyvisa.VisaIOError, BrokenPipeError):
                general.message(f"No connection {self.__class__.__name__}")
                self.status_flag = 0
                sys.exit()

        else:
            general.message(f"Incorrect interface setting {self.__class__.__name__}")
            self.status_flag = 0
            sys.exit()

    def close_connection(self):
        if self.test_flag != 'test':
            self.status_flag = 0
            gc.collect()
        elif self.test_flag == 'test':
            pass

    #### transport
    def device_write(self, command):
        if self.status_flag == 1:
            command = str(command)
            self.device.write(command)
        else:
            general.message(f"No connection {self.__class__.__name__}")
            self.status_flag = 0
            sys.exit()

    def device_query(self, command):
        if self.status_flag == 1:
            if self.config['interface'] == 'gpib':
                self.device.write(command)
                general.wait(self.gpib_query_wait)
                answer = self.device.read()
            else:
                answer = self.device.query(command)
            return answer
        else:
            general.message(f"No connection {self.__class__.__name__}")
            self.status_flag = 0
            sys.exit()
