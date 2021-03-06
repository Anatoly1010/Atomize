#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import gc
import sys
import pyvisa
import numpy as np 
import atomize.device_modules.config.config_utils as cutil
import atomize.general_modules.general_functions as general

#### Inizialization
# setting path to *.ini file
path_current_directory = os.path.dirname(__file__)
path_config_file = os.path.join(path_current_directory, 'config','Keysight_3034t_config.ini')

# configuration data
config = cutil.read_conf_util(path_config_file)
specific_parameters = cutil.read_specific_parameters(path_config_file)

# auxilary dictionaries
points_list = [100, 250, 500, 1000, 2000, 5000, 10000, 20000, 50000, 100000, 200000, 500000]
points_list_average = [100, 250, 500, 1000, 2000, 4000, 8000, 16000]
# Number of point is different for Average mode and three other modes

channel_dict = {'CH1': 'CHAN1', 'CH2': 'CHAN2', 'CH3': 'CHAN3', 'CH4': 'CHAN4',}
trigger_channel_dict = {'CH1': 'CHAN1', 'CH2': 'CHAN2', 'CH3': 'CHAN3', 'CH4': 'CHAN4', \
                        'Ext': 'EXTernal', 'Line': 'LINE', 'WGen': 'WGEN',}
timebase_dict = {'s': 1, 'ms': 1000, 'us': 1000000, 'ns': 1000000000,};
scale_dict = {'V': 1, 'mV': 1000,};
frequency_dict = {'MHz': 1000000, 'kHz': 1000, 'Hz': 1, 'mHz': 0.001,};
wavefunction_dic = {'Sin': 'SINusoid', 'Sq': 'SQUare', 'Ramp': 'RAMP', 'Pulse': 'PULSe',
                    'DC': 'DC', 'Noise': 'NOISe', 'Sinc': 'SINC', 'ERise': 'EXPRise',
                    'EFall': 'EXPFall', 'Card': 'CARDiac', 'Gauss': 'GAUSsian',
                    'Arb': 'ARBitrary'};
ac_type_dic = {'Normal': "NORMal", 'Average': "AVER", 'Hres': "HRES",'Peak': "PEAK"}
wave_gen_interpolation_dictionary = {'On': 1, 'Off': 0, }

# Limits and Ranges (depends on the exact model):
analog_channels = int(specific_parameters['analog_channels'])
numave_min = 2
numave_max = 65536
timebase_max = float(specific_parameters['timebase_max'])
timebase_min = float(specific_parameters['timebase_min'])
sensitivity_min = float(specific_parameters['sensitivity_min'])
sensitivity_max = float(specific_parameters['sensitivity_max'])
wave_gen_freq_max = float(specific_parameters['wave_gen_freq_max'])
wave_gen_freq_min = float(specific_parameters['wave_gen_freq_min'])

# Test run parameters
# These values are returned by the modules in the test run 
if len(sys.argv) > 1:
    test_flag = sys.argv[1]
else:
    test_flag = 'None'

test_record_length = 2000
test_acquisition_type = 'Norm'
test_num_aver = 2
test_impedance = 1000000
test_timebase = '100 ms'
test_h_offset = '10 ms'
test_sensitivity = 0.1
test_offset = 0.1
test_coupling = 'AC'
test_tr_mode = 'Normal'
test_tr_channel = 'CH1'
test_trigger_level = 0.
test_wave_gen_frequency = 500
test_wave_gen_width = '350 us'
test_wave_gen_function = 'Sin'
test_wave_gen_amplitude = '500 mV'
test_wave_gen_offset = 0.
test_wave_gen_impedance = '1 M'
test_wave_gen_interpolation = 'Off'
test_wave_gen_points = 10

class Keysight_3000_Xseries:
    #### Basic interaction functions
    def __init__(self):
        if test_flag != 'test':
            if config['interface'] == 'ethernet':
                rm = pyvisa.ResourceManager()
                try:
                    self.status_flag = 1
                    self.device = rm.open_resource(config['ethernet_address'])
                    self.device.timeout = config['timeout'] # in ms
                    self.device.read_termination = config['read_termination']  # for WORD (a kind of binary) format
                    try:
                        self.device_write('*CLS')
                        self.status_flag = 1
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
            answer = self.device.query_binary_values(command, 'H', is_big_endian=True, container=np.array)
            # H for 3034T; h for 2012A
            return answer
        else:
            general.message("No connection")
            self.status_flag = 0
            sys.exit()

    #### Device specific functions
    def oscilloscope_name(self):
        if test_flag != 'test':
            answer = self.device_query('*IDN?')
            return answer
        elif test_flag == 'test':
            answer = config['name']
            return answer

    def oscilloscope_record_length(self, *points):
        if test_flag != 'test': 
            if len(points) == 1:
                temp = int(points[0])
                test_acq_type = self.oscilloscope_acquisition_type()
                if test_acq_type == 'Average':
                    poi = min(points_list_average, key = lambda x: abs(x - temp))
                    if int(poi) != temp:
                        general.message("Desired record length cannot be set, the nearest available value is used")
                    self.device_write(":WAVeform:POINts " + str(poi))
                else:
                    poi = min(points_list, key = lambda x: abs(x - temp))
                    if int(poi) != temp:
                        general.message("Desired record length cannot be set, the nearest available value is used")
                    self.device_write(":WAVeform:POINts " + str(poi))

            elif len(points) == 0:
                answer = int(self.device_query(':WAVeform:POINts?'))
                return answer
            else:
                general.message("Invalid argument")
                sys.exit()

        elif test_flag == 'test':
            if len(points) == 1:
                temp = int(points[0])
                poi = min(points_list, key = lambda x: abs(x - temp))
            elif len(points) == 0:
                answer = test_record_length
                return answer
            else:
                assert (1 == 2), 'Invalid record length argument'

    def oscilloscope_acquisition_type(self, *ac_type):
        if test_flag != 'test': 
            if  len(ac_type) == 1:
                at = str(ac_type[0])
                if at in ac_type_dic:
                    flag = ac_type_dic[at]
                    self.device_write(":ACQuire:TYPE " + str(flag))
                else:
                    general.message("Invalid acquisition type")
                    sys.exit()
            elif len(ac_type) == 0:
                raw_answer = str(self.device_query(":ACQuire:TYPE?"))
                answer  = cutil.search_keys_dictionary(ac_type_dic, raw_answer)
                return answer
            else:
                general.message("Invalid argument")
                sys.exit()

        elif test_flag == 'test':
            if len(ac_type) == 1:
                at = str(ac_type[0])
                if at in ac_type_dic:
                    flag = ac_type_dic[at]
                else:
                    assert(1 == 2), "Invalid acquisition type"
            elif len(ac_type) == 0:
                answer = test_acquisition_type
                return answer
            else:
                assert (1 == 2), 'Invalid acquisition type argument'

    def oscilloscope_number_of_averages(self, *number_of_averages):
        if test_flag != 'test':
            if len(number_of_averages) == 1:
                numave = int(number_of_averages[0])
                if numave >= numave_min and numave <= numave_max:
                    ac = self.oscilloscope_acquisition_type()
                    if ac == "Average":
                        self.device_write(":ACQuire:COUNt " + str(numave))
                    elif ac == 'Normal':
                        general.message("Your are in NORM mode")
                    elif ac == 'Hres':
                        general.message("Your are in HRES mode")
                    elif ac == 'Peak':
                        general.message("Your are in PEAK mode")
                else:
                    general.message("Invalid number of averages")
                    sys.exit()
            elif len(number_of_averages) == 0:
                answer = int(self.device_query(":ACQuire:COUNt?"))
                return answer
            else:
                general.message("Invalid argument")
                sys.exit()

        elif test_flag == 'test':
            if len(number_of_averages) == 1:
                numave = int(number_of_averages[0])
                assert(numave >= numave_min and numave <= numave_max), 'Incorrect number of averages'
            elif len(number_of_averages) == 0:
                answer = test_num_aver
                return answer
            else:
                assert (1 == 2), 'Invalid number of averages argument' 

    def oscilloscope_timebase(self, *timebase):
        if test_flag != 'test':
            if len(timebase) == 1:
                temp = timebase[0].split(" ")
                tb = float(temp[0])
                scaling = temp[1]
                if scaling in timebase_dict:
                    coef = timebase_dict[scaling]
                    if tb/coef >= timebase_min and tb/coef <= timebase_max:
                        self.device_write(":TIMebase:RANGe "+ str(tb/coef))
                    else:
                        general.message("Incorrect timebase range")
                        sys.exit()                        
                else:
                    general.message("Incorrect timebase")
                    sys.exit()
            elif len(timebase) == 0:
                answer = float(self.device_query(":TIMebase:RANGe?"))*1000000
                return answer
            else:
                general.message("Invalid argument")
                sys.exit()

        elif test_flag == 'test':
            if  len(timebase) == 1:
                temp = timebase[0].split(" ")
                tb = float(temp[0])
                scaling = temp[1]
                if scaling in timebase_dict:
                    coef = timebase_dict[scaling]
                    assert(tb/coef >= timebase_min and tb/coef <= timebase_max), "Incorrect timebase range"
                else:
                    assert(1 == 2), 'Incorrect timebase argument'
            elif len(timebase) == 0:
                answer = test_timebase
                return answer
            else:
                assert (1 == 2), 'Invalid timebase argument'               

    def oscilloscope_time_resolution(self):
        if test_flag != 'test':
            points = int(self.oscilloscope_record_length())
            answer = 1000000*float(self.device_query(":TIMebase:RANGe?"))/points
            return answer
        elif test_flag == 'test':
            answer = 1000000*float(test_timebase.split(' ')[0])/test_record_length
            return answer

    def oscilloscope_start_acquisition(self):
        if test_flag != 'test':
            #start_time = datetime.now()
            self.device_write(':WAVeform:FORMat WORD')
            self.device_query('*ESR?;:DIGitize;*OPC?') # return 1, if everything is ok;
            # the whole sequence is the following 1-binary format; 2-clearing; 3-digitizing; 4-checking of the completness
            #end_time=datetime.now()
            general.message('Acquisition completed')
            #print("Duration of Acquisition: {}".format(end_time - start_time))
        elif test_flag == 'test':
            pass

    def oscilloscope_preamble(self, channel):
        if test_flag != 'test':
            ch = str(channel)
            if ch in channel_dict:
                flag = channel_dict[ch]
                if flag[0] == 'C' and int(flag[-1]) <= analog_channels:
                    self.device_write(':WAVeform:SOURce ' + str(flag))
                    preamble = self.device_query_ascii(":WAVeform:PREamble?")   
                    return preamble
                else:
                    general.message("Invalid channel is given")
                    sys.exit()
            else:
                general.message("Invalid channel is given")
                sys.exit()

        elif test_flag == 'test':
            ch = str(channel)
            assert(ch in channel_dict), 'Invalid channel is given'
            flag = channel_dict[ch]
            if flag[0] == 'C' and int(flag[-1]) > analog_channels:
                assert(1 == 2), 'Invalid channel is given'
            else:
                preamble = np.arange(10)
                return preamble

    def oscilloscope_stop(self):
        if test_flag != 'test':
            self.device_write(":STOP")
        elif test_flag == 'test':
            pass

    def oscilloscope_run(self):
        if test_flag != 'test':
            self.device_write(":RUN")
        elif test_flag == 'test':
            pass

    def oscilloscope_run_stop(self):
        if test_flag != 'test':
            self.device_write(":RUN")
            general.wait('500 ms')
            self.device_write(":STOP")
        elif test_flag == 'test':
            pass

    def oscilloscope_get_curve(self, channel):
        if test_flag != 'test':
            ch = str(channel)
            if ch in channel_dict:
                flag = channel_dict[ch]
                if flag[0] == 'C' and int(flag[-1]) <= analog_channels:
                    self.device_write(':WAVeform:SOURce ' + str(flag))
                    array_y = self.device_read_binary(':WAVeform:DATA?')
                    preamble = self.device_query_ascii(":WAVeform:PREamble?")
                    #x_orig = preamble[5]
                    y_inc = preamble[7]
                    y_orig = preamble[8]
                    y_ref = preamble[9]
                    #print(y_inc)
                    #print(y_orig)
                    #print(y_ref)
                    array_y = (array_y - y_ref)*y_inc + y_orig
                    #array_x = list(map(lambda x: resolution*(x+1) + 1000000*x_orig, list(range(points))))
                    #final_data = list(zip(array_x,array_y))
                    return array_y
                else:
                    general.message("Invalid channel is given")
                    sys.exit()
            else:
                general.message("Invalid channel is given")
                sys.exit()

        elif test_flag == 'test':
            ch = str(channel)
            assert(ch in channel_dict), 'Invalid channel is given'
            flag = channel_dict[ch]
            if flag[0] == 'C' and int(flag[-1]) > analog_channels:
                assert(1 == 2), 'Invalid channel is given'
            else:
                array_y = np.arange(test_record_length)
                return array_y

    def oscilloscope_sensitivity(self, *channel):
        if test_flag != 'test':
            if len(channel) == 2:
                temp = channel[1].split(" ")
                ch = str(channel[0])
                val = float(temp[0])
                scaling = str(temp[1]);
                if scaling in scale_dict:
                    coef = scale_dict[scaling]
                    if val/coef >= sensitivity_min and val/coef <= sensitivity_max:
                        if ch in channel_dict:
                            flag = channel_dict[ch]
                            if flag[0] == 'C' and int(flag[-1]) <= analog_channels:
                                self.device_write(':' + str(flag) + ':SCALe ' + str(val/coef))
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
                if ch in channel_dict:
                    flag = channel_dict[ch]
                    if flag[0] == 'C' and int(flag[-1]) <= analog_channels:
                        answer = float(self.device_query(":" + str(flag) + ":SCALe?"))*1000
                        return answer
                    else:
                        general.message("Incorrect channel is given")
                        sys.exit()
                else:
                    general.message("Incorrect channel is given")
                    sys.exit()
            else:
                general.message("Invalid argument")
                sys.exit()

        elif test_flag == 'test':
            if len(channel) == 2:
                temp = channel[1].split(" ")
                ch = str(channel[0])
                val = float(temp[0])
                scaling = str(temp[1])
                if scaling in scale_dict:
                    coef = scale_dict[scaling]
                    assert(val/coef >= sensitivity_min and val/coef <= \
                        sensitivity_max), "Incorrect sensitivity range"
                    assert(ch in channel_dict), 'Invalid channel is given'
                    flag = channel_dict[ch]
                    if flag[0] == 'C' and int(flag[-1]) > analog_channels:
                        assert(1 == 2), 'Invalid channel is given'
                else:
                    assert(1 == 2), "Incorrect sensitivity argument"
            elif len(channel) == 1:
                ch = str(channel[0])
                assert(ch in channel_dict), 'Invalid channel is given'
                flag = channel_dict[ch]
                if flag[0] == 'C' and int(flag[-1]) > analog_channels:
                    assert(1 == 2), 'Invalid channel is given'
                else:
                    answer = test_sensitivity*1000
                    return answer
            else:
                assert(1 == 2), "Incorrect sensitivity argument"

    def oscilloscope_offset(self, *channel):
        if test_flag != 'test':
            if len(channel) == 2:
                temp = channel[1].split(" ")
                ch = str(channel[0])
                val = float(temp[0])
                scaling = str(temp[1]);
                if scaling in scale_dict:
                    coef = scale_dict[scaling]
                    if ch in channel_dict:
                        flag = channel_dict[ch]
                        if flag[0] == 'C' and int(flag[-1]) <= analog_channels:
                            self.device_write(':' + str(flag) + ':OFFSet ' + str(val/coef))
                        else:
                            general.message("Invalid channel is given")
                            sys.exit()
                    else:
                        general.message("Incorrect channel is given")
                        sys.exit()
                else:
                    general.message("Incorrect scaling factor")
                    sys.exit()

            elif len(channel) == 1:
                ch = str(channel[0])
                if ch in channel_dict:
                    flag = channel_dict[ch]
                    if flag[0] == 'C' and int(flag[-1]) <= analog_channels:
                        answer = float(self.device_query(":" + str(flag) + ":OFFSet?"))*1000
                        return answer
                    else:
                        general.message("Incorrect channel is given")
                        sys.exit()
            else:
                general.message("Invalid argument")
                sys.exit()

        elif test_flag == 'test':
            if len(channel) == 2:
                temp = channel[1].split(" ")
                ch = str(channel[0])
                val = float(temp[0])
                scaling = str(temp[1])
                if scaling in scale_dict:
                    coef = scale_dict[scaling]
                    assert(ch in channel_dict), 'Invalid channel is given'
                    flag = channel_dict[ch]
                    if flag[0] == 'C' and int(flag[-1]) > analog_channels:
                        assert(1 == 2), 'Invalid channel is given'
                else:
                    assert(1 == 2), "Incorrect offset argument"
            elif len(channel) == 1:
                ch = str(channel[0])
                assert(ch in channel_dict), 'Invalid channel is given'
                flag = channel_dict[ch]
                if flag[0] == 'C' and int(flag[-1]) > analog_channels:
                    assert(1 == 2), 'Invalid channel is given'
                else:
                    answer = test_offset*1000
                    return answer
            else:
                assert(1 == 2), "Incorrect offset argument"

    def oscilloscope_horizontal_offset(self, *h_offset):
        if test_flag != 'test':
            if len(h_offset) == 1:
                temp = h_offset[0].split(" ")
                offset = float(temp[0])
                scaling = temp[1]
                if scaling in timebase_dict:
                    coef = timebase_dict[scaling]
                    self.device_write(":TIMebase:DELay "+ str(offset/coef))
                else:
                    general.message("Incorrect horizontal offset")
                    sys.exit()
            elif len(h_offset) == 0:
                answer = float(self.device_query(":TIMebase:DELay?"))*1000000
                return answer
            else:
                general.message("Invalid argument")
                sys.exit()

        elif test_flag == 'test':
            if len(h_offset) == 1:
                temp = delay[0].split(" ")
                offset = float(temp[0])
                scaling = temp[1]
                if scaling in timebase_dict:
                    coef = timebase_dict[scaling]
                else:
                    assert(1 == 2), 'Incorrect horizontal offset scaling'
            elif len(h_offset) == 0:
                answer = test_h_offset
                return answer
            else:
                assert(1 == 2), 'Incorrect horizontal offset argument'

    def oscilloscope_coupling(self, *coupling):
        if test_flag != 'test':
            if len(coupling) == 2:
                ch = str(coupling[0])
                cpl = str(coupling[1])
                if ch in channel_dict:
                    flag = channel_dict[ch]
                    if flag[0] == 'C' and int(flag[-1]) <= analog_channels:
                        self.device_write(':' + str(flag) + ':COUPling ' + str(cpl))
                    else:
                        general.message("Invalid channel is given")
                        sys.exit()
                else:
                    general.message("Incorrect channel is given")
                    sys.exit()

            elif len(coupling) == 1:
                ch = str(coupling[0])
                if ch in channel_dict:
                    flag = channel_dict[ch]
                    if flag[0] == 'C' and int(flag[-1]) <= analog_channels:
                        answer = self.device_query(":" + str(flag) + ":COUPling?")
                        return answer
                    else:
                        general.message("Incorrect channel is given")
                        sys.exit()
                else:
                    general.message("Incorrect channel is given")
                    sys.exit()
            else:
                general.message("Invalid argument")
                sys.exit()

        elif test_flag == 'test':
            if len(coupling) == 2:
                ch = str(coupling[0])
                cpl = str(coupling[1])
                assert(ch in channel_dict), 'Invalid channel is given'
                flag = channel_dict[ch]
                if flag[0] == 'C' and int(flag[-1]) > analog_channels:
                    assert(1 == 2), 'Invalid channel is given'
                assert(cpl == 'AC' or cpl == 'DC'), 'Invalid coupling is given'
            elif len(coupling) == 1:
                ch = str(coupling[0])
                assert(ch in channel_dict), 'Invalid channel is given'
                flag = channel_dict[ch]
                if flag[0] == 'C' and int(flag[-1]) > analog_channels:
                    assert(1 == 2), 'Invalid channel is given'
                answer = test_coupling
                return answer
            else:
                asser(1 == 2), 'Invalid coupling argument'

    def oscilloscope_impedance(self, *impedance):
        if test_flag != 'test':
            if len(impedance) == 2:
                ch = str(impedance[0])
                cpl = str(impedance[1])
                if cpl == '1 M':
                    cpl = 'ONEMeg'
                elif cpl == '50':
                    cpl = 'FIFTy'
                if ch in channel_dict:
                    flag = channel_dict[ch]
                    if flag[0] == 'C' and int(flag[-1]) <= analog_channels:
                        self.device_write(':' + str(flag) + ':IMPedance ' + str(cpl))
                    else:
                        general.message("Invalid channel is given")
                        sys.exit()
                else:
                    general.message("Incorrect channel is given")
                    sys.exit()

            elif len(impedance) == 1:
                ch = str(impedance[0])
                if ch in channel_dict:
                    flag = channel_dict[ch]
                    if flag[0] == 'C' and int(flag[-1]) <= analog_channels:
                        answer = self.device_query(":" + str(flag) + ":IMPedance?")
                        return answer
                    else:
                        general.message("Incorrect channel is given")
                        sys.exit()
                else:
                    general.message("Incorrect channel is given")
                    sys.exit()
            else:
                general.message("Invalid argument")
                sys.exit()

        elif test_flag == 'test':
            if len(impedance) == 2:
                ch = str(impedance[0])
                cpl = str(impedance[1])
                assert(ch in channel_dict), 'Invalid channel is given'
                flag = channel_dict[ch]
                if flag[0] == 'C' and int(flag[-1]) > analog_channels:
                    assert(1 == 2), 'Invalid channel is given'
                assert(cpl == '1 M' or cpl == '50'), 'Invalid impedance is given'
            elif len(impedance) == 1:
                ch = str(impedance[0])
                assert(ch in channel_dict), 'Invalid channel is given'
                flag = channel_dict[ch]
                if flag[0] == 'C' and int(flag[-1]) > analog_channels:
                    assert(1 == 2), 'Invalid channel is given'
                answer = test_impedance
                return answer
            else:
                assert(1 == 2), 'Invalid impedance argument'

    def oscilloscope_trigger_mode(self, *mode):
        if test_flag != 'test':
            if len(mode) == 1:
                md = str(mode[0])
                if md == 'Auto':
                    self.device_write(":TRIGger:SWEep " + 'AUTO')
                elif md == 'Normal':
                    self.device_write(":TRIGger:SWEep " + 'NORMal')
                else:
                    general.message("Incorrect trigger mode is given")
            elif len(mode) == 0:
                answer = self.device_query(":TRIGger:SWEep?")
                return answer
            else:
                general.message("Invalid argument")
                sys.exit()

        elif test_flag == 'test':
            if len(mode) == 1:
                md = str(mode[0])
                assert(md == 'Auto' or md == 'Normal'), 'Incorrect trigger mode is given'
            elif len(mode) == 0:
                answer = test_tr_mode
                return answer
            else:
                assert(1 == 2), 'Incorrect trigger mode argument'

    def oscilloscope_trigger_channel(self, *channel):
        if test_flag != 'test':
            if len(channel) == 1:
                ch = str(channel[0])
                if ch in trigger_channel_dict:
                    flag = trigger_channel_dict[ch]
                    if flag[0] == 'C' and int(flag[-1]) <= analog_channels:
                        self.device_write(':TRIGger:EDGE:SOURce ' + str(flag))
                    elif flag[0] != 'C':
                        self.device_write(':TRIGger:EDGE:SOURce ' + str(flag))
                    else:
                        general.message("Invalid trigger channel is given")
                        sys.exit()
                else:
                    general.message("Incorrect trigger channel is given")
                    sys.exit()

            elif len(channel) == 0:
                answer = self.device_query(":TRIGger:EDGE:SOURce?")
                return answer
            else:
                general.message("Invalid argument")
                sys.exit()

        if test_flag == 'test':        
            if len(channel) == 1:
                ch = str(channel[0])
                assert(ch in trigger_channel_dict), 'Invalid trigger channel is given'
                flag = trigger_channel_dict[ch]
                if flag[0] == 'C' and int(flag[-1]) > analog_channels:
                    assert(1 == 2), 'Invalid trigger channel is given'
            elif len(channel) == 0:
                answer = test_tr_channel
                return answer
            else:
                assert(1 == 2), "Invalid trigger channel argument"

    def oscilloscope_trigger_low_level(self, *level):
        if test_flag != 'test':
            if len(level) == 2:
                ch = str(level[0])
                lvl = float(level[1])
                if ch in channel_dict:
                    flag = channel_dict[ch]
                    if flag[0] == 'C' and int(flag[-1]) <= analog_channels:
                        self.device_write(':TRIGger:LEVel:LOW ' + str(lvl) + ', ' + str(flag))
                    else:
                        general.message("Incorrect channel is given")
                        sys.exit()
                else:
                    general.message("Incorrect channel is given")
                    sys.exit()
            elif len(level) == 1:
                ch = str(level[0])
                if ch in channel_dict:
                    flag = channel_dict[ch]
                    if flag[0] == 'C' and int(flag[-1]) <= analog_channels:
                        answer = self.device_query(':TRIGger:LEVel:LOW? ' + str(flag))
                        return answer
                    else:
                        general.message("Incorrect channel is given")
                        sys.exit()
                else:
                    general.message("Incorrect channel is given")
                    sys.exit()
            else:
                general.message("Invalid argument")
                sys.exit()

        elif test_flag == 'test':
            if len(level) == 2:
                ch = str(level[0])
                lvl = float(level[1])
                assert(ch in channel_dict), 'Invalid  channel is given'
                flag = channel_dict[ch]
                if flag[0] == 'C' and int(flag[-1]) > analog_channels:
                    assert(1 == 2), 'Invalid  channel is given'
            elif len(level) == 1:
                ch = str(level[0])
                assert(ch in channel_dict), 'Invalid  channel is given'
                flag = channel_dict[ch]
                if flag[0] == 'C' and int(flag[-1]) > analog_channels:
                    assert(1 == 2), 'Invalid  channel is given'
                answer = test_trigger_level
                return answer
            else:
                assert(1 == 2), "Invalid trigger level argument"

    def oscilloscope_command(self, command):
        if test_flag != 'test':
            self.device_write(command)
        elif test_flag == 'test':
            pass

    def oscilloscope_query(self, command):
        if test_flag != 'test':
            answer = self.device_query(command)
            return answer
        elif test_flag == 'test':
            answer = None
            return answer

    #### Functions of wave generator
    def wave_gen_name(self):
        if test_flag != 'test':
            answer = self.device_query('*IDN?')
            return answer
        elif test_flag == 'test':
            answer = config['name']
            return answer

    def wave_gen_frequency(self, *frequency):
        if test_flag != 'test':
            if len(frequency) == 1:
                temp = frequency[0].split(" ")
                freq = float(temp[0])
                scaling = temp[1]
                if scaling in frequency_dict:
                    coef = frequency_dict[scaling]
                    if freq*float(coef) >= wave_gen_freq_min and freq*float(coef) <= wave_gen_freq_max:
                        self.device_write(":WGEN:FREQuency " + str(freq*coef))
                    else:
                        general.message("Incorrect frequency range")
                        sys.exit()   
                else:
                    general.message("Incorrect frequency scaling")
                    sys.exit()
            elif len(frequency) == 0:
                answer = float(self.device_query(":WGEN:FREQuency?"))
                return answer
            else:
                general.message("Invalid argument")
                sys.exit()

        elif test_flag == 'test':
            if len(frequency) == 1:
                temp = frequency[0].split(" ")
                freq = float(temp[0])
                scaling = temp[1]
                if scaling in frequency_dict:
                    coef = frequency_dict[scaling]
                    assert(freq*float(coef) >= wave_gen_freq_min and \
                        freq*float(coef) <= wave_gen_freq_max), "Incorrect frequency range"
                else:
                    assert(1 == 2), "Incorrect frequency scaling"
            elif len(frequency) == 0:
                answer = test_wave_gen_frequency
                return answer
            else:
                assert(1 == 2), "Incorrect wave generator channel" 

    def wave_gen_pulse_width(self, *width):
        if test_flag != 'test':
            answer = self.device_query(":WGEN:FUNCtion?")
            if answer == 'PULS':
                if len(width) == 1:
                    temp = width[0].split(" ")
                    wid = float(temp[0])
                    scaling = temp[1];
                    if scaling in timebase_dict:
                        coef = timebase_dict[scaling]
                        self.device_write(":WGEN:FUNCtion:PULSe:WIDTh " + str(wid/coef))
                    else:
                        general.message("Incorrect width")
                        sys.exit()
                elif len(width) == 0:
                    answer = float(self.device_query(":WGEN:FUNCtion:PULSe:WIDTh?"))*1000000
                    return answer
                else:
                    general.message("Invalid argument")
                    sys.exit()
            else:
                general.message("You are not in the pulse mode")
                sys.exit()

        elif test_flag == 'test':
            if len(width) == 1:
                temp = width[0].split(" ")
                wid = float(temp[0])
                scaling = temp[1]
                if scaling in timebase_dict:
                    coef = timebase_dict[scaling]
                else:
                    assert(1 == 2), "Incorrect width argument"
            elif len(width) == 0:
                answer = test_wave_gen_width
                return answer
            else:
                assert(1 == 2), "Incorrect width argument"

    def wave_gen_function(self, *function):
        if test_flag != 'test':
            if  len(function) == 1:
                func = str(function[0])
                if func in wavefunction_dic:
                    flag = wavefunction_dic[func]
                    self.device_write(":WGEN:FUNCtion " + str(flag))
                else:
                    general.message("Invalid wave generator function")
                    sys.exit()
            elif len(function) == 0:
                answer = str(self.device_query(':WGEN:FUNCtion?'))
                return answer
            else:
                general.message("Invalid argument")
                sys.exit()

        elif test_flag == 'test':
            if  len(function) == 1:
                func = str(function[0])
                if func in wavefunction_dic:
                    flag = wavefunction_dic[func]
                else:
                    assert(1 == 2), "Invalid wave generator function"
            elif len(function) == 0:
                answer = test_wave_gen_function
                return answer
            else:
                assert(1 == 2), "Invalid wave generator function"

    def wave_gen_amplitude(self, *amplitude):
        if test_flag != 'test':
            if len(amplitude) == 1:
                temp = amplitude[0].split(" ")
                val = float(temp[0])
                scaling = temp[1]
                if scaling in scale_dict:
                    coef = scale_dict[scaling]
                    self.device_write(":WGEN:VOLTage " + str(val/coef))
                else:
                    general.message("Incorrect amplitude")
                    sys.exit()
            elif len(amplitude) == 0:
                answer = float(self.device_query(":WGEN:VOLTage?"))*1000
                return answer
            else:
                general.message("Invalid argument")
                sys.exit()

        elif test_flag == 'test':
            if len(amplitude) == 1:
                temp = amplitude[0].split(" ")
                val = float(temp[0])
                scaling = temp[1]
                if scaling in scale_dict:
                    coef = scale_dict[scaling]
                else:
                    assert(1 == 2), "Incorrect amplitude scaling"
            elif len(amplitude) == 0:
                answer = test_wave_gen_amplitude
                return answer
            else:
                assert(1 == 2), "Incorrect amplitude argument"

    def wave_gen_offset(self, *offset):
        if test_flag != 'test':
            if len(offset) == 1:
                temp = offset[0].split(" ")
                val = float(temp[0])
                scaling = temp[1]
                if scaling in scale_dict:
                    coef = scale_dict[scaling]
                    self.device_write(":WGEN:VOLTage:OFFSet " + str(val/coef))
                else:
                    general.message("Incorrect offset voltage")
                    sys.exit()
            elif len(offset) == 0:
                answer = float(self.device_query(":WGEN:VOLTage:OFFSet?"))*1000
                return answer
            else:
                general.message("Invalid argument")
                sys.exit()

        elif test_flag == 'test':
            if len(offset) == 1:
                temp = offset[0].split(" ")
                val = float(temp[0])
                scaling = temp[1]
                if scaling in scale_dict:
                    coef = scale_dict[scaling]
                else:
                    assert(1 == 2), "Incorrect offset voltage scaling"
            elif len(offset) == 0:
                answer = test_wave_gen_offset
                return answer
            else:
                assert(1 == 2), "Incorrect offset voltage scaling"

    def wave_gen_impedance(self, *impedance):
        if test_flag != 'test':
            if len(impedance) == 1:
                cpl = str(impedance[0])
                if cpl == '1 M':
                    cpl = 'ONEMeg'
                    self.device_write(":WGEN:OUTPut:LOAD " + str(cpl))
                elif cpl == '50':
                    cpl = 'FIFTy'
                    self.device_write(":WGEN:OUTPut:LOAD " + str(cpl))
                else:
                    general.message("Incorrect impedance")
                    sys.exit()
            elif len(impedance) == 0:
                answer = str(self.device_query(":WGEN:OUTPut:LOAD?"))
                return answer
            else:
                general.message("Invalid argument")
                sys.exit()

        elif test_flag == 'test':
            if len(impedance) == 1:
                cpl = str(impedance[0])
                assert(cpl == '1 M' or cpl == '50'), "Incorrect impedance"
            elif len(impedance) == 0:
                answer = test_wave_gen_impedance
                return answer
            else:
                assert(1 == 2), "Invalid impedance argument"

    def wave_gen_run(self):
        if test_flag != 'test':
            self.device_write(":WGEN:OUTPut 1")
        elif test_flag == 'test':
            pass

    def wave_gen_stop(self):
        if test_flag != 'test':
            self.device_write(":WGEN:OUTPut 0")
        elif test_flag == 'test':
            pass

    def wave_gen_arbitrary_function(self, list):
        if test_flag != 'test':
            if len(list) > 0:
                if all(element >= -1.0 and element <= 1.0 for element in list) ==True:
                    str_to_general = ", ".join(str(x) for x in list)
                    self.device_write(":WGEN:ARBitrary:DATA " + str(str_to_general))
                else:
                    general.message('Incorrect points are used')
                    sys.exit()
            else:
                general.message('Incorrect list of points')
                sys.exit()

        elif test_flag == 'test':
            if len(list) > 0:
                if all(element >= -1.0 and element <= 1.0 for element in list) ==True:
                    str_to_general = ", ".join(str(x) for x in list)
                else:
                    assert(1 == 2), 'Incorrect points are used'
            else:
                assert(1 == 2), 'Incorrect list of points'

    def wave_gen_arbitrary_interpolation(self, *mode):
        if test_flag != 'test':
            if len(mode) == 1:
                md = str(mode[0])
                if md == 'On':
                    self.device_write(":WGEN:ARBitrary:INTerpolate 1")
                elif md == 'Off':
                    self.device_write(":WGEN:ARBitrary:INTerpolate 0")
                else:
                    general.message("Incorrect interpolation control setting is given")
                    sys.exit()
            elif len(mode) == 0:
                raw_answer = int(self.device_query(":WGEN"+str(ch)+":ARBitrary:INTerpolate?"))
                answer = cutil.search_keys_dictionary(wave_gen_interpolation_dictionary, raw_answer)
                return answer
            else:
                general.message("Invalid argument")
                sys.exit()

        elif test_flag == 'test':
            if len(mode) == 1:
                md = str(mode[0])
                assert(md == 'On' or md == 'Off'), "Incorrect interpolation control setting is given"
            elif len(mode) == 0:
                answer = test_wave_gen_interpolation
                return answer
            else:
                assert(1 == 2), "Invalid argument"

    def wave_gen_arbitrary_clear(self):
        if test_flag != 'test':
            self.device_write(":WGEN:ARBitrary:DATA:CLEar")
        elif test_flag == 'test':
            pass

    def wave_gen_arbitrary_points(self):
        if test_flag != 'test':
            answer = int(self.device_query(":WGEN:ARBitrary:DATA:ATTRibute:POINts?"))
            return answer
        elif test_flag == 'test':
            answer = test_wave_gen_points
            return answer

    def wave_gen_command(self, command):
        if test_flag != 'test':
            self.device_write(command)
        elif test_flag == 'test':
            pass

    def wave_gen_query(self, command):
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