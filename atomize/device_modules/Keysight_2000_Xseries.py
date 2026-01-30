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

class Keysight_2000_Xseries:
    #### Basic interaction functions
    def __init__(self):

        #### Inizialization
        # setting path to *.ini file
        self.path_current_directory = lconf.load_config_device()
        self.path_config_file = os.path.join(self.path_current_directory, 'Keysight_2012a_config.ini')

        # configuration data
        self.config = cutil.read_conf_util(self.path_config_file)
        self.specific_parameters = cutil.read_specific_parameters(self.path_config_file)

        # auxilary dictionaries
        self.points_list = [100, 250, 500, 1000, 2000, 5000, 10000, 20000, 50000, 100000, 200000, 500000]
        self.points_list_average = [100, 250, 500, 1000, 2000, 4000, 8000]
        self.points_list_average_real = [99, 247, 479, 959, 1919, 3839, 7679]
        # Number of point is different for Average mode and three other modes

        self.channel_dict = {'CH1': 'CHAN1', 'CH2': 'CHAN2', 'CH3': 'CHAN3', 'CH4': 'CHAN4',}
        self.trigger_channel_dict = {'CH1': 'CHAN1', 'CH2': 'CHAN2', 'CH3': 'CHAN3', 'CH4': 'CHAN4', 'Ext': 'EXTernal', 'Line': 'LINE', 'WGen': 'WGEN',}

        #should be checked, since it is incorrect for 2000 Series
        self.timebase_dict = {'s': 1, 'ms': 1000, 'us': 1000000, 'ns': 1000000000,};
        self.scale_dict = {'V': 1, 'mV': 1000,};
        self.frequency_dict = {'MHz': 1000000, 'kHz': 1000, 'Hz': 1, 'mHz': 0.001,};
        self.wavefunction_dic = {'Sin': 'SIN', 'Sq': 'SQU', 'Ramp': 'RAMP', 'Pulse': 'PULS', 'DC': 'DC', 'Noise': 'NOIS'};
        self.ac_type_dic = {'Normal': "NORM", 'Average': "AVER", 'Hres': "HRES",'Peak': "PEAK"}

        self.modulation_wavefunction_dict = {'Sin': 'SIN', 'Sq': 'SQU', 'Ramp': 'RAMP'}
        self.status_dict = {'Off': 0, 'On': 1}
        self.modulation_type_dict = {'AM': 'AM', 'FM': 'FM', 'Freq-Shift': 'FSK'}
        self.rate_freq_list = ['MHz', 'kHz', 'Hz', 'mHz']

        self.func_type = 'SIN'
        self.mod_type = 'AM'

        # Limits and Ranges:
        self.analog_channels = int(self.specific_parameters['analog_channels'])
        self.numave_min = 2
        self.numave_max = 65536
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
        self.wave_gen = str(self.specific_parameters['wave_gen'])

        self.max_freq_dict = {'SIN': 20e6, 'SQU': 10e6, 'RAMP': 100e3, 'PULS': 10e6, 'DC': 0, 'NOIS': 0}

        self.f_min = pg.siFormat( self.wave_gen_freq_min, suffix = 'Hz', precision = 3, allowUnicode = False)
        self.f_max = pg.siFormat( self.wave_gen_freq_max, suffix = 'Hz', precision = 3, allowUnicode = False)


        #integration window
        self.win_left = 0
        self.win_right = 1

        self.wg_coupling_1 = '1 M'

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
                    self.device.read_termination = self.config['read_termination']  # for WORD (a kind of binary) format
                    try:
                        self.device_write('*CLS')
                        self.status_flag = 1

                        if self.wave_gen == 'True':
                            self.wg_coupling_1 = self.device_query(":WGEN:OUTPut:LOAD?")
                            
                            if self.wg_coupling_1 == 'ONEM':
                                self.wg_coupling_1 = '1 M'
                            elif self.wg_coupling_1 == 'FIFTy':
                                self.wg_coupling_1 = '50'

                            self.func_type = str(self.device_query(':WGEN:FUNCtion?'))
                            self.mod_type = str(self.device_query(':WGEN:MODulation:TYPE?'))
                            self.freq = float(self.device_query(":WGEN:FREQuency?"))

                        else:
                            pass


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
            self.test_trigger_level = ' 1 mV'
            self.test_wave_gen_frequency = '500 Hz'
            self.test_wave_gen_width = '350 us'
            self.test_wave_gen_function = 'Sin'
            self.test_wave_gen_amplitude = '500 mV'
            self.test_wave_gen_offset = '0 mV'
            self.test_wave_gen_impedance = '1 M'
            self.test_area = 0.001

            self.test_mod_function = 'Sin'
            self.test_mod_status = 'Off'
            self.test_mod_type = 'AM'
            self.test_mod_depth = '100 %'
            self.test_mod_hop = '1 kHz'
            self.test_mod_rate = '100 Hz'
            self.test_mod_span_frequency = '50 Hz'

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
            answer = self.device.query_binary_values(command, 'H', is_big_endian=True, container=np.array)
            # H for 3034T; H for 2012A
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
                self.oscilloscope_run()

                if test_acq_type == 'Average':
                    poi = min(self.points_list_average, key = lambda x: abs(x - temp))
                    poi_real = min(self.points_list_average_real, key = lambda x: abs(x - temp))   
                    if int(poi) != temp:
                        general.message(f"Desired record length cannot be set, the nearest available value of {poi_real} is used")
                    self.device_write(":WAVeform:POINts " + str(poi))
                else:
                    poi = min(self.points_list, key = lambda x: abs(x - temp))
                    if int(poi) != temp:
                        general.message(f"Desired record length cannot be set, the nearest available value of {poi} is used")
                    self.device_write(":WAVeform:POINts " + str(poi))

                #answer = int(self.device_query(':WAVeform:POINts?'))
                #tb_0 = pg.siEval(self.oscilloscope_timebase())
                #i = 0
                #st_time = time.time()
                #while answer != poi_real:
                #    mod_tb = pg.siEval(self.oscilloscope_timebase()) + 0.001 * tb_0
                #    self.oscilloscope_timebase( pg.siFormat( mod_tb, suffix = 's', precision = 5, allowUnicode = False))
                #    answer = int(self.device_query(':WAVeform:POINts?'))
                #    general.message(answer)
                #    if i == 0:
                #        general.message('Incorrect number of points. Timebase will be changed')
                #        i = 1

                #    if (time.time() - st_time) > 60:
                #        general.message(f'Correct timebase was not found. The number of point is {answer}')
                #        self.oscilloscope_timebase( pg.siFormat( tb_0, suffix = 's', precision = 5, allowUnicode = False))
                #        break

            elif len(points) == 0:
                answer = int(self.device_query(':WAVeform:POINts?'))
                return answer

        elif self.test_flag == 'test':
            if len(points) == 1:
                temp = int(points[0])
                poi = min(self.points_list, key = lambda x: abs(x - temp))
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
                    self.device_write(":ACQuire:TYPE " + str(flag))
                    general.wait('150 ms')
            elif len(ac_type) == 0:
                raw_answer = str(self.device_query(":ACQuire:TYPE?"))
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
                numave = int(number_of_averages[0])
                if numave >= self.numave_min and numave <= self.numave_max:
                    ac = self.oscilloscope_acquisition_type()
                    if ac == "Average":
                        self.device_write(":ACQuire:COUNt " + str(numave))
                    elif ac == 'Normal':
                        general.message("Your are in NORM mode")
                    elif ac == 'Hres':
                        general.message("Your are in HRES mode")
                    elif ac == 'Peak':
                        general.message("Your are in PEAK mode")
            elif len(number_of_averages) == 0:
                answer = int(self.device_query(":ACQuire:COUNt?"))
                return answer

        elif self.test_flag == 'test':
            if len(number_of_averages) == 1:
                numave = int(number_of_averages[0])
                assert(numave >= self.numave_min and numave <= self.numave_max), \
                    f'Incorrect number of averages. The available range is form {self.numave_min} to {self.numave_max}'
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
                        self.device_write(f":TIMebase:RANGe {tb/coef}")

            elif len(timebase) == 0:
                raw_answer = float(self.device_query(":TIMebase:RANGe?"))
                answer = pg.siFormat( raw_answer, suffix = 's', precision = 4, allowUnicode = False)
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
            raw_answer = float(self.device_query(":TIMebase:RANGe?")) / points
            answer = pg.siFormat( raw_answer, suffix = 's', precision = 9, allowUnicode = False)
            return answer
        elif self.test_flag == 'test':
            raw_answer = pg.siEval(self.test_timebase) / self.test_record_length
            answer = pg.siFormat( raw_answer, suffix = 's', precision = 9, allowUnicode = False)
            return answer

    def oscilloscope_start_acquisition(self):
        if self.test_flag != 'test':
            #start_time = datetime.now()
            self.device_write(':WAVeform:FORMat WORD')
            self.device_write('*ESR?;:DIGitize;*OPC?') # return 1, if everything is ok; #;*OPC?
            # the whole sequence is the following 1-binary format; 2-clearing; 3-digitizing; 4-checking of the completness
            #end_time=datetime.now()
            #general.message('Acquisition completed')
            #print("Duration of Acquisition: {}".format(end_time - start_time))
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

    def oscilloscope_get_curve(self, channel, integral = False):
        if self.test_flag != 'test':
            ch = str(channel)
            if ch in self.channel_dict:
                flag = self.channel_dict[ch]
                if flag[0] == 'C' and int(flag[-1]) <= self.analog_channels:
                    self.device_write(':WAVeform:SOURce ' + str(flag))
                    array_y = self.device_read_binary(':WAVeform:DATA?')
                    preamble = self.device_query_ascii(":WAVeform:PREamble?")

                    x_inc = preamble[4]
                    x_orig = preamble[5]
                    y_inc = preamble[7]
                    y_orig = preamble[8]
                    y_ref = preamble[9]
                    #print(y_inc)
                    #print(y_orig)
                    #print(y_ref)
                    array_y = (array_y - y_ref)*y_inc + y_orig
                    #array_x = list(map(lambda x: resolution*(x+1) + 1000000*x_orig, list(range(points))))
                    #final_data = list(zip(array_x,array_y))
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
                array_y = np.arange(self.test_record_length)
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
                    area = float(self.device_query(':MEASure:AREa? DISPlay , ' + str(flag)))
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
                    assert(1 == 2), f"Incorrect sensitivity argument; sensitivity: 'int + [' mV', ' V']; channel: {list(self.channel_dict.keys())}"
            elif len(channel) == 1:
                ch = str(channel[0])
                assert(ch in self.channel_dict), f'Invalid channel is given; channel: {list(self.channel_dict.keys())}'
                flag = self.channel_dict[ch]
                if flag[0] == 'C' and int(flag[-1]) > self.analog_channels:
                    assert(1 == 2), f'Invalid channel is given; channel: {list(self.channel_dict.keys())}'
                else:
                    answer = self.test_sensitivity
                    return answer
            else:
                assert(1 == 2), f"Incorrect sensitivity argument; sensitivity: 'int + [' mV', ' V']; channel: {list(self.channel_dict.keys())}"

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
                    self.device_write(":TIMebase:DELay "+ str(offset/coef))
            elif len(h_offset) == 0:
                raw_answer = float(self.device_query(":TIMebase:DELay?"))
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
        if self.test_flag != 'test':
            if len(coupling) == 2:
                ch = str(coupling[0])
                cpl = str(coupling[1])
                if ch in self.channel_dict:
                    flag = self.channel_dict[ch]
                    if flag[0] == 'C' and int(flag[-1]) <= self.analog_channels:
                        self.device_write(':' + str(flag) + ':COUPling ' + str(cpl))

            elif len(coupling) == 1:
                ch = str(coupling[0])
                if ch in self.channel_dict:
                    flag = self.channel_dict[ch]
                    if flag[0] == 'C' and int(flag[-1]) <= self.analog_channels:
                        answer = self.device_query(":" + str(flag) + ":COUPling?")
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
                    cpl = 'ONEMeg'
                if ch in self.channel_dict:
                    flag = self.channel_dict[ch]
                    if flag[0] == 'C' and int(flag[-1]) <= self.analog_channels:
                        self.device_write(':' + str(flag) + ':IMPedance ' + str(cpl))

            elif len(impedance) == 1:
                ch = str(impedance[0])
                if ch in self.channel_dict:
                    flag = self.channel_dict[ch]
                    if flag[0] == 'C' and int(flag[-1]) <= self.analog_channels:
                        raw_answer = self.device_query(":" + str(flag) + ":IMPedance?")
                        if raw_answer == 'ONEM':
                            return '1 M'

        elif self.test_flag == 'test':
            if len(impedance) == 2:
                ch = str(impedance[0])
                cpl = str(impedance[1])
                assert(ch in self.channel_dict), f'Invalid channel is given; channel: {list(self.channel_dict.keys())}'
                flag = self.channel_dict[ch]
                if flag[0] == 'C' and int(flag[-1]) > self.analog_channels:
                    assert(1 == 2), f'Invalid channel is given; channel: {list(self.channel_dict.keys())}'
                assert(cpl == '1 M'), "Invalid impedance argument; impedance: ['1 M']"
            elif len(impedance) == 1:
                ch = str(impedance[0])
                assert(ch in self.channel_dict), f'Invalid channel is given; channel: {list(self.channel_dict.keys())}'
                flag = self.channel_dict[ch]
                if flag[0] == 'C' and int(flag[-1]) > self.analog_channels:
                    assert(1 == 2), f'Invalid channel is given; channel: {list(self.channel_dict.keys())}'
                answer = self.test_impedance
                return answer
            else:
                assert(1 == 2), "Invalid impedance argument; impedance: ['1 M']"

    def oscilloscope_trigger_mode(self, *mode):
        if self.test_flag != 'test':
            if len(mode) == 1:
                md = str(mode[0])
                if md == 'Auto':
                    self.device_write(":TRIGger:SWEep " + 'AUTO')
                elif md == 'Normal':
                    self.device_write(":TRIGger:SWEep " + 'NORMal')

            elif len(mode) == 0:
                answer = self.device_query(":TRIGger:SWEep?")
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
                answer = self.device_query(":TRIGger:EDGE:SOURce?")
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
                ch = str(level[0])
                lvl = pg.siEval(level[1])
                if ch in self.channel_dict:
                    flag = self.channel_dict[ch]
                    if flag[0] == 'C' and int(flag[-1]) <= self.analog_channels:
                        self.device_write(':TRIGger:LEVel:LOW ' + str(lvl) + ', ' + str(flag))

            elif len(level) == 1:
                ch = str(level[0])
                if ch in self.channel_dict:
                    flag = self.channel_dict[ch]
                    if flag[0] == 'C' and int(flag[-1]) <= self.analog_channels:
                        raw_answer = float(self.device_query(':TRIGger:LEVel:LOW? ' + str(flag)))
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
            #path_file = os.path.join(path_to_main, '../../atomize/control_center/digitizer.param')
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

    def wave_gen_frequency(self, *frequency):
        f_max = pg.siFormat( self.max_freq_dict[self.func_type], suffix = 'Hz', precision = 3, allowUnicode = False)
        if self.test_flag != 'test':
            if len(frequency) == 1:
                temp = frequency[0].split(" ")
                freq = float(temp[0])
                scaling = temp[1]
                if scaling in self.frequency_dict:
                    coef = self.frequency_dict[scaling]
                    if freq*float(coef) >= self.wave_gen_freq_min and freq*float(coef) <= self.max_freq_dict[self.func_type]:
                        self.device_write(":WGEN:FREQuency " + str(freq*coef))
                        self.freq = freq * coef
                    else:
                        general.message(f"Incorrect frequency range for {cutil.search_keys_dictionary(self.wavefunction_dic, self.func_type)}. The available range is from {self.f_min} to {f_max}")

            elif len(frequency) == 0:
                raw_answer = float(self.device_query(":WGEN:FREQuency?"))
                self.freq = raw_answer
                answer = pg.siFormat( raw_answer, suffix = 'Hz', precision = 6, allowUnicode = False)
                return answer

        elif self.test_flag == 'test':
            if len(frequency) == 1:
                temp = frequency[0].split(" ")
                freq = float(temp[0])
                scaling = temp[1]
                if scaling in self.frequency_dict:
                    coef = self.frequency_dict[scaling]

                    assert(freq*float(coef) >= self.wave_gen_freq_min and \
                        freq*float(coef) <= self.max_freq_dict[self.func_type]), f"Incorrect frequency range for {cutil.search_keys_dictionary(self.wavefunction_dic, self.func_type)}. The available range is from {self.f_min} to {f_max}"
                    self.freq = freq * coef
                else:
                    assert(1 == 2), "Incorrect argument; frequency: float + [' MHz', ' kHz', ' Hz', ' mHz']"
            elif len(frequency) == 0:
                answer = self.test_wave_gen_frequency
                return answer
            else:
                assert(1 == 2), "Incorrect argument; frequency: float + [' MHz', ' kHz', ' Hz', ' mHz']"

    def wave_gen_pulse_width(self, *width):
        if self.test_flag != 'test':
            answer = self.device_query(":WGEN:FUNCtion?")
            if answer == 'PULS':
                if len(width) == 1:
                    temp = width[0].split(" ")
                    wid = float(temp[0])
                    scaling = temp[1];
                    if scaling in self.timebase_dict:
                        coef = self.timebase_dict[scaling]
                        self.device_write(":WGEN:FUNCtion:PULSe:WIDTh " + str(wid/coef))
                elif len(width) == 0:
                    raw_answer = float(self.device_query(":WGEN:FUNCtion:PULSe:WIDTh?"))
                    answer = pg.siFormat( raw_answer, suffix = 's', precision = 6, allowUnicode = False)
                    return answer
            else:
                general.message(f"You are not using the pulsed function of the waveform generator {self.__class__.__name__}")

        elif self.test_flag == 'test':
            if len(width) == 1:
                temp = width[0].split(" ")
                wid = float(temp[0])
                scaling = temp[1]
                if scaling in self.timebase_dict:
                    coef = self.timebase_dict[scaling]
                else:
                    assert(1 == 2), "Incorrect argument; width: float + [' s', ' ms', ' us', ' ns']"
            elif len(width) == 0:
                answer = self.test_wave_gen_width
                return answer
            else:
                assert(1 == 2), "Incorrect argument; width: float + [' s', ' ms', ' us', ' ns']"

    def wave_gen_function(self, *function):
        if self.test_flag != 'test':
            if  len(function) == 1:
                func = str(function[0])
                if func in self.wavefunction_dic:
                    flag = self.wavefunction_dic[func]
                    f_max = pg.siFormat( self.max_freq_dict[flag], suffix = 'Hz', precision = 3, allowUnicode = False)

                    if self.freq >= self.wave_gen_freq_min and self.freq <= self.max_freq_dict[self.func_type]:
                        self.device_write(":WGEN:FUNCtion " + str(flag))
                        self.func_type = flag
                    else:
                        general.message(f"Incorrect frequency range for {cutil.search_keys_dictionary(self.wavefunction_dic, flag)}. The available range is from {self.f_min} to {f_max}")

            elif len(function) == 0:
                raw_answer = str(self.device_query(':WGEN:FUNCtion?'))
                answer = cutil.search_keys_dictionary(self.wavefunction_dic, raw_answer)
                self.func_type = raw_answer
                return answer

        elif self.test_flag == 'test':
            if  len(function) == 1:
                func = str(function[0])
                if func in self.wavefunction_dic:
                    flag = self.wavefunction_dic[func]
                    f_max = pg.siFormat( self.max_freq_dict[flag], suffix = 'Hz', precision = 3, allowUnicode = False)
                else:
                    assert(1 == 2), f"Invalid waveform generator function. Available options are {list(self.wavefunction_dic.keys())}"

                assert( self.freq >= self.wave_gen_freq_min and self.freq <= self.max_freq_dict[flag]), f"Incorrect frequency range for {cutil.search_keys_dictionary(self.wavefunction_dic, flag)}. The available range is from {self.f_min} to {f_max}"

                self.func_type = flag

            elif len(function) == 0:
                answer = self.test_wave_gen_function
                return answer
            else:
                assert(1 == 2), f"Invalid argument; function: {list(self.wavefunction_dic.keys())}"

    def wave_gen_amplitude(self, *amplitude):
        if self.test_flag != 'test':
            if len(amplitude) == 1:
                temp = amplitude[0]
                val = pg.siEval(temp)
                ampl_50_max = pg.siFormat( self.ampl_50_max, suffix = 'V', precision = 3, allowUnicode = False)
                ampl_50_min = pg.siFormat( self.ampl_50_min, suffix = 'V', precision = 3, allowUnicode = False)
                ampl_hz_max = pg.siFormat( self.ampl_hz_max, suffix = 'V', precision = 3, allowUnicode = False)
                ampl_hz_min = pg.siFormat( self.ampl_hz_min, suffix = 'V', precision = 3, allowUnicode = False)

                if self.wg_coupling_1 == '1 M':
                    if (val >= self.ampl_hz_min and val <= self.ampl_hz_max):
                        self.device_write(f":WGEN:VOLTage {val}")
                    else:    
                        f"Invalid amplitude range. Available ranges are (i) '1 M' {ampl_hz_min} - {ampl_hz_max}; (ii) '50' {ampl_50_min} - {ampl_50_max}"
                elif self.wg_coupling_1 == '50':
                    if (val >= self.ampl_50_min and val <= self.ampl_50_max):
                        self.device_write(f":WGEN:VOLTage {val}")
                    else:    
                        f"Invalid amplitude range. Available ranges are (i) '1 M' {ampl_hz_min} - {ampl_hz_max}; (ii) '50' {ampl_50_min} - {ampl_50_max}"

            elif len(amplitude) == 0:
                raw_answer = float(self.device_query( f":WGEN:VOLTage?" ) )
                answer = pg.siFormat( raw_answer, suffix = 'V', precision = 3, allowUnicode = False)
                return answer

        elif self.test_flag == 'test':
            if len(amplitude) == 1:
                temp = amplitude[0]
                val = pg.siEval(temp)
                ampl_50_max = pg.siFormat( self.ampl_50_max, suffix = 'V', precision = 3, allowUnicode = False)
                ampl_50_min = pg.siFormat( self.ampl_50_min, suffix = 'V', precision = 3, allowUnicode = False)
                ampl_hz_max = pg.siFormat( self.ampl_hz_max, suffix = 'V', precision = 3, allowUnicode = False)
                ampl_hz_min = pg.siFormat( self.ampl_hz_min, suffix = 'V', precision = 3, allowUnicode = False)
                if self.wg_coupling_1 == '1 M':
                    assert(val >= self.ampl_hz_min and val <= self.ampl_hz_max), f"Invalid amplitude range. Available ranges are (i) '1 M' {ampl_hz_min} - {ampl_hz_max}; (ii) '50' {ampl_50_min} - {ampl_50_max}"
                elif self.wg_coupling_1 == '50':
                    assert(val >= self.ampl_50_min and val <= self.ampl_50_max), f"Invalid amplitude range. Available ranges are (i) '1 M' {ampl_hz_min} - {ampl_hz_max}; (ii) '50' {ampl_50_min} - {ampl_50_max}"

            elif len(amplitude) == 0:
                answer = self.test_wave_gen_amplitude
                return answer
            else:
                assert(1 == 2), f"Invalid argument; amplitude: float + [' V', ' mV']"

    def wave_gen_offset(self, *offset):
        if self.test_flag != 'test':
            if len(offset) == 1:
                temp = offset[0].split(" ")
                val = float(temp[0])
                scaling = temp[1]
                if scaling in self.scale_dict:
                    coef = self.scale_dict[scaling]
                    self.device_write(":WGEN:VOLTage:OFFSet " + str(val/coef))

            elif len(offset) == 0:
                raw_answer = float(self.device_query( ":WGEN:VOLTage:OFFSet?" ) )
                answer = pg.siFormat( raw_answer, suffix = 'V', precision = 3, allowUnicode = False)
                return answer

        elif self.test_flag == 'test':
            if len(offset) == 1:
                temp = offset[0].split(" ")
                val = float(temp[0])
                scaling = temp[1]
                if scaling in self.scale_dict:
                    coef = self.scale_dict[scaling]
                else:
                    assert(1 == 2), "Incorrect argument; offset: float + [' V', ' mV']"
            elif len(offset) == 0:
                answer = self.test_wave_gen_offset
                return answer
            else:
                assert(1 == 2), "Incorrect argument; offset: float + [' V', ' mV']"

    def wave_gen_impedance(self, *impedance):
        if self.test_flag != 'test':
            if len(impedance) == 1:
                cpl = str(impedance[0])
                self.wg_coupling_1 = cpl

                if cpl == '1 M':
                    cpl = 'ONEMeg'
                    self.device_write(":WGEN:OUTPut:LOAD " + str(cpl))
                elif cpl == '50':
                    cpl = 'FIFTy'
                    self.device_write(":WGEN:OUTPut:LOAD " + str(cpl))

            elif len(impedance) == 0:
                answer = str(self.device_query(":WGEN:OUTPut:LOAD?"))
                return answer

        elif self.test_flag == 'test':
            if len(impedance) == 1:
                cpl = str(impedance[0])
                assert(cpl == '1 M' or cpl == '50'), "Invalid impedance argument; impedance: ['1 M', '50']; channel: ['1', '2']"
                self.wg_coupling_1 = cpl

            elif len(impedance) == 0:
                answer = self.test_wave_gen_impedance
                return answer
            else:
                assert(1 == 2), "Invalid impedance argument; impedance: ['1 M', '50']; channel: ['1', '2']"

    def wave_gen_start(self):
        if self.test_flag != 'test':
            self.device_write(":WGEN:OUTPut 1")
        elif self.test_flag == 'test':
            pass

    def wave_gen_stop(self):
        if self.test_flag != 'test':
            self.device_write(":WGEN:OUTPut 0")
        elif self.test_flag == 'test':
            pass

    def wave_gen_modulation_type(self, *type):
        """
        [AM', 'FM', 'Freq-Shift']
        """
        if len(type) == 1:
            func = str(type[0])
            flag = self.modulation_type_dict[func]
            if self.test_flag != 'test':
                self.device_write(f":WGEN:MODulation:TYPE {flag}")
                self.mod_type = flag
            elif self.test_flag == 'test':
                assert(func in self.modulation_type_dict), f"Invalid modulation function. Available options are {list(self.modulation_type_dict.keys())}"

        elif len(type) == 0:
            if self.test_flag != 'test':            
                raw_answer = str(self.device_query(':WGEN:MODulation:TYPE?'))
                self.mod_type = raw_answer
                answer = cutil.search_keys_dictionary(self.modulation_type_dict, raw_answer)
                return answer
            elif self.test_flag == 'test':
                answer = self.test_mod_type
                return answer

        else:
            if self.test_flag == 'test':
                assert( 1 == 2 ), f"Incorrect argument; type: {list(self.modulation_type_dict.keys())}"

    def wave_gen_modulation_function(self, *function):
        """
        ['Sin', 'Sq', 'Ramp']
        """
        if len(function) == 1:
            func = str(function[0])
            flag = self.modulation_wavefunction_dict[func]
            if self.test_flag != 'test':
                self.device_write(f":WGEN:MODulation:FUNCtion {flag}")
            elif self.test_flag == 'test':
                assert(func in self.modulation_wavefunction_dict), f"Invalid modulation function. Available options are {list(self.modulation_wavefunction_dict.keys())}"

        elif len(function) == 0:
            if self.test_flag != 'test':            
                raw_answer = str(self.device_query(':WGEN:MODulation:FUNCtion?'))
                answer = cutil.search_keys_dictionary(self.modulation_wavefunction_dict, raw_answer)
                return answer
            elif self.test_flag == 'test':
                answer = self.test_mod_function
                return answer
        else:
            if self.test_flag == 'test':
                assert( 1 == 2 ), f"Incorrect argument; function: {list(self.modulation_wavefunction_dict.keys())}"

    def wave_gen_modulation_depth(self, *depth):
        """
        sets the AM modulation depth to i percent ( 0 to 100%).
        """
        if len(depth) == 1:
            val = int(depth[0])
            if self.test_flag != 'test':
                self.device_write(f":WGEN:MODulation:AM:DEPTh {val}")
            elif self.test_flag == 'test':
                assert( (val >= 0) and (val <= 100) ), f"Invalid modulation depth range. The available range is from 0 % to 100 %"

        elif len(depth) == 0:
            if self.test_flag != 'test':            
                raw_answer = int(self.device_query(':WGEN:MODulation:AM:DEPTh?'))
                return f"{raw_answer} %"
            elif self.test_flag == 'test':
                answer = self.test_mod_depth
                return answer

        else:
            if self.test_flag == 'test':
                assert( 1 == 2 ), f"Incorrect argument; depth: int [0 - 100]"

    def wave_gen_modulation_status(self, *status):
        """
        except pulse, DC, and noise.
        """
        if len(status) == 1:
            func = str(status[0])
            flag = self.status_dict[func]
            if self.test_flag != 'test':
                if (self.func_type != 'PULS') or (self.func_type != 'DC') or (self.func_type != 'NOIS'):
                    self.device_write(f":WGEN:MODulation:STATe {flag}")
                else:
                    general.message(f"Modulation is not available for ['Pulse', 'DC', 'Noise']. The current function is {cutil.search_keys_dictionary(self.wavefunction_dic, self.func_type)}")

            elif self.test_flag == 'test':
                assert(func in self.status_dict), f"Invalid modulation regime. Available options are {list(self.status_dict.keys())}"

        elif len(status) == 0:
            if self.test_flag != 'test':            
                raw_answer = int(self.device_query(':WGEN:MODulation:STATe?'))
                answer = cutil.search_keys_dictionary(self.status_dict, raw_answer)
                return answer
            elif self.test_flag == 'test':
                answer = self.test_mod_status
                return answer

        else:
            if self.test_flag == 'test':
                assert( 1 == 2 ), f"Incorrect argument; status: {list(self.status_dict.keys())}"

    def wave_gen_modulation_rate(self, *rate):
        """
        The :WGEN:MODulation:FM:FREQuency command specifies the frequency of the modulating signal
        The :WGEN:MODulation:AM:FREQuency command specifies the frequency of the modulating signal
        self.mod_type: ['AM', 'FM']
        """
        if len(rate) == 1:
            freq = pg.siEval( rate[0] )

            if self.test_flag != 'test':
                if self.mod_type == 'AM':
                    self.device_write( f":WGEN:MODulation:AM:FREQuency {freq}" )
                elif self.mod_type == 'FM':
                    self.device_write( f":WGEN:MODulation:FM:FREQuency {freq}" )
                else:
                    general.message(f"Frequency of the modulating signal can be set only for ['AM', 'FM'] modulation type. The current type is {cutil.search_keys_dictionary(self.modulation_type_dict, self.mod_type)}")

            elif self.test_flag == 'test':
                temp = rate[0].split(" ")
                scaling = temp[1]
                assert(scaling in self.rate_freq_list), f"Incorrect SI suffix. Available options are {self.rate_freq_list}"
                # there is no limit indication in the programming guide 
                #assert( freq >= 0.001 and freq <= 10e3 ), f"Incorrect frequency rate range. The available range is from 1 mHz to 10 kHz"

        elif len(rate) == 0:
            if self.test_flag != 'test':
                if self.mod_type == 'AM':
                    raw_answer = self.device_query( f":WGEN:MODulation:AM:FREQuency?" )
                elif self.mod_type == 'FM':
                    raw_answer = self.device_query( f":WGEN:MODulation:FM:FREQuency?" )
                else:
                    general.message(f"Frequency of the modulating signal can be get only for ['AM', 'FM'] modulation type. The current type is {cutil.search_keys_dictionary(self.modulation_type_dict, self.mod_type)}")

                answer = pg.siFormat( raw_answer, suffix = 'Hz', precision = 7, allowUnicode = False)
                return answer
            elif self.test_flag == 'test':
                return self.test_mod_rate

        else:
            if self.test_flag == 'test':
                assert(1 == 2), "Incorrect argument; rate: float + [' MHz', ' kHz', ' Hz', ' mHz']"

    def wave_gen_modulation_frequency_span(self, *span):
        """
        :WGEN:MODulation:FM:DEViation <frequency>
        The frequency deviation cannot be greater than the original carrier signal
        frequency.
        Also, the sum of the original carrier signal frequency and the frequency deviation
        must be less than or equal to the maximum frequency for the selected waveform
        generator function plus 100 kHz
        """
        f_max = pg.siFormat( self.max_freq_dict[self.func_type], suffix = 'Hz', precision = 3, allowUnicode = False)
        if len(span) == 1:
            freq = pg.siEval( span[0] ) / 2

            if self.test_flag != 'test':
                if (self.freq - freq) >= self.wave_gen_freq_min and (self.freq + freq) <= self.max_freq_dict[self.func_type]:
                    self.device_write(":WGEN:MODulation:FM:DEViation " + str(freq))
                else:
                    general.message(f"Incorrect frequency range for {cutil.search_keys_dictionary(self.wavefunction_dic, self.func_type)}. The available range is from {self.f_min} to {f_max}")

            elif self.test_flag == 'test':
                temp = span[0].split(" ")
                scaling = temp[1]
                assert(scaling in self.freq_list), f"Incorrect SI suffix. Available options are {self.freq_list}"
                #assert( (self.freq - freq) >= self.wave_gen_freq_min and (self.freq + freq) <= self.max_freq_dict[self.func_type] ), f"Incorrect frequency range for {cutil.search_keys_dictionary(self.wavefunction_dic, self.func_type)}. The available range is from {self.f_min} to {f_max}"

        elif len(span) == 0:
            if self.test_flag != 'test':
                raw_answer = float(self.device_query(":WGEN:MODulation:FM:DEViation?"))
                answer = pg.siFormat( raw_answer, suffix = 'Hz', precision = 8, allowUnicode = False)
                return answer
            elif self.test_flag == 'test':
                return self.test_mod_span_frequency

        else:
            if self.test_flag == 'test':
                assert(1 == 2), "Incorrect argument; span: float + [' MHz', ' kHz', ' Hz', ' mHz', ' uHz']"

    def wave_gen_modulation_hop_frequency(self, *frequency):
        """
        The :WGEN:MODulation:FSKey:FREQuency command specifies the "hop frequency".
        The output frequency "shifts" between the original carrier frequency and this "hop frequency".
        """
        if len(frequency) == 1:
            freq = pg.siEval( frequency[0] )

            if self.test_flag != 'test':
                self.device_write( f":WGEN:MODulation:FSKey:FREQuency {freq}" )

            elif self.test_flag == 'test':
                temp = frequency[0].split(" ")
                scaling = temp[1]
                assert(scaling in self.rate_freq_list), f"Incorrect SI suffix. Available options are {self.rate_freq_list}"
                assert( self.mod_type == 'FSK' ), f"This function is available only for 'Freq-Shift' modulation type. Current type is {cutil.search_keys_dictionary(self.modulation_type_dict, self.mod_type)}"

        elif len(rate) == 0:
            if self.test_flag != 'test':
                raw_answer = self.device_query( f":WGEN:MODulation:FSKey:FREQuency?" )
                answer = pg.siFormat( raw_answer, suffix = 'Hz', precision = 7, allowUnicode = False)
                return answer
            elif self.test_flag == 'test':
                return self.test_mod_hop

        else:
            if self.test_flag == 'test':
                assert(1 == 2), "Incorrect argument; rate: float + [' MHz', ' kHz', ' Hz', ' mHz']"

    def wave_gen_modulation_hop_rate(self, *rate):
        """
        The :WGEN:MODulation:FSKey:RATE command specifies the rate at which the
        output frequency "shifts".
        The FSK rate specifies a digital square wave modulating signal.
        """
        if len(rate) == 1:
            rt = pg.siEval( rate[0] )

            if self.test_flag != 'test':
                self.device_write( f":WGEN:MODulation:FSKey:RATE {rt}" )

            elif self.test_flag == 'test':
                temp = rate[0].split(" ")
                scaling = temp[1]
                assert(scaling in self.rate_freq_list), f"Incorrect SI suffix. Available options are {self.rate_freq_list}"
                assert( self.mod_type == 'FSK' ), f"This function is available only for 'Freq-Shift' modulation type. Current type is {cutil.search_keys_dictionary(self.modulation_type_dict, self.mod_type)}"

        elif len(rate) == 0:
            if self.test_flag != 'test':
                raw_answer = self.device_query( f":WGEN:MODulation:FSKey:RATE?" )
                answer = pg.siFormat( raw_answer, suffix = 'Hz', precision = 7, allowUnicode = False)
                return answer
            elif self.test_flag == 'test':
                return self.test_mod_rate

        else:
            if self.test_flag == 'test':
                assert(1 == 2), "Incorrect argument; rate: float + [' MHz', ' kHz', ' Hz', ' mHz']"


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
