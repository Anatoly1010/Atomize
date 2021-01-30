#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import gc
import sys
import pyvisa
from pyvisa.constants import StopBits, Parity
import atomize.device_modules.config.config_utils as cutil
import atomize.general_modules.general_functions as general

#### Inizialization
# setting path to *.ini file
path_current_directory = os.path.dirname(__file__)
path_config_file = os.path.join(path_current_directory, 'config','Keysight_53230a_config.ini')

# configuration data
config = cutil.read_conf_util(path_config_file)
specific_parameters = cutil.read_specific_parameters(path_config_file)

# auxilary dictionaries
startarm_dic = {'Immediate': 'IMMediate', 'External': 'EXTernal',}
stoparm_dic = {'Immediate': 'IMMediate', 'Timer': 'TIME', 'Events': 'EVENts',}
gate_dic = {'External': 'EXTernal', 'Timer': 'TIME',}
scale_dict = {'s': 1, 'ms': 0.001, 'us': 0.000001, 'ns': 0.000000001,}
impedance_dict = {'1 M': 1000000, '50': 50, }

# Ranges and limits
min_gate_time = 0.00000001
max_gate_time = 10

# Test run parameters
# These values are returned by the modules in the test run 
if len(sys.argv) > 1:
    test_flag = sys.argv[1]
else:
    test_flag = 'None'

test_frequency = 10000
test_impedance = '1 M'
test_coupling = 'AC'
test_gate_stop_mode = 'Immediate'
test_gate_start_mode = 'Immediate'
test_gate = 'External'
test_gate_time = 0.1

class Keysight_53230a:
    #### Basic interaction functions
    def __init__(self):
        if test_flag != 'test':
            if config['interface'] == 'gpib':
                try:
                    import Gpib
                    self.status_flag = 1
                    self.device = Gpib.Gpib(config['board_address'], config['gpib_address'])
                    try:
                        # test should be here
                        self.device_write('*CLS')
                        self.device_write( "*SRE 0" )
                        self.device_write( "*ESE 0" )
                        self.device_write( "FORMAT ASC" )
                        
                        self.device_write('AUToscale')
                        self.status_flag = 1
                        # *TST? is very slow
                        #answer = int(self.device_query('*TST?'))
                        #if answer == 0:
                        #    self.status_flag = 1
                        #else:
                        #    general.message('During internal device test errors are found')
                        #    self.status_flag = 0
                        #    sys.exit()
                    except BrokenPipeError:
                        general.message("No connection")
                        self.status_flag = 0
                        sys.exit()
                except BrokenPipeError:
                    general.message("No connection")
                    self.status_flag = 0
                    sys.exit()

            elif config['interface'] == 'rs232':
                try:
                    self.status_flag = 1
                    rm = pyvisa.ResourceManager()
                    self.device = rm.open_resource(config['serial_address'], read_termination=config['read_termination'],
                    write_termination=config['write_termination'], baud_rate=config['baudrate'],
                    data_bits=config['databits'], parity=config['parity'], stop_bits=config['stopbits'])
                    self.device.timeout = config['timeout'] # in ms
                    try:
                        # test should be here
                        self.device_write('*CLS')
                        self.device_write( "*SRE 0" )
                        self.device_write( "*ESE 0" )
                        self.device_write( "FORMAT ASC" )
                        
                        self.device_write('AUToscale')
                        self.status_flag = 1
                        # *TST? is very slow
                        #answer = int(self.device_query('*TST?'))
                        #if answer == 0:
                        #    self.status_flag = 1
                        #else:
                        #    general.message('During internal device test errors are found')
                        #    self.status_flag = 0
                        #    sys.exit()
                    except pyvisa.VisaIOError:
                        self.status_flag = 0
                        general.message("No connection")
                        sys.exit()
                    except BrokenPipeError:
                        general.message("No connection")
                        self.status_flag = 0
                        sys.exit()
                except pyvisa.VisaIOError:
                    general.message("No connection")
                    self.status_flag = 0
                    sys.exit()
                except BrokenPipeError:
                    general.message("No connection")
                    self.status_flag = 0
                    sys.exit()

            elif config['interface'] == 'ethernet':
                try:
                    self.status_flag = 1
                    rm = pyvisa.ResourceManager()
                    self.device = rm.open_resource(config['ethernet_address'])
                    self.device.timeout = config['timeout'] # in ms
                    try:
                        # test should be here
                        self.device_write('*CLS')
                        self.device_write( "*SRE 0" )
                        self.device_write( "*ESE 0" )
                        self.device_write( "FORMAT ASC" )
                        
                        self.device_write('AUToscale')
                        self.status_flag = 1
                        # *TST? is very slow
                        #answer = int(self.device_query('*TST?'))
                        #if answer == 0:
                        #    self.status_flag = 1
                        #else:
                        #    general.message('During internal device test errors are found')
                        #    self.status_flag = 0
                        #    sys.exit()
                    except pyvisa.VisaIOError:
                        self.status_flag = 0
                        general.message("No connection")
                        sys.exit()
                    except BrokenPipeError:
                        general.message("No connection")
                        self.status_flag = 0
                        sys.exit()ag = 0
                        sys.exit()
                except pyvisa.VisaIOError:
                    general.message("No connection")
                    self.status_flag = 0
                    sys.exit()
                except BrokenPipeError:
                    general.message("No connection")
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

    def device_write(self, command):
        if self.status_flag == 1:
            command = str(command)
            self.device.write(command)
        else:
            general.message("No Connection")
            self.status_flag = 0
            sys.exit()

    def device_query(self, command):
        if self.status_flag == 1:
            if config['interface'] == 'gpib':
                self.device.write(command)
                general.wait('50 ms')
                answer = self.device.read().decode()
                return answer
            elif config['interface'] == 'rs232':
                answer = self.device.query(command)
                return answer
            elif config['interface'] == 'ethernet':
                answer = self.device.query(command)
                return answer
        else:
            general.message("No Connection")
            self.status_flag = 0
            sys.exit()

    #### Device specific functions
    def freq_counter_name(self):
        if test_flag != 'test':
            answer = self.device_query('*IDN?')
            return answer
        elif test_flag == 'test':
            answer = config['name']
            return answer

    def freq_counter_frequency(self, channel):
        if test_flag != 'test':
            if channel == 'CH1':
                # make sure that the channel is correct
                self.device_write("FUNC 'FREQ 1'")
                general.wait('30 ms')
                answer = float(self.device_query('READ?'))/1000
                self.device_write('INITiate')
                return answer
            elif channel == 'CH2':
                # make sure that the channel is correct
                self.device_write("FUNC 'FREQ 2'")
                general.wait('30 ms')
                answer = float(self.device_query('READ?'))/1000
                self.device_write('INITiate')
                return answer
            elif channel == 'CH3':
                # make sure that the channel is correct
                self.device_write("FUNC 'FREQ 3'")
                general.wait('30 ms')
                answer = float(self.device_query('READ?'))/1000
                self.device_write('INITiate')
                return answer
            else:
                general.message('Invalid argument')
                sys.exit()

        elif test_flag == 'test':
            assert(channel == 'CH1' or channel == 'CH2' or channel == 'CH3'), 'Invalid channel'
            answer = test_frequency
            return answer

    def freq_counter_impedance(self, *impedance):
        if test_flag != 'test':
            if len(impedance) == 2:
                ch = str(impedance[0])
                imp = str(impedance[1])
                if imp in impedance_dict:
                    flag = impedance_dict[imp]
                    if ch == 'CH1':
                        self.device_write("INPut1:IMPedance " + str(imp))
                    elif ch == 'CH2':
                        self.device_write("INPut2:IMPedance " + str(imp))
                    elif ch == 'CH3':
                        general.message('The impedance for CH3 is only 50 Ohm')
            elif len(impedance) == 1:
                ch = str(impedance[0])
                if ch == 'CH1':
                    raw_answer = float(self.device_query("INPut1:IMPedance?"))
                    answer = cutil.search_keys_dictionary(impedance_dict, raw_answer)
                    return answer
                elif ch == 'CH2':
                    raw_answer = float(self.device_query("INPut1:IMPedance?"))
                    answer = cutil.search_keys_dictionary(impedance_dict, raw_answer)
                    return answer
                elif ch == 'CH3':
                    answer = '50'
                    general.message('The impedance for CH3 is only 50 Ohm')
                    return answer
            else:
                general.message('Invalid argument')
                sys.exit()

        elif test_flag == 'test':
            if len(impedance) == 2:
                ch = str(impedance[0])
                imp = str(impedance[1])
                assert(ch == 'CH1' or ch == 'CH2' or ch == 'CH3'), 'Invalid channel is given'
                assert(imp in impedance_dict), 'Invalid impedance is given'
            elif len(impedance) == 1:
                ch = str(impedance[0])
                assert(ch == 'CH1' or ch == 'CH2' or ch == 'CH3'), 'Invalid channel is given'
                answer = test_impedance
                return answer
            else:
                assert(1 == 2), "Incorrect impedance argument"

    def freq_counter_coupling(self, *coupling):
        if test_flag != 'test':
            if len(coupling) == 2:
                ch = str(coupling[0])
                cpl = str(coupling[1])
                if ch == 'CH1':
                    self.device_write("INPut1:COUPling " + str(cpl))
                elif ch == 'CH2':
                    self.device_write("INPut2:COUPling " + str(cpl))
                elif ch == 'CH3':
                    general.message('The coupling for CH3 is only AC')
            elif len(coupling) == 1:
                ch = str(coupling[0])
                if ch == 'CH1':
                    answer = str(self.device_query("INPut1:COUPling?"))
                    return answer
                elif ch == 'CH2':
                    answer = str(self.device_query("INPut2:COUPling?"))
                    return answer
                elif ch == 'CH3':
                    answer = 'AC'
                    general.message('The coupling for CH3 is only AC')
                    return answer
            else:
                general.message('Invalid argument')
                sys.exit()

        elif test_flag == 'test':
            if len(coupling) == 2:
                ch = str(coupling[0])
                cpl = str(coupling[1])
                assert(ch == 'CH1' or ch == 'CH2' or ch == 'CH3'), 'Invalid channel is given'
                assert(cpl == 'AC' or cpl == 'DC'), 'Invalid coupling is given'
            elif len(coupling) == 1:
                ch = str(coupling[0])
                assert(ch == 'CH1' or ch == 'CH2' or ch == 'CH3'), 'Invalid channel is given'
                answer = test_coupling
                return answer
            else:
                assert(1 == 2), "Incorrect coupling argument"

    def freq_counter_stop_mode(self, *mode):
        if test_flag != 'test':
            if  len(mode) == 1:
                md = str(mode[0])
                if md in stoparm_dic:
                    flag = stoparm_dic[md]
                    self.device_write("GATE:STARt:DELay:SOURce "+ str(flag))
                else:
                    general.message("Invalid stop arm mode")
                    sys.exit()
            elif len(mode) == 0:
                raw_answer = str(self.device_query('GATE:STARt:DELay:SOURce?'))
                answer = cutil.search_keys_dictionary(stoparm_dic, raw_answer)
                return answer
            else:
                general.message("Invalid argument")
                sys.exit()

        elif test_flag == 'test':
            if  len(mode) == 1:
                md = str(mode[0])
                if md in stoparm_dic:
                    flag = stoparm_dic[md]
                else:
                    assert(1 == 2), "Invalid stop arm mode"
            elif len(mode) == 0:
                answer = test_gate_stop_mode
                return answer
            else:
                assert(1 == 2), "Invalid argument"

    def freq_counter_start_mode(self, *mode):
        if test_flag != 'test':
            if  len(mode) == 1:
                md = str(mode[0])
                if md in startarm_dic:
                    flag = startarm_dic[md]
                    self.device_write("GATE:STARt:SOURce "+ str(flag))
                else:
                    general.message("Invalid start arm mode")
                    sys.exit()
            elif len(mode) == 0:
                raw_answer = str(self.device_query('GATE:STARt:SOURce?'))
                answer = cutil.search_keys_dictionary(startarm_dic, raw_answer)
                return answer
            else:
                general.message("Invalid argument")
                sys.exit()

        elif test_flag == 'test':
            if  len(mode) == 1:
                md = str(mode[0])
                if md in startarm_dic:
                    flag = startarm_dic[md]
                else:
                    assert(1 == 2), "Invalid start arm mode"
            elif len(mode) == 0:
                answer = test_gate_start_mode
                return answer
            else:
                assert(1 == 2), "Invalid argument"

    def freq_counter_gate_mode(self, *mode):
        if test_flag != 'test':
            if  len(mode) == 1:
                md = str(mode[0])
                if md in gate_dic:
                    flag = gate_dic[md]
                    self.device_write("FREQuency:GATE:SOURce "+ str(flag))
                else:
                    general.message("Invalid gate mode")
                    sys.exit()
            elif len(mode) == 0:
                raw_answer = str(self.device_query('FREQuency:GATE:SOURce?'))
                answer = cutil.search_keys_dictionary(gate_dic, raw_answer)
                return answer
            else:
                general.message("Invalid argument")
                sys.exit()

        elif test_flag == 'test':
            if  len(mode) == 1:
                md = str(mode[0])
                if md in gate_dic:
                    flag = gate_dic[md]
                else:
                    assert(1 == 2), "Invalid gate mode"
            elif len(mode) == 0:
                answer = test_gate
                return answer
            else:
                assert(1 == 2), "Invalid argument"

    def freq_counter_gate_time(self, *time):
        if test_flag != 'test':
            if len(time) == 1:
                temp = time[0].split(" ")
                tb = float(temp[0])
                scaling = temp[1]
                if scaling in scale_dict:
                    coef = scale_dict[scaling]
                    if tb*coef >= min_gate_time and tb*coef <= max_gate_time:
                        self.device_write("GATE:STARt:DELay:TIME "+ str(tb*coef))
                    else:
                        general.message("Incorrect gate time range")
                        sys.exit()
                else:
                    general.message("Incorrect gate time")
                    sys.exit()
            elif len(time) == 0:
                answer = float(self.device_query("GATE:STARt:DELay:TIME?"))
                return answer
            else:
                general.message("Invalid argument")
                sys.exit()

        elif test_flag == 'test':
            if len(time) == 1:
                temp = time[0].split(" ")
                tb = float(temp[0])
                scaling = temp[1]
                if scaling in scale_dict:
                    coef = scale_dict[scaling]
                    assert(tb*coef >= min_gate_time and tb*coef <= max_gate_time), "Incorrect gate time range"
                else:
                    assert(1 == 2), "Incorrect gate time"
            elif len(time) == 0:
                answer = test_gate_time
                return answer
            else:
                assert(1 == 2), "Invalid argument"

    def freq_counter_command(self, command):
        if test_flag != 'test':
            self.device_write(command)
        elif test_flag == 'test':
            pass

    def freq_counter_query(self, command):
        if test_flag != 'test':
            answer = self.device_query(command)
            return answer
        elif test_flag == 'test':
            answer = None
            return answer

def main():
    pass

if __name__ == "__main__":
    main()