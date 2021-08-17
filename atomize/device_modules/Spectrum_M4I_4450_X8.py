#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
###AWG
#sys.path.append('/home/pulseepr/Sources/AWG/Examples/python')
sys.path.append('/home/anatoly/AWG/spcm_examples/python')
#sys.path.append('/home/anatoly/awg_files/python')
#sys.path.append('C:/Users/User/Desktop/Examples/python')
import numpy as np
import atomize.device_modules.config.config_utils as cutil
import atomize.general_modules.general_functions as general

from pyspcm import *
from spcm_tools import *

class Spectrum_M4I_4450_X8:
    def __init__(self):

        #### Inizialization
        # setting path to *.ini file
        self.path_current_directory = os.path.dirname(__file__)
        self.path_config_file = os.path.join(self.path_current_directory, 'config','Spectrum_M4I_4450_X8_config.ini')

        # configuration data
        #config = cutil.read_conf_util(self.path_config_file)
        self.specific_parameters = cutil.read_specific_parameters(self.path_config_file)

        # Channel assignments
        #ch0 = self.specific_parameters['ch0'] # TRIGGER

        self.timebase_dict = {'ms': 1000000, 'us': 1000, 'ns': 1, }
        self.channel_dict = {'CH0': 0, 'CH1': 1, }
        self.coupling_dict = {'DC': 0, 'AC': 1, }
        self.impedance_dict = {'1 M': 0, '50': 1, }
        self.sample_rate_list = [1907, 3814, 7629, 15258, 30517, 61035, 122070, 244140, 488281, 976562, \
                            1953125, 3906250, 7812500, 15625000, 31250000, 62500000, 125000000, \
                            250000000, 500000000]
        self.hf_mode_range_list = [500, 1000, 2500, 5000]
        self.buffered_mode_range_list = [200, 500, 1000, 2000, 5000, 10000]

        # Limits and Ranges (depends on the exact model):
        #clock = float(self.specific_parameters['clock'])

        # Delays and restrictions
        # MaxDACValue corresponds to the amplitude of the output signal; MaxDACValue - Amplitude and so on
        # lMaxDACValue = int32 (0)
        # spcm_dwGetParam_i32 (hCard, SPC_MIINST_MAXADCVALUE, byref(lMaxDACValue))
        # lMaxDACValue.value = lMaxDACValue.value - 1
        #maxCAD = 8191 # MaxCADValue of the AWG card - 1
        #minCAD = -8192
        self.amplitude_max = 2500 # mV
        self.amplitude_min = 80 # mV
        self.sample_rate_max = 500 # MHz
        self.sample_rate_min = 0.001907 # MHz
        self.sample_ref_clock_max = 100 # MHz
        self.sample_ref_clock_min = 10 # MHz
        self.averages_max = 100000
        self.delay_max = 8589934576
        self.delay_min = 0 

        # Test run parameters
        # These values are returned by the modules in the test run 
        if len(sys.argv) > 1:
            self.test_flag = sys.argv[1]
        else:
            self.test_flag = 'None'

        if self.test_flag != 'test':

            # Collect all parameters for digitizer settings
            self.sample_rate = 500 # MHz
            self.clock_mode = 1 # 1 is Internal; 32 is External
            self.reference_clock = 100 # MHz
            self.card_mode = 1 # 1 is Single; 131072 is Average;
            self.trigger_ch = 2 # 1 is Software; 2 is External
            self.trigger_mode = 1 # 1 is Positive; 2 is Negative; 8 is High; 10 is Low
            self.aver = 2 # 0 is infinity
            self.delay = 0 # in sample rate; step is 32; rounded
            self.channel = 3 # 1 is CH0; 2 is CH1; 3 is CH0 + CH1
            self.points = 128 # number of points
            self.posttrig_points = 64 # number of posttrigger points

            self.input_mode = 1 # 1 is HF mode; 0 is Buffered
            self.amplitude_0 = 500 # amlitude for CH0 in mV
            self.amplitude_1 = 500 # amlitude for CH1 in mV
            self.offset_0 = 0 # offset for CH0 in percentage
            self.offset_1 = 0 # offset for CH1 in percentage
            self.coupling_0 = 0 # coupling for CH0; AC is 1; DC is 0
            self.coupling_1 = 0 # coupling for CH1
            self.impedance_0 = 1 # impedance for CH0; 1 M is 0; 50 is 0
            self.impedance_1 = 1 # impedance for CH1;

            self.num_segments = 1 # number of segments for 'Average mode'
            
            # change of settings
            self.setting_change_count = 0

            # state counter
            self.state = 0

        elif self.test_flag == 'test':        
            self.test_sample_rate = '500 MHz'
            self.test_clock_mode = 'Internal'
            self.test_ref_clock = 100
            self.test_card_mode = 'Single'
            self.test_trigger_ch = 'External'
            self.test_trigger_mode = 'Positive'
            self.test_averages = 10
            self.test_delay = 0
            self.test_channel = 'CH0'
            self.test_amplitude = 'CH0: 500 mV; CH1: 500 mV'
            self.test_num_segments = 1
            self.test_points = 128
            self.test_posttrig_points = 64
            self.test_input_mode = 'HF'
            self.test_offset = 'CH0: 10'
            self.test_coupling = 'CH0: DC'
            self.test_impedance = 'CH0: 50'

            # Collect all parameters for digitizer settings
            self.sample_rate = 500 
            self.clock_mode = 1
            self.reference_clock = 100
            self.card_mode = 1
            self.trigger_ch = 2
            self.trigger_mode = 1
            self.aver = 2
            self.delay = 0
            self.channel = 3
            self.points = 128
            self.posttrig_points = 64

            self.input_mode = 1
            self.amplitude_0 = 500
            self.amplitude_1 = 500
            self.offset_0 = 0
            self.offset_1 = 0
            self.coupling_0 = 0
            self.coupling_1 = 0
            self.impedance_0 = 1
            self.impedance_1 = 1

            self.num_segments = 1

            # change of settings
            self.setting_change_count = 0

            # state counter
            self.state = 0

    # Module functions
    def digitizer_name(self):
        answer = 'Spectrum M4I.4450-X8'
        return answer

    def digitizer_setup(self):
        """
        Write settings to the digitizer. No argument; No output
        Everything except the buffer information will be write to the digitizer

        This function should be called after all functions that change settings are called
        """
        if self.test_flag != 'test':
            
            if self.state == 0:
                # open card
                self.hCard = spcm_hOpen ( create_string_buffer (b'/dev/spcm1') )
                self.state = 1
                if self.hCard == None:
                    general.message("No card found...")
                    sys.exit()
            else:
                pass

            spcm_dwSetParam_i32 (self.hCard, SPC_TIMEOUT, 10000) 
            # general parameters of the card; internal/external clock
            if self.clock_mode == 1:
                spcm_dwSetParam_i64 (self.hCard, SPC_SAMPLERATE, int( 1000000 * self.sample_rate ))
            elif self.clock_mode == 32:
                spcm_dwSetParam_i32 (self.hCard, SPC_CLOCKMODE, self.clock_mode)
                spcm_dwSetParam_i64 (self.hCard, SPC_REFERENCECLOCK, MEGA(self.reference_clock))
                spcm_dwSetParam_i64 (self.hCard, SPC_SAMPLERATE, int( 1000000 * self.sample_rate ) )

            # change card mode and memory
            if self.card_mode == 1:
                spcm_dwSetParam_i32(self.hCard, SPC_CARDMODE, self.card_mode)
                spcm_dwSetParam_i32(self.hCard, SPC_MEMSIZE, self.points)
                spcm_dwSetParam_i32(self.hCard, SPC_POSTTRIGGER, self.posttrig_points)
            elif self.card_mode == 131072:
                spcm_dwSetParam_i32(self.hCard, SPC_CARDMODE, self.card_mode)
                # TO CHECK:
                spcm_dwSetParam_i32(self.hCard, SPC_MEMSIZE, int( self.points * self.num_segments ) )
                # segment size should be multiple of memory size
                spcm_dwSetParam_i32(self.hCard, SPC_SEGMENTSIZE, self.points)
                spcm_dwSetParam_i32(self.hCard, SPC_POSTTRIGGER, self.posttrig_points)
                spcm_dwSetParam_i32(self.hCard, SPC_SEGMENTSIZE, self.aver)
                # SPC_LOOPS ?? page 181


            # trigger
            spcm_dwSetParam_i32(self.hCard, SPC_TRIG_TERM, 1) # 50 Ohm trigger load
            spcm_dwSetParam_i32(self.hCard, SPC_TRIG_ORMASK, self.trigger_ch) # software / external
            if self.trigger_ch == 2:
                spcm_dwSetParam_i32(self.hCard, SPC_TRIG_EXT0_MODE, self.trigger_mode)
            
            # loop
            #spcm_dwSetParam_i32(self.hCard, SPC_LOOPS, self.loop)
            
            # trigger delay
            spcm_dwSetParam_i32( self.hCard, SPC_TRIG_DELAY, int(self.delay) )

            # set the output channels
            spcm_dwSetParam_i32 (self.hCard, SPC_PATH0, self.input_mode)
            spcm_dwSetParam_i32 (self.hCard, SPC_PATH1, self.input_mode)
            spcm_dwSetParam_i32 (self.hCard, SPC_CHENABLE, self.channel)
            spcm_dwSetParam_i32 (self.hCard, SPC_AMP0, self.amplitude_0)
            spcm_dwSetParam_i32 (self.hCard, SPC_AMP1, self.amplitude_1)

            if ( self.amplitude_0 != 1000 or self.amplitude_0 != 10000 ) and self.input_mode == 0:
                spcm_dwSetParam_i32 (self.hCard, SPC_OFFS0, -self.offset_0 )
                spcm_dwSetParam_i32 (self.hCard, SPC_OFFS1, -self.offset_1 )
            elif self.input_mode == 1:
                spcm_dwSetParam_i32 (self.hCard, SPC_OFFS0, -self.offset_0 )
                spcm_dwSetParam_i32 (self.hCard, SPC_OFFS1, -self.offset_1 )

            spcm_dwSetParam_i32 (self.hCard, SPC_ACDC0, self.coupling_0)
            spcm_dwSetParam_i32 (self.hCard, SPC_ACDC1, self.coupling_1)

            # in HF mode impedance is fixed
            if self.input_mode == 0:
                spcm_dwSetParam_i32 (self.hCard, SPC_50OHM0, self.impedance_0 )
                spcm_dwSetParam_i32 (self.hCard, SPC_50OHM1, self.impedance_1 )

            # define the memory size / max amplitude
            #llMemSamples = int64 (self.memsize)
            #lBytesPerSample = int32(0)
            #spcm_dwGetParam_i32 (hCard, SPC_MIINST_BYTESPERSAMPLE,  byref(lBytesPerSample))
            #lSetChannels = int32 (0)
            #spcm_dwGetParam_i32 (hCard, SPC_CHCOUNT, byref (lSetChannels))


            # The Spectrum driver also contains a register that holds the value of the decimal value of the full scale representation of the installed ADC. This
            # value should be used when converting ADC values (in LSB) into real-world voltage values, because this register also automatically takes any
            # specialities into account, such as slightly reduced ADC resolution with reserved codes for gain/offset compensation.
            self.lMaxDACValue = int32 (0)
            spcm_dwGetParam_i32 (self.hCard, SPC_MIINST_MAXADCVALUE, byref(self.lMaxDACValue))

            #if lMaxDACValue.value == maxCAD:
            #    pass
            #else:
            #    general.message('maxCAD value does not equal to lMaxDACValue.value')
            #    sys.exit()

            if self.channel == 1 or self.channel == 2:
                
                if self.card_mode == 1:
                    self.qwBufferSize = uint64 (self.points * 2 * 1) # in bytes. samples with 2 bytes each, one channel active
                # MAYBE DIFFERENT FOR AVERAGE MODE
                elif self.card_mode == 131072:
                    self.qwBufferSize = uint64 (self.points * sizeof(int32) * 1) # for averaging the number of bytes per sample is fixed to 4 (32 bit samples)

            elif self.channel == 3:

                if self.card_mode == 1:
                    self.qwBufferSize = uint64 (self.points * 2 * 2) # in bytes. samples with 2 bytes each
                # MAYBE DIFFERENT FOR AVERAGE MODE
                elif self.card_mode == 131072:
                    self.qwBufferSize = uint64 (self.points * sizeof(int32) * 2) # for averaging the number of bytes per sample is fixed to 4 (32 bit samples)

            self.lNotifySize = int32 (0) # driver should notify program after all data has been transfered

            spcm_dwSetParam_i32 (self.hCard, SPC_M2CMD, M2CMD_CARD_WRITESETUP)

        elif self.test_flag == 'test':
            # to run several important checks
            #if self.setting_change_count == 1:
            #    if self.card_mode == 32768 and self.sequence_mode == 0:
            #        self.buf = self.define_buffer_single()[0]
            #    elif self.card_mode == 32768 and self.sequence_mode == 0:
            #        self.buf = self.define_buffer_single_joined()[0]
            #    elif self.card_mode == 512 and self.sequence_mode == 0:
            #        self.buf = self.define_buffer_multi()[0]
            #else:
            pass

    def digitizer_get_curve(self):
        """
        Start digitizer. No argument; No output
        Default settings:
        Sample clock is 500 MHz; Clock mode is 'Internal'; Reference clock is 100 MHz; Card mode is 'Single';
        Trigger channel is 'External'; Trigger mode is 'Positive'; Number of averages is 2; Trigger delay is 0;
        Enabled channels is CH0 and CH1; Range of CH0 is '500 mV'; Range of CH1 is '500 mV';
        Number of segments is 1; Number of points is 128 samples; Posttriger points is 64;
        Input mode if 'HF'; Coupling of CH0 and CH1 are 'DC'; Impedance of CH0 and CH1 are '50';
        Horizontal offset of CH0 and CH1 are 0%; 
        """
        if self.test_flag != 'test':

            #spcm_dwSetParam_i32 (self.hCard, SPC_M2CMD, M2CMD_CARD_WRITESETUP)

            # define the buffer
            pvBuffer = c_void_p ()
            pvBuffer = pvAllocMemPageAligned ( self.qwBufferSize.value )

            # transfer
            spcm_dwDefTransfer_i64 (self.hCard, SPCM_BUF_DATA, SPCM_DIR_CARDTOPC, self.lNotifySize, pvBuffer, uint64 (0), self.qwBufferSize)

            # start card and DMA
            spcm_dwSetParam_i32 (self.hCard, SPC_M2CMD, M2CMD_CARD_START | M2CMD_CARD_ENABLETRIGGER | M2CMD_DATA_STARTDMA)
            # wait for acquisition
            # dwError = 
            dwError = spcm_dwSetParam_i32 (self.hCard, SPC_M2CMD, M2CMD_CARD_WAITREADY | M2CMD_DATA_WAITDMA)

            # timeout Error
            if dwError == 263:
                general.message('A timeout occurred while waiting. Probably the digitizer is not triggered')
                self.digitizer_stop()

            # this is the point to do anything with the data
            lBitsPerSample = int32 (0)
            spcm_dwGetParam_i32 (self.hCard, SPC_MIINST_BITSPERSAMPLE, byref (lBitsPerSample)) # lBitsPerSample.value = 14

            pnData = cast  (pvBuffer, ptr16) # cast to pointer to 16bit integer
            if self.channel == 1 or self.channel == 2:

                if self.card_mode == 1:

                    if self.channel == 1:
                        data = ( self.amplitude_0 / 1000) * np.ctypeslib.as_array(pnData, shape = (int( self.qwBufferSize.value / 2 ), )) / self.lMaxDACValue.value

                    elif self.channel == 2:
                        data = ( self.amplitude_1 / 1000) * np.ctypeslib.as_array(pnData, shape = (int( self.qwBufferSize.value / 2 ), )) / self.lMaxDACValue.value

                    xs = np.arange( len(data) ) / (self.sample_rate * 1000000)

                # SHOULD BE CHECKED
                elif self.card_mode == 131072:

                    if self.channel == 1:
                        data = ( self.amplitude_0 / 1000) * np.ctypeslib.as_array(pnData, shape = (int( self.qwBufferSize.value / 4 ), )) / self.lMaxDACValue.value

                    elif self.channel == 2:
                        data = ( self.amplitude_1 / 1000) * np.ctypeslib.as_array(pnData, shape = (int( self.qwBufferSize.value / 4 ), )) / self.lMaxDACValue.value

                    xs = np.arange( len(data) ) / (self.sample_rate * 1000000)

                return xs, data

            elif self.channel == 3:

                if self.card_mode == 1:

                    data = np.ctypeslib.as_array(pnData, shape = (int( self.qwBufferSize.value / 2 ), ))
                    # / 1000 convertion in V
                    # CH0
                    data1 = ( data[0::2] * ( self.amplitude_0 / 1000) ) / self.lMaxDACValue.value
                    # CH1
                    data2 = ( data[1::2] * ( self.amplitude_1 / 1000) ) / self.lMaxDACValue.value

                    xs = np.arange( len(data1) ) / (self.sample_rate * 1000000)
                
                # SHOULD BE CHECKED
                elif self.card_mode == 131072:
                    
                    data = np.ctypeslib.as_array(pnData, shape = (int( self.qwBufferSize.value / 4 ), ))
                    # / 1000 convertion in V
                    # CH0
                    data1 = ( data[0::2] * ( self.amplitude_0 / 1000) ) / self.lMaxDACValue.value
                    # CH1
                    data2 = ( data[1::2] * ( self.amplitude_1 / 1000) ) / self.lMaxDACValue.value

                    xs = np.arange( len(data1) ) / (self.sample_rate * 1000000)

                return xs, data1, data2

            #print( len(data) )
            #xs = 2*np.arange( int(qwBufferSize.value / 4) )

            # test or error message
            #general.message(dwError)

            # clean up
            #spcm_vClose (hCard)

        elif self.test_flag == 'test':

            # CHECK FOR AVERAGE MODE
            dummy = np.zeros( self.points )

            if self.channel == 1 or self.channel == 2:
                return dummy, dummy
            elif self.channel == 3:
                return dummy, dummy, dummy

    def digitizer_close(self):
        """
        Close the digitizer. No argument; No output
        """
        if self.test_flag != 'test':
            # clean up
            spcm_vClose ( self.hCard )
            self.state == 0

        elif self.test_flag == 'test':
            pass

    def digitizer_stop(self):
        """
        Stop the digitizer. No argument; No output
        """
        if self.test_flag != 'test':

            # open card
            #hCard = spcm_hOpen( create_string_buffer (b'/dev/spcm0') )
            #if hCard == None:
            #    general.message("No card found...")
            #    sys.exit()
            spcm_dwSetParam_i32 (self.hCard, SPC_M2CMD, M2CMD_CARD_STOP)
            #general.message('Digitizer stopped')

        elif self.test_flag == 'test':
            pass

    def digitizer_number_of_points(self, *points):
        """
        Set or query number of points;
        Input: digitizer_number_of_points(128); Number of points should be divisible by 16; 32 is the minimum
        Default: 128;
        Output: '128'
        """
        if self.test_flag != 'test':
            self.setting_change_count = 1

            if len(points) == 1:
                pnts = int(points[0])
                if pnts < 32:
                    pnts = 32
                    general.message('Number of points must be more than 32')
                if pnts % 16 != 0:
                    general.message('Number of points should be divisible by 16; The closest avalaibale number is used')
                    #self.points = int( 16*(pnts // 16) )
                    self.points = self.round_to_closest(pnts, 16)
                else:
                    self.points = pnts


            # to update on-the-fly
            if self.state == 0:
                pass
            elif self.state == 1:

                # change card mode and memory
                if self.card_mode == 1:
                    spcm_dwSetParam_i32(self.hCard, SPC_MEMSIZE, self.points)
                elif self.card_mode == 131072:
                    # TO CHECK:
                    spcm_dwSetParam_i32(self.hCard, SPC_MEMSIZE, int( self.points * self.num_segments ) )
                    # segment size should be multiple of memory size
                    spcm_dwSetParam_i32(self.hCard, SPC_SEGMENTSIZE, self.points)

                # correct buffer size
                if self.channel == 1 or self.channel == 2:
                
                    if self.card_mode == 1:
                        self.qwBufferSize = uint64 (self.points * 2 * 1) # in bytes. samples with 2 bytes each, one channel active
                    # MAYBE DIFFERENT FOR AVERAGE MODE
                    elif self.card_mode == 131072:
                        self.qwBufferSize = uint64 (self.points * sizeof(int32) * 1) # for averaging the number of bytes per sample is fixed to 4 (32 bit samples)

                elif self.channel == 3:

                    if self.card_mode == 1:
                        self.qwBufferSize = uint64 (self.points * 2 * 2) # in bytes. samples with 2 bytes each
                    # MAYBE DIFFERENT FOR AVERAGE MODE
                    elif self.card_mode == 131072:
                        self.qwBufferSize = uint64 (self.points * sizeof(int32) * 2) # for averaging the number of bytes per sample is fixed to 4 (32 bit samples)

                spcm_dwSetParam_i32 (self.hCard, SPC_M2CMD, M2CMD_CARD_WRITESETUP)


            elif len(points) == 0:
                return self.points

        elif self.test_flag == 'test':
            self.setting_change_count = 1

            if len(points) == 1:
                pnts = int(points[0])
                assert( pnts >= 32 ), "Number of points must be more than 32"
                if pnts % 16 != 0:
                    #general.message('Number of points should be divisible by 16; The closest avalaibale number is used')
                    #self.points = int( 16*(pnts // 16) )
                    self.points = self.round_to_closest(pnts, 16)
                else:
                    self.points = pnts

            elif len(points) == 0:
                return self.test_points    
            else:
                assert( 1 == 2 ), 'Incorrect argument'

    def digitizer_posttrigger(self, *post_points):
        """
        Set or query number of posttrigger points;
        Input: digitizer_posttrigger(64); Number of points should be divisible by 16; 16 is the minimum
        Default: 64;
        Output: '64'
        """
        if self.test_flag != 'test':
            self.setting_change_count = 1

            if len(post_points) == 1:
                pnts = int(post_points[0])
                if pnts < 16:
                    pnts = 16
                    general.message('Number of posttrigger points must be more than 16')
                if pnts % 16 != 0:
                    general.message('Number of posttrigger points should be divisible by 16; The closest avalaibale number is used')
                    #self.posttrig_points = int( 16*(pnts // 16) )
                    self.posttrig_points = self.round_to_closest(pnts, 16)
                else:
                    self.posttrig_points = pnts
                if self.posttrig_points > self.points:
                    general.message('Number of posttrigger points should be less than number of points; The closest avalaibale number is used')
                    self.posttrig_points = self.points

            # to update on-the-fly
            if self.state == 0:
                pass
            elif self.state == 1:
                spcm_dwSetParam_i32(self.hCard, SPC_POSTTRIGGER, self.posttrig_points)
                spcm_dwSetParam_i32 (self.hCard, SPC_M2CMD, M2CMD_CARD_WRITESETUP)


            elif len(post_points) == 0:
                return self.posttrig_points

        elif self.test_flag == 'test':
            self.setting_change_count = 1

            if len(post_points) == 1:
                pnts = int(post_points[0])
                assert( pnts >= 16 ), "Number of points must be more than 16"
                if pnts % 16 != 0:
                    #general.message('Number of points should be divisible by 16; The closest avalaibale number is used')
                    #self.posttrig_points = int( 16*(pnts // 16) )
                    self.posttrig_points = self.round_to_closest(pnts, 16)
                else:
                    self.posttrig_points = pnts
                if self.posttrig_points > self.points:
                    #general.message('Number of posttrigger points should be less than number of points; The closest avalaibale number is used')
                    self.posttrig_points = self.points                

            elif len(post_points) == 0:
                return self.test_posttrig_points    
            else:
                assert( 1 == 2 ), 'Incorrect argument'
    
    def digitizer_number_of_segments(self, *segments):
        """
        Set or query the number of segments for 'Average' digitizer mode;
        Digitizer should be in 'Average' mode. Please, refer to digitizer_card_mode() function
        Input: digitizer_number_of_segments(2); Number of segment is from the range 0-200
        Default: 1;
        Output: '2'
        """
        if self.test_flag != 'test':
            self.setting_change_count = 1

            if len(segments) == 1:
                seg = int(segments[0])
                if self.card_mode == 131072:
                    self.num_segments = seg
                else:
                    general.message('Digitizer is not in Average mode')
                    sys.exit()
            elif len(segments) == 0:
                return self.num_segments

        elif self.test_flag == 'test':
            self.setting_change_count = 1

            if len(segments) == 1:
                seg = int(segments[0])
                if seg != 1:
                    assert( self.card_mode == 131072), 'Number of segments higher than one is available only in Average mode. Please, change it using digitizer_card_mode()'
                assert (seg > 0 and seg <= 200), 'Incorrect number of segments; Should be 0 < segmenets <= 200'
                self.num_segments = seg

            elif len(segments) == 0:
                return self.test_num_segments
            else:
                assert( 1 == 2 ), 'Incorrect argumnet'

    def digitizer_channel(self, *channel):
        """
        Enable the specified channel or query enabled channels;
        Input: digitizer_channel('CH0', 'CH1'); Channel is 'CH0' or 'CH1'
        Default: both channels are enabled
        Output: 'CH0'
        """
        if self.test_flag != 'test':
            self.setting_change_count = 1

            if len(channel) == 1:
                ch = str(channel[0])
                if ch == 'CH0':
                    self.channel = 1
                elif ch == 'CH1':
                    self.channel = 2
                else:
                    general.message('Incorrect channel')
                    sys.exit()
            elif len(channel) == 2:
                ch1 = str(channel[0])
                ch2 = str(channel[1])
                if (ch1 == 'CH0' and ch2 == 'CH1') or (ch1 == 'CH1' and ch2 == 'CH0'):
                    self.channel = 3
                else:
                    general.message('Incorrect channel; Channel should be CH0 or CH1')
                    sys.exit()
            elif len(channel) == 0:
                if self.channel == 1:
                    return 'CH0'
                elif self.channel == 2:
                    return 'CH1'
                elif self.channel == 3:
                    return 'CH0, CH1'

            else:
                general.message('Incorrect argument; Channel should be CH0 or CH1')
                sys.exit()

        elif self.test_flag == 'test':
            self.setting_change_count = 1

            if len(channel) == 1:
                ch = str(channel[0])
                assert( ch == 'CH0' or ch == 'CH1' ), 'Incorrect channel; Channel should be CH0 or CH1'
                if ch == 'CH0':
                    self.channel = 1
                elif ch == 'CH1':
                    self.channel = 2
            elif len(channel) == 2:
                ch1 = str(channel[0])
                ch2 = str(channel[1])
                assert( (ch1 == 'CH0' and ch2 == 'CH1') or (ch1 == 'CH1' and ch2 == 'CH0')), 'Incorrect channel; Channel should be CH0 or CH1'
                if (ch1 == 'CH0' and ch2 == 'CH1') or (ch1 == 'CH1' and ch2 == 'CH0'):
                    self.channel = 3
            elif len(channel) == 0:
                return self.test_channel
            else:
                assert( 1 == 2 ), 'Incorrect argument'

    def digitizer_sample_rate(self, *s_rate):
        """
        Set or query sample rate; Range: 500 MHz - 1.907 kHz
        Input: digitizer_sample_rate('500'); Sample rate is in MHz
        Default: '500';
        Output: '500 MHz'
        """
        if self.test_flag != 'test':
            self.setting_change_count = 1

            if len(s_rate) == 1:
                rate = 1000000 * int(s_rate[0])
                if rate <= 1000000 * self.sample_rate_max and rate >= 1000000 * self.sample_rate_min:
                    closest_available = min(self.sample_rate_list, key = lambda x: abs(x - rate))
                    if int(closest_available) != rate:
                        general.message("Desired sample rate cannot be set, the nearest available value " + str(closest_available) + " is used")
                    self.sample_rate = closest_available / 1000000
                
                else:
                    general.message('Incorrect sample rate; Should be 500 <= Rate <= 50')
                    sys.exit()

            elif len(s_rate) == 0:
                return str(self.sample_rate / 1000000) + ' MHz'

            # to update on-the-fly
            if self.state == 0:
                pass
            elif self.state == 1:
                spcm_dwSetParam_i64 (self.hCard, SPC_SAMPLERATE, int( 1000000 * self.sample_rate ))
                spcm_dwSetParam_i32 (self.hCard, SPC_M2CMD, M2CMD_CARD_WRITESETUP)


        elif self.test_flag == 'test':
            self.setting_change_count = 1

            if len(s_rate) == 1:
                rate = 1000000 * int(s_rate[0])
                closest_available = min(self.sample_rate_list, key = lambda x: abs(x - rate))
                assert(rate <= 1000000 * self.sample_rate_max and rate >= 1000000 * self.sample_rate_min), "Incorrect sample rate; Should be 500 MHz <= Rate <= 0.001907 MHz"
                self.sample_rate = closest_available / 1000000

            elif len(s_rate) == 0:
                return self.test_sample_rate
            else:
                assert( 1 == 2 ), 'Incorrect argument'

    def digitizer_clock_mode(self, *mode):
        """
        Set or query clock mode; the driver needs to know the external fed in frequency
        Input: digitizer_clock_mode('Internal'); Clock mode is 'Internal' or 'External'
        Default: 'Internal';
        Output: 'Internal'
        """
        if self.test_flag != 'test':
            self.setting_change_count = 1

            if len(mode) == 1:
                md = str(mode[0])
                if md == 'Internal':
                    self.clock_mode = 1
                elif md == 'External':
                    self.clock_mode = 32
                else:
                    general.message('Incorrect clock mode; Only Internal and External modes are available')
                    sys.exit()

            elif len(mode) == 0:
                if self.clock_mode == 1:
                    return 'Internal'
                elif self.clock_mode == 32:
                    return 'External'

        elif self.test_flag == 'test':
            self.setting_change_count = 1

            if len(mode) == 1:
                md = str(mode[0])
                assert(md == 'Internal' or md == 'External'), "Incorrect clock mode; Only Internal and External modes are available"
                if md == 'Internal':
                    self.clock_mode = 1
                elif md == 'External':
                    self.clock_mode = 32

            elif len(mode) == 0:
                return self.test_clock_mode
            else:
                assert( 1 == 2 ), 'Incorrect argument'

    def digitizer_reference_clock(self, *ref_clock):
        """
        Set or query reference clock; the driver needs to know the external fed in frequency
        Input: digitizer_reference_clock(100); Reference clock is in MHz; Range: 10 - 100
        Default: '100';
        Output: '200 MHz'
        """
        if self.test_flag != 'test':
            self.setting_change_count = 1

            if len(ref_clock) == 1:
                rate = int(ref_clock[0])
                if rate <= self.sample_ref_clock_max and rate >= self.sample_ref_clock_min:
                    self.reference_clock = rate
                else:
                    general.message('Incorrect reference clock; Should be 100 MHz <= Clock <= 10 MHz')
                    sys.exit()

            elif len(ref_clock) == 0:
                return str(self.reference_clock) + ' MHz'

        elif self.test_flag == 'test':
            self.setting_change_count = 1

            if len(ref_clock) == 1:
                rate = int(ref_clock[0])
                assert(rate <= self.sample_ref_clock_max and rate >= self.sample_ref_clock_min), "Incorrect reference clock; Should be 100 MHz <= Clock <= 10 MHz"
                self.reference_clock = rate

            elif len(ref_clock) == 0:
                return self.test_ref_clock
            else:
                assert( 1 == 2 ), 'Incorrect argument'

    def digitizer_card_mode(self, *mode):
        """
        Set or query digitizer mode;

        'Single' is "Data acquisition to on-board memory for one single trigger event."
        "Average" is "The memory is segmented and with each trigger condition a predefined number of samples, a
        segment, is acquired."

        Input: digitizer_card_mode('Single'); Card mode is 'Single'; 'Average';
        Default: 'Single';
        Output: 'Single'
        """
        if self.test_flag != 'test':
            self.setting_change_count = 1

            if len(mode) == 1:
                md = str(mode[0])
                if md == 'Single':
                    self.card_mode = 1
                elif md == 'Average':
                    self.card_mode = 131072
                else:
                    general.message('Incorrect card mode; Only Single and Average modes are available')
                    sys.exit()

            elif len(mode) == 0:
                if self.card_mode == 1:
                    return 'Single'
                elif self.card_mode == 131072:
                    return 'Average'

        elif self.test_flag == 'test':
            self.setting_change_count = 1

            if len(mode) == 1:
                md = str(mode[0])
                assert(md == 'Single' or md == 'Average'), "Incorrect card mode; Only Single and Average modes are available"
                if md == 'Single':
                    self.card_mode = 1
                elif md == 'Average':
                    self.card_mode = 131072
              
            elif len(mode) == 0:
                return self.test_card_mode        
            else:
                assert( 1 == 2 ), 'Incorrect argument'

    def digitizer_trigger_channel(self, *ch):
        """
        Set or query trigger channel;
        Input: digitizer_trigger_channel('Software'); Trigger channel is 'Software'; 'External'
        Default: 'External';
        Output: 'Software'
        """
        if self.test_flag != 'test':
            self.setting_change_count = 1

            if len(ch) == 1:
                md = str(ch[0])
                if md == 'Software':
                    self.trigger_ch = 1
                elif md == 'External':
                    self.trigger_ch = 2
                else:
                    general.message('Incorrect trigger channel; Only Software and External modes are available')
                    sys.exit()

            elif len(ch) == 0:
                if self.trigger_ch == 1:
                    return 'Software'
                elif self.trigger_ch == 2:
                    return 'External'

        elif self.test_flag == 'test':
            self.setting_change_count = 1

            if len(ch) == 1:
                md = str(ch[0])
                assert(md == 'Software' or md == 'External'), "Incorrect trigger channel; Only Software and External modes are available"
                if md == 'Software':
                    self.trigger_ch = 1
                elif md == 'External':
                    self.trigger_ch = 2

            elif len(ch) == 0:
                return self.test_trigger_ch
            else:
                assert( 1 == 2 ), 'Incorrect argument'

    def digitizer_trigger_mode(self, *mode):
        """
        Set or query trigger mode;
        Input: digitizer_trigger_mode('Positive'); Trigger mode is 'Positive'; 'Negative'; 'High'; 'Low'
        Default: 'Positive';
        Output: 'Positive'
        """
        if self.test_flag != 'test':
            self.setting_change_count = 1

            if len(mode) == 1:
                md = str(mode[0])
                if md == 'Positive':
                    self.trigger_mode = 1
                elif md == 'Negative':
                    self.trigger_mode = 2
                elif md == 'High':
                    self.trigger_mode = 8
                elif md == 'Low':
                    self.trigger_mode = 10
                else:
                    general.message("Incorrect trigger mode; Only Positive, Negative, High, and Low are available")
                    sys.exit()

            elif len(mode) == 0:
                if self.trigger_mode == 1:
                    return 'Positive'
                elif self.trigger_mode == 2:
                    return 'Negative'
                elif self.trigger_mode == 8:
                    return 'High'
                elif self.trigger_mode == 10:
                    return 'Low'

        elif self.test_flag == 'test':
            self.setting_change_count = 1

            if len(mode) == 1:
                md = str(mode[0])
                assert(md == 'Positive' or md == 'Negative' or md == 'High' or md == 'Low'), "Incorrect trigger mode; \
                    Only Positive, Negative, High, and Low are available"
                if md == 'Positive':
                    self.trigger_mode = 1
                elif md == 'Negative':
                    self.trigger_mode = 2
                elif md == 'High':
                    self.trigger_mode = 8
                elif md == 'Low':
                    self.trigger_mode = 10

            elif len(mode) == 0:
                return self.test_trigger_mode        
            else:
                assert( 1 == 2 ), 'Incorrect argument'

    def digitizer_number_of_averages(self, *averages):
        """
        Set or query number of averages;
        Input: digitizer_number_of_averages(10); Number of averages from 1 to 100000; 0 is infinite averages
        Default: 2;
        Output: '100'
        """
        if self.test_flag != 'test':
            self.setting_change_count = 1

            if len(averages) == 1:
                ave = int(averages[0])
                self.aver = ave

            elif len(averages) == 0:
                return self.aver

        elif self.test_flag == 'test':
            self.setting_change_count = 1

            if len(averages) == 1:
                ave = int(averages[0])
                assert( ave >= 0 and ave <= self.averages_max ), "Incorrect number of averages; Should be 0 <= Averages <= 100000"
                self.aver = ave

            elif len(aver) == 0:
                return self.test_averages     
            else:
                assert( 1 == 2 ), 'Incorrect argument'

    def digitizer_trigger_delay(self, *delay):
        """
        Set or query trigger delay;
        Input: digitizer_trigger_delay('100 ns'); delay in [ms, us, ns]
        Step is 16 sample clock; will be rounded if input is not divisible by 16 sample clock
        Default: 0 ns;
        Output: '100 ns'
        """
        if self.test_flag != 'test':
            self.setting_change_count = 1

            if len(delay) == 1:
                temp = delay[0].split(' ')
                delay_num = int(temp[0])
                dimen = str(temp[1])

                if dimen in self.timebase_dict:
                    flag = self.timebase_dict[dimen]
                    # trigger delay in samples; maximum is 8589934576, step is 16
                    del_in_sample = int( delay_num*flag*self.sample_rate / 1000 )
                    if del_in_sample % 16 != 0:
                        #self.delay = int( 16*(del_in_sample // 16) )
                        self.delay = self.round_to_closest(del_in_sample, 16)
                        general.message('Delay should be divisible by 16 samples (32 ns at 500 MHz); The closest avalaibale number ' + str( self.delay * 1000 / self.sample_rate) + ' ns is used')
                    else:
                        self.delay = del_in_sample

                else:
                    general.message('Incorrect delay dimension; Should be ns, us or ms')
                    sys.exit()

            elif len(delay) == 0:
                return str(self.delay / self.sample_rate * 1000) + ' ns'

        elif self.test_flag == 'test':
            self.setting_change_count = 1

            if len(delay) == 1:
                temp = delay[0].split(' ')
                delay_num = int(temp[0])
                dimen = str(temp[1])

                assert( dimen in self.timebase_dict), 'Incorrect delay dimension; Should be ns, us or ms'
                flag = self.timebase_dict[dimen]
                # trigger delay in samples; maximum is 8589934576, step is 16
                del_in_sample = int( delay_num*flag*self.sample_rate / 1000 )
                if del_in_sample % 16 != 0:
                    #self.delay = int( 16*(del_in_sample // 16) )
                    self.delay = self.round_to_closest(del_in_sample, 16)
                else:
                    self.delay = del_in_sample

                assert(self.delay >= self.delay_min and self.delay <= self.delay_max), 'Incorrect delay; Should be 0 <= Delay <= 8589934560 samples'


            elif len(delay) == 0:
                return self.test_delay
            else:
                assert( 1 == 2 ), 'Incorrect argument'

    def digitizer_input_mode(self, *mode):
        """
        Set or query input mode;
        Input: digitizer_input_mode('HF'); Input mode is 'HF'; 'Buffered'.
        HF mode allows using a high frequency 50 ohm path to have full bandwidth and best dynamic performance.
        Buffered mode allows using a buffered path with all features but limited bandwidth and dynamic performance.
        The specified input mode will be used for both channels.
        Default: 'HF';
        Output: 'Buffered'
        """
        if self.test_flag != 'test':
            self.setting_change_count = 1

            if len(mode) == 1:
                md = str(mode[0])
                if md == 'Buffered':
                    self.input_mode = 0
                elif md == 'HF':
                    self.input_mode = 1
                else:
                    general.message("Incorrect input mode; Only HF and Buffered are available")
                    sys.exit()

            elif len(mode) == 0:
                if self.input_mode == 0:
                    return 'Buffered'
                elif self.input_mode == 1:
                    return 'HF'

        elif self.test_flag == 'test':
            self.setting_change_count = 1

            if len(mode) == 1:
                md = str(mode[0])
                assert(md == 'Buffered' or md == 'HF'), "Incorrect input mode; Only HF and Buffered are available"
                if md == 'Buffered':
                    self.input_mode = 0
                elif md == 'HF':
                    self.input_mode = 1

            elif len(mode) == 0:
                return self.test_input_mode        
            else:
                assert( 1 == 2 ), 'Incorrect argument'        

    def digitizer_amplitude(self, *ampl):
        """
        Set or query range of the channels in mV;
        Input: digitizer_amplitude(500);
        Buffered range is [200, 500, 1000, 2000, 5000, 10000]
        HF range is [500, 1000, 25200, 5000]
        The specified range will be used for both channels.
        Default: '500';
        Output: 'CH0: 500 mV; CH1: 500 mV'
        """
        if self.test_flag != 'test':
            self.setting_change_count = 1

            if len(ampl) == 1:
                amp = int(ampl[0])
                if self.input_mode == 0: # Buffered
                    closest_available = min(self.buffered_mode_range_list, key = lambda x: abs(x - amp))
                    if closest_available != amp:
                        general.message("Desired amplitude cannot be set, the nearest available value " + str(closest_available) + " mV is used")
                    self.amplitude_0 = closest_available
                    self.amplitude_1 = closest_available
                elif self.input_mode == 1: # HF
                    closest_available = min(self.hf_mode_range_list, key = lambda x: abs(x - amp))
                    if closest_available != amp:
                        general.message("Desired amplitude cannot be set, the nearest available value " + str(closest_available) + " mV is used")
                    self.amplitude_0 = closest_available
                    self.amplitude_1 = closest_available
                
                else:
                    general.message('Incorrect amplitude or input mode')
                    sys.exit()

            elif len(ampl) == 0:
                return 'CH0: ' + str(self.amplitude_0) + ' mV; ' + 'CH1: ' + str(self.amplitude_1) + ' mV'

            # to update on-the-fly
            if self.state == 0:
                pass
            elif self.state == 1:
                
                spcm_dwGetParam_i32 (self.hCard, SPC_MIINST_MAXADCVALUE, byref(self.lMaxDACValue))
                spcm_dwSetParam_i32 (self.hCard, SPC_AMP0, self.amplitude_0)
                spcm_dwSetParam_i32 (self.hCard, SPC_AMP1, self.amplitude_1)
                spcm_dwSetParam_i32 (self.hCard, SPC_M2CMD, M2CMD_CARD_WRITESETUP)


        elif self.test_flag == 'test':
            self.setting_change_count = 1

            if len(ampl) == 1:
                amp = int(ampl[0])
                if self.input_mode == 0: # Buffered
                    closest_available = min(self.buffered_mode_range_list, key = lambda x: abs(x - amp))
                    if closest_available != amp:
                        general.message("Desired amplitude cannot be set, the nearest available value " + str(closest_available) + " mV is used")
                    self.amplitude_0 = closest_available
                    self.amplitude_1 = closest_available
                elif self.input_mode == 1: # HF
                    closest_available = min(self.hf_mode_range_list, key = lambda x: abs(x - amp))
                    if closest_available != amp:
                        general.message("Desired amplitude cannot be set, the nearest available value " + str(closest_available) + " mV is used")
                    self.amplitude_0 = closest_available
                    self.amplitude_1 = closest_available
                
                else:
                    assert( 1 == 2), 'Incorrect amplitude or input mode'

            elif len(ampl) == 0:
                return self.test_amplitude

    def digitizer_offset(self, *offset):
        """
        Set or query offset of the channels as a percentage of range;
        The value of the offset (range * percentage) is ALWAYS substracted from the signal
        No offset can be used for 1000 mV and 10000 mV range in Buffered mode
        Input: digitizer_offset('CH0', '1', 'CH1', '50')
        Default: '0'; '0'
        Output: 'CH0: 10'
        """
        if self.test_flag != 'test':
            self.setting_change_count = 1

            if self.input_mode == 0:
                if self.amplitude_0 == 1000 or self.amplitude_0 == 10000:
                    general.message("No offset can be used for 1000 mV and 10000 mV range in Buffered mode")
                    sys.exit()
                elif self.amplitude_1 == 1000 or self.amplitude_1 == 10000:
                    general.message("No offset can be used for 1000 mV and 10000 mV range in Buffered mode")
                    sys.exit()

            if len(offset) == 2:
                ch = str(offset[0])
                ofst = int(offset[1])

                if ch == 'CH0':
                    self.offset_0 = ofst
                elif ch == 'CH1':
                    self.offset_1 = ofst
            
            elif len(offset) == 4:
                ch1 = str(offset[0])
                ofst1 = int(offset[1])
                ch2 = str(offset[2])
                ofst2 = int(offset[3])
                
                if ch1 == 'CH0':
                    self.offset_0 = ofst1
                elif ch1 == 'CH1':
                    self.offset_1 = ofst1
                if ch2 == 'CH0':
                    self.offset_0 = ofst2
                elif ch2 == 'CH1':
                    self.offset_1 = ofst2

            elif len(offset) == 1:
                ch = str(offset[0])
                if ch == 'CH0':
                    return 'CH0: ' + str(self.offset_0)
                elif ch == 'CH1':
                    return 'CH1: ' + str(self.offset_1)

            # to update on-the-fly
            if self.state == 0:
                pass
            elif self.state == 1:
                if ( self.amplitude_0 != 1000 or self.amplitude_0 != 10000 ) and self.input_mode == 0:
                    spcm_dwSetParam_i32 (self.hCard, SPC_OFFS0, -self.offset_0 )
                    spcm_dwSetParam_i32 (self.hCard, SPC_OFFS1, -self.offset_1 )
                elif self.input_mode == 1:
                    spcm_dwSetParam_i32 (self.hCard, SPC_OFFS0, -self.offset_0 )
                    spcm_dwSetParam_i32 (self.hCard, SPC_OFFS1, -self.offset_1 )

                spcm_dwSetParam_i32 (self.hCard, SPC_M2CMD, M2CMD_CARD_WRITESETUP)



        elif self.test_flag == 'test':
            self.setting_change_count = 1

            if self.input_mode == 0:
                assert(self.amplitude_0 != 1000 or self.amplitude_0 != 10000 ), "No offset can be used for 1000 mV and 10000 mV range in Buffered mode"
                assert(self.amplitude_1 != 1000 or self.amplitude_1 != 10000 ), "No offset can be used for 1000 mV and 10000 mV range in Buffered mode"

            if len(offset) == 2:
                ch = str(offset[0])
                ofst = int(offset[1])

                assert(ch == 'CH0' or ch == 'CH1'), "Incorrect channel; Should be CH0 or CH1"
                assert( ofst >= 0 and ofst <= 100 ), "Incorrect offset percentage; Should be 0 <= offset <= 100"
                if ch == 'CH0':
                    self.offset_0 = ofst
                elif ch == 'CH1':
                    self.offset_1 = ofst
            
            elif len(offset) == 4:
                ch1 = str(offset[0])
                ofst1 = int(offset[1])
                ch2 = str(offset[2])
                ofst2 = int(offset[3])

                assert(ch1 == 'CH0' or ch1 == 'CH1'), "Incorrect channel 1; Should be CH0 or CH1"
                assert( ofst1 >= 0 and ofst1 <= 100 ), "Incorrect offset percentage 1; Should be 0 <= offset <= 100"
                assert(ch2 == 'CH0' or ch2 == 'CH1'), "Incorrect channel 2; Should be CH0 or CH1"
                assert( ofst2 >= 0 and ofst2 <= 100 ), "Incorrect offset percentage 2; Should be 0 <= offset <= 100"
                if ch1 == 'CH0':
                    self.offset_0 = ofst1
                elif ch1 == 'CH1':
                    self.offset_1 = ofst1
                if ch2 == 'CH0':
                    self.offset_0 = ofst2
                elif ch2 == 'CH1':
                    self.offset_1 = ofst2

            elif len(offset) == 1:
                ch1 = str(offset[0])
                assert(ch1 == 'CH0' or ch1 == 'CH1'), "Incorrect channel; Should be CH0 or CH1"
                return self.test_offset

            else:
                assert( 1 == 2 ), 'Incorrect arguments'

    def digitizer_coupling(self, *coupling):
        """
        Set or query coupling of the channels; Two options are available: [AC, DC]
        Input: digitizer_coupling('CH0', 'AC', 'CH1', 'DC')
        Default: 'DC'; 'DC'
        Output: 'CH0: AC'
        """
        if self.test_flag != 'test':
            self.setting_change_count = 1
            
            if len(coupling) == 2:
                ch = str(coupling[0])
                cplng = str(coupling[1])
                flag = self.coupling_dict[cplng]
                if ch == 'CH0':
                    self.coupling_0 = flag
                elif ch == 'CH1':
                    self.coupling_1 = flag
            
            elif len(coupling) == 4:
                ch1 = str(coupling[0])
                cplng1 = str(coupling[1])
                flag1 = self.coupling_dict[cplng1]
                ch2 = str(coupling[2])
                cplng2 = str(coupling[3])
                flag2 = self.coupling_dict[cplng2]
                if ch1 == 'CH0':
                    self.coupling_0 = flag1
                elif ch1 == 'CH1':
                    self.coupling_1 = flag1
                if ch2 == 'CH0':
                    self.coupling_0 = flag2
                elif ch2 == 'CH1':
                    self.coupling_1 = flag2

            elif len(coupling) == 1:
                ch = str(coupling[0])
                if ch == 'CH0':
                    return 'CH0: ' + str(self.coupling_0)
                elif ch == 'CH1':
                    return 'CH1: ' + str(self.coupling_1)

        elif self.test_flag == 'test':
            self.setting_change_count = 1

            if len(coupling) == 2:
                ch = str(coupling[0])
                cplng = str(coupling[1])
                assert(ch == 'CH0' or ch == 'CH1'), "Incorrect channel; Should be CH0 or CH1"
                assert( cplng in self.coupling_dict ), "Incorrect coupling; Only DC and AC are available"
                flag = self.coupling_dict[cplng]
                if ch == 'CH0':
                    self.coupling_0 = flag
                elif ch == 'CH1':
                    self.coupling_1 = flag
            
            elif len(coupling) == 4:
                ch1 = str(coupling[0])
                cplng1 = str(coupling[1])
                ch2 = str(coupling[2])
                cplng2 = str(coupling[3])
                assert(ch1 == 'CH0' or ch1 == 'CH1'), "Incorrect channel 1; Should be CH0 or CH1"
                assert( cplng1 in self.coupling_dict ), "Incorrect coupling 1; Only DC and AC are available"
                flag1 = self.coupling_dict[cplng1]
                assert(ch2 == 'CH0' or ch2 == 'CH1'), "Incorrect channel 2; Should be CH0 or CH1"
                assert( cplng2 in self.coupling_dict ), "Incorrect coupling 2; Only DC and AC are available"
                flag2 = self.coupling_dict[cplng2]
                if ch1 == 'CH0':
                    self.coupling_0 = flag1
                elif ch1 == 'CH1':
                    self.coupling_1 = flag1
                if ch2 == 'CH0':
                    self.coupling_0 = flag2
                elif ch2 == 'CH1':
                    self.coupling_1 = flag2

            elif len(coupling) == 1:
                ch1 = str(coupling[0])
                assert(ch1 == 'CH0' or ch1 == 'CH1'), "Incorrect channel; Should be CH0 or CH1"
                return self.test_coupling

            else:
                assert( 1 == 2 ), 'Incorrect arguments'

    def digitizer_impedance(self, *impedance):
        """
        Set or query impedance of the channels in buffered mode; Two options are available: [1 M, 50]
        In the HF mode impedance is fixed at 50 ohm
        Input: digitizer_coupling('CH0', '50', 'CH1', '50')
        Default: '50'; '50'
        Output: 'CH0: 50'
        """
        if self.test_flag != 'test':
            self.setting_change_count = 1
            
            if self.input_mode == 1:
                general.message("Impedance is fixed at 50 Ohm in HF mode")
                sys.exit()

            if len(impedance) == 2:
                ch = str(impedance[0])
                imp = str(impedance[1])
                flag = self.impedance_dict[imp]
                if ch == 'CH0':
                    self.impedance_0 = flag
                elif ch == 'CH1':
                    self.impedance_1 = flag
                
            elif len(impedance) == 4:
                ch1 = str(impedance[0])
                imp1 = str(impedance[1])
                flag1 = self.impedance_dict[imp1]
                ch2 = str(impedance[2])
                imp2 = str(impedance[3])
                flag2 = self.impedance_dict[imp2]

                if ch1 == 'CH0':
                    self.impedance_0 = flag1
                elif ch1 == 'CH1':
                    self.impedance_1 = flag1
                if ch2 == 'CH0':
                    self.impedance_0 = flag2
                elif ch2 == 'CH1':
                    self.impedance_1 = flag2

            elif len(impedance) == 1:
                ch = str(impedance[0])
                if ch == 'CH0':
                    return 'CH0: ' + str(self.impedance_0)
                elif ch == 'CH1':
                    return 'CH1: ' + str(self.impedance_1)

        elif self.test_flag == 'test':
            self.setting_change_count = 1

            if self.input_mode == 1:
                assert( 1 == 2 ), "Impedance is fixed at 50 Ohm in HF mode"

            if len(impedance) == 2:

                ch = str(impedance[0])
                imp = str(impedance[1])
                assert(ch == 'CH0' or ch == 'CH1'), "Incorrect channel; Should be CH0 or CH1"
                assert( imp in self.impedance_dict ), "Incorrect impedance; Only 1 M and 50 are available"
                flag = self.impedance_dict[imp]
                if ch == 'CH0':
                    self.impedance_0 = flag
                elif ch == 'CH1':
                    self.impedance_1 = flag
            
            elif len(impedance) == 4:
                ch1 = str(impedance[0])
                imp1 = str(impedance[1])
                ch2 = str(impedance[2])
                imp2 = str(impedance[3])
                assert(ch1 == 'CH0' or ch1 == 'CH1'), "Incorrect channel 1; Should be CH0 or CH1"
                assert( imp1 in self.impedance_dict ), "Incorrect impedance 1; Only 1 M and 50 are available"
                flag1 = self.impedance_dict[imp1]
                assert(ch2 == 'CH0' or ch2 == 'CH1'), "Incorrect channel 2; Should be CH0 or CH1"
                assert( imp2 in self.impedance_dict ), "Incorrect impedance 2; Only 1 M and 50 are available"
                flag2 = self.impedance_dict[imp2]
                if ch1 == 'CH0':
                    self.impedance_0 = flag1
                elif ch1 == 'CH1':
                    self.impedance_1 = flag1
                if ch2 == 'CH0':
                    self.impedance_0 = flag2
                elif ch2 == 'CH1':
                    self.impedance_1 = flag2

            elif len(impedance) == 1:
                ch1 = str(impedance[0])
                assert(ch1 == 'CH0' or ch1 == 'CH1'), "Incorrect channel; Should be CH0 or CH1"
                return self.test_impedance

            else:
                assert( 1 == 2 ), 'Incorrect arguments'

    # Auxilary functions
    def round_to_closest(self, x, y):
        """
        A function to round x to divisible by y
        """
        #temp = int( 16*(x // 16) )

        #if temp < x:
        #   temp = temp + 16

        return int( y * ( ( x // y) + (x % y > 0) ) )

def main():
    pass

if __name__ == "__main__":
    main()
