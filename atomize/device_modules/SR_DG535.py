#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import gc
import sys
import pyvisa
from typing import (
    Any,
    Optional, )
import pyqtgraph as pg
import atomize.main.local_config as lconf
import atomize.device_modules.config.config_utils as cutil
import atomize.general_modules.general_functions as general

class SR_DG535:
    #### Basic interaction functions
    def __init__(self):

        #### Inizialization
        # setting path to *.ini file
        self.path_current_directory = lconf.load_config_device()
        self.path_config_file = os.path.join(self.path_current_directory, 'SR_DG535_config.ini')

        # configuration data
        self.config = cutil.read_conf_util(self.path_config_file)
        self.specific_parameters = cutil.read_specific_parameters(self.path_config_file)

        # auxilary dictionaries
        self.delay_channel_dict = {'T0': 1, 'A': 2, 'B': 3, 'C': 5, 'D': 6,}
        self.input_output_channel_dict = {'Trigger': 0, 'T0': 1, 'A': 2, 'B': 3, 'AB': 4, 'C': 5, 'D': 6, 'CD': 7,}
        self.output_channel_dict = {'T0': 1, 'A': 2, 'B': 3, 'AB': 4, 'C': 5, 'D': 6, 'CD': 7,}
        self.time_dict = {'s': 1, 'ms': 1000, 'us': 1000000, 'ns': 1000000000, 'ps': 1000000000000,}
        self.impedance_dict = {'50': 0, '1 M': 1,}
        self.mode_dict = {'TTL': 0, 'NIM': 1, 'ECL': 2, 'Variable': 3,}
        self.ampl_dict = {'V': 1, 'mV': 1000,}
        self.polarity_dict = {'Inverted': 0, 'Normal': 1,}
        self.trigger_source_dict = {'Internal': 0, 'External': 1, 'Single': 2, 'Burst': 3,}
        self.trigger_slope_dict = {'Falling': 0, 'Rising': 1}
        self.rate_freq_list = ['MHz', 'kHz', 'Hz', 'mHz']
        self.level_list = ['V', 'mV']


        # Ranges and limits
        self.delay_max = 999.99
        self.delay_min = 0.
        self.var_ampl_min = -3.
        self.var_ampl_max = 4.
        self.trigger_rate_min = 1e-3
        self.trigger_rate_max = 1e6
        self.burst_count_min = 2
        self.burst_count_max = 32766
        self.burst_period_min = 4
        self.burst_period_max = 32766
        self.burst_count = 2
        self.burst_period = 4

        # Test run parameters
        # These values are returned by the modules in the test run 
        if len(sys.argv) > 1:
            self.test_flag = sys.argv[1]
        else:
            self.test_flag = 'None'

        if self.test_flag != 'test':
            if self.config['interface'] == 'gpib':
                try:
                    address = self.config['gpib_address']

                    try:
                        f_let = address[0]
                    except TypeError:
                        f_let = 0

                    if f_let == 'G':
                        rm = pyvisa.ResourceManager()
                        self.device = rm.open_resource(self.config['gpib_address'], timeout = self.config['timeout'])
                        self.gpib_be = 1
                    else:
                        import Gpib
                        self.device = Gpib.Gpib(self.config['board_address'], self.config['gpib_address'], timeout = self.config['timeout'])

                    self.status_flag = 1

                    try:
                        self.tr_source = int(self.device_query('TM'))
                        self.burst_count = int(self.device_query('BC'))
                        self.burst_period = int(self.device_query('BP'))

                    except BrokenPipeError:
                        general.message(f"No connection {self.__class__.__name__}")
                        self.status_flag = 0
                        sys.exit()
                except BrokenPipeError:
                    general.message(f"No connection {self.__class__.__name__}")
                    self.status_flag = 0
                    sys.exit()

            else:
                general.message(f"Incorrect interface setting {self.__class__.__name__}")
                self.status_flag = 0
                sys.exit()

        elif self.test_flag == 'test':
            self.test_delay = 'B + 1.0 us'
            self.test_impedance = '1 M'
            self.test_mode = 'TTL'
            self.test_amplitude_offset = 'Amplitude: 2. V; Offset: 0. V'
            self.test_polarity = 'Normal'
            self.trigger_source = 'Internal'
            self.test_trigger_rate = '1 kHz'
            self.test_trigger_level = '2 V'
            self.test_trigger_slope = 'Rising'

    def close_connection(self):
        if self.test_flag != 'test':
            self.status_flag = 0
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
            if self.config['interface'] == 'gpib':
                if self.gpib_be == 0:
                    self.device.write(command)
                    general.wait('50 ms')
                    answer = self.device.read().decode()
                else:
                    answer = self.device.query(command, 0.05)
        else:
            general.message(f"No connection {self.__class__.__name__}")
            self.status_flag = 0
            sys.exit()

    #### device specific functions
    def delay_generator_name(self):
        if self.test_flag != 'test':
            answer = self.config['name']
            return answer
        elif self.test_flag == 'test':
            answer = self.config['name']
            return answer

    def delay_generator_delay(self, *delay):
        """
        attempt to reference A to B
        and B to A so that neither is referenced to T0. 
        """
        if self.test_flag != 'test':
            if len(delay) == 3:
                ch_1 = str(delay[0])
                ch_2 = str(delay[1])
                temp = delay[2].split(" ")
                delay = float(temp[0])
                scaling = temp[1]
                if (ch_1 in self.delay_channel_dict) and (ch_2 in self.delay_channel_dict):
                    flag_1 = self.delay_channel_dict[ch_1]
                    flag_2 = self.delay_channel_dict[ch_2]
                    if scaling in self.time_dict:
                        coef = self.time_dict[scaling]
                        if delay/coef >= self.delay_min and delay/coef <= self.delay_max:
                            self.device_write('DT ' + str(flag_1) + ',' + str(flag_2) + ',' + str(delay/coef))

                            ans = int( self.device_query('ES 4') )
                            if ans == 1:
                                general.message('Delay linkage error. At least one channel should be referenced to "T0"')

            elif len(delay) == 1:
                ch_1 = str(delay[0])
                if (ch_1 in self.delay_channel_dict):
                    flag_1 = self.delay_channel_dict[ch_1]
                    raw_answer = str(self.device_query('DT ' + str(flag_1))).split(',')
                    ch_answer = cutil.search_keys_dictionary(self.delay_channel_dict, int(raw_answer[0]))
                    delay_answer = float(raw_answer[1])
                    del_answer = pg.siFormat( delay_answer, suffix = 's', precision = 5, allowUnicode = False)
                    answer = str(ch_answer) + ' + ' + str(del_answer)
                    return answer

        elif self.test_flag == 'test':
            if len(delay) == 3:
                ch_1 = str(delay[0])
                ch_2 = str(delay[1])
                temp = delay[2].split(" ")
                delay = float(temp[0])
                scaling = temp[1]
                assert(ch_1 in self.delay_channel_dict), f"Incorrect channel 1; channel: {list(self.delay_channel_dict.keys())}"
                assert(ch_2 in self.delay_channel_dict), f"Incorrect channel 2; channel: {list(self.delay_channel_dict.keys())}"
                assert(scaling in self.time_dict), f"Invalid argument; channel 1, 2: {list(self.delay_channel_dict.keys())}; delay: int + [' s', ' ms', ' us', ' ns', ' ps']"
                coef = self.time_dict[scaling]
                min_d = pg.siFormat( self.delay_min, suffix = 's', precision = 3, allowUnicode = False)
                max_d = pg.siFormat( self.delay_max, suffix = 's', precision = 3, allowUnicode = False)
                assert(delay/coef >= self.delay_min and delay/coef <= self.delay_max), \
                    f"Incorrect delay. The available range is from {min_d} to {max_d}"

            elif len(delay) == 1:
                ch_1 = str(delay[0])
                assert(ch_1 in self.delay_channel_dict), f"Incorrect channel 1; channel: {list(self.delay_channel_dict.keys())}"
                answer = self.test_delay
                return answer
            else:
                assert(1 == 2), f"Invalid argument; channel 1, 2: {list(self.delay_channel_dict.keys())}; delay: int + [' s', ' ms', ' us', ' ns', ' ps']"

    def delay_generator_impedance(self, *impedance):
        if self.test_flag != 'test':
            if len(impedance) == 2:
                ch = str(impedance[0])
                imp = str(impedance[1])
                if ch in self.input_output_channel_dict:
                    flag_1 = self.input_output_channel_dict[ch]
                    if imp in self.impedance_dict:
                        flag_2 = self.impedance_dict[imp]
                        self.device_write('TZ ' + str(flag_1) + ',' + str(flag_2))
            
            elif len(impedance) == 1:
                ch = str(impedance[0])
                if ch in self.input_output_channel_dict:
                    flag = self.input_output_channel_dict[ch]
                    raw_answer = int(self.device_query('TZ ' + str(flag)))
                    answer = cutil.search_keys_dictionary(self.impedance_dict, raw_answer)
                    return answer

        elif self.test_flag == 'test':
            if len(impedance) == 2:
                ch = str(impedance[0])
                imp = str(impedance[1])
                assert(ch in self.input_output_channel_dict), f"Incorrect channel; channel: {list(self.input_output_channel_dict.keys())}"
                assert(imp in self.impedance_dict), f'Invalid impedance; impedance: {list(self.impedance_dict.keys())}'

            elif len(impedance) == 1:
                ch = str(impedance[0])
                assert(ch in self.input_output_channel_dict), f"Incorrect channel; channel: {list(self.input_output_channel_dict.keys())}"
                answer = self.test_impedance
                return answer
            else:
                assert(1 == 2), f"Invalid argument; channel: {list(self.input_output_channel_dict.keys())}; impedance: {list(self.impedance_dict.keys())}"

    def delay_generator_output_mode(self, *mode):
        if self.test_flag != 'test':
            if len(mode) == 2:
                ch = str(mode[0])
                md = str(mode[1])
                if ch in self.output_channel_dict:
                    flag_1 = self.output_channel_dict[ch]
                    if md in self.mode_dict:
                        flag_2 = self.mode_dict[md]
                        self.device_write('OM ' + str(flag_1) + ',' + str(flag_2))
            
            elif len(mode) == 1:
                ch = str(mode[0])
                if ch in self.output_channel_dict:
                    flag = self.output_channel_dict[ch]
                    raw_answer = int(self.device_query('OM ' + str(flag)))
                    answer = cutil.search_keys_dictionary(self.mode_dict, raw_answer)
                    return answer

        elif self.test_flag == 'test':
            if len(mode) == 2:
                ch = str(mode[0])
                md = str(mode[1])
                assert(ch in self.output_channel_dict), f"Incorrect channel; channel: {list(self.output_channel_dict.keys())}"
                assert(md in self.mode_dict), f"Invalid argument; channel: {list(self.output_channel_dict.keys())}; mode: {list(self.mode_dict.keys())}"

            elif len(mode) == 1:
                ch = str(mode[0])
                assert(ch in self.output_channel_dict), f"Incorrect channel; channel: {list(self.output_channel_dict.keys())}"
                answer = self.test_mode
                return answer
            else:
                assert(1 == 2), f"Invalid argument; channel: {list(self.output_channel_dict.keys())}; mode: {list(self.mode_dict.keys())}"

    def delay_generator_amplitude_offset(self, *amplitude_offset):
        """
        The maximum step size is limited
        to ±4 Volts: the minimum step size is ±0.1VDC.
        The specified step size must not cause the output
        level (including the programmed offset) to
        exceed +4V or -3V.
        """
        if self.test_flag != 'test':
            if len(amplutide) == 3:
                ch = str(amplutide[0])
                temp_1 = amplutide[1].split(" ")
                temp_2 = amplutide[2].split(" ")
                ampl = float(temp_1[0])
                scaling_1 = temp_1[1]
                ofst = float(temp_2[0])
                scaling_2 = temp_2[1]
                if ch in self.output_channel_dict:
                    flag_1 = self.output_channel_dict[ch]
                    if (scaling_1 in self.ampl_dict) and (scaling_2 in self.ampl_dict):
                        coef_1 = self.ampl_dict[scaling_1]
                        coef_2 = self.ampl_dict[scaling_2]
                        if int(self.device_query('OM ' + str(flag_1))) == 3:
                            general.wait('30 ms')
                            if (ampl/coef_1 + ofst/coef_2) >= self.var_ampl_min and (ampl/coef_1 + ofst/coef_2) <= self.var_ampl_max and (ampl/coef_1) >= self.var_ampl_min and (ampl/coef_1) <= self.var_ampl_max and (ofst/coef_2) >= self.var_ampl_min (ofst/coef_2) <= self.var_ampl_max:
                                self.device_write('OA ' + str(flag_1) + ',' + str(round( ampl/coef_1, 1 )))
                                self.device_write('OO ' + str(flag_1) + ',' + str(round( ofst/coef_2, 1 )))
                        else:
                            general.message(f"Delay generator {self.__class__.__name__} is not in 'Variable' output mode")

            elif len(amplutide) == 1:
                ch = str(amplutide[0])
                if ch in self.output_channel_dict:
                    flag = self.output_channel_dict[ch]
                    answer_1 = float(self.device_query('OA ' + str(flag)))
                    answer_2 = float(self.device_query('OO ' + str(flag)))
                    answer = 'Amplitude: ' + str(answer_1) + ' V; ' + 'Offset: ' + str(answer_2) + ' V'
                    return answer

        elif self.test_flag == 'test':
            if len(amplutide) == 3:
                ch = str(amplutide[0])
                temp_1 = amplutide[1].split(" ")
                temp_2 = amplutide[2].split(" ")
                ampl = float(temp_1[0])
                scaling_1 = temp_1[1]
                ofst = float(temp_2[0])
                scaling_2 = temp_2[1]
                assert(ch in self.output_channel_dict), f"Incorrect channel; channel: {list(self.output_channel_dict.keys())}"
                assert(scaling_1 in self.ampl_dict),\
                    f"Invalid argument; channel: {list(self.output_channel_dict.keys())}; amplutide: float + [' mV', ' V']; offset: float + [' mV', ' V']"
                assert(scaling_2 in self.ampl_dict),\
                    f"Invalid argument; channel: {list(self.output_channel_dict.keys())}; amplutide: float + [' mV', ' V']; offset: float + [' mV', ' V']"
                coef_1 = self.ampl_dict[scaling_1]
                coef_2 = self.ampl_dict[scaling_2]
                min_a = pg.siFormat( self.var_ampl_min, suffix = 'V', precision = 3, allowUnicode = False)
                max_a = pg.siFormat( self.var_ampl_max, suffix = 'V', precision = 3, allowUnicode = False)
                assert(ampl/coef_1 >= self.var_ampl_min and ampl/coef_1 <= self.var_ampl_max), f"Incorrect amplitude. The available rande is from {min_a} to {max_a}"
                assert(ofst/coef_2 >= self.var_ampl_min and ofst/coef_2 <= self.var_ampl_max), f"Incorrect offset. The available rande is from {min_a} to {max_a}"
                assert(ampl/coef_1 + ofst/coef_2 >= self.var_ampl_min and ampl/coef_1 + ofst/coef_2 <= self.var_ampl_max), \
                    f"Incorrect range. The available rande is from {min_a} to {max_a}"

            elif len(amplutide) == 1:
                ch = str(amplutide[0])
                assert(ch in self.output_channel_dict), f"Incorrect channel; channel: {list(self.output_channel_dict.keys())}"
                answer = self.test_amplitude_offset
                return answer
            else:
                assert(1 == 2),\
                    f"Invalid argument; channel: {list(self.output_channel_dict.keys())}; amplutide: float + [' mV', ' V']; offset: float + [' mV', ' V']"

    def delay_generator_output_polarity(self, *polarity):
        if self.test_flag != 'test':
            if len(polarity) == 2:
                ch = str(polarity[0])
                plr = str(polarity[1])
                if ch in self.output_channel_dict:
                    flag_1 = self.output_channel_dict[ch]
                    if plr in self.polarity_dict:
                        flag_2 = self.polarity_dict[plr]
                        if int(self.device_query('OM ' + str(flag_1))) != 3:
                            general.wait('30 ms')
                            self.device_write('OP ' + str(flag_1) + ',' + str(flag_2))
                        else:
                            general.message(f"Delay generator {self.__class__.__name__} is in 'Variable' output mode")
            
            elif len(polarity) == 1:
                ch = str(polarity[0])
                if ch in self.output_channel_dict:
                    flag = self.output_channel_dict[ch]
                    raw_answer = int(self.device_query('OP ' + str(flag)))
                    answer = cutil.search_keys_dictionary(self.polarity_dict, raw_answer)
                    return answer

        elif self.test_flag == 'test':
            if len(polarity) == 2:
                ch = str(polarity[0])
                plr = str(polarity[1])
                assert(ch in self.output_channel_dict), f"Incorrect channel; channel: {list(self.output_channel_dict.keys())}"
                assert(plr in self.polarity_dict), f"Incorrect polarity; polarity: {list(self.polarity_dict.keys())}"

            elif len(polarity) == 1:
                ch = str(polarity[0])
                assert(ch in self.output_channel_dict), f"Incorrect channel; channel: {list(self.output_channel_dict.keys())}"
                answer = self.test_polarity
                return answer
            else:
                assert(1 == 2), f"Invalid argument; channel: {list(self.output_channel_dict.keys())}; polarity: {list(self.polarity_dict.keys())}"

    def delay_generator_trigger_source(self, *source):
        """
        TM {i}
        Set Trigger Mode to Int, Ext, SS or Bur (i=0,1,2,3).
        This command selects between Internal, External, Single-Shot, or Burst trigger modes
        """
        if len(source) == 1:
            func = str(source[0])
            flag = self.trigger_source_dict[func]
            self.tr_source = flag
            if self.test_flag != 'test':
                self.device_write(f"TM {flag}")
            elif self.test_flag == 'test':
                assert(func in self.trigger_source_dict), f"Invalid trigger source. Available options are {list(self.trigger_source_dict.keys())}"

        elif len(source) == 0:
            if self.test_flag != 'test':            
                raw_answer = int(self.device_query('TM'))
                self.tr_source = raw_answer
                answer = cutil.search_keys_dictionary(self.trigger_source_dict, raw_answer)
                return answer
            elif self.test_flag == 'test':
                answer = self.trigger_source
                return answer
        else:
            if self.test_flag == 'test':
                assert( 1 == 2 ), f"Incorrect argument; source: {list(self.trigger_source_dict.keys())}"

    def delay_generator_trigger_rate(self, *rate):
        """
        TR i{,f}
        Set Internal Trigger Rate (i=0) or Burst Trigger Rate
        (i=1) to f Hz. The frequency may be any value
        between 0.001 Hz and 1.000MHz.         
        """
        rate_min = pg.siFormat( self.trigger_rate_min, suffix = 'Hz', precision = 3, allowUnicode = False)
        rate_max = pg.siFormat( self.trigger_rate_max, suffix = 'Hz', precision = 3, allowUnicode = False)
        if len(rate) == 1:
            freq = pg.siEval( rate[0] )

            if freq < 10:
                freq_r = pg.siEval( pg.siFormat( raw_answer, suffix = 'Hz', precision = 5, allowUnicode = False) )
            else:
                freq_r = pg.siEval( pg.siFormat( raw_answer, suffix = 'Hz', precision = 4, allowUnicode = False) )

            if self.test_flag != 'test':
                if self.tr_source == 0:
                    # 3 Wrong mode for the command 
                    self.device_write( f"TM 2; TR 0,{freq_r}" )
                    general.wait('2000 ms')
                    self.device_write( f"TM {self.tr_source}" )
                elif self.tr_source == 3:
                    self.device_write( f"TM 2; TR 1,{freq_r}" )
                    general.wait('2000 ms')
                    self.device_write( f"TM {self.tr_source}" )
                else:
                    general.message(f"Trigger rate can be set only for 'Internal' or 'Burst' mode. The current mode is {cutil.search_keys_dictionary(self.trigger_source_dict, self.tr_source)}")

            elif self.test_flag == 'test':
                temp = rate[0].split(" ")
                scaling = temp[1]
                assert(scaling in self.rate_freq_list), f"Incorrect SI suffix. Available options are {self.rate_freq_list}"
                assert( freq_r >= self.trigger_rate_min and freq_r <= self.trigger_rate_max ), f"Incorrect trigger rate. The available range is from {rate_min} to {rate_max}"

        elif len(rate) == 0:
            if self.test_flag != 'test':
                raw_answer = float(self.device_query("TR"))
                answer = pg.siFormat( raw_answer, suffix = 'Hz', precision = 5, allowUnicode = False)
                return answer
            elif self.test_flag == 'test':
                return self.test_trigger_rate

        else:
            if self.test_flag == 'test':
                assert(1 == 2), "Incorrect argument; rate: float + [' MHz', ' kHz', ' Hz', ' mHz']"

    def delay_generator_trigger(self):
        """
        Single-Shot trigger if Trigger Mode = 2
        """
        if self.test_flag != 'test':
            if self.tr_source == 2:
                self.device_write( "SS" )
            else:
                general.message( "The trigger source should be set to 'Single" )

    def delay_generator_trigger_level(self, *level):
        """
        TL {v}
        Set External Trigger Level to v Volts. This
        command sets the threshold voltage for external
        triggers. 
        """
        if len(level) == 1:
            lvl = pg.siEval( level[0] )
            lvl_r = pg.siEval( pg.siFormat( raw_answer, suffix = 'V', precision = 3, allowUnicode = False) )
            if self.test_flag != 'test':
                self.device_write( f"TL {lvl_r}" )
            elif self.test_flag == 'test':
                temp = level[0].split(" ")
                scaling = temp[1]
                assert(scaling in self.level_list), f"Incorrect SI suffix. Available options are {self.level_list}"

        elif len(level) == 0:
            if self.test_flag != 'test':
                raw_answer = float(self.device_query("TL"))
                answer = pg.siFormat( raw_answer, suffix = 'V', precision = 3, allowUnicode = False)
                return answer
            elif self.test_flag == 'test':
                return self.test_trigger_level

        else:
            if self.test_flag == 'test':
                assert(1 == 2), "Incorrect argument; level: float + [' V', ' mV']"

    def delay_generator_trigger_slope(self, *slope):
        """
        TS {i}
        Trigger Slope set to falling (i=0) or Rising Edge
        (i=1)
        """
        if len(slope) == 1:
            func = str(slope[0])
            flag = self.trigger_slope_dict[func]
            if self.test_flag != 'test':
                self.device_write(f"TS {flag}")
            elif self.test_flag == 'test':
                assert(func in self.trigger_slope_dict), f"Invalid trigger slope. Available options are {list(self.trigger_slope_dict.keys())}"

        elif len(slope) == 0:
            if self.test_flag != 'test':            
                raw_answer = int(self.device_query('TS'))
                answer = cutil.search_keys_dictionary(self.trigger_slope_dict, raw_answer)
                return answer
            elif self.test_flag == 'test':
                answer = self.test_trigger_slope
                return answer
        else:
            if self.test_flag == 'test':
                assert( 1 == 2 ), f"Incorrect argument; slope: {list(self.trigger_slope_dict.keys())}"

    def delay_generator_trigger_impedance(self, *impedance):
        """
        TZ 0{,j}
        Set the input impedance of the external trigger
        input to 50Ω (j=0) or high impedance (j=1). 
        """
        if len(impedance) == 1:
            func = str(impedance[0])
            flag = self.self.impedance_dict[func]
            if self.test_flag != 'test':
                self.device_write(f"TZ {flag}")
            elif self.test_flag == 'test':
                assert(func in self.self.impedance_dict), f"Invalid trigger impedance. Available options are {list(self.impedance_dict.keys())}"

        elif len(impedance) == 0:
            if self.test_flag != 'test':            
                raw_answer = int(self.device_query('TZ'))
                answer = cutil.search_keys_dictionary(self.impedance_dict, raw_answer)
                return answer
            elif self.test_flag == 'test':
                answer = self.test_impedance
                return answer
        else:
            if self.test_flag == 'test':
                assert( 1 == 2 ), f"Incorrect impedance; slope: {list(self.impedance_dict.keys())}"

    def delay_generator_burst_count(self, count: Optional[int] = None):
        """
        BC {i}
        Burst Count of i (2 to 32766) pulses per burst.
        This command is used to specify the number of
        pulses, which will be in each burst of pulses
        when in the burst mode.
        """
        if isinstance(count, int):
            if self.test_flag != 'test':
                if self.tr_source == 3:
                    self.device_write( f"BC {count}" )
                    self.burst_count = count
                else:
                    general.message(f"Burst count can be set only for 'Burst' mode. The current mode is {cutil.search_keys_dictionary(self.trigger_source_dict, self.tr_source)}")

            elif self.test_flag == 'test':
                assert( count >= self.burst_count_min and count <= self.burst_count_max ), f"Incorrect burst count. The available range is from {self.burst_count_min} to {self.burst_count_max}"

        elif count is None:
            if self.test_flag != 'test':
                raw_answer = int(self.device_query("BC"))
                self.burst_count = raw_answer
                return raw_answer
            elif self.test_flag == 'test':
                return self.burst_count

        else:
            if self.test_flag == 'test':
                assert(1 == 2), "Incorrect argument; count: int [2 - 32766]"

    def delay_generator_burst_period(self, *period):
        """
        BP {i}
        Burst Period of i (4 to 32766) triggers per burst.
        This command specifies the number of triggers
        between the start of each burst of pulses when in
        the burst mode. The burst period must always be
        at least one larger than the Burst Count. 
        """
        if len(period) == 1:
            pr = int( period[0] )
            if self.test_flag != 'test':
                if self.tr_source == 3:
                    if pr > self.burst_count:
                        self.device_write( f"BP {pr}" )
                        self.burst_period = pr
                    else:
                        general.message(f"Burst period should always be at least one larger than the burst count. The current burst count is {self.burst_count}")
                else:
                    general.message(f"Burst period can be set only for 'Burst' mode. The current mode is {cutil.search_keys_dictionary(self.trigger_source_dict, self.tr_source)}")

            elif self.test_flag == 'test':
                assert( pr >= self.burst_period_min and pr <= self.burst_period_max ), f"Incorrect burst period. The available range is from {self.burst_period_min} to {self.burst_period_max}"

        elif len(period) == 0:
            if self.test_flag != 'test':
                raw_answer = int(self.device_query("BP"))
                self.burst_period = raw_answer
                return raw_answer
            elif self.test_flag == 'test':
                return self.burst_period

        else:
            if self.test_flag == 'test':
                assert(1 == 2), "Incorrect argument; period: int [4 - 32766]"

    def delay_generator_command(self, command):
        if self.test_flag != 'test':
            self.device_write(command)
        elif self.test_flag == 'test':
            pass

    def delay_generator_query(self, command):
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
