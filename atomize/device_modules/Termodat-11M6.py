#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import gc
import sys
import minimalmodbus
import atomize.device_modules.config.config_utils as cutil
import atomize.general_modules.general_functions as general

#### Inizialization
# setting path to *.ini file
path_current_directory = os.path.dirname(__file__)
path_config_file = os.path.join(path_current_directory, 'config','Termodat_11M6_config.ini')

# configuration data
config = cutil.read_conf_util(path_config_file)
modbus_parameters = cutil.read_modbus_parameters(path_config_file)

print(config)

# auxilary dictionaries
delay_channel_dict = {'1': 1, '2': 2, '3': 3, '4': 4, }

# Test run parameters
# These values are returned by the modules in the test run 
if len(sys.argv) > 1:
    test_flag = sys.argv[1]
else:
    test_flag = 'None'

test_temperature = 300
test_impedance = 'High Z'

class Termodat_11M6:
    #### Basic interaction functions
    def __init__(self):
        if test_flag != 'test':
            if config['interface'] == 'rs485':
                try:
                    self.status_flag = 1
                    self.device = minimalmodbus.Instrument(config['serial_address'], modbus_parameters[1])
                    self.device.mode = minimalmodbus.MODE_ASCII
                    #check there
                    self.device.serial.baurate = config['baudrate']
                    self.device.serial.bytesize = config['databits']
                    self.device.serial.parity = config['parity']
                    #check there
                    self.device.serial.stopbits = config['stopbits']
                    self.device.serial.timeout = config['timeout']/1000
                    try:
                        pass
                        # test should be here
                        #self.device_write('*CLS')

                    except serial.serialutil.SerialException:
                        general.message("No connection")
                        self.status_flag = 0
                        sys.exit()
                except serial.serialutil.SerialException:
                    general.message("No connection")
                    self.status_flag = 0
                    sys.exit()

            else:
                general.message("Incorrect interface setting")
                self.status_flag = 0
                sys.exit()

        elif test_flag == 'test':
            pass

    def close_connection(self):
        if test_flag != 'test':
            self.status_flag = 0;
            gc.collect()
        elif test_flag == 'test':
            pass

    def device_write_signed(self, register, value, decimals):
        if self.status_flag == 1:
            self.device.write_register(register, value, decimals, functioncode=6, signed=True)
        else:
            general.message("No Connection")
            self.status_flag = 0
            sys.exit()

    def device_read_signed(self, register, decimals):
        if self.status_flag == 1:
            answer = self.device.read_register(register, decimals, signed=True)
            return answer
        else:
            general.message("No Connection")
            self.status_flag = 0
            sys.exit()

    #### device specific functions
    def tc_name(self):
        if test_flag != 'test':
            answer = config['name']
                return answer
        elif test_flag == 'test':
            answer = config['name']
            return answer

    def tc_temperature(self, channel):
        if test_flag != 'test':
            if channel == '1':
                answer = float(self.device_read_signed(368, 1))
                return answer
            elif channel == '2':
                answer = float(self.device_read_signed(1392, 1))
                return answer
            elif channel == '3':
                answer = float(self.device_read_signed(2416, 1))
                return answer
            elif channel == '4':
                answer = float(self.device_read_signed(3440, 1))
                return answer
            else:
                general.message("Invalid argument")
                sys.exit()
        
        elif test_flag == 'test':
            assert(channel == '1' or channel == '2' or channel == '3' or channel == '4'), "Incorrect channel"
            answer = test_temperature
            return answer

    #TO DO
    def tc_setpoint(self, *temp):
        if test_flag != 'test':
            if int(loop_config) in loop_list:
                if len(temp) == 1:
                    temp = float(temp[0])
                    if temp <= temperature_max and temp >= temperature_min:
                        self.device.write('SETP ' + str(loop_config) + ',' + str(temp))
                    else:
                        general.message("Incorrect set point temperature")
                        sys.exit()
                elif len(temp) == 0:
                    answer = float(self.device_query('SETP? ' + str(loop_config)))
                    return answer   
                else:
                    general.message("Invalid argument")
                    sys.exit()
            else:
                general.message("Invalid loop")
                sys.exit()              

        elif test_flag == 'test':
            if len(temp) == 1:
                temp = float(temp[0])
                assert(temp <= temperature_max and temp >= temperature_min), 'Incorrect set point temperature is reached'
                assert(int(loop_config) in loop_list), 'Invalid loop argument'
            elif len(temp) == 0:
                answer = test_set_point
                return answer

def main():
    pass

if __name__ == "__main__":
    main()



#instrument = minimalmodbus.Instrument('/dev/ttyUSB0', 12)  # port name, slave address (in decimal)
#instrument.mode = minimalmodbus.MODE_ASCII
#MODE_RTU
#instrument.serial.baurate = 19200
#instrument.serial.bytesize = 8
#instrument.serial.parity = minimalmodbus.serial.PARITY_EVEN
#PARITY_NONE
#instrument.serial.stopbits = 1
#instrument.serial.timeout = 0.15

#temperature = instrument.read_register(384, 1, signed=True)  # Registernumber, number of decimals
#temperature = instrument.read_register(384+1024, 0, signed=False)  # Registernumber, number of decimals
#instrument.write_register(371, -10, 1, functioncode=6, signed=True)  # Registernumber, number of decimals

#temperature = instrument.read_register(369, 1, signed=True)  # Registernumber, number of decimals

#print(temperature)
