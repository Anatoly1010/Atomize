#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import math
import time
import ctypes
import fileinput
from copy import deepcopy
from operator import iconcat
from functools import reduce
from itertools import groupby, chain
from math import remainder, ceil
import numpy as np
import atomize.main.local_config as lconf
import atomize.device_modules.config.config_utils as cutil
import atomize.general_modules.general_functions as general

class Insys_FPGA:
    def __init__(self):
        #### Inizialization
        # setting path to *.ini file
        self.path_current_directory = lconf.load_config_device()
        self.path_config_file_pulser = os.path.join(self.path_current_directory, 'PB_Insys_pulser_config.ini')

        path_to_main_status = os.path.abspath( os.getcwd() )
        self.path_status_file = os.path.join(path_to_main_status, 'status')

        # configuration data
        #config = cutil.read_conf_util(self.path_config_file)
        self.specific_parameters_pulser = cutil.read_specific_parameters(self.path_config_file_pulser)

        # Test run parameters
        if len(sys.argv) > 1:
            self.test_flag = sys.argv[1]
        else:
            self.test_flag = 'None'

        ####################GIM################################################################################
        # Channel assignments
        self.ch0 = self.specific_parameters_pulser['ch0'] # DETECTION
        self.ch1 = self.specific_parameters_pulser['ch1'] # TRIGGER_AWG 
        self.ch2 = self.specific_parameters_pulser['ch2'] # MW 
        self.ch3 = self.specific_parameters_pulser['ch3'] # AMP_ON 
        self.ch4 = self.specific_parameters_pulser['ch4'] # LNA_PROTECT 
        self.ch5 = self.specific_parameters_pulser['ch5'] # -X 
        self.ch6 = self.specific_parameters_pulser['ch6'] # +Y
        self.ch7 = self.specific_parameters_pulser['ch7'] # AWG
        self.ch8 = self.specific_parameters_pulser['ch8'] # LASER
        self.ch9 = self.specific_parameters_pulser['ch9'] # SYNT2

        # AWG pulse will be substitued by a shifted RECT_AWG pulse and AMP_ON pulse
        # TRIGGER_AWG is used to trigger AWG card

        self.timebase_dict = {'s': 1000000000, 'ms': 1000000, 'us': 1000, 'ns': 1, }
        # -Y for Mikran bridge is simutaneously turned on -X; +Y
        # that is why there is no -Y channel instead we add both -X and +Y pulses
        self.channel_dict_pulser = {self.ch0: 0, self.ch1: 1, self.ch2: 2, self.ch3: 3, self.ch4: 4, self.ch5: 5, \
                        self.ch6: 6, self.ch7: 7, self.ch8: 8, self.ch9: 9, 'CH10': 10, 'CH11': 11,\
                        'CH12': 12, 'CH13': 13, 'CH14': 14, 'CH15': 15, 'CH16': 16, 'CH17': 17,\
                        'CH18': 18, 'CH19': 19, 'CH20': 20, 'CH21': 21, }

        # Limits and Ranges (depends on the exact model):
        self.clock_pulser = float(self.specific_parameters_pulser['clock'])
        self.timebase_pulser = float(float(self.specific_parameters_pulser['timebase'])) # in ns/clock; convertion of clock to ns
        self.repetition_rate_pulser = self.specific_parameters_pulser['default_rep_rate']
        self.auto_defense_pulser = self.specific_parameters_pulser['auto_defense']
        self.max_pulse_length_pulser = float(float(self.specific_parameters_pulser['max_pulse_length'])) # in ns
        self.min_pulse_length_pulser = float(float(self.specific_parameters_pulser['min_pulse_length'])) # in ns

        self.ext_trigger = int(self.specific_parameters_pulser['ext_trigger'])
        if self.ext_trigger == 0:
            self.change_two_ini_files('exam_adc.ini', "StartBaseSource = 7", "StartBaseSource = 0")
            self.change_two_ini_files('exam_edac.ini', "StartBaseSource=7", "StartBaseSource=0")
        elif self.ext_trigger == 1:
            self.change_two_ini_files('exam_adc.ini', "StartBaseSource = 0", "StartBaseSource = 7")
            self.change_two_ini_files('exam_edac.ini', "StartBaseSource=0", "StartBaseSource=7")

        self.ext_clock = int(self.specific_parameters_pulser['ext_clock'])
        self.clock_value = round(float(self.specific_parameters_pulser['clock_value']), 1)

        if self.ext_clock == 0:
            self.change_two_ini_files('exam_adc.ini', "ClockSource = 0x3", "ClockSource = 0x2")
            self.change_two_ini_files('exam_edac.ini', "ClockSource = 0x3", "ClockSource = 0x2")
            self.change_three_ini_files('exam_adc.ini', "BaseClockValue = ", '200.0')
            self.change_three_ini_files('exam_edac.ini', "BaseClockValue = ", '200.0')

        elif self.ext_clock == 1:
            self.change_two_ini_files('exam_adc.ini', "ClockSource = 0x2", "ClockSource = 0x3")
            self.change_two_ini_files('exam_edac.ini', "ClockSource = 0x2", "ClockSource = 0x3")
            self.change_three_ini_files('exam_adc.ini', "BaseClockValue = ", str(self.clock_value) )
            self.change_three_ini_files('exam_edac.ini', "BaseClockValue = ", str(self.clock_value) )

        # minimal distance between two pulses of MW
        # pulse blaster restriction
        self.minimal_distance_pulser = int(float(self.specific_parameters_pulser['minimal_distance'])/self.timebase_pulser) # in clock

        # a constant that use to overcome short instruction for our diagonal amp_on and mw pulses
        # see also add_amp_on_pulses() function; looking for pulses with +-overlap_amp_lna_mw overlap
        self.overlap_amp_lna_mw_pulser = 0 # in clock ### it was 5; 06.03.2023

        # after all manupulations with diagonal amp_on pulses there is a variant
        # when we use several mw pulses with app. 40 ns distance and with the phase different from
        # +x. In this case two phase pulses start to be at the distance less than current minimal distance
        # in 40 ns. That is why a different minimal distance (10 ns) is added for phase pulses
        # see also preparing_to_bit_pulse() function
        self.minimal_distance_phase_pulser = 0 # in clock ### it was 6; 06.10.2021

        # minimal distance for joining AMP_ON and LNA_PROTECT pulses
        # decided to keep it as 12 ns, while for MW pulses the limit is 40 ns
        self.minimal_distance_amp_lna_pulser = 0 # in clock

        # Delays and restrictions
        self.constant_shift_pulser = int(640 / self.timebase_pulser) # in clock; shift of all sequence for not getting negative start times
        self.switch_delay_pulser = int(float(self.specific_parameters_pulser['switch_amp_delay'])/self.timebase_pulser) # in clock; delay for AMP_ON turning on; switch_delay BEFORE MW pulse
        self.switch_protect_delay_pulser = int(float(self.specific_parameters_pulser['switch_protect_delay'])/self.timebase_pulser) # in clock; delay for LNA_PROTECT turning on; switch_protect_delay_pulser BEFORE MW pulse
        self.amp_delay_pulser = int(float(self.specific_parameters_pulser['amp_delay'])/self.timebase_pulser) # in clock; delay for AMP_ON turning off; amp_delay AFTER MW pulse
        self.protect_delay_pulser = int(float(self.specific_parameters_pulser['protect_delay'])/self.timebase_pulser) # in clock; delay for LNA_PROTECT turning off; protect_delay AFTER MW pulse
        self.switch_phase_delay_pulser = int(float(self.specific_parameters_pulser['switch_phase_delay'])) # in ns; delay for FAST_PHASE turning on; switch_phase_delay BEFORE MW pulse
        self.phase_delay_pulser = int(float(self.specific_parameters_pulser['phase_delay'])) # in ns; delay for FAST_PHASE turning off; phase_delay AFTER MW pulse
        
        # currently RECT_AWG is coincide with AMP_ON pulse;
        self.rect_awg_switch_delay_pulser = int(float(self.specific_parameters_pulser['rect_awg_switch_delay'])) # in ns; delay for RECT_AWG turning on; rect_awg_switch_delay BEFORE MW pulse
        self.rect_awg_delay_pulser = int(float(self.specific_parameters_pulser['rect_awg_delay'])) # in ns; delay for RECT_AWG turning off; rect_awg_delay AFTER MW pulse
        self.protect_awg_delay_pulser = int(float(self.specific_parameters_pulser['protect_awg_delay'])/self.timebase_pulser) # in clock; delay for LNA_PROTECT turning off; because of shift a 
        # combination of rect_awg_delay and protect_awg_delay is used

        self.internal_pause_pulser = '0 us'

        # interval that shift the first pulse in the sequence
        # start times of other pulses can be calculated from this time.
        # I. E. first pulse: 
        # pb.pulser_pulse(name ='P0', channel = 'MW', start = '100 ns', length = '20 ns')
        # second: pb.pulser_pulse(name ='P1', channel = 'MW', start = '330 ns', length = '30 ns', delta_start = '10 ns')
        # we will have first pulse at 50 ns (add_shft*2)
        # second at (330 - 100) + 50 = 280 ns
        # if there is no AMP_ON/LNA_PROTECT pulses
        self.add_shift_pulser = int(0) # in ns; *self.timebase

        ####################GIM################################################################################
        if self.test_flag != 'test':
            #pb_core_clock(self.clock)
            self.detection_phase_list = []
            self.pulse_array_pulser = []
            self.phase_array_length_pulser = []
            self.pulse_name_array_pulser = []
            self.pulse_array_init_pulser = []
            self.rep_rate_pulser = (self.repetition_rate_pulser, )
            self.shift_count_pulser = 0
            self.rep_rate_count_pulser = 0
            self.increment_count_pulser = 0
            self.reset_count_pulser = 0
            self.current_phase_index_pulser = 0
            self.awg_pulses_pulser = 0
            self.phase_pulses_pulser = 0
            self.instr_from_file_pulser = 0
            self.iterator_of_updates_pulser = 0
            # Default synt for AWG channel
            self.synt_number = 2
            self.synt2_shift = 15
            self.synt2_ext = 4

        elif self.test_flag == 'test':
            self.test_rep_rate_pulser = '200 Hz'
            
            self.detection_phase_list = []
            self.pulse_array_pulser = []
            self.phase_array_length_pulser = []
            self.pulse_name_array_pulser = []
            self.pulse_array_init_pulser = []
            self.rep_rate_pulser = (self.repetition_rate_pulser, )
            self.shift_count_pulser = 0
            self.rep_rate_count_pulser = 0
            self.increment_count_pulser = 0
            self.reset_count_pulser = 0
            self.current_phase_index_pulser = 0
            self.awg_pulses_pulser = 0
            self.phase_pulses_pulser = 0
            self.instr_from_file_pulser = 0
            # Default synt for AWG channel
            self.synt_number = 2
            self.synt2_shift = 15
            self.synt2_ext = 4

        #### Inizialization
        # setting path to *.ini file
        ####################DAC################################################################################
        self.path_current_directory = os.path.dirname(__file__)
        self.path_config_file_awg = os.path.join(self.path_current_directory, 'config', 'PB_Insys_DAC_config.ini')

        # configuration data
        #config = cutil.read_conf_util(self.path_config_file_awg)
        self.specific_parameters_awg = cutil.read_specific_parameters(self.path_config_file_awg)

        # Channel assignments
        self.channel_dict_awg = {'CH0': 0, 'CH1': 1, }
        self.function_dict_awg = {'SINE': 0, 'GAUSS': 1, 'SINC': 2, 'BLANK': 3, 'WURST': 4, 'SECH/TANH': 5, 'TEST': 6, 'TEST2': 7, 'TEST3': 8, }

        # Limits and Ranges (depends on the exact model):
        #clock = float(self.specific_parameters_awg['clock'])
        self.max_pulse_length_awg = int(float(self.specific_parameters_awg['max_pulse_length'])) # in ns
        self.min_pulse_length_awg = int(float(self.specific_parameters_awg['min_pulse_length'])) # in ns
        self.max_freq_awg = int(float(self.specific_parameters_awg['max_freq'])) # in MHz
        self.min_freq_awg = int(float(self.specific_parameters_awg['min_freq'])) # in MHz
        self.phase_shift_ch1_seq_mode_awg = float(self.specific_parameters_awg['ch1_phase_shift']) # in radians

        ###self.phase_x = np.pi/2
        self.maxCAD_awg = 32767 # MaxCADValue of the AWG card - 1
        self.amplitude_max_awg = 260 # mV
        self.amplitude_min_awg = 1 # mV

        ####################ADC################################################################################
        if self.test_flag != 'test':
            self.sample_rate_adc = 2500 # MHz

        elif self.test_flag == 'test':
            self.test_sample_rate_adc = '2500 MHz'

        ####################DAC################################################################################
        if self.test_flag != 'test':
            # Collect all parameters for AWG settings
            self.sample_rate_awg = 1250 # MHz
            self.amplitude_0_awg = 260 # amlitude for CH0 in mV
            self.amplitude_1_awg = 260 # amlitude for CH0 in mV; 533
            self.single_joined_awg = 0

            # pulse settings
            self.reset_count_awg = 0
            self.shift_count_awg = 0
            self.increment_count_awg = 0
            self.setting_change_count_awg = 0
            self.pulse_array_awg = []
            self.pulse_array_init_awg = []
            self.pulse_name_array_awg = []
            self.pulse_ch0_array_awg = []
            self.pulse_ch1_array_awg = []
            # phase list
            self.current_phase_index_awg = 0
            self.phase_array_length_0_awg = []
            self.phase_array_length_1_awg = []

            # state counter
            self.state_awg = 0

            # update and visualize counters
            self.update_counter_awg = 0
            self.visualize_counter_awg = 0

            # correction
            self.bl_awg = 1
            self.a1_awg = 0
            self.x1_awg = 0
            self.w1_awg = 1
            self.a2_awg = 0
            self.x2_awg = 0
            self.w2_awg = 1
            self.a3_awg = 0
            self.x3_awg = 0
            self.w3_awg = 1
            self.pi2flag_awg = 1
            # in MHz
            self.low_level_awg = 16
            self.limit_awg = 23

        elif self.test_flag == 'test':
            self.test_sample_rate_awg = '1250 MHz'

            self.test_channel_awg = 'CH0'
            self.test_amplitude_awg = '250 mV'
            
            # Collect all parameters for AWG settings
            self.sample_rate_awg = 1250 
            self.amplitude_0_awg = 260
            self.amplitude_1_awg = 260
            self.single_joined_awg = 0

            # pulse settings
            self.reset_count_awg = 0
            self.shift_count_awg = 0
            self.increment_count_awg = 0
            self.setting_change_count_awg = 0
            self.pulse_array_awg = []
            self.pulse_array_init_awg = []
            self.pulse_name_array_awg = []
            self.pulse_ch0_array_awg = []
            self.pulse_ch1_array_awg = []
            # phase list
            self.current_phase_index_awg = 0
            self.phase_array_length_0_awg = []
            self.phase_array_length_1_awg = []

            # state counter
            self.state_awg = 0
            
            # update and visualize counters
            self.update_counter_awg = 0
            self.visualize_counter_awg = 0
            
            # correction
            self.bl_awg = 1
            self.a1_awg = 0
            self.x1_awg = 0
            self.w1_awg = 1
            self.a2_awg = 0
            self.x2_awg = 0
            self.w2_awg = 1
            self.a3_awg = 0
            self.x3_awg = 0
            self.w3_awg = 1
            self.pi2flag_awg = 1

            # in MHz
            self.low_level_awg = 16
            self.limit_awg = 23

        ####################INSYS BOARD###########################################################################
        if self.test_flag != 'test':
            
            file_brdLib = 'libNvsbLib.so'
            path_brdLib = "/".join(  (*(__file__.split("/")), )[:-3] + ("libs", ) + (file_brdLib, ) )
            brdLib = ctypes.cdll.LoadLibrary(path_brdLib)
            
            #===========================
            brdLib.initBrd.restype                = ctypes.c_int32
            self.initBrd                          = brdLib.initBrd

            brdLib.closeBrd.restype               = ctypes.c_int32
            self.closeBrd                         = brdLib.closeBrd

            brdLib.getDAC_ChanNum.restype         = ctypes.c_int32
            self.getDAC_ChanNum                   = brdLib.getDAC_ChanNum

            brdLib.getStrmBufSizeb.restype        = ctypes.c_int32
            self.getStrmBufSizeb                  = brdLib.getStrmBufSizeb

            brdLib.rst_GIM.restype                = ctypes.c_int32
            self.rst_GIM                          = brdLib.rst_GIM

            brdLib.setZero_GIM.restype            = ctypes.c_int32
            self.setZero_GIM                      = brdLib.setZero_GIM

            brdLib.setSync_GIM.restype            = ctypes.c_int32
            self.setSync_GIM                      = brdLib.setSync_GIM

            brdLib.getGIM_swComp_GIM_status.restype = ctypes.c_int32
            self.getGIM_swComp_GIM_status           = brdLib.getGIM_swComp_GIM_status

            brdLib.DAC_Start.restype              = ctypes.c_int32
            self.DAC_Start                        = brdLib.DAC_Start

            brdLib.AdcStreamStart.restype         = ctypes.c_int32
            self.AdcStreamStart                   = brdLib.AdcStreamStart
             
            brdLib.AdcStreamGetBufState.restype   = ctypes.c_int32
            self.AdcStreamGetBufState             = brdLib.AdcStreamGetBufState

            brdLib.AdcStreamGetBuf_ptr.restype    = ctypes.POINTER(ctypes.c_int32)
            self.AdcStreamGetBuf_ptr              = brdLib.AdcStreamGetBuf_ptr

            brdLib.getStreamBufNum.restype        = ctypes.c_int32
            self.getStreamBufNum                  = brdLib.getStreamBufNum

            #===========================
            brdLib.write_DAC_data.restype         = ctypes.c_int
            brdLib.write_DAC_data.argtypes        = [ctypes.POINTER(ctypes.c_int16), ctypes.c_int]
            self.write_DAC_data                   = brdLib.write_DAC_data

            brdLib.rstDACFIFO_GIM.restype         = ctypes.c_int32
            brdLib.rstDACFIFO_GIM.argtypes        = [ctypes.c_int]
            self.rstDACFIFO_GIM                   = brdLib.rstDACFIFO_GIM

            brdLib.setDACWriteEnable_GIM.restype  = ctypes.c_int32
            brdLib.setDACWriteEnable_GIM.argtypes = [ctypes.c_int, ctypes.c_int]
            self.setDACWriteEnable_GIM            = brdLib.setDACWriteEnable_GIM

            brdLib.rstFIFO_GIM.restype            = ctypes.c_int32
            brdLib.rstFIFO_GIM.argtypes           = [ctypes.c_int]
            self.rstFIFO_GIM                      = brdLib.rstFIFO_GIM

            brdLib.setWriteEnable_GIM.restype     = ctypes.c_int32
            brdLib.setWriteEnable_GIM.argtypes    = [ctypes.c_int, ctypes.c_int]
            self.setWriteEnable_GIM               = brdLib.setWriteEnable_GIM

            brdLib.setFIFOCnt_GIM.restype         = ctypes.c_int32
            brdLib.setFIFOCnt_GIM.argtypes        = [ctypes.c_int, ctypes.c_int]
            self.setFIFOCnt_GIM                   = brdLib.setFIFOCnt_GIM 

            brdLib.set1stChanImpLen_GIM.restype   = ctypes.c_int32
            brdLib.set1stChanImpLen_GIM.argtypes  = [ctypes.c_int, ctypes.c_int]
            self.set1stChanImpLen_GIM             = brdLib.set1stChanImpLen_GIM

            brdLib.setId_GIM.restype              = ctypes.c_int32
            brdLib.setId_GIM.argtypes             = [ctypes.c_int, ctypes.c_int, ctypes.c_int]
            self.setId_GIM                        = brdLib.setId_GIM

            brdLib.setGIM_mode.restype            = ctypes.c_int32
            brdLib.setGIM_mode.argtypes           = [ctypes.c_int, ctypes.c_int, ctypes.c_int]
            self.setGIM_mode                      = brdLib.setGIM_mode

            brdLib.setDACEnable_GIM.restype       = ctypes.c_int32
            brdLib.setDACEnable_GIM.argtypes      = [ctypes.c_int]
            self.setDACEnable_GIM                 = brdLib.setDACEnable_GIM

            brdLib.setEnable_GIM.restype          = ctypes.c_int32
            brdLib.setEnable_GIM.argtypes         = [ctypes.c_int]
            self.setEnable_GIM                    = brdLib.setEnable_GIM

            brdLib.setSelect_GIM.restype          = ctypes.c_int32
            brdLib.setSelect_GIM.argtypes         = [ctypes.c_int]
            self.setSelect_GIM                    = brdLib.setSelect_GIM

            brdLib.setSwitchEn_GIM.restype        = ctypes.c_int32
            brdLib.setSwitchEn_GIM.argtypes       = [ctypes.c_int]
            self.setSwitchEn_GIM                  = brdLib.setSwitchEn_GIM

            brdLib.writeIP.restype                = ctypes.c_int32
            brdLib.writeIP.argtypes               = [ctypes.POINTER(ctypes.c_int32), ctypes.c_int32]
            self.writeIP                          = brdLib.writeIP

            brdLib.AdcStreamGetBuf_buf.restype    = ctypes.c_int32
            brdLib.AdcStreamGetBuf_buf.argtypes   = [ctypes.POINTER(ctypes.c_int)]
            self.AdcStreamGetBuf_buf              = brdLib.AdcStreamGetBuf_buf
            

            self.nIP_No_brd                        = 0
            self.gimSum_brd                        = 1
            self.nStrmBufTotalCnt_brd              = 0
            self.nBufToClcNum_brd                  = 0
            self.nIP_NoKeeper_brd                  = -1
            
            self.data_buf_IP_GIM_brd               = []
            self.flag_sum_brd                      = 1 # 1 - average mode; 0 - single mode

            self.data_raw                          = np.zeros(10, dtype = np.int32 )
            self.count_nip                         = np.zeros(10, dtype = np.int32 )
            self.answer                            = np.zeros(10, dtype = np.complex64 )
            self.data_raw                          += self.data_raw

            self.flag_buffer_cut                   = 0
            self.nid_split                         = -1
            
            self.nid_prev                          = -1

            self.nid_pc_prev                       = 0
            self.nid_pc_prev_no_reset              = 0
            self.n_scans                           = 0
            self.ind_test                          = []
            self.correction                        = 0
            self.m                                 = 0

            self.adc_window                        = 0
            self.dac_window                        = 0
            self.flag_adc_buffer                   = 0
            self.flag_phase_cycle                  = 0
            self.buffer_ready                      = 0
            self.phases                            = 1
            self.N_IP                              = 0
            self.reset_count_nip                   = 0
            self.sub_flag                          = 0
            self.reset_flag                        = 0
            self.start                             = 0
            self.adc_sens                          = 1500 / 32768
            self.sample_rate                       = 2500 # MHz
            self.win_left                          = 0
            self.win_right                         = 2
            self.dec_coef                          = 1
            self.awg_start                         = 0

            self.mes                               = 0

        elif self.test_flag == 'test':

            self.nIP_No_brd                        = 0
            self.gimSum_brd                        = 1
            self.nStrmBufTotalCnt_brd              = 0
            self.nBufToClcNum_brd                  = 0
            self.nIP_NoKeeper_brd                  = -1
            
            self.data_buf_IP_GIM_brd               = []
            self.flag_sum_brd                      = 1

            self.data_raw                          = np.zeros(10, dtype = np.int32 )
            self.count_nip                         = np.zeros(10, dtype = np.int32 )
            self.answer                            = np.zeros(10, dtype = np.complex64 )
            self.data_raw                          += self.data_raw

            self.flag_buffer_cut                   = 0
            self.nid_split                         = -1

            self.nid_prev                          = -1

            self.nid_pc_prev                       = 0
            self.nid_pc_prev_no_reset              = 0
            self.n_scans                           = 0
            self.ind_test                          = []
            self.correction                        = 0
            self.m                                 = 0

            self.adc_window                        = 0
            self.dac_window                        = 0
            self.flag_adc_buffer                   = 0
            self.flag_phase_cycle                  = 0
            self.buffer_ready                      = 1

            self.phases                            = 1
            self.N_IP                              = 0
            self.reset_count_nip                   = 0
            self.sub_flag                          = 0
            self.reset_flag                        = 0
            self.start                             = 0
            self.adc_sens                          = 1500 / 32768
            self.sample_rate                       = 2500 # MHz
            self.win_left                          = 0
            self.win_right                         = 2
            self.dec_coef                          = 1
            self.awg_start                         = 0

            self.mes                               = 0

    # Module functions
    ####################GIM#################
    def pulser_name(self):
        answer = 'Insys 312.5 MHz MPG'
        return answer

    def pulser_pulse(self, name = 'P0', channel = 'DETECTION', start = '0 ns', length = '100 ns', \
        delta_start = '0 ns', length_increment = '0 ns', phase_list = []):
        """
        A function that added a new pulse at specified channel. The possible arguments:
        NAME, CHANNEL, START, LENGTH, DELTA_START, LENGTH_INCREMENT, PHASE_SEQUENCE
        """
        if self.test_flag != 'test':
            pulse = {'name': name, 'channel': channel, 'start': start, 'length': length, 'delta_start' : delta_start, 'length_increment': length_increment, 'phase_list': phase_list}

            temp_length = length.split(" ")
            if temp_length[1] in self.timebase_dict:
                coef = self.timebase_dict[temp_length[1]]
                p_length_raw = coef*float(temp_length[0])
                
                p_length = self.round_to_closest(p_length_raw, 3.2)
                if p_length != p_length_raw:
                    general.message(f"Pulse Length of {p_length_raw} is not divisible by 3.2. The closest available Pulse Length of {p_length} ns is used")

                pulse['length'] = str(p_length) + ' ns'

                if channel == 'DETECTION':
                    self.adc_window = int( self.adc_window + ceil(p_length / self.timebase_pulser) )
                    self.detection_phase_list = list(phase_list)
                    #self.win_right = self.adc_window - 1
                elif channel == 'TRIGGER_AWG':
                    self.dac_window = int( self.dac_window + ceil(p_length / self.timebase_pulser) )
                    pulse_awg = {'name': name + 'AWG', 'channel': 'AWG', 'start': start, 'length': length, 'delta_start' : delta_start, 'length_increment': length_increment, 'phase_list': phase_list}
                    self.pulse_array_pulser.append( pulse_awg )
                    self.pulse_name_array_pulser.append( pulse['name'] )

            temp_start = start.split(" ")
            if temp_start[1] in self.timebase_dict:
                coef = self.timebase_dict[temp_start[1]]
                p_start_raw = coef*float(temp_start[0])

                p_start = self.round_to_closest(p_start_raw, 3.2)
                if p_start != p_start_raw:
                    general.message(f"Pulse Start of {p_start_raw} is not divisible by 3.2. The closest available Pulse Start of {p_start} ns is used")

                pulse['start'] = str(p_start) + ' ns'

            temp_delta_start = delta_start.split(" ")
            if temp_delta_start[1] in self.timebase_dict:
                coef = self.timebase_dict[temp_delta_start[1]]
                p_delta_start_raw = coef*float(temp_delta_start[0])

                p_delta_start = self.round_to_closest(p_delta_start_raw, 3.2)
                if p_delta_start != p_delta_start_raw:
                    general.message(f"Pulse Delta Start of {p_delta_start_raw} is not divisible by 3.2. The closest available Pulse Delta Start of {p_delta_start} ns is used")

                pulse['delta_start'] = str(p_delta_start) + ' ns'

            temp_length_increment = length_increment.split(" ")
            if temp_length_increment[1] in self.timebase_dict:
                coef = self.timebase_dict[temp_length_increment[1]]
                p_length_increment_raw = coef*float(temp_length_increment[0])

                p_length_increment = self.round_to_closest(p_length_increment_raw, 3.2)
                if p_length_increment != p_length_increment_raw:
                    general.message(f"Pulse Length Increment of {p_length_increment_raw} is not divisible by 3.2. The closest available Pulse Length Increment of {p_length_increment} ns is used")

                pulse['length_increment'] = str(p_length_increment) + ' ns'

            self.pulse_array_pulser.append( pulse )
            # for saving the initial pulse_array_pulser without increments
            # deepcopy helps to create a TRULY NEW array and not a link to the object
            self.pulse_array_init_pulser = deepcopy( self.pulse_array_pulser )
            # pulse_name array
            self.pulse_name_array_pulser.append( pulse['name'] )
            # for correcting AMP_ON (PB restriction in 10 ns minimal instruction) according to phase pulses
            if channel == 'MW':
                self.phase_array_length_pulser.append(len(list(phase_list)))

        elif self.test_flag == 'test':

            pulse = {'name': name, 'channel': channel, 'start': start, \
                'length': length, 'delta_start' : delta_start, 'length_increment': length_increment, 'phase_list': phase_list}
            
            # phase_list's length
            if channel == 'MW':
                self.phase_array_length_pulser.append(len(list(phase_list)))
            elif channel == 'DETECTION':
                self.detection_phase_list = list(phase_list)
                self.phase_array_length_pulser.append(len(self.detection_phase_list))
                self.phase_array_length_0_awg.append(len(self.detection_phase_list))

                ###assert( len(list(phase_list)) ) == 0, 'DETECTION pulse should not have phase'

            # Checks
            # two equal names
            temp_name = str(name)
            set_from_list = set(self.pulse_name_array_pulser)
            if temp_name in set_from_list:
                assert (1 == 2), 'Two pulses have the same name. Please, rename'

            self.pulse_name_array_pulser.append( pulse['name'] )

            temp_length = length.split(" ")
            if temp_length[1] in self.timebase_dict:
                coef = self.timebase_dict[temp_length[1]]
                p_length_raw = coef*float(temp_length[0])
                
                p_length = self.round_to_closest(p_length_raw, 3.2)
                if p_length != p_length_raw:
                    general.message(f"Pulse Length is not divisible by 3.2. The closest available Pulse Length of {p_length} is used")

                pulse['length'] = str(p_length) + ' ns'

                assert( round(remainder(p_length, 3.2), 2) == 0), 'Pulse length should be divisible by 3.2'

                if channel == 'DETECTION':
                    self.adc_window = int( self.adc_window + ceil(p_length / self.timebase_pulser) )
                    assert( self.adc_window <= 3853 ), 'Maximum DETECTION WINDOW is 3270.4 ns'
                    #self.win_right = self.adc_window - 1
                elif channel == 'TRIGGER_AWG':
                    self.dac_window = int( self.dac_window + ceil(p_length / self.timebase_pulser) )
                    pulse_awg = {'name': name + 'AWG', 'channel': 'AWG', 'start': start, 'length': length, 'delta_start' : delta_start,\
                            'length_increment': length_increment, 'phase_list': phase_list}
                    self.pulse_array_pulser.append( pulse_awg )
                    self.pulse_name_array_pulser.append( pulse['name'] )

                if channel not in ('DETECTION', 'LASER', 'SYNT2'):
                    assert(p_length >= self.min_pulse_length_pulser), 'Pulse is shorter than minimum available length (' + str(self.min_pulse_length_pulser) +' ns)'
                    assert(p_length <  self.max_pulse_length_pulser), 'Pulse is longer than maximum available length (' + str(self.max_pulse_length_pulser) +' ns)'
            else:
                assert( 1 == 2 ), 'Incorrect time dimension (s, ms, us, ns)'

            temp_start = start.split(" ")
            if temp_start[1] in self.timebase_dict:
                coef = self.timebase_dict[temp_start[1]]
                p_start_raw = coef*float(temp_start[0])
                p_start = self.round_to_closest(p_start_raw, 3.2)
                if p_start != p_start_raw:
                    general.message(f"Pulse Start is not divisible by 3.2. The closest available Pulse Start of {p_start} ns is used")

                pulse['start'] = str(p_start) + ' ns'

                assert(round(remainder(p_start, 3.2), 2) == 0), 'Pulse start should be divisible by 3.2'
                assert(p_start >= 0), 'Pulse start is a negative number'
            else:
                assert( 1 == 2 ), 'Incorrect time dimension (s, ms, us, ns)'

            temp_delta_start = delta_start.split(" ")
            if temp_delta_start[1] in self.timebase_dict:
                coef = self.timebase_dict[temp_delta_start[1]]
                p_delta_start_raw = coef*float(temp_delta_start[0])

                p_delta_start = self.round_to_closest(p_delta_start_raw, 3.2)
                if p_delta_start != p_delta_start_raw:
                    general.message(f"Pulse Delta Start is not divisible by 3.2. The closest available Pulse Delta Start of {p_delta_start} ns is used")

                pulse['delta_start'] = str(p_delta_start) + ' ns'

                assert(round(remainder(p_delta_start, 3.2), 2) == 0), 'Pulse delta start should be divisible by 3.2'
                assert(p_delta_start >= 0), 'Pulse delta start is a negative number'
            else:
                assert( 1 == 2 ), 'Incorrect time dimension (s, ms, us, ns)'

            temp_length_increment = length_increment.split(" ")
            if temp_length_increment[1] in self.timebase_dict:
                coef = self.timebase_dict[temp_length_increment[1]]
                p_length_increment_raw = coef*float(temp_length_increment[0])

                p_length_increment = self.round_to_closest(p_length_increment_raw, 3.2)
                if p_length_increment != p_length_increment_raw:
                    general.message(f"Pulse Length Increment is not divisible by 3.2. The closest available Pulse Length Increment of {p_length_increment} ns is used")

                pulse['length_increment'] = str(p_length_increment) + ' ns'

                assert(round(remainder(p_length_increment, 3.2), 2) == 0), 'Pulse length increment should be divisible by 3.2'
                assert (p_length_increment >= 0 and p_length_increment < self.max_pulse_length_pulser), \
                'Pulse length increment is longer than maximum available length or negative'
            else:
                assert( 1 == 2 ), 'Incorrect time dimension (s, ms, us, ns)'

            if channel in self.channel_dict_pulser:
                if self.auto_defense_pulser == 'False':
                    self.pulse_array_pulser.append( pulse )
                    # for saving the initial pulse_array_pulser without increments
                    # deepcopy helps to create a TRULY NEW array and not a link to the object
                    self.pulse_array_init_pulser = deepcopy(self.pulse_array_pulser)
                elif self.auto_defense_pulser == 'True':
                    if channel == 'AMP_ON' or channel == 'LNA_PROTECT':
                        assert( 1 == 2), 'In auto_defense mode AMP_ON and LNA_PROTECT pulses are set automatically'
                    else:
                        self.pulse_array_pulser.append( pulse )
                        # for saving the initial pulse_array_pulser without increments
                        # deepcopy helps to create a TRULY NEW array and not a link to the object
                        self.pulse_array_init_pulser = deepcopy(self.pulse_array_pulser)
                else:
                    assert(1 == 2), 'Incorrect auto_defense setting'
            else:
                assert (1 == 2), 'Incorrect channel name'

    def pulser_redefine_start(self, *, name, start):
        """
        A function for redefining start of the specified pulse.
        pulser_redefine_start(name = 'P0', start = '100 ns') changes start of the 'P0' pulse to 100 ns.
        The main purpose of the function is non-uniform sampling / 2D experimental scripts

        def func(*, name1, name2): defines a function without default values of key arguments
        """

        if self.test_flag != 'test':
            i = 0

            while i < len( self.pulse_array_pulser ):
                if name == self.pulse_array_pulser[i]['name']:

                    temp_start = start.split(" ")
                    if temp_start[1] in self.timebase_dict:
                        coef = self.timebase_dict[temp_start[1]]
                        p_start_raw = coef*float(temp_start[0])
                        p_start = self.round_to_closest(p_start_raw, 3.2)
                        if p_start != p_start_raw:
                            general.message(f"Pulse Start is not divisible by 3.2. The closest available Pulse Start of {p_start} ns is used")
                    self.pulse_array_pulser[i]['start'] = str(p_start) + ' ns'
                    self.shift_count_pulser = 1
                else:
                    pass

                i += 1

        elif self.test_flag == 'test':
            i = 0
            assert( name in self.pulse_name_array_pulser ), 'Pulse with the specified name is not defined'

            while i < len( self.pulse_array_pulser ):
                if name == self.pulse_array_pulser[i]['name']:

                    # checks
                    temp_start = start.split(" ")
                    if temp_start[1] in self.timebase_dict:
                        coef = self.timebase_dict[temp_start[1]]
                        p_start_raw = coef*float(temp_start[0])
                        p_start = self.round_to_closest(p_start_raw, 3.2)
                        if p_start != p_start_raw:
                            general.message(f"Pulse Start is not divisible by 3.2. The closest available Pulse Start of {p_start} ns is used")
                        assert(round(remainder(p_start, 3.2), 2) == 0), 'Pulse start should be divisible by 3.2'
                        assert(p_start >= 0), 'Pulse start is a negative number'
                    else:
                        assert( 1 == 2 ), 'Incorrect time dimension (s, ms, us, ns)'

                    self.pulse_array_pulser[i]['start'] = str(p_start) + ' ns'
                    self.shift_count_pulser = 1
                else:
                    pass

                i += 1

    def pulser_redefine_delta_start(self, *, name, delta_start):
        """
        A function for redefining delta_start of the specified pulse.
        pulser_redefine_delta_start(name = 'P0', delta_start = '10 ns') changes delta_start of the 'P0' pulse to 10 ns.
        The main purpose of the function is non-uniform sampling.

        def func(*, name1, name2): defines a function without default values of key arguments
        """

        if self.test_flag != 'test':
            i = 0

            while i < len( self.pulse_array_pulser ):
                if name == self.pulse_array_pulser[i]['name']:
                    temp_delta_start = delta_start.split(" ")
                    if temp_delta_start[1] in self.timebase_dict:
                        coef = self.timebase_dict[temp_delta_start[1]]
                        p_delta_start_raw = coef*float(temp_delta_start[0])
                        p_delta_start = self.round_to_closest(p_delta_start_raw, 3.2)
                        if p_delta_start != p_delta_start_raw:
                            general.message(f"Pulse Delta start of {p_delta_start_raw} is not divisible by 3.2. The closest available Pulse Delta start of {p_delta_start} ns is used")

                    self.pulse_array_pulser[i]['delta_start'] = str(p_delta_start) + ' ns'
                    self.shift_count_pulser = 1
                else:
                    pass

                i += 1

        elif self.test_flag == 'test':
            i = 0
            assert( name in self.pulse_name_array_pulser ), 'Pulse with the specified name is not defined'

            while i < len( self.pulse_array_pulser ):
                if name == self.pulse_array_pulser[i]['name']:

                    # checks
                    temp_delta_start = delta_start.split(" ")
                    if temp_delta_start[1] in self.timebase_dict:
                        coef = self.timebase_dict[temp_delta_start[1]]
                        p_delta_start_raw = coef*float(temp_delta_start[0])
                        p_delta_start = self.round_to_closest(p_delta_start_raw, 3.2)
                        if p_delta_start != p_delta_start_raw:
                            general.message(f"Pulse Delta start is not divisible by 3.2. The closest available Pulse Delta start of {p_delta_start} ns is used")

                        assert(round(remainder(p_delta_start, 3.2), 2) == 0), 'Pulse delta start should be divisible by 3.2'
                        assert(p_delta_start >= 0), 'Pulse delta start is a negative number'
                    else:
                        assert( 1 == 2 ), 'Incorrect time dimension (s, ms, us, ns)'

                    self.pulse_array_pulser[i]['delta_start'] = str(p_delta_start) + ' ns'
                    self.shift_count_pulser = 1
                else:
                    pass

                i += 1

    def pulser_redefine_length_increment(self, *, name, length_increment):
        """
        A function for redefining length_increment of the specified pulse.
        pulser_redefine_length_increment(name = 'P0', length_increment = '10 ns') changes length_increment of the 'P0' pulse to '10 ns'.
        The main purpose of the function is non-uniform sampling.

        def func(*, name1, name2): defines a function without default values of key arguments
        """

        if self.test_flag != 'test':
            i = 0

            while i < len( self.pulse_array_pulser ):
                if name == self.pulse_array_pulser[i]['name']:
                    temp_length_increment = length_increment.split(" ")
                    if temp_length_increment[1] in self.timebase_dict:
                        coef = self.timebase_dict[temp_length_increment[1]]
                        p_length_increment_raw = coef*float(temp_length_increment[0])
                        p_length_increment = self.round_to_closest(p_length_increment_raw, 3.2)
                        if p_length_increment != p_length_increment_raw:
                            general.message(f"Pulse length increment of {p_length_increment_raw} is not divisible by 3.2. The closest available Pulse length increment of {p_length_increment} ns is used")

                    self.pulse_array_pulser[i]['length_increment'] = str(length_increment)
                    self.increment_count_pulser = 1
                else:
                    pass

                i += 1

        elif self.test_flag == 'test':
            i = 0

            assert( name in self.pulse_name_array_pulser ), 'Pulse with the specified name is not defined'

            while i < len( self.pulse_array_pulser ):
                if name == self.pulse_array_pulser[i]['name']:
                    # checks
                    temp_length_increment = length_increment.split(" ")
                    if temp_length_increment[1] in self.timebase_dict:
                        coef = self.timebase_dict[temp_length_increment[1]]
                        p_length_increment_raw = coef*float(temp_length_increment[0])
                        p_length_increment = self.round_to_closest(p_length_increment_raw, 3.2)
                        if p_length_increment != p_length_increment_raw:
                            general.message(f"Pulse length increment is not divisible by 3.2. The closest available Pulse length increment of {p_length_increment} ns is used")
                        
                        assert(round(remainder(p_length_increment, 3.2), 2) == 0), 'Pulse length increment should be divisible by 3.2'
                        assert (p_length_increment >= 0 and p_length_increment < self.max_pulse_length_pulser), \
                        'Pulse length increment is longer than maximum available length or negative'
                    else:
                        assert( 1 == 2 ), 'Incorrect time dimension (s, ms, us, ns)'

                    self.pulse_array_pulser[i]['length_increment'] = str(p_length_increment) + ' ns'
                    self.increment_count_pulser = 1
                else:
                    pass

                i += 1

    def pulser_next_phase(self):
        """
        A function for phase cycling. It works using phase_list decleared in pulser_pulse():
        phase_list = ['-y', '+x', '-x', '+x']
        self.current_phase_index_pulser is an iterator of the current phase
        functions pulser_shift() and pulser_increment() reset the iterator

        after calling pulser_next_phase() the next phase is taken from phase_list and a 
        corresponding trigger pulse is added to self.pulse_array_pulser

        the length of all phase lists specified for different MW pulses has to be the same
        
        the function also immediately sends intructions to pulse blaster as
        a function pulser_update() does. 
        """
        if self.test_flag != 'test':
            # deleting old phase switch pulses from self.pulse_array_pulser
            # before adding new ones
            for i in range(self.phase_pulses_pulser):
                for index, element in enumerate(self.pulse_array_pulser):
                    if element['channel'] == '-X' or element['channel'] == '+Y':
                        del self.pulse_array_pulser[index]
                        break

            self.phase_pulses_pulser = 0
            # adding phase switch pulses
            for index, element in enumerate(self.pulse_array_pulser):            
                if (len(list(element['phase_list'])) != 0) and (element['channel'] != 'DETECTION'):
                    if element['phase_list'][self.current_phase_index_pulser] == '+x':
                        #pass
                        # 21-08-2021; Correction of non updating case for ['-x', '+x']
                        if self.phase_array_length_pulser[0] == 1:
                            pass
                        else:
                            self.reset_count_pulser = 0

                    elif element['phase_list'][self.current_phase_index_pulser] == '-x':
                        name = element['name'] + '_ph_seq-x'
                        # taking into account delays of phase switching
                        start = self.change_pulse_settings_pulser(element['start'], -self.switch_phase_delay_pulser)
                        length = self.change_pulse_settings_pulser(element['length'], self.phase_delay_pulser + self.switch_phase_delay_pulser)

                        self.pulse_array_pulser.append({'name': name, 'channel': '-X', 'start': start, \
                            'length': length, 'delta_start' : '0 ns', 'length_increment': '0 ns', 'phase_list': []})
                        
                        if self.phase_array_length_pulser[0] == 1:
                            pass
                        else:
                            self.reset_count_pulser = 0

                        self.phase_pulses_pulser += 1

                    elif element['phase_list'][self.current_phase_index_pulser] == '+y':
                        name = element['name'] + '_ph_seq+y'
                        # taking into account delays of phase switching
                        start = self.change_pulse_settings_pulser(element['start'], -self.switch_phase_delay_pulser)
                        length = self.change_pulse_settings_pulser(element['length'], self.phase_delay_pulser + self.switch_phase_delay_pulser)

                        self.pulse_array_pulser.append({'name': name, 'channel': '+Y', 'start': start, \
                            'length': length, 'delta_start' : '0 ns', 'length_increment': '0 ns', 'phase_list': []})

                        if self.phase_array_length_pulser[0] == 1:
                            pass
                        else:
                            self.reset_count_pulser = 0

                        self.phase_pulses_pulser += 1

                    elif element['phase_list'][self.current_phase_index_pulser] == '-y':
                        name = element['name'] + '_ph_seq-y'
                        # taking into account delays of phase switching
                        start = self.change_pulse_settings_pulser(element['start'], -self.switch_phase_delay_pulser)
                        length = self.change_pulse_settings_pulser(element['length'], self.phase_delay_pulser + self.switch_phase_delay_pulser)

                        # -Y for Mikran bridge is simutaneously turned on -X; +Y
                        # that is why there is no -Y channel
                        self.pulse_array_pulser.append({'name': name, 'channel': '-X', 'start': start, \
                            'length': length, 'delta_start' : '0 ns', 'length_increment': '0 ns', 'phase_list': []})
                        self.pulse_array_pulser.append({'name': name, 'channel': '+Y', 'start': start, \
                            'length': length, 'delta_start' : '0 ns', 'length_increment': '0 ns', 'phase_list': []})

                        if self.phase_array_length_pulser[0] == 1:
                            pass
                        else:
                            self.reset_count_pulser = 0

                        self.phase_pulses_pulser += 2

            if self.phase_array_length_pulser[0] == 1:
                pass
            else:
                self.current_phase_index_pulser += 1


            # update pulses
            # get repetition rate
            rep_rate_pulser = self.rep_rate_pulser[0]
            if rep_rate_pulser[-3:] == ' Hz':
                rep_time = int(1000000000/float(rep_rate_pulser[:-3]))
            elif rep_rate_pulser[-3:] == 'kHz':
                rep_time = int(1000000/float(rep_rate_pulser[:-4]))
            elif rep_rate_pulser[-3:] == 'MHz':
                rep_time = int(1000/float(rep_rate_pulser[:-4]))

            rep_time = self.round_to_closest(rep_time, 3.2)

            self.pulser_update()

        elif self.test_flag == 'test':

            # check that the length is equal (compare all elements in self.phase_array_length_pulser)
            gr = groupby(self.phase_array_length_pulser)
            if (next(gr, True) and not next(gr, False)) == False:
                assert(1 == 2), 'Phase sequence does not have equal length'

            for i in range(self.phase_pulses_pulser):
                for index, element in enumerate(self.pulse_array_pulser):
                    if element['channel'] == '-X' or element['channel'] == '+Y':
                        del self.pulse_array_pulser[index]
                        break

            self.phase_pulses_pulser = 0
            for index, element in enumerate(self.pulse_array_pulser):
                if (len(list(element['phase_list'])) != 0) and (element['channel'] != 'DETECTION'):
                    if element['phase_list'][self.current_phase_index_pulser] == '+x':
                        #pass
                        # 21-08-2021; Correction of non updating case for ['-x', '+x']
                        if self.phase_array_length_pulser[0] == 1:
                            pass
                        else:
                            self.reset_count_pulser = 0

                    elif element['phase_list'][self.current_phase_index_pulser] == '-x':
                        name = element['name'] + '_ph_seq-x'
                        # taking into account delays
                        start = self.change_pulse_settings_pulser(element['start'], -self.switch_phase_delay_pulser)
                        length = self.change_pulse_settings_pulser(element['length'], self.phase_delay_pulser + self.switch_phase_delay_pulser)

                        self.pulse_array_pulser.append({'name': name, 'channel': '-X', 'start': start, \
                            'length': length, 'delta_start' : '0 ns', 'length_increment': '0 ns', 'phase_list': []})

                        # check that we still have a next phase to switch
                        if self.phase_array_length_pulser[0] == 1:
                            pass
                        else:
                            self.reset_count_pulser = 0
                        self.phase_pulses_pulser += 1

                    elif element['phase_list'][self.current_phase_index_pulser] == '+y':
                        name = element['name'] + '_ph_seq+y'
                        # taking into account delays
                        start = self.change_pulse_settings_pulser(element['start'], -self.switch_phase_delay_pulser)
                        length = self.change_pulse_settings_pulser(element['length'], self.phase_delay_pulser + self.switch_phase_delay_pulser)

                        self.pulse_array_pulser.append({'name': name, 'channel': '+Y', 'start': start, \
                            'length': length, 'delta_start' : '0 ns', 'length_increment': '0 ns', 'phase_list': []})

                        # check that we still have a next phase to switch
                        if self.phase_array_length_pulser[0] == 1:
                            pass
                        else:
                            self.reset_count_pulser = 0
                        self.phase_pulses_pulser += 1

                    elif element['phase_list'][self.current_phase_index_pulser] == '-y':
                        name = element['name'] + '_ph_seq-y'
                        # taking into account delays
                        start = self.change_pulse_settings_pulser(element['start'], -self.switch_phase_delay_pulser)
                        length = self.change_pulse_settings_pulser(element['length'], self.phase_delay_pulser + self.switch_phase_delay_pulser)

                        # -Y for Mikran bridge is simutaneously turned on -X; +Y
                        # that is why there is no -Y channel
                        self.pulse_array_pulser.append({'name': name, 'channel': '-X', 'start': start, \
                            'length': length, 'delta_start' : '0 ns', 'length_increment': '0 ns', 'phase_list': []})
                        self.pulse_array_pulser.append({'name': name, 'channel': '+Y', 'start': start, \
                            'length': length, 'delta_start' : '0 ns', 'length_increment': '0 ns', 'phase_list': []})

                        # check that we still have a next phase to switch
                        if self.phase_array_length_pulser[0] == 1:
                            pass
                        else:
                            self.reset_count_pulser = 0
                        self.phase_pulses_pulser += 2

                    else:
                        assert( 1 == 2 ), 'Incorrect phase name (+x, -x, +y, -y)'
                else:
                    pass
            
            if self.phase_array_length_pulser[0] == 1:
                pass
            else:
                self.current_phase_index_pulser += 1
            
            # update pulses
            # get repetition rate
            rep_rate_pulser = self.rep_rate_pulser[0]
            if rep_rate_pulser[-3:] == ' Hz':
                rep_time = int(1000000000/float(rep_rate_pulser[:-3]))
            elif rep_rate_pulser[-3:] == 'kHz':
                rep_time = int(1000000/float(rep_rate_pulser[:-4]))
            elif rep_rate_pulser[-3:] == 'MHz':
                rep_time = int(1000/float(rep_rate_pulser[:-4]))

            rep_time = self.round_to_closest(rep_time, 3.2)

            self.pulser_update()

    def pulser_update(self):
        """
        A function that write instructions to PB. 
        Repetition rate is taking into account by adding a last pulse with delay.
        Currently, all pulses are cycled using BRANCH.
        """
        if self.test_flag != 'test':
            # get repetition rate
            rep_rate_pulser = self.rep_rate_pulser[0]
            if rep_rate_pulser[-3:] == ' Hz':
                rep_time = int(1000000000/float(rep_rate_pulser[:-3]))
            elif rep_rate_pulser[-3:] == 'kHz':
                rep_time = int(1000000/float(rep_rate_pulser[:-4]))
            elif rep_rate_pulser[-3:] == 'MHz':
                rep_time = int(1000/float(rep_rate_pulser[:-4]))

            rep_time = self.round_to_closest(rep_time, 3.2)

            if self.reset_count_pulser == 0 or self.shift_count_pulser == 1 or self.increment_count_pulser == 1 or self.rep_rate_count_pulser == 1:
                # using a special functions for convertion to instructions
                # we get two return arrays because of pulser_visualizer. It is not the case for test flag.
                #temp, visualizer = self.convert_to_bit_pulse( self.pulse_array_pulser )
                
                #to_spinapi = self.instruction_pulse( temp, rep_time )
                to_spinapi = self.split_into_parts_pulser( self.pulse_array_pulser, rep_time )            
                
                to_spinapi2 = np.array(to_spinapi, dtype = np.int64)
                if self.awg_pulses_pulser == 1:
                    to_spinapi3 = to_spinapi2 + np.array( [512, 0, 0] )
                    to_spinapi3[-1, 0] = 0
                    self.gen_GIM_words( to_spinapi3 ) # Создает главный буфер 
                else:
                    self.gen_GIM_words( to_spinapi2 ) # Создает главный буфер 
                #general.message( to_spinapi3 )
                #self.gen_GIM_words( np.array(to_spinapi, dtype = np.int64) ) # Создает главный буфер 
                
                if (self.nIP_NoKeeper_brd != self.nIP_No_brd):

                    if self.awg_pulses_pulser == 1:
                        self.write_data_DAC(self.nIP_No_brd)
                    
                    self.write_data_GIM_brd()

                    self.nIP_NoKeeper_brd = self.nIP_No_brd

                #general.message(f"N_IP: {self.nIP_No_brd}")

                # Run GIM at the begining of the experiment
                if self.nIP_No_brd == 0:
                    if self.start == 0:
                        self.nIP_No_brd += 1
                        self.start_brd()
                        self.start = 1
                    else:
                        # SCANS
                        while True:
                            if( 1 == self.getGIM_swComp_GIM_status() ):
                                self.nIP_No_brd += 1
                                break
                            else:
                                pass
                    #if( 1 == self.getGIM_swComp_GIM_status() ):
                    #    self.nIP_No_brd = self.nIP_No_brd + 1
                else:
                    while True:
                        if( 1 == self.getGIM_swComp_GIM_status() ):
                            self.nIP_No_brd += 1
                            break
                        else:
                            pass

                #general.message( f'PU: {self.nIP_No_brd}' )
                self.reset_count_pulser = 1
                self.shift_count_pulser = 0
                self.increment_count_pulser = 0
                self.rep_rate_count_pulser = 0

                self.iterator_of_updates_pulser += 1
            else:
                pass

        elif self.test_flag == 'test':
            # get repetition rate
            rep_rate_pulser = self.rep_rate_pulser[0]
            if rep_rate_pulser[-3:] == ' Hz':
                rep_time = int(1000000000/float(rep_rate_pulser[:-3]))
            elif rep_rate_pulser[-3:] == 'kHz':
                rep_time = int(1000000/float(rep_rate_pulser[:-4]))
            elif rep_rate_pulser[-3:] == 'MHz':
                rep_time = int(1000/float(rep_rate_pulser[:-4]))
            else:
                assert(1 == 2), "Incorrect repetition rate dimension (Hz, kHz, MHz)"

            rep_time = self.round_to_closest(rep_time, 3.2)
            #assert( float(self.rep_rate_pulser[0].split(" ")[0]) < 12000 ), f'Repetition rate cannot exceed {12} kHz'

            if self.reset_count_pulser == 0 or self.shift_count_pulser == 1 or self.increment_count_pulser == 1:
                # using a special functions for convertion to instructions
                #to_spinapi = self.instruction_pulse( self.convert_to_bit_pulse( self.pulse_array_pulser ) )
                to_spinapi = self.split_into_parts_pulser( self.pulse_array_pulser, rep_time )

                to_spinapi2 = np.array(to_spinapi, dtype = np.int64)
                if self.awg_pulses_pulser == 1:
                    to_spinapi3 = to_spinapi2 + np.array( [512, 0, 0] )
                    to_spinapi3[-1, 0] = 0
                    self.gen_GIM_words( to_spinapi3 ) # Создает главный буфер
                else:
                    self.gen_GIM_words( to_spinapi2 ) # Создает главный буфер 

                #self.gen_GIM_words( np.array(to_spinapi, dtype = np.int64) ) # Создает главный буфер 

                if self.awg_pulses_pulser == 1:
                    self.awg_update()
                    self.write_data_DAC(0)

                #general.message(to_spinapi)
                #self.spinapi = to_spinapi
                #self.gen_GIM_words( np.array(to_spinapi, dtype = np.int64) ) # Создает главный буфер 

                self.reset_count_pulser = 1
                self.shift_count_pulser = 0
                self.increment_count_pulser = 0
                self.rep_rate_count_pulser = 0

            else:
                pass

    def pulser_repetition_rate(self, *r_rate):
        """
        A function to get or set repetition rate.
        !!!! BEFORE PULSER_OPEN() !!!!
        """
        if self.test_flag != 'test':
            if  len(r_rate) == 1:
                self.rep_rate_pulser = r_rate

                rep_rate_pulser = self.rep_rate_pulser[0]
                if rep_rate_pulser[-3:] == ' Hz':
                    rep_time = int(1000000000/float(rep_rate_pulser[:-3]))
                elif rep_rate_pulser[-3:] == 'kHz':
                    rep_time = int(1000000/float(rep_rate_pulser[:-4]))
                elif rep_rate_pulser[-3:] == 'MHz':
                    rep_time = int(1000/float(rep_rate_pulser[:-4]))

                rep_time = self.round_to_closest(rep_time, 3.2)

                if rep_time > 20408163:
                    if self.adc_window <= 256:
                        self.change_ini_file("streamBufSizeKb = 1024", "streamBufSizeKb = 128")
                    elif (self.adc_window > 256) and (self.adc_window <= 511):
                        self.change_ini_file("streamBufSizeKb = 1024", "streamBufSizeKb = 256")
                    elif (self.adc_window > 511) and (self.adc_window <= 1022):
                        self.change_ini_file("streamBufSizeKb = 1024", "streamBufSizeKb = 512")
                elif rep_time <= 20408163:
                    self.change_ini_file("streamBufSizeKb = 128", "streamBufSizeKb = 1024")
                    #self.change_ini_file("streamBufSizeKb = 256", "streamBufSizeKb = 1024")
                    self.change_ini_file("streamBufSizeKb = 512", "streamBufSizeKb = 1024")
                    

                self.rep_rate_count_pulser = 1
            elif len(r_rate) == 0:
                return self.rep_rate_pulser[0]

        elif self.test_flag == 'test':
            if  len(r_rate) == 1:
                self.rep_rate_pulser = r_rate
                rep_rate_pulser = self.rep_rate_pulser[0]
                if rep_rate_pulser[-3:] == ' Hz':
                    rep_time = int(1000000000/float(rep_rate_pulser[:-3]))
                elif rep_rate_pulser[-3:] == 'kHz':
                    rep_time = int(1000000/float(rep_rate_pulser[:-4]))
                elif rep_rate_pulser[-3:] == 'MHz':
                    rep_time = int(1000/float(rep_rate_pulser[:-4]))

                rep_time = self.round_to_closest(rep_time, 3.2)

                if rep_time > 20408163:
                    self.change_ini_file("streamBufSizeKb = 1024", "streamBufSizeKb = 128")
                elif rep_time <= 20408163:
                    self.change_ini_file("streamBufSizeKb = 128", "streamBufSizeKb = 1024")

                self.rep_rate_count_pulser = 1
            elif len(r_rate) == 0:
                return self.rep_rate_pulser[0]

    def pulser_shift(self, *pulses):
        """
        A function to shift the start of the pulses.
        The function directly affects the pulse_array_pulser.
        """
        if self.test_flag != 'test':
            if len(pulses) == 0:
                i = 0
                while i < len( self.pulse_array_pulser ):
                    if float( self.pulse_array_pulser[i]['delta_start'][:-3] ) == 0:
                        pass
                    else:
                        # convertion to ns
                        temp = self.pulse_array_pulser[i]['delta_start'].split(' ')
                        if temp[1] in self.timebase_dict:
                            flag = self.timebase_dict[temp[1]]
                            d_start = float((temp[0]))*flag
                        else:
                            pass

                        temp2 = self.pulse_array_pulser[i]['start'].split(' ')
                        if temp2[1] in self.timebase_dict:
                            flag2 = self.timebase_dict[temp2[1]]
                            st = float((temp2[0]))*flag2
                        else:
                            pass
                                
                        self.pulse_array_pulser[i]['start'] = str( st + d_start ) + ' ns'
 
                    i += 1

                self.shift_count_pulser = 1
                self.current_phase_index_pulser = 0

            else:
                set_from_list = set(pulses)
                for element in set_from_list:
                    if element in self.pulse_name_array_pulser:
                        pulse_index =  self.pulse_name_array_pulser.index(element)

                        if float( self.pulse_array_pulser[pulse_index]['delta_start'][:-3] ) == 0:
                            pass
                        else:
                            # convertion to ns
                            temp = self.pulse_array_pulser[pulse_index]['delta_start'].split(' ')
                            if temp[1] in self.timebase_dict:
                                flag = self.timebase_dict[temp[1]]
                                d_start = float((temp[0]))*flag
                            else:
                                pass

                            temp2 = self.pulse_array_pulser[pulse_index]['start'].split(' ')
                            if temp2[1] in self.timebase_dict:
                                flag2 = self.timebase_dict[temp2[1]]
                                st = float((temp2[0]))*flag2
                            else:
                                pass
                                    
                            self.pulse_array_pulser[pulse_index]['start'] = str( st + d_start ) + ' ns'

                        self.shift_count_pulser = 1
                        self.current_phase_index_pulser = 0

        elif self.test_flag == 'test':
            if len(pulses) == 0:
                i = 0
                while i < len( self.pulse_array_pulser ):
                    if float( self.pulse_array_pulser[i]['delta_start'][:-3] ) == 0:
                        pass
                    else:
                        # convertion to ns
                        temp = self.pulse_array_pulser[i]['delta_start'].split(' ')
                        if temp[1] in self.timebase_dict:
                            flag = self.timebase_dict[temp[1]]
                            d_start = float((temp[0]))*flag
                        else:
                            assert(1 == 2), "Incorrect time dimension (ns, us, ms, s)"

                        temp2 = self.pulse_array_pulser[i]['start'].split(' ')
                        if temp2[1] in self.timebase_dict:
                            flag2 = self.timebase_dict[temp2[1]]
                            st = float((temp2[0]))*flag2
                        else:
                            assert(1 == 2), "Incorrect time dimension (ns, us, ms, s)"
                                
                        self.pulse_array_pulser[i]['start'] = str( st + d_start ) + ' ns'

                    i += 1

                self.shift_count_pulser = 1
                self.current_phase_index_pulser = 0

            else:
                set_from_list = set(pulses)
                for element in set_from_list:
                    if element in self.pulse_name_array_pulser:
                        pulse_index =  self.pulse_name_array_pulser.index(element)

                        if float( self.pulse_array_pulser[pulse_index]['delta_start'][:-3] ) == 0:
                            pass
                        else:
                            # convertion to ns
                            temp = self.pulse_array_pulser[pulse_index]['delta_start'].split(' ')
                            if temp[1] in self.timebase_dict:
                                flag = self.timebase_dict[temp[1]]
                                d_start = float((temp[0]))*flag
                            else:
                                assert(1 == 2), "Incorrect time dimension (ns, us, ms, s)"
                            

                            temp2 = self.pulse_array_pulser[pulse_index]['start'].split(' ')
                            if temp2[1] in self.timebase_dict:
                                flag2 = self.timebase_dict[temp2[1]]
                                st = float((temp2[0]))*flag2
                            else:
                                assert(1 == 2), "Incorrect time dimension (ns, us, ms, s)"
                                    
                            self.pulse_array_pulser[pulse_index]['start'] = str( st + d_start ) + ' ns'

                        self.shift_count_pulser = 1
                        self.current_phase_index_pulser = 0

                    else:
                        assert(1 == 2), "There is no pulse with the specified name"

    def pulser_increment(self, *pulses):
        """
        A function to increment the length of the pulses.
        The function directly affects the pulse_array_pulser.
        """
        if self.test_flag != 'test':
            if len(pulses) == 0:
                i = 0
                while i < len( self.pulse_array_pulser ):
                    if float( self.pulse_array_pulser[i]['length_increment'][:-3] ) == 0:
                        pass
                    else:
                        # convertion to ns
                        temp = self.pulse_array_pulser[i]['length_increment'].split(' ')
                        if temp[1] in self.timebase_dict:
                            flag = self.timebase_dict[temp[1]]
                            d_length = (float(temp[0]))*flag
                        else:
                            pass

                        temp2 = self.pulse_array_pulser[i]['length'].split(' ')
                        if temp2[1] in self.timebase_dict:
                            flag2 = self.timebase_dict[temp2[1]]
                            leng = (float(temp2[0]))*flag2
                        else:
                            pass

                        self.pulse_array_pulser[i]['length'] = str( leng + d_length ) + ' ns'
 
                    i += 1

                self.increment_count_pulser = 1
                self.current_phase_index_pulser = 0

            else:
                set_from_list = set(pulses)
                for element in set_from_list:
                    if element in self.pulse_name_array_pulser:
                        pulse_index = self.pulse_name_array_pulser.index(element)

                        if float( self.pulse_array_pulser[pulse_index]['length_increment'][:-3] ) == 0:
                            pass
                        else:
                            # convertion to ns
                            temp = self.pulse_array_pulser[pulse_index]['length_increment'].split(' ')
                            if temp[1] in self.timebase_dict:
                                flag = self.timebase_dict[temp[1]]
                                d_length = (float(temp[0]))*flag
                            else:
                                pass

                            temp2 = self.pulse_array_pulser[pulse_index]['length'].split(' ')
                            if temp2[1] in self.timebase_dict:
                                flag2 = self.timebase_dict[temp2[1]]
                                leng = (float(temp2[0]))*flag2
                            else:
                                pass
                            
                            self.pulse_array_pulser[pulse_index]['length'] = str( leng + d_length ) + ' ns'

                        self.increment_count_pulser = 1
                        self.current_phase_index_pulser = 0

        elif self.test_flag == 'test':
            if len(pulses) == 0:
                i = 0
                while i < len( self.pulse_array_pulser ):
                    if float( self.pulse_array_pulser[i]['length_increment'][:-3] ) == 0:
                        pass
                    else:
                        # convertion to ns
                        temp = self.pulse_array_pulser[i]['length_increment'].split(' ')
                        if temp[1] in self.timebase_dict:
                            flag = self.timebase_dict[temp[1]]
                            d_length = (float(temp[0]))*flag
                        else:
                            assert(1 == 2), "Incorrect time dimension (ns, us, ms, s)"

                        temp2 = self.pulse_array_pulser[i]['length'].split(' ')
                        if temp2[1] in self.timebase_dict:
                            flag2 = self.timebase_dict[temp2[1]]
                            leng = (float(temp2[0]))*flag2
                        else:
                            assert(1 == 2), "Incorrect time dimension (ns, us, ms, s)"
                        
                        if ( leng + d_length ) <= self.max_pulse_length_pulser:
                            self.pulse_array_pulser[i]['length'] = str( leng + d_length ) + ' ns'
                        else:
                            assert(1 == 2), 'Exceeded maximum pulse length (1900 ns) when increment the pulse'

                    i += 1

                self.increment_count_pulser = 1
                self.current_phase_index_pulser = 0

            else:
                set_from_list = set(pulses)
                for element in set_from_list:
                    if element in self.pulse_name_array_pulser:

                        pulse_index = self.pulse_name_array_pulser.index(element)
                        if float( self.pulse_array_pulser[pulse_index]['length_increment'][:-3] ) == 0:
                            pass
                        else:
                            # convertion to ns
                            temp = self.pulse_array_pulser[pulse_index]['length_increment'].split(' ')
                            if temp[1] in self.timebase_dict:
                                flag = self.timebase_dict[temp[1]]
                                d_length = (float(temp[0]))*flag
                            else:
                                assert(1 == 2), "Incorrect time dimension (ns, us, ms, s)"

                            temp2 = self.pulse_array_pulser[pulse_index]['length'].split(' ')
                            if temp2[1] in self.timebase_dict:
                                flag2 = self.timebase_dict[temp2[1]]
                                leng = (float(temp2[0]))*flag2
                            else:
                                assert(1 == 2), "Incorrect time dimension (ns, us, ms, s)"
                                    
                            if ( leng + d_length ) <= self.max_pulse_length_pulser:
                                self.pulse_array_pulser[pulse_index]['length'] = str( leng + d_length ) + ' ns'
                            else:
                                assert(1 == 2), 'Exceeded maximum pulse length (1900 ns) when increment the pulse'

                        self.increment_count_pulser = 1
                        self.current_phase_index_pulser = 0

                    else:
                        assert(1 == 2), "There is no pulse with the specified name"

    def pulser_pulse_reset(self, *pulses, interal_cycle = 'False'):
        """
        Reset all pulses to the initial state it was in at the start of the experiment.
        It does not update the pulser, if you want to reset all pulses and and also update 
        the pulser use the function pulser_reset() instead.
        """
        if self.test_flag != 'test':

            #general.wait('10 ms')
            #self.pulser_stop()
            self.nIP_No_brd = 0
            #self.nBufToClcNum_brd = 0
            #self.nStrmBufTotalCnt_brd = 0
            self.nIP_NoKeeper_brd = -1
            ###self.buffer_ready = 1
            self.reset_count_nip = 1
            self.sub_flag = 0
            # 1 -> 0
            self.reset_flag = 0
            #self.flag_adc_buffer = 0
            #self.flag_phase_cycle = 0
            self.nid_pc_prev = 0
            self.N_IP = 0

            if len(pulses) == 0:
                self.pulse_array_pulser = deepcopy(self.pulse_array_init_pulser)
                self.reset_count_pulser = 0
                self.increment_count_pulser = 0
                self.shift_count_pulser = 0
                self.current_phase_index_pulser = 0
                if interal_cycle == 'False':
                    self.iterator_of_updates_pulser = 0
                elif interal_cycle == 'True':
                    pass

            else:
                set_from_list = set(pulses)
                for element in set_from_list:
                    if element in self.pulse_name_array_pulser:
                        pulse_index = self.pulse_name_array_pulser.index(element)

                        self.pulse_array_pulser[pulse_index]['start'] = self.pulse_array_init_pulser[pulse_index]['start']
                        self.pulse_array_pulser[pulse_index]['length'] = self.pulse_array_init_pulser[pulse_index]['length']

                        self.reset_count_pulser = 0
                        self.increment_count_pulser = 0
                        self.shift_count_pulser = 0
                        self.current_phase_index_pulser = 0
                        #self.iterator_of_updates_pulser = 0

        elif self.test_flag == 'test':

            #self.pulser_stop()
            self.nIP_No_brd = 0
            #self.nBufToClcNum_brd = 0
            #self.nStrmBufTotalCnt_brd = 0
            self.nIP_NoKeeper_brd = -1
            ###self.buffer_ready = 1
            self.reset_count_nip = 1
            self.sub_flag = 0
            self.reset_flag = 0
            #self.flag_adc_buffer = 0
            #self.flag_phase_cycle = 0
            self.N_IP = 0
            self.nid_pc_prev = 0

            if len(pulses) == 0:
                self.pulse_array_pulser = deepcopy(self.pulse_array_init_pulser)
                self.reset_count_pulser = 0
                self.increment_count_pulser = 0
                self.shift_count_pulser = 0
                self.current_phase_index_pulser = 0
            else:
                set_from_list = set(pulses)
                for element in set_from_list:
                    if element in self.pulse_name_array_pulser:
                        pulse_index = self.pulse_name_array_pulser.index(element)

                        self.pulse_array_pulser[pulse_index]['start'] = self.pulse_array_init_pulser[pulse_index]['start']
                        self.pulse_array_pulser[pulse_index]['length'] = self.pulse_array_init_pulser[pulse_index]['length']

                        self.reset_count_pulser = 0
                        self.increment_count_pulser = 0
                        self.shift_count_pulser = 0
                        self.current_phase_index_pulser = 0
        
    def pulser_visualize(self):
        """
        Function for visualization of pulse sequence.
        There are two possibilities:
        1) Real final instructions with already summed up channel numbers
        2) Individual pulses
        """
        if self.test_flag != 'test':
            rep_rate_pulser = self.rep_rate_pulser[0]
            if rep_rate_pulser[-3:] == ' Hz':
                rep_time = int(1000000000/float(rep_rate_pulser[:-3]))
            elif rep_rate_pulser[-3:] == 'kHz':
                rep_time = int(1000000/float(rep_rate_pulser[:-4]))
            elif rep_rate_pulser[-3:] == 'MHz':
                rep_time = int(1000/float(rep_rate_pulser[:-4]))

            rep_time = self.round_to_closest(rep_time, 3.2)

            # Real final instructions with already summed up channel numbers
            #preparation = self.split_into_parts_pulser( self.pulse_array_pulser, rep_time )
            #visualizer = self.convert_to_bit_pulse_visualizer_final_instructions( np.asarray(preparation[:-1] ))

            # Individual pulses
            visualizer = self.convert_to_bit_pulse_visualizer_pulser( self.pulse_array_pulser )

            #general.plot_1d('Plot XY Test', np.arange(len(to_spinapi)), to_spinapi, label='test data1', timeaxis = 'False')
            general.plot_2d('Pulse Visualizer', np.transpose( visualizer ), \
                start_step = ( (0, 1), (0, 1) ), xname = 'Time',\
                xscale = 'ns', yname = 'Pulse Number', yscale = '', zname = 'channel', zscale = '')

        elif self.test_flag == 'test':
            pass

    def pulser_pulse_list(self):
        """
        Function for saving a pulse list from 
        the script into the
        header of the experimental data
        """
        pulse_list_mod = ''
        for element in self.pulse_array_init_pulser:
            pulse_list_mod = pulse_list_mod + str(element) + '\n'

        return pulse_list_mod
    
    def pulser_clear(self):
        """
        A special function for Pulse Control module
        It clear self.pulse_array_pulser and other status flags
        """
        self.pulse_array_pulser = []
        self.phase_array_length_pulser = []
        self.pulse_name_array_pulser = []
        self.pulse_array_init_pulser = []
        self.rep_rate_pulser = (self.repetition_rate_pulser, )
        self.shift_count_pulser = 0
        self.rep_rate_count_pulser = 0
        self.increment_count_pulser = 0
        self.reset_count_pulser = 0
        self.current_phase_index_pulser = 0
        self.awg_pulses_pulser = 0
        self.phase_pulses_pulser = 0

    def pulser_test_flag(self, flag):
        """
        A special function for Pulse Control module
        It runs TEST mode
        """
        self.test_flag = flag

    def pulser_acquisition_cycle(self, data1, data2, points, phases, adc_window, acq_cycle = ['+x']):
        if self.test_flag != 'test':
            
            #self.nid_pc_prev                             - start
            #self.nid_prev - (self.nid_prev % phases)     - last completed

            k = 0
            l = 0

            #general.message(f'i / j / nores: {self.nid_pc_prev } / {self.nid_prev - (self.nid_prev % phases) } / {self.nid_pc_prev_no_reset}')

            i = self.nid_pc_prev 
            j = self.nid_prev - (self.nid_prev % phases)

            # LAST POINT:
            sh_points = int(points * phases)

            if (( int( j - i ) < 0 ) or ( self.nid_pc_prev_no_reset == int( sh_points - phases) )) and (i != 0):
                #general.message(i, j, self.nid_pc_prev_no_reset)
                i = 0
                j = sh_points
                k = 1

                if ( self.n_scans == 2) and (len(self.count_nip[self.nid_pc_prev_no_reset:sh_points] > phases)):
                    self.correction = int( self.ind_test[-1] + 1)
                    #general.message(f'E2: {self.count_nip[self.nid_pc_prev_no_reset:sh_points]}')
                    #general.message(self.ind_test)
                    self.m = 1

            if (( self.n_scans == 3 ) or ( ( self.n_scans == 2 ) and (j == int( sh_points - phases)) and (i != 0 ) )) and ( self.m == 1 ):
                for index, element in enumerate(self.count_nip[self.correction:sh_points]):
                    if element > 1:
                        self.count_nip[int(index + self.correction)] -= 1
                #general.message(f'E3: {self.count_nip[self.nid_pc_prev_no_reset:sh_points]}')
                self.m = 0

            if (j == int( sh_points - phases)) and (i != 0 ):
                j = sh_points

            counts_adc = int( adc_window * 8 / self.dec_coef )
            counts_adc_full = int( adc_window * 16 )
            points_to_cycle = int( j - i)
            points_to_cycle_ph = int( points_to_cycle//phases)

            data_for_cycling = self.data_raw[int(i*counts_adc_full):int(j*counts_adc_full)]

            data_i =  self.adc_sens * (data_for_cycling[0::(2*self.dec_coef)]).reshape( points_to_cycle, counts_adc, order = 'C'  ) / self.count_nip[i:j,None] / self.gimSum_brd / phases
            data_q =  self.adc_sens * (data_for_cycling[1::(2*self.dec_coef)]).reshape( points_to_cycle, counts_adc, order = 'C'  ) / self.count_nip[i:j,None] / self.gimSum_brd / phases

            #SCANS:
            if (i == 0) and (k == 0):
                self.n_scans += 1

            if self.flag_phase_cycle == 0:

                self.answer = np.zeros( ( int( sh_points / phases), counts_adc ), dtype = np.complex64 )
                self.flag_phase_cycle = 1

            #SCANS
            if self.n_scans > 1:
                self.answer[(i//phases):(j//phases),:] = np.zeros( ( points_to_cycle_ph, counts_adc ), dtype = np.complex64 )


            for index, element in enumerate(acq_cycle):
                if element == '+' or element == '+x':
                    self.answer[(i//phases):(j//phases),:] += (data_i)[index::phases] + 1j*(data_q)[index::phases]
                elif element == '-' or element == '-x':
                    self.answer[(i//phases):(j//phases),:] += -(data_i)[index::phases] - 1j*(data_q)[index::phases]
                elif element == '+i' or element == '+y':
                    self.answer[(i//phases):(j//phases),:] += 1j*(data_i)[index::phases] - (data_q)[index::phases]
                elif element == '-i' or element == '-y':
                    self.answer[(i//phases):(j//phases),:] += -1j*(data_i)[index::phases] + (data_q)[index::phases]

            ## NO LAST POINT IN SCANS
            if (i == 0) and (self.n_scans > 1) and (k == 0):
                i = self.nid_pc_prev_no_reset
                j = sh_points
                points_to_cycle = int( j - i)
                points_to_cycle_ph = int( points_to_cycle//phases)

                if (self.n_scans == 2):
                    #general.message(f'B: {self.count_nip[i:j]}')

                    for index, element in enumerate(self.count_nip[i:j]):
                        if element > 1:
                            
                            if self.count_nip[i] != 1:
                                l = 1
                            
                            self.count_nip[int(index + i)] -= 1
                            self.ind_test.append(int(index + i))
                            
                            ###
                            if l == 1:
                                if (self.count_nip[int(index + i)] == 1):# and (index) != 0:
                                    self.count_nip[int(index + i)] += 1
                            l = 0
                            ###

                    #general.message(f'A: {self.count_nip[i:j]}')

                data_for_cycling = self.data_raw[int(i*counts_adc_full):int(j*counts_adc_full)]
                data_i =  self.adc_sens * (data_for_cycling[0::(2*self.dec_coef)]).reshape( points_to_cycle, counts_adc, order = 'C' ) / self.count_nip[i:j,None] / self.gimSum_brd / phases
                data_q =  self.adc_sens * (data_for_cycling[1::(2*self.dec_coef)]).reshape( points_to_cycle, counts_adc, order = 'C' ) / self.count_nip[i:j,None] / self.gimSum_brd / phases
            
                if (self.n_scans - 1 ) > 1:
                    self.answer[(i//phases):(j//phases),:] = np.zeros( ( points_to_cycle_ph, counts_adc ), dtype = np.complex64 )

                for index, element in enumerate(acq_cycle):
                    if element == '+' or element == '+x':
                        self.answer[(i//phases):(j//phases),:] += (data_i)[index::phases] + 1j*(data_q)[index::phases]
                    elif element == '-' or element == '-x':
                        self.answer[(i//phases):(j//phases),:] += -(data_i)[index::phases] - 1j*(data_q)[index::phases]
                    elif element == '+i' or element == '+y':
                        self.answer[(i//phases):(j//phases),:] += 1j*(data_i)[index::phases] - (data_q)[index::phases]
                    elif element == '-i' or element == '-y':
                        self.answer[(i//phases):(j//phases),:] += -1j*(data_i)[index::phases] + (data_q)[index::phases]


            self.nid_pc_prev_no_reset = self.nid_prev - (self.nid_prev % phases)
            self.nid_pc_prev = self.nid_prev - (self.nid_prev % phases)

            k = 0

            return self.answer.real, self.answer.imag

        elif self.test_flag == 'test':

            phases = len(acq_cycle)

            if self.awg_pulses_pulser == 0:
                rect_p_phase = self.phase_array_length_pulser[0]
                if rect_p_phase == 0:
                    rect_p_phase = 1
                    assert( rect_p_phase == phases ), 'Acquisition cycle and number of phases of RECT MW pulses have incompatible size'
                    rect_p_phase = 0
                elif rect_p_phase != 0:
                    assert( rect_p_phase == phases ), 'Acquisition cycle and number of phases of RECT MW pulses have incompatible size'
            elif self.awg_pulses_pulser == 1:
                awg_p_phase = self.phase_array_length_0_awg[0]
                if awg_p_phase == 0:
                    awg_p_phase = 1
                    assert( awg_p_phase == phases ), 'Acquisition cycle and number of phases of AWG MW pulses have incompatible size'
                    awg_p_phase = 0
                elif awg_p_phase != 0:
                    assert( awg_p_phase == phases ), 'Acquisition cycle and number of phases of AWG MW pulses have incompatible size'

            counts_adc = int( adc_window * 8 / self.dec_coef )

            if self.flag_phase_cycle == 0:
            
                #self.answer = np.empty( ( int( data1.shape[0] / phases), data1.shape[1] ), dtype = np.complex64 )
                self.answer = np.zeros( (points, counts_adc ), dtype = np.int32 )
                self.flag_phase_cycle = 1

            #answer = np.zeros( ( int( data1.shape[0] / phases), data1.shape[1]  ), dtype = np.complex128 ) #+ 1j*np.zeros( ( int( data2.shape[0] / phases), data2.shape[1]  ) ) 
            
            #general.message(self.answer[0:600,:].shape)
            # This function is executed only once in the test mode:    
            #self.nid_pc_prev  - begin = 0
            #self.nid_prev     - end   = -1

            # SLOW
            #for index, element in enumerate(acq_cycle):
            #    if element == '+' or element == '+x':
            #        answer += data1[index::phases] + 1j*data2[index::phases]
            #    elif element == '-' or element == '-x':
            #        answer += -data1[index::phases] - 1j*data2[index::phases]
            #    elif element == '+i' or element == '+y':
            #        answer += 1j*data1[index::phases] - data2[index::phases]
            #    elif element == '-i' or element == '-y':
            #        answer += -1j*data1[index::phases] + data2[index::phases]

            #return (self.answer.real / len(acq_cycle)), (self.answer.imag / len(acq_cycle))
            return self.answer, self.answer

    def pulser_open(self):
        if self.test_flag != 'test':
            initRet                = self.initBrd() # Функция открывает плату для использования.

            setZeroGIMRet          = self.setZero_GIM()    #;print("setZero_GIM:"    ,setZeroGIMRet         ) # Функция зануляет регистр управления ГИМ.
            rstGIMRet              = self.rst_GIM()        #;print("rst_GIM:"        ,rstGIMRet             ) # функция выполняет сброс узла ГИМ.
                                                    #1
            setSync_GIMRet         = self.setSync_GIM( self.ext_trigger )   #;print("setSync_GIM:"    ,setSync_GIMRet        ) # Функция выставляет синхронный режим ГИМ (старт ГИМ от сетки стартов, старт ввода/вывода  от ГИМ).
            self.nDacChanNum_brd   = self.getDAC_ChanNum() #;print("getDAC_ChanNum:" ,self.nDacChanNum_brd  ) # Функция возвращает количество используемых каналов ЦАП (задается в exam_edac.ini)
            self.nStrmBufSizeb_brd = self.getStrmBufSizeb()#;print("getStrmBufSizeb:",self.nStrmBufSizeb_brd) # Функция возвращает размер буфера стрима в байтах.
            #general.message( self.nStrmBufSizeb_brd )
            self.brdDataBuf_brd    = (ctypes.c_int * self.nStrmBufSizeb_brd)()
            self.strmBufNum_brd    = self.getStreamBufNum()

            file_to_read = open(self.path_status_file, 'w')
            file_to_read.write('Status:  On' + '\n')
            file_to_read.close()

        elif self.test_flag == 'test':

            text = open( self.path_status_file ).read()
            lines = text.split('\n')
            assert( str( lines[0].split(':  ')[1] ) != 'On' ), "Insys FPGA card is already opened. Please, close it."

            file_to_read = open(self.path_status_file, 'w')
            file_to_read.write('Status:  On' + '\n')
            file_to_read.close()

    def pulser_close(self):
        if self.test_flag != 'test':
            
            #self.setEnable_GIM(0)
            closeRet = self.closeBrd()
            #general.message(f'CLOSE BOARD: {closeRet}')
            
            file_to_read = open(self.path_status_file, 'w')
            file_to_read.write('Status:  Off' + '\n')
            file_to_read.close()
            #general.message(self.count_nip[-4:])

        elif self.test_flag == 'test':
            
            file_to_read = open(self.path_status_file, 'w')
            file_to_read.write('Status:  Off' + '\n')
            file_to_read.close()

    def pulser_default_synt(self, num):
        """
        Function to change synthetizer for AWG channel of the ITC microwave bridge
        """
        if self.test_flag != 'test':
            self.synt_number = num
        elif self.test_flag == 'test':
            assert(num == 1 or num == 2), 'Incorrect synthetizer number'

    ####################ADC###############################
    def digitizer_name(self):
        answer = 'Insys 2.5 GHz 14 bit ADC'
        return answer

    def digitizer_get_curve(self, p, ph, live_mode = 0, integral = False, current_scan = 1, total_scan = 1):
        """
        p - points
        ph - phases
        """
        if self.test_flag != 'test':

            total_points = int(p * ph)
            adc_window = self.adc_window
            
            if (self.flag_adc_buffer == 0) and (live_mode == 0):
                self.data_raw = np.zeros( ( int(p * ph * adc_window * 16) ), dtype = np.int32 )
                self.count_nip = np.zeros( ( total_points ), dtype = np.int32 ) + 1
                self.flag_adc_buffer = 1

            elif (live_mode == 1):
                self.data_raw = np.zeros( ( int(p * ph * adc_window * 16) ), dtype = np.int32 )
                self.count_nip = np.zeros( ( total_points ), dtype = np.int32 ) + 1
                #self.flag_adc_buffer = 1

            #Функция проверки готовности буферов. Функция возвращает номер последнего записанного блока. Исходя из этого номера можно посчитать сколько блоков необходимо “забрать” 
            #strmBufNum = self.getStreamBufNum()
            #general.message(f"ADC Buffer Number: {strmBufNum}")


            if (self.nIP_No_brd != total_points) or ( (self.nIP_No_brd == total_points) and (current_scan != total_scan) ):

                BufCnt = self.AdcStreamGetBufState()
                self.nBufToClcNum_brd = BufCnt - self.nStrmBufTotalCnt_brd
                self.nBufToClcNum_brd = self.overflow_check(self.strmBufNum_brd, self.nBufToClcNum_brd, BufCnt, self.nStrmBufTotalCnt_brd)

                if (self.nBufToClcNum_brd > 0):
                    #general.message(f'BF_CNT: {self.nBufToClcNum_brd}')

                    for kk in range( self.nBufToClcNum_brd ):

                        self.AdcStreamGetBuf_buf( self.brdDataBuf_brd )
                        if self.flag_sum_brd == 1:

                            # в режиме с усреднениями 4 байта на отсчет
                            # 1.4 ms for 301 points, 2 phases, 20 averages, 400 Hz
                            data_raw, count_nip = self.gen_2d_array_from_buffer( np.frombuffer(self.brdDataBuf_brd, dtype = np.int32), adc_window, p, ph, live_mode)

                            i = self.nid_pc_prev
                            j = self.nid_prev - (self.nid_prev % ph)
                            
                            #general.message(f'GC i / j: {i} / {j}')

                            #self.data_raw = self.data_raw + data_raw
                            #self.count_nip = self.count_nip + count_nip
                            # 0.8 ms for 301 points, 2 phases, 20 averages, 400 Hz
                            #st_time = time.time()
                            if ( i == 0 ) or ( i > int( (p - 5) * ph) ):
                                #general.message(f'GC i / j: {i} / {j}')
                                self.data_raw += data_raw
                                self.count_nip += count_nip
                            elif j < int( (p - 5) * ph):
                                self.data_raw[int((i - ph) * adc_window * 16):int((j + ph) * adc_window * 16)] += data_raw[int((i - ph) * adc_window * 16):int((j + ph) * adc_window * 16)]
                                self.count_nip[int((i - ph)):int((j + ph))] += count_nip[int((i - ph)):int((j + ph))]
                            else:
                                self.data_raw += data_raw
                                self.count_nip += count_nip

                            #general.message(f'TIME: {round( 1000*(time.time() - st_time), 1)} ms')
                            
                            #general.message( np.nonzero(data_raw)[-1] )
                            #general.message( f'I: {int((i - ph) * adc_window * 16)}' )
                            #general.message( f'J: {int((j + ph) * adc_window * 16)}' )
                            
                            ###self.data_raw += data_raw
                            ###self.count_nip += count_nip

                    self.nStrmBufTotalCnt_brd = BufCnt

            elif (self.nIP_No_brd == total_points) and (live_mode == 0) and (current_scan == total_scan):
                #general.message(f'LAST: {self.nStrmBufTotalCnt_brd}')
                #general.message(f'LAST_IP: {self.N_IP}')
                while True:

                    BufCnt = self.AdcStreamGetBufState()
                    self.nBufToClcNum_brd = BufCnt - self.nStrmBufTotalCnt_brd
                    self.nBufToClcNum_brd = self.overflow_check(self.strmBufNum_brd, self.nBufToClcNum_brd, BufCnt, self.nStrmBufTotalCnt_brd)

                    if (self.nBufToClcNum_brd > 0):
                        for kk in range(self.nBufToClcNum_brd):
                            #general.message(f'BF_CNT: {self.nBufToClcNum_brd}')

                            self.AdcStreamGetBuf_buf( self.brdDataBuf_brd )
                            if self.flag_sum_brd == 1:
                                # в режиме с усреднениями 4 байта на отсчет
                                data_raw, count_nip = self.gen_2d_array_from_buffer( np.frombuffer(self.brdDataBuf_brd, dtype = np.int32), adc_window, p, ph, live_mode)

                                #self.data_raw = self.data_raw + data_raw
                                #self.count_nip = self.count_nip + count_nip
                                self.data_raw += data_raw
                                self.count_nip += count_nip

                        self.nStrmBufTotalCnt_brd = BufCnt
                    
                    # the case of 1 repetition of the last ID
                    if ((self.nIP_No_brd - 1) == self.N_IP) and (self.count_nip[-1] > 0):
                        #general.message(f'STOP: {self.nStrmBufTotalCnt_brd}')
                        #self.pulser_stop()
                        break

                        #elif (self.count_nip[-1] <= 0):
                        #    self.count_nip[-1] = 1

            elif (self.nIP_No_brd == total_points) and (live_mode == 1):
                #general.message(f'LAST: {self.nStrmBufTotalCnt_brd}')
                #general.message(f'LAST_IP: {self.N_IP}')

                BufCnt = self.AdcStreamGetBufState()
                self.nBufToClcNum_brd = BufCnt - self.nStrmBufTotalCnt_brd
                self.nBufToClcNum_brd = self.overflow_check(self.strmBufNum_brd, self.nBufToClcNum_brd, BufCnt, self.nStrmBufTotalCnt_brd)

                if (self.nBufToClcNum_brd > 0):
                    for kk in range(self.nBufToClcNum_brd):
                        #general.message(f'BF_CNT: {self.nBufToClcNum_brd}')

                        self.AdcStreamGetBuf_buf( self.brdDataBuf_brd )
                        if self.flag_sum_brd == 1:
                            # в режиме с усреднениями 4 байта на отсчет
                            data_raw, count_nip = self.gen_2d_array_from_buffer( np.frombuffer(self.brdDataBuf_brd, dtype = np.int32), adc_window, p, ph, live_mode)

                            #self.data_raw = self.data_raw + data_raw
                            #self.count_nip = self.count_nip + count_nip
                            self.data_raw += data_raw
                            self.count_nip += count_nip

                    self.nStrmBufTotalCnt_brd = BufCnt

            #data_i = self.adc_sens * self.data_raw[0::(2*self.dec_coef)]
            #data_q = self.adc_sens * self.data_raw[1::(2*self.dec_coef)]

            if self.buffer_ready == 1:
                #general.message(self.count_nip)
                #data_i = self.adc_sens * self.data_raw[0::(2*self.dec_coef)]
                #data_q = self.adc_sens * self.data_raw[1::(2*self.dec_coef)]

                if integral == False:
                    self.data_i_ph, self.data_q_ph = self.pulser_acquisition_cycle(1, 1, p, ph, adc_window, acq_cycle = self.detection_phase_list)
                    self.buffer_ready = 0
                    
                    #self.data_i_ph_T, self.data_q_ph_T = self.data_i_ph.T, self.data_q_ph.T
                    return self.data_i_ph.T, self.data_q_ph.T ###self.data_i_ph_T, self.data_q_ph_T#, self.count_nip #, self.buffer_ready + 1

                elif integral == True:
                    self.data_i_ph, self.data_q_ph = self.pulser_acquisition_cycle(1, 1, p, ph, adc_window, acq_cycle = self.detection_phase_list)
                    #self.data_i_ph, self.data_q_ph = self.pulser_acquisition_cycle(data_i.reshape(int(p * ph), int( adc_window * 8 / self.dec_coef  )) / self.count_nip[:,None] / self.gimSum_brd, data_q.reshape(int(p * ph), int( adc_window * 8 / self.dec_coef  )) / self.count_nip[:,None] / self.gimSum_brd, acq_cycle = self.detection_phase_list)
                    self.buffer_ready = 0
                    return 1 * 0.4 * self.dec_coef * np.sum( (self.data_i_ph)[:, self.win_left:self.win_right], axis = 1 ), 1 * 0.4 * self.dec_coef * np.sum( (self.data_q_ph)[:, self.win_left:self.win_right], axis = 1 )#, self.buffer_ready + 1

            elif self.buffer_ready == 0:
                if integral == False:
                    self.buffer_ready = 0
                    return None, None #, None#, 0
                    #return self.data_i_ph_T, self.data_q_ph_T, self.buffer_ready
  
                elif integral == True:
                    self.buffer_ready = 0
                    return None, None#, 0
                    #return np.sum( (self.data_i_ph).T[:, self.win_left:self.win_right], axis = 1 ), np.sum( (self.data_q_ph).T[:, self.win_left:self.win_right], axis = 1 ), self.buffer_ready

        elif self.test_flag == 'test':

            self.count_nip = np.ones( (int(p * ph)), dtype = np.int32 )
            #####
            rep_rate_pulser = self.rep_rate_pulser[0]
            if rep_rate_pulser[-3:] == ' Hz':
                rep_time = int(1000000000/float(rep_rate_pulser[:-3]))
            elif rep_rate_pulser[-3:] == 'kHz':
                rep_time = int(1000000/float(rep_rate_pulser[:-4]))
            elif rep_rate_pulser[-3:] == 'MHz':
                rep_time = int(1000/float(rep_rate_pulser[:-4]))

            rep_time = self.round_to_closest(rep_time, 3.2)
            min_time = 20
            ###assert( self.gimSum_brd * rep_time/ 1000000 > min_time ), f'Too low number of averages per phase.\nPlease increase number of avegares to { int(1000000 * min_time / rep_time ) + 1 }' 
            #####


            if self.awg_pulses_pulser == 0:
                rect_p_phase = self.phase_array_length_pulser[0]
                if rect_p_phase == 0:
                    rect_p_phase = 1
                    assert( rect_p_phase == ph ), 'Number of phases and number of phases of RECT MW pulses have incompatible size'
                    rect_p_phase = 0
                elif rect_p_phase != 0:
                    assert( rect_p_phase == ph ), 'Number of phases and number of phases of RECT MW pulses have incompatible size'
            elif self.awg_pulses_pulser == 1:
                awg_p_phase = self.phase_array_length_0_awg[0]
                if awg_p_phase == 0:
                    awg_p_phase = 1
                    assert( awg_p_phase == ph ), 'Number of phases and number of phases of AWG MW pulses have incompatible size'
                    awg_p_phase = 0
                elif awg_p_phase != 0:
                    assert( awg_p_phase == ph ), 'Number of phases and number of phases of AWG MW pulses have incompatible size'

            adc_window = self.adc_window
            #self.data_raw = np.zeros( ( int(p * ph) * int( adc_window * 16) ) )
            #self.count_nip = np.ones( (int(p * ph) * 1) )
            #data_i = self.adc_sens * self.data_raw[0::(2*self.dec_coef)]
            #data_q = self.adc_sens * self.data_raw[1::(2*self.dec_coef)]

            if self.buffer_ready == 1:
                if integral == False:
                    self.data_i_ph, self.data_q_ph = self.pulser_acquisition_cycle(1, 1, p, ph, adc_window, acq_cycle = self.detection_phase_list)
                    #self.data_i_ph, self.data_q_ph = self.pulser_acquisition_cycle(np.zeros( ( int(p * ph), int( adc_window * 8 / self.dec_coef  ) ) ), np.zeros( ( int(p * ph), int( adc_window * 8 / self.dec_coef  ) ) ), p, ph, adc_window, acq_cycle = self.detection_phase_list)

                    self.buffer_ready = 0
                    return self.data_i_ph.T, self.data_q_ph.T #, None#, self.buffer_ready + 1
                elif integral == True:
                    self.data_i_ph, self.data_q_ph = self.pulser_acquisition_cycle(1, 1, p, ph, adc_window, acq_cycle = self.detection_phase_list)
                    #self.data_i_ph, self.data_q_ph = self.pulser_acquisition_cycle(np.zeros( ( int(p * ph), int( adc_window * 8 / self.dec_coef  ) ) ), np.zeros( ( int(p * ph), int( adc_window * 8 / self.dec_coef ) ) ), p, ph, adc_window, acq_cycle = self.detection_phase_list)
                    #general.message( len(np.sum( ((self.data_i_ph))[:, self.win_left:self.win_right], axis = 1 )) )
                    self.buffer_ready = 0
                    return  1 * 0.4 * self.dec_coef * np.sum( (self.data_i_ph)[:, self.win_left:self.win_right], axis = 1 ),  1 * 0.4 * self.dec_coef * np.sum( (self.data_q_ph)[:, self.win_left:self.win_right], axis = 1 )#, self.buffer_ready + 1

            elif self.buffer_ready == 0:
                if integral == False:
                    self.buffer_ready = 0
                    #return self.data_i_ph_T, self.data_q_ph_T, self.buffer_ready
                    return None, None #, None#, 0
                elif integral == True:
                    self.buffer_ready = 0
                    #return np.sum( (self.data_i_ph).T[:, self.win_left:self.win_right], axis = 1 ), np.sum( (self.data_q_ph).T[:, self.win_left:self.win_right], axis = 1 ), self.buffer_ready
                    return None, None#, 0

    def digitizer_get_curve2(self, p, ph, live_mode = 0, integral = False, current_scan = 1, total_scan = 1):
        """
        p - points
        ph - phases
        """
        if self.test_flag != 'test':
            adc_window = self.adc_window
            total_points = int(p * ph)

            if (self.flag_adc_buffer == 0) and (live_mode == 0):

                self.data_raw = np.zeros( ( int(p * ph * adc_window * 16) ), dtype = np.int32 )
                self.count_nip = np.ones( (int(p * ph)), dtype = np.int32 )
                self.flag_adc_buffer = 1
            elif (live_mode == 1):
                self.data_raw = np.zeros( ( int(p * ph * adc_window * 16) ), dtype = np.int32 )
                self.count_nip = np.ones( (int(p * ph)), dtype = np.int32 )
                #self.flag_adc_buffer = 1

            #Функция проверки готовности буферов. Функция возвращает номер последнего записанного блока. Исходя из этого номера можно посчитать сколько блоков необходимо “забрать” 
            #strmBufNum = self.getStreamBufNum()
            #general.message(f"ADC Buffer Number: {strmBufNum}")

            if (self.nIP_No_brd != total_points) or ( (self.nIP_No_brd == total_points) and (current_scan != total_scan) ):

                BufCnt = self.AdcStreamGetBufState()
                self.nBufToClcNum_brd = BufCnt - self.nStrmBufTotalCnt_brd
                self.nBufToClcNum_brd = self.overflow_check(self.strmBufNum_brd, self.nBufToClcNum_brd, BufCnt, self.nStrmBufTotalCnt_brd)

                if (self.nBufToClcNum_brd > 0):
                    #general.message(f'BF_CNT: {self.nBufToClcNum_brd}')

                    for kk in range( self.nBufToClcNum_brd ):

                        self.AdcStreamGetBuf_buf( self.brdDataBuf_brd )
                        if self.flag_sum_brd == 1:

                            # в режиме с усреднениями 4 байта на отсчет
                            data_raw, count_nip = self.gen_2d_array_from_buffer2( np.frombuffer(self.brdDataBuf_brd, dtype = np.int32), adc_window, p, ph, live_mode)

                            i = self.nid_pc_prev
                            j = self.nid_prev - (self.nid_prev % ph)
                            
                            #self.data_raw += data_raw
                            #self.count_nip += count_nip

                            if ( i == 0 ) or ( i > int( (p - 5) * ph) ):
                                self.data_raw += data_raw
                                self.count_nip += count_nip
                            elif j < int( (p - 5) * ph):
                                self.data_raw[int((i - ph) * adc_window * 16):int((j + ph) * adc_window * 16)] += data_raw[int((i - ph) * adc_window * 16):int((j + ph) * adc_window * 16)]
                                self.count_nip[int((i - ph)):int((j + ph))] += count_nip[int((i - ph)):int((j + ph))]
                            else:
                                self.data_raw += data_raw
                                self.count_nip += count_nip


                    self.nStrmBufTotalCnt_brd = BufCnt

            elif (self.nIP_No_brd == total_points) and (live_mode == 0) and (current_scan == total_scan):
                #general.message(f'LAST: {self.nStrmBufTotalCnt_brd}')
                #general.message(f'LAST_IP: {self.N_IP}')
                while True:

                    BufCnt = self.AdcStreamGetBufState()
                    self.nBufToClcNum_brd = BufCnt - self.nStrmBufTotalCnt_brd
                    self.nBufToClcNum_brd = self.overflow_check(self.strmBufNum_brd, self.nBufToClcNum_brd, BufCnt, self.nStrmBufTotalCnt_brd)

                    if (self.nBufToClcNum_brd > 0):
                        for kk in range(self.nBufToClcNum_brd):
                            #general.message(f'BF_CNT: {self.nBufToClcNum_brd}')

                            self.AdcStreamGetBuf_buf( self.brdDataBuf_brd )
                            if self.flag_sum_brd == 1:
                                # в режиме с усреднениями 4 байта на отсчет
                                data_raw, count_nip = self.gen_2d_array_from_buffer2( np.frombuffer(self.brdDataBuf_brd, dtype = np.int32), adc_window, p, ph, live_mode)

                                #self.data_raw = self.data_raw + data_raw
                                #self.count_nip = self.count_nip + count_nip
                                self.data_raw += data_raw
                                self.count_nip += count_nip

                        self.nStrmBufTotalCnt_brd = BufCnt
                    
                    # the case of 1 repetition of the last ID
                    if ((self.nIP_No_brd - 1) == self.N_IP) and (self.count_nip[-1] > 0):
                        #general.message(f'STOP: {self.nStrmBufTotalCnt_brd}')
                        #self.pulser_stop()
                        break

                        #elif (self.count_nip[-1] <= 0):
                        #    self.count_nip[-1] = 1

            elif (self.nIP_No_brd == total_points) and (live_mode == 1):
                #general.message(f'LAST: {self.nStrmBufTotalCnt_brd}')
                #general.message(f'LAST_IP: {self.N_IP}')

                BufCnt = self.AdcStreamGetBufState()
                self.nBufToClcNum_brd = BufCnt - self.nStrmBufTotalCnt_brd
                self.nBufToClcNum_brd = self.overflow_check(self.strmBufNum_brd, self.nBufToClcNum_brd, BufCnt, self.nStrmBufTotalCnt_brd)

                if (self.nBufToClcNum_brd > 0):
                    for kk in range(self.nBufToClcNum_brd):
                        #general.message(f'BF_CNT: {self.nBufToClcNum_brd}')

                        self.AdcStreamGetBuf_buf( self.brdDataBuf_brd )
                        if self.flag_sum_brd == 1:
                            # в режиме с усреднениями 4 байта на отсчет
                            data_raw, count_nip = self.gen_2d_array_from_buffer2( np.frombuffer(self.brdDataBuf_brd, dtype = np.int32), adc_window, p, ph, live_mode)

                            #self.data_raw = self.data_raw + data_raw
                            #self.count_nip = self.count_nip + count_nip
                            self.data_raw += data_raw
                            self.count_nip += count_nip

                    self.nStrmBufTotalCnt_brd = BufCnt

            #data_i = self.adc_sens * self.data_raw[0::(2*self.dec_coef)]
            #data_q = self.adc_sens * self.data_raw[1::(2*self.dec_coef)]

            if self.buffer_ready == 1:
                #data_i = self.adc_sens * self.data_raw[0::(2*self.dec_coef)]
                #data_q = self.adc_sens * self.data_raw[1::(2*self.dec_coef)]
                
                #general.message(self.count_nip)
                if integral == False:
                    self.data_i_ph, self.data_q_ph = self.pulser_acquisition_cycle(1, 1, p, ph, adc_window, acq_cycle = self.detection_phase_list)

                    self.buffer_ready = 0
                    return self.data_i_ph.T, self.data_q_ph.T ##self.data_i_ph_T, self.data_q_ph_T#, self.count_nip #, self.buffer_ready + 1
                elif integral == True:
                    #self.data_i_ph, self.data_q_ph = self.pulser_acquisition_cycle(data_i.reshape(int(p * ph), int( adc_window * 8 / self.dec_coef  )) / self.count_nip[:,None] / self.gimSum_brd, data_q.reshape(int(p * ph), int( adc_window * 8 / self.dec_coef  )) / self.count_nip[:,None] / self.gimSum_brd, acq_cycle = self.detection_phase_list)
                    self.data_i_ph, self.data_q_ph = self.pulser_acquisition_cycle(1, 1, p, ph, adc_window, acq_cycle = self.detection_phase_list)
                    self.buffer_ready = 0
                    return 1 * 0.4 * self.dec_coef * np.sum( (self.data_i_ph)[:, self.win_left:self.win_right], axis = 1 ), 1 * 0.4 * self.dec_coef * np.sum( (self.data_q_ph)[:, self.win_left:self.win_right], axis = 1 )#, self.buffer_ready + 1

            elif self.buffer_ready == 0:
                if integral == False:
                    self.buffer_ready = 0
                    return None, None #, None#, 0
                    #return self.data_i_ph_T, self.data_q_ph_T, self.buffer_ready
  
                elif integral == True:
                    self.buffer_ready = 0
                    return None, None#, 0
                    #return np.sum( (self.data_i_ph).T[:, self.win_left:self.win_right], axis = 1 ), np.sum( (self.data_q_ph).T[:, self.win_left:self.win_right], axis = 1 ), self.buffer_ready

        elif self.test_flag == 'test':

            self.count_nip = np.ones( (int(p * ph)), dtype = np.int32 )
            acq_cycle = self.detection_phase_list

            #####
            rep_rate_pulser = self.rep_rate_pulser[0]
            if rep_rate_pulser[-3:] == ' Hz':
                rep_time = int(1000000000/float(rep_rate_pulser[:-3]))
            elif rep_rate_pulser[-3:] == 'kHz':
                rep_time = int(1000000/float(rep_rate_pulser[:-4]))
            elif rep_rate_pulser[-3:] == 'MHz':
                rep_time = int(1000/float(rep_rate_pulser[:-4]))

            rep_time = self.round_to_closest(rep_time, 3.2)
            ##assert( self.gimSum_brd * rep_time/ 1000000 > 25 ), f'Too low number of averages per phase.\nPlease increase number of avegares to { int(1000000 * 25 / rep_time ) + 1 }' 
            #####


            if self.awg_pulses_pulser == 0:
                rect_p_phase = self.phase_array_length_pulser[0]
                if rect_p_phase == 0:
                    rect_p_phase = 1
                    assert( rect_p_phase == ph ), 'Number of phases and number of phases of RECT MW pulses have incompatible size'
                    rect_p_phase = 0
                elif rect_p_phase != 0:
                    assert( rect_p_phase == ph ), 'Number of phases and number of phases of RECT MW pulses have incompatible size'
            elif self.awg_pulses_pulser == 1:
                awg_p_phase = self.phase_array_length_0_awg[0]
                if awg_p_phase == 0:
                    awg_p_phase = 1
                    assert( awg_p_phase == ph ), 'Number of phases and number of phases of AWG MW pulses have incompatible size'
                    awg_p_phase = 0
                elif awg_p_phase != 0:
                    assert( awg_p_phase == ph ), 'Number of phases and number of phases of AWG MW pulses have incompatible size'

            adc_window = self.adc_window
            #self.data_raw = np.zeros( ( int(p * ph) * int( adc_window * 16) ) )
            #self.count_nip = np.ones( (int(p * ph) * 1) )
            #data_i = self.adc_sens * self.data_raw[0::(2*self.dec_coef)]
            #data_q = self.adc_sens * self.data_raw[1::(2*self.dec_coef)]

            if self.buffer_ready == 1:
                if integral == False:
                    #self.data_i_ph, self.data_q_ph = self.pulser_acquisition_cycle(data_i.reshape(int(p * ph), int( adc_window * 8 / self.dec_coef )) / self.count_nip[:,None] / self.gimSum_brd, data_q.reshape(int(p * ph), int( adc_window * 8 / self.dec_coef )) / self.count_nip[:,None] / self.gimSum_brd, acq_cycle = acq_cycle)
                    #self.data_i_ph, self.data_q_ph = self.pulser_acquisition_cycle(np.empty( ( int(p * ph), int( adc_window * 8 / self.dec_coef  ) ) ), np.empty( ( int(p * ph), int( adc_window * 8 / self.dec_coef  ) ) ), acq_cycle = self.detection_phase_list)
                    self.data_i_ph, self.data_q_ph = self.pulser_acquisition_cycle(1, 1, p, ph, adc_window, acq_cycle = self.detection_phase_list)
                    self.buffer_ready = 0
                    return self.data_i_ph.T, self.data_q_ph.T #, None#, self.buffer_ready + 1
                elif integral == True:
                    #self.data_i_ph, self.data_q_ph = self.pulser_acquisition_cycle(np.empty( ( int(p * ph), int( adc_window * 8 / self.dec_coef  ) ) ), np.empty( ( int(p * ph), int( adc_window * 8 / self.dec_coef ) ) ), acq_cycle = self.detection_phase_list)
                    #general.message( len(np.sum( ((self.data_i_ph))[:, self.win_left:self.win_right], axis = 1 )) )
                    self.data_i_ph, self.data_q_ph = self.pulser_acquisition_cycle(1, 1, p, ph, adc_window, acq_cycle = self.detection_phase_list)
                    self.buffer_ready = 0
                    return  1 * 0.4 * self.dec_coef * np.sum( (self.data_i_ph)[:, self.win_left:self.win_right], axis = 1 ),  1 * 0.4 * self.dec_coef * np.sum( (self.data_q_ph)[:, self.win_left:self.win_right], axis = 1 )#, self.buffer_ready + 1

            elif self.buffer_ready == 0:
                if integral == False:
                    self.buffer_ready = 0
                    #return self.data_i_ph_T, self.data_q_ph_T, self.buffer_ready
                    return None, None #, None#, 0
                elif integral == True:
                    self.buffer_ready = 0
                    #return np.sum( (self.data_i_ph).T[:, self.win_left:self.win_right], axis = 1 ), np.sum( (self.data_q_ph).T[:, self.win_left:self.win_right], axis = 1 ), self.buffer_ready
                    return None, None#, 0

    def digitizer_number_of_averages(self, *averages):
        """
        Set or query number of averages;
        Input: digitizer_number_of_averages(10); Number of averages from 1 to 10000; 0 is infinite averages
        Default: 2;
        Output: '100'
        """
        if self.test_flag != 'test':
            #self.setting_change_count = 1

            if len(averages) == 1:
                ave = int(averages[0])
                self.gimSum_brd = ave
            elif len(averages) == 0:
                return self.gimSum_brd

            # to update on-the-fly
            #if self.state == 0:
            #    pass
            #elif self.state == 1:

            #    # change card mode and memory
            #    if self.card_mode == 2:
            #        spcm_dwSetParam_i32(self.hCard, SPC_MEMSIZE, int( self.points * self.aver ) )
            #        #spcm_dwSetParam_i32(self.hCard, SPC_SEGMENTSIZE, self.points )

            #    # correct buffer size
            #    if self.channel == 1 or self.channel == 2:
                
            #        if self.card_mode == 2:
            #            self.qwBufferSize = uint64 (int( self.points * self.aver ) * 1 * 1)

            #    elif self.channel == 3:

            #        if self.card_mode == 2:
            #            self.qwBufferSize = uint64 (int( self.points * self.aver ) * 1 * 2)

            #    spcm_dwSetParam_i32 (self.hCard, SPC_M2CMD, M2CMD_CARD_WRITESETUP)

        elif self.test_flag == 'test':
            #self.setting_change_count = 1

            if len(averages) == 1:
                ave = int(averages[0])
                assert( ave >= 1 and ave <= 10000 ), "Incorrect number of averages; Should be 1 <= Averages <= 10000"
                self.gimSum_brd = ave

            elif len(aver) == 0:
                return self.gimSum_brd     
            else:
                assert( 1 == 2 ), 'Incorrect argument'

    def digitizer_window(self):
        """
        Special function for reading integration window
        """
        return ( self.win_right - self.win_left ) * 1000 / self.sample_rate

    def digitizer_decimation(self, *dec):
        """
        Special function for decimation
        """
        if self.test_flag != 'test':
            if  len(dec) == 1:
                self.dec_coef = int(dec[0])
            elif len(dec) == 0:
                return self.dec_coef

        elif self.test_flag == 'test':
            if  len(dec) == 1:
                assert ( (int(dec[0]) > 0) and ( int(dec[0]) <= 4 ) ), "Incorrect decimation coefficient. Should be 1-4"
                self.dec_coef = int(dec[0])
            elif len(dec) == 0:
                return self.dec_coef

    def digitizer_read_settings(self):
        """
        Special function for reading settings of the digitizer from the special file
        """
        if self.test_flag != 'test':

            path_to_main = os.path.abspath( os.getcwd() )
            path_file = os.path.join(path_to_main, '..', 'atomize/control_center/digitizer_insys.param')
            #path_file = os.path.join(path_to_main, 'digitizer_insys.param')
            file_to_read = open(path_file, 'r')

            text_from_file = file_to_read.read().split('\n')
            # ['Points: 224', 'Sample Rate: 250', 'Posstriger: 16', 'Range: 500', 'CH0 Offset: 0', 'CH1 Offset: 0', 
            # 'Window Left: 0', 'Window Right: 0', '']

            points = str( text_from_file[0].split(': ')[1] )
            self.points =round( float(points.split(' ')[0]), 1)
            #self.digitizer_number_of_points( points )

            #self.sample_rate = int( text_from_file[1].split(' ')[2] )
            #self.digitizer_sample_rate( sample_rate )

            #self.posttrig_points = int( text_from_file[2].split(' ')[1] )
            #self.digitizer_posttrigger( posttrigger )

            #self.amplitude_0 = int( text_from_file[3].split(' ')[1] )
            #self.amplitude_1 = int( text_from_file[3].split(' ')[1] )
            #self.digitizer_amplitude( amplitude )

            #self.offset_0 = int( text_from_file[4].split(' ')[2] )
            #self.offset_1 = int( text_from_file[5].split(' ')[2] )
            #self.digitizer_offset('CH0', ch0_offset, 'CH1', ch1_offset)

            self.win_left = int( text_from_file[6].split(' ')[2] )
            self.win_right = 1 + int( text_from_file[7].split(' ')[2] )

            self.dec_coef = int( text_from_file[8].split(' ')[1] )
            #self.digitizer_setup()
            return self.points

        elif self.test_flag == 'test':
            
            #self.digitizer_card_mode('Average')
            #self.digitizer_clock_mode('External')
            #self.digitizer_reference_clock(100)
            
            path_to_main = os.path.abspath( os.getcwd() )
            path_file = os.path.join(path_to_main, '..', 'atomize/control_center/digitizer_insys.param')
            #path_file = os.path.join(path_to_main, 'digitizer_insys.param')
            file_to_read = open(path_file, 'r')

            text_from_file = file_to_read.read().split('\n')
            # ['Points: 224', 'Sample Rate: 250', 'Posstriger: 16', 'Range: 500', 'CH0 Offset: 0', 'CH1 Offset: 0', 
            # 'Window Left: 0', 'Window Right: 0', '']
            points = str( text_from_file[0].split(': ')[1] )

            self.points = round( float(points.split(' ')[0]), 1)
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

            self.dec_coef = int( text_from_file[8].split(' ')[1] )
            return self.points

    def digitizer_sample_rate(self):
        """
        Set or query sample rate;
        Input: digitizer_sample_rate('500'); Sample rate is in MHz
        Default: '2500';
        Output: '2500 MHz'
        """
        if self.test_flag != 'test':
            return f'{int( self.sample_rate_adc / self.dec_coef )} MHz'

        elif self.test_flag == 'test':
            return self.test_sample_rate

    ####################DAC#######################
    def awg_name(self):
        answer = 'Insys 1.25 GHz 16 bit DAC'
        return answer

    def awg_update(self):
        """
        Start AWG card. No argument; No output
        Default settings:
        Sample clock is 1250 MHz; Clock mode is 'Internal'; Reference clock is 100 MHz; Card mode is 'Single';
        Trigger channel is 'External'; Trigger mode is 'Positive'; Loop is infinity; Trigger delay is 0;
        Enabled channels is CH0 and CH1; Amplitude of CH0 is '600 mV'; Amplitude of CH1 is '533 mV';
        Number of segments is 1; Card memory size is 64 samples;
        """
        if self.test_flag != 'test':

            if self.reset_count_awg == 0 or self.shift_count_awg == 1 or self.increment_count_awg == 1 or self.setting_change_count_awg == 1:

                self.update_counter_awg += 1
                self.channel_1 , self.channel_2 = self.define_buffer_single_joined_awg()

                self.shift_count_pulser = 1
                

                self.reset_count_awg = 1
                self.shift_count_awg = 0
                self.increment_count_awg = 0
                self.setting_change_count_awg = 0

            else:
                pass

        elif self.test_flag == 'test':
            # to run several important checks
            if self.reset_count_awg == 0 or self.shift_count_awg == 1 or self.increment_count_awg == 1 or self.setting_change_count_awg == 1:

                self.update_counter_awg += 1
                self.channel_1 , self.channel_2 = self.define_buffer_single_joined_awg()

                self.shift_count_pulser = 1


                self.reset_count_awg = 1
                self.shift_count_awg = 0
                self.increment_count_awg = 0
                self.setting_change_count_awg = 0

            else:
                pass
    
    def awg_pulse(self, name = 'P0', channel = 'CH0', func = 'SINE', frequency = '200 MHz', phase = 0, delta_phase = 0, phase_list = [], length = '16 ns', sigma = '0 ns', length_increment = '0 ns', start = '0 ns', delta_start = '0 ns', amplitude = 100, n = 1, b = 0.02):
        """
        A function for awg pulse creation;
        The possible arguments:
        NAME,
        CHANNEL (CHO, CH1), FUNC (SINE, GAUSS, SINC, BLANK, WURST, SECH/TANH), 
        FREQUENCY (1 - 280 MHz), for WURST frequency is a tuple: (center_freq, sweep_freq)
        PHASE (in rad),
        DELTA_PHASE (in rad), phase 1000 means random phase
        PHASE_LIST in ['+x', '-x', '+y', '-y'] 
        LENGTH (in ns, us; should be longer than sigma; minimun is 10 ns; maximum is 1900 ns), 
        SIGMA (sigma for gauss; sinc (length = 32 ns, sigma = 16 ns means +-2pi); sine for uniformity )
        INCREMENT (in ns, us, ms; for incrementing both sigma and length)
        START (in ns, us, ms; for joined pulses in 'Single mode')
        DELTA_START (in ns, us, ms; for joined pulses in 'Single mode')
        AMPLITUDE (in %; additional coefficient to adjust pulse amplitudes)
        N (in arb u); special coefficient for WURST and SECH/TANH pulse determining the steepness of the amplitude function
        b (in ns^-1); special coefficient for SECH/TANH pulse determining the truncation parameter

        Buffer according to arguments will be filled after
        """
        d_coef = 100 / amplitude

        if self.test_flag != 'test':
            pulse = {'name': name, 'channel': channel, 'function': func, 'frequency': frequency, 'phase' : phase, 'delta_phase': delta_phase, 'length': length, 'sigma': sigma, 'length_increment': length_increment, 'start': start, 'delta_start': delta_start, 'amp': d_coef, 'phase_list': phase_list, 'n': n, 'b': b }

            # length
            temp_length = length.split(" ")
            if temp_length[1] in self.timebase_dict:
                coef = self.timebase_dict[temp_length[1]]
                p_length_raw = coef*float(temp_length[0])

                p_length = self.round_to_closest(p_length_raw, 3.2)
                if p_length != p_length_raw:
                    general.message(f"Pulse length is not divisible by 3.2. The closest available Pulse length of {p_length} is used")

                pulse['length'] = str(p_length) + ' ns'

            # sigma
            temp_sigma = sigma.split(" ")
            if temp_sigma[1] in self.timebase_dict:
                coef = self.timebase_dict[temp_sigma[1]]
                p_sigma_raw = coef*float(temp_sigma[0])

                p_sigma = self.round_to_closest(p_sigma_raw, 3.2)
                if p_sigma != p_sigma_raw:
                    general.message(f"Pulse sigma is not divisible by 3.2. The closest available Pulse sigma of {p_sigma} is used")

                pulse['sigma'] = str(p_sigma) + ' ns'

            # increment
            temp_increment = length_increment.split(" ")
            if temp_increment[1] in self.timebase_dict:
                coef = self.timebase_dict[temp_increment[1]]
                p_increment_raw = coef*float(temp_increment[0])
                p_increment = self.round_to_closest(p_increment_raw, 3.2)
                if p_increment != p_increment_raw:
                    general.message(f"Pulse increment is not divisible by 3.2. The closest available Pulse increment of {p_increment} ns is used")

                pulse['length_increment'] = str(p_increment) + ' ns'

            # start
            temp_start = start.split(" ")
            if temp_start[1] in self.timebase_dict:
                coef = self.timebase_dict[temp_start[1]]
                p_start_raw = coef*float(temp_start[0])
                p_start = self.round_to_closest(p_start_raw, 3.2)
                if p_start != p_start_raw:
                    general.message(f"Pulse start is not divisible by 3.2. The closest available Pulse start of {p_start} ns is used")

                pulse['start'] = str(p_start) + ' ns'

            # delta_start
            temp_delta_start = delta_start.split(" ")
            if temp_delta_start[1] in self.timebase_dict:
                coef = self.timebase_dict[temp_delta_start[1]]
                p_delta_start_raw = coef*float(temp_delta_start[0])
                p_delta_start = self.round_to_closest(p_delta_start_raw, 3.2)
                if p_delta_start != p_delta_start_raw:
                    general.message(f"Pulse delta start is not divisible by 3.2. The closest available Pulse delta start of {p_delta_start} ns is used")

                pulse['delta_start'] = str(p_delta_start) + ' ns'

            self.pulse_array_awg.append( pulse )
            # for saving the initial pulse_array without increments
            # deepcopy helps to create a TRULY NEW array and not a link to the object
            self.pulse_array_init_awg = deepcopy( self.pulse_array_awg )
            # pulse_name array
            self.pulse_name_array_awg.append( pulse['name'] )

            # For Single/Multi mode checking
            # Only one pulse per channel for Single
            # Number of segments equals to number of pulses for each channel
            if channel == 'CH0':
                self.pulse_ch0_array_awg.append( pulse['name'] )
                # phase_list's length
                self.phase_array_length_0_awg.append(len(list(phase_list)))
            
        elif self.test_flag == 'test':
            pulse = {'name': name, 'channel': channel, 'function': func, 'frequency': frequency, 'phase' : phase, 'delta_phase' : delta_phase, 'length': length, 'sigma': sigma, 'length_increment': length_increment, 'start': start, 'delta_start': delta_start, 'amp': d_coef, 'phase_list': phase_list, 'n': n, 'b': b }

            if channel == 'CH0':
                # phase_list's length
                self.phase_array_length_0_awg.append(len(list(phase_list)))
            else:
                assert (1 == 2), 'Incorrect channel is given. Only CH0 is available'

            # Checks
            # two equal names
            temp_name = str(name)
            set_from_list = set(self.pulse_name_array_awg)
            if temp_name in set_from_list:
                assert (1 == 2), 'Two pulses have the same name. Please, rename'

            self.pulse_name_array_awg.append( pulse['name'] )

            # channels
            temp_ch = str(channel)
            assert (temp_ch in self.channel_dict_awg), 'Incorrect channel. Only CH0 or CH1 are available'

            # for Single/Multi mode checking
            if channel == 'CH0':
                self.pulse_ch0_array_awg.append( pulse['name'] )
            elif channel == 'CH1':
                self.pulse_ch1_array_awg.append( pulse['name'] )

            # Function type
            temp_func = str(func)
            assert (temp_func in self.function_dict_awg), 'Incorrect pulse type. Only SINE, GAUSS, SINC, BLANK, WURST, and SECH/TANH pulses are available'
            if temp_func == 'WURST' or temp_func == 'TEST2' or temp_func == 'SECH/TANH':
                assert ( len(frequency) == 2 ), 'For WURST and SECH/TANH pulses frequency should be a tuple: frequency = ("Center MHz", "Sweep MHz")'

            # Frequency
            if temp_func != 'WURST' and temp_func != 'TEST2' and temp_func != 'SECH/TANH':
                temp_freq = frequency.split(" ")
                coef = temp_freq[1]
                p_freq = float(temp_freq[0])
                assert (coef == 'MHz'), 'Incorrect frequency dimension. Only MHz is possible'
                assert(p_freq >= self.min_freq_awg), 'Frequency is lower than minimum available (' + str(self.min_freq_awg) +' MHz)'
                assert(p_freq < self.max_freq_awg), 'Frequency is longer than minimum available (' + str(self.max_freq_awg) +' MHz)'
            else:
                temp_freq_st = frequency[0].split(" ")
                temp_freq_end = frequency[1].split(" ")
                coef_st = temp_freq_st[1]
                coef_end = temp_freq_end[1]
                p_freq_st = float(temp_freq_st[0])
                p_freq_end = float(temp_freq_end[0])
                assert (coef_st == 'MHz' and coef_end == 'MHz'), 'Incorrect frequency dimension. Only MHz is possible'
                assert(p_freq_st >= self.min_freq_awg and p_freq_end >= self.min_freq_awg), 'Frequency is lower than minimum available (' + str(self.min_freq_awg) +' MHz)'
                assert(p_freq_st < self.max_freq_awg and p_freq_end < self.max_freq_awg), 'Frequency is longer than minimum available (' + str(self.max_freq_awg) +' MHz)'
                #assert(p_freq_end > p_freq_st), 'End frequency in WURST pulse should be higher than start frequency)'

            # length
            temp_length = length.split(" ")
            if temp_length[1] in self.timebase_dict:
                coef = self.timebase_dict[temp_length[1]]
                p_length_raw = coef*float(temp_length[0])

                p_length = self.round_to_closest(p_length_raw, 3.2)
                if p_length != p_length_raw:
                    general.message(f"Pulse length is not divisible by 3.2. The closest available Pulse length of {p_length} is used")

                pulse['length'] = str(p_length) + ' ns'
                assert( round(remainder(p_length, 3.2), 2) == 0), 'Pulse length should be divisible by 3.2'

                assert(p_length >= self.min_pulse_length_awg), 'Pulse is shorter than minimum available length (' + str(self.min_pulse_length_awg) +' ns)'
                assert(p_length < self.max_pulse_length_awg), 'Pulse is longer than maximum available length (' + str(self.max_pulse_length_awg) +' ns)'
            else:
                assert( 1 == 2 ), 'Incorrect time dimension (ms, us, ns)'

            # sigma
            temp_sigma = sigma.split(" ")
            if temp_sigma[1] in self.timebase_dict:
                coef = self.timebase_dict[temp_sigma[1]]
                p_sigma_raw = coef*float(temp_sigma[0])

                p_sigma = self.round_to_closest(p_sigma_raw, 3.2)
                if p_sigma != p_sigma_raw:
                    general.message(f"Pulse sigma is not divisible by 3.2. The closest available Pulse sigma of {p_sigma} is used")

                pulse['sigma'] = str(p_sigma) + ' ns'

                assert( round(remainder(p_sigma, 3.2), 2) == 0), 'Pulse sigma should be divisible by 3.2'

                assert(p_sigma >= self.min_pulse_length_awg), 'Sigma is shorter than minimum available length (' + str(self.min_pulse_length_awg) +' ns)'
                assert(p_sigma < self.max_pulse_length_awg), 'Sigma is longer than maximum available length (' + str(self.max_pulse_length_awg) +' ns)'
            else:
                assert( 1 == 2 ), 'Incorrect time dimension (ms, us, ns)'

            # length should be longer than sigma
            assert( p_length >= p_sigma ), 'Pulse length should be longer or equal to sigma'

            # increment
            temp_increment = length_increment.split(" ")
            if temp_increment[1] in self.timebase_dict:
                coef = self.timebase_dict[temp_increment[1]]
                p_increment_raw = coef*float(temp_increment[0])
                p_increment = self.round_to_closest(p_increment_raw, 3.2)
                if p_increment != p_increment_raw:
                    general.message(f"Pulse increment is not divisible by 3.2. The closest available Pulse increment of {p_increment} ns is used")

                pulse['length_increment'] = str(p_increment) + ' ns'
                assert( round(remainder(p_increment, 3.2), 2) == 0), 'Pulse increment should be divisible by 3.2'

                assert (p_increment >= 0 and p_increment < self.max_pulse_length_awg), \
                'Length and sigma increment is longer than maximum available length or negative'
            else:
                assert( 1 == 2 ), 'Incorrect time dimension (ms, us, ns)'

            # start
            temp_start = start.split(" ")
            if temp_start[1] in self.timebase_dict:
                coef = self.timebase_dict[temp_start[1]]
                p_start_raw = coef*float(temp_start[0])
                p_start = self.round_to_closest(p_start_raw, 3.2)
                if p_start != p_start_raw:
                    general.message(f"Pulse start is not divisible by 3.2. The closest available Pulse start of {p_start} ns is used")

                pulse['start'] = str(p_start) + ' ns'

                assert(p_start >= 0), 'Pulse start should be a positive number'
                assert( round(remainder(p_start, 3.2), 2) == 0), 'Pulse start should be divisible by 3.2'
            else:
                assert( 1 == 2 ), 'Incorrect time dimension (ms, us, ns)'

            # delta_start
            temp_delta_start = delta_start.split(" ")
            if temp_delta_start[1] in self.timebase_dict:
                coef = self.timebase_dict[temp_delta_start[1]]
                p_delta_start_raw = coef*float(temp_delta_start[0])
                p_delta_start = self.round_to_closest(p_delta_start_raw, 3.2)
                if p_delta_start != p_delta_start_raw:
                    general.message(f"Pulse delta start is not divisible by 3.2. The closest available Pulse delta start of {p_delta_start} ns is used")

                pulse['delta_start'] = str(p_delta_start) + ' ns'

                assert(p_delta_start >= 0), 'Pulse delta start should be a positive number'
                assert( round(remainder(p_delta_start, 3.2), 2) == 0), 'Pulse delta start should be divisible by 3.2'
            else:
                assert( 1 == 2 ), 'Incorrect time dimension (ms, us, ns)'

            # d_coef
            temp_amp = float( d_coef )
            #assert(temp_amp != 0), 'Amplification coefficient should not be zero'
            assert(temp_amp >= 1), 'Amplification coefficient should be more or equal to 1'

            # b
            temp_b = float( b )
            assert(temp_b > 0), 'Parameter b should be more than 0'

            self.pulse_array_awg.append( pulse )
            self.pulse_array_init_awg = deepcopy(self.pulse_array_awg)

    def awg_next_phase(self):
        """
        A function for phase cycling. It works using phase_list decleared in awg_pulse():
        phase_list = ['-y', '+x', '-x', '+x']
        self.current_phase_index_awg is an iterator of the current phase
        functions awg_shift() and awg_increment() reset the iterator

        after calling awg_next_phase() the next phase is taken from phase_list

        the length of all phase lists specified for different pulses has to be the same
        
        the function also immediately sends a new buffer to awg card as
        a function awg_update() does. 
        """
        if self.test_flag != 'test':
            for index, element in enumerate(self.pulse_array_awg):
                if len(list(element['phase_list'])) != 0:
                    if element['phase_list'][self.current_phase_index_awg] == '+x':
                        element['phase'] = self.pulse_array_init_awg[index]['phase']

                        if self.phase_array_length_0_awg[0] == 1:
                            pass
                        else:
                            self.reset_count_awg = 0

                    elif element['phase_list'][self.current_phase_index_awg] == '-x':
                        element['phase'] = self.pulse_array_init_awg[index]['phase'] + np.pi #+ self.phase_x
                        
                        if self.phase_array_length_0_awg[0] == 1:
                            pass
                        else:
                            self.reset_count_awg = 0

                    elif element['phase_list'][self.current_phase_index_awg] == '+y':
                        element['phase'] = self.pulse_array_init_awg[index]['phase'] + np.pi / 2

                        if self.phase_array_length_0_awg[0] == 1:
                            pass
                        else:
                            self.reset_count_awg = 0

                    elif element['phase_list'][self.current_phase_index_awg] == '-y':
                        element['phase'] = self.pulse_array_init_awg[index]['phase'] + 3 * np.pi / 2

                        if self.phase_array_length_0_awg[0] == 1:
                            pass
                        else:
                            self.reset_count_awg = 0

            if self.phase_array_length_0_awg[0] == 1:
                pass
            else:
                self.current_phase_index_awg += 1

            self.awg_update()

        elif self.test_flag == 'test':
            # check that the length is equal (compare all elements in self.phase_array_length)
            gr = groupby(self.phase_array_length_0_awg)

            if (next(gr, True) and not next(gr, False)) == False:
                assert(1 == 2), 'Phase sequence for CH0 does not have equal length'

            gr = groupby(self.phase_array_length_1_awg)
            if (next(gr, True) and not next(gr, False)) == False:
                assert(1 == 2), 'Phase sequence for CH1 does not have equal length'

            for index, element in enumerate(self.pulse_array_awg):
                if len(list(element['phase_list'])) != 0:
                    if element['phase_list'][self.current_phase_index_awg] == '+x':
                        element['phase'] = self.pulse_array_init_awg[index]['phase']

                        if self.phase_array_length_0_awg[0] == 1:
                            pass
                        else:
                            self.reset_count_awg = 0

                    elif element['phase_list'][self.current_phase_index_awg] == '-x':
                        element['phase'] = self.pulse_array_init_awg[index]['phase'] + np.pi

                        if self.phase_array_length_0_awg[0] == 1:
                            pass
                        else:
                            self.reset_count_awg = 0

                    elif element['phase_list'][self.current_phase_index_awg] == '+y':
                        element['phase'] = self.pulse_array_init_awg[index]['phase'] + np.pi / 2

                        if self.phase_array_length_0_awg[0] == 1:
                            pass
                        else:
                            self.reset_count_awg = 0

                    elif element['phase_list'][self.current_phase_index_awg] == '-y':
                        element['phase'] = self.pulse_array_init_awg[index]['phase'] + 3 * np.pi / 2

                        if self.phase_array_length_0_awg[0] == 1:
                            pass
                        else:
                            self.reset_count_awg = 0

                    else:
                        assert( 1 == 2 ), 'Incorrect phase name (+x, -x, +y, -y)'

            if self.phase_array_length_0_awg[0] == 1:
                pass
            else:
                self.current_phase_index_awg += 1

            self.awg_update()

    def awg_redefine_delta_start(self, *, name, delta_start):
        """
        A function for redefining delta_start of the specified pulse for Single Joined mode.
        awg_redefine_delta_start(name = 'P0', delta_start = '10 ns') changes delta_start of the 'P0' pulse to 10 ns.
        The main purpose of the function is non-uniform sampling.

        def func(*, name1, name2): defines a function without default values of key arguments
        """

        if self.test_flag != 'test':
            i = 0

            while i < len( self.pulse_array_awg ):
                if name == self.pulse_array_awg[i]['name']:
                    # checks
                    temp_delta_start = delta_start.split(" ")
                    if temp_delta_start[1] in self.timebase_dict:
                        coef = self.timebase_dict[temp_delta_start[1]]
                        p_delta_start_raw = coef*float(temp_delta_start[0])
                        p_delta_start = self.round_to_closest(p_delta_start_raw, 3.2)

                        if p_delta_start != p_delta_start_raw:
                            general.message(f"Pulse delta start is not divisible by 3.2. The closest available Pulse delta start of {p_delta_start} ns is used")
                    
                    self.pulse_array_awg[i]['delta_start'] = str(p_delta_start) + ' ns'
                    self.shift_count_awg = 1
                else:
                    pass

                i += 1

        elif self.test_flag == 'test':
            i = 0
            assert( name in self.pulse_name_array_awg ), 'Pulse with the specified name is not defined'

            while i < len( self.pulse_array_awg ):
                if name == self.pulse_array_awg[i]['name']:
                    # checks
                    temp_delta_start = delta_start.split(" ")
                    if temp_delta_start[1] in self.timebase_dict:
                        coef = self.timebase_dict[temp_delta_start[1]]
                        
                        p_delta_start_raw = coef*float(temp_delta_start[0])
                        p_delta_start = self.round_to_closest(p_delta_start_raw, 3.2)
                        if p_delta_start != p_delta_start_raw:
                            general.message(f"Pulse delta start is not divisible by 3.2. The closest available Pulse delta start of {p_delta_start} ns is used")
                        assert( round(remainder(p_delta_start, 3.2), 2) == 0), 'Pulse delta start should be divisible by 3.2'
                        assert(p_delta_start >= 0), 'Pulse delta start is a negative number'
                    else:
                        assert( 1 == 2 ), 'Incorrect time dimension (s, ms, us, ns)'

                    self.pulse_array_awg[i]['delta_start'] = str(p_delta_start) + ' ns'
                    self.shift_count_awg = 1
                else:
                    pass

                i += 1

    def awg_redefine_frequency(self, *, name, freq):
        """
        A function for redefining frequency of the specified pulse.
        awg_redefine_frequency(name = 'P0', freq = '100 MHz') changes frequency of the 'P0' pulse to 100 MHz.

        def func(*, name1, name2): defines a function without default values of key arguments
        """

        if self.test_flag != 'test':
            i = 0

            while i < len( self.pulse_array_awg ):
                if name == self.pulse_array_awg[i]['name']:
                    self.pulse_array_awg[i]['frequency'] = freq
                    self.shift_count_awg = 1
                else:
                    pass

                i += 1

        elif self.test_flag == 'test':
            i = 0
            assert( name in self.pulse_name_array_awg ), 'Pulse with the specified name is not defined'

            while i < len( self.pulse_array_awg ):
                if name == self.pulse_array_awg[i]['name']:
                    # checks

                    if self.pulse_array_awg[i]['function'] != 'WURST' and self.pulse_array_awg[i]['function'] != 'SECH/TANH':
                        temp_freq = freq.split(" ")
                        coef = temp_freq[1]
                        p_freq = float(temp_freq[0])
                        assert (coef == 'MHz'), 'Incorrect frequency dimension. Only MHz is possible'
                        assert(p_freq >= self.min_freq_awg), 'Frequency is lower than minimum available (' + str(self.min_freq_awg) +' MHz)'
                        assert(p_freq < self.max_freq_awg), 'Frequency is longer than minimum available (' + str(self.max_freq_awg) +' MHz)'
                    else:
                        temp_freq_st = frequency[0].split(" ")
                        temp_freq_end = frequency[1].split(" ")
                        coef_st = temp_freq_st[1]
                        coef_end = temp_freq_end[1]
                        p_freq_st = float(temp_freq_st[0])
                        p_freq_end = float(temp_freq_end[0])
                        assert (coef_st == 'MHz' and coef_end == 'MHz'), 'Incorrect frequency dimension. Only MHz is possible'
                        assert(p_freq_st >= self.min_freq_awg and p_freq_end >= self.min_freq_awg), 'Frequency is lower than minimum available (' + str(self.min_freq_awg) +' MHz)'
                        assert(p_freq_st < self.max_freq_awg and p_freq_end < self.max_freq_awg), 'Frequency is longer than minimum available (' + str(self.max_freq_awg) +' MHz)'

                    self.pulse_array_awg[i]['frequency'] = freq
                    self.shift_count_awg = 1
                else:
                    pass

                i += 1

    def awg_redefine_phase(self, *, name, phase):
        """
        A function for redefining phase of the specified pulse.
        awg_redefine_phase(name = 'P0', phase = pi/2) changes phase of the 'P0' pulse to pi/2.
        The main purpose of the function phase cycling.

        def func(*, name1, name2): defines a function without default values of key arguments
        """

        if self.test_flag != 'test':
            i = 0

            while i < len( self.pulse_array_awg ):
                if name == self.pulse_array_awg[i]['name']:
                    self.pulse_array_awg[i]['phase'] = float(phase)
                    self.shift_count_awg = 1
                else:
                    pass

                i += 1

        elif self.test_flag == 'test':
            i = 0
            assert( name in self.pulse_name_array_awg ), 'Pulse with the specified name is not defined'

            while i < len( self.pulse_array_awg ):
                if name == self.pulse_array_awg[i]['name']:
                    self.pulse_array_awg[i]['phase'] = float(phase)
                    self.shift_count_awg = 1
                else:
                    pass

                i += 1

    def awg_redefine_delta_phase(self, *, name, delta_phase):
        """
        A function for redefining delta_phase of the specified pulse.
        awg_redefine_delta_phase(name = 'P0', delta_phase = pi/2) changes delta_phase of the 'P0' pulse to pi/2.
        The main purpose of the function is non-uniform sampling.

        def func(*, name1, name2): defines a function without default values of key arguments
        """

        if self.test_flag != 'test':
            i = 0

            while i < len( self.pulse_array_awg ):
                if name == self.pulse_array_awg[i]['name']:
                    self.pulse_array_awg[i]['delta_phase'] = float(delta_phase)
                    self.shift_count_awg = 1
                else:
                    pass

                i += 1

        elif self.test_flag == 'test':
            i = 0
            assert( name in self.pulse_name_array_awg ), 'Pulse with the specified name is not defined'

            while i < len( self.pulse_array_awg ):
                if name == self.pulse_array_awg[i]['name']:
                    self.pulse_array_awg[i]['delta_phase'] = float(delta_phase)
                    self.shift_count_awg = 1
                else:
                    pass

                i += 1

    def awg_add_phase(self, *, name, add_phase):
        """
        A function for adding a constant phase to the specified pulse.
        awg_add_phase(name = 'P0', add_phase = pi/2) changes the current phase of the 'P0' pulse 
        to the value of current_phase + pi/2.
        The main purpose of the function is phase cycling.

        def func(*, name1, name2): defines a function without default values of key arguments
        """

        if self.test_flag != 'test':
            i = 0

            while i < len( self.pulse_array_awg ):
                if name == self.pulse_array_awg[i]['name']:
                    self.pulse_array_awg[i]['phase'] = self.pulse_array_awg[i]['phase'] + float(add_phase)
                    self.shift_count_awg = 1
                else:
                    pass

                i += 1

            # it is bad idea to update it here, since the phase of only one pulse
            # can be changed in one call of this function
            #self.awg_update_test()

        elif self.test_flag == 'test':
            i = 0
            assert( name in self.pulse_name_array_awg ), 'Pulse with the specified name is not defined'

            while i < len( self.pulse_array_awg ):
                if name == self.pulse_array_awg[i]['name']:
                    self.pulse_array_awg[i]['phase'] = self.pulse_array_awg[i]['phase'] + float(add_phase)
                    self.shift_count_awg = 1
                else:
                    pass

                i += 1

            #self.awg_update_test()

    def awg_redefine_length_increment(self, *, name, length_increment):
        """
        A function for redefining length increment of the specified pulse.
        awg_redefine_increment(name = 'P0', length_increment = '10 ns') changes length increment of the 'P0' pulse to '10 ns'.
        The main purpose of the function is non-uniform sampling.

        def func(*, name1, name2): defines a function without default values of key arguments
        """

        if self.test_flag != 'test':
            i = 0

            while i < len( self.pulse_array_awg ):
                if name == self.pulse_array_awg[i]['name']:

                    temp_increment = length_increment.split(" ")
                    if temp_increment[1] in self.timebase_dict:
                        coef = self.timebase_dict[temp_increment[1]]
                        p_increment_raw = coef*float(temp_increment[0])
                        p_increment = self.round_to_closest(p_increment_raw, 3.2)
                        if p_increment != p_increment_raw:
                            general.message(f"Pulse increment is not divisible by 3.2. The closest available Pulse increment of {p_increment} ns is used")
                    self.pulse_array_awg[i]['length_increment'] = str(p_increment) + ' ns'
                    self.increment_count_awg = 1
                else:
                    pass

                i += 1

        elif self.test_flag == 'test':
            i = 0
            assert( name in self.pulse_name_array_awg ), 'Pulse with the specified name is not defined'

            while i < len( self.pulse_array_awg ):
                if name == self.pulse_array_awg[i]['name']:
                    # checks
                    temp_increment = length_increment.split(" ")
                    if temp_increment[1] in self.timebase_dict:
                        coef = self.timebase_dict[temp_increment[1]]
                        p_increment_raw = coef*float(temp_increment[0])
                        p_increment = self.round_to_closest(p_increment_raw, 3.2)
                        if p_increment != p_increment_raw:
                            general.message(f"Pulse increment is not divisible by 3.2. The closest available Pulse increment of {p_increment} ns is used")
                        assert( round(remainder(p_increment, 3.2), 2) == 0), 'Pulse increment should be divisible by 3.2'
                        assert (p_increment >= 0 and p_increment < self.max_pulse_length_awg), \
                        'Length and sigma increment is longer than maximum available length or negative'
                    else:
                        assert( 1 == 2 ), 'Incorrect time dimension (ms, us, ns)'

                    self.pulse_array_awg[i]['length_increment'] = str(p_increment) + ' ns'
                    self.increment_count_awg = 1
                else:
                    pass

                i += 1

    def awg_shift(self, *pulses):
        """
        A function to shift the phase of the pulses for Single mode.
        Or the start of the pulses for Single Joined mode.
        The function directly affects the pulse_array.
        """
        if self.test_flag != 'test':
            self.shift_count_awg = 1
            self.current_phase_index_awg = 0

            if len(pulses) == 0:
                i = 0
                while i < len( self.pulse_array_awg ):
                    if float( self.pulse_array_awg[i]['delta_phase'] ) == 0.:
                        pass
                    else:
                        temp  = float( self.pulse_array_awg[i]['phase'] )
                        temp2 = float( self.pulse_array_awg[i]['delta_phase'] )

                        self.pulse_array_awg[i]['phase'] = temp + temp2
 
                    i += 1

            else:
                set_from_list = set(pulses)
                for element in set_from_list:
                    if element in self.pulse_name_array_awg:
                        pulse_index = self.pulse_name_array_awg.index(element)

                        if float( self.pulse_array_awg[pulse_index]['delta_phase'] ) == 0.:
                            pass

                        else:
                            temp = float( self.pulse_array_awg[pulse_index]['phase'] )
                            temp2 = float( self.pulse_array_awg[pulse_index]['delta_phase'] )
                                    
                            self.pulse_array_awg[pulse_index]['phase'] = temp + temp2

        elif self.test_flag == 'test':
            self.shift_count_awg = 1
            self.current_phase_index_awg = 0

            if len(pulses) == 0:
                i = 0
                while i < len( self.pulse_array_awg ):
                    if float( self.pulse_array_awg[i]['delta_phase'] ) == 0.:
                        pass
                    else:
                        temp = float( self.pulse_array_awg[i]['phase'] )
                        temp2 = float( self.pulse_array_awg[i]['delta_phase'] )

                        self.pulse_array_awg[i]['phase'] = temp + temp2
                        
                    i += 1

            else:
                set_from_list = set(pulses)
                for element in set_from_list:
                    if element in self.pulse_name_array_awg:
                        pulse_index = self.pulse_name_array_awg.index(element)

                        if float( self.pulse_array_awg[pulse_index]['delta_phase'] ) == 0.:
                            pass

                        else:
                            temp = float( self.pulse_array_awg[pulse_index]['phase'] )
                            temp2 = float( self.pulse_array_awg[pulse_index]['delta_phase'] )
                                    
                            self.pulse_array_awg[pulse_index]['phase'] = temp + temp2

                    else:
                        assert(1 == 2), "There is no pulse with the specified name"

    def awg_increment(self, *pulses):
        """
        A function to increment both the length and sigma of the pulses.
        The function directly affects the pulse_array.
        """
        if self.test_flag != 'test':
            if len(pulses) == 0:
                i = 0
                while i < len( self.pulse_array_awg ):
                    if float( self.pulse_array_awg[i]['length_increment'][:-3] ) == 0:
                        pass
                    else:
                        # convertion to ns
                        temp = self.pulse_array_awg[i]['length_increment'].split(' ')
                        if temp[1] in self.timebase_dict:
                            flag = self.timebase_dict[temp[1]]
                            d_length = (float(temp[0]))*flag
                            self.dac_window = int( self.dac_window + ceil(d_length / self.timebase_pulser) )

                        else:
                            pass

                        temp2 = self.pulse_array_awg[i]['length'].split(' ')
                        if temp2[1] in self.timebase_dict:
                            flag2 = self.timebase_dict[temp2[1]]
                            leng = (float(temp2[0]))*flag2
                        else:
                            pass

                        temp3 = self.pulse_array_awg[i]['sigma'].split(' ')
                        if temp3[1] in self.timebase_dict:
                            flag3 = self.timebase_dict[temp3[1]]
                            sigm = (float(temp3[0]))*flag3
                        else:
                            pass

                        if self.pulse_array_awg[i]['function'] == 'SINE':
                            self.pulse_array_awg[i]['length'] = str( leng + d_length ) + ' ns'
                            self.pulse_array_awg[i]['sigma'] = str( sigm + d_length ) + ' ns'
                        elif self.pulse_array_awg[i]['function'] == 'GAUSS' or self.pulse_array_awg[i]['function'] == 'SINC':
                            ratio = leng/sigm
                            self.pulse_array_awg[i]['length'] = str( leng + ratio*d_length ) + ' ns'
                            self.pulse_array_awg[i]['sigma'] = str( sigm + d_length ) + ' ns'

                    i += 1

                self.increment_count_awg = 1
                self.current_phase_index_awg = 0

            else:
                set_from_list = set(pulses)
                for element in set_from_list:
                    if element in self.pulse_name_array_awg:
                        pulse_index = self.pulse_name_array_awg.index(element)

                        if float( self.pulse_array_awg[pulse_index]['length_increment'][:-3] ) == 0:
                            pass
                        else:
                            # convertion to ns
                            temp = self.pulse_array_awg[pulse_index]['length_increment'].split(' ')
                            if temp[1] in self.timebase_dict:
                                flag = self.timebase_dict[temp[1]]
                                d_length = (float(temp[0]))*flag
                                self.dac_window = int( self.dac_window + ceil(d_length / self.timebase_pulser) )
                            else:
                                pass

                            temp2 = self.pulse_array_awg[pulse_index]['length'].split(' ')
                            if temp2[1] in self.timebase_dict:
                                flag2 = self.timebase_dict[temp2[1]]
                                leng = (float(temp2[0]))*flag2
                            else:
                                pass

                            temp3 = self.pulse_array_awg[pulse_index]['sigma'].split(' ')
                            if temp3[1] in self.timebase_dict:
                                flag3 = self.timebase_dict[temp3[1]]
                                sigm = (float(temp3[0]))*flag3
                            else:
                                pass

                            if self.pulse_array_awg[pulse_index]['function'] == 'SINE':
                                self.pulse_array_awg[pulse_index]['length'] = str( leng + d_length ) + ' ns'
                                self.pulse_array_awg[pulse_index]['sigma'] = str( sigm + d_length ) + ' ns'
                            elif self.pulse_array_awg[pulse_index]['function'] == 'GAUSS' or self.pulse_array_awg[i]['function'] == 'SINC':
                                ratio = leng/sigm
                                self.pulse_array_awg[pulse_index]['length'] = str( leng + ratio*d_length ) + ' ns'
                                self.pulse_array_awg[pulse_index]['sigma'] = str( sigm + d_length ) + ' ns'

                        self.increment_count_awg = 1
                        self.current_phase_index_awg = 0

        elif self.test_flag == 'test':

            if len(pulses) == 0:
                i = 0
                while i < len( self.pulse_array_awg ):
                    if float( self.pulse_array_awg[i]['length_increment'][:-3] ) == 0:
                        pass
                    else:
                        # convertion to ns
                        temp = self.pulse_array_awg[i]['length_increment'].split(' ')
                        if temp[1] in self.timebase_dict:
                            flag = self.timebase_dict[temp[1]]
                            d_length = (float(temp[0]))*flag
                            self.dac_window = int( self.dac_window + ceil(d_length / self.timebase_pulser) )
                        else:
                            assert(1 == 2), "Incorrect time dimension (ns, us, ms)"

                        temp2 = self.pulse_array_awg[i]['length'].split(' ')
                        if temp2[1] in self.timebase_dict:
                            flag2 = self.timebase_dict[temp2[1]]
                            leng = (float(temp2[0]))*flag2
                        else:
                            assert(1 == 2), "Incorrect time dimension (ns, us, ms)"

                        temp3 = self.pulse_array_awg[i]['sigma'].split(' ')
                        if temp3[1] in self.timebase_dict:
                            flag3 = self.timebase_dict[temp3[1]]
                            sigm = (float(temp3[0]))*flag3
                        else:
                            assert(1 == 2), "Incorrect time dimension (ns, us, ms)"
                        

                        ratio = leng/sigm
                        if ( leng + ratio*d_length ) <= self.max_pulse_length_awg:
                            if self.pulse_array_awg[i]['function'] == 'SINE':
                                self.pulse_array_awg[i]['length'] = str( leng + d_length ) + ' ns'
                                self.pulse_array_awg[i]['sigma'] = str( sigm + d_length ) + ' ns'
                            elif self.pulse_array_awg[i]['function'] == 'GAUSS' or self.pulse_array_awg[i]['function'] == 'SINC':
                                #ratio = leng/sigm
                                self.pulse_array_awg[i]['length'] = str( leng + ratio*d_length ) + ' ns'
                                self.pulse_array_awg[i]['sigma'] = str( sigm + d_length ) + ' ns'
                        else:
                            assert(1 == 2), 'Exceeded maximum pulse length' + str(self.max_pulse_length_awg) + 'when increment the pulse'

                    i += 1

                self.increment_count_awg = 1
                self.current_phase_index_awg = 0

            else:
                set_from_list = set(pulses)
                for element in set_from_list:
                    if element in self.pulse_name_array_awg:

                        pulse_index = self.pulse_name_array_awg.index(element)
                        if float( self.pulse_array_awg[pulse_index]['length_increment'][:-3] ) == 0:
                            pass
                        else:
                            # convertion to ns
                            temp = self.pulse_array_awg[pulse_index]['length_increment'].split(' ')
                            if temp[1] in self.timebase_dict:
                                flag = self.timebase_dict[temp[1]]
                                d_length = (float(temp[0]))*flag
                                self.dac_window = int( self.dac_window + ceil(d_length / self.timebase_pulser) )

                            else:
                                assert(1 == 2), "Incorrect time dimension (ns, us, ms, s)"

                            temp2 = self.pulse_array_awg[pulse_index]['length'].split(' ')
                            if temp2[1] in self.timebase_dict:
                                flag2 = self.timebase_dict[temp2[1]]
                                leng = (float(temp2[0]))*flag2
                            else:
                                assert(1 == 2), "Incorrect time dimension (ns, us, ms, s)"
                            
                            temp3 = self.pulse_array_awg[pulse_index]['sigma'].split(' ')
                            if temp3[1] in self.timebase_dict:
                                flag3 = self.timebase_dict[temp3[1]]
                                sigm = (float(temp3[0]))*flag3
                            else:
                                assert(1 == 2), "Incorrect time dimension (ns, us, ms)"

                            ratio = leng/sigm
                            if ( leng + ratio*d_length ) <= self.max_pulse_length_awg:
                                if self.pulse_array_awg[pulse_index]['function'] == 'SINE':
                                    self.pulse_array_awg[pulse_index]['length'] = str( leng + d_length ) + ' ns'
                                    self.pulse_array_awg[pulse_index]['sigma'] = str( sigm + d_length ) + ' ns'
                                elif self.pulse_array_awg[pulse_index]['function'] == 'GAUSS' or self.pulse_array_awg[i]['function'] == 'SINC':
                                    #ratio = leng/sigm
                                    self.pulse_array_awg[pulse_index]['length'] = str( leng + ratio*d_length ) + ' ns'
                                    self.pulse_array_awg[pulse_index]['sigma'] = str( sigm + d_length ) + ' ns'
                            else:
                                assert(1 == 2), 'Exceeded maximum pulse length' + str(self.max_pulse_length_awg) + 'when increment the pulse'

                        self.increment_count_awg = 1
                        self.current_phase_index_awg = 0

                    else:
                        assert(1 == 2), "There is no pulse with the specified name"

    def awg_pulse_reset(self, *pulses):
        """
        Reset all pulses to the initial state it was in at the start of the experiment.
        It does not update the AWG card, if you want to reset all pulses and and also update 
        the AWG card use the function awg_reset() instead.
        """
        if self.test_flag != 'test':
            
            if len(pulses) == 0:

                # free memory
                self.pulse_array_awg = deepcopy(self.pulse_array_init_awg)
                self.reset_count_awg = 0
                self.increment_count_awg = 0
                self.shift_count_awg = 0
                self.current_phase_index_awg = 0

                #gc.collect()
                self.update_counter_awg = 0

            else:
                set_from_list = set(pulses)
                for element in set_from_list:
                    if element in self.pulse_name_array_awg:
                        pulse_index = self.pulse_name_array_awg.index(element)

                        self.pulse_array_awg[pulse_index]['phase'] = self.pulse_array_init_awg[pulse_index]['phase']
                        self.pulse_array_awg[pulse_index]['length'] = self.pulse_array_init_awg[pulse_index]['length']
                        self.pulse_array_awg[pulse_index]['sigma'] = self.pulse_array_init_awg[pulse_index]['sigma']

                        self.reset_count_awg = 0
                        self.increment_count_awg = 0
                        self.shift_count_awg = 0

        elif self.test_flag == 'test':
            if len(pulses) == 0:
                self.pulse_array_awg = deepcopy(self.pulse_array_init_awg)
                self.reset_count_awg = 0
                self.increment_count_awg = 0
                self.shift_count_awg = 0
                self.current_phase_index_awg = 0

                # free memory                
                #gc.collect()
                self.update_counter_awg = 0

            else:
                set_from_list = set(pulses)
                for element in set_from_list:
                    if element in self.pulse_name_array_awg:
                        pulse_index = self.pulse_name_array_awg.index(element)

                        self.pulse_array_awg[pulse_index]['phase'] = self.pulse_array_init_awg[pulse_index]['phase']
                        self.pulse_array_awg[pulse_index]['length'] = self.pulse_array_init_awg[pulse_index]['length']
                        self.pulse_array_awg[pulse_index]['sigma'] = self.pulse_array_init_awg[pulse_index]['sigma']

                        self.reset_count_awg = 0
                        self.increment_count_awg = 0
                        self.shift_count_awg = 0

    def awg_amplitude(self, *amplitude):
        """
        Set or query amplitude of the channel;
        Input: awg_amplitude('CH0', '600'); amplitude is in mV
        awg_amplitude('CH0', '600', 'CH1', '600')
        Default: CH0 - 600 mV; CH1 - 533 mV;
        Output: '600 mV'
        """
        if self.test_flag != 'test':
            self.setting_change_count_awg = 1

            if len(amplitude) == 2:
                ch = str(amplitude[0])
                ampl = int(amplitude[1])
                if ch == 'CH0':
                    self.amplitude_0_awg = ampl
                elif ch == 'CH1':
                    self.amplitude_1_awg = ampl
            
            elif len(amplitude) == 4:
                ch1 = str(amplitude[0])
                ampl1 = int(amplitude[1])
                ch2 = str(amplitude[2])
                ampl2 = int(amplitude[3])
                if ch1 == 'CH0':
                    self.amplitude_0_awg = ampl1
                elif ch1 == 'CH1':
                    self.amplitude_1_awg = ampl1
                if ch2 == 'CH0':
                    self.amplitude_0_awg = ampl2
                elif ch2 == 'CH1':
                    self.amplitude_1_awg = ampl2

            elif len(amplitude) == 1:
                ch = str(amplitude[0])
                if ch == 'CH0':
                    return str(self.amplitude_0_awg) + ' mV'
                elif ch == 'CH1':
                    return str(self.amplitude_1_awg) + ' mV'

        elif self.test_flag == 'test':
            self.setting_change_count_awg = 1

            if len(amplitude) == 2:
                ch = str(amplitude[0])
                ampl = int(amplitude[1])
                assert(ch == 'CH0' or ch == 'CH1'), "Incorrect channel; Should be CH0 or CH1"
                assert( ampl >= self.amplitude_min_awg and ampl <= self.amplitude_max_awg ), "Incorrect amplitude; Should be 10 <= amplitude <= 260"
                if ch == 'CH0':
                    self.amplitude_0_awg = ampl
                elif ch == 'CH1':
                    self.amplitude_1_awg = ampl
            
            elif len(amplitude) == 4:
                ch1 = str(amplitude[0])
                ampl1 = int(amplitude[1])
                ch2 = str(amplitude[2])
                ampl2 = int(amplitude[3])
                assert(ch1 == 'CH0' or ch1 == 'CH1'), "Incorrect channel 1; Should be CH0 or CH1"
                assert( ampl1 >= self.amplitude_min_awg and ampl1 <= self.amplitude_max_awg ), "Incorrect amplitude 1; Should be 10 <= amplitude <= 260"
                assert(ch2 == 'CH0' or ch2 == 'CH1'), "Incorrect channel 2; Should be CH0 or CH1"
                assert( ampl2 >= self.amplitude_min_awg and ampl2 <= self.amplitude_max_awg ), "Incorrect amplitude 2; Should be 10 <= amplitude <= 260"
                if ch1 == 'CH0':
                    self.amplitude_0_awg = ampl1
                elif ch1 == 'CH1':
                    self.amplitude_1_awg = ampl1
                if ch2 == 'CH0':
                    self.amplitude_0_awg = ampl2
                elif ch2 == 'CH1':
                    self.amplitude_1_awg = ampl2

            elif len(amplitude) == 1:
                ch1 = str(amplitude[0])
                assert(ch1 == 'CH0' or ch1 == 'CH1'), "Incorrect channel; Should be CH0 or CH1"
                if ch1 == 'CH0':
                    return str(self.amplitude_0_awg) + ' mV'
                elif ch1 == 'CH1':
                    return str(self.amplitude_1_awg) + ' mV'
            else:
                assert( 1 == 2 ), 'Incorrect arguments'

    def awg_test_flag(self, flag):
        """
        A special function for AWG Control module
        It runs TEST mode
        """
        self.test_flag = flag
        self.test_amplitude_awg = '250 mV'

    def awg_pulse_list(self):
        """
        Function for saving a pulse list from 
        the script into the header of the experimental data
        """
        pulse_list_mod = ''
        pulse_list_mod = pulse_list_mod + 'AWG amplitude (CH0, CH1): ' + str( self.awg_amplitude('CH0') ) + '; ' + str( self.awg_amplitude('CH1') ) + '\n'

        for element in self.pulse_array_awg:
            pulse_list_mod = pulse_list_mod + str(element) + '\n'

        return pulse_list_mod

    def awg_visualize(self):
        """
        A function for buffer visualization
        """
        if self.test_flag != 'test':
            
            self.channel_1 , self.channel_2 = self.define_buffer_single_joined_awg()
            xs = ( round( 1000 / self.sample_rate_awg, 1 ) ) * np.arange(len(self.channel_1))
            general.plot_1d('DAC buffer', xs, (self.channel_1, self.channel_2), label = 'ch')
        
        elif self.test_flag == 'test':
            
            self.channel_1 , self.channel_2 = self.define_buffer_single_joined_awg()
            xs = ( round( 1000 / self.sample_rate_awg, 1 ) ) * np.arange(len(self.channel_1))
            general.plot_1d('DAC buffer', xs, (self.channel_1, self.channel_2), label = 'ch')

    def awg_correction(self, only_pi_half = 'True', coef_array = [1, 0, 0, 1, 0, 0, 1, 0, 0, 1], low_level = 16, limit = 23):
        """
        Funtion for amplitude correction taking into account the resonator frequency profile
        """
        self.bl_awg = coef_array[0]
        self.a1_awg = coef_array[1]
        self.x1_awg = coef_array[2]
        self.w1_awg = coef_array[3]
        self.a2_awg = coef_array[4]
        self.x2_awg = coef_array[5]
        self.w2_awg = coef_array[6]
        self.a3_awg = coef_array[7]
        self.x3_awg = coef_array[8]
        self.w3_awg = coef_array[9]

        if only_pi_half == 'True':
            self.pi2flag_awg = 1
        else:
            self.pi2flag_awg = 0

        # in MHz
        # limit minimum B1
        # 16 MHz is the value for MD3 at +-150 MHz around the center
        # 23 MHz is an arbitrary limit; around 210 MHz width        
        self.low_level_awg = low_level
        self.limit_awg = limit

    # UNDOCUMENTED
    def awg_clear(self):
        """
        A special function for AWG Control module
        It clear self.pulse_array_awg and other status flags
        """
        self.pulse_array_awg = []
        self.phase_array_length = []
        self.phase_array_length_0_awg = []
        self.phase_array_length_1_awg = []
        self.pulse_name_array_awg = []
        self.pulse_array_init_awg = []
        self.pulse_ch0_array_awg = []
        self.pulse_ch1_array_awg = []
        
        self.reset_count_awg = 0
        self.shift_count_awg = 0
        self.increment_count_awg = 0
        self.setting_change_count_awg = 0
        self.state_awg = 0
        self.current_phase_index_awg = 0

    # UNDOCUMENTED
    def awg_clear_pulses(self):
        """
        A special function for clearing pulses and flags
        when the card is opened
        """
        self.pulse_array_awg = []
        self.phase_array_length = []
        self.phase_array_length_0_awg = []
        self.phase_array_length_1_awg = []
        self.pulse_name_array_awg = []
        self.pulse_array_init_awg = []
        self.pulse_ch0_array_awg = []
        self.pulse_ch1_array_awg = []
        
        self.reset_count_awg = 0
        self.shift_count_awg = 0
        self.increment_count_awg = 0
        self.setting_change_count_awg = 0
        self.state_awg = 1
        self.current_phase_index_awg = 0

    ####################AUX#####################
    def gen_2d_array_from_buffer(self, data, adc_window, p, ph, live_mode):
        #начало заголовка
        #0хAA5500FF

        self.buffer_ready = 1
        ind = np.where(data == -1437269761)[0]
        ind = np.append(ind, [int (self.nStrmBufSizeb_brd / 4 )])

        ####
        self.nid_prev = self.nid_split
        ####

        # FOR SCANS
        if self.reset_flag == 0:
            # to get rid of splitted buffer in live mode
            if live_mode == 0:
                splitted_data = np.split(data, ind )[1:-1]
                splitted_data_tail = np.split(data, ind )[0:1]
            elif live_mode == 1:
                splitted_data = np.split(data, ind )[1:-2] # or -3?
                splitted_data_tail = (np.array([]), np.array([]))

        elif self.reset_flag == 1:
            # to get rid of splitted buffer in live mode
            if live_mode == 0:
                splitted_data = np.split(data, ind )[1:-2]
                splitted_data_tail = np.split(data, ind )[0:1]
            elif live_mode == 1:
                splitted_data = np.split(data, ind )[1:-2] # or -3?
                splitted_data_tail = (np.array([]), np.array([]))
            
            ###self.flag_buffer_cut = 0
            # this does nothing
            self.reset_flag = 0
            #self.nid_prev = -1  # important
        
        #splitted_data_tail = np.split(data, ind )[0:1]
        
        #a = []
        #b = []

        full_adc = adc_window * 16
        data_raw = np.zeros( ( int(p * ph * full_adc ) ), dtype = np.int32 )
        count_nip = np.zeros( (int(p * ph) ), dtype = np.int16 )

        for i in range(len(splitted_data)):

            nid = int.from_bytes( ( (splitted_data[i])[2:4] ).tobytes()[0:6], byteorder='little' )
            
            #if self.nid_prev != nid:
                #a.append(nid)

            len_data = len((splitted_data[i]))
            dif = int( full_adc + 8) - len_data

            len_data_tail = len(splitted_data_tail[0])
            dif_tail = int( full_adc ) - len_data_tail

            if (len(splitted_data_tail[0]) != 0) and (self.flag_buffer_cut == 1):
                #if self.nid_split != nid:
                if (nid != 0):
                    data_raw[(self.nid_split*full_adc + dif_tail):((self.nid_split + 1)*full_adc)] += (splitted_data_tail[0])
                    self.flag_buffer_cut = 0
                    #b.append(self.nid_split)

            # only in the last part of the buffer => beginning of the splitted data
            if dif != 0: #) and (nid != self.N_IP)
                if self.flag_buffer_cut == 0:
                    # inccorect head in the last point
                    if (nid != (p * ph - 1)):
                        data_raw[(nid*full_adc):(nid*full_adc + len_data - 8)] += (splitted_data[i])[8:]
                    else:
                        # inccorect count in the last point and prevent double subtraction
                        if (self.sub_flag == 0): #and (self.reset_count_nip == 1)
                            count_nip[nid] += -1
                            self.sub_flag = 1

                    self.flag_buffer_cut = 1
                    self.nid_split = nid

            else:
                data_raw[(nid*full_adc):((nid + 1)*full_adc)] += (splitted_data[i])[8:]

            if self.reset_count_nip == 0:
                if (count_nip[nid] == 1) and (self.nid_prev != nid):
                    pass
                elif (self.nid_prev == nid):
                    count_nip[nid] += 1
            elif self.reset_count_nip == 1:
                count_nip[nid] += 1

            self.nid_prev = nid

        # In live_ mode self.reset_count_nip is always 1
        if live_mode == 1:
            count_nip += -1

        self.N_IP = nid

        #general.message(f'NID_SPLIT: {self.nid_split}')
        #general.message(count_nip)
        #general.message(f'N_IP_BOARD: {self.nIP_No_brd}')
        #general.message(f'N_IP_BUFFER: {self.N_IP}')

        return data_raw, count_nip

    def gen_2d_array_from_buffer2(self, data, adc_window, p, ph, live_mode):
        """
        Skip additional repetitons
        """

        #начало заголовка
        #0хAA5500FF

        self.buffer_ready = 1
        ind = np.where(data == -1437269761)[0]
        ind = np.append(ind, [int (self.nStrmBufSizeb_brd / 4 )])

        ####
        ####self.nid_prev = self.nid_split
        ####

        # FOR SCANS
        if self.reset_flag == 0:
            # to get rid of splitted buffer in live mode
            if live_mode == 0:
                splitted_data = np.split(data, ind )[1:-1]
                splitted_data_tail = np.split(data, ind )[0:1]
            elif live_mode == 1:
                splitted_data = np.split(data, ind )[1:-2] # or -3?
                splitted_data_tail = (np.array([]), np.array([]))

        elif self.reset_flag == 1:
            # to get rid of splitted buffer in live mode
            if live_mode == 0:
                splitted_data = np.split(data, ind )[1:-2]
                splitted_data_tail = np.split(data, ind )[0:1]
            elif live_mode == 1:
                splitted_data = np.split(data, ind )[1:-2] # or -3?
                splitted_data_tail = (np.array([]), np.array([]))
            
            ###self.flag_buffer_cut = 0
            self.reset_flag = 0
            #self.nid_prev = -1  # important
        
        #splitted_data_tail = np.split(data, ind )[0:1]
        
        #a = []
        #b = []

        full_adc = adc_window * 16
        data_raw = np.zeros( ( int(p * ph * full_adc ) ), dtype = np.int32 )
        count_nip = np.zeros( (int(p * ph) * 1), dtype = np.int16 )

        for i in range(len(splitted_data)):

            nid = int.from_bytes( ( (splitted_data[i])[2:4] ).tobytes()[0:6], byteorder='little' )
            
            if self.nid_prev != nid:
                #a.append(nid)

                len_data = len((splitted_data[i]))
                dif = int( full_adc + 8) - len_data

                len_data_tail = len(splitted_data_tail[0])
                dif_tail = int( full_adc ) - len_data_tail

                if (len(splitted_data_tail[0]) != 0) and (self.flag_buffer_cut == 1):
                    #if self.nid_split != nid:
                    if (nid != 0) :
                        data_raw[(self.nid_split*full_adc + dif_tail):((self.nid_split + 1)*full_adc)] += (splitted_data_tail[0])
                        self.flag_buffer_cut = 0
                        #b.append(self.nid_split)

                # only in the last part of the buffer => beginning of the splitted data
                if dif != 0: #) and (nid != self.N_IP)
                    if self.flag_buffer_cut == 0:
                        # inccorect head in the last point
                        if (nid != (p * ph - 1)):
                            data_raw[(nid*full_adc):(nid*full_adc + len_data - 8)] += (splitted_data[i])[8:]
                        else:
                            # inccorect count in the last point and prevent double subtraction
                            if (self.sub_flag == 0): #and (self.reset_count_nip == 1)
                                count_nip[nid] += -1
                                self.sub_flag = 1

                        self.flag_buffer_cut = 1
                        self.nid_split = nid

                else:
                    data_raw[(nid*full_adc):((nid + 1)*full_adc)] += (splitted_data[i])[8:]

                if self.reset_count_nip == 0:
                    if (count_nip[nid] == 1) and (self.nid_prev != nid):
                        pass
                    elif (self.nid_prev == nid):
                        count_nip[nid] += 1
                elif self.reset_count_nip == 1:
                    count_nip[nid] += 1

            self.nid_prev = nid

        # In live_ mode self.reset_count_nip is always 1
        if live_mode == 1:
            count_nip += -1

        self.N_IP = nid
        #general.message(a)
        #general.message(count_nip)
        #general.message(f'N_IP_BOARD: {self.nIP_No_brd}')
        #general.message(f'N_IP_BUFFER: {self.N_IP}')

        return data_raw, count_nip

    def overflow_check(self, BufNum, BufTot, BufCnt, StreamBufTot):
        """
        Buffer Overflow
        """
        if ( BufTot > ( BufNum ) ): 
            general.message(f"overflow error nBufToClcNum = {BufTot}")
            #general.message(f"BufCnt = {BufCnt}")
            #general.message(f"nStrmBufTotalCnt = {StreamBufTot}" )
            BufTot = BufTot % BufNum
            #BufTot = 1
            
        return BufTot

    def convertion_to_numpy_pulser(self, p_array):
        """
        Convertion of the pulse_array_pulser into numpy array in the form of
        [channel_number, start, end, delta_start, length_increment]
        channel_number is an integer: ch, where ch from self.channel_dict
        start is a pulse start in a pulser self.clock sample rate
        end is a pulse end in a pulser self.clock sample rate
        delta_start is a pulse delta_start in a pulser self.clock sample rate
        length_increment is a pulse length_increment in a pulser self.clock sample rate
        The numpy array is shifted (250 ns) and sorted according to channel number
        """
        if self.test_flag != 'test':
            i = 0
            pulse_temp_array = []
            num_pulses = len( p_array )
            while i < num_pulses:
                # get channel number
                ch = p_array[i]['channel']
                if ch in self.channel_dict_pulser:
                    ch_num = self.channel_dict_pulser[ch]

                # get start
                if ch != 'AWG':
                    st = p_array[i]['start']
                else:
                    # shift AWG pulse to get RECT_AWG
                    st = self.change_pulse_settings_pulser(p_array[i]['start'], -self.rect_awg_switch_delay_pulser)
                    self.awg_pulses_pulser = 1

                if st[-2:] == 'ns':
                    st_time = int( ceil(round( float(st[:-3]) / self.timebase_pulser, 1) ) )
                elif st[-2:] == 'us':
                    st_time = int( ceil(round( float(st[:-3]) * 1000 / self.timebase_pulser, 1) ) )
                elif st[-2:] == 'ms':
                    st_time = int( ceil(round( float(st[:-3]) * 1000000 / self.timebase_pulser, 1) ) )
                elif st[-2:] == 's':
                    st_time = int( ceil(round( float(st[:-3]) * 1000000000 / self.timebase_pulser, 1) ) )
                
                # get length
                if ch != 'AWG':
                    leng = p_array[i]['length']
                else:
                    # shift AWG pulse to get RECT_AWG
                    leng = self.change_pulse_settings_pulser(p_array[i]['length'], self.rect_awg_switch_delay_pulser + self.rect_awg_delay_pulser)
                    self.awg_pulses_pulser = 1

                if leng[-2:] == 'ns':
                    leng_time = int( ceil(round( float(leng[:-3]) / self.timebase_pulser, 1) ) )
                elif leng[-2:] == 'us':
                    leng_time = int( ceil(round( float(leng[:-3]) * 1000 / self.timebase_pulser, 1) ) )
                elif leng[-2:] == 'ms':
                    leng_time = int( ceil(round( float(leng[:-3]) * 1000000 / self.timebase_pulser, 1) ) )
                elif leng[-2:] == 's':
                    leng_time = int( ceil(round( float(leng[:-3]) * 1000000000 / self.timebase_pulser, 1) ) )

                # get delta start
                del_st = p_array[i]['delta_start']
                if del_st[-2:] == 'ns':
                    delta_start = int( ceil(round( float(del_st[:-3]) / self.timebase_pulser, 1) ) )
                elif del_st[-2:] == 'us':
                    delta_start = int( ceil(round( float(del_st[:-3]) * 1000 / self.timebase_pulser, 1) ) )
                elif del_st[-2:] == 'ms':
                    delta_start = int( ceil(round( float(leng[:-3]) * 1000000 / self.timebase_pulser, 1) ) )
                elif del_st[-2:] == 's':
                    delta_start = int( ceil(round( float(del_st[:-3]) * 1000000000 / self.timebase_pulser, 1) ) )

                # get length_increment
                len_in = p_array[i]['length_increment']
                if len_in[-2:] == 'ns':
                    length_increment = int( ceil(round( float(len_in[:-3]) / self.timebase_pulser, 1) ) )
                elif len_in[-2:] == 'us':
                    length_increment = int( ceil(round( float(len_in[:-3]) * 1000 / self.timebase_pulser, 1) ) )
                elif len_in[-2:] == 'ms':
                    length_increment = int( ceil(round( float(len_in[:-3]) * 1000000 / self.timebase_pulser, 1) ) )
                elif len_in[-2:] == 's':
                    length_increment = int( ceil(round( float(len_in[:-3]) * 1000000000 / self.timebase_pulser, 1) ) )

                # creating converted array
                # in terms of bits the number of channel is 2**(ch_num - 1)
                #pulse_temp_array.append( (2**(ch_num), st_time, st_time + leng_time, delta_start, length_increment) )
                pulse_temp_array.append( (2**(ch_num), st_time + self.constant_shift_pulser, self.constant_shift_pulser + st_time + leng_time) )

                i += 1

            # should be sorted according to channel number for corecct splitting into subarrays
            return np.asarray(sorted(pulse_temp_array, key = lambda x: int(x[0])), dtype = np.int64)

        elif self.test_flag == 'test':
            i = 0
            pulse_temp_array = []
            num_pulses = len( p_array )

            while i < num_pulses:
                # get channel number
                ch = p_array[i]['channel']
                if ch in self.channel_dict_pulser:
                    ch_num = self.channel_dict_pulser[ch]

                # get start
                if ch != 'AWG':
                    st = p_array[i]['start']
                else:
                    st = self.change_pulse_settings_pulser(p_array[i]['start'], -self.rect_awg_switch_delay_pulser)
                    self.awg_pulses_pulser = 1

                if st[-2:] == 'ns':
                    st_time = int( ceil(round( float(st[:-3]) / self.timebase_pulser, 1) ) )
                elif st[-2:] == 'us':
                    st_time = int( ceil(round( float(st[:-3]) * 1000 / self.timebase_pulser, 1) ) )
                elif st[-2:] == 'ms':
                    st_time = int( ceil(round( float(st[:-3]) * 1000000 / self.timebase_pulser, 1) ) )
                elif st[-2:] == 's':
                    st_time = int( ceil(round( float(st[:-3]) * 1000000000 / self.timebase_pulser, 1) ) )

                # get length
                if ch != 'AWG':
                    leng = p_array[i]['length']
                else:
                    # shift AWG pulse to get RECT_AWG
                    leng = self.change_pulse_settings_pulser(p_array[i]['length'], self.rect_awg_switch_delay_pulser + self.rect_awg_delay_pulser)
                    self.awg_pulses_pulser = 1

                if leng[-2:] == 'ns':
                    leng_time = int( ceil(round( float(leng[:-3]) / self.timebase_pulser, 1) ) )
                elif leng[-2:] == 'us':
                    leng_time = int( ceil(round( float(leng[:-3]) * 1000 / self.timebase_pulser, 1) ) )
                elif leng[-2:] == 'ms':
                    leng_time = int( ceil(round( float(leng[:-3]) * 1000000 / self.timebase_pulser, 1) ) )
                elif leng[-2:] == 's':
                    leng_time = int( ceil(round( float(leng[:-3]) * 1000000000 / self.timebase_pulser, 1) ) )

                # get delta start
                del_st = p_array[i]['delta_start']

                if del_st[-2:] == 'ns':
                    delta_start = int( ceil(round( float(del_st[:-3]) / self.timebase_pulser, 1) ) )
                elif del_st[-2:] == 'us':
                    delta_start = int( ceil(round( float(del_st[:-3]) * 1000 / self.timebase_pulser, 1) ) )
                elif del_st[-2:] == 'ms':
                    delta_start = int( ceil(round( float(del_st[:-3]) * 1000000 / self.timebase_pulser, 1) ) )
                elif del_st[-2:] == 's':
                    delta_start = int( ceil(round( float(del_st[:-3]) * 1000000000 / self.timebase_pulser, 1) ) )

                # get length_increment
                len_in = p_array[i]['length_increment']

                if len_in[-2:] == 'ns':
                    length_increment = int( ceil(round( float(len_in[:-3]) / self.timebase_pulser, 1) ) )
                elif len_in[-2:] == 'us':
                    length_increment = int( ceil(round( float(len_in[:-3]) * 1000 / self.timebase_pulser, 1) ) )
                elif len_in[-2:] == 'ms':
                    length_increment = int( ceil(round( float(len_in[:-3]) * 1000000 / self.timebase_pulser, 1) ) )
                elif len_in[-2:] == 's':
                    length_increment = int( ceil(round( float(len_in[:-3]) * 1000000000 / self.timebase_pulser, 1) ) )

                # creating converted array
                # in terms of bits the number of channel is 2**(ch_num - 1)
                pulse_temp_array.append( (2**(ch_num), self.constant_shift_pulser + st_time, self.constant_shift_pulser + st_time + leng_time ) )

                i += 1

            # should be sorted according to channel number for corecct splitting into subarrays
            return np.asarray(sorted(pulse_temp_array, key = lambda x: int(x[0])), dtype = np.int64)

    def splitting_acc_to_channel_pulser(self, np_array):
        """
        A function that splits pulse array into
        several array that have the same channel
        I.E. [[1, 10, 100], [8, 100, 40], [8, 200, 20], [8, 300, 20] 
        -> [array([[1, 10, 100]]) , array([[8, 100, 40], [8, 200, 20], [8, 300, 20]])]
        Input array should be sorted

        RECT_AWG pulses are combined with MW pulses in the same array, since for
        both of them AMP_ON and LNA_PROTECT pulses are needed
        """
        if self.test_flag != 'test':
            # according to 0 element (channel number)
            answer = np.split(np_array, np.where(np.diff(np_array[:,0]))[0] + 1)

            # to save time if there is no AWG pulses
            if self.awg_pulses_pulser == 0:
                pass
            elif self.awg_pulses_pulser == 1:
                # join AWG and MW pulses in order to add AMP_ON and LNA_PROTECT for them together
                for index, element in enumerate(answer):
                    # memorize indexes
                    if element[0, 0] == self.channel_dict_pulser['MW']:
                        mw_index = index
                    elif element[0, 0] == self.channel_dict_pulser['AWG']:
                        awg_index = index

                # combines arrays of MW and AWG pulses if there is MW and AWG pulses
                try:
                    # continuation of combining
                    answer[mw_index] = np.concatenate((answer[mw_index], answer[awg_index]), axis = 0)
                    # delete duplicated AWG pulses; answer is python list -> pop
                    answer.pop(awg_index)

                except UnboundLocalError:
                    pass

            return answer

        elif self.test_flag == 'test':
            # according to 0 element (channel number)
            answer = np.split(np_array, np.where(np.diff(np_array[:,0]))[0] + 1)

            if self.awg_pulses_pulser == 0:
                pass
            elif self.awg_pulses_pulser == 1:
                # attempt to join AWG and MW pulses in order to add AMP_ON and LNA_PROTECT for them together
                for index, element in enumerate(answer):
                    # memorize indexes
                    if element[0, 0] == self.channel_dict_pulser['MW']:
                        mw_index = index
                    elif element[0, 0] == self.channel_dict_pulser['AWG']:
                        awg_index = index

                # combines arrays if there is MW and AWG pulses
                try:
                    answer[mw_index] = np.concatenate((answer[mw_index], answer[awg_index]), axis = 0)
                    # delete duplicated AWG pulses; answer is python list -> pop
                    answer.pop(awg_index)

                except UnboundLocalError:
                    pass

            return answer

    def extending_rect_awg_pulser(self, np_array):
        """
        Replace RECT_AWG pulse with the extending one (in the same way as AMP_ON and LNA_PROTECT)
        
        Instead of directly changing self.pulse_array_pulser we change the output of 
        self.splitting_acc_to_channel_pulser() and use this function in the output of preparing_to_bit_pulse_pulser()


        """
        if self.test_flag != 'test':
            answer = self.splitting_acc_to_channel_pulser( self.convertion_to_numpy_pulser( np_array ) )
            # return flatten np.array of pulses that has the same format as self.convertion_to_numpy_pulser( np_array )
            # but with extended RECT_AWG pulse
            for index, element in enumerate(answer):
                if element[0, 0] == 2**self.channel_dict_pulser['MW'] or element[0, 0] == 2**self.channel_dict_pulser['AWG']:
                    answer[index] = self.check_problem_pulses_pulser(element)
            
            return np.asarray(list(chain(*answer)))

        elif self.test_flag == 'test':
            answer = self.splitting_acc_to_channel_pulser( self.convertion_to_numpy_pulser( np_array ) )
            # iterate over all pulses at different channels
            for index, element in enumerate(answer):
                if element[0, 0] == 2**self.channel_dict_pulser['MW'] or element[0, 0] == 2**self.channel_dict_pulser['AWG'] or element[0, 0] == 2**self.channel_dict_pulser['TRIGGER_AWG']:
                    answer[index] = self.check_problem_pulses_pulser(element)
                        
            return np.asarray(list(chain(*answer)))

    def check_problem_pulses_pulser(self, np_array):
        """
        A function for checking whether there is a two
        close to each other pulses (less than 40 ns)
        In auto_defense_pulser = True we checked everything except
        AMN_ON and LNA_PROTECT
        """
        if self.test_flag != 'test':
            # sorted pulse list in order to be able to have an arbitrary pulse order inside
            # the definition in the experimental script
            sorted_np_array = np.asarray(sorted(np_array, key = lambda x: int(x[1])), dtype = np.int64)

            ### compare the end time with the start time for each couple of pulses
            index = 0
            data_to_check = sorted_np_array[:-1] 

            while index < len(sorted_np_array) - 1:
                element = sorted_np_array[index]
                next_element = sorted_np_array[index + 1]

                if next_element[1] - element[2] < self.min_pulse_length_pulser:

                    sorted_np_array[index][2] = next_element[2]
                    sorted_np_array = np.delete(sorted_np_array, index + 1, 0)

                    if self.mes == 0:
                        general.message(f'Overlapping pulses or two pulses with less than {self.min_pulse_length_pulser} ns distance')
                        self.mes = 1
                    
                    index = 0
                    continue
                        
                index += 1

            return sorted_np_array

        elif self.test_flag == 'test':
            sorted_np_array = np.asarray(sorted(np_array, key = lambda x: int(x[1])), dtype = np.int64)
            
            index = 0
            data_to_check = sorted_np_array[:-1] 

            while index < len(sorted_np_array) - 1:
                element = sorted_np_array[index]
                next_element = sorted_np_array[index + 1]

                if next_element[1] - element[2] < self.min_pulse_length_pulser:
                    if element[0] == 2**self.channel_dict_pulser['TRIGGER_AWG']:
                        assert False, 'Overlapping AWG pulses'
                    else:

                        sorted_np_array[index][2] = next_element[2]
                        sorted_np_array = np.delete(sorted_np_array, index + 1, 0)

                        if self.mes == 0:
                            general.message(f'Overlapping pulses or two pulses with less than {self.min_pulse_length_pulser} ns distance')
                            self.mes = 1
                        
                        index = 0 
                        continue
                        
                index += 1

            return sorted_np_array

    def check_problem_pulses_phase_pulser(self, np_array):
        """
        A function for checking whether there is a two
        close to each other pulses (less than 12 ns)
        In auto_defense_pulser = True by this function we checked only 
        -X +Y -Y pulses since they have different minimal distance
        """
        if self.test_flag != 'test':
            # sorted pulse list in order to be able to have an arbitrary pulse order inside
            # the definition in the experimental script
            sorted_np_array = np.asarray(sorted(np_array, key = lambda x: int(x[1])), dtype = np.int64)

            ## 16-09-2021; An attempt to optimize the speed; all pulses should be already checked in the TEST RUN
            ## Uncomment everything starting with ## if needed

            ### compare the end time with the start time for each couple of pulses
            ##for index, element in enumerate(sorted_np_array[:-1]):
            ##    if sorted_np_array[index + 1][1] - element[2] < self.minimal_distance_phase_pulser:
            ##        assert(1 == 2), 'Overlapping pulses or two pulses with less than ' + str(self.minimal_distance_phase_pulser * self.timebase_pulser) + ' ns distance'
            ##    else:
            ##        pass

            return sorted_np_array

        elif self.test_flag == 'test':
            sorted_np_array = np.asarray(sorted(np_array, key = lambda x: int(x[1])), dtype = np.int64)

            # compare the end time with the start time for each couple of pulses
            for index, element in enumerate(sorted_np_array[:-1]):
                if sorted_np_array[index + 1][1] - element[2] < self.minimal_distance_phase_pulser:
                    assert(1 == 2), f'Overlapping pulses or two pulses with less than {self.minimal_distance_phase_pulser * self.timebase_pulser} ns distance'
                else:
                    pass

            return np_array

    def delete_duplicates_pulser(self, np_array):
        """
        Auxilary function that delete duplicates from numpy array
        It is used when we deal with AMP_ON and LNA_PROTECT pulses
        with less than 12 ns distance
        """
        if self.test_flag != 'test':
            no_duplicate_array = np.unique(np_array, axis = 0)
            return no_duplicate_array

        elif self.test_flag == 'test':
            no_duplicate_array = np.unique(np_array, axis = 0)
            return no_duplicate_array

    def preparing_to_bit_pulse_pulser(self, np_array):
        """
        For pulses at each channel we check whether there is overlapping pulses using 
        check_problem_pulses_pulser()

        This function also automatically adds LNA_PROTECT and AMP_ON pulses 
        using add_amp_on_pulses() / add_lna_protect_pulses_pulser() and check
        them on the distance < 12 ns, if so they are combined in one pulse inside 
        instruction_pulse_short_lna_amp_pulser() function

        for phase pulses the minimal distance for checking is 10 ns
        for mw, awg or cross mw-awg - 40 ns

        RECT_AWG pulses are shifted back in order to compare their distance with MW pulses

        """
        if self.test_flag != 'test':
            if self.auto_defense_pulser == 'False':
                split_pulse_array = self.splitting_acc_to_channel_pulser( self.convertion_to_numpy_pulser( np_array ) )
                # iterate over all pulses at different channels
                for index, element in enumerate(split_pulse_array):
                    # for all pulses just check 40 ns distance
                    self.check_problem_pulses_pulser(element)
                    # get assertion error if the distance < 40 ns
                    
                return self.convertion_to_numpy_pulser( np_array )

            elif self.auto_defense_pulser == 'True':
                # for delete AWG pulses before overlap check; and for checking only AWG pulses
                awg_index = []
                mw_index = []
                # for checking of overlap MW and non-shifted AWG; in the real pulse sequence AWG is converted to shifter RECT_AWG
                shifted_back_awg_pulses = []

                split_pulse_array = self.splitting_acc_to_channel_pulser( self.convertion_to_numpy_pulser( np_array ) )

                # iterate over all pulses at different channels
                for index, element in enumerate(split_pulse_array):
                    if element[0, 0] == 2**self.channel_dict_pulser['MW'] or element[0, 0] == 2**self.channel_dict_pulser['AWG']:

                        self.check_problem_pulses_pulser(element)
                        
                        #if self.awg_pulses_pulser != 1:
                        #    # for MW pulses check 40 ns distance and add AMP_ON, LNA_PROTECT pulses
                        #    self.check_problem_pulses_pulser(element)
                        #else:
                        #    # for AWG we do not check 40 ns distance, since RECT_AWG will be extended in the same way as AMP_ON
                        #    for index_awg_mw, element_awg_mw in enumerate(element):
                        #        if element_awg_mw[0] == self.channel_dict_pulser['AWG']:
                        #            # shift back RECT_AWG to AWG
                        #            shifted_back_awg_pulses.append([element_awg_mw[0], element_awg_mw[1] + 0*int(self.rect_awg_switch_delay_pulser/self.timebase_pulser), \
                        #                element_awg_mw[2] + 0*int(self.rect_awg_switch_delay_pulser/self.timebase_pulser) - 0*int(self.rect_awg_switch_delay_pulser/self.timebase_pulser) - 0*int(self.rect_awg_delay_pulser/self.timebase_pulser)])
                        #
                        #            awg_index.append(index_awg_mw)
                        #
                        #        elif element_awg_mw[0] == self.channel_dict_pulser['MW']:
                        #            mw_index.append(index_awg_mw)
                        #
                        #
                        #    no_mw_element = np.delete( element, list(dict.fromkeys(mw_index)), axis = 0 ).tolist()
                        #    no_awg_element = np.delete( element, list(dict.fromkeys(awg_index)), axis = 0 ).tolist()
                        #    # if there is no MW
                        #    try:
                        #        shifted_back_awg_mw = np.concatenate((no_awg_element, shifted_back_awg_pulses), axis = 0)
                        #    except ValueError:
                        #        shifted_back_awg_mw = shifted_back_awg_pulses
                        #    
                        #    self.check_problem_pulses_pulser(no_awg_element)
                        #    self.check_problem_pulses_pulser(no_mw_element)
                        #    self.check_problem_pulses_pulser(shifted_back_awg_mw)

                        # add AMP_ON and LNA_PROTECT
                        amp_on_pulses = self.add_amp_on_pulses_pulser(element)
                        lna_pulses = self.add_lna_protect_pulses_pulser(element)

                        # check AMP_ON, LNA_PROTECT pulses on < 12 ns distance
                        cor_pulses_amp, prob_pulses_amp = self.check_problem_pulses_amp_lna_pulser(amp_on_pulses)
                        cor_pulses_lna, prob_pulses_lna = self.check_problem_pulses_amp_lna_pulser(lna_pulses)

                        # combining short distance AMP_ON pulses; the action depends on
                        # whether there are "problenatic pulses" (prob_pulses_amp)
                        # cor_pulses_amp - pulses with > 12 ns distance
                        # problenatic pulses are joined by convertion to bit array, applying 
                        # check_short_pulses_pulser() / joining_pulses_pulser() inside convert_to_bit_pulse_amp_lna_pulser()
                        # and back to instruction instruction_pulse_short_lna_amp_pulser()
                        if prob_pulses_amp[0][0] == 0:
                            cor_pulses_amp_final = cor_pulses_amp
                        elif cor_pulses_amp[0][0] == 0:
                            # nothing to concatenate
                            amp_on_pulses = self.convert_to_bit_pulse_amp_lna_pulser(prob_pulses_amp, \
                                self.channel_dict_pulser['AMP_ON'])
                            cor_pulses_amp_final = self.instruction_pulse_short_lna_amp_pulser(amp_on_pulses)
                        else:
                            amp_on_pulses = self.convert_to_bit_pulse_amp_lna_pulser(prob_pulses_amp, \
                                self.channel_dict_pulser['AMP_ON'])
                            try:
                                #cor_pulses_amp_final = cor_pulses_amp, self.instruction_pulse_short_lna_amp_pulser(amp_on_pulses)
                                cor_pulses_amp_final = np.concatenate((cor_pulses_amp, self.instruction_pulse_short_lna_amp_pulser(amp_on_pulses)), axis = 0)
                            except ValueError:
                                cor_pulses_amp_final = np.concatenate((cor_pulses_amp, self.instruction_pulse_short_lna_amp_pulser(amp_on_pulses)), axis = 0)

                        # combining short distance LNA_PROTECT pulses
                        if prob_pulses_lna[0][0] == 0:
                            cor_pulses_lna_final = cor_pulses_lna
                        elif cor_pulses_lna[0][0] == 0:
                            # nothing to concatenate
                            lna_pulses = self.convert_to_bit_pulse_amp_lna_pulser(prob_pulses_lna, self.channel_dict_pulser['LNA_PROTECT'])
                            cor_pulses_lna_final = self.instruction_pulse_short_lna_amp_pulser(lna_pulses)
                        else:
                            lna_pulses = self.convert_to_bit_pulse_amp_lna_pulser(prob_pulses_lna, self.channel_dict_pulser['LNA_PROTECT'])
                            cor_pulses_lna_final =  np.concatenate((cor_pulses_lna, self.instruction_pulse_short_lna_amp_pulser(lna_pulses)), axis = 0)


                    elif element[0, 0] == 2**self.channel_dict_pulser['-X'] or element[0, 0] == 2**self.channel_dict_pulser['+Y']:
                        pass
                        # for phase pulses just check 10 ns distance
                        # self.check_problem_pulses_pulser(element)
                        # get assertion error if the distance < 10 ns
                    else:
                        pass
                        # for non-MW pulses just check 40 ns distance
                        #self.check_problem_pulses_pulser(element)
                        # get assertion error if the distance < 40 ns

                # combine all pulses
                #np.concatenate( (self.convertion_to_numpy_pulser( self.pulse_array_pulser ), cor_pulses_amp_final, cor_pulses_lna_final), axis = None)
                try:
                    #return np.row_stack( (self.convertion_to_numpy_pulser( self.pulse_array_pulser ), cor_pulses_amp_final, cor_pulses_lna_final))
                    # self.extending_rect_awg_pulser( self.pulse_array_pulser ) is for extendind RECT_AWG pulses
                    # see self.extending_rect_awg_pulser()
                    return np.row_stack( (self.extending_rect_awg_pulser( self.pulse_array_pulser ), cor_pulses_amp_final, cor_pulses_lna_final))

                # when we do not MW pulses at all
                except UnboundLocalError:
                    #return self.convertion_to_numpy_pulser( self.pulse_array_pulser )
                    return self.extending_rect_awg_pulser( self.pulse_array_pulser )

        elif self.test_flag == 'test':
            if self.auto_defense_pulser == 'False':
                split_pulse_array = self.splitting_acc_to_channel_pulser( self.convertion_to_numpy_pulser( np_array ) )

                # iterate over all pulses at different channels
                for index, element in enumerate(split_pulse_array):
                    # for all pulses just check 40 ns distance
                    self.check_problem_pulses_pulser(element)
                    # get assertion error if the distance < 40 ns
                    
                return self.convertion_to_numpy_pulser( np_array )

            elif self.auto_defense_pulser == 'True':
                awg_index = []
                mw_index = []
                shifted_back_awg_pulses = []

                split_pulse_array = self.splitting_acc_to_channel_pulser( self.convertion_to_numpy_pulser( np_array ) )

                for index, element in enumerate(split_pulse_array):
                    if element[0, 0] == 2**self.channel_dict_pulser['MW'] or element[0, 0] == 2**self.channel_dict_pulser['AWG']:

                        self.check_problem_pulses_pulser(element)

                        #if self.awg_pulses_pulser != 1:
                        #    # for MW pulses check 40 ns distance and add AMP_ON, LNA_PROTECT pulses
                        #    self.check_problem_pulses_pulser(element)
                        #else:
                        #    # for AWG we do not check 40 ns distance, since RECT_AWG will be extended in the same way as AMP_ON
                        #   for index_awg_mw, element_awg_mw in enumerate(element):
                        #        if element_awg_mw[0] == self.channel_dict_pulser['AWG']:
                        #            # shift back RECT_AWG to AWG
                        #            shifted_back_awg_pulses.append([element_awg_mw[0], element_awg_mw[1] + 0*int(self.rect_awg_switch_delay_pulser/self.timebase_pulser), \
                        #                element_awg_mw[2] + 0*int(self.rect_awg_switch_delay_pulser/self.timebase_pulser) - 0*int(self.rect_awg_switch_delay_pulser/self.timebase_pulser) - 0*int(self.rect_awg_delay_pulser/self.timebase_pulser)])
                        #
                        #            awg_index.append(index_awg_mw)
                        #
                        #        elif element_awg_mw[0] == self.channel_dict_pulser['MW']:
                        #            mw_index.append(index_awg_mw)
                        #
                        #
                        #    no_mw_element = np.delete( element, list(dict.fromkeys(mw_index)), axis = 0 ).tolist()
                        #    no_awg_element = np.delete( element, list(dict.fromkeys(awg_index)), axis = 0 ).tolist()
                        #    # if there is no MW
                        #    try:
                        #        shifted_back_awg_mw = np.concatenate((no_awg_element, shifted_back_awg_pulses), axis = 0)
                        #    except ValueError:
                        #        shifted_back_awg_mw = shifted_back_awg_pulses
                        #    
                        #    self.check_problem_pulses_pulser(no_awg_element)
                        #    # 09-10-2021 Commented next line for full AWG ESEEM
                        #    # uncomment in case of problems
                        #    self.check_problem_pulses_pulser(no_mw_element)
                        #    self.check_problem_pulses_pulser(shifted_back_awg_mw)

                            ##with open("test.out", "a") as f:
                            ##    np.savetxt(f, no_mw_element, delimiter=',', fmt = '%u') 
                            
                            ##f.close()

                        amp_on_pulses = self.add_amp_on_pulses_pulser(element)
                        lna_pulses = self.add_lna_protect_pulses_pulser(element)

                        # check AMP_ON, LNA_PROTECT pulses
                        cor_pulses_amp, prob_pulses_amp = self.check_problem_pulses_amp_lna_pulser(amp_on_pulses)
                        cor_pulses_lna, prob_pulses_lna = self.check_problem_pulses_amp_lna_pulser(lna_pulses)

                        # combining short distance AMP_ON pulses
                        if prob_pulses_amp[0][0] == 0:
                            cor_pulses_amp_final = cor_pulses_amp
                        elif cor_pulses_amp[0][0] == 0:
                            # nothing to concatenate
                            amp_on_pulses = self.convert_to_bit_pulse_amp_lna_pulser(prob_pulses_amp, self.channel_dict_pulser['AMP_ON'])
                            cor_pulses_amp_final = self.instruction_pulse_short_lna_amp_pulser(amp_on_pulses)
                        else:
                            amp_on_pulses = self.convert_to_bit_pulse_amp_lna_pulser(prob_pulses_amp, self.channel_dict_pulser['AMP_ON'])
                            try:
                                cor_pulses_amp_final = np.concatenate((cor_pulses_amp, self.instruction_pulse_short_lna_amp_pulser(amp_on_pulses)), axis = 0)
                            except ValueError:
                                cor_pulses_amp_final = np.concatenate((cor_pulses_amp, self.instruction_pulse_short_lna_amp_pulser(amp_on_pulses)), axis = 0)

                        # combining short distance LNA_PROTECT pulses
                        if prob_pulses_lna[0][0] == 0:
                            cor_pulses_lna_final = cor_pulses_lna
                        elif cor_pulses_lna[0][0] == 0:
                            # nothing to concatenate
                            lna_pulses = self.convert_to_bit_pulse_amp_lna_pulser(prob_pulses_lna, self.channel_dict_pulser['LNA_PROTECT'])
                            cor_pulses_lna_final =  self.instruction_pulse_short_lna_amp_pulser(lna_pulses)
                        else:
                            lna_pulses = self.convert_to_bit_pulse_amp_lna_pulser(prob_pulses_lna, self.channel_dict_pulser['LNA_PROTECT'])
                            cor_pulses_lna_final =  np.concatenate((cor_pulses_lna, self.instruction_pulse_short_lna_amp_pulser(lna_pulses)), axis = 0)

                    elif element[0, 0] == 2**self.channel_dict_pulser['-X'] or element[0, 0] == 2**self.channel_dict_pulser['+Y']:
                        # for phases pulses just check 10 ns distance
                        self.check_problem_pulses_phase_pulser(element)
                    else:
                        # for non-MW pulses just check 40 ns distance
                        self.check_problem_pulses_pulser(element)

                # combine all pulses
                #np.concatenate( (self.convertion_to_numpy_pulser( self.pulse_array_pulser ), cor_pulses_amp_final, cor_pulses_lna_final), axis = None) 
                try:
                    return np.row_stack( (self.extending_rect_awg_pulser( self.pulse_array_pulser ), cor_pulses_amp_final, cor_pulses_lna_final))
                except UnboundLocalError:
                    return self.extending_rect_awg_pulser( self.pulse_array_pulser )

    def split_into_parts_pulser(self, np_array, rep_time):
        """
        This function is adapted for using with Micran pulse generator instructions
        """
        if self.test_flag != 'test':
            answer = []
            min_list = []
            pulses = self.preparing_to_bit_pulse_pulser(np_array)

            sorted_pulses_start = np.asarray(sorted(pulses, key = lambda x: int(x[1])), dtype = np.int64)

            #LASER HERE
            # [[256 125 145] [  2 160 188] [  4 160 238] [  8 245 253] [  2 260 296] [  4 260 361] [ 16 330 361] [  8 345 361] [  1 455 505]]


            # self.max_pulse_length_pulser is 2000 ns now
            index_jump = np.where(np.diff(sorted_pulses_start[:,1], axis = 0) > int(self.max_pulse_length_pulser / self.timebase_pulser) )[0]
            sorted_arrays_parts = np.split(sorted_pulses_start, index_jump + 1)

            for index, element in enumerate(sorted_arrays_parts):
                temp, min_value = self.convert_to_bit_pulse_pulser(element)

                ###??????
                temp = np.concatenate((np.array([0]), temp), axis=None)

                answer.append(self.instruction_pulse_pulser(temp))
                # keep them all for further shifting
                min_list.append(min_value)
            # at this point we have different array for different interval:
            # I. E. [[[0, 0, 70], [6, 70, 200], [14, 270, 20], [4, 290, 100],\
            # [0, 390, 560], [1, 950, 20]], [[0, 0, 20000050], [6, 20000050, 200], [14, 20000250, 30], [4, 20000280, 100]]]

            # We should adjust the beginning of all sub array with index >= 1
            for index, element in enumerate(answer):
                # the first sub array is ok
                if index == 0:
                    pass
                elif index > 0:
                    # the second and further should be shifted using data from the previous sub array
                    shift_region = answer[index - 1][-1][1] + answer[index - 1][-1][2]
                    # sweep through sub array
                    for index2, element2 in enumerate(element):
                        # to take into account the jump region between two sub arrays
                        # - min_list[0]*self.timebase_pulser common shifting of the first pulse
                        if index2 == 0:
                            element2[1] = shift_region
                            element2[2] = min_list[index]*1 + element2[2] - shift_region - min_list[0]*1
                        elif index2 > 0:
                            element2[1] = element2[1] + min_list[index]*1 - min_list[0]*1
                            #element2[2] = min_list[index]*1 + element2[2] - shift_region - min_list[0]*1

                    #shift_region = element[-1][1] + element[-1][2]
                    #general.message(shift_region)

                        #general.message(element)
                        #element[0][1] = answer[index - 1][-1][1] + answer[index - 1][-1][2]
                        #element[0][2] = element[0][2] - element[0][1]

            # flatten list
            one_array = sum(answer, [])
            # append delay for repetition rate
            #one_array.append( [0, one_array[-1][1] + one_array[-1][2], \
            #    rep_time - one_array[-1][2] - one_array[-1][1]] )

            if int( rep_time / self.timebase_pulser ) - one_array[-1][2] - one_array[-1][1] > (self.min_pulse_length_pulser + 4):
                one_array.append( [0, one_array[-1][1] + one_array[-1][2], \
                    int( rep_time / self.timebase_pulser ) - one_array[-1][2] - one_array[-1][1]] )

                return one_array
            else:
                general.message('Pulse sequence is longer than one period of the repetition rate')
                sys.exit()

        elif self.test_flag == 'test':
            answer = []
            min_list = []
            pulses = self.preparing_to_bit_pulse_pulser(np_array)
            

            sorted_pulses_start = np.asarray(sorted(pulses, key = lambda x: int(x[1])), dtype = np.int64)
            # self.max_pulse_length_pulser is 2000 ns now
            index_jump = np.where(np.diff(sorted_pulses_start[:,1], axis = 0) > int(self.max_pulse_length_pulser / self.timebase_pulser) )[0]
            sorted_arrays_parts = np.split(sorted_pulses_start, index_jump + 1)

            for index, element in enumerate(sorted_arrays_parts):
                temp, min_value = self.convert_to_bit_pulse_pulser(element)
                temp = np.concatenate((np.array([0]), temp), axis=None)

                answer.append(self.instruction_pulse_pulser(temp))
                # keep them all for further shifting
                min_list.append(min_value)

            # We should adjust the beginning of all sub array with index >= 1
            for index, element in enumerate(answer):
                # the first sub array is ok
                if index == 0:
                    pass
                elif index > 0:
                    # the second and further should be shifted using data from the previous sub array
                    shift_region = answer[index - 1][-1][1] + answer[index - 1][-1][2]
                    # sweep through sub array
                    for index2, element2 in enumerate(element):
                        # to take into account the jump region between two sub arrays
                        if index2 == 0:
                            element2[1] = shift_region
                            element2[2] = min_list[index]*1+ element2[2] - shift_region - min_list[0]*1
                        elif index2 > 0:
                            element2[1] = element2[1] + min_list[index]*1 - min_list[0]*1
                        
                    #shift_region = element[-1][1] + element[-1][2]
                    #general.message(shift_region)

                        #general.message(element)
                        #element[0][1] = answer[index - 1][-1][1] + answer[index - 1][-1][2]
                        #element[0][2] = element[0][2] - element[0][1]

            one_array = sum(answer, [])

            if int( rep_time / self.timebase_pulser ) - one_array[-1][2] - one_array[-1][1] > (self.min_pulse_length_pulser + 4):
                one_array.append( [0, one_array[-1][1] + one_array[-1][2], \
                    int( rep_time / self.timebase_pulser ) - one_array[-1][2] - one_array[-1][1]] )
                return one_array
            else:
                assert(1 == 2), 'Pulse sequence is longer than one period of the repetition rate'             

    def convert_to_bit_pulse_pulser(self, np_array):
        """
        A function to calculate in which time interval
        two or more different channels are on.
        All the pulses converted in an bit_array of 0 and 1, where
        1 corresponds to the time interval when the channel is on.
        The size of the bit_array is determined by the total length
        of the full pulse sequence.
        Finally, a bit_array is multiplied by a ch in order to
        calculate CH instructions.

        It is optimized for using at subarrays inside split_into_parts_pulser()
        """

        if self.test_flag != 'test':
            #pulses = self.preparing_to_bit_pulse_pulser(np_array)
            pulses = np_array
            max_pulse = np.amax(pulses[:,2])
            # we get rid of constant shift in the first pulse, since
            # it is useless in terms of pulse bluster instructions
            # the first pulse in sequence will start at 50 ns all other shifted accordingly
            # this value can be adjust by add_shift_pulser parameter (multiplited by self.timebase_pulser)
            min_pulse = np.amin(pulses[:,1]) - self.add_shift_pulser

            bit_array = np.zeros( max_pulse - min_pulse, dtype = np.int64 )

            i = 0
            while i < len(pulses):
                # convert each pulse in an array of 0 and 1,
                # 1 corresponds to the time interval, where the channel is on
                translation_array = pulses[i, 0]*np.concatenate( (np.zeros( pulses[i, 1] - min_pulse, dtype = np.int64), \
                        np.ones(pulses[i, 2] - pulses[i, 1], dtype = np.int64), \
                        np.zeros(max_pulse - pulses[i, 2], dtype = np.int64)), axis = None)
                
                # summing arrays for each pulse into the finalbit_array
                bit_array = bit_array + translation_array

                # ITC bridge with two syntetizer
                # AWG channel uses synt2 as default
                # we need to add a pulse
                # RECT/AWG pulse: pulses[i, 0] == 2**7
                #if self.synt_number == 1 and pulses[i, 0] == 2**7:
                #    bit_array = bit_array + 2**self.channel_dict_pulser[self.ch9]*np.concatenate( (np.zeros( pulses[i, 1] - min_pulse + self.synt2_shift, dtype = np.int64), \
                #        np.ones(pulses[i, 2] - pulses[i, 1] + self.synt2_ext, dtype = np.int64), \
                #        np.zeros(max_pulse - pulses[i, 2] - self.synt2_shift - self.synt2_ext, dtype = np.int64)), axis = None)

                i += 1

            return bit_array, min_pulse

        elif self.test_flag == 'test':
            #pulses = self.preparing_to_bit_pulse_pulser(np_array)
            pulses = np_array

            max_pulse = np.amax(pulses[:,2])
            min_pulse = np.amin(pulses[:,1]) - self.add_shift_pulser

            bit_array = np.zeros( max_pulse - min_pulse, dtype = np.int64 )
            
            i = 0
            while i < len(pulses):
                # convert each pulse in an array of 0 and 1,
                # 1 corresponds to the time interval, where the channel is on
                translation_array = pulses[i, 0]*np.concatenate( (np.zeros( pulses[i, 1] - min_pulse, dtype = np.int64), \
                        np.ones(pulses[i, 2] - pulses[i, 1], dtype = np.int64), \
                        np.zeros(max_pulse - pulses[i, 2], dtype = np.int64)), axis = None)
                
                # summing arrays for each pulse into the finalbit_array
                bit_array = bit_array + translation_array

                # ITC bridge with two syntetizer
                # AWG channel uses synt2 as default
                # we need to add a pulse
                # RECT/AWG pulse: pulses[i, 0] == 2**7
                #if self.synt_number == 1 and pulses[i, 0] == 2**7:
                #    bit_array = bit_array + 2**self.channel_dict_pulser[self.ch9]*np.concatenate( (np.zeros( pulses[i, 1] - min_pulse + self.synt2_shift, dtype = np.int64), \
                #        np.ones(pulses[i, 2] - pulses[i, 1] + self.synt2_ext, dtype = np.int64), \
                #        np.zeros(max_pulse - pulses[i, 2] - self.synt2_shift - self.synt2_ext, dtype = np.int64)), axis = None)

                i += 1

            return bit_array, min_pulse

    def convert_to_bit_pulse_visualizer_pulser(self, np_array):
        """
        The same function optimized for using in pulser_visualize()
        in which we DO NOT split all area into subarrays if 
        there are > 2000 ns distance between pulses
        
        A constant shift in the first pulse is omitted

        Note that this function provides a different treatment of
        pulse sequence. It order to check what EXACTLY we havw after
        convert_to_bit_pulse_pulser() use convert_to_bit_pulse_visualizer_final_instructions()
        """

        if self.test_flag != 'test':
            pulses = self.preparing_to_bit_pulse_pulser(np_array)
            #pulses = np_array
            #for index, element in enumerate(pulses):
            #    element[2] = element[1] + element[2]  
            max_pulse = np.amax(pulses[:,2])
            min_pulse = np.amin(pulses[:,1])

            #bit_array = np.zeros( 2*(max_pulse - min_pulse), dtype = np.int64 )
            bit_array_pulses = []

            i = 0
            while i < len(pulses):
                # convert each pulse in an array of 0 and 1,
                # 1 corresponds to the time interval, where the channel is on
                if pulses[i, 0] != 0:

                    translation_array = pulses[i, 0]*np.concatenate( (np.zeros( 1*(pulses[i, 1] - min_pulse), dtype = np.int64), \
                        np.ones(1*(pulses[i, 2] - pulses[i, 1]), dtype = np.int64), \
                        np.zeros(1*(max_pulse - pulses[i, 2]), dtype = np.int64)), axis = None)
                
                    # appending each pulses individually
                    bit_array_pulses.append(translation_array)

                    # ITC bridge with two syntetizer
                    # AWG channel uses synt2 as default
                    # we need to add a pulse
                    # RECT/AWG pulse: pulses[i, 0] == 2**7
                    #if self.synt_number == 1 and pulses[i, 0] == 2**7:

                    #    translation_array = 2**self.channel_dict_pulser[self.ch9]*np.concatenate( (np.zeros( 1*(pulses[i, 1] - min_pulse + self.synt2_shift), dtype = np.int64), \
                    #        np.ones(1*(pulses[i, 2] - pulses[i, 1] + self.synt2_ext), dtype = np.int64), \
                    #        np.zeros(1*(max_pulse - pulses[i, 2] - self.synt2_shift - self.synt2_ext), dtype = np.int64)), axis = None)
                    #    bit_array_pulses.append(translation_array)

                i += 1

            return bit_array_pulses

        elif self.test_flag == 'test':
            pulses = self.preparing_to_bit_pulse_pulser(np_array)
            #pulses = np_array
            #for index, element in enumerate(pulses):
            #    element[2] = element[1] + element[2]  

            max_pulse = np.amax(pulses[:,2])
            min_pulse = np.amin(pulses[:,1])

            #bit_array = np.zeros( max_pulse - 0*min_pulse, dtype = np.int64 )
            bit_array_pulses = []

            i = 0
            while i < len(pulses):
                # convert each pulse in an array of 0 and 1,
                # 1 corresponds to the time interval, where the channel is on
                if pulses[i, 0] != 0:

                    translation_array = pulses[i, 0]*np.concatenate( (np.zeros( pulses[i, 1] - min_pulse, dtype = np.int64), \
                        np.ones(pulses[i, 2] - pulses[i, 1], dtype = np.int64), \
                        np.zeros(max_pulse - pulses[i, 2], dtype = np.int64)), axis = None)
                
                    # summing arrays for each pulse into the finalbit_array
                    bit_array_pulses.append(translation_array)


                    # ITC bridge with two syntetizer
                    # AWG channel uses synt2 as default
                    # we need to add a pulse
                    # RECT/AWG pulse: pulses[i, 0] == 2**7
                    #if self.synt_number == 1 and pulses[i, 0] == 2**7:
                    #    
                    #    translation_array = 2**self.channel_dict_pulser[self.ch9]*np.concatenate( (np.zeros( 1*(pulses[i, 1] - min_pulse + self.synt2_shift), dtype = np.int64), \
                    #        np.ones(1*(pulses[i, 2] - pulses[i, 1] + self.synt2_ext), dtype = np.int64), \
                    #        np.zeros(1*(max_pulse - pulses[i, 2] - self.synt2_shift - self.synt2_ext), dtype = np.int64)), axis = None)
                    #    bit_array_pulses.append(translation_array)


                i += 1

            return bit_array_pulses

    def convert_to_bit_pulse_visualizer_final_instructions_pulser(self, np_array):
        """
        The same function optimized for using in pulser_visualize()
        in which we DO NOT split all area into subarrays if 
        there are > 2000 ns distance between pulses
        
        A constant shift in the first pulse is omitted.

        It is shown exactly the pulses we will have after convert_to_bit_pulse_pulser()

        Please note that channel numbers will be already joined if two channels are turned on
        simultaneously
        """

        if self.test_flag != 'test':
            #pulses = self.preparing_to_bit_pulse_pulser(np_array)
            pulses = np_array
            # convert back to channel, start, end
            # from channel, start, length
            for index, element in enumerate(pulses):
                element[2] = element[1] + element[2]  

            max_pulse = np.amax(pulses[:,2])
            min_pulse = np.amin(pulses[:,1]) - self.add_shift_pulser*0

            bit_array = np.zeros( max_pulse - min_pulse, dtype = np.int64 )
            bit_array_pulses = []

            i = 0
            while i < len(pulses):
                # convert each pulse in an array of 0 and 1,
                # 1 corresponds to the time interval, where the channel is on
                if pulses[i, 0] != 0:
                    translation_array = pulses[i, 0]*np.concatenate( (np.zeros( pulses[i, 1] - min_pulse, dtype = np.int64), \
                        np.ones(pulses[i, 2] - pulses[i, 1], dtype = np.int64), \
                        np.zeros(max_pulse - pulses[i, 2], dtype = np.int64)), axis = None)
                
                    # appending each pulses individually
                    bit_array_pulses.append(translation_array)

                i += 1

            return bit_array_pulses

        elif self.test_flag == 'test':
            #pulses = self.preparing_to_bit_pulse_pulser(np_array)
            pulses = np_array
            for index, element in enumerate(pulses):
                element[2] = element[1] + element[2]  

            max_pulse = np.amax(pulses[:,1])
            min_pulse = np.amin(pulses[:,1]) - self.add_shift_pulser*0

            bit_array = np.zeros( max_pulse - min_pulse, dtype = np.int64 )
            bit_array_pulses = []

            i = 0
            while i < len(pulses):
                # convert each pulse in an array of 0 and 1,
                # 1 corresponds to the time interval, where the channel is on
                if pulses[i, 0] != 0:
                    translation_array = pulses[i, 0]*np.concatenate( (np.zeros( pulses[i, 1] - min_pulse, dtype = np.int64), \
                        np.ones(pulses[i, 2] - pulses[i, 1], dtype = np.int64), \
                        np.zeros(max_pulse - pulses[i, 2], dtype = np.int64)), axis = None)
                
                # summing arrays for each pulse into the finalbit_array
                    bit_array_pulses.append(translation_array)

                i += 1

            return bit_array_pulses

    def instruction_pulse_pulser(self, np_array):
        """
        Final convertion to the pulse blaster instruction pulses
        It splits the bit_array into sequence of bit_arrays for individual pulses
        After that convert them into instructions [channel, start, length]
        
        Bit array should not start with nonzero elements

        It is used inside convert_to_bit_pulse_pulser()
        """
        if self.test_flag != 'test':
            final_pulse_array = []

            # Create an array that is 1 where a is 0, and pad each end with an extra 0.
            iszero = np.concatenate(([0], np_array, [0]))
            absdiff = np.abs(np.diff(iszero))

            # creating a mask to split bit array
            ranges = np.where(absdiff != 0)[0]
            # using a mask
            pulse_array_pulser = np.split(np_array, ranges)
            pulse_info = np.concatenate(([0], ranges))

            # return back self.timebase_pulser; convert to instructions
            for index, element in enumerate(pulse_info[:-1]):
                final_pulse_array.append( [pulse_array_pulser[index][0], 1*pulse_info[index], 1*(pulse_info[index + 1] - pulse_info[index])] )

            return final_pulse_array

        elif self.test_flag == 'test':
            final_pulse_array = []

            # Create an array that is 1 where a is 0, and pad each end with an extra 0.
            iszero = np.concatenate(([0], np_array, [0]))
            absdiff = np.abs(np.diff(iszero))
            
            ranges = np.where(absdiff != 0)[0]
            pulse_array_pulser = np.split(np_array, ranges)
            pulse_info = np.concatenate(([0], ranges))

            for index, element in enumerate(pulse_info[:-1]):
                final_pulse_array.append( [pulse_array_pulser[index][0], 1*pulse_info[index], 1*(pulse_info[index + 1] - pulse_info[index])] )

            return final_pulse_array

    def add_amp_on_pulses_pulser(self, p_list):
        """
        A function that automatically add AMP_ON pulses with corresponding delays
        specified by switch_delay and amp_delay_pulser
        """
        if self.test_flag != 'test':
            if self.auto_defense_pulser == 'False':
                pass
            elif self.auto_defense_pulser == 'True':
                amp_on_list = []
                # for dealing with overlap of RECT_AWG pulse with MW; RECT_AWG should behaves the same as AMP_ON
                for index, element in enumerate(p_list):
                    if element[0] == 2**(self.channel_dict_pulser['MW']):
                        amp_on_list.append( [2**(self.channel_dict_pulser['AMP_ON']), element[1] - self.switch_delay_pulser, element[2] + self.amp_delay_pulser] )
                        #amp_on_list.append( [self.channel_dict_pulser['SHAPER'], element[1] - self.switch_shaper_delay, element[2] + self.shaper_delay] )
                    # AMP_ON and RECT_AWG coincide now
                    elif element[0] == 2**(self.channel_dict_pulser['AWG']):
                        amp_on_list.append( [2**(self.channel_dict_pulser['AMP_ON']), element[1] - self.switch_delay_pulser, element[2] + self.amp_delay_pulser] )
                        #amp_on_list.append( [self.channel_dict_pulser['SHAPER'], element[1] - self.switch_shaper_delay, element[2] + self.shaper_delay] )
                    else:
                        pass

                return np.asarray(amp_on_list)

        elif self.test_flag == 'test':
            if self.auto_defense_pulser == 'False':
                pass
            elif self.auto_defense_pulser == 'True':
                amp_on_list = []

                for index, element in enumerate(p_list):
                    if element[0] == 2**(self.channel_dict_pulser['MW']):
                        if (element[2] + self.amp_delay_pulser) - (element[1] - self.switch_delay_pulser) <= self.max_pulse_length_pulser:
                            amp_on_list.append( [2**(self.channel_dict_pulser['AMP_ON']), element[1] - self.switch_delay_pulser, element[2] + self.amp_delay_pulser] )
                            #amp_on_list.append( [self.channel_dict_pulser['SHAPER'], element[1] - self.switch_shaper_delay, element[2] + self.shaper_delay] )
                        else:
                            assert(1 == 2), 'Maximum available length (4980 ns) for AMP_ON pulse is reached'
                    # AMP_ON and RECT_AWG coincide now
                    elif element[0] == 2**(self.channel_dict_pulser['AWG']):
                        if element[2] - element[1]  <= self.max_pulse_length_pulser/2:
                            amp_on_list.append( [2**(self.channel_dict_pulser['AMP_ON']), element[1] - self.switch_delay_pulser, element[2] + self.amp_delay_pulser] )
                            #amp_on_list.append( [self.channel_dict_pulser['SHAPER'], element[1] - self.switch_shaper_delay, element[2] + self.shaper_delay] )
                        else:
                            assert(1 == 2), 'Maximum available length (4980 ns) for AMP_ON pulse is reached'

                    else:
                        pass

                return np.asarray(amp_on_list)

    def add_lna_protect_pulses_pulser(self, p_list):
        """
        A function that automatically add LNA_PROTECT and HPA_PROTECT pulses with corresponding delays
        specified by switch_delay_pulser and protect_delay_pulser
        """
        if self.test_flag != 'test':
            if self.auto_defense_pulser == 'False':
                pass
            elif self.auto_defense_pulser == 'True':
                lna_protect_list = []
                for index, element in enumerate(p_list):
                    if element[0] == 2**(self.channel_dict_pulser['MW']):
                        lna_protect_list.append( [2**(self.channel_dict_pulser['LNA_PROTECT']), element[1] - self.switch_protect_delay_pulser, element[2] + self.protect_delay_pulser] )
                        #lna_protect_list.append( [self.channel_dict_pulser['VIDEO_PROTECT'], element[1] - self.switch_protect_delay_pulser, element[2] + self.protect_delay_pulser] )
                    # LNA_PROTECT and RECT_AWG coincide in the start position but LNA is longer at protect_delay_pulser
                    elif element[0] == 2**(self.channel_dict_pulser['AWG']):
                        lna_protect_list.append( [2**(self.channel_dict_pulser['LNA_PROTECT']), element[1] - self.switch_protect_delay_pulser, element[2] - int(self.rect_awg_delay_pulser/self.timebase_pulser) + self.protect_awg_delay_pulser] )
                        #lna_protect_list.append( [self.channel_dict_pulser['VIDEO_PROTECT'], element[1] - self.switch_protect_delay_pulser, element[2] - int(self.rect_awg_delay_pulser/self.timebase_pulser) + self.protect_awg_delay_pulser] )
                    else:
                        pass

            return np.asarray(lna_protect_list)

        elif self.test_flag == 'test':
            if self.auto_defense_pulser == 'False':
                pass
            elif self.auto_defense_pulser == 'True':
                lna_protect_list = []
                for index, element in enumerate(p_list):
                    if element[0] == 2**(self.channel_dict_pulser['MW']):
                        lna_protect_list.append( [2**(self.channel_dict_pulser['LNA_PROTECT']), element[1] - self.switch_protect_delay_pulser, element[2] + self.protect_delay_pulser] )
                        #lna_protect_list.append( [self.channel_dict_pulser['VIDEO_PROTECT'], element[1] - self.switch_protect_delay_pulser, element[2] + self.protect_delay_pulser] )
                    # LNA_PROTECT and RECT_AWG coincide in the start position but LNA is longer at protect_delay_pulser
                    elif element[0] == 2**(self.channel_dict_pulser['AWG']):
                        lna_protect_list.append( [2**(self.channel_dict_pulser['LNA_PROTECT']), element[1] - self.switch_protect_delay_pulser, element[2] - int(self.rect_awg_delay_pulser/self.timebase_pulser) + self.protect_awg_delay_pulser] )
                        #lna_protect_list.append( [self.channel_dict_pulser['VIDEO_PROTECT'], element[1] - self.switch_protect_delay_pulser, element[2] - int(self.rect_awg_delay_pulser/self.timebase_pulser) + self.protect_awg_delay_pulser] )
                    else:
                        pass

                return np.asarray(lna_protect_list)

    def check_problem_pulses_amp_lna_pulser(self, p_list):
        """
        A function for checking whether there is a two
        close to each other AMP_ON or LNA_PROTECT pulses (less than 12 ns)
        If so pulse array is splitted into the problematic part and correct part

        Returns both specified parts for further convertion in shich problematic part
        are joined using check_short_pulses_pulser() and joining_pulses_pulser()
        """
        if self.test_flag != 'test':
            if self.auto_defense_pulser == 'False':
                pass
            elif self.auto_defense_pulser == 'True':
                problem_list = []
                # memorize index of problem elements
                problem_index = []
                # numpy arrays don't support element deletion
                no_problem_list = deepcopy(p_list.tolist())

                # there STILL can be errors
                # now compare two pulses with I and I+2 indexes, since there are two pulses SHAPER and AMP_ON; LNA_PROTECT and VIDEO_PROTECT
                # (end and start + 1)
                for index, element in enumerate(p_list[:-1]):

                    # minimal_distance_amp_lna_pulser is 0 ns now
                    if p_list[index + 1][1] - element[2] < self.minimal_distance_amp_lna_pulser:
                        problem_list.append(element)
                        problem_list.append(p_list[index + 1])
                        # memorize indexes of the problem pulses
                        problem_index.append(index)
                        problem_index.append(index + 1)

                # delete duplicates in the index list: list(dict.fromkeys(problem_index)) )
                # delete problem pulses from no_problem_list
                # np.delete( no_problem_list, list(dict.fromkeys(problem_index)), axis = 0 ).tolist() )
                no_problem_list = np.delete( no_problem_list, list(dict.fromkeys(problem_index)), axis = 0 ).tolist()

                # for not returning an empty list
                # the same conditions are used in preparing_to_bit_pulse_pulser()
                if len(problem_list) == 0:
                    return self.delete_duplicates_pulser(np.asarray(no_problem_list)), np.array([[0]])
                elif len(no_problem_list) == 0:
                    return np.array([[0]]), self.delete_duplicates_pulser(np.asarray(problem_list))
                else:
                    return self.delete_duplicates_pulser(np.asarray(no_problem_list)), self.delete_duplicates_pulser(np.asarray(problem_list))

        elif self.test_flag == 'test':
            if self.auto_defense_pulser == 'False':
                pass
            elif self.auto_defense_pulser == 'True':            
                problem_list = []
                problem_index = []
                # numpy arrays don't support element deletion
                no_problem_list = deepcopy(p_list.tolist())

                for index, element in enumerate(p_list[:-1]):
                    # minimal_distance_amp_lna_pulser is 0 ns now
                    if p_list[index + 1][1] - element[2] < (self.minimal_distance_amp_lna_pulser):
                        problem_list.append(element)
                        problem_list.append(p_list[index + 1])
                        # memorize indexes of the problem pulses
                        problem_index.append(index)
                        problem_index.append(index + 1)

                no_problem_list = np.delete( no_problem_list, list(dict.fromkeys(problem_index)), axis = 0 ).tolist()

                if len(problem_list) == 0:
                    return self.delete_duplicates_pulser(np.asarray(no_problem_list)), np.array([[0]])
                elif len(no_problem_list) == 0:
                    return np.array([[0]]), self.delete_duplicates_pulser(np.asarray(problem_list))
                else:
                    return self.delete_duplicates_pulser(np.asarray(no_problem_list)), self.delete_duplicates_pulser(np.asarray(problem_list))

    def convert_to_bit_pulse_amp_lna_pulser(self, p_list, channel):
        """
        A function to calculate in which time interval
        two or more different channels are on.
        All the pulses converted in an bit_array of 0 and 1, where
        1 corresponds to the time interval when the channel is on.
        The size of the bit_array is determined by the total length
        of the full pulse sequence.
        Finally, a bit_array is multiplied by a ch in order to
        calculate CH instructions for SpinAPI.
        
        It is used to check (check_short_pulses_pulser()) whether there are two AMP_ON or LNA_PROTECT pulses
        with the distanse less than 12 ns between them
        If so they are combined in one pulse by joining_pulses_pulser()

        Generally, this function is close to convert_to_bit_pulse_pulser() and other convertion
        functions
        """
        if self.test_flag != 'test':
            if self.auto_defense_pulser == 'False':
                pass
            elif self.auto_defense_pulser == 'True':
                max_pulse = np.amax(p_list[:,2])
                bit_array = np.zeros(max_pulse, dtype = np.int64)
                #bit_array2 = np.zeros(max_pulse, dtype = np.int64)
                # two types of pulses: AMP_ON and SHAPER; LNA_PROTECT and VIDEO_PROTECT
                #first_channel = p_list[1, 0]
                i = 0
                while i < len(p_list):
                    # convert each pulse in an array of 0 and 1,
                    # 1 corresponds to the time interval, where the channel is on
                    translation_array = np.concatenate( (np.zeros(p_list[i, 1], dtype = np.int64), \
                            np.ones(p_list[i, 2] - p_list[i, 1], dtype = np.int64), \
                            np.zeros(max_pulse - p_list[i, 2], dtype = np.int64)), axis = None)

                    bit_array = bit_array | translation_array

                    #if p_list[i, 0] == first_channel:
                    #    bit_array = bit_array | translation_array
                    #else:
                    #    second_channel = p_list[i, 0]
                    #    bit_array2 = bit_array2 | translation_array

                    i += 1

                bit_array = 2**(channel)*self.check_short_pulses_pulser(bit_array, channel)
                #bit_array = (first_channel)*self.check_short_pulses_pulser(bit_array, first_channel)
                #try:
                #    bit_array2 = (second_channel)*self.check_short_pulses_pulser(bit_array2, second_channel)
                #except UnboundLocalError:
                #    return bit_array, bit_array2

                return bit_array#, bit_array2

        elif self.test_flag == 'test':
            if self.auto_defense_pulser == 'False':
                pass
            elif self.auto_defense_pulser == 'True':            
                max_pulse = np.amax(p_list[:,2])
                bit_array = np.zeros(max_pulse, dtype = np.int64)
                #bit_array2 = np.zeros(max_pulse, dtype = np.int64)
                # two types of pulses: AMP_ON and SHAPER; LNA_PROTECT and VIDEO_PROTECT
                #first_channel = p_list[1, 0]
                i = 0
                while i < len(p_list):
                    # convert each pulse in an array of 0 and 1,
                    # 1 corresponds to the time interval, where the channel is on
                    translation_array = np.concatenate( (np.zeros(p_list[i, 1], dtype = np.int64), \
                            np.ones(p_list[i, 2] - p_list[i, 1], dtype = np.int64), \
                            np.zeros(max_pulse - p_list[i, 2], dtype = np.int64)), axis = None)

                    bit_array = bit_array | translation_array

                    #if p_list[i, 0] == first_channel:
                    #    bit_array = bit_array | translation_array
                    #else:
                    #    second_channel = p_list[i, 0]
                    #    bit_array2 = bit_array2 | translation_array

                    i += 1

                bit_array = 2**(channel)*self.check_short_pulses_pulser(bit_array, channel)

                #bit_array = (first_channel)*self.check_short_pulses_pulser(bit_array, first_channel)
                #try:
                #    bit_array2 = (second_channel)*self.check_short_pulses_pulser(bit_array2, second_channel)
                #except UnboundLocalError:
                #    return bit_array, bit_array2

                return bit_array#, bit_array2

    def instruction_pulse_short_lna_amp_pulser(self, np_array):
        """
        Final convertion to the pulse blaster instruction pulses
        It splits the bit_array into sequence of bit_arrays for individual pulses
        after that converts them into instructions

        We can drop pulses with channel 0 for AMP_ON and LNA_PROTECT case

        Generally, this function is close to instruction_pulse_pulser() 
        """
        if self.test_flag != 'test':
            if self.auto_defense_pulser == 'False':
                pass
            elif self.auto_defense_pulser == 'True':
                final_pulse_array = []

                # Create an array that is 1 where a is 0, and pad each end with an extra 0.
                iszero = np.concatenate(([0], np_array, [0]))
                absdiff = np.abs(np.diff(iszero))

                # creating a mask to split bit array
                ranges = np.where(absdiff != 0)[0]
                # split using a mask
                pulse_array_pulser = np.split(np_array, ranges)
                pulse_info = np.concatenate(([0], ranges))

                for index, element in enumerate(pulse_info[:-1]):
                    # we can drop pulses with channel 0 for AMP_ON and LNA_PROTECT case
                    if pulse_array_pulser[index][0] != 0:
                        final_pulse_array.append( [pulse_array_pulser[index][0], pulse_info[index], pulse_info[index + 1]] )
                    else:
                        pass

                return final_pulse_array

        elif self.test_flag == 'test':
            if self.auto_defense_pulser == 'False':
                pass
            elif self.auto_defense_pulser == 'True':
                final_pulse_array = []

                # Create an array that is 1 where a is 0, and pad each end with an extra 0.
                iszero = np.concatenate(([0], np_array, [0]))
                absdiff = np.abs(np.diff(iszero))

                ranges = np.where(absdiff != 0)[0]
                pulse_array_pulser = np.split(np_array, ranges)
                pulse_info = np.concatenate(([0], ranges))

                for index, element in enumerate(pulse_info[:-1]):
                    if pulse_array_pulser[index][0] != 0:
                        final_pulse_array.append( [pulse_array_pulser[index][0], pulse_info[index], pulse_info[index + 1]] )
                    else:
                        pass

                return final_pulse_array

    def check_short_pulses_pulser(self, np_array, channel):
        """
        A function for checking whether there is two pulses with
        the distance between them shorter than 40 ns

        If there are such pulses on MW channel an error will be raised
        LNA_PROTECT and AMP_ON pulsess will be combined in one pulse

        """
        if self.test_flag != 'test':
            # checking where the pulses are
            one_indexes = np.argwhere(np_array == 1).flatten()
            difference = np.diff(one_indexes)
            
            ## 16-09-2021; An attempt to optimize the speed; all pulses should be already checked in the TEST RUN
            ## Uncomment everything starting with ## if needed
            if channel == self.channel_dict_pulser['LNA_PROTECT'] or channel == self.channel_dict_pulser['AMP_ON']:
            ##if channel != self.channel_dict_pulser['LNA_PROTECT'] and channel != self.channel_dict_pulser['AMP_ON']:

            ##    # (min_pulse_length_pulser + 1) is 13 now
            ##    if any(1 < element < (self.min_pulse_length_pulser + 1) for element in difference) == False:
            ##        pass
            ##    else:
            ##        general.message('There are two pulses with shorter than ' + str(self.min_pulse_length_pulser*2) + ' ns distance between them')
            ##        sys.exit()
            ##else:
                if any(1 < element < (self.min_pulse_length_pulser + self.minimal_distance_amp_lna_pulser) for element in difference) == False:
                    return np_array
                else:
                    final_array = self.joining_pulses_pulser(np_array)
                    return final_array

        if self.test_flag == 'test':
            # checking where the pulses are
            one_indexes = np.argwhere(np_array == 1).flatten()
            difference = np.diff(one_indexes)

            if channel != self.channel_dict_pulser['LNA_PROTECT'] and channel != self.channel_dict_pulser['AMP_ON']:
                if any(1 < element < (self.min_pulse_length_pulser + self.minimal_distance_amp_lna_pulser) for element in difference) == False:
                    pass
                else:
                    assert(1 == 2), 'There are two pulses with shorter than ' + str(self.min_pulse_length_pulser) + ' ns distance between them'
            else:
                if any(1 < element < (self.min_pulse_length_pulser + self.minimal_distance_amp_lna_pulser) for element in difference) == False:
                    return np_array
                else:
                    final_array = self.joining_pulses_pulser(np_array)
                    return final_array
    
    def joining_pulses_pulser(self, np_array):
        """
        A function that joing two short pulses in one
        It is used for LNA_PROTECT and AMP_ON pulses
        """
        i = 0
        j = 0
        counter = 0

        array_len = len(np_array)
        # drop several first and last zeros
        index_first_one = np.argwhere(np_array == 1)[0]
        index_last_one = np.argwhere(np_array == 1)[-1]
        short_array = np_array[index_first_one[0]:(index_last_one[0] + 1)]

        while i < len(short_array):
            if short_array[i] == 0:
                # looking for several 0 in a row
                if short_array[i + 1] == 0:
                    counter += 1
                elif short_array[i + 1] == 1:
                    # (minimal_distance + 1) is 13 now
                    if counter < (self.min_pulse_length_pulser + self.minimal_distance_amp_lna_pulser):
                        # replace 0 with 1
                        while j <= counter:
                            short_array[i + j - counter] = 1
                            j += 1
                        counter = 0
                        j = 0
                    else:
                        counter = 0

            i += 1

        final_array = np.concatenate( (np.zeros(index_first_one[0], dtype = np.int64), short_array, \
            np.zeros( array_len - index_last_one[0] - 1, dtype = np.int64)), axis = None)

        return final_array

    def change_pulse_settings_pulser(self, parameter, delay):
        """
        A special function for parsing some parameter (i.e. start, length) value from the pulse
        and changing them according to specified delay

        It is used in phase cycling
        """
        if self.test_flag != 'test':
            temp = parameter.split(' ')
            if temp[1] in self.timebase_dict:
                flag = self.timebase_dict[temp[1]]
                par_st = int(float((temp[0]))*flag + delay)
                new_parameter = str( par_st ) + ' ns'

            return new_parameter

        elif self.test_flag == 'test':
            temp = parameter.split(' ')
            if temp[1] in self.timebase_dict:
                flag = self.timebase_dict[temp[1]]
                par_st = int(float((temp[0]))*flag + delay)
                new_parameter = str( par_st ) + ' ns'
            else:
                assert(1 == 2), 'Incorrect time dimension (ns, us, ms, s)'

            return new_parameter

    def power_of_two_pulser(self, value):
        powers = []
        i = 1

        while i <= value:
            if i & value:
                powers.append( i )
            i <<= 1

        return np.log2( powers ).astype(int)

    def round_to_closest(self, x, y):
        """
        A function to round x to divisible by y
        """
        return round(( y * ( ( x // y ) + (round(x % y, 2) > 0) ) ), 1)

    def gen_GIM_words(self, spinapi):
        """
        A function to create GIM words from old PB_ESR_Pro instructions
        """
        sa = np.array(spinapi)
        
        range_time           = sa[1:,-1]
        range_time_tail      = range_time >> 16
        range_time           = range_time - (range_time_tail << 16)

        qqq                  = sa[1:,0]
        qqq[-1]              = qqq[-1] + (1 << 15)

        zer                  = np.zeros( (len(qqq), 8) , dtype = np.uint32 )
        zer[:,0] , zer[:,1]  = ((range_time << 16) +  qqq ), ( range_time_tail << 0)
        kk                   = zer.reshape(len(qqq) * 8).copy()

        self.data_buf_IP_GIM_brd = len(kk) , kk.ctypes.data_as( ctypes.POINTER( ctypes.c_int32 ) )

    def awg_update_test(self):
        """
        Function that can be used for tests instead of awg_update()
        """
        if self.test_flag != 'test':
            if self.reset_count_awg == 0 or self.shift_count_awg == 1 or self.increment_count_awg == 1 or self.setting_change_count_awg == 1:
                buf1, buf2 = self.define_buffer_single_joined_awg()
                #general.message( buf1 )
                xs = 0.8 * np.arange(len(buf1))
                general.plot_1d('Buffer_single', xs, (buf1, buf2), label = 'ch0 or ch1')
                
                #self.reset_count_awg = 1
                #self.shift_count_awg = 0
                #self.increment_count_awg = 0
                #self.setting_change_count_awg = 0

            else:
                pass

        elif self.test_flag == 'test':

            if self.reset_count_awg == 0 or self.shift_count_awg == 1 or self.increment_count_awg == 1 or self.setting_change_count_awg == 1:
                buf = self.define_buffer_single_joined_awg()[0]

                #self.reset_count_awg = 1
                #self.shift_count_awg = 0
                #self.increment_count_awg = 0
                #self.setting_change_count_awg = 0

            else:
                pass

    def convertion_to_numpy_awg(self, p_array):
        """
        Convertion of the pulse_array into numpy array in the form of
        [channel_number, function, frequency, phase, length, sigma, start, delta_start, amp]
        channel_number is from self.channel_dict_awg
        function is from self.function_dict_awg
        frequency is a pulse frequency in MHz; or a tuple (center_freq, sweep_freq) for WURST pulse
        phase is a pulse phase in rad
        length is a pulse length in sample rate
        sigma is a pulse sigma in sample rate
        start is a pulse start in sample rate forjoined pulses in 'Single'
        delta_start is a pulse delta start in sample rate forjoined pulses in 'Single'
        amp is an additional amplification coefficient to adjust pulse amplitudes
        n is a special coefficient for WURST and SECH/TANH pulses determining the steepness of the amplitude function
        b (in ns^-1); special coefficient for SECH/TANH pulse determining the truncation parameter

        The numpy array is sorted according to channel number
        """
        if self.test_flag != 'test':
            i = 0
            pulse_temp_array = []
            num_pulses = len( p_array )
            while i < num_pulses:
                # get channel number
                ch = p_array[i]['channel']
                if ch in self.channel_dict_awg:
                    ch_num = self.channel_dict_awg[ch]

                # get function
                fun = p_array[i]['function']
                if fun in self.function_dict_awg:
                    func = self.function_dict_awg[fun]
                
                # get length
                leng = p_array[i]['length']

                if leng[-2:] == 'ns':
                    leng_time = int( ceil(round( (float(leng[:-3])*self.sample_rate_awg / 1000), 1) ) )
                elif leng[-2:] == 'us':
                    leng_time = int( ceil(round( (float(leng[:-3])*1000*self.sample_rate_awg / 1000), 1) ) )
                elif leng[-2:] == 'ms':
                    leng_time = int( ceil(round( (float(leng[:-3])*1000000*self.sample_rate_awg / 1000), 1) ) )
                elif leng[-2:] == 's':
                    leng_time = int( ceil(round( (float(leng[:-3])*1000000000*self.sample_rate_awg / 1000), 1) ) )

                # get frequency
                freq = p_array[i]['frequency']
                if func != 4 and func != 5 and func != 7: # 4 is WURST; 7 is TEST2; 5 is SECH/TANH
                    freq_mhz = int(float(freq[:-3]))
                else:
                    # for WURST and SECH/TANH convert center_freq; sweep_freq to start_freq; end_freq
                    cen = float(freq[0][:-3])
                    sw = float(freq[1][:-3])
                    freq_mhz = [  ( 2 * cen - sw ) / 2, ( 2 * cen + sw ) / 2 ]

                # get phase
                phase = float(p_array[i]['phase'])

                # get sigma
                sig = p_array[i]['sigma']

                if sig[-2:] == 'ns':
                    sig_time = int( ceil(round( (float(sig[:-3])*self.sample_rate_awg / 1000), 1) ) )
                elif sig[-2:] == 'us':
                    sig_time = int( ceil(round( (float(sig[:-3])*1000*self.sample_rate_awg / 1000), 1) ) )
                elif sig[-2:] == 'ms':
                    sig_time = int( ceil(round( (float(sig[:-3])*1000000*self.sample_rate_awg / 1000), 1) ) )
                elif sig[-2:] == 's':
                    sig_time = int( ceil(round( (float(sig[:-3])*1000000000*self.sample_rate_awg / 1000), 1) ) )

                # get start
                st = p_array[i]['start']

                if st[-2:] == 'ns':
                    st_time = int( ceil(round((float(st[:-3])*self.sample_rate_awg / 1000), 1) ) )
                elif st[-2:] == 'us':
                    st_time = int( ceil(round((float(st[:-3])*1000*self.sample_rate_awg / 1000), 1) ) )
                elif st[-2:] == 'ms':
                    st_time = int( ceil(round((float(st[:-3])*1000000*self.sample_rate_awg / 1000), 1) ) )
                elif st[-2:] == 's':
                    st_time = int( ceil(round((float(st[:-3])*1000000000*self.sample_rate_awg / 1000), 1) ) )

                # get delta_start
                del_st = p_array[i]['delta_start']

                if del_st[-2:] == 'ns':
                    del_st_time = int( ceil(round((float(del_st[:-3])*self.sample_rate_awg / 1000), 1) ) )
                elif del_st[-2:] == 'us':
                    del_st_time = int( ceil(round((float(del_st[:-3])*1000*self.sample_rate_awg / 1000), 1) ) )
                elif del_st[-2:] == 'ms':
                    del_st_time = int( ceil(round((float(del_st[:-3])*1000000*self.sample_rate_awg / 1000), 1) ) )
                elif del_st[-2:] == 's':
                    del_st_time = int( ceil(round((float(del_st[:-3])*1000000000*self.sample_rate_awg / 1000), 1) ) )

                # get amp
                amp = float(p_array[i]['amp'])

                # get n
                n_wurst = float(p_array[i]['n'])

                # get b
                b_sech = float(p_array[i]['b'])

                # creating converted array
                pulse_temp_array.append( (ch_num, func, freq_mhz, phase, leng_time, sig_time, st_time, del_st_time, amp, n_wurst, b_sech) )

                i += 1

            # should be sorted according to channel number for corecct splitting into subarrays
            return np.asarray(sorted(pulse_temp_array, key = lambda x: ( int(x[0]), int(x[6]) ) ), dtype = "object") #, dtype = np.int64 

        elif self.test_flag == 'test':
            i = 0
            pulse_temp_array = []
            num_pulses = len( p_array )
            while i < num_pulses:
                # get channel number
                ch = p_array[i]['channel']
                if ch in self.channel_dict_awg:
                    ch_num = self.channel_dict_awg[ch]

                # get function
                fun = p_array[i]['function']
                if fun in self.function_dict_awg:
                    func = self.function_dict_awg[fun]
                
                # get length
                leng = p_array[i]['length']

                if leng[-2:] == 'ns':
                    leng_time = int( ceil(round((float(leng[:-3])*self.sample_rate_awg / 1000), 1) ) )
                elif leng[-2:] == 'us':
                    leng_time = int( ceil(round((float(leng[:-3])*1000*self.sample_rate_awg / 1000), 1) ) )
                elif leng[-2:] == 'ms':
                    leng_time = int( ceil(round((float(leng[:-3])*1000000*self.sample_rate_awg / 1000), 1) ) )
                elif leng[-2:] == 's':
                    leng_time = int( ceil(round((float(leng[:-3])*1000000000*self.sample_rate_awg / 1000), 1) ) )

                # get frequency
                freq = p_array[i]['frequency']
                if func != 4 and func != 5 and func != 7: # 4 is WURST; 5 is SECH/TANH 7 is TEST2:
                    freq_mhz = int(float(freq[:-3]))
                else:
                    # for WURST convert center_freq; sweep_freq to start_freq; end_freq
                    cen = float(freq[0][:-3])
                    sw = float(freq[1][:-3])
                    freq_mhz = [  ( 2 * cen - sw ) / 2, ( 2 * cen + sw ) / 2 ]

                # get phase
                phase = float(p_array[i]['phase'])

                # get sigma
                sig = p_array[i]['sigma']

                if sig[-2:] == 'ns':
                    sig_time = int( ceil(round((float(sig[:-3])*self.sample_rate_awg / 1000), 1) ) )
                elif sig[-2:] == 'us':
                    sig_time = int( ceil(round((float(sig[:-3])*1000*self.sample_rate_awg / 1000), 1) ) )
                elif sig[-2:] == 'ms':
                    sig_time = int( ceil(round((float(sig[:-3])*1000000*self.sample_rate_awg / 1000), 1) ) )
                elif sig[-2:] == 's':
                    sig_time = int( ceil(round((float(sig[:-3])*1000000000*self.sample_rate_awg / 1000), 1) ) )

                # get start
                st = p_array[i]['start']

                if st[-2:] == 'ns':
                    st_time = int( ceil(round((float(st[:-3])*self.sample_rate_awg / 1000), 1) ) )
                elif st[-2:] == 'us':
                    st_time = int( ceil(round((float(st[:-3])*1000*self.sample_rate_awg / 1000), 1) ) )
                elif st[-2:] == 'ms':
                    st_time = int( ceil(round((float(st[:-3])*1000000*self.sample_rate_awg / 1000), 1) ) )
                elif st[-2:] == 's':
                    st_time = int( ceil(round((float(st[:-3])*1000000000*self.sample_rate_awg / 1000), 1) ) )

                # get delta_start
                del_st = p_array[i]['delta_start']

                if del_st[-2:] == 'ns':
                    del_st_time = int( ceil(round((float(del_st[:-3])*self.sample_rate_awg / 1000), 1) ) )
                elif del_st[-2:] == 'us':
                    del_st_time = int( ceil(round((float(del_st[:-3])*1000*self.sample_rate_awg / 1000), 1) ) )
                elif del_st[-2:] == 'ms':
                    del_st_time = int( ceil(round((float(del_st[:-3])*1000000*self.sample_rate_awg / 1000), 1) ) )
                elif del_st[-2:] == 's':
                    del_st_time = int( ceil(round((float(del_st[:-3])*1000000000*self.sample_rate_awg / 1000), 1) ) )

                # get amp
                amp = float(p_array[i]['amp'])

                # get n
                n_wurst = float(p_array[i]['n'])

                # get b
                b_sech = float(p_array[i]['b'])

                # creating converted array
                pulse_temp_array.append( ( ch_num, func, freq_mhz, phase, leng_time, sig_time, st_time, del_st_time, amp, n_wurst, b_sech ) )

                i += 1

            # should be sorted according to channel number for corecct splitting into subarrays
            return np.asarray(sorted(pulse_temp_array, key = lambda x: ( int(x[0]), int(x[6]) ) ), dtype="object") #, dtype = np.int64

    def splitting_acc_to_channel_awg(self, np_array):
        """
        A function that splits pulse array into
        several array that have the same channel
        I.E. [[0, 0, 10, 70, 10, 16], [0, 0, 20, 70, 10, 16]]
        -> [array([0, 0, 10, 70, 10, 16], [0, 0, 20, 70, 10, 16])]
        Input array should be sorted
        """
        if self.test_flag != 'test':
            # according to 0 element (channel number)
            answer = np.split(np_array, np.where(np.diff(np_array[:,0]))[0] + 1)
            return answer

        elif self.test_flag == 'test':
            # according to 0 element (channel number)
            try:
                answer = np.split(np_array, np.where(np.diff(np_array[:,0]))[0] + 1)
            except IndexError:
                assert( 1 == 2 ), 'No AWG pulses are defined'

            return answer

    def closest_power_of_two_awg(self, x):
        """
        A function to round card memory or sequence segments
        """
        return int( 2**int(log2(x - 1) + 1 ) )
    
    def preparing_buffer_single_awg(self):
        """
        A function to prepare everything for buffer filling in the 'Single' mode
        Return pulses
        """
        if self.test_flag != 'test':
            
            pulses = self.splitting_acc_to_channel_awg( self.convertion_to_numpy_awg(self.pulse_array_awg) )
            return pulses

        elif self.test_flag == 'test':

            pulses = self.splitting_acc_to_channel_awg( self.convertion_to_numpy_awg(self.pulse_array_awg) )
            return pulses

    def define_buffer_single_joined_awg(self):
        """
        Define and fill the buffer in 'Single Joined' mode;
        
        Every even index is a new data sample for CH0,
        Every odd index is a new data sample for CH1.

        Second channel will be filled automatically
        """
        # pulses are in a form [channel_number, function, frequency, phase, length, sigma, start, delta_start, amp, n_wurst, b_sech] 
        #                      [0,              1,        2,         3,      4,     5,      6,    7,           8,   9,       10    ]
        pulses = self.preparing_buffer_single_awg() # 0.2-0.3 ms
        # only ch0 pulses are analyzed
        # ch1 will be generated automatically with shifted phase
        arguments_array = [[], [], [], [], [], [], [], [], [], []]
        for element in pulses[0]:
            # collect arguments in special array for further handling
            arguments_array[0].append(int(element[1]))     #   0    type; 0 is SINE; 1 is GAUSS; 2 is SINC; 3 is BLANK, 4 is WURST, 5 is SECH/TANH
            arguments_array[1].append(element[6])          #   1    start
            arguments_array[2].append(element[7])          #   2    delta_start
            arguments_array[3].append(element[4])          #   3    length
            arguments_array[4].append(element[3])          #   4    phase
            arguments_array[5].append(element[5])          #   5    sigma
            arguments_array[6].append(element[2])          #   6    frequency
            arguments_array[7].append(element[8])          #   8    amp coefficient
            arguments_array[8].append(element[9])          #   9    n
            arguments_array[9].append(element[10])         #   10   b

        # convert everything in samples 
        pulse_phase_np        = np.asarray(arguments_array[4])
        pulse_start_smp       = (np.asarray(arguments_array[1])).astype('int64')
        pulse_delta_start_smp = (np.asarray(arguments_array[2])).astype('int64')
        pulse_length_smp      = (np.asarray(arguments_array[3])).astype('int64')
        pulse_sigma_smp       = np.asarray(arguments_array[5])
        pulse_frequency       = np.asarray(arguments_array[6], dtype=object)
        pulse_amp             = np.asarray(arguments_array[7])
        pulse_n_wurst         = np.asarray(arguments_array[8])
        pulse_b_sech          = np.asarray(arguments_array[9])

        #_start = pulse_start_smp
        #_end   = pulse_start_smp + pulse_length_smp 
        #self.list_start_end = np.array([_start, _end]).T

        last_pulse_length = pulse_length_smp[-1]
        last_start = pulse_start_smp[-1]

        # define buffer differently for only one or two channels enabled
        # for ch1 phase is automatically shifted by self.phase_shift_ch1_seq_mode_awg
        channel_1 = np.array([], dtype = np.int16)
        channel_2 = np.array([], dtype = np.int16)

        norm_c = self.maxCAD_awg / self.amplitude_max_awg  # 32767 - 260 mV MAX

        #general.message( pulse_length_smp % 4 )
        for index, element in enumerate(arguments_array[0]):

            if element == 0: # 'SINE'
                #start, end = self.list_start_end[index]
                x = np.linspace(0, pulse_length_smp[index], pulse_length_smp[index] ) * pulse_frequency[index] / self.sample_rate_awg
                # 32767 - 260 mV MAX
                y1 = norm_c * self.amplitude_0_awg / pulse_amp[index] * np.sin(2 * np.pi * x + pulse_phase_np[index] )
                y2 = norm_c * self.amplitude_1_awg / pulse_amp[index] * np.sin(2 * np.pi * x + pulse_phase_np[index] + self.phase_shift_ch1_seq_mode_awg)
                channel_1 = np.concatenate( (channel_1, y1.astype(int) ), axis = 0)
                channel_2 = np.concatenate( (channel_2, y2.astype(int) ), axis = 0)

            elif element == 1: # GAUSS
                x_mean = int( pulse_length_smp[index] / 2 )
                sigma  = pulse_sigma_smp[index] 
                x = np.linspace(0, pulse_length_smp[index], pulse_length_smp[index] ) * pulse_frequency[index] / self.sample_rate_awg
                xg = np.linspace(0, pulse_length_smp[index], pulse_length_smp[index] )

                y1 = norm_c * self.amplitude_0_awg / pulse_amp[index] * np.sin(2 * np.pi * x + pulse_phase_np[index] ) * np.exp(-(( xg  - x_mean)**2)*(1 / (2*sigma**2)))
                y2 = norm_c * self.amplitude_1_awg / pulse_amp[index] * np.sin(2 * np.pi * x + pulse_phase_np[index] + self.phase_shift_ch1_seq_mode_awg) * np.exp(- ( (xg - x_mean) / sigma )** 2 / 2)
                channel_1 = np.concatenate( (channel_1, y1.astype(int) ), axis = 0)
                channel_2 = np.concatenate( (channel_2, y2.astype(int) ), axis = 0)

            elif element == 2: # SINC
                x_mean = int( pulse_length_smp[index] / 2 )
                sigma  = pulse_sigma_smp[index] 
                x = np.linspace(0, pulse_length_smp[index], pulse_length_smp[index] ) * pulse_frequency[index] / self.sample_rate_awg
                xs = np.linspace(0, pulse_length_smp[index], pulse_length_smp[index] )

                y1 = norm_c * self.amplitude_0_awg / pulse_amp[index] * np.sin(2 * np.pi * x + pulse_phase_np[index] ) * np.sinc(- ( 2 * ( xs  - x_mean)) / sigma)
                y2 = norm_c * self.amplitude_1_awg / pulse_amp[index] * np.sin(2 * np.pi * x + pulse_phase_np[index] + self.phase_shift_ch1_seq_mode_awg) * np.sinc(- ( 2 * ( xs  - x_mean)) / sigma)
                channel_1 = np.concatenate( (channel_1, y1.astype(int) ), axis = 0)
                channel_2 = np.concatenate( (channel_2, y2.astype(int) ), axis = 0)

            elif element == 3: # BLANK
                pass

            elif element == 4: # WURST
                # at = A*( 1 - abs( sin(pi*(t-tp/2)/tp) )^n )
                # ph = 2*pi*(Fstr*t + 0.5*( Ffin - Fstr )*t^2/tp )
                # WURST = at*sin(ph + phase_0)
                x_mean = int( pulse_length_smp[index] / 2 )
                 ###############################################
                # resonator profile correction test
                freq_sweep = pulse_frequency[index][1] - pulse_frequency[index][0]
                m_p = ( x_mean - pulse_start_smp[index] )
                
                ###LO - RF; high frequency first; flip order
                t_axis = np.flip( np.arange(0, 0 + pulse_length_smp[index] ) - m_p )

                # 300 is wurst sweep
                # md4
                #c = 1 / self.triple_gauss(t_axis * 300 / pulse_length_smp[index], 0.570786, 0.383363, 12.2448, 1241.89, \
                #                                                                            0.191815, -43.478, 1913.96, \
                #                                                                            0.06655,  77.3173, 614.985)

                # md3
                #c = 1 / self.triple_lorentzian(t_axis * 300 / pulse_length_smp[index], 5.92087, 412.868, -124.647, 62.0069, \
                #                                                                            420.717, -35.8879, 34.4214, \
                #                                                                            9893.97,  12.4056, 150.304)
                
                c = 1 / self.triple_lorentzian(t_axis * freq_sweep / pulse_length_smp[index], self.bl_awg, self.a1_awg, self.x1_awg, self.w1_awg, \
                                                                                              self.a2_awg, self.x2_awg, self.w2_awg, \
                                                                                              self.a3_awg, self.x3_awg, self.w3_awg)

                c = c / c[0]
                # limit minimum B1
                # 16 MHz is the value for MD3 at +-150 MHz around the center
                # 23 MHz is an arbitrary limit; around 210 MHz width
                c[c > self.low_level_awg / self.limit_awg] = self.low_level_awg / self.limit_awg
                
                c = c / c[0]
                ph_cor = 0

                if freq_sweep >= 0:
                    pass
                else:
                    np.flip( c )

                # only pi/2 correction
                if self.pi2flag_awg == 1:
                    if int( pulse_amp[index] ) > 1:
                        pass
                    else:
                        c = 1

                #general.plot_1d( 'C', np.arange(0, 0 + pulse_length_smp[index] ), c )
                
                #phase and amplitude from ideal resonator with f0 and Q
                ##Q = 88
                ##f0 = 9700

                ##length = pulse_length_smp[index]
                ##end_freq = pulse_frequency[index][1]
                ##st_freq = pulse_frequency[index][0]
                ##sweep = end_freq - st_freq

                #LO - RF; high frequency first; flip order
                ##t_axis = np.flip( np.arange( st_freq + f0, end_freq + f0, sweep / length ) )

                ##ideal_res = 1 / ( 1 + 1j * Q * ( t_axis / f0 - f0 / t_axis ) )
                ##ph_cor = np.arctan2( ideal_res.imag, ideal_res.real ) 
                # only pi/2 correction
                ##if int( pulse_amp[index] ) > 1:
                ##    amp_cor = 1 / np.abs( ideal_res )
                ##    c = amp_cor / amp_cor[0]
                ##else:
                ##    c = 1

                #general.plot_1d( 'C', np.arange(0, 0 + pulse_length_smp[index] ), ph_cor * 180 / np.pi )
                #general.plot_1d( 'C', np.arange(0, 0 + pulse_length_smp[index] ), c )

                ###############################################
                #x = np.linspace(0, pulse_length_smp[index], pulse_length_smp[index] ) * pulse_frequency[index] / self.sample_rate_awg
                xs = np.linspace(0, pulse_length_smp[index], pulse_length_smp[index] )
                y1 = norm_c * self.amplitude_0_awg / pulse_amp[index] * (1 - np.abs( np.sin( np.pi * ( xs - x_mean) / pulse_length_smp[index] )) ** pulse_n_wurst[index] ) * \
                        np.sin( 2*np.pi * ( xs * pulse_frequency[index][0] / self.sample_rate + 0.5 * (pulse_frequency[index][1] - \
                        pulse_frequency[index][0]) * xs**2 / self.sample_rate / pulse_length_smp[index] ) + pulse_phase_np[index] + ph_cor)
                y2 = norm_c * self.amplitude_1_awg / pulse_amp[index] * (1 - np.abs( np.sin( np.pi * ( xs - x_mean)  / pulse_length_smp[index] )) ** pulse_n_wurst[index] ) * \
                        np.sin( 2*np.pi * ( xs * pulse_frequency[index][0] / self.sample_rate + 0.5 * (pulse_frequency[index][1] - \
                        pulse_frequency[index][0]) * xs**2 / self.sample_rate / pulse_length_smp[index] ) + pulse_phase_np[index] + self.phase_shift_ch1_seq_mode_awg + ph_cor)
                channel_1 = np.concatenate( (channel_1, y1.astype(int) ), axis = 0)
                channel_2 = np.concatenate( (channel_2, y2.astype(int) ), axis = 0)
            
            elif element == 5: # 'SECH/TANH'
                # mid_point for GAUSS and SINC and WURST and SECH/TANH
                # at = A*Sech[b*tp*2^(n - 1) ((t - tp/2)/tp)^n]
                # ph = 2*Pi*bw/b*Log[Cosh[b*(t - tp/2)]]/2/Tanh[b*tp/2]
                # SECH = at*sin(ph + phase_0)
                x_mean = int( pulse_length_smp[index] / 2 )

                #########################################################
                # resonator profile correction test
                m_p = ( x_mean - pulse_start_smp[index] )
                freq_sweep = pulse_frequency[index][1] - pulse_frequency[index][0]

                ###LO - RF; high frequency first; flip order
                t_axis = np.flip( np.arange(0, 0 + pulse_length_smp[index] ) - m_p )
                
                # 300 is wurst sweep
                c = 1 / self.triple_lorentzian(t_axis * freq_sweep / pulse_length_smp[index], self.bl_awg, self.a1_awg, self.x1_awg, self.w1_awg, \
                                                                                              self.a2_awg, self.x2_awg, self.w2_awg, \
                                                                                              self.a3_awg, self.x3_awg, self.w3_awg)

                c = c / c[0]
                # limit minimum B1
                # 16 MHz is the value for MD3 at +-150 MHz around the center
                # 23 MHz is an arbitrary limit; around 210 MHz width
                c[c > self.low_level_awg/self.limit_awg] = self.low_level_awg/self.limit_awg
                
                c = c / c[0]
                ph_cor = 0

                if freq_sweep >= 0:
                    pass
                else:
                    np.flip( c )

                # only pi/2 correction
                if self.pi2flag_awg == 1:
                    if int( pulse_amp[index] ) > 1:
                        pass
                    else:
                        c = 1

                #general.plot_1d( 'C', np.arange(0, 0 + pulse_length_smp[index] ), c )
                freq_cen = ( pulse_frequency[index][1] + pulse_frequency[index][0] ) / 2

                bw = (pulse_frequency[index][1] - pulse_frequency[index][0]) / self.sample_rate
                #pulse_b_sech[index]
                xs = np.linspace(0, pulse_length_smp[index], pulse_length_smp[index] )
                y1 = norm_c * self.amplitude_0_awg / pulse_amp[index] * ( 1 / np.cosh( (pulse_b_sech[index] * x_mean * 2 ** (pulse_n_wurst[index] - 1)) * ((xs - x_mean) / pulse_length_smp[index]) ** pulse_n_wurst[index]) ) * \
                        np.sin( 2*np.pi * ( bw / pulse_b_sech[index] * np.log( np.cosh( pulse_b_sech[index] * ( xs - x_mean ) ) ) / 2 / np.tanh(  pulse_b_sech[index] *x_mean ) ) \
                        + pulse_phase_np[index] + ph_cor + 0 * 2*np.pi*freq_cen / self.sample_rate * xs )
                y2 = norm_c * self.amplitude_1_awg / pulse_amp[index] * ( 1 / np.cosh( (pulse_b_sech[index] * x_mean * 2 ** (pulse_n_wurst[index] - 1)) * ((xs - x_mean) / pulse_length_smp[index]) ** pulse_n_wurst[index]) ) * \
                        np.sin( 2*np.pi * ( bw / pulse_b_sech[index] * np.log( np.cosh( pulse_b_sech[index] * ( xs - x_mean ) ) ) / 2 / np.tanh(  pulse_b_sech[index] *x_mean ) ) \
                        + pulse_phase_np[index] + self.phase_shift_ch1_seq_mode_awg + ph_cor + 0 * 2*np.pi*freq_cen / self.sample_rate * xs )
                channel_1 = np.concatenate( (channel_1, y1.astype(int) ), axis = 0)
                channel_2 = np.concatenate( (channel_2, y2.astype(int) ), axis = 0)

        return channel_1 , channel_2
    
    def double_gauss(self, x, bl, a1, x1, w1, a2, x2, w2):
        return bl + a1 * np.exp( -(x - x1)**2 / w1  ) + a2 * np.exp( -(x - x2)**2 / w2  )

    def triple_gauss(self, x, bl, a1, x1, w1, a2, x2, w2, a3, x3, w3):
        return bl + a1 * np.exp( -(x - x1)**2 / w1  ) + a2 * np.exp( -(x - x2)**2 / w2  ) + a3 * np.exp( -(x - x3)**2 / w3  )

    def triple_lorentzian(self, x, bl, a1, x1, w1, a2, x2, w2, a3, x3, w3):
        return bl + a1 * 0.5 * w1 / np.pi / ( (x - x1)**2 + (0.5 * w1)**2  ) + a2 * 0.5 * w2 / np.pi / ( (x - x2)**2 + (0.5 * w2)**2  ) + a3 * 0.5 * w3 / np.pi / ( (x - x3)**2 + (0.5 * w3)**2  )

    def round_to_closest_awg(self, x, y):
        """
        A function to round x to divisible by y
        """
        return round(( y * ( ( x // y ) + (round(x % y, 2) > 0) ) ), 1)

    ####################BOARD#######################
    def write_data_GIM_brd(self):
        if self.test_flag != 'test':
            size , data             = self.data_buf_IP_GIM_brd
            len_2st_ch              = self.adc_window
            
            setSwitchEn_GIMRet      = self.setSwitchEn_GIM     (0                                                )
            
            rstFIFO_GIMRet          = self.rstFIFO_GIM         ((self.nIP_No_brd&1)                              )
            setWriteEnable_GIMRet   = self.setWriteEnable_GIM  ((self.nIP_No_brd&1), 1                           ) 

            setFIFOCnt_GIMRet       = self.setFIFOCnt_GIM      ((self.nIP_No_brd&1), self.gimSum_brd             ) 
            writeIPRet              = self.writeIP             (data               , ctypes.c_int32(size)        )
            set1stChanImpLen_GIMRet = self.set1stChanImpLen_GIM((self.nIP_No_brd&1), ctypes.c_int32(len_2st_ch)  )   
            
            setWriteEnable_GIMRet   = self.setWriteEnable_GIM  ((self.nIP_No_brd&1), 0                           )
            setId_GIMRet            = self.setId_GIM           ((self.nIP_No_brd&1), self.nIP_No_brd     ,     0 )
            setGIM_modeRet          = self.setGIM_mode         ((self.nIP_No_brd&1), ((self.nIP_No_brd - 1)&1), self.flag_sum_brd)
            
            setSelect_GIMRet        = self.setSelect_GIM       ((self.nIP_No_brd&1)                              )
            setSwitchEn_GIMRet      = self.setSwitchEn_GIM     (1                                                )


        elif self.test_flag == 'test':
            size , data             = self.data_buf_IP_GIM_brd
            len_2st_ch              = self.adc_window

    def start_brd(self):
        if self.test_flag != 'test':
            self.setDACEnable_GIM(1)
            self.DAC_Start()
            self.setEnable_GIM(1)
            self.AdcStreamStart()

        elif self.test_flag == 'test':
            pass

    def write_data_DAC(self, nFIFO):
        """
        """
        if self.test_flag != 'test':
            len_1st_ch              = self.dac_window
            fl1  = np.array([-self.channel_1, -self.channel_2, self.channel_2, self.channel_1], dtype = ctypes.c_int16).T.ravel()
            self.arr1 = ( ctypes.c_int16 * len(fl1) )(*fl1)

            #writing data to FPGA
            self.rstDACFIFO_GIM( (nFIFO&1) )
            self.setDACWriteEnable_GIM( (nFIFO&1), 1 )
            retval = self.write_DAC_data( self.arr1, ctypes.c_int(len(self.arr1)) )
            self.setDACWriteEnable_GIM( (nFIFO&1), 0 )

        elif self.test_flag == 'test':
            len_1st_ch              = self.dac_window
            #general.message(len_1st_ch)
            #general.message(f'BUF: {int( len(self.channel_1) / 4 )}')

            assert( int( len(self.channel_1) / 4 ) == len_1st_ch ), 'Length of TRIGGER_AWG pulses does not equal to Length of AWG pulses'

    def change_ini_file(self, search_text, new_text):
        """
        pb.change_ini_file("streamBufSizeKb = 512", "streamBufSizeKb = 1024")
        """

        if self.test_flag != 'test':

            file_ini = 'exam_adc.ini'
            file_path =  "/".join(  (*(__file__.split("/")), )[:-3] + ("libs", ) + (file_ini, ) )

            with fileinput.input(file_path, inplace = True) as file:
                for line in file:
                    new_line = line.replace(search_text, new_text)
                    print(new_line, end = '')

        elif self.test_flag == 'test':

            pass

    def change_two_ini_files(self, file_ini, search_text, new_text):
        """
        pb.change_two_ini_files('exam_adc.ini', "streamBufSizeKb = 512", "streamBufSizeKb = 1024")
        """

        if self.test_flag != 'test':

            #file_ini = 'exam_adc.ini'
            file_path =  "/".join(  (*(__file__.split("/")), )[:-3] + ("libs", ) + (file_ini, ) )

            with fileinput.input(file_path, inplace = True) as file:
                for line in file:
                    new_line = line.replace(search_text, new_text)
                    print(new_line, end = '')

        elif self.test_flag == 'test':

            pass

    def change_three_ini_files(self, file_ini, search_text, new_text):
        """
        pb.change_two_ini_files('exam_adc.ini', "streamBufSizeKb = 512", "streamBufSizeKb = 1024")
        """
        file_path =  "/".join(  (*(__file__.split("/")), )[:-3] + ("libs", ) + (file_ini, ) )

        with fileinput.input(file_path, inplace = True) as file:
            for line in file:
                new_line = line.replace(search_text, search_text)
                if new_line[0:14] == 'BaseClockValue':
                    print(search_text + new_text + '\n', end = '')
                else:
                    print(new_line, end = '')

    def count_ip(self, ph):
        return np.sum( self.count_nip.reshape( len( self.count_nip ) // ph, ph, order = 'C' ), axis = 1 )

def main():
    pass

if __name__ == "__main__":
    main()