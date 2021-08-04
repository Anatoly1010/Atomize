#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
###AWG
sys.path.append('/home/anatoly/AWG/spcm_examples/python')
#sys.path.append('C:/Users/User/Desktop/Examples/python')
import numpy as np
import atomize.device_modules.config.config_utils as cutil
import atomize.general_modules.general_functions as general

from pyspcm import *
from spcm_tools import *

#### Inizialization
# setting path to *.ini file
path_current_directory = os.path.dirname(__file__)
path_config_file = os.path.join(path_current_directory, 'config','Spectrum_M4I_4450_X8_config.ini')

# configuration data
#config = cutil.read_conf_util(path_config_file)
specific_parameters = cutil.read_specific_parameters(path_config_file)

# Channel assignments
#ch0 = specific_parameters['ch0'] # TRIGGER

timebase_dict = {'ms': 1000000, 'us': 1000, 'ns': 1, }
channel_dict = {'CH0': 0, 'CH1': 1, }
sample_rate_list = [1907, 3814, 7629, 15258, 30517, 61035, 122070, 244140, 488281, 976562, \
                    1953125, 3906250, 7812500, 15625000, 31250000, 62500000, 125000000, \
                    250000000, 500000000]

# Limits and Ranges (depends on the exact model):
#clock = float(specific_parameters['clock'])

# Delays and restrictions
# MaxDACValue corresponds to the amplitude of the output signal; MaxDACValue - Amplitude and so on
# lMaxDACValue = int32 (0)
# spcm_dwGetParam_i32 (hCard, SPC_MIINST_MAXADCVALUE, byref(lMaxDACValue))
# lMaxDACValue.value = lMaxDACValue.value - 1
maxCAD = 8191 # MaxCADValue of the AWG card - 1
minCAD = -8192
amplitude_max = 2500 # mV
amplitude_min = 80 # mV
sample_rate_max = 500 # MHz
sample_rate_min = 0.001907 # MHz
sample_ref_clock_max = 100 # MHz
sample_ref_clock_min = 10 # MHz
averages_max = 100000
delay_max = 8589934576
delay_min = 0 

# Test run parameters
# These values are returned by the modules in the test run 
if len(sys.argv) > 1:
    test_flag = sys.argv[1]
else:
    test_flag = 'None'

test_amplitude = 600
test_channel = 1
test_sample_rate = '500 MHz'
test_clock_mode = 'Internal'
test_ref_clock = 100
test_card_mode = 'Single'
test_trigger_ch = 'External'
test_trigger_mode = 'Positive'
test_averages = 10
test_delay = 0
test_channel = 'CH0'
test_amplitude = '600 mV'
test_num_segments = 1
test_points = 128
test_posttrig_points = 64

class Spectrum_M4I_4450_X8:
    def __init__(self):
        if test_flag != 'test':

            # Collect all parameters for AWG settings
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

            self.amplitude_0 = 600 # amlitude for CH0 in mV
            self.amplitude_1 = 533 # amlitude for CH0 in mV
            self.num_segments = 1 # number of segments for 'Multi mode'
            
            # change of settings
            self.setting_change_count = 0

            # state counter
            self.state = 0

        elif test_flag == 'test':
            # Collect all parameters for AWG settings
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

            self.amplitude_0 = 600
            self.amplitude_1 = 533
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
        if test_flag != 'test':
            
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
                er = spcm_dwSetParam_i64 (self.hCard, SPC_SAMPLERATE, int( 1000000 * self.sample_rate ))
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
                # TO DO:
                spcm_dwSetParam_i32(self.hCard, SPC_MEMSIZE, self.points)
                spcm_dwSetParam_i32(self.hCard, SPC_POSTTRIGGER, self.posttrig_points)

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
            spcm_dwSetParam_i32 (self.hCard, SPC_CHENABLE, self.channel)
            # TO DO
            spcm_dwSetParam_i32 (self.hCard, SPC_AMP0, int32 (1000))
            spcm_dwSetParam_i32 (self.hCard, SPC_AMP1, int32 (1000))

            # define the memory size / max amplitude
            #llMemSamples = int64 (self.memsize)
            #lBytesPerSample = int32(0)
            #spcm_dwGetParam_i32 (hCard, SPC_MIINST_BYTESPERSAMPLE,  byref(lBytesPerSample))
            #lSetChannels = int32 (0)
            #spcm_dwGetParam_i32 (hCard, SPC_CHCOUNT, byref (lSetChannels))

            # MaxDACValue corresponds to the amplitude of the output signal; MaxDACValue - Amplitude and so on
            lMaxDACValue = int32 (0)
            spcm_dwGetParam_i32 (self.hCard, SPC_MIINST_MAXADCVALUE, byref(lMaxDACValue))
            lMaxDACValue.value = lMaxDACValue.value - 1

            if lMaxDACValue.value == maxCAD:
                pass
            else:
                general.message('maxCAD value does not equal to lMaxDACValue.value')
                sys.exit()

            if self.channel == 1 or self.channel == 2:
                # MAYBE DIFFERENT FOR AVERAGE MODE
                self.qwBufferSize = uint64 (self.points * 2 * 1) # in bytes. samples with 2 bytes each, one channel active
            elif self.channel == 3:
                self.qwBufferSize = uint64 (self.points * 2 * 2)

            self.lNotifySize = int32 (0) # driver should notify program after all data has been transfered

            spcm_dwSetParam_i32 (self.hCard, SPC_M2CMD, M2CMD_CARD_WRITESETUP)

        elif test_flag == 'test':
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
        Enabled channels is CH0 and CH1; Range of CH0 is '1000 mV'; Range of CH1 is '1000 mV';
        Number of segments is 1; Number of points is 128 samples; Posttriger points is 64;
        """
        if test_flag != 'test':

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
            spcm_dwSetParam_i32 (self.hCard, SPC_M2CMD, M2CMD_CARD_WAITREADY | M2CMD_DATA_WAITDMA)

            # this is the point to do anything with the data
            lBitsPerSample = int32 (0)
            spcm_dwGetParam_i32 (self.hCard, SPC_MIINST_BITSPERSAMPLE, byref (lBitsPerSample)) # lBitsPerSample.value = 14

            pnData = cast  (pvBuffer, ptr16) # cast to pointer to 16bit integer
            if self.channel == 1 or self.channel == 2:
                data = np.ctypeslib.as_array(pnData, shape = (int( self.qwBufferSize.value / 1 ), ))
                xs = np.arange( len(data) ) / (self.sample_rate * 1000000)

                return xs, data
            elif self.channel == 3:
                data = np.ctypeslib.as_array(pnData, shape = (int( self.qwBufferSize.value / 2 ), ))
                # in V
                # CH0
                data1 = data[0::2] * 1 / ( maxCAD + 1 )     # * Range of the chanell
                # CH1
                data2 = data[1::2] * 1 / ( maxCAD + 1 )

                xs = np.arange( len(data1) ) / (self.sample_rate * 1000000)
                
                return xs, data1, data2

            #print( len(data) )
            #xs = 2*np.arange( int(qwBufferSize.value / 4) )

            # test or error message
            #general.message(dwError)

            # clean up
            #spcm_vClose (hCard)

        elif test_flag == 'test':
            dummy = np.zeros( self.points )
            if self.channel == 1 or self.channel == 2:
                return dummy, dummy
            elif self.channel == 3:
                return dummy, dummy, dummy

    def digitizer_close(self):
        """
        Close the digitizer. No argument; No output
        """
        if test_flag != 'test':
            # clean up
            spcm_vClose (self.hCard)

        elif test_flag == 'test':
            pass

    def digitizer_stop(self):
        """
        Stop the digitizer. No argument; No output
        """
        if test_flag != 'test':

            # open card
            #hCard = spcm_hOpen( create_string_buffer (b'/dev/spcm0') )
            #if hCard == None:
            #    general.message("No card found...")
            #    sys.exit()
            spcm_dwSetParam_i32 (self.hCard, SPC_M2CMD, M2CMD_CARD_STOP)
            #general.message('AWG card stopped')

        elif test_flag == 'test':
            pass

    def digitizer_number_of_points(self, *points):
        """
        Set or query number of points;
        Input: digitizer_number_of_points(128); Number of points should be divisible by 16; 32 is the minimum
        Default: 128;
        Output: '128'
        """
        if test_flag != 'test':
            self.setting_change_count = 1

            if len(points) == 1:
                pnts = int(points[0])
                if pnts < 32:
                    pnts = 32
                    general.message('Number of points must be more than 32')
                if pnts % 16 != 0:
                    general.message('Number of points should be divisible by 16; The closest avalaibale number is used')
                    self.points = int( 16*(pnts // 16) )
                else:
                    self.points = pnts

            elif len(points) == 0:
                return self.points

        elif test_flag == 'test':
            self.setting_change_count = 1

            if len(points) == 1:
                pnts = int(points[0])
                assert( pnts >= 32 ), "Number of points must be more than 32"
                if pnts % 16 != 0:
                    #general.message('Number of points should be divisible by 16; The closest avalaibale number is used')
                    self.points = int( 16*(pnts // 16) )
                else:
                    self.points = pnts

            elif len(points) == 0:
                return test_points    
            else:
                assert( 1 == 2 ), 'Incorrect argument'

    def digitizer_posttrigger(self, *post_points):
        """
        Set or query number of posttrigger points;
        Input: digitizer_posttrigger(64); Number of points should be divisible by 16; 16 is the minimum
        Default: 64;
        Output: '64'
        """
        if test_flag != 'test':
            self.setting_change_count = 1

            if len(post_points) == 1:
                pnts = int(post_points[0])
                if pnts < 16:
                    pnts = 16
                    general.message('Number of posttrigger points must be more than 16')
                if pnts % 16 != 0:
                    general.message('Number of posttrigger points should be divisible by 16; The closest avalaibale number is used')
                    self.posttrig_points = int( 16*(pnts // 16) )
                else:
                    self.posttrig_points = pnts
                if self.posttrig_points > self.points:
                    general.message('Number of posttrigger points should be less than number of points; The closest avalaibale number is used')
                    self.posttrig_points = self.points

            elif len(post_points) == 0:
                return self.posttrig_points

        elif test_flag == 'test':
            self.setting_change_count = 1

            if len(post_points) == 1:
                pnts = int(post_points[0])
                assert( pnts >= 16 ), "Number of points must be more than 16"
                if pnts % 16 != 0:
                    #general.message('Number of points should be divisible by 16; The closest avalaibale number is used')
                    self.posttrig_points = int( 16*(pnts // 16) )
                else:
                    self.posttrig_points = pnts
                if self.posttrig_points > self.points:
                    #general.message('Number of posttrigger points should be less than number of points; The closest avalaibale number is used')
                    self.posttrig_points = self.points                

            elif len(post_points) == 0:
                return test_posttrig_points    
            else:
                assert( 1 == 2 ), 'Incorrect argument'
    
    # TO DO
    def awg_number_of_segments(self, *segmnets):
        """
        Set or query the number of segments for 'Multi" card mode;
        AWG should be in 'Multi' mode. Please, refer to awg_card_mode() function
        Input: awg_number_of_segments(2); Number of segment is from the range 0-200
        Default: 1;
        Output: '2'
        """
        if test_flag != 'test':
            self.setting_change_count = 1

            if len(segmnets) == 1:
                seg = int(segmnets[0])
                if self.card_mode == 512:
                    self.num_segments = seg
                elif self.card_mode == 32768 and seg == 1:
                    self.num_segments = seg
                else:
                    general.message('AWG is not in Multi mode')
                    sys.exit()
            elif len(segmnets) == 0:
                return self.num_segments

        elif test_flag == 'test':
            self.setting_change_count = 1

            if len(segmnets) == 1:
                seg = int(segmnets[0])
                if seg != 1:
                    assert( self.card_mode == 512), 'Number of segments higher than one is available only in Multi mode. Please, change it using awg_card_mode()'
                assert (seg > 0 and seg <= 200), 'Incorrect number of segments; Should be 0 < segmenets <= 200'
                self.num_segments = seg

            elif len(segmnets) == 0:
                return test_num_segments
            else:
                assert( 1 == 2 ), 'Incorrect argumnet'

    def digitizer_channel(self, *channel):
        """
        Enable the specified channel or query enabled channels;
        Input: digitizer_channel('CH0', 'CH1'); Channel is 'CH0' or 'CH1'
        Default: both channels are enabled
        Output: 'CH0'
        """
        if test_flag != 'test':
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

        elif test_flag == 'test':
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
                return test_channel
            else:
                assert( 1 == 2 ), 'Incorrect argument'

    def digitizer_sample_rate(self, *s_rate):
        """
        Set or query sample rate; Range: 500 MHz - 1.907 kHz
        Input: digitizer_sample_rate('500'); Sample rate is in MHz
        Default: '500';
        Output: '500 MHz'
        """
        if test_flag != 'test':
            self.setting_change_count = 1

            if len(s_rate) == 1:
                rate = 1000000 * int(s_rate[0])
                if rate <= sample_rate_max and rate >= sample_rate_min:
                    closest_available = min(sample_rate_list, key = lambda x: abs(x - rate))
                    if int(closest_available) != rate:
                        general.message("Desired sample rate cannot be set, the nearest available value " + str(closest_available) + " is used")
                    self.sample_rate = closest_available / 1000000
                
                else:
                    general.message('Incorrect sample rate; Should be 500 <= Rate <= 50')
                    sys.exit()

            elif len(s_rate) == 0:
                return str(self.sample_rate / 1000000) + ' MHz'

        elif test_flag == 'test':
            self.setting_change_count = 1

            if len(s_rate) == 1:
                rate = 1000000 * int(s_rate[0])
                closest_available = min(sample_rate_list, key = lambda x: abs(x - rate))
                assert(rate <= sample_rate_max and rate >= sample_rate_min), "Incorrect sample rate; Should be 500 MHz <= Rate <= 0.001907 MHz"
                self.sample_rate = closest_available / 1000000

            elif len(s_rate) == 0:
                return test_sample_rate
            else:
                assert( 1 == 2 ), 'Incorrect argument'

    def digitizer_clock_mode(self, *mode):
        """
        Set or query clock mode; the driver needs to know the external fed in frequency
        Input: digitizer_clock_mode('Internal'); Clock mode is 'Internal' or 'External'
        Default: 'Internal';
        Output: 'Internal'
        """
        if test_flag != 'test':
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

        elif test_flag == 'test':
            self.setting_change_count = 1

            if len(mode) == 1:
                md = str(mode[0])
                assert(md == 'Internal' or md == 'External'), "Incorrect clock mode; Only Internal and External modes are available"
                if md == 'Internal':
                    self.clock_mode = 1
                elif md == 'External':
                    self.clock_mode = 32

            elif len(mode) == 0:
                return test_clock_mode
            else:
                assert( 1 == 2 ), 'Incorrect argument'

    def digitizer_reference_clock(self, *ref_clock):
        """
        Set or query reference clock; the driver needs to know the external fed in frequency
        Input: digitizer_reference_clock(100); Reference clock is in MHz; Range: 10 - 100
        Default: '100';
        Output: '200 MHz'
        """
        if test_flag != 'test':
            self.setting_change_count = 1

            if len(ref_clock) == 1:
                rate = int(ref_clock[0])
                if rate <= sample_ref_clock_max and rate >= sample_ref_clock_min:
                    self.reference_clock = rate
                else:
                    general.message('Incorrect reference clock; Should be 100 MHz <= Clock <= 10 MHz')
                    sys.exit()

            elif len(ref_clock) == 0:
                return str(self.reference_clock) + ' MHz'

        elif test_flag == 'test':
            self.setting_change_count = 1

            if len(ref_clock) == 1:
                rate = int(ref_clock[0])
                assert(rate <= sample_ref_clock_max and rate >= sample_ref_clock_min), "Incorrect reference clock; Should be 100 MHz <= Clock <= 10 MHz"
                self.reference_clock = rate

            elif len(ref_clock) == 0:
                return test_ref_clock
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
        if test_flag != 'test':
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

        elif test_flag == 'test':
            self.setting_change_count = 1

            if len(mode) == 1:
                md = str(mode[0])
                assert(md == 'Single' or md == 'Average'), "Incorrect card mode; Only Single and Average modes are available"
                if md == 'Single':
                    self.card_mode = 1
                elif md == 'Average':
                    self.card_mode = 131072
              
            elif len(mode) == 0:
                return test_card_mode        
            else:
                assert( 1 == 2 ), 'Incorrect argument'

    def digitizer_trigger_channel(self, *ch):
        """
        Set or query trigger channel;
        Input: digitizer_trigger_channel('Software'); Trigger channel is 'Software'; 'External'
        Default: 'External';
        Output: 'Software'
        """
        if test_flag != 'test':
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

        elif test_flag == 'test':
            self.setting_change_count = 1

            if len(ch) == 1:
                md = str(ch[0])
                assert(md == 'Software' or md == 'External'), "Incorrect trigger channel; Only Software and External modes are available"
                if md == 'Software':
                    self.trigger_ch = 1
                elif md == 'External':
                    self.trigger_ch = 2

            elif len(ch) == 0:
                return test_trigger_ch
            else:
                assert( 1 == 2 ), 'Incorrect argument'

    def digitizer_trigger_mode(self, *mode):
        """
        Set or query trigger mode;
        Input: digitizer_trigger_mode('Positive'); Trigger mode is 'Positive'; 'Negative'; 'High'; 'Low'
        Default: 'Positive';
        Output: 'Positive'
        """
        if test_flag != 'test':
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

        elif test_flag == 'test':
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
                return test_trigger_mode        
            else:
                assert( 1 == 2 ), 'Incorrect argument'

    def digitizer_number_of_averages(self, *averages):
        """
        Set or query number of averages;
        Input: digitizer_number_of_averages(10); Number of averages from 1 to 100000; 0 is infinite averages
        Default: 10;
        Output: '100'
        """
        if test_flag != 'test':
            self.setting_change_count = 1

            if len(averages) == 1:
                ave = int(averages[0])
                self.aver = ave

            elif len(averages) == 0:
                return self.aver

        elif test_flag == 'test':
            self.setting_change_count = 1

            if len(averages) == 1:
                ave = int(averages[0])
                assert( ave >= 0 and ave <= averages_max ), "Incorrect number of averages; Should be 0 <= Averages <= 100000"
                self.aver = ave

            elif len(aver) == 0:
                return test_averages     
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
        if test_flag != 'test':
            self.setting_change_count = 1

            if len(delay) == 1:
                temp = delay[0].split(' ')
                delay_num = int(temp[0])
                dimen = str(temp[1])

                if dimen in timebase_dict:
                    flag = timebase_dict[dimen]
                    # trigger delay in samples; maximum is 8589934576, step is 16
                    del_in_sample = int( delay_num*flag*self.sample_rate / 1000 )
                    if del_in_sample % 16 != 0:
                        general.message('Delay should be divisible by 16 samples (32 ns at 500 MHz); The closest avalaibale number is used')
                        self.delay = int( 16*(del_in_sample // 16) )
                    else:
                        self.delay = del_in_sample

                else:
                    general.message('Incorrect delay dimension; Should be ns, us or ms')
                    sys.exit()

            elif len(delay) == 0:
                return str(self.delay / self.sample_rate * 1000) + ' ns'

        elif test_flag == 'test':
            self.setting_change_count = 1

            if len(delay) == 1:
                temp = delay[0].split(' ')
                delay_num = int(temp[0])
                dimen = str(temp[1])

                assert( dimen in timebase_dict), 'Incorrect delay dimension; Should be ns, us or ms'
                flag = timebase_dict[dimen]
                # trigger delay in samples; maximum is 8589934576, step is 16
                del_in_sample = int( delay_num*flag*self.sample_rate / 1000 )
                if del_in_sample % 16 != 0:
                    self.delay = int( 16*(del_in_sample // 16) )
                else:
                    self.delay = del_in_sample

                assert(self.delay >= delay_min and self.delay <= delay_max), 'Incorrect delay; Should be 0 <= Delay <= 8589934560 samples'


            elif len(delay) == 0:
                return test_delay
            else:
                assert( 1 == 2 ), 'Incorrect argument'

    # TO DO different channel settings
    def awg_amplitude(self, *amplitude):
        """
        Set or query amplitude of the channel;
        Input: awg_amplitude('CH0', '600'); amplitude is in mV
        awg_amplitude('CH0', '600', 'CH1', '600')
        Default: CH0 - 600 mV; CH1 - 533 mV;
        Output: '600 mV'
        """
        if test_flag != 'test':
            self.setting_change_count = 1

            if len(amplitude) == 2:
                ch = str(amplitude[0])
                ampl = int(amplitude[1])
                if ch == 'CH0':
                    self.amplitude_0 = ampl
                elif ch == 'CH1':
                    self.amplitude_1 = ampl
            
            elif len(amplitude) == 4:
                ch1 = str(amplitude[0])
                ampl1 = int(amplitude[1])
                ch2 = str(amplitude[2])
                ampl2 = int(amplitude[3])
                if ch1 == 'CH0':
                    self.amplitude_0 = ampl1
                elif ch1 == 'CH1':
                    self.amplitude_1 = ampl2
                if ch2 == 'CH0':
                    self.amplitude_0 = ampl1
                elif ch2 == 'CH1':
                    self.amplitude_1 = ampl2

            elif len(amplitude) == 1:
                ch = str(amplitude[0])
                if ch == 'CH0':
                    return str(self.amplitude_0) + ' mV'
                elif ch == 'CH1':
                    return str(self.amplitude_1) + ' mV'

        elif test_flag == 'test':
            self.setting_change_count = 1

            if len(amplitude) == 2:
                ch = str(amplitude[0])
                ampl = int(amplitude[1])
                assert(ch == 'CH0' or ch == 'CH1'), "Incorrect channel; Should be CH0 or CH1"
                assert( ampl >= amplitude_min and ampl <= amplitude_max ), "Incorrect amplitude; Should be 80 <= amplitude <= 2500"
                if ch == 'CH0':
                    self.amplitude_0 = ampl
                elif ch == 'CH1':
                    self.amplitude_1 = ampl
            
            elif len(amplitude) == 4:
                ch1 = str(amplitude[0])
                ampl1 = int(amplitude[1])
                ch2 = str(amplitude[2])
                ampl2 = int(amplitude[3])
                assert(ch1 == 'CH0' or ch1 == 'CH1'), "Incorrect channel 1; Should be CH0 or CH1"
                assert( ampl1 >= amplitude_min and ampl1 <= amplitude_max ), "Incorrect amplitude 1; Should be 80 <= amplitude <= 2500"
                assert(ch2 == 'CH0' or ch2 == 'CH1'), "Incorrect channel 2; Should be CH0 or CH1"
                assert( ampl2 >= amplitude_min and ampl2 <= amplitude_max ), "Incorrect amplitude 2; Should be 80 <= amplitude <= 2500"
                if ch1 == 'CH0':
                    self.amplitude_0 = ampl1
                elif ch1 == 'CH1':
                    self.amplitude_1 = ampl2
                if ch2 == 'CH0':
                    self.amplitude_0 = ampl1
                elif ch2 == 'CH1':
                    self.amplitude_1 = ampl2

            elif len(amplitude) == 1:
                assert(ch1 == 'CH0' or ch1 == 'CH1'), "Incorrect channel; Should be CH0 or CH1"
                return test_amplitude

            else:
                assert( 1 == 2 ), 'Incorrect arguments'

    # Auxilary functions
    def closest_power_of_two(self, x):
        """
        A function to round card memory or sequence segments
        """
        return 2**int(log2(x - 1) + 1 )


def main():
    pass

if __name__ == "__main__":
    main()

