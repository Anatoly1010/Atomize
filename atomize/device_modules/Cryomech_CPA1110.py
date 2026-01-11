#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import gc
import sys
import serial
import minimalmodbus
import numpy as np
import atomize.main.local_config as lconf
import atomize.device_modules.config.config_utils as cutil
import atomize.general_modules.general_functions as general

class Cryomech_CPA1110:
    #### Basic interaction functions
    def __init__(self):

        #### Inizialization
        # setting path to *.ini file
        self.path_current_directory = lconf.load_config_device()
        self.path_config_file = os.path.join(self.path_current_directory, 'Cryomech_CPA1110_config.ini')

        # configuration data
        self.config = cutil.read_conf_util(self.path_config_file)
        self.modbus_parameters = cutil.read_modbus_parameters(self.path_config_file)

        # auxilary dictionaries
        self.state_dict = {'Idling': 0, 'Starting': 2, 'Running': 3, 'Stopping': 5, 'Error Lockout': 6, 'Error': 7, 
                           'Helium Cool Down': 8, 'Power related Error': 9, 'Recovered from Error': 15, }
        self.warning_dict = {'No warnings': 0, 'Coolant IN running High': 1, 'Coolant IN running Low': 2, 'Coolant OUT running High': 4, 
                             'Coolant OUT running Low': 8, 'Oil running High': 16, 'Oil running Low': 32, 'Helium running High': 64, 
                             'Helium running Low': 128, 'Low Pressure running High': 256, 'Low Pressure running Low': 512, 
                             'High Pressure running High': 1024, 'High Pressure running Low': 2048, 'Delta Pressure running High': 4096, 
                             'Delta Pressure running Low': 8192, 'Static Presure running High': 131072, 'Static Presure running Low': 262144, 
                             'Cold head motor Stall': 524288, }
        self.alarm_dict = {'No Errors': 0, 'Coolant IN High': 1, 'Coolant IN Low': 2, 'Coolant OUT High': 4, 
                             'Coolant OUT Low': 8, 'Oil High': 16, 'Oil Low': 32, 'Helium High': 64, 
                             'Helium Low': 128, 'Low Pressure High': 256, 'Low Pressure Low': 512, 
                             'High Pressure High': 1024, 'High Pressure Low': 2048, 'Delta Pressure High': 4096, 
                             'Delta Pressure Low': 8192, 'Motor Current Low': 16384, 'Three Phase Error': 32768,
                             'Power Supply Error': 65536, 'Static Presure High': 131072, 'Static Presure Low': 262144, }
        self.pressure_dict = {'PSI': 0, 'Bar': 1, 'KPA': 2, }
        self.temperature_dict = {'Fahrenheit': 0, 'Celsius': 1, 'Kelvin': 2, }

        # Ranges and limits
        ##self.temperature_max = 750

        # Test run parameters
        # These values are returned by the modules in the test run 
        if len(sys.argv) > 1:
            self.test_flag = sys.argv[1]
        else:
            self.test_flag = 'None'

        if self.test_flag != 'test':
            if self.config['interface'] == 'rs485':
                try:
                    self.status_flag = 1
                    self.device = minimalmodbus.Instrument(self.config['serial_address'], self.modbus_parameters[1])
                    self.device.mode = self.modbus_parameters[0]
                    #check there
                    self.device.serial.baudrate = self.config['baudrate']
                    self.device.serial.bytesize = self.config['databits']
                    self.device.serial.parity = self.config['parity']
                    #check there
                    self.device.serial.stopbits = self.config['stopbits']
                    self.device.serial.timeout = self.config['timeout'] / 1000
                    try:
                        pass
                        # test should be here
                        #self.device_write('*CLS')

                    except serial.serialutil.SerialException:
                        general.message(f"No connection {self.__class__.__name__}")
                        self.status_flag = 0
                        sys.exit()
                except serial.serialutil.SerialException:
                    general.message(f"No connection {self.__class__.__name__}")
                    self.status_flag = 0
                    sys.exit()

            else:
                general.message(f"Incorrect interface setting {self.__class__.__name__}")
                self.status_flag = 0
                sys.exit()

        elif self.test_flag == 'test':
            self.test_state = 'Idling'
            self.test_status_array = np.array( [ 33.4, 37.8, 45.1, 10.1, 189.1, 180.1, 221.2, 220.0, 40.1, 4.7, 1000.1 ] )
            self.test_warning_array = ['No warnings', 'No Errors']
            self.test_pressure_scale = 'PSI'
            self.test_temp_scale = 'Celsius'

    def close_connection(self):
        if self.test_flag != 'test':
            self.status_flag = 0
            gc.collect()
        elif self.test_flag == 'test':
            pass

    def device_write_unsigned(self, register, value, decimals):
        if self.status_flag == 1:
            # functioncode = 6 for writing to holding registers
            self.device.write_register(register, value, decimals, functioncode = 6, signed = False)
        else:
            general.message(f"No connection {self.__class__.__name__}")
            self.status_flag = 0
            sys.exit()

    def device_read_unsigned(self, register, decimals):
        if self.status_flag == 1:
            # functioncode = 4 for reading from input registers
            answer = self.device.read_register(register, decimals, functioncode = 4, signed = False)
            return answer
        else:
            general.message(f"No connection {self.__class__.__name__}")
            self.status_flag = 0
            sys.exit()
    
    def device_read_float(self, register):
        if self.status_flag == 1:
            # functioncode = 4 for reading from input registers
            # Cryomech uses BYTEORDER_LITTLE_SWAP (byteorder = 3) bit order for float values (two registers)
            answer = self.device.read_float(register, functioncode = 4, byteorder = 3)
            return answer
        else:
            general.message(f"No connection {self.__class__.__name__}")
            self.status_flag = 0
            sys.exit()

    #### device specific functions
    def cryogenic_refrigerator_name(self):
        if self.test_flag != 'test':
            answer = self.config['name']
            return answer
        elif self.test_flag == 'test':
            answer = self.config['name']
            return answer

    def cryogenic_refrigerator_state(self, *st):
        if self.test_flag != 'test':
            if len( st ) == 0:
                raw_answer = int(self.device_read_unsigned(1, 0))
                answer = cutil.search_keys_dictionary(self.state_dict, raw_answer)
                return answer

            elif len( st ) == 1:
                if st[0] == 'On':
                    self.device_write_unsigned(1, 1, 0)
                elif st[0] == 'Off':
                    self.device_write_unsigned(1, 255, 0)
        
        elif self.test_flag == 'test':
            if len( st ) == 0:
                answer = self.test_state
                return answer
            elif len( st ) == 1:
                assert(st[0] == 'On' or st[0] == 'Off'), "Incorrect state; state: ['On', 'Off']"
            else:
                assert(1 == 2), "Invalid argument; state: ['On', 'Off']"

    def cryogenic_refrigerator_status_data(self):
        if self.test_flag != 'test':
            status_array = np.zeros( 11 )
            # [               0,                1,        2,           3,            4,                5,
            # [ Coolant Temp In, Coolant Temp Out, Oil Temp, Helium Temp, Low Pressure, Low Pressure Ave,
            #             6,                 7,                  8,             9,              10 ]
            # High Pressure, High Pressure Ave, Delta Pressure Ave, Motor Current, Operation Hours ]
            status_array[0] =   round( self.device_read_float(7), 2 )
            status_array[1] =   round( self.device_read_float(9), 2 )
            status_array[2] =   round( self.device_read_float(11), 2 )
            status_array[3] =   round( self.device_read_float(13), 2 )
            status_array[4] =   round( self.device_read_float(15), 0 )
            status_array[5] =   round( self.device_read_float(17), 2 )
            status_array[6] =   round( self.device_read_float(19), 0 )
            status_array[7] =   round( self.device_read_float(21), 2 )
            status_array[8] =   round( self.device_read_float(23), 2 )
            status_array[9] =   round( self.device_read_float(25), 2 )
            status_array[10] =  round( self.device_read_float(27), 0 ) / 1000
            
            return status_array

        elif self.test_flag == 'test':
            return self.test_status_array

    def cryogenic_refrigerator_warning_data(self):
        if self.test_flag != 'test':
            # should be python list
            warning_array = []
            # [            0,           1 ]
            # [Warning State, Alarm State ]

            warn = cutil.search_keys_dictionary( self.warning_dict, int( abs( self.device_read_float( 3 ) ) ) ) 
            warning_array.append( warn )
            alarm = cutil.search_keys_dictionary( self.alarm_dict, int( abs( self.device_read_float( 5 ) ) ) ) 
            warning_array.append( alarm )
            
            return warning_array
        
        elif self.test_flag == 'test':
            return self.test_warning_array

    def cryogenic_refrigerator_pressure_scale(self):
        if self.test_flag != 'test':
            answer = cutil.search_keys_dictionary( self.pressure_dict, int(self.device_read_unsigned(29, 0)) ) 
            return answer
        
        elif self.test_flag == 'test':
            return self.test_pressure_scale
    
    def cryogenic_refrigerator_temperature_scale(self):
        if self.test_flag != 'test':
            answer = cutil.search_keys_dictionary( self.temperature_dict, int(self.device_read_unsigned(30, 0)) ) 
            return answer
        
        elif self.test_flag == 'test':
            return self.test_temp_scale

def main():
    pass

if __name__ == "__main__":
    main()
