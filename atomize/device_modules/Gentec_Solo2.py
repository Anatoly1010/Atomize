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
        self.scale_dict = {'pW': 'p', 'nW': 'n', 'uW': 'u', 'mW': 'm', 'W': '', 'kW': 'k', 'MW': 'meg'}
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
                    general.wait(f'{self.config['timeout']} ms')

            general.message('New data is not available')
            return 0

        elif self.test_flag == 'test':
            return self.test_data

    def laser_power_meter_set_wavelength(self, *wavelength):
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
                            f"Incorrect wavelength for correction is used. The available range is: {self.min_wavelength} - {self.max_wavelength} nm"
                self.test_wavelength = wl
            elif len(wavelength) == 0:
                return f'Wavelength for correction: {self.test_wavelength} nm'
            else:
                assert( 1 == 2 ), "Invalid Argument."

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
                    assert(1 == 2), f"Incorrect zero mode is used. The only available options are: {self.offset_dict}"
            elif len(zero_mode) == 0:
                return f'Zero offset mode: {self.zero}'

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
                    assert(1 == 2), f"Incorrect analog output is used. The only available options are: {self.analog_output_dict}"
            elif len(analog_output) == 0:
                return f'Analog output: {self.test_analog_output}'

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
                    assert(1 == 2), f"Incorrect energy mode is used. The only available options are: {self.energy_mode_dict}"
            elif len(energy_mode) == 0:
                return self.test_energy_mode

    def laser_power_meter_scale(self, scale):
        """
        This command is used to force the display of the current data into a specific range. The lower
        range is always zero, and the higher ranges can be found in the table below. The Auto scale
        applies the best scale for the current values in real time.
        """
        if self.test_flag != 'test':
            a = 0
            raw_answer = self.device_query('*SSA Auto')
            if raw_answer == 'ACK':
                general.message(f'Auto scaling is done {self.__class__.__name__}')
            else:
                general.message( raw_answer )

            temp = scale[0].split(' ')
            if float(temp[0]) < 1 and temp[1] == 'pW':
                raw_answer = self.device_query(f'*SSA 1p')
                if raw_answer == 'ACK':
                    send.message("Desired scale cannot be set, the nearest available value of 1 pW is used")
                else:
                    general.message( raw_answer )
            elif float(temp[0]) > 300 and temp[1] == 'kW':
                raw_answer = self.device_query(f'*SSA 300k')
                if raw_answer == 'ACK':
                    general.message("Desired scale cannot be set, the nearest available value of 300 kW is used")
                else:
                    general.message( raw_answer )
            else:
                number_scale = min(self.helper_scale_list, key=lambda x: abs(x - int(temp[0])))
                if int(number_scale) == 1000 and temp[1] == 'pW':
                    number_scale = 1
                    temp[1] = 'nV'
                elif int(number_scale) == 1000 and temp[1] == 'nV':
                    number_scale = 1
                    temp[1] = 'uW'
                elif int(number_scale) == 1000 and temp[1] == 'uW':
                    number_scale = 1
                    temp[1] = 'mW'
                elif int(number_scale) == 1000 and temp[1] == 'mW':
                    number_scale = 1
                    temp[1] = 'W'
                elif int(number_scale) == 1000 and temp[1] == 'W':
                    number_scale = 1
                    temp[1] = 'kW'

                if int(number_scale) != int(temp[0]):
                    a = 1

                scale_dim = temp[1]
                flag = self.scale_dict[scale_dim]
                raw_answer = self.device_query(f'*SSA {number_scale}{flag}')
                if raw_answer == 'ACK':
                    if a == 1:
                        general.message(f"Desired scale cannot be set, the nearest available value of {number_scale} {temp[1]} is used")  
                else:
                    general.message( raw_answer )

        elif self.test_flag == 'test':
            if  len(scale) == 1:

                temp = scale[0].split(' ')
                number_scale = min(self.helper_scale_list, key=lambda x: abs(x - int(temp[0])))
                if int(number_scale) == 1000 and temp[1] == 'pW':
                    number_scale = 1
                    temp[1] = 'nV'
                elif int(number_scale) == 1000 and temp[1] == 'nV':
                    number_scale = 1
                    temp[1] = 'uW'
                elif int(number_scale) == 1000 and temp[1] == 'uW':
                    number_scale = 1
                    temp[1] = 'mW'
                elif int(number_scale) == 1000 and temp[1] == 'mW':
                    number_scale = 1
                    temp[1] = 'W'
                elif int(number_scale) == 1000 and temp[1] == 'W':
                    number_scale = 1
                    temp[1] = 'kW'

                scale_dim = temp[1]
                assert( scale_dim in self.scale_dict ), "Incorrect dimension is used.\
                                The only available options are [pW, nW, uW, mW, W, kW]"

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

