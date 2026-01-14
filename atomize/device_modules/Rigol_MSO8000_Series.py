#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import gc
import sys
import pyvisa
import numpy as np
import pyqtgraph as pg
import atomize.main.local_config as lconf
import atomize.device_modules.config.config_utils as cutil
import atomize.general_modules.general_functions as general

class Rigol_MSO8000_Series:
    #### Basic interaction functions
    def __init__(self):

        #### Inizialization
        # setting path to *.ini file
        self.path_current_directory = lconf.load_config_device()
        self.path_config_file = os.path.join(self.path_current_directory, 'Rigol_mso8104_config.ini')

        # configuration data
        self.config = cutil.read_conf_util(self.path_config_file)
        self.specific_parameters = cutil.read_specific_parameters(self.path_config_file)

        # auxilary dictionaries
        self.points_list = [1e3, 1e4, 1e5, 1e6, 1e7, 2.5e7, 5e7, 1e8, 1.25e8]
        self.points_list_average = [1e3, 1e4, 1e5, 1e6, 1e7, 2.5e7]
        # Number of point is different for Average mode and three other modes

        self.channel_dict = {'CH1': 'CHAN1', 'CH2': 'CHAN2', 'CH3': 'CHAN3', 'CH4': 'CHAN4'}
        self.trigger_channel_dict = {'CH1': 'CHAN1', 'CH2': 'CHAN2', 'CH3': 'CHAN3', 'CH4': 'CHAN4', \
                                'Ext': 'EXT', 'Line': 'ACLine'}
        self.timebase_dict = {'s': 1, 'ms': 1000, 'us': 1000000, 'ns': 1000000000};
        self.scale_dict = {'V': 1, 'mV': 1000};
        self.frequency_dict = {'MHz': 1000000, 'kHz': 1000, 'Hz': 1, 'mHz': 0.001,};
        self.wavefunction_dic = {'Sin': 'SIN', 'Sq': 'SQU', 'Ramp': 'RAMP', 'Pulse': 'PULS',
                            'DC': 'DC', 'Noise': 'NOIS', 'Sinc': 'SINC', 'ERise': 'EXPR',
                            'EFall': 'EXPF', 'ECG': 'ECG', 'Gauss': 'GAUS',
                            'Lorentz': 'LOR', 'Haversine': 'HAV'};

        self.ac_type_dic = {'Normal': "NORM", 'Average': "AVER", 'Hres': "HRES",'Peak': "PEAK"}
        self.mode_dict = {'Normal': "NORM", 'Raw': "RAW"}
        self.wave_gen_interpolation_dictionary = {'On': 1, 'Off': 0}
        self.number_average_list = [2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384, \
                                    32768, 65536]

        # Limits and Ranges (depends on the exact model):
        self.analog_channels = int(self.specific_parameters['analog_channels'])
        self.numave_min = 2
        self.numave_max = 65536
        self.max_duty = 98
        self.min_duty = 2
        self.ampl_50_max = 2.5
        self.ampl_50_min = 0.01
        self.ampl_hz_max = 5
        self.ampl_hz_min = 0.02
        self.timebase_max = float(self.specific_parameters['timebase_max'])
        self.timebase_min = float(self.specific_parameters['timebase_min'])
        self.sensitivity_min = float(self.specific_parameters['sensitivity_min'])
        self.sensitivity_max = float(self.specific_parameters['sensitivity_max'])
        self.wave_gen_freq_max = float(self.specific_parameters['wave_gen_freq_max'])
        self.wave_gen_freq_min = float(self.specific_parameters['wave_gen_freq_min'])
        self.wave_gen = str(self.specific_parameters['wage_gen'])

        #integration window
        self.win_left = 0
        self.win_right = 1

        self.wg_coupling_1 = '1 M'
        self.wg_coupling_2 = '1 M'

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
                    self.device.timeout = self.config['timeout'] # in ms
                    #self.device.read_termination = self.config['read_termination']  # for WORD (a kind of binary) format
                    try:
                        self.device_write('*CLS')

                        # enabling fine adjustment
                        self.device_write(':TIMebase:VERNier')
                        for i in range(self.analog_channels):
                            self.device_write(f':CHANnel{i}:VERNier')

                        if self.wave_gen == 'True':
                        
                            self.wg_coupling_1 = self.device_query(":OUTPut1:IMPedance?")[:-1]
                            self.wg_coupling_2 = self.device_query(":OUTPut2:IMPedance?")[:-1]
                            if self.wg_coupling_1 == 'OMEG':
                                self.wg_coupling_1 = '1 M'
                            elif self.wg_coupling_1 == 'FIFT':
                                self.wg_coupling_1 = '50'
                            
                            if self.wg_coupling_2 == 'OMEG':
                                self.wg_coupling_2 = '1 M'
                            elif self.wg_coupling_2 == 'FIFT':
                                self.wg_coupling_2 = '50'

                        else:
                            pass
                        
                        self.status_flag = 1
                    except (pyvisa.VisaIOError, BrokenPipeError):
                        general.message(f"No connection {self.__class__.__name__}")
                        self.status_flag = 0
                        self.device.clear()
                        sys.exit()
                except (pyvisa.VisaIOError, BrokenPipeError):
                    general.message(f"No connection {self.__class__.__name__}")
                    self.status_flag = 0
                    os._exit(0)

        elif self.test_flag == 'test':
            self.test_record_length = 2000
            self.test_acquisition_type = 'Norm'
            self.test_num_aver = 2
            self.test_impedance = '1 M'
            self.test_timebase = '100 us'
            self.test_h_offset = '10 ms'
            self.test_sensitivity = '100 mV'
            self.test_offset = '1 mV'
            self.test_coupling = 'AC'
            self.test_tr_mode = 'NORMal'
            self.test_tr_channel = 'CH1'
            self.test_trigger_level = '1 mV'
            self.test_wave_gen_frequency = '500 Hz'
            self.test_wave_gen_width = '5 %'
            self.test_wave_gen_function = 'Sin'
            self.test_wave_gen_amplitude = '500 mV'
            self.test_wave_gen_offset = '0 mV'
            self.test_wave_gen_impedance = '1 M'
            self.test_wave_gen_interpolation = 'Off'
            self.test_wave_gen_points = 10
            self.test_area = 0.001
            self.test_phase = 15

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

    def device_query_ascii(self, command):
        if self.status_flag == 1:
            answer = self.device.query_ascii_values(command, converter='f', separator=',', container=np.array)
            return answer
        else:
            general.message(f"No connection {self.__class__.__name__}")
            self.status_flag = 0
            sys.exit()

    def device_read_binary(self, command):
        if self.status_flag == 1:
            answer = self.device.query_binary_values(command, 'h', is_big_endian=True, container=np.array)
            # H for 3034T; h for 2012A
            return answer
        else:
            general.message(f"No connection {self.__class__.__name__}")
            self.status_flag = 0
            sys.exit()

    def device_read_binary_H(self, command):
        if self.status_flag == 1:
            answer = self.device.query_binary_values(command, 'H', is_big_endian=False, container=np.array)
            # H for 3034T; h for 2012A
            return answer
        else:
            general.message(f"No connection {self.__class__.__name__}")
            self.status_flag = 0
            sys.exit()

    #### Device specific functions
    def oscilloscope_name(self):
        if self.test_flag != 'test':
            answer = self.device_query('*IDN?')
            return answer
        elif self.test_flag == 'test':
            answer = self.config['name']
            return answer

    def oscilloscope_record_length(self, *points):
        if self.test_flag != 'test': 
            if len(points) == 1:
                temp = int(points[0])
                test_acq_type = self.oscilloscope_acquisition_type()
                if test_acq_type == 'Average':
                    poi = int(min(self.points_list_average, key = lambda x: abs(x - temp)))
                    if int(poi) != temp:
                        general.message(f"Desired record length cannot be set, the nearest available value of {poi} is used")
                    self.device_write(":ACQuire:MDEPth " + str(poi))
                else:
                    poi = int(min(self.points_list, key = lambda x: abs(x - temp)))
                    if int(poi) != temp:
                        general.message(f"Desired record length cannot be set, the nearest available value of {poi} is used")
                    self.device_write(":ACQuire:MDEPth " + str(poi))

            elif len(points) == 0:
                answer = int(float(self.device_query(':ACQuire:MDEPth?')))
                return answer

        elif self.test_flag == 'test':
            if len(points) == 1:
                temp = int(points[0])
                if self.test_acquisition_type == 'Average':
                    poi = int(min(self.points_list, key = lambda x: abs(x - temp)))
                    self.test_record_length = poi
                else:
                    poi = int(min(self.points_list_average, key = lambda x: abs(x - temp)))
                    self.test_record_length = poi
            elif len(points) == 0:
                answer = self.test_record_length
                return answer
            else:
                assert (1 == 2), 'Invalid record length argument; points: int'

    def oscilloscope_acquisition_type(self, *ac_type):
        if self.test_flag != 'test': 
            if  len(ac_type) == 1:
                at = str(ac_type[0])
                if at in self.ac_type_dic:
                    flag = self.ac_type_dic[at]

                    # only when running
                    self.oscilloscope_run()
                    self.device_write(":ACQuire:TYPE " + str(flag))
                    # very long operation
                    while True:
                        ans = int( self.device_query("*OPC?") )
                        if ans == 1:
                            break
                        else:
                            general.wait('30 ms')

            elif len(ac_type) == 0:
                raw_answer = str(self.device_query(":ACQuire:TYPE?"))[:-1]
                answer  = cutil.search_keys_dictionary(self.ac_type_dic, raw_answer)
                return answer

        elif self.test_flag == 'test':
            if len(ac_type) == 1:
                at = str(ac_type[0])
                if at in self.ac_type_dic:
                    flag = self.ac_type_dic[at]
                else:
                    assert(1 == 2), f"Invalid acquisition type; ac_type: {list(self.ac_type_dic.keys())}"
            elif len(ac_type) == 0:
                answer = self.test_acquisition_type
                return answer
            else:
                assert (1 == 2), f'Invalid argument; ac_type: {list(self.ac_type_dic.keys())}'

    def oscilloscope_number_of_averages(self, *number_of_averages):
        if self.test_flag != 'test':
            if len(number_of_averages) == 1:
                temp = int(number_of_averages[0])
                numave = min(self.number_average_list, key = lambda x: abs(x - temp))
                if int(numave) != temp:
                    general.message(f"Desired number of averages cannot be set, the nearest available value of {numave} is used")
                    ac = self.oscilloscope_acquisition_type()
                if ac == "Average":
                    self.device_write(":ACQuire:AVERages " + str(numave))
                elif ac == 'Normal':
                    general.message("You are in NORM mode")
                elif ac == 'Hres':
                    general.message("You are in HRES mode")
                elif ac == 'Peak':
                    general.message("You are in PEAK mode")
            elif len(number_of_averages) == 0:
                answer = int(self.device_query(":ACQuire:AVERages?"))
                return answer

        elif self.test_flag == 'test':
            if len(number_of_averages) == 1:
                numave = int(number_of_averages[0])
                assert(numave >= self.numave_min and numave <= self.numave_max), \
                    f'Incorrect number of averages. The available range is from { self.numave_min} to { self.numave_max}'
            elif len(number_of_averages) == 0:
                answer = self.test_num_aver
                return answer
            else:
                assert (1 == 2), 'Invalid argument; number_of_averages: int' 

    def oscilloscope_timebase(self, *timebase):
        if self.test_flag != 'test':
            if len(timebase) == 1:
                temp = timebase[0].split(" ")
                tb = float(temp[0])
                scaling = temp[1]
                if scaling in self.timebase_dict:
                    coef = self.timebase_dict[scaling]
                    if tb/coef >= self.timebase_min and tb/coef <= self.timebase_max:
                        self.device_write(":TIMebase:MAIN:SCALe "+ str(tb/coef/10))
            elif len(timebase) == 0:
                raw_answer = 10*float(self.device_query(":TIMebase:MAIN:SCALe?"))
                answer = pg.siFormat( raw_answer, suffix = 's', precision = 3, allowUnicode = False)
                return answer

        elif self.test_flag == 'test':
            if  len(timebase) == 1:
                temp = timebase[0].split(" ")
                tb = float(temp[0])
                scaling = temp[1]
                if scaling in self.timebase_dict:
                    coef = self.timebase_dict[scaling]
                    min_tb = pg.siFormat( self.timebase_min, suffix = 's', precision = 3, allowUnicode = False)
                    max_tb = pg.siFormat( self.timebase_max, suffix = 's', precision = 3, allowUnicode = False)
                    assert(tb/coef >= self.timebase_min and tb/coef <= self.timebase_max), f"Incorrect timebase range. The available range is from {min_tb} to {max_tb}"
                else:
                    assert(1 == 2), "Incorrect timebase argument; timebase: float + [' s', ' ms', ' us', ' ns']"
            elif len(timebase) == 0:
                answer = self.test_timebase
                return answer
            else:
                assert (1 == 2), "Incorrect timebase argument; timebase: float + [' s', ' ms', ' us', ' ns']"

    def oscilloscope_time_resolution(self):
        if self.test_flag != 'test':
            points = int(self.oscilloscope_record_length())
            raw_answer = 10 * float(self.device_query(":TIMebase:MAIN:SCALe?")) / points
            answer = pg.siFormat( raw_answer, suffix = 's', precision = 9, allowUnicode = False)
            return answer
        elif self.test_flag == 'test':
            raw_answer = pg.siEval(self.test_timebase) / self.test_record_length
            answer = pg.siFormat( raw_answer, suffix = 's', precision = 9, allowUnicode = False)
            return answer
    
    def oscilloscope_start_acquisition(self):
        if self.test_flag != 'test':
            self.device_write(':CLEar')
            self.oscilloscope_run()
        elif self.test_flag == 'test':
            pass

    def oscilloscope_preamble(self, channel):
        if self.test_flag != 'test':
            ch = str(channel)
            if ch in self.channel_dict:
                flag = self.channel_dict[ch]
                if flag[0] == 'C' and int(flag[-1]) <= self.analog_channels:
                    self.device_write(':WAVeform:SOURce ' + str(flag))
                    preamble = self.device_query_ascii(":WAVeform:PREamble?")   
                    return preamble

        elif self.test_flag == 'test':
            ch = str(channel)
            assert(ch in self.channel_dict), f'Invalid channel is given; channel: {list(self.channel_dict.keys())}'
            flag = self.channel_dict[ch]
            if flag[0] == 'C' and int(flag[-1]) > self.analog_channels:
                assert(1 == 2), f'Invalid channel is given; channel: {list(self.channel_dict.keys())}'
            else:
                preamble = np.arange(10)
                return preamble

    def oscilloscope_stop(self):
        if self.test_flag != 'test':
            self.device_write(":STOP")
        elif self.test_flag == 'test':
            pass

    def oscilloscope_run(self):
        if self.test_flag != 'test':
            self.device_write(":RUN")
        elif self.test_flag == 'test':
            pass

    def oscilloscope_run_stop(self):
        if self.test_flag != 'test':
            self.device_write(":RUN")
            general.wait('500 ms')
            self.device_write(":STOP")
        elif self.test_flag == 'test':
            pass

    def oscilloscope_get_curve(self, channel, integral = False, mode = 'Normal'):
        if self.test_flag != 'test':
            ch = str(channel)
            if ch in self.channel_dict:
                flag = self.channel_dict[ch]
                if flag[0] == 'C' and int(flag[-1]) <= self.analog_channels:

                    if mode == 'Normal':
                        self.device_write(':WAVeform:SOURce ' + str(flag))
                        self.device_write(f':WAVeform:MODE {self.mode_dict[mode]}')
                        self.device_write(':WAVeform:FORM WORD')
                    elif mode == 'Raw':
                        self.oscilloscope_stop()
                        self.device_write(':WAVeform:SOURce ' + str(flag))
                        self.device_write(f':WAVeform:MODE {self.mode_dict[mode]}')
                        self.device_write(':WAVeform:FORM WORD')
                        points = int(float(self.device_query(':ACQuire:MDEPth?')))
                        self.device_write(f':WAVeform:POINTs {points}')

                    ac_type = str(self.device_query(":ACQuire:TYPE?"))[:-1]
                    if ac_type == 'NORM':
                        array_y = self.device_read_binary(':WAVeform:DATA?')
                    else:
                        array_y = self.device_read_binary_H(':WAVeform:DATA?')

                    preamble = self.device_query_ascii(":WAVeform:PREamble?")

                    x_inc = preamble[4]
                    x_orig = preamble[5]
                    #x_ref = preamble[6]
                    y_inc = preamble[7]
                    y_orig = preamble[8]
                    y_ref = preamble[9]

                    if ac_type == 'NORM':
                        array_y = (array_y - 128) / 256 * y_inc * 65536
                    else:
                        array_y = (array_y - y_ref) * y_inc 
                    #xs = x_orig + np.arange( len(array_y) ) * x_inc

                    if integral == False:
                        return array_y
                    elif integral == True:
                        integ = np.sum( array_y[self.win_left:self.win_right] ) * ( pg.siEval(self.oscilloscope_time_resolution()) )
                        return integ
                    elif integral == 'Both':
                        integ = np.sum( array_y[self.win_left:self.win_right] ) * ( pg.siEval(self.oscilloscope_time_resolution()) )
                        xs = x_orig + np.arange( len(array_y) ) * x_inc
                        return xs, array_y, integ

        elif self.test_flag == 'test':
            ch = str(channel)
            assert(ch in self.channel_dict), f'Invalid channel is given; channel: {list(self.channel_dict.keys())}'
            flag = self.channel_dict[ch]
            if flag[0] == 'C' and int(flag[-1]) > self.analog_channels:
                assert(1 == 2), f'Invalid channel is given; channel: {list(self.channel_dict.keys())}'
            else:
                if mode == 'Normal':
                    array_y = np.arange(1000)
                    xs = np.arange(1000)
                elif mode == 'Raw':
                    array_y = np.arange(self.test_record_length)
                    xs = np.arange(self.test_record_length)

                if integral == False:
                    return array_y
                elif integral == True:
                    integ = np.sum( array_y[self.win_left:self.win_right] ) * ( pg.siEval(self.oscilloscope_time_resolution()) )
                    return integ
                elif integral == 'Both':
                    integ = np.sum( array_y[self.win_left:self.win_right] ) * ( pg.siEval(self.oscilloscope_time_resolution()) )
                    xs = np.arange( len(array_y) ) * ( pg.siEval(self.oscilloscope_time_resolution()) )
                    return xs, array_y, integ

    def oscilloscope_area(self, channel):
        if self.test_flag != 'test':
            ch = str(channel)
            if ch in self.channel_dict:
                flag = self.channel_dict[ch]
                if flag[0] == 'C' and int(flag[-1]) <= self.analog_channels:
                    area = float(self.device_query(':MEASure:ITEM? MARea,' + str(flag)))
                    return area

        elif self.test_flag == 'test':
            ch = str(channel)
            assert(ch in self.channel_dict), f'Invalid channel is given; channel: {list(self.channel_dict.keys())}'
            flag = self.channel_dict[ch]
            if flag[0] == 'C' and int(flag[-1]) > self.analog_channels:
                assert(1 == 2), f'Invalid channel is given; channel: {list(self.channel_dict.keys())}'
            else:
                return self.test_area

    def oscilloscope_sensitivity(self, *channel):
        if self.test_flag != 'test':
            if len(channel) == 2:
                temp = channel[1].split(" ")
                ch = str(channel[0])
                val = int(temp[0])
                scaling = str(temp[1]);
                if scaling in self.scale_dict:
                    coef = self.scale_dict[scaling]
                    if val/coef >= self.sensitivity_min and val/coef <= self.sensitivity_max:
                        if ch in self.channel_dict:
                            flag = self.channel_dict[ch]
                            if flag[0] == 'C' and int(flag[-1]) <= self.analog_channels:
                                self.device_write(':' + str(flag) + ':SCALe ' + str(float(val/coef)))

            elif len(channel) == 1:
                ch = str(channel[0])
                if ch in self.channel_dict:
                    flag = self.channel_dict[ch]
                    if flag[0] == 'C' and int(flag[-1]) <= self.analog_channels:
                        raw_answer = float(self.device_query(":" + str(flag) + ":SCALe?"))
                        answer = pg.siFormat( raw_answer, suffix = 'V', precision = 3, allowUnicode = False)
                        return answer

        elif self.test_flag == 'test':
            if len(channel) == 2:
                temp = channel[1].split(" ")
                ch = str(channel[0])
                val = int(temp[0])
                scaling = str(temp[1])
                if scaling in self.scale_dict:
                    coef = self.scale_dict[scaling]

                    min_sens = pg.siFormat( self.sensitivity_min, suffix = 'V', precision = 3, allowUnicode = False)
                    max_sens = pg.siFormat( self.sensitivity_max, suffix = 'V', precision = 3, allowUnicode = False)
                    assert(val/coef >= self.sensitivity_min and val/coef <= \
                        self.sensitivity_max), f"Incorrect sensitivity range. The available range is from {min_sens} to {max_sens}"
                    assert(ch in self.channel_dict), f'Invalid channel is given; channel: {list(self.channel_dict.keys())}'     
                    flag = self.channel_dict[ch]
                    if flag[0] == 'C' and int(flag[-1]) > self.analog_channels:
                        assert(1 == 2), f'Invalid channel is given; channel: {list(self.channel_dict.keys())}'
                else:
                    assert(1 == 2), f"Incorrect sensitivity argument; sensitivity: int; channel: {list(self.channel_dict.keys())}"
            elif len(channel) == 1:
                ch = str(channel[0])
                assert(ch in self.channel_dict),  f'Invalid channel is given; channel: {list(self.channel_dict.keys())}'
                flag = self.channel_dict[ch]
                if flag[0] == 'C' and int(flag[-1]) > self.analog_channels:
                    assert(1 == 2),  f'Invalid channel is given; channel: {list(self.channel_dict.keys())}'
                else:
                    answer = self.test_sensitivity
                    return answer
            else:
                assert(1 == 2), f"Incorrect sensitivity argument; sensitivity: int; channel: {list(self.channel_dict.keys())}"

    def oscilloscope_offset(self, *channel):
        if self.test_flag != 'test':
            if len(channel) == 2:
                temp = channel[1].split(" ")
                ch = str(channel[0])
                val = int(temp[0])
                scaling = str(temp[1]);
                if scaling in self.scale_dict:
                    coef = self.scale_dict[scaling]
                    if ch in self.channel_dict:
                        flag = self.channel_dict[ch]
                        if flag[0] == 'C' and int(flag[-1]) <= self.analog_channels:
                            self.device_write(':' + str(flag) + ':OFFSet ' + str(float(val/coef)))

            elif len(channel) == 1:
                ch = str(channel[0])
                if ch in self.channel_dict:
                    flag = self.channel_dict[ch]
                    if flag[0] == 'C' and int(flag[-1]) <= self.analog_channels:
                        raw_answer = float(self.device_query(":" + str(flag) + ":OFFSet?"))
                        answer = pg.siFormat( raw_answer, suffix = 'V', precision = 3, allowUnicode = False)
                        return answer

        elif self.test_flag == 'test':
            if len(channel) == 2:
                temp = channel[1].split(" ")
                ch = str(channel[0])
                val = int(temp[0])
                scaling = str(temp[1])
                if scaling in self.scale_dict:
                    coef = self.scale_dict[scaling]
                    assert(ch in self.channel_dict), f'Invalid channel is given; channel: {list(self.channel_dict.keys())}'
                    flag = self.channel_dict[ch]
                    if flag[0] == 'C' and int(flag[-1]) > self.analog_channels:
                        assert(1 == 2), f'Invalid channel is given; channel: {list(self.channel_dict.keys())}'
                else:
                    assert(1 == 2), f"Incorrect offset argument; offset: 'int + [' mV', ' V']; channel: {list(self.channel_dict.keys())}"
            elif len(channel) == 1:
                ch = str(channel[0])
                assert(ch in self.channel_dict), f'Invalid channel is given; channel: {list(self.channel_dict.keys())}'
                flag = self.channel_dict[ch]
                if flag[0] == 'C' and int(flag[-1]) > self.analog_channels:
                    assert(1 == 2), f'Invalid channel is given; channel: {list(self.channel_dict.keys())}'
                else:
                    answer = self.test_offset
                    return answer
            else:
                assert(1 == 2), f"Incorrect offset argument; offset: 'int + [' mV', ' V']; channel: {list(self.channel_dict.keys())}"

    def oscilloscope_horizontal_offset(self, *h_offset):
        if self.test_flag != 'test':
            if len(h_offset) == 1:
                temp = h_offset[0].split(" ")
                offset = float(temp[0])
                scaling = temp[1]
                if scaling in self.timebase_dict:
                    coef = self.timebase_dict[scaling]
                    # :TIMebase:DELay:SCALe <scale>
                    self.device_write(":TIMebase:OFFSet "+ str(offset/coef))

            elif len(h_offset) == 0:
                raw_answer = float(self.device_query(":TIMebase:OFFSet?"))
                answer = pg.siFormat( raw_answer, suffix = 's', precision = 6, allowUnicode = False)
                return answer

        elif self.test_flag == 'test':
            if len(h_offset) == 1:
                temp = h_offset[0].split(" ")
                offset = float(temp[0])
                scaling = temp[1]
                if scaling in self.timebase_dict:
                    coef = self.timebase_dict[scaling]
                else:
                    assert(1 == 2), "Incorrect horizontal offset argument; h_offset: float + [' s', ' ms', ' us', ' ns']"
            elif len(h_offset) == 0:
                answer = self.test_h_offset
                return answer
            else:
                assert(1 == 2), "Incorrect horizontal offset argument; h_offset: float + [' s', ' ms', ' us', ' ns']"

    def oscilloscope_coupling(self, *coupling):
        """
        AC only for 1 M impedance
        """
        if self.test_flag != 'test':
            if len(coupling) == 2:
                ch = str(coupling[0])
                cpl = str(coupling[1])
                if ch in self.channel_dict:
                    flag = self.channel_dict[ch]
                    if flag[0] == 'C' and int(flag[-1]) <= self.analog_channels:
                        imp = self.device_query(":" + str(flag) + ":IMPedance?")[:-1]
                        if cpl == 'AC':
                            if imp == 'OMEG':
                                self.device_write(':' + str(flag) + ':COUPling ' + str(cpl))
                            elif imp == 'FIFT':
                                general.message("AC couping is not available for '50' impedance")
                        else:
                            self.device_write(':' + str(flag) + ':COUPling ' + str(cpl))

            elif len(coupling) == 1:
                ch = str(coupling[0])
                if ch in self.channel_dict:
                    flag = self.channel_dict[ch]
                    if flag[0] == 'C' and int(flag[-1]) <= self.analog_channels:
                        answer = self.device_query(":" + str(flag) + ":COUPling?")[:-1]
                        return answer

        elif self.test_flag == 'test':
            if len(coupling) == 2:
                ch = str(coupling[0])
                cpl = str(coupling[1])
                assert(ch in self.channel_dict), f'Invalid channel is given; channel: {list(self.channel_dict.keys())}'
                flag = self.channel_dict[ch]
                if flag[0] == 'C' and int(flag[-1]) > self.analog_channels:
                    assert(1 == 2), f'Invalid channel is given; channel: {list(self.channel_dict.keys())}'
                assert(cpl == 'AC' or cpl == 'DC'), "Invalid coupling argument; coupling: ['AC', 'DC']"
            elif len(coupling) == 1:
                ch = str(coupling[0])
                assert(ch in self.channel_dict), f'Invalid channel is given; channel: {list(self.channel_dict.keys())}'
                flag = self.channel_dict[ch]
                if flag[0] == 'C' and int(flag[-1]) > self.analog_channels:
                    assert(1 == 2), f'Invalid channel is given; channel: {list(self.channel_dict.keys())}'
                answer = self.test_coupling
                return answer
            else:
                asser(1 == 2), "Invalid coupling argument; coupling: ['AC', 'DC']"

    def oscilloscope_impedance(self, *impedance):
        if self.test_flag != 'test':
            if len(impedance) == 2:
                ch = str(impedance[0])
                cpl = str(impedance[1])
                if cpl == '1 M':
                    cpl = 'OMEG'
                elif cpl == '50':
                    cpl = 'FIFTy'
                if ch in self.channel_dict:
                    flag = self.channel_dict[ch]
                    if flag[0] == 'C' and int(flag[-1]) <= self.analog_channels:
                        self.device_write(':' + str(flag) + ':IMPedance ' + str(cpl))

            elif len(impedance) == 1:
                ch = str(impedance[0])
                if ch in self.channel_dict:
                    flag = self.channel_dict[ch]
                    if flag[0] == 'C' and int(flag[-1]) <= self.analog_channels:
                        raw_answer = self.device_query(":" + str(flag) + ":IMPedance?")[:-1]
                        if raw_answer == 'OMEG':
                            return '1 M'
                        elif raw_answer == 'FIFT':
                            return '50'

        elif self.test_flag == 'test':
            if len(impedance) == 2:
                ch = str(impedance[0])
                cpl = str(impedance[1])
                assert(ch in self.channel_dict), f'Invalid channel is given; channel: {list(self.channel_dict.keys())}'
                flag = self.channel_dict[ch]
                if flag[0] == 'C' and int(flag[-1]) > self.analog_channels:
                    assert(1 == 2), f'Invalid channel is given; channel: {list(self.channel_dict.keys())}'
                assert(cpl == '1 M' or cpl == '50'), "Invalid impedance argument; impedance: ['1 M', '50']"
            elif len(impedance) == 1:
                ch = str(impedance[0])
                assert(ch in self.channel_dict), f'Invalid channel is given; channel: {list(self.channel_dict.keys())}'
                flag = self.channel_dict[ch]
                if flag[0] == 'C' and int(flag[-1]) > self.analog_channels:
                    assert(1 == 2), f'Invalid channel is given; channel: {list(self.channel_dict.keys())}'
                answer = self.test_impedance
                return answer
            else:
                assert(1 == 2), "Invalid impedance argument; impedance: ['1 M', '50']"
    
    def oscilloscope_trigger_mode(self, *mode):
        if self.test_flag != 'test':
            if len(mode) == 1:
                md = str(mode[0])
                if md == 'Auto':
                    self.device_write(":TRIGger:SWEep " + 'AUTO')
                elif md == 'Normal':
                    self.device_write(":TRIGger:SWEep " + 'NORMal')
            elif len(mode) == 0:
                answer = self.device_query(":TRIGger:SWEep?")[:-1]
                return answer

        elif self.test_flag == 'test':
            if len(mode) == 1:
                md = str(mode[0])
                assert(md == 'Auto' or md == 'Normal'), "Incorrect trigger mode argumnet; mode: ['Auto', 'Normal']"
            elif len(mode) == 0:
                answer = self.test_tr_mode
                return answer
            else:
                assert(1 == 2), "Incorrect trigger mode argumnet; mode: ['Auto', 'Normal']"

    def oscilloscope_trigger_channel(self, *channel):
        if self.test_flag != 'test':
            if len(channel) == 1:
                ch = str(channel[0])
                if ch in self.trigger_channel_dict:
                    flag = self.trigger_channel_dict[ch]
                    if flag[0] == 'C' and int(flag[-1]) <= self.analog_channels:
                        self.device_write(':TRIGger:EDGE:SOURce ' + str(flag))
                    elif flag[0] != 'C':
                        self.device_write(':TRIGger:EDGE:SOURce ' + str(flag))

            elif len(channel) == 0:
                answer = self.device_query(":TRIGger:EDGE:SOURce?")[:-1]
                return answer

        if self.test_flag == 'test':        
            if len(channel) == 1:
                ch = str(channel[0])
                assert(ch in self.trigger_channel_dict), f'Invalid trigger channel is given; channel: {list(self.trigger_channel_dict.keys())}'
                flag = self.trigger_channel_dict[ch]
                if flag[0] == 'C' and int(flag[-1]) > self.analog_channels:
                    assert(1 == 2), f'Invalid trigger channel is given; channel: {list(self.trigger_channel_dict.keys())}'
            elif len(channel) == 0:
                answer = self.test_tr_channel
                return answer
            else:
                assert(1 == 2), f'Invalid trigger channel is given; channel: {list(self.trigger_channel_dict.keys())}'

    def oscilloscope_trigger_low_level(self, *level):
        if self.test_flag != 'test':
            if len(level) == 2:
                self.device_write(':TRIGger:MODE EDGE')
                ch = str(level[0])
                lvl = pg.siEval(level[1])
                if ch in self.channel_dict:
                    flag = self.channel_dict[ch]
                    if flag[0] == 'C' and int(flag[-1]) <= self.analog_channels:
                        self.device_write(':TRIGger:EDGE:LEVel ' + str(lvl))

            elif len(level) == 1:
                ch = str(level[0])
                if ch in self.channel_dict:
                    flag = self.channel_dict[ch]
                    if flag[0] == 'C' and int(flag[-1]) <= self.analog_channels:
                        raw_answer = float(self.device_query(':TRIGger:EDGE:LEVel?'))
                        answer = pg.siFormat( raw_answer, suffix = 'V', precision = 3, allowUnicode = False)
                        return answer
 
        elif self.test_flag == 'test':
            if len(level) == 2:
                ch = str(level[0])
                lvl = pg.siEval(level[1])
                assert(ch in self.channel_dict), f'Invalid trigger channel is given; channel: {list(self.trigger_channel_dict.keys())}'
                flag = self.channel_dict[ch]
                if flag[0] == 'C' and int(flag[-1]) > self.analog_channels:
                    assert(1 == 2), f'Invalid trigger channel is given; channel: {list(self.trigger_channel_dict.keys())}'
            elif len(level) == 1:
                ch = str(level[0])
                assert(ch in self.channel_dict), f'Invalid trigger channel is given; channel: {list(self.trigger_channel_dict.keys())}'
                flag = self.channel_dict[ch]
                if flag[0] == 'C' and int(flag[-1]) > self.analog_channels:
                    assert(1 == 2), f'Invalid trigger channel is given; channel: {list(self.trigger_channel_dict.keys())}'
                answer = self.test_trigger_level
                return answer
            else:
                assert(1 == 2), f"Invalid trigger level argument; channel: {list(self.trigger_channel_dict.keys())}; level: float"

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

    def oscilloscope_window(self):
        """
        Special function for reading integration window
        """
        return ( self.win_right - self.win_left ) * ( pg.siEval(self.oscilloscope_time_resolution()) )

    def oscilloscope_read_settings(self):
        """
        Special function for reading settings of the oscilloscope from the special file
        """
        if self.test_flag != 'test':

            path_to_main = os.path.abspath( os.getcwd() )
            path_file = os.path.join(path_to_main, 'atomize/control_center/digitizer.param')
            file_to_read = open(path_file, 'r')

            text_from_file = file_to_read.read().split('\n')
            # ['Points: 224', 'Sample Rate: 250', 'Posstriger: 16', 'Range: 500', 'CH0 Offset: 0', 'CH1 Offset: 0', 
            # 'Window Left: 0', 'Window Right: 0', '']

            #self.points = int( text_from_file[0].split(' ')[1] )
            
            #self.sample_rate = int( text_from_file[1].split(' ')[2] )
            
            #self.posttrig_points = int( text_from_file[2].split(' ')[1] )
            
            #self.amplitude_0 = int( text_from_file[3].split(' ')[1] )
            #self.amplitude_1 = int( text_from_file[3].split(' ')[1] )
            
            #self.offset_0 = int( text_from_file[4].split(' ')[2] )
            #self.offset_1 = int( text_from_file[5].split(' ')[2] )
            
            self.win_left = int( text_from_file[6].split(' ')[2] )
            self.win_right = 1 + int( text_from_file[7].split(' ')[2] )

            #self.digitizer_setup()

        elif self.test_flag == 'test':
            
            path_to_main = os.path.abspath( os.getcwd() )
            path_file = os.path.join(path_to_main, 'atomize/control_center/digitizer.param')
            file_to_read = open(path_file, 'r')

            text_from_file = file_to_read.read().split('\n')
            # ['Points: 224', 'Sample Rate: 250', 'Posstriger: 16', 'Range: 500', 'CH0 Offset: 0', 'CH1 Offset: 0', 
            # 'Window Left: 0', 'Window Right: 0', '']

            #points = int( text_from_file[0].split(' ')[1] )
            #self.digitizer_number_of_points( points )

            #sample_rate = int( text_from_file[1].split(' ')[2] )
            #self.digitizer_sample_rate( sample_rate )

            #posttrigger = int( text_from_file[2].split(' ')[1] )
            #self.digitizer_posttrigger( posttrigger )

            #amplitude = int( text_from_file[3].split(' ')[1] )
            #self.digitizer_amplitude( amplitude )

            #ch0_offset = int( text_from_file[4].split(' ')[2] )
            #ch1_offset = int( text_from_file[5].split(' ')[2] )
            #self.digitizer_offset('CH0', ch0_offset, 'CH1', ch1_offset)

            self.win_left = int( text_from_file[6].split(' ')[2] )
            self.win_right = 1 + int( text_from_file[7].split(' ')[2] )
    
    #### Functions of waveform generator
    def wave_gen_name(self):
        if self.test_flag != 'test':
            answer = self.device_query('*IDN?')
            return answer
        elif self.test_flag == 'test':
            answer = self.config['name']
            return answer

    def wave_gen_frequency(self, *frequency, channel = '1'):
        if self.test_flag != 'test':
            ch = channel
            if ch == '1' or ch == '2':
                if len(frequency) == 1:
                    temp = frequency[0].split(" ")
                    freq = float(temp[0])
                    scaling = temp[1]
                    if scaling in self.frequency_dict:
                        coef = self.frequency_dict[scaling]
                        if freq*float(coef) >= self.wave_gen_freq_min and freq*float(coef) <= self.wave_gen_freq_max:
                            self.device_write( f":SOURce{ch}:FREQuency:FIXed {freq*coef}" )

                elif len(frequency) == 0:
                    raw_answer = float(self.device_query( f":SOURce{ch}:FREQuency:FIXed?" ) )
                    answer = pg.siFormat( raw_answer, suffix = 'Hz', precision = 6, allowUnicode = False)
                    return answer

        elif self.test_flag == 'test':
            ch = channel
            assert(ch == '1' or ch == '2'), "Incorrect waveform generator channel; channel: ['1', '2']"
            if len(frequency) == 1:
                temp = frequency[0].split(" ")
                freq = float(temp[0])
                scaling = temp[1]
                if scaling in self.frequency_dict:
                    coef = self.frequency_dict[scaling]
                    f_min = pg.siFormat( self.wave_gen_freq_min, suffix = 'Hz', precision = 3, allowUnicode = False)
                    f_max = pg.siFormat( self.wave_gen_freq_max, suffix = 'Hz', precision = 3, allowUnicode = False)
                    assert(freq*float(coef) >= self.wave_gen_freq_min and \
                        freq*float(coef) <= self.wave_gen_freq_max), f"Incorrect frequency range. The available range is from {f_min} to {f_max}"
                else:
                    assert(1 == 2), "Incorrect argument; frequency: float + [' MHz', ' kHz', ' Hz', ' mHz']; channel: ['1', '2']"
            elif len(frequency) == 0:
                answer = self.test_wave_gen_frequency
                return answer
            else:
                assert(1 == 2), "Incorrect argument; frequency: float + [' MHz', ' kHz', ' Hz', ' mHz']; channel: ['1', '2']"

    def wave_gen_pulse_width(self, *width, channel = '1'):
        if self.test_flag != 'test':
            ch = channel
            if ch == '1' or ch == '2':
                answer = self.device_query(f":SOURce{ch}:FUNCtion:SHAPe?")[:-1]
                if answer == 'PULS':
                    if len(width) == 1:
                        temp = width[0]
                        wid = int(temp)
                        self.device_write(f":SOURce{ch}:PULSe:DCYCle {wid}")

                    elif len(width) == 0:
                        raw_answer = float(self.device_query(f":SOURce{ch}:PULSe:DCYCle?"))
                        return f"{raw_answer} %"
                else:
                    general.message(f"You are not using the pulsed function of the waveform generator {self.__class__.__name__}")

        elif self.test_flag == 'test':
            ch = channel
            assert(ch == '1' or ch == '2'), "Incorrect waveform generator channel; channel: ['1', '2']"
            if len(width) == 1:
                temp = width[0]
                wid = int(temp)
                assert( wid >= self.min_duty and \
                        wid <= self.max_duty), f"Incorrect duty cycle. The available range is from {self.min_duty} to {self.max_duty}"
            elif len(width) == 0:
                answer = self.test_wave_gen_width
                return answer
            else:
                assert(1 == 2), "Incorrect argument; duty_cycle: int; channel: ['1', '2']"

    def wave_gen_function(self, *function, channel = '1'):
        if self.test_flag != 'test':
            ch = channel
            if ch == '1' or ch == '2':
                if len(function) == 1:
                    func = str(function[0])
                    if func in self.wavefunction_dic:
                        flag = self.wavefunction_dic[func]
                        self.device_write(f":SOURce{ch}:FUNCtion:SHAPe {flag}")

                elif len(function) == 0:
                    raw_answer = str(self.device_query(f":SOURce{ch}:FUNCtion:SHAPe?"))[:-1]
                    answer = cutil.search_keys_dictionary(self.wavefunction_dic, raw_answer)
                    return answer

        if self.test_flag == 'test':
            ch = channel
            assert(ch == '1' or ch == '2'), "Incorrect waveform generator channel; channel: ['1', '2']"
            if len(function) == 1:
                func = str(function[0])
                if func in self.wavefunction_dic:
                    flag = self.wavefunction_dic[func]
                else:
                    assert(1 == 2), f"Invalid waveform generator function. Available options are {list(self.wavefunction_dic.keys())}"
            elif len(function) == 0:
                answer = self.test_wave_gen_function
                return answer
            else:
                assert(1 == 2), f"Invalid argument; function: {list(self.wavefunction_dic.keys())}; channel: ['1', '2']"

    def wave_gen_amplitude(self, *amplitude, channel = '1'):
        if self.test_flag != 'test':
            ch = channel
            if ch == '1' or ch == '2':
                if len(amplitude) == 1:
                    temp = amplitude[0]
                    val = pg.siEval(temp)
                    ampl_50_max = pg.siFormat( self.ampl_50_max, suffix = 'V', precision = 3, allowUnicode = False)
                    ampl_50_min = pg.siFormat( self.ampl_50_min, suffix = 'V', precision = 3, allowUnicode = False)
                    ampl_hz_max = pg.siFormat( self.ampl_hz_max, suffix = 'V', precision = 3, allowUnicode = False)
                    ampl_hz_min = pg.siFormat( self.ampl_hz_min, suffix = 'V', precision = 3, allowUnicode = False)

                    if ch == '1':
                        if self.wg_coupling_1 == '1 M':
                            if (val >= self.ampl_hz_min and val <= self.ampl_hz_max):
                                self.device_write(f":SOURce{ch}:VOLTage:LEVel:IMMediate:AMPLitude {val}")
                            else:    
                                f"Invalid amplitude range. Available ranges are (i) '1 M' {ampl_hz_min} - {ampl_hz_max}; (ii) '50' {ampl_50_min} - {ampl_50_max}"
                        elif self.wg_coupling_1 == '50':
                            if (val >= self.ampl_50_min and val <= self.ampl_50_max):
                                self.device_write(f":SOURce{ch}:VOLTage:LEVel:IMMediate:AMPLitude {val}")
                            else:    
                                f"Invalid amplitude range. Available ranges are (i) '1 M' {ampl_hz_min} - {ampl_hz_max}; (ii) '50' {ampl_50_min} - {ampl_50_max}"
                    
                    elif ch == '2':
    
                        if self.wg_coupling_2 == '1 M':
                            if (val >= self.ampl_hz_min and val <= self.ampl_hz_max):
                                self.device_write(f":SOURce{ch}:VOLTage:LEVel:IMMediate:AMPLitude {val}")
                            else:    
                                f"Invalid amplitude range. Available ranges are (i) '1 M' {ampl_hz_min} - {ampl_hz_max}; (ii) '50' {ampl_50_min} - {ampl_50_max}"
                        elif self.wg_coupling_2 == '50':
                            if (val >= self.ampl_50_min and val <= self.ampl_50_max):
                                self.device_write(f":SOURce{ch}:VOLTage:LEVel:IMMediate:AMPLitude {val}")
                            else:    
                                f"Invalid amplitude range. Available ranges are (i) '1 M' {ampl_hz_min} - {ampl_hz_max}; (ii) '50' {ampl_50_min} - {ampl_50_max}"

                elif len(amplitude) == 0:
                    raw_answer = float(self.device_query( f":SOURce{ch}:VOLTage:LEVel:IMMediate:AMPLitude?" ) )
                    answer = pg.siFormat( raw_answer, suffix = 'V', precision = 3, allowUnicode = False)
                    return answer

        elif self.test_flag == 'test':
            ch = channel
            assert(ch == '1' or ch == '2'), "Incorrect waveform generator channel; channel: ['1', '2']"
            if len(amplitude) == 1:
                temp = amplitude[0]
                val = pg.siEval(temp)
                ampl_50_max = pg.siFormat( self.ampl_50_max, suffix = 'V', precision = 3, allowUnicode = False)
                ampl_50_min = pg.siFormat( self.ampl_50_min, suffix = 'V', precision = 3, allowUnicode = False)
                ampl_hz_max = pg.siFormat( self.ampl_hz_max, suffix = 'V', precision = 3, allowUnicode = False)
                ampl_hz_min = pg.siFormat( self.ampl_hz_min, suffix = 'V', precision = 3, allowUnicode = False)
                if ch == '1':
                    if self.wg_coupling_1 == '1 M':
                        assert(val >= self.ampl_hz_min and val <= self.ampl_hz_max), f"Invalid amplitude range. Available ranges are (i) '1 M' {ampl_hz_min} - {ampl_hz_max}; (ii) '50' {ampl_50_min} - {ampl_50_max}"
                    elif self.wg_coupling_1 == '50':
                        assert(val >= self.ampl_50_min and val <= self.ampl_50_max), f"Invalid amplitude range. Available ranges are (i) '1 M' {ampl_hz_min} - {ampl_hz_max}; (ii) '50' {ampl_50_min} - {ampl_50_max}"
                elif ch == '2':
                    if self.wg_coupling_2 == '1 M':
                        assert(val >= self.ampl_hz_min and val <= self.ampl_hz_max), f"Invalid amplitude range. Available ranges are (i) '1 M' {ampl_hz_min} - {ampl_hz_max}; (ii) '50' {ampl_50_min} - {ampl_50_max}"
                    elif self.wg_coupling_2 == '50':
                        assert(val >= self.ampl_50_min and val <= self.ampl_50_max), f"Invalid amplitude range. Available ranges are (i) '1 M' {ampl_hz_min} - {ampl_hz_max}; (ii) '50' {ampl_50_min} - {ampl_50_max}"

            elif len(amplitude) == 0:
                answer = self.test_wave_gen_amplitude
                return answer
            else:
                assert(1 == 2), f"Invalid argument; amplitude: float + [' V', ' mV']; channel: ['1', '2']"

    def wave_gen_offset(self, *offset, channel = '1'):
        if self.test_flag != 'test':
            ch = channel
            if ch == '1' or ch == '2':
                if len(offset) == 1:
                    temp = offset[0].split(" ")
                    val = float(temp[0])
                    scaling = temp[1]
                    if scaling in self.scale_dict:
                        coef = self.scale_dict[scaling]
                        self.device_write(f":SOURce{ch}:VOLTage:LEVel:IMMediate:OFFSet {val/coef}")

                elif len(offset) == 0:
                    raw_answer = float(self.device_query( f":SOURce{ch}:VOLTage:LEVel:IMMediate:OFFSet?" ) )
                    answer = pg.siFormat( raw_answer, suffix = 'V', precision = 3, allowUnicode = False)
                    return answer

        elif self.test_flag == 'test':
            ch = channel
            assert(ch == '1' or ch == '2'), "Incorrect waveform generator channel; channel: ['1', '2']"
            if len(offset) == 1:
                temp = offset[0].split(" ")
                val = float(temp[0])
                scaling = temp[1]
                if scaling in self.scale_dict:
                    coef = self.scale_dict[scaling]
                else:
                    assert(1 == 2), "Incorrect argument; offset: float + [' V', ' mV']; channel: ['1', '2']"
            elif len(offset) == 0:
                answer = self.test_wave_gen_offset
                return answer
            else:
                assert(1 == 2), "Incorrect argument; offset: float + [' V', ' mV']; channel: ['1', '2']"

    def wave_gen_impedance(self, *impedance, channel = '1'):
        if self.test_flag != 'test':
            ch = channel
            if ch == '1' or ch == '2':
                if len(impedance) == 1:
                    cpl = str(impedance[0])

                    if ch == '1':
                        self.wg_coupling_1 = cpl
                    elif ch == '2':
                        self.wg_coupling_2 = cpl

                    if cpl == '1 M':
                        cpl = 'OMEG'
                        self.device_write( f":OUTPut{ch}:IMPedance {cpl}" )
                    elif cpl == '50':
                        cpl = 'FIFTy'
                        self.device_write( f":OUTPut{ch}:IMPedance {cpl}" )

                elif len(impedance) == 0:
                    answer = str(self.device_query( f":OUTPut{ch}:IMPedance?" ) )[:-1]
                    return answer

        elif self.test_flag == 'test':
            ch = channel
            assert(ch == '1' or ch == '2'), "Incorrect waveform generator channel; channel: ['1', '2']"
            if len(impedance) == 1:
                cpl = str(impedance[0])

                if ch == '1':
                    self.wg_coupling_1 = cpl
                elif ch == '2':
                    self.wg_coupling_2 = cpl

                assert(cpl == '1 M' or cpl == '50'), "Invalid impedance argument; impedance: ['1 M', '50']; channel: ['1', '2']"
            elif len(impedance) == 0:
                answer = self.test_wave_gen_impedance
                return answer
            else:
                assert(1 == 2), "Invalid impedance argument; impedance: ['1 M', '50']; channel: ['1', '2']"

    def wave_gen_start(self, channel = '1'):
        if self.test_flag != 'test':
            ch = channel
            if ch == '1' or ch == '2':
                self.device_write( f":SOURce{ch}:OUTPut{ch}:STATe 1" )
        elif self.test_flag == 'test':
            ch = channel
            assert(ch == '1' or ch == '2'), "Incorrect waveform generator channel; channel: ['1', '2']"

    def wave_gen_stop(self, channel = '1'):
        if self.test_flag != 'test':
            ch = channel
            if ch == '1' or ch == '2':
                self.device_write( f":SOURce{ch}:OUTPut{ch}:STATe 0" )

        elif self.test_flag == 'test':
            ch = channel
            assert(ch == '1' or ch == '2'), "Incorrect waveform generator channel; channel: ['1', '2']"

    def wave_gen_phase(self, *phase, channel = '1'):
        ch = channel
        if self.test_flag != 'test':
            if len(phase) == 1:
                ph = int(phase[0])
                if self.test_flag != 'test':
                    self.device_write( f":SOURce{ch}:PHASe:ADJust {ph}" )
                elif self.test_flag == 'test':
                    assert( ph >= 0 and ph <= 360 ), f"Incorrect phase. Available phase range is from 0 deg to 360 deg"
            elif len(phase) == 0:
                if self.test_flag != 'test':
                    raw_answer = float( self.device_query(f":SOURce{ch}:PHASe:ADJust?") )
                elif self.test_flag == 'test':
                    raw_answer = self.test_phase
                
                return f"{raw_answer} deg"

        elif self.test_flag == 'test':
            assert( ch == '1' or ch == '2' ), "Incorrect waveform generator channel; phase: int; channel: ['1', '2']"

    def wave_gen_command(self, command):
        if self.test_flag != 'test':
            self.device_write(command)
        elif self.test_flag == 'test':
            pass

    def wave_gen_query(self, command):
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
