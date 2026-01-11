#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import gc
import sys
import pyvisa
from pyvisa.constants import StopBits, Parity
import atomize.main.local_config as lconf
import atomize.device_modules.config.config_utils as cutil
import atomize.general_modules.general_functions as general

class Gentec_Solo2:
    #### Basic interaction functions
    def __init__(self):

        #### Inizialization
        # setting path to *.ini file
        self.path_current_directory = lconf.load_config_device()
        self.path_config_file = os.path.join(self.path_current_directory, 'Gentec_Solo2_config.ini')

        # configuration data
        self.config = cutil.read_conf_util(self.path_config_file)
        self.specific_parameters = cutil.read_specific_parameters(self.path_config_file)

        # auxilary dictionaries
        self.offset_dict = {'Off': 0, 'On': 1, 'Undo': 2}
        self.energy_mode_dict = {'Off': 0, 'On': 1}
        self.analog_output_dict = {'Off': 0, 'On': 1}
        self.scale_dict =  {'1 pW': '1p', '3 pW': '3p', '10 pW': '10p', '30 pW': '30p', '100 pW': '100p', '300 pW': '300p', \
                            '1 nW': '1n', '3 nW': '3n', '10 nW': '10n', '30 nW': '30n', '100 nW': '100n', '300 nW': '300n',\
                            '1 uW': '1u', '3 uW': '3u', '10 uW': '10u', '30 uW': '30u', '100 uW': '100u', '300 uW': '300u',\
                            '1 mW': '1m', '3 mW': '3m', '10 mW': '10m', '30 mW': '30m', '100 mW': '100m', '300 mW': '300m',\
                            '1 W': '1', '3 W': '3', '10 W': '10', '30 W': '30', '100 W': '100', '300 W': '300',\
                            '1 kW': '1k', '3 kW': '3k', '10 kW': '10k', '30 kW': '30k', '100 kW': '100k', '300 kW': '300k',\
                            '1 MW': '1meg', '3 MW': '3meg', '10 MW': '10meg', '30 MW': '30meg', '100 MW': '100meg', '300 MW': '300meg'}
        self.helper_scale_list = [1, 3, 10, 30, 100, 300, 1000]

        # Ranges and limits
        self.min_wavelength = 193
        self.max_wavelength = 2100

        self.wavelength = 1064
        self.zero = 'Off'
        self.energy_mode = 'Off'
        self.analog_output = 'Off'
        self.max_attempt = 10

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
                        self.status_flag = 1
                        raw_answer = self.device_query('*STA')

                        ### Auto Scale setting
                        ### Attenuator setting
                        try:
                            self.device.read()
                            self.device.read()
                        except ( pyvisa.VisaIOError,  BrokenPipeError ):
                            pass
                        
                        self.wavelength = int((((raw_answer.split("\t")[7]).split(": "))[1]).split(" ")[0])
                        self.energy_mode = (((raw_answer.split("\t")[13]).split(": "))[1]).split(" ")[0]
                        self.analog_output = (((raw_answer.split("\t")[22]).split(": "))[1]).split(" ")[0]

                    except ( pyvisa.VisaIOError,  BrokenPipeError ):
                        self.status_flag = 0
                        general.message(f"No connection {self.__class__.__name__}")
                        sys.exit();
                except ( pyvisa.VisaIOError,  BrokenPipeError ):
                    general.message(f"No connection {self.__class__.__name__}")
                    self.status_flag = 0
                    sys.exit()

        elif self.test_flag == 'test':
            self.test_data = 0.001
            self.test_wavelength = 1064
            self.test_zero = 'Off'
            self.test_energy_mode = 'Off'
            self.test_analog_output = 'Off'

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

    def device_query(self, command):
        if self.status_flag == 1:
            answer = self.device.query(command)
            return answer
        else:
            general.message(f"No connection {self.__class__.__name__}")
            self.status_flag = 0
            sys.exit()

    #### device specific functions
    def laser_power_meter_name(self):
        if self.test_flag != 'test':
            answer = self.device_query('*VER')
            return answer
        elif self.test_flag == 'test':
            answer = self.config['name']
            return answer

    def laser_power_meter_head_name(self):
        """
        This command is used to query the model name of the current head.
        """
        if self.test_flag != 'test':
            answer = self.device_query('*HEA')
            return answer
        elif self.test_flag == 'test':
            answer = self.config['name']
            return f'Head name: {answer}'

    def laser_power_meter_get_data(self):
        if self.test_flag != 'test':

            for i in range (self.max_attempt):
                raw_answer = self.device_query('*NVU')
                if raw_answer == "New Data Available":
                    answer = float( self.device_query('*CVU').split(": ")[1] )
                    return answer
                else:
                    general.wait(f'{self.config["timeout"]} ms')

            general.message(f'New data is not available {self.__class__.__name__}')
            return 0

        elif self.test_flag == 'test':
            return self.test_data

    def laser_power_meter_wavelength(self, *wavelength):
        """
        Specifying zero as a wavelength or providing an out-of-bound value as a
        parameter restores the default settings.
        """
        if self.test_flag != 'test':
            
            if len(wavelength) == 1:
                wl = int(wavelength[0])
                self.wavelength = wl
                raw_answer = self.device_query('*SWA '+ str(wl))
                if raw_answer != "ACK":
                    general.message( raw_answer )
            elif len(wavelength) == 0:
                return f'Wavelength for correction: {self.wavelength} nm'

        elif self.test_flag == 'test':
            if len(wavelength) == 1:
                wl = int(wavelength[0])
                assert(wl <= self.max_wavelength and wl >= self.min_wavelength), \
                            f"Incorrect wavelength. The available range is from {self.min_wavelength} nm to {self.max_wavelength} nm"
                self.test_wavelength = wl
            elif len(wavelength) == 0:
                return f'Wavelength for correction: {self.test_wavelength} nm'
            else:
                assert( 1 == 2 ), "Invalid argument; wavelength: int"

    def laser_power_meter_zero_offset(self, *zero_mode):
        """
        This command subtracts the current value from all future measurements the moment the
        command is issued to set a new zero point.
        """
        if self.test_flag != 'test':
            if len(zero_mode) == 1:
                md = str(zero_mode[0])
                if md in self.offset_dict:
                    flag = self.offset_dict[md]
                    raw_answer = self.device_query("*EOA "+ str(flag))
                    self.zero = md
                    if raw_answer != 'ACK':
                        general.message( raw_answer )
            elif len(zero_mode) == 0:
                return f'Zero offset mode: {self.zero}'

        elif self.test_flag == 'test':
            if len(zero_mode) == 1:
                md = str(zero_mode[0])
                if md in self.offset_dict:
                    self.test_zero = md
                else:
                    assert(1 == 2), f"Incorrect zero mode; zero_mode: {list(self.offset_dict.keys())}"
            elif len(zero_mode) == 0:
                return f'Zero offset mode: {self.zero}'
            else:
                assert( 1 == 2 ), f"Incorrect argument; zero_mode: {list(self.offset_dict.keys())}"

    def laser_power_meter_analog_output(self, *analog_output):
        """
        This command is used to enable or disable the output of the current value on the analog port of 
        the device.
        """
        if self.test_flag != 'test':
            if len(analog_output) == 1:
                md = str(analog_output[0])
                if md in self.analog_output_dict:
                    flag = self.analog_output_dict[md]
                    raw_answer = self.device_query("*ANO "+ str(flag))
                    self.analog_output = md
                    if raw_answer != 'ACK':
                        general.message( raw_answer )
            elif len(analog_output) == 0:
                return f'Analog output: {self.analog_output}'

        elif self.test_flag == 'test':
            if len(analog_output) == 1:
                md = str(analog_output[0])
                if md in self.analog_output_dict:
                    self.test_analog_output = md
                else:
                    assert(1 == 2), f"Incorrect analog output; analog_output: {list(self.energy_mode_dict.keys())}"
            elif len(analog_output) == 0:
                return f'Analog output: {self.test_analog_output}'
            else:
                assert( 1 == 2 ), f"Incorrect argument; analog_output: {list(self.energy_mode_dict.keys())}"

    def laser_power_meter_energy_mode(self, *energy_mode):
        """
        This command is used to toggle Energy mode when using a wattmeter.
        """
        if self.test_flag != 'test':
            if len(energy_mode) == 1:
                md = str(energy_mode[0])
                if md in self.energy_mode_dict:
                    flag = self.energy_mode_dict[md]
                    raw_answer = self.device_query("*SCA "+ str(flag))
                    self.energy_mode = md
                    if raw_answer != 'ACK':
                        general.message( raw_answer )
            elif len(energy_mode) == 0:
                return f'Energy mode: {self.energy_mode}'

        elif self.test_flag == 'test':
            if len(energy_mode) == 1:
                md = str(energy_mode[0])
                if md in self.energy_mode_dict:
                    self.test_energy_mode = md
                else:
                    assert(1 == 2), f"Incorrect energy mode; mode: {list(self.energy_mode_dict.keys())}"
            elif len(energy_mode) == 0:
                return self.test_energy_mode
            else:
                assert( 1 == 2 ), f"Incorrect argument; mode: {list(self.energy_mode_dict.keys())}"

    def laser_power_meter_scale(self, scale):
        """
        This command is used to force the display of the current data into a specific range. The lower
        range is always zero, and the higher ranges can be found in the table below. The Auto scale
        applies the best scale for the current values in real time.
        """
        if self.test_flag != 'test':
            if scale == 0:
                raw_answer = self.device_query('*SSA Auto')
                if raw_answer == 'ACK':
                    general.message(f'Auto scaling is done {self.__class__.__name__}')
                else:
                    general.message( raw_answer )
            else:
                parsed_value, int_value, a = cutil.parse_pg(scale, self.helper_scale_list)
                val, val_key, b = cutil.search_and_limit_keys_dictionary( self.scale_dict, parsed_value, 1e-12, 1e6 )
                #general.message(f'ANSWER: {val}')

                raw_answer = self.device_query(f'*SSA {val}')
                if raw_answer == 'ACK':
                    if ( a == 1 ) or ( b == 1 ):
                        general.message(f"Desired scale cannot be set, the nearest available value of {val_key} is used")  
                else:
                    general.message( raw_answer )

        elif self.test_flag == 'test':
            if scale == 0:
                pass
            elif scale != 0:
                assert( isinstance(scale, str) ), "Incorrect argument; scale: 0 (auto-scale); int + [' pW', ' nW', ' uW', ' mW', ' W', ' kW'])"
                val, val_key, b = cutil.search_and_limit_keys_dictionary( self.scale_dict, \
                                    cutil.parse_pg(scale, self.helper_scale_list)[0], 1e-12, 1e6 )
                assert( val in self.scale_dict.values() ), "Incorrect argument; scale: 0 (auto-scale); int + [' pW', ' nW', ' uW', ' mW', ' W', ' kW'])"
            else:
                assert( 1 == 2 ), "Incorrect argument; scale: 0 (auto-scale); int + [' pW', ' nW', ' uW', ' mW', ' W', ' kW'])"

    def laser_power_meter_command(self, command):
        if self.test_flag != 'test':
            self.device_write(command)
        elif self.test_flag == 'test':
            pass

    def laser_power_meter_query(self, command):
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

