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
path_config_file = os.path.join(path_current_directory, 'config','Agilent_53181a_config.ini')

# configuration data
config = cutil.read_conf_util(path_config_file)
specific_parameters = cutil.read_specific_parameters(path_config_file)

# auxilary dictionaries
startarm_dic = {'Im': 'IMMediate', 'Ext': 'EXTernal',}
stoparm_dic = {'Im': 'IMMediate', 'Ext': 'EXTernal', 'Tim': 'TIMer', 'Dig': 'DIGits',}
scale_dict = {'ks': 1000,' s': 1, 'ms': 0.001,}
scalefreq_dict = {'GHz': 1000000000, 'MHz': 1000000, 'kHz': 1000, 'Hz': 1, }

# Ranges and limits
min_digits = 3
max_digits = 15
min_gate_time = 0.001
max_gate_time = 1000

# Test run parameters
# These values are returned by the modules in the test run 
if len(sys.argv) > 1:
    test_flag = sys.argv[1]
else:
    test_flag = 'None'

test_frequency = 10000
test_impedance = 1000000
test_coupling = 'AC'
test_gate_stop_mode = 'Im'
test_gate_start_mode = 'Im'
test_digits = 10
test_gate_time = 0.1
test_ratio = 1
test_expect_freq = 10000
test_period = 10

class Agilent_53181a:
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
                        answer = int(self.device_query('*TST?'))
                        if answer == 0:
                            self.status_flag = 1
                        else:
                            general.message('During internal device test errors are found')
                            self.status_flag = 0
                            sys.exit()
                    except BrokenPipeError:
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
                raw_answer = self.device.read()
                answer = raw_answer.decode()
                return answer
            else:
                general.message('Incorrect interface setting')
                self.status_flag = 0
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
                answer = float(self.device_query(':MEASURE:FREQ? (@1)'))
                return answer
            elif channel == 'CH2':
                answer = float(self.device_query(':MEASURE:FREQ? (@2)'))
                return answer
            else:
                general.message('Invalid argument')
                sys.exit()

        elif test_flag == 'test':
            assert(channel == 'CH1' or channel == 'CH2'), 'Invalid channel'
            answer = test_frequency
            return answer

    def freq_counter_impedance(self, *impedance):
        if test_flag != 'test':
            if len(impedance) == 2:
                ch = str(impedance[0])
                imp = str(impedance[1])
                if imp == '1 M':
                    imp = '1.0E6'
                elif imp == '50':
                    imp = '50'
                if ch == 'CH1':
                    self.device_write(":INPut1:IMPedance " + str(imp))
                elif ch == 'CH2':
                    general.message('The impedance for CH3 is only 50 Ohm')
                elif ch == 'CH3':
                    general.message('Invalid channel')
            elif len(impedance) == 1:
                ch = str(impedance[0])
                if ch == 'CH1':
                    answer = float(self.device_query(":INPut1:IMPedance?"))
                    return answer
                elif ch == 'CH2':
                    answer = float(self.device_query(":INPut2:IMPedance?"))
                    return answer
                elif ch == 'CH3':
                    general.message('Invalid channel')
            else:
                general.message('Invalid argument')
                sys.exit()

        elif test_flag == 'test':
            if len(impedance) == 2:
                ch = str(impedance[0])
                imp = str(impedance[1])
                assert(ch == 'CH1' or ch == 'CH2'), 'Invalid channel is given'
                assert(cpl == '1 M' or cpl == '50'), 'Invalid impedance is given'
            elif len(impedance) == 1:
                ch = str(impedance[0])
                assert(ch == 'CH1' or ch == 'CH2'), 'Invalid channel is given'
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
                    self.device_write(":INPut1:COUPling " + str(cpl))
                elif ch == 'CH2':
                    general.message('The coupling for CH2 is only AC')
                elif ch == 'CH3':
                    general.message('Invalid channel')
            elif len(coupling) == 1:
                ch = str(coupling[0])
                if ch == 'CH1':
                    answer = str(self.device_query(":INPut1:COUPling?"))
                    return answer
                elif ch == 'CH2':
                    answer = str(self.device_query(":INPut2:COUPling?"))
                    return answer
                elif ch == 'CH3':
                    general.message('Invalid channel')
            else:
                general.message('Invalid argument')
                sys.exit()

        elif test_flag == 'test':
            if len(coupling) == 2:
                ch = str(coupling[0])
                cpl = str(coupling[1])
                assert(ch == 'CH1' or ch == 'CH2'), 'Invalid channel is given'
                assert(cpl == 'AC' or cpl == 'DC'), 'Invalid coupling is given'
            elif len(coupling) == 1:
                assert(ch == 'CH1' or ch == 'CH2'), 'Invalid channel is given'
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
                    self.device_write(":FREQuency:ARM:STOP:SOURce "+ str(flag))
                else:
                    general.message("Invalid stop arm mode")
                    sys.exit()
            elif len(mode) == 0:
                answer = str(self.device_query(':FREQuency:ARM:STOP:SOURce?'))
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
                    self.device_write(":FREQuency:ARM:START:SOURce "+ str(flag))
                else:
                    general.message("Invalid start arm mode")
                    sys.exit()
            elif len(mode) == 0:
                answer = str(self.device_query(':FREQuency:ARM:START:SOURce?'))
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

    def freq_counter_digits(self, *digits):
        if test_flag != 'test':
            if  len(digits) == 1:
                val = int(digits[0])
                if val >= min_digits and val <= max_digits:
                    self.device_write(":FREQuency:ARM:STOP:DIGits "+ str(val))
                else:
                    general.message("Invalid amount of digits")
                    sys.exit()
            elif len(digits) == 0:
                answer = int(self.device_query(':FREQuency:ARM:STOP:DIGits?'))
                return answer
            else:
                general.message("Invalid argument")
                sys.exit()

        elif test_flag == 'test':
            if  len(digits) == 1:
                val = int(digits[0])
                assert(val >= min_digits and val <= max_digits), "Invalid amount of digits"
            elif len(digits) == 0:
                answer = test_digits
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
                answer = float(self.device_query(":FREQuency:ARM:STOP:TIMer?"))
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

    def freq_counter_ratio(self, channel1, channel2):
        if test_flag != 'test':
            if channel1 == 'CH1' and channel2 == 'CH2':
                answer = float(self.device_query(':MEASure:FREQuency:RATio? (@1),(@2)'))
                return answer
            elif channel1 == 'CH2' and channel2 == 'CH1':
                answer = float(self.device_query(':MEASure:FREQuency:RATio? (@2),(@1)'))
                return answer
            else:
                general.message('Invalid argument')
                sys.exit()

        elif test_flag == 'test':
            assert(channel1 == 'CH1' or channel1 == 'CH2'), \
            "Invalid channel 1 argument"
            assert(channel2 == 'CH1' or channel2 == 'CH2'), \
            "Invalid channel 2 argument"
            answer = test_ratio
            return answer

    def freq_counter_expected_freq(self, *frequency):
        if test_flag != 'test':
            if len(frequency) == 2:
                temp = frequency[1].split(" ")
                ch = str(frequency[0])
                val = float(temp[0])
                scaling = str(temp[1])
                if scaling in scalefreq_dict:
                    coef = scalefreq_dict[scaling]
                    if ch == 'CH1':
                        self.device_write(":FREQuency:EXPected1 "+str(val*coef))
                    elif ch == 'CH2':
                        self.device_write(":FREQuency:EXPected2 "+str(val*coef))
                    elif ch == 'CH3':
                        general.message("Invalid channel is given")
                    else:
                        general.message("Invalid channel is given")
                        sys.exit()
                else:
                    general.message("Invalid argument")
                    sys.exit()
            elif len(frequency) == 1:
                ch = str(frequency[0])
                if ch == 'CH1':
                    temp = int(self.device_query(':FREQuency:EXPected1:AUTO?'))
                    if temp == 0:
                        answer = float(self.device_query(":FREQuency:EXPected1?"))
                        return answer
                    else:
                        general.message("No expected frequency is found")
                elif ch == 'CH2':
                    temp = int(self.device_query(':FREQuency:EXPected2:AUTO?'))
                    if temp == 0:
                        answer = float(self.device_query(":FREQuency:EXPected2?"))
                        return answer
                    else:
                        general.message("No expected frequency is found")
                else:
                    general.message("Invalid channel is given")
                    sys.exit()
            else:
                general.message("Invalid argument")
                sys.exit()

        elif test_flag == 'test':
            if len(frequency) == 2:
                temp = frequency[1].split(" ")
                ch = str(frequency[0])
                val = float(temp[0])
                scaling = str(temp[1])
                if scaling in scalefreq_dict:
                    coef = scalefreq_dict[scaling]
                    assert(ch == 'CH1' or ch == 'CH2'), "Invalid channel is given"
                else:
                    assert(1 == 2), "Invalid argument"
            elif len(frequency) == 1:
                ch = str(frequency[0])
                assert(ch == 'CH1' or ch == 'CH2'), "Invalid channel is given"
                answer = test_expect_freq
            else:
                assert(1 == 2), "Invalid argument"

    def freq_counter_period(self, channel):
        if test_flag != 'test':
            if channel == 'CH1':
                answer = float(self.device_query(':MEASURE:PERiod? (@1)'))*1000000
                return answer
            elif channel == 'CH2':
                answer = float(self.device_query(':MEASURE:PERiod? (@2)'))*1000000
                return answer
            else:
                general.message('Invalid argument')
                sys.exit()

        elif test_flag == 'test':
            assert(channel == 'CH1' or channel == 'CH2'), 'Invalid channel is given'
            answer = test_period
            return answer

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