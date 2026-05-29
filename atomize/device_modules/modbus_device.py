#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import gc
import sys
import serial
import minimalmodbus
import atomize.main.local_config as lconf
import atomize.device_modules.config.config_utils as cutil
import atomize.general_modules.general_functions as general


class ModbusDevice:
    """Shared connection / transport plumbing for Modbus (RS-485) device modules.

    Sibling to ``BaseDevice``: Modbus instruments talk over minimalmodbus's
    register interface (``read_register`` / ``write_register``), not the SCPI
    ``device_write`` / ``device_query`` string interface, so they get their own
    base. A subclass sets ``config_file`` and (if its register writes use a
    different Modbus function code) ``write_function_code``, then implements its
    device-specific functions on top of the register read/write helpers.

    Subclass hooks:
      - ``config_file``        : name of the *_config.ini file (required)
      - ``write_function_code``: Modbus function code for register writes
                                 (6 = single, 16 = multiple; default 16)
      - ``_init_test_values()``: set the canned values returned in test mode
    """

    config_file = None
    write_function_code = 16

    def __init__(self):
        # setting path to the *.ini file
        self.path_current_directory = lconf.load_config_device()
        self.path_config_file = os.path.join(self.path_current_directory, self.config_file)

        # configuration data
        self.config = cutil.read_conf_util(self.path_config_file)
        self.modbus_parameters = cutil.read_modbus_parameters(self.path_config_file)
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

    #### connection
    def _connect(self):
        self.status_flag = 1
        if self.config['interface'] == 'rs485':
            try:
                self.device = minimalmodbus.Instrument(self.config['serial_address'], self.modbus_parameters[1])
                self.device.mode = self.modbus_parameters[0]
                self.device.serial.baudrate = self.config['baudrate']
                self.device.serial.bytesize = self.config['databits']
                self.device.serial.parity = self.config['parity']
                self.device.serial.stopbits = self.config['stopbits']
                self.device.serial.timeout = self.config['timeout'] / 1000
            except serial.serialutil.SerialException:
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

    #### transport (register read/write)
    def device_write_unsigned(self, register, value, decimals):
        if self.status_flag == 1:
            self.device.write_register(register, value, decimals,
                                       functioncode=self.write_function_code, signed=False)
        else:
            general.message(f"No connection {self.__class__.__name__}")
            self.status_flag = 0
            sys.exit()

    def device_write_signed(self, register, value, decimals):
        if self.status_flag == 1:
            self.device.write_register(register, value, decimals,
                                       functioncode=self.write_function_code, signed=True)
        else:
            general.message(f"No connection {self.__class__.__name__}")
            self.status_flag = 0
            sys.exit()

    def device_read_unsigned(self, register, decimals):
        if self.status_flag == 1:
            return self.device.read_register(register, decimals, signed=False)
        else:
            general.message(f"No connection {self.__class__.__name__}")
            self.status_flag = 0
            sys.exit()

    def device_read_signed(self, register, decimals):
        if self.status_flag == 1:
            return self.device.read_register(register, decimals, signed=True)
        else:
            general.message(f"No connection {self.__class__.__name__}")
            self.status_flag = 0
            sys.exit()
