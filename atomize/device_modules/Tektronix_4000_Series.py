#!/usr/bin/env python3 # -*- coding: utf-8 -*-

import os
import gc
import sys
import pyvisa
import numpy as np 
import atomize.device_modules.config.config_utils as cutil
import atomize.general_modules.general_functions as general

class Tektronix_4000_Series:
    #### Basic interaction functions
    def __init__(self):

        #### Inizialization
        # setting path to *.ini file
        self.path_current_directory = os.path.dirname(__file__)
        self.path_config_file = os.path.join(self.path_current_directory, 'config','Tektronix_4032_config.ini')

        # configuration data
        self.config = cutil.read_conf_util(self.path_config_file)
        self.specific_parameters = cutil.read_specific_parameters(self.path_config_file)

        # auxilary dictionaries
        self.channel_dict = {'CH1': 'CH1', 'CH2': 'CH2', 'CH3': 'CH3', 'CH4': 'CH4', }
        self.trigger_channel_dict = {'CH1': 'CH1', 'CH2': 'CH2', 'CH3': 'CH3', 'CH4': 'CH4', \
                                'Ext': 'EXTernal', 'Line': 'LINE', }
        self.number_averag_list = [2, 4, 8, 16, 32, 64, 128, 256, 512]
        self.points_list = [1000, 10000, 100000, 1000000, 10000000]
        self.timebase_dict = {'s': 1, 'ms': 1000, 'us': 1000000, 'ns': 1000000000, }
        self.timebase_helper_list = [1, 2, 4, 10, 20, 40, 100, 200, 400, 1000]
        self.scale_dict = {'V': 1, 'mV': 1000, }
        self.ac_type_dic = {'Normal': "SAMple", 'Average': "AVErage", 'Hres': "HIRes",'Peak': "PEAKdetect", }

        # Ranges and limits
        self.analog_channels = int(self.specific_parameters['analog_channels'])
        self.sensitivity_min = float(self.specific_parameters['sensitivity_min'])
        self.sensitivity_max = float(self.specific_parameters['sensitivity_max'])

        # Test run parameters
        # These values are returned by the modules in the test run 
        if len(sys.argv) > 1:
            self.test_flag = sys.argv[1]
        else:
            self.test_flag = 'None'

        if self.test_flag != 'test':
            if self.config['interface'] == 'ethernet':
                rm = pyvisa.ResourceManager()
                try:
                    self.status_flag = 1
                    self.device = rm.open_resource(self.config['ethernet_address'])
                    self.device.timeout = self.config['timeout']; # in ms
                    self.device.read_termination = self.config['read_termination']
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
                    except pyvisa.VisaIOError:
                        general.message("No connection")
                        self.status_flag = 0
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
                    self.status_flag = 0;
                    sys.exit()

        elif self.test_flag == 'test':
            self.test_start = 1
            self.test_stop = 1000
            self.test_record_length = 2000
            self.test_impedance = 1000000
            self.test_acquisition_type = 'Normal'
            self.test_num_aver = 2
            self.test_timebase = 100
            self.test_h_offset = '10 ms'
            self.test_sensitivity = 0.1
            self.test_coupling = 'AC'
            self.test_tr_mode = 'Normal'
            self.test_tr_channel = 'CH1'
            self.test_trigger_level = 0.

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
            general.message("No connection")
            self.status_flag = 0
            sys.exit()

    def device_query(self, command):
        if self.status_flag == 1:
            answer = self.device.query(command)
            return answer
        else:
            general.message("No connection")
            self.status_flag = 0
            sys.exit()

    def device_query_ascii(self, command):
        if self.status_flag == 1:
            answer = self.device.query_ascii_values(command, converter='f', separator=',', container=np.array)
            return answer
        else:
            general.message("No connection")
            self.status_flag = 0
            sys.exit()

    def device_read_binary(self, command):
        if self.status_flag == 1:
            answer = self.device.query_binary_values(command, 'b', is_big_endian=True, container=np.array)
            # RPBinary, value from 0 to 255. 'b'
            # Endianness is primarily expressed as big-endian (BE) or little-endian (LE).
            # A big-endian system stores the most significant byte of a word at the smallest memory address 
            # and the least significant byte at the largest. A little-endian system, in contrast, stores 
            # the least-significant byte at the smallest address.
            return answer
        else:
            general.message("No connection")
            self.status_flag = 0
            sys.exit()

    #### device specific functions
    def oscilloscope_name(self):
        if self.test_flag != 'test':
            answer = self.device_query('*IDN?')
            return answer
        elif self.test_flag == 'test':
            answer = self.config['name']
            return answer

    def oscilloscope_define_window(self, **kargs):
        if self.test_flag != 'test':        
            try:
                st = int(kargs['start'])
                stop = int(kargs['stop'])
                points = self.oscilloscope_record_length()
                if stop > points or st > points:
                    general.message('Invalid arguments')
                    sys.exit()
                else:
                    self.device_write("DATa:STARt " + str(st))
                    self.device_write("DATa:STOP " + str(stop))
            except KeyError:
                answer1 = int(self.device_query('DATa:STARt?'))
                answer2 = int(self.device_query('DATa:STOP?'))
                return answer1, answer2

        elif self.test_flag == 'test':
            try:
                st = int(kargs['start'])
                stop = int(kargs['stop'])
                points = self.oscilloscope_record_length()
                assert(stop > points or st > points), 'Invalid window'
            except KeyError:
                answer1 = self.test_start
                answer2 = self.test_stop
                return answer1, answer2

    def oscilloscope_record_length(self, *points):
        if self.test_flag != 'test': 
            if len(points) == 1:
                temp = int(points[0])
                poi = min(self.points_list, key = lambda x: abs(x - temp))
                if int(poi) != temp:
                    general.message("Desired record length cannot be set, the nearest available value is used")
                self.device_write("HORizontal:RECOrdlength " + str(poi))
            elif len(points) == 0:
                answer = int(self.device_query('HORizontal:RECOrdlength?'))
                return answer
            else:
                general.message("Invalid argument")
                sys.exit()

        elif self.test_flag == 'test':
            if len(points) == 1:
                temp = int(points[0])
                poi = min(self.points_list, key = lambda x: abs(x - temp))
            elif len(points) == 0:
                answer = self.test_record_length
                return answer
            else:
                assert (1 == 2), 'Invalid record length argument'       

    def oscilloscope_acquisition_type(self, *ac_type):
        if self.test_flag != 'test':        
            if len(ac_type) == 1:
                at = str(ac_type[0])
                if at in self.ac_type_dic:
                    flag = self.ac_type_dic[at]
                    self.device_write("ACQuire:MODe "+ str(flag))
                else:
                    general.message("Invalid acquisition type")
                    sys.exit()
            elif len(ac_type) == 0:
                raw_answer = str(self.device_query("ACQuire:MODe?"))
                answer  = cutil.search_keys_dictionary(self.ac_type_dic, raw_answer)                
                return answer
            else:
                general.message("Invalid argument")
                sys.exit()

        elif self.test_flag == 'test':
            if len(ac_type) == 1:
                at = str(ac_type[0])
                if at in self.ac_type_dic:
                    flag = self.ac_type_dic[at]
                else:
                    assert(1 == 2), "Invalid acquisition type"
            elif len(ac_type) == 0:
                answer = self.test_acquisition_type
                return answer
            else:
                assert (1 == 2), 'Invalid acquisition type argument' 

    def oscilloscope_number_of_averages(self, *number_of_averages):
        if self.test_flag != 'test':
            if len(number_of_averages) == 1:
                temp = int(number_of_averages[0])
                numave = min(self.number_averag_list, key = lambda x: abs(x - temp))
                if int(numave) != temp:
                    general.message("Desired number of averages cannot be set, the nearest available value is used")
                ac = self.oscilloscope_acquisition_type()
                if ac == 'AVE':
                    self.device_write("ACQuire:NUMAVg " + str(numave))
                elif ac == 'SAM':
                    general.message("Your are in SAMple mode")
                elif ac == 'HIR':
                    general.message("Your are in HRES mode")
                elif ac == 'PEAK':
                    general.message("Your are in PEAK mode")
            elif len(number_of_averages) == 0:
                answer = int(self.device_query("ACQuire:NUMAVg?"))
                return answer
            else:
                general.message("Invalid argument")
                sys.exit()

        elif self.test_flag == 'test':
            if len(number_of_averages) == 1:
                temp = int(number_of_averages[0])
                numave = min(self.number_averag_list, key = lambda x: abs(x - temp))
            elif len(number_of_averages) == 0:
                answer = self.test_num_aver
                return answer
            else:
                assert (1 == 2), 'Invalid number of averages argument' 

    def oscilloscope_timebase(self, *timebase):
        if self.test_flag != 'test':
            if  len(timebase) == 1:
                temp = timebase[0].split(' ')
                if temp[1] == 'ns' and float(temp[0]) >= 60 and float(temp[0]) <= 90:
                    if timebase != '80 ns':
                        self.device_write("HORizontal:SCAle " + str(80/1000000000))
                        general.message("Desired time constant cannot be set, the nearest available value is used")
                    else:
                        self.device_write("HORizontal:SCAle " + str(80/1000000000))              
                else:
                    number_tb = min(self.timebase_helper_list, key = lambda x: abs(x - int(temp[0])))
                    if number_tb > 40 and temp[1] == 's':
                        number_tb = 40
                    if number_tb == 1000 and temp[1] == 'ns':
                        number_tb = 1
                        temp[1] = 'us'
                    elif number_tb == 1000 and temp[1] == 'us':
                        number_tb = 1
                        temp[1] = 'ms'
                    elif number_tb == 1000 and temp[1] == 'ms':
                        number_tb = 1
                        temp[1] = 's'
                    if int(number_tb) != float(temp[0]):
                        general.message("Desired time constant cannot be set, the nearest available value is used")
                    if temp[1] in self.timebase_dict:
                        coef = self.timebase_dict[temp[1]]
                        self.device_write("HORizontal:SCAle "+ str(number_tb/coef))
                    else:
                        general.message("Incorrect timebase")
                        sys.exit()
            elif len(timebase) == 0:
                answer = float(self.device_query("HORizontal:SCAle?"))*1000000
                return answer
            else:
                general.message("Invalid argument")
                sys.exit()

        elif self.test_flag == 'test':
            if  len(timebase) == 1:
                temp = timebase[0].split(' ')
                number_tb = min(self.timebase_helper_list, key = lambda x: abs(x - int(temp[0])))
                if number_tb > 40 and temp[1] == 's':
                        number_tb = 40
                if number_tb == 1000 and temp[1] == 'ns':
                    number_tb = 1
                    temp[1] = 'us'
                elif number_tb == 1000 and temp[1] == 'us':
                    number_tb = 1
                    temp[1] = 'ms'
                elif number_tb == 1000 and temp[1] == 'ms':
                    number_tb = 1
                    temp[1] = 's'
                if temp[1] in self.timebase_dict:
                    coef = self.timebase_dict[temp[1]]
                else:
                    assert (1 == 2), 'Invalid timebase argument'
            elif len(timebase) == 0:
                answer = self.test_timebase
                return answer
            else:
                assert (1 == 2), 'Invalid timebase argument'

    def oscilloscope_time_resolution(self):
        if self.test_flag != 'test':
            points = int(self.oscilloscope_record_length())
            answer = 1000000*float(self.device_query("HORizontal:SCAle?"))/points
            return answer
        elif self.test_flag == 'test':
            answer = 1000000*float(self.test_timebase.split(' ')[0])/self.test_record_length
            return answer

    def oscilloscope_start_acquisition(self):
        if self.test_flag != 'test':
            #start_time = time.time()
            self.device_query('*ESR?')
            self.device_write('ACQuire:STATE RUN;:ACQuire:STOPAfter SEQ')
            self.device_query('*OPC?') # return 1, if everything is ok;
            # the whole sequence is the following 1-clearing; 2-3-digitizing; 4-checking of the completness
            #end_time=time.time()
            general.message('Acquisition completed') 
            #general.message("Duration of Acquisition: {}".format(end_time - start_time))
        elif self.test_flag == 'test':
            pass

    def oscilloscope_preamble(self, channel):
        if self.test_flag != 'test':
            ch = str(channel)
            if ch in self.channel_dict:
                flag = self.channel_dict[ch]
                if flag[0] == 'C' and int(flag[-1]) <= self.analog_channels:
                    self.device_write('DATa:SOUrce ' + str(flag))
                    preamble = self.device_query("WFMOutpre?")
                    return preamble
                else:
                    general.message("Invalid channel is given")
                    sys.exit()
            else:
                general.message("Invalid channel is given")
                sys.exit()

        elif self.test_flag == 'test':
            ch = str(channel)
            assert(ch in self.channel_dict), 'Invalid channel is given'
            flag = self.channel_dict[ch]
            if flag[0] == 'C' and int(flag[-1]) > self.analog_channels:
                assert(1 == 2), 'Invalid channel is given'
            else:
                preamble = np.arange(21)
                return preamble

    def oscilloscope_stop(self):
        if self.test_flag != 'test':
            self.device_write("ACQuire:STATE STOP")
        elif self.test_flag == 'test':
            pass

    def oscilloscope_run(self):
        if self.test_flag != 'test':
            self.device_write("ACQuire:STATE RUN")
        elif self.test_flag == 'test':
            pass

    def oscilloscope_get_curve(self, channel):
        if self.test_flag != 'test':
            ch = str(channel)
            if ch in self.channel_dict:
                flag = self.channel_dict[ch]
                if flag[0] == 'C' and int(flag[-1]) <= self.analog_channels:
                    self.device_write('DATa:SOUrce ' + str(flag))
                    self.device_write('DATa:ENCdg RIBinary')

                    array_y = self.device_read_binary('CURVe?')
                    #x_orig=float(self.device_query("WFMOutpre:XZEro?"))
                    #x_inc=float(self.device_query("WFMOutpre:XINcr?"))
                    #general.message(preamble)
                    y_ref = float(self.device_query("WFMOutpre:YOFf?"))
                    y_inc = float(self.device_query("WFMOutpre:YMUlt?"))
                    y_orig = float(self.device_query("WFMOutpre:YZEro?"))
                    #general.message(y_inc)
                    #general.message(y_orig)
                    #general.message(y_ref)
                    array_y = (array_y - y_ref)*y_inc + y_orig
                    #array_x= list(map(lambda x: x_inc*(x+1) + x_orig, list(range(len(array_y)))))
                    #final_data = np.asarray(list(zip(array_x,array_y)))
                    return array_y
                else:
                    general.message('Invalid channel')
                    sys.exit()
            else:
                general.message('Invalid channel')
                sys.exit()            

        elif self.test_flag == 'test':
            ch = str(channel)
            assert(ch in self.channel_dict), 'Invalid channel is given'
            flag = self.channel_dict[ch]
            if flag[0] == 'C' and int(flag[-1]) > self.analog_channels:
                assert(1 == 2), 'Invalid channel is given'
            else:
                array_y = np.arange(self.test_stop - self.test_start + 1)
                return array_y

    def oscilloscope_sensitivity(self, *channel):
        if self.test_flag != 'test':
            if len(channel) == 2:
                temp = channel[1].split(" ")
                ch = str(channel[0])
                val = float(temp[0])
                scaling = str(temp[1])
                if scaling in self.scale_dict:
                    coef = self.scale_dict[scaling]
                    if val/coef >= self.sensitivity_min and val/coef <= self.sensitivity_max:
                        if ch in self.channel_dict:
                            flag = self.channel_dict[ch]
                            if flag[0] == 'C' and int(flag[-1]) <= self.analog_channels:
                                self.device_write(str(flag) + ':SCAle ' + str(val/coef))
                            else:
                                general.message("Invalid channel is given")
                                sys.exit()
                        else:
                            general.message("Invalid channel is given")
                            sys.exit()
                    else:
                        general.message("Incorrect sensitivity range")
                        sys.exit()                    
                else:
                    general.message("Incorrect scaling factor")
                    sys.exit()

            elif len(channel) == 1:
                ch = str(channel[0])
                if ch in self.channel_dict:
                    flag = self.channel_dict[ch]
                    if flag[0] == 'C' and int(flag[-1]) <= self.analog_channels:
                        answer = float(self.device_query(str(flag) + ':SCAle?'))*1000
                        return answer
                    else:
                        general.message("Invalid channel is given")
                        sys.exit()
                else:
                    general.message("Incorrect channel is given")
                    sys.exit()
            else:
                general.message("Invalid argument")
                sys.exit()

        elif self.test_flag == 'test':
            if len(channel) == 2:
                temp = channel[1].split(" ")
                ch = str(channel[0])
                val = float(temp[0])
                scaling = str(temp[1])
                if scaling in self.scale_dict:
                    coef = self.scale_dict[scaling]
                    assert(val/coef >= self.sensitivity_min and val/coef <= \
                        self.sensitivity_max), "Incorrect sensitivity range"
                    assert(ch in self.channel_dict), 'Invalid channel is given'
                    flag = self.channel_dict[ch]
                    if flag[0] == 'C' and int(flag[-1]) > self.analog_channels:
                        assert(1 == 2), 'Invalid channel is given'
                    else:
                        pass
                else:
                    assert(1 == 2), "Incorrect sensitivity argument"
            elif len(channel) == 1:
                ch = str(channel[0])
                assert(ch in self.channel_dict), 'Invalid channel is given'
                flag = self.channel_dict[ch]
                if flag[0] == 'C' and int(flag[-1]) > self.analog_channels:
                    assert(1 == 2), 'Invalid channel is given'
                else:
                    answer = self.test_sensitivity
                    return answer
            else:
                assert(1 == 2), "Incorrect sensitivity argument"

    def oscilloscope_offset(self, *channel):
        if self.test_flag != 'test':
            if len(channel) == 2:
                temp = channel[1].split(" ")
                ch = str(channel[0])
                val = float(temp[0])
                scaling = str(temp[1]);
                if scaling in self.scale_dict:
                    coef = self.scale_dict[scaling]
                    if ch in self.channel_dict:
                        flag = self.channel_dict[ch]
                        if flag[0] == 'C' and int(flag[-1]) <= self.analog_channels:
                            self.device_write(str(flag) + ':OFFSet ' + str(val/coef))
                        else:
                            general.message("Invalid channel is given")
                            sys.exit()
                    else:
                        general.message("Invalid channel is given")
                        sys.exit()
                else:
                    general.message("Incorrect scaling factor")
                    sys.exit()

            elif len(channel) == 1:
                ch = str(channel[0])
                if ch in self.channel_dict:
                    flag = self.channel_dict[ch]
                    if flag[0] == 'C' and int(flag[-1]) <= self.analog_channels:
                        answer = float(self.device_query(str(flag) + ':OFFSet?'))*1000
                        return answer
                    else:
                        general.message("Invalid channel is given")
                        sys.exit()
                else:
                    general.message("Incorrect channel is given")
                    sys.exit()
            else:
                general.message("Invalid argument")
                sys.exit()

        elif self.test_flag == 'test':
            if len(channel) == 2:
                temp = channel[1].split(" ")
                ch = str(channel[0])
                val = float(temp[0])
                scaling = str(temp[1])
                if scaling in self.scale_dict:
                    coef = self.scale_dict[scaling]
                    assert(ch in self.channel_dict), 'Invalid channel is given'
                    flag = self.channel_dict[ch]
                    if flag[0] == 'C' and int(flag[-1]) > self.analog_channels:
                        assert(1 == 2), 'Invalid channel is given'
                    else:
                        pass
                else:
                    assert(1 == 2), "Incorrect offset argument"
            elif len(channel) == 1:
                ch = str(channel[0])
                assert(ch in self.channel_dict), 'Invalid channel is given'
                flag = self.channel_dict[ch]
                if flag[0] == 'C' and int(flag[-1]) > self.analog_channels:
                    assert(1 == 2), 'Invalid channel is given'
                else:
                    answer = self.test_sensitivity
                    return answer
            else:
                assert(1 == 2), "Incorrect offset argument"

    def oscilloscope_horizontal_offset(self, *h_offset):
        if self.test_flag != 'test':
            if len(h_offset) == 1:
                temp = h_offset[0].split(" ")
                offset = float(temp[0])
                scaling = temp[1]
                if scaling in self.timebase_dict:
                    coef = self.timebase_dict[scaling]
                    self.device_write("HORizontal:DELay:TIMe " + str(offset/coef))
                else:
                    general.message("Incorrect horizontal offset")
                    sys.exit()
            elif len(h_offset) == 0:
                answer = float(self.device_query("HORizontal:DELay:TIMe?"))*1000000
                return answer
            else:
                general.message("Invalid argument")
                sys.exit()

        elif self.test_flag == 'test':
            if len(h_offset) == 1:
                temp = h_offset[0].split(" ")
                offset = float(temp[0])
                scaling = temp[1]
                if scaling in self.timebase_dict:
                    coef = self.timebase_dict[scaling]
                else:
                    assert(1 == 2), "Incorrect horizontal offset"
            elif len(delay) == 0:
                answer = test_delay
                return answer
            else:
                assert(1 == 2), "Incorrect horizontal offset argument"

    def oscilloscope_coupling(self, *coupling):
        if self.test_flag != 'test':
            if len(coupling) == 2:
                ch = str(coupling[0])
                cpl = str(coupling[1])
                if ch in self.channel_dict:
                    flag = self.channel_dict[ch]
                    if flag[0] == 'C' and int(flag[-1]) <= self.analog_channels:
                        self.device_write(str(flag) + ':COUPling ' + str(cpl))
                    else:
                        general.message("Invalid channel is given")
                        sys.exit()
                else:
                    general.message("Invalid channel is given")
                    sys.exit()

            elif len(coupling) == 1:
                ch = str(coupling[0])
                if ch in self.channel_dict:
                    flag = self.channel_dict[ch]
                    if flag[0] == 'C' and int(flag[-1]) <= self.analog_channels:
                        answer = self.device_query(str(flag) + ':COUPling?')
                        return answer
                    else:
                        general.message("Invalid channel is given")
                        sys.exit()
                else:
                    general.message("Incorrect channel is given")
                    sys.exit()
            else:
                general.message("Invalid argument")
                sys.exit()

        elif self.test_flag == 'test':
            if len(coupling) == 2:
                ch = str(coupling[0])
                cpl = str(coupling[1])
                assert(ch in self.channel_dict), 'Invalid channel is given'
                assert(cpl == 'AC' or cpl == 'DC'), 'Invalid coupling is given'
                flag = self.channel_dict[ch]
                if flag[0] == 'C' and int(flag[-1]) > self.analog_channels:
                    assert(1 == 2), 'Invalid channel is given'
                else:
                    pass
            elif len(coupling) == 1:
                ch = str(coupling[0])
                assert(ch in self.channel_dict), 'Invalid channel is given'
                flag = self.channel_dict[ch]
                if flag[0] == 'C' and int(flag[-1]) > self.analog_channels:
                    assert(1 == 2), 'Invalid channel is given'
                else:
                    answer = self.test_coupling
                    return answer
            else:
                assert(1 == 2), 'Invalid coupling argument'

    def oscilloscope_impedance(self, *impedance):
        if self.test_flag != 'test':
            if len(impedance) == 2:
                ch = str(impedance[0])
                cpl = str(impedance[1])
                if cpl == '1 M':
                    cpl = 'MEG'
                elif cpl == '50':
                    cpl = 'FIFty'

                if ch in self.channel_dict:
                    flag = self.channel_dict[ch]
                    if flag[0] == 'C' and int(flag[-1]) <= self.analog_channels:
                        self.device_write(str(flag) + ':TERmination ' + str(cpl))
                    else:
                        general.message("Invalid channel is given")
                        sys.exit()
                else:
                    general.message("Invalid channel is given")
                    sys.exit()

            elif len(impedance) == 1:
                ch = str(impedance[0])
                if ch in self.channel_dict:
                    flag = self.channel_dict[ch]
                    if flag[0] == 'C' and int(flag[-1]) <= self.analog_channels:
                        answer = self.device_query(str(flag) + ':TERmination?')
                        return answer
                    else:
                        general.message("Invalid channel is given")
                        sys.exit()
                else:
                    general.message("Incorrect channel is given")
                    sys.exit()
            else:
                general.message("Invalid argument")
                sys.exit()

        elif self.test_flag == 'test':
            if len(impedance) == 2:
                ch = str(impedance[0])
                cpl = str(impedance[1])
                assert(ch in self.channel_dict), 'Invalid channel is given'
                assert(cpl == '1 M' or cpl == '50'), 'Invalid impedance is given'
                flag = self.channel_dict[ch]
                if flag[0] == 'C' and int(flag[-1]) > self.analog_channels:
                    assert(1 == 2), 'Invalid channel is given'
                else:
                    pass
            elif len(impedance) == 1:
                ch = str(impedance[0])
                assert(ch in self.channel_dict), 'Invalid channel is given'
                flag = self.channel_dict[ch]
                if flag[0] == 'C' and int(flag[-1]) > self.analog_channels:
                    assert(1 == 2), 'Invalid channel is given'
                else:
                    answer = self.test_impedance
                    return answer
            else:
                assert(1 == 2), 'Invalid impedance argument'

    def oscilloscope_trigger_mode(self, *mode):
        if self.test_flag != 'test':
            if len(mode) == 1:
                md = str(mode[0])
                if md == 'Auto':
                    self.device_write("TRIGger:A:MODe " + 'AUTO')
                elif md == 'Normal':
                    self.device_write("TRIGger:A:MODe " + 'NORMal')
                else:
                    general.message("Incorrect trigger mode is given")
                    sys.exit()
            elif len(mode) == 0:
                answer = self.device_query("TRIGger:A:MODe?")
                return answer
            else:
                general.message("Invalid argument")
                sys.exit()

        elif self.test_flag == 'test':
            if len(mode) == 1:
                md = str(mode[0])
                assert(md == 'Auto' or md == 'Normal'), 'Incorrect trigger mode is given'
            elif len(mode) == 0:
                answer = self.test_tr_mode
                return answer
            else:
                assert(1 == 2), 'Incorrect trigger mode argument'

    def oscilloscope_trigger_channel(self, *channel):
        if self.test_flag != 'test':    
            if len(channel) == 1:
                ch = str(channel[0])
                if ch in self.trigger_channel_dict:
                    flag = self.trigger_channel_dict[ch]
                    if flag[0] == 'C' and int(flag[-1]) <= self.analog_channels:
                        self.device_write("TRIGger:A:EDGE:SOUrce " + str(flag))
                    elif flag[0] != 'C':
                        self.device_write('TRIGger:A:EDGE:SOUrce ' + str(flag))
                    else:
                        general.message("Invalid trigger channel is given")
                        sys.exit()
                else:
                    general.message("Invalid trigger channel is given")
                    sys.exit()

            elif len(channel) == 0:
                answer = self.device_query("TRIGger:A:EDGE:SOUrce?")
                return answer
            else:
                general.message("Invalid argument")
                sys.exit()

        if self.test_flag == 'test':        
            if len(channel) == 1:
                ch = str(channel[0])
                assert(ch in self.trigger_channel_dict), 'Invalid channel is given'
                flag = self.trigger_channel_dict[ch]
                if flag[0] == 'C' and int(flag[-1]) > self.analog_channels:
                    assert(1 == 2), 'Invalid trigger channel is given'
                else:
                    pass
            elif len(channel) == 0:
                answer = self.test_tr_channel
                return answer
            else:
                assert(1 == 2), "Invalid trigger channel argument"

    def oscilloscope_trigger_low_level(self, *level):
        if self.test_flag != 'test':
            if len(level) == 2:
                ch = str(level[0])
                lvl = level[1]
                if lvl != 'ECL' and lvl != 'TTL':
                    lvl = float(level[1])

                if ch in self.channel_dict:
                    flag = self.channel_dict[ch]
                    if flag[0] == 'C' and int(flag[-1]) <= self.analog_channels:
                        self.device_write("TRIGger:A:LEVel:" + str(flag) + str(lvl))
                    else:
                        general.message("Invalid trigger channel is given")
                        sys.exit()
                else:
                    general.message("Invalid trigger channel is given")
                    sys.exit()

            elif len(level) == 1:
                ch = str(level[0])
                if ch in self.channel_dict:
                    flag = self.channel_dict[ch]
                    if flag[0] == 'C' and int(flag[-1]) <= self.analog_channels:
                        answer = self.device_query('TRIGger:A:LEVel:' + str(flag) + '?')
                        return answer
                    else:
                        general.message("Invalid channel is given")
                        sys.exit()
                else:
                    general.message("Incorrect channel is given")
                    sys.exit()
            else:
                general.message("Invalid argument")
                sys.exit()

        elif self.test_flag == 'test':
            if len(level) == 2:
                ch = str(level[0])
                lvl = level[1]
                if lvl != 'ECL' and lvl != 'TTL':
                    lvl = float(level[1])
                assert(ch in self.channel_dict), 'Invalid channel is given'
                flag = self.channel_dict[ch]
                if flag[0] == 'C' and int(flag[-1]) > self.analog_channels:
                    assert(1 == 2), 'Invalid trigger channel is given'
                else:
                    pass
            elif len(level) == 1:
                ch = str(level[0])
                assert(ch in self.channel_dict), 'Invalid trigger channel is given'
                flag = self.channel_dict[ch]
                if flag[0] == 'C' and int(flag[-1]) > self.analog_channels:
                    assert(1 == 2), 'Invalid channel is given'
                else:
                    answer = self.test_trigger_level
                    return answer
            else:
                assert(1 == 2), "Invalid trigger level argument"

    def oscilloscope_command(self, command):
        if self.test_flag != 'test':
            self.device_write(command)
        elif self.test_flag == 'test':
            pass

    def oscilloscope_query(self, command):
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

