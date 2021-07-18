#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
###AWG
#sys.path.append('/home/pulseepr/Sources/AWG/Examples/python')
from math import sin, pi, exp, log2
from itertools import groupby, chain
import numpy as np
import atomize.device_modules.config.config_utils as cutil
import atomize.general_modules.general_functions as general

#from pyspcm import *
#from spcm_tools import *

#### Inizialization
# setting path to *.ini file
path_current_directory = os.path.dirname(__file__)
path_config_file = os.path.join(path_current_directory, 'config','Spectrum_M4I_6631_X8_config.ini')

# configuration data
#config = cutil.read_conf_util(path_config_file)
specific_parameters = cutil.read_specific_parameters(path_config_file)

# Channel assignments
#ch0 = specific_parameters['ch0'] # TRIGGER

timebase_dict = {'ms': 1000000, 'us': 1000, 'ns': 1, }
channel_dict = {'CH0': 0, 'CH1': 1, }
function_dict = {'SINE': 0, 'GAUSS': 1, 'SINC': 2, }

# Limits and Ranges (depends on the exact model):
#clock = float(specific_parameters['clock'])
max_pulse_length = int(float(specific_parameters['max_pulse_length'])) # in ns
min_pulse_length = int(float(specific_parameters['min_pulse_length'])) # in ns
max_freq = int(float(specific_parameters['max_freq'])) # in MHz
min_freq = int(float(specific_parameters['min_freq'])) # in MHz

# Delays and restrictions
amplitude_max = 2500 # mV
amplitude_min = 80 # mV
sample_rate_max = 1250 # MHz
sample_rate_min = 50 # MHz
sample_ref_clock_max = 1000 # MHz
sample_ref_clock_min = 10 # MHz
loop_max = 100000
delay_max = 8589934560
delay_min = 0 

# Test run parameters
# These values are returned by the modules in the test run 
if len(sys.argv) > 1:
    test_flag = sys.argv[1]
else:
    test_flag = 'None'

test_amplitude = 600
test_channel = 1
test_sample_rate = '1250 MHz'
test_clock_mode = 'Internal'
test_ref_clock = 100
test_card_mode = 'Single'
test_trigger_ch = 'External'
test_trigger_mode = 'Positive'
test_loop = 0
test_delay = 0
test_channel = 'CH0'
test_amplitude = '600 mV'
test_num_segments = 1

class Spectrum_M4I_6631_X8:
    def __init__(self):
        if test_flag != 'test':

            # Collect all parameters for AWG settings
            self.sample_rate = 1250 # MHz
            self.clock_mode = 1 # 1 is Internal; 32 is External
            self.reference_clock = 100 # MHz
            self.card_mode = 32768 # 32768 is Single; 512 is Multi
            self.trigger_ch = 2 # 1 is Software; 2 is External
            self.trigger_mode = 1 # 1 is Positive; 2 is Negative; 8 is High; 10 is Low
            self.loop = 0 # 0 is infinity
            self.delay = 0 # in sample rate; step is 32; rounded
            self.channel = 3 # 1 is CH0; 2 is CH1; 3 is CH0 + CH1
            self.enable_out_0 = 1 # 1 means ON; 0 means OFF
            self.enable_out_1 = 1 # 1 means ON; 0 means OFF
            self.amplitude_0 = 600 # amlitude for CH0 in mV
            self.amplitude_1 = 533 # amlitude for CH0 in mV
            self.num_segments = 1 # number of segments for 'Multi mode'
            self.memsize = 64 # full card memory
            self.buffer_size = 2*self.memsize # two bytes per sample
            self.segment_memsize = 32 # segment card memory
            # pulse settings
            self.pulse_array = []
            self.pulse_name_array = []

        elif test_flag == 'test':
            # Collect all parameters for AWG settings
            self.sample_rate = 1250 
            self.clock_mode = 1
            self.reference_clock = 100
            self.card_mode = 32768
            self.trigger_ch = 2
            self.trigger_mode = 1
            self.loop = 0
            self.delay = 0
            self.channel = 3
            self.enable_out_0 = 1
            self.enable_out_1 = 1
            self.amplitude_0 = 600
            self.amplitude_1 = 533
            self.num_segments = 1
            self.memsize = 64 # full card memory
            self.buffer_size = 2*self.memsize # two bytes per sample
            self.segment_memsize = 32 # segment card memory
            # pulse settings
            self.pulse_array = []
            self.pulse_name_array = []

    # Module functions
    def awg_name(self):
        answer = 'Spectrum M4I.6631-X8'
        return answer

    def awg_start(self):
        """
        Start AWG card. No argument; No output
        A big function that write all the settings into AWG card.
        Default settings:
        Sample clock is 1250 MHz; Clock mode is 'Internal'; Reference clock is 100 MHz; Card mode is 'Single';
        Trigger channel is 'External'; Trigger mode is 'Positive'; Loop is infinity; Trigger delay is 0;
        Enabled channels is CH0 and CH1; Amplitude of CH0 is '600 mV'; Amplitude of CH1 is '533 mV';
        Number of segments is 1; Card memory size is 64 samples;
        """
        if test_flag != 'test':
            # open card
            hCard = spcm_hOpen (create_string_buffer (b'/dev/spcm0'))
            if hCard == None:
                general.message("No card found...")
                sys.exit()

            # general parameters of the card; internal/external clock
            if self.clock_mode == 1:
                spcm_dwSetParam_i64 (hCard, SPC_SAMPLERATE, MEGA(self.sample_rate))
            elif self.clock_mode == 32:
                spcm_dwSetParam_i32 (hCard, SPC_CLOCKMODE, self.clock_mode)
                spcm_dwSetParam_i64 (hCard, SPC_REFERENCECLOCK, MEGA(self.reference_clock))
                spcm_dwSetParam_i64 (hCard, SPC_SAMPLERATE, MEGA(self.sample_rate))

            # change card mode and memory
            if self.card_mode == 32768:
                spcm_dwSetParam_i32(hCard, SPC_CARDMODE, self.card_mode)
                spcm_dwSetParam_i32(hCard, SPC_MEMSIZE, self.memsize)
            elif self.card_mode == 512:
                spcm_dwSetParam_i32(hCard, SPC_CARDMODE, self.card_mode)
                spcm_dwSetParam_i32(hCard, SPC_MEMSIZE, self.memsize)
                spcm_dwSetParam_i32(hCard, SPC_SEGMENTSIZE, self.segment_memsize)
                
            # trigger
            spcm_dwSetParam_i32(hCard, SPC_TRIG_ORMASK, self.trigger_ch) # software / external
            if self.trigger_ch == 2:
                spcm_dwSetParam_i32(hCard, SPC_TRIG_EXT0_MODE, self.trigger_mode)
            
            # loop
            spcm_dwSetParam_i32(hCard, SPC_LOOPS, self.loop)
            
            # trigger delay
            spcm_dwSetParam_i32( hCard, SPC_TRIG_DELAY, int(self.delay) )

            # set the output channels
            spcm_dwSetParam_i32 (hCard, SPC_CHENABLE, self.channel)
            spcm_dwSetParam_i32 (hCard, SPC_ENABLEOUT0, self.enable_out_0)
            spcm_dwSetParam_i32 (hCard, SPC_ENABLEOUT1, self.enable_out_1)
            spcm_dwSetParam_i32 (hCard, SPC_AMP0, int32 (self.amplitude_0))
            spcm_dwSetParam_i32 (hCard, SPC_AMP1, int32 (self.amplitude_1))

            # define the memory size / max amplitude
            llMemSamples = int64 (self.memsize)
            #lBytesPerSample = int32(0)
            #spcm_dwGetParam_i32 (hCard, SPC_MIINST_BYTESPERSAMPLE,  byref(lBytesPerSample))
            #lSetChannels = int32 (0)
            #spcm_dwGetParam_i32 (hCard, SPC_CHCOUNT, byref (lSetChannels))

            # MaxDACValue corresponds to the amplitude of the output signal; MaxDACValue - Amplitude and so on
            lMaxDACValue = int32 (0)
            spcm_dwGetParam_i32 (hCard, SPC_MIINST_MAXADCVALUE, byref(lMaxDACValue))
            lMaxDACValue.value = lMaxDACValue.value - 1

            # define the buffer
            pnBuffer = c_void_p()
            qwBufferSize = uint64 (self.buffer_size)  # buffer size
            pvBuffer = pvAllocMemPageAligned (qwBufferSize.value)
            pnBuffer = cast (pvBuffer, ptr16)

            # fill the buffer
            if self.card_mode == 32768:
                # convert numpy array to integer
                pnBuffer = (lMaxDACValue.value * self.define_buffer_single()).astype('int64')
            elif self.card_mode == 512:
                pnBuffer = (lMaxDACValue.value * self.define_buffer_multi()).astype('int64')

            # we define the buffer for transfer and start the DMA transfer
            #sys.stdout.write("Starting the DMA transfer and waiting until data is in board memory\n")
            # spcm_dwDefTransfer_i64 (device, buffer_type, direction, event (0=and of transfer), data, offset, buffer length)
            spcm_dwDefTransfer_i64 (hCard, SPCM_BUF_DATA, SPCM_DIR_PCTOCARD, int32 (0), pvBuffer, uint64 (0), qwBufferSize)
            # transfer
            spcm_dwSetParam_i32 (hCard, SPC_M2CMD, M2CMD_DATA_STARTDMA | M2CMD_DATA_WAITDMA)
            general.message("AWG buffer has been transferred to board memory")

            # We'll start and wait until the card has finished or until a timeout occurs
            dwError = spcm_dwSetParam_i32 (hCard, SPC_M2CMD, M2CMD_CARD_START | M2CMD_CARD_ENABLETRIGGER | M2CMD_CARD_WAITTRIGGER)
            # test or error message
            general.message(dwError)

            # clean up
            spcm_vClose (hCard)

        elif test_flag == 'test':
            pass

    def awg_stop(self):
        """
        Stop AWG card. No argument; No output
        """
        if test_flag != 'test':

            # open card
            hCard = spcm_hOpen( create_string_buffer (b'/dev/spcm0') )
            if hCard == None:
                general.message("No card found...")
                sys.exit()

            spcm_dwSetParam_i32 (hCard, SPC_M2CMD, M2CMD_CARD_STOP)

            # clean up
            spcm_vClose (hCard)

            general.message('AWG card stopped.')

        elif test_flag == 'test':
            pass

    def awg_pulse(self, name = 'P0', channel = 'CH0', func = 'SINE', frequency = '200 MHz', phase = 0, length = '16 ns', sigma = '16 ns'):
        """
        A function for awg pulse creation;
        The possible arguments:
        NAME, CHANNEL (CHO, CH1), FUNC (SINE, GAUSS, SINC), FREQUENCY (1 - 280 MHz),
        PHASE (in rad), LENGTH (in ns, us; should be longer than sigma; minimun is 10 ns; maximum is 1900 ns), 
        SIGMA (sigma for gauss; sinc (length = 32 ns, sigma = 16 ns means +-2pi); sine for uniformity )
        Buffer according to arguments will be filled after
        """
        if test_flag != 'test':
            pulse = {'name': name, 'channel': channel, 'function': func, 'frequency': frequency, 'phase' : phase,\
             'length': length, 'sigma': sigma}

            self.pulse_array.append( pulse )
            
        elif test_flag == 'test':
            pulse = {'name': name, 'channel': channel, 'function': func, 'frequency': frequency, 'phase' : phase,\
             'length': length, 'sigma': sigma}

            # Checks
            # two equal names
            temp_name = str(name)
            set_from_list = set(self.pulse_name_array)          
            if temp_name in set_from_list:
                assert (1 == 2), 'Two pulses have the same name. Please, rename'

            self.pulse_name_array.append( pulse['name'] )

            # channels
            temp_ch = str(channel)
            assert (temp_ch in channel_dict), 'Incorrect channel. Only CH0 or CH1 are available'

            # Function type
            temp_func = str(func)
            assert (temp_func in function_dict), 'Incorrect pulse type. Only SINE, GAUSS or SINC are available'

            # Frequency
            temp_freq = frequency.split(" ")
            coef = temp_freq[1]
            p_freq = float(temp_freq[0])
            assert (coef == 'MHz'), 'Incorrect frequency dimension. Only MHz is possible'
            assert(p_freq >= min_freq), 'Frequency is lower than minimum available (' + str(min_freq) +' MHz)'
            assert(p_freq < max_freq), 'Frequency is longer than minimum available (' + str(max_freq) +' MHz)'

            # length
            temp_length = length.split(" ")
            if temp_length[1] in timebase_dict:
                coef = timebase_dict[temp_length[1]]
                p_length = coef*float(temp_length[0])
                assert(p_length >= min_pulse_length), 'Pulse is shorter than minimum available length (' + str(min_pulse_length) +' ns)'
                assert(p_length < max_pulse_length), 'Pulse is longer than maximum available length (' + str(max_pulse_length) +' ns)'
            else:
                assert( 1 == 2 ), 'Incorrect time dimension (ms, us, ns)'

            # sigma
            temp_sigma = sigma.split(" ")
            if temp_sigma[1] in timebase_dict:
                coef = timebase_dict[temp_sigma[1]]
                p_sigma = coef*float(temp_sigma[0])
                assert(p_sigma >= min_pulse_length), 'Sigma is shorter than minimum available length (' + str(min_pulse_length) +' ns)'
                assert(p_sigma < max_pulse_length), 'Sigma is longer than maximum available length (' + str(max_pulse_length) +' ns)'
            else:
                assert( 1 == 2 ), 'Incorrect time dimension (ms, us, ns)'

            # length should be longer than sigma
            assert( p_length >= p_sigma ), 'Pulse length should be longer or equal to sigma'

            self.pulse_array.append( pulse )

    def awg_number_of_segments(self, *segmnets):
        """
        Set or query the number of segments for 'Multi" card mode;
        AWG should be in 'Multi' mode. Please, refer to awg_card_mode() function
        Input: awg_number_of_segments(2); Number of segment is from the range 0-200
        Default: 1;
        Output: '2'
        """
        if test_flag != 'test':
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
            if len(segmnets) == 1:
                seg = int(segmnets[0])
                if seg != 1:
                    assert( self.card_mode == 512), 'AWG is not in Multi mode. Please, change it using awg_card_mode()'
                assert (seg > 0 and seg <= 200), 'Incorrect number of segments; Should be 0 < segmenets <= 200'
                self.num_segments = seg

            elif len(segmnets) == 0:
                return test_num_segments
            else:
                assert( 1 == 2 ), 'Incorrect argumnet'

    def awg_channel(self, *channel):
        """
        Enable output from the specified channel or query enabled channels;
        Input: awg_channel('CH0', 'CH1'); Channel is 'CH0' or 'CH1'
        Default: both channels are enabled
        Output: 'CH0'
        """
        if test_flag != 'test':
            if len(channel) == 1:
                ch = str(channel[0])
                if ch == 'CH0':
                    self.channel = 1
                    self.enable_out_0 = 1
                    self.enable_out_1 = 0
                elif ch == 'CH1':
                    self.channel = 2
                    self.enable_out_0 = 0
                    self.enable_out_1 = 1
                else:
                    general.message('Incorrect channel')
                    sys.exit()
            elif len(channel) == 2:
                ch1 = str(channel[0])
                ch2 = str(channel[1])
                if (ch1 == 'CH0' and ch2 == 'CH1') or (ch1 == 'CH1' and ch2 == 'CH0'):
                    self.channel = 3
                    self.enable_out_0 = 1
                    self.enable_out_1 = 1
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
            if len(channel) == 1:
                ch = str(channel[0])
                assert( ch == 'CH0' or ch == 'CH1' ), 'Incorrect channel; Channel should be CH0 or CH1'
                if ch == 'CH0':
                    self.channel = 1
                    self.enable_out_0 = 1
                    self.enable_out_1 = 0
                elif ch == 'CH1':
                    self.channel = 2
                    self.enable_out_0 = 0
                    self.enable_out_1 = 1
            elif len(channel) == 2:
                ch1 = str(channel[0])
                ch2 = str(channel[1])
                assert( (ch1 == 'CH0' and ch2 == 'CH1') or (ch1 == 'CH1' and ch2 == 'CH0')), 'Incorrect channel; Channel should be CH0 or CH1'
                if (ch1 == 'CH0' and ch2 == 'CH1') or (ch1 == 'CH1' and ch2 == 'CH0'):
                    self.channel = 3
                    self.enable_out_0 = 1
                    self.enable_out_1 = 1
            elif len(channel) == 0:
                return test_channel
            else:
                assert( 1 == 2 ), 'Incorrect argument'

    def awg_sample_rate(self, *s_rate):
        """
        Set or query sample rate; Range: 50 - 1250
        Input: awg_sample_rate('1250'); Sample rate is in MHz
        Default: '1250';
        Output: '1000 MHz'
        """
        if test_flag != 'test':
            if len(s_rate) == 1:
                rate = int(s_rate[0])
                if rate <= sample_rate_max and rate >= sample_rate_min:
                    self.sample_rate = rate
                else:
                    general.message('Incorrect sample rate; Should be 1250 <= Rate <= 50')
                    sys.exit()

            elif len(s_rate) == 0:
                return str(self.sample_rate) + ' MHz'

        elif test_flag == 'test':
            if len(s_rate) == 1:
                rate = int(s_rate[0])
                assert(rate <= sample_rate_max and rate >= sample_rate_min), "Incorrect sample rate; Should be 1250 <= Rate <= 50"
                self.sample_rate = rate

            elif len(s_rate) == 0:
                return test_sample_rate
            else:
                assert( 1 == 2 ), 'Incorrect argument'

    def awg_clock_mode(self, *mode):
        """
        Set or query clock mode; the driver needs to know the external fed in frequency
        Input: awg_clock_mode('Internal'); Clock mode is 'Internal' or 'External'
        Default: 'Internal';
        Output: 'Internal'
        """
        if test_flag != 'test':
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

    def awg_reference_clock(self, *ref_clock):
        """
        Set or query reference clock; the driver needs to know the external fed in frequency
        Input: awg_reference_clock(100); Reference clock is in MHz; Range: 10 - 1000
        Default: '100';
        Output: '200 MHz'
        """
        if test_flag != 'test':
            if len(ref_clock) == 1:
                rate = int(ref_clock[0])
                if rate <= sample_ref_clock_max and rate >= sample_ref_clock_min:
                    self.reference_clock = rate
                else:
                    general.message('Incorrect reference clock; Should be 1000 <= Clock <= 10')
                    sys.exit()

            elif len(ref_clock) == 0:
                return str(self.reference_clock) + ' MHz'

        elif test_flag == 'test':
            if len(ref_clock) == 1:
                rate = int(ref_clock[0])
                assert(rate <= sample_ref_clock_max and rate >= sample_ref_clock_min), "Incorrect reference clock; Should be 1000 <= Clock <= 10"
                self.reference_clock = rate

            elif len(ref_clock) == 0:
                return test_ref_clock
            else:
                assert( 1 == 2 ), 'Incorrect argument'

    def awg_card_mode(self, *mode):
        """
        Set or query card mode; 
        'Single' is "Data generation from on-board memory replaying the complete programmed memory on every detected trigger
        event. The number of replays can be programmed by loops."
        'Multi' is "With every detected trigger event one data block (segment) is replayed."
        Segmented memory is available only in External trigger mode.
        Input: awg_card_mode('Single'); Card mode is 'Single'; 'Multi'
        Default: 'Single';
        Output: 'Single'
        """
        if test_flag != 'test':
            if len(mode) == 1:
                md = str(mode[0])
                if md == 'Single':
                    self.card_mode = 32768
                elif md == 'Multi':
                    self.card_mode = 512
                else:
                    general.message('Incorrect card mode; Only Single and Multi modes are available')
                    sys.exit()

            elif len(mode) == 0:
                if self.card_mode == 32768:
                    return 'Single'
                elif self.card_mode == 512:
                    return 'Multi'

        elif test_flag == 'test':
            if len(mode) == 1:
                md = str(mode[0])
                assert(md == 'Single' or md == 'Multi'), "Incorrect card mode; Only Single and Multi modes are available"
                if md == 'Single':
                    self.card_mode = 32768
                elif md == 'Multi':
                    self.card_mode = 512

            elif len(mode) == 0:
                return test_card_mode        
            else:
                assert( 1 == 2 ), 'Incorrect argument'

    def awg_trigger_channel(self, *ch):
        """
        Set or query trigger channel;
        Input: awg_trigger_channel('Software'); Trigger channel is 'Software'; 'External'
        Default: 'External';
        Output: 'Software'
        """
        if test_flag != 'test':
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

    def awg_trigger_mode(self, *mode):
        """
        Set or query trigger mode;
        Input: awg_trigger_mode('Positive'); Trigger mode is 'Positive'; 'Negative'; 'High'; 'Low'
        Default: 'Positive';
        Output: 'Positive'
        """
        if test_flag != 'test':
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

    def awg_loop(self, *loop):
        """
        Set or query number of loop;
        Input: awg_loop(0); Number of loop from 1 to 100000; 0 is infinite loop
        Default: 0;
        Output: '100'
        """
        if test_flag != 'test':
            if len(loop) == 1:
                lp = int(loop[0])
                self.loop = lp

            elif len(loop) == 0:
                return self.loop

        elif test_flag == 'test':
            if len(loop) == 1:
                lp = int(loop[0])
                assert( lp >= 0 and lp <= loop_max ), "Incorrect number of loops; Should be 0 <= Loop <= 100000"
                self.loop = lp

            elif len(loop) == 0:
                return test_loop      
            else:
                assert( 1 == 2 ), 'Incorrect argument'

    def awg_trigger_delay(self, *delay):
        """
        Set or query trigger delay;
        Input: awg_trigger_delay('100 ns'); delay in [ms, us, ns]
        Step is 32 sample clock; will be rounded if input is not dividable by 32 sample clock
        Default: 0 ns;
        Output: '100 ns'
        """
        if test_flag != 'test':
            if len(delay) == 1:
                temp = delay[0].split(' ')
                delay_num = int(temp[0])
                dimen = str(temp[1])

                if dimen in timebase_dict:
                    flag = timebase_dict[dimen]
                    # trigger delay in samples; maximum is 8589934560, step is 32
                    del_in_sample = int( delay_num*flag*self.sample_rate / 1000 )
                    if del_in_sample % 32 != 0:
                        general.message('Delay should be dividable by 25.8 ns; The closest avalaibale number is used')
                        self.delay = int( 32*(del_in_sample // 32) )
                    else:
                        self.delay = del_in_sample

                else:
                    general.message('Incorrect delay dimension; Should be ns, us or ms')
                    sys.exit()

            elif len(delay) == 0:
                return str(self.delay / self.sample_rate * 1000) + ' ns'

        elif test_flag == 'test':
            if len(delay) == 1:
                temp = delay[0].split(' ')
                delay_num = int(temp[0])
                dimen = str(temp[1])

                assert( dimen in timebase_dict), 'Incorrect delay dimension; Should be ns, us or ms'
                flag = timebase_dict[dimen]
                # trigger delay in samples; maximum is 8589934560, step is 32
                del_in_sample = int( delay_num*flag*self.sample_rate / 1000 )
                if del_in_sample % 32 != 0:
                    self.delay = int( 32*(del_in_sample // 32) )
                else:
                    self.delay = del_in_sample

                assert(self.delay >= delay_min and self.delay <= delay_max), 'Incorrect delay; Should be 0 <= Delay <= 8589934560 samples'


            elif len(delay) == 0:
                return test_delay
            else:
                assert( 1 == 2 ), 'Incorrect argument'

    def awg_amplitude(self, *amplitude):
        """
        Set or query amplitude of the channel;
        Input: awg_amplitude('CH0', '600'); amplitude is in mV
        awg_amplitude('CH0', '600', 'CH1', '600')
        Default: CH0 - 600 mV; CH1 - 533 mV;
        Output: '600 mV'
        """
        if test_flag != 'test':
            if len(amplitude) == 2:
                temp = delay[0].split(' ')
                ch = str(temp[0])
                ampl = int(temp[1])
                if ch == 'CH0':
                    self.amplitude_0 = ampl
                elif ch == 'CH1':
                    self.amplitude_1 = ampl
            
            elif len(amplitude) == 4:
                temp = delay[0].split(' ')
                ch1 = str(temp[0])
                ampl1 = int(temp[1])
                ch2 = str(temp[2])
                ampl2 = int(temp[3])
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
            if len(amplitude) == 2:
                temp = delay[0].split(' ')
                ch = str(temp[0])
                ampl = int(temp[1])
                assert(ch == 'CH0' or ch == 'CH1'), "Incorrect channel; Should be CH0 or CH1"
                assert( ampl >= amplitude_min and ampl <= amplitude_max ), "Incorrect amplitude; Should be 80 <= amplitude <= 2500"
                if ch == 'CH0':
                    self.amplitude_0 = ampl
                elif ch == 'CH1':
                    self.amplitude_1 = ampl
            
            elif len(amplitude) == 4:
                temp = delay[0].split(' ')
                ch1 = str(temp[0])
                ampl1 = int(temp[1])
                ch2 = str(temp[2])
                ampl2 = int(temp[3])
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

    def awg_pulse_list(self):
        """
        Function for saving a pulse list from 
        the script into the
        header of the experimental data
        """
        pulse_list_mod = ''
        for element in self.pulse_array:
            pulse_list_mod = pulse_list_mod + str(element) + '\n'

        return pulse_list_mod

    # Auxilary functions
    def convertion_to_numpy(self, p_array):
        """
        Convertion of the pulse_array into numpy array in the form of
        [channel_number, function, frequency, phase, length, sigma]
        channel_number is from channel_dict
        function is from function_dict
        frequency is a pulse frequency in MHz
        phase is a pulse phase in rad
        length is a pulse length in sample rate
        sigma is a pulse sigma in sample rate
        The numpy array is sorted according to channel number
        """
        if test_flag != 'test':
            i = 0
            pulse_temp_array = []
            num_pulses = len( p_array )
            while i < num_pulses:
                # get channel number
                ch = p_array[i]['channel']
                if ch in channel_dict:
                    ch_num = channel_dict[ch]

                # get function
                fun = p_array[i]['function']
                if fun in function_dict:
                    func = function_dict[fun]
                
                # get length
                leng = p_array[i]['length']

                if leng[-2:] == 'ns':
                    leng_time = int(float(leng[:-3])*self.sample_rate/1000)
                elif leng[-2:] == 'us':
                    leng_time = int(float(leng[:-3])*1000*self.sample_rate/1000)
                elif leng[-2:] == 'ms':
                    leng_time = int(float(leng[:-3])*1000000*self.sample_rate/1000)
                elif leng[-2:] == 's':
                    leng_time = int(float(leng[:-3])*1000000000*self.sample_rate/1000)

                # get frequency
                freq = p_array[i]['frequency']
                freq_mhz = int(float(freq[:-3]))

                # get phase
                phase = float(p_array[i]['phase'])

                # get sigma
                sig = p_array[i]['sigma']

                if sig[-2:] == 'ns':
                    sig_time = int(float(sig[:-3])*self.sample_rate/1000)
                elif sig[-2:] == 'us':
                    sig_time = int(float(sig[:-3])*1000*self.sample_rate/1000)
                elif sig[-2:] == 'ms':
                    sig_time = int(float(sig[:-3])*1000000*self.sample_rate/1000)
                elif sig[-2:] == 's':
                    sig_time = int(float(sig[:-3])*1000000000*self.sample_rate/1000)

                # creating converted array
                pulse_temp_array.append( (ch_num, func, freq_mhz, phase, leng_time, sig_time) )

                i += 1

            # should be sorted according to channel number for corecct splitting into subarrays
            return np.asarray(sorted(pulse_temp_array, key = lambda x: int(x[0])) ) #, dtype = np.int64 

        elif test_flag == 'test':
            i = 0
            pulse_temp_array = []
            num_pulses = len( p_array )
            while i < num_pulses:
                # get channel number
                ch = p_array[i]['channel']
                if ch in channel_dict:
                    ch_num = channel_dict[ch]

                # get function
                fun = p_array[i]['function']
                if fun in function_dict:
                    func = function_dict[fun]
                
                # get length
                leng = p_array[i]['length']

                if leng[-2:] == 'ns':
                    leng_time = int(float(leng[:-3])*self.sample_rate/1000)
                elif leng[-2:] == 'us':
                    leng_time = int(float(leng[:-3])*1000*self.sample_rate/1000)
                elif leng[-2:] == 'ms':
                    leng_time = int(float(leng[:-3])*1000000*self.sample_rate/1000)
                elif leng[-2:] == 's':
                    leng_time = int(float(leng[:-3])*1000000000*self.sample_rate/1000)

                # get frequency
                freq = p_array[i]['frequency']
                freq_mhz = int(float(freq[:-3]))

                # get phase
                phase = float(p_array[i]['phase'])

                # get sigma
                sig = p_array[i]['sigma']

                if sig[-2:] == 'ns':
                    sig_time = int(float(sig[:-3])*self.sample_rate/1000)
                elif sig[-2:] == 'us':
                    sig_time = int(float(sig[:-3])*1000*self.sample_rate/1000)
                elif sig[-2:] == 'ms':
                    sig_time = int(float(sig[:-3])*1000000*self.sample_rate/1000)
                elif sig[-2:] == 's':
                    sig_time = int(float(sig[:-3])*1000000000*self.sample_rate/1000)

                # creating converted array
                pulse_temp_array.append( (ch_num, func, freq_mhz, phase, leng_time, sig_time) )

                i += 1

            # should be sorted according to channel number for corecct splitting into subarrays
            return np.asarray(sorted(pulse_temp_array, key = lambda x: int(x[0])), dtype = np.int64) 

    def splitting_acc_to_channel(self, np_array):
        """
        A function that splits pulse array into
        several array that have the same channel
        I.E. [[0, 0, 10, 70, 10, 16], [0, 0, 20, 70, 10, 16]]
        -> [array([0, 0, 10, 70, 10, 16], [0, 0, 20, 70, 10, 16])]
        Input array should be sorted
        """
        if test_flag != 'test':
            # according to 0 element (channel number)
            answer = np.split(np_array, np.where(np.diff(np_array[:,0]))[0] + 1)
            return answer

        elif test_flag == 'test':
            # according to 0 element (channel number)
            try:
                answer = np.split(np_array, np.where(np.diff(np_array[:,0]))[0] + 1)
            except IndexError:
                assert( 1 == 2 ), 'No AWG pulses are defined'

            return answer

    def preparing_buffer_multi(self):
        """
        A function to prepare everything for buffer filling in the 'Multi' mode
        Check of 'Multi' card mode and 'External' trigger mode.
        Check of number of segments.
        Find a pulse with the maximum length. Determine the memory size.
        Return memory_size, number_of_segments, pulses
        """
        if test_flag != 'test':
            
            #checks
            #if self.card_mode == 32768:
            #    general.message('You are not in Multi mode')
            #    sys.exit()
            #if self.trigger_ch == 'Software':
            #    general.message('Segmented memory is available only in External trigger mode')
            #    sys.exit()

            # maximum length and number of segments array
            num_segments_array = []
            max_length_array = []

            pulses = self.splitting_acc_to_channel( self.convertion_to_numpy(self.pulse_array) )

            # Check that number of segments and number of pulses are equal
            for index, element in enumerate(pulses):
                num_segments_array.append( len(element) )
                max_length_array.append( max( element[:,4] ))
            num_segments_array.append( self.num_segments )

            #gr = groupby( num_segments_array )
            #if (next(gr, True) and not next(gr, False)) == False:
            #    assert(1 == 2), 'Number of segments are not equal to the number of AWG pulses'

            # finding the maximum pulse length to create a buffer
            max_pulse_length = max( max_length_array )
            buffer_per_max_pulse = self.closest_power_of_two( max_pulse_length )
            if buffer_per_max_pulse < 32:
                buffer_per_max_pulse = 32
                general.message('Buffer size was rounded to the minimal available value (32 samples)')

            # determine the memory size (buffer size will be doubled if two channels are enabled)
            memsize = buffer_per_max_pulse*num_segments_array[0]

            return memsize, num_segments_array[0], pulses

        elif test_flag == 'test':            
            
            #checks
            assert( self.card_mode == 512 ), 'You are not in Multi mode'
            assert( self.trigger_ch == 2 ), 'Segmented memory is available only in External trigger mode'

            num_segments_array = []
            max_length_array = []

            pulses = self.splitting_acc_to_channel( self.convertion_to_numpy(self.pulse_array) )

            # Check that number of segments and number of pulses
            # are equal
            for index, element in enumerate(pulses):
                num_segments_array.append( len(element) )
                max_length_array.append( max( element[:,4] ))
            num_segments_array.append( self.num_segments )

            gr = groupby( num_segments_array )
            if (next(gr, True) and not next(gr, False)) == False:
                assert(1 == 2), 'Number of segments are not equal to the number of AWG pulses'

            # finding the maximum pulse length to create a buffer
            max_pulse_length = max( max_length_array )
            buffer_per_max_pulse = self.closest_power_of_two( max_pulse_length )
            if buffer_per_max_pulse < 32:
                buffer_per_max_pulse = 32
                general.message('Buffer size was rounded to the minimal available value (32 samples)')

            # check number of channels and determine the memory size 
            # (buffer size will be doubled if two channels are enabled)
            num_ch = len(pulses)
            assert( (num_ch == 1 and ( self.channel == 1 or self.channel == 2)) or \
                num_ch == 2 and ( self.channel == 3 ) ), 'Number of enabled channels are not equal to the number of channels in AWG pulses'

            memsize = buffer_per_max_pulse*num_segments_array[0]

            return memsize, num_segments_array[0], pulses

    def define_buffer_multi(self):
        """
        Define and fill the buffer in 'Multi' mode;
        Full card memory is splitted into number of segments.
        
        If a number of enabled channels is 1:
        In every segment each index is a new data sample
        
        If a number of enabled channels are 2:
        In every segment every even index is a new data sample for CH0,
        every odd index is a new data sample for CH1.
        """

        # all the data
        self.memsize, segments, pulses = self.preparing_buffer_multi()
        self.segment_memsize = int( self.memsize / segments )

        # define buffer differently for only one or two channels enabled
        if self.channel == 1 or self.channel == 2:
            # two bytes per sample; multiply by number of enabled channels
            self.buffer_size = np.zeros(2 * self.memsize * 1)
            buffer = np.zeros(self.memsize * 1, dtype = np.float64 )

            # pulses for different channel
            for element in pulses:
                # individual pulses at each channel
                for index2, element2 in enumerate( element ):
                    # segmented memory; mid_point for GAUSS and SINC
                    mid_point = int( element2[4]/2 )

                    # take a segment: self.segment_memsize*index2, self.segment_memsize*(index2 + 1)
                    for i in range ( self.segment_memsize*index2, self.segment_memsize*(index2 + 1), 1):
                        if element2[1] == 0: # SINE; [channel, function, frequency (MHz), phase, length (samples), sigma (samples)]
                            if i <= ( element2[4] + self.segment_memsize*index2 ):
                                buffer[i] = sin(2*pi*(( i - self.segment_memsize*index2))*element2[2] / self.sample_rate + element2[3])
                            else:
                                # keeping 0
                                pass
                        elif element2[1] == 1: # GAUSS
                            if i <= ( element2[4] + self.segment_memsize*index2 ):
                                buffer[i] = exp(-((( i - self.segment_memsize*index2) - mid_point)**2)*(1/(2*element2[5]**2)))*\
                                    sin(2*pi*(( i - self.segment_memsize*index2))*element2[2] / self.sample_rate + element2[3])
                            else:
                                pass
                        elif element2[1] == 2: # SINC
                            if i <= ( element2[4] + self.segment_memsize*index2 ):
                                buffer[i] = np.sinc(2*(( i - self.segment_memsize*index2) - mid_point) / (element2[5]) )*\
                                    sin(2*pi*( i - self.segment_memsize*index2)*element2[2] / self.sample_rate + element2[3])
                            else:
                                pass

            return buffer

        elif self.channel == 3:
            # two bytes per sample; multiply by number of enabled channels
            self.buffer_size = np.zeros(2 * self.memsize * 2)
            buffer = np.zeros(self.memsize * 2)

            # pulses for different channel
            for element in pulses:
                # individual pulses at each channel
                for index2, element2 in enumerate( element ):
                    # segments memory; mid_point for GAUSS and SINC
                    mid_point = int( element2[4]/2 )
                    
                    if element2[0] == 0:
                        # take a segment: 2*self.segment_memsize*index2, 2*self.segment_memsize*(index2 + 1)
                        # fill even indexes for CH0; step in the cycle is 2
                        for i in range (2 * self.segment_memsize*index2, 2 * self.segment_memsize*(index2 + 1), 2):
                            if element2[1] == 0: # SINE; [channel, function, frequency (MHz), phase, length (samples), sigma (samples)]
                                if i <= (2 * element2[4] + 2 * self.segment_memsize*index2 ):
                                    # Sine Signal CH_0; i/2 in order to keep the frequency
                                    buffer[i] = sin(2*pi*(( i/2 - self.segment_memsize*index2))*element2[2] / self.sample_rate + element2[3])
                                else:
                                    pass
                            elif element2[1] == 1: # GAUSS
                                if i <= ( 2 * element2[4] + 2 * self.segment_memsize*index2 ):
                                    buffer[i] = exp(-((( i/2 - self.segment_memsize*index2) - mid_point)**2)*(1/(2*element2[5]**2)))*\
                                        sin(2*pi*(( i/2 - self.segment_memsize*index2))*element2[2] / self.sample_rate + element2[3])
                                else:
                                    pass
                            elif element2[1] == 2: # SINC
                                if i <= ( 2 * element2[4] + 2 * self.segment_memsize*index2 ):
                                    buffer[i] = np.sinc(2*(( i/2 - self.segment_memsize*index2) - mid_point) / (element2[5]) )*\
                                        sin(2*pi*( i/2 - self.segment_memsize*index2)*element2[2] / self.sample_rate + element2[3])
                                else:
                                    pass

                    elif element2[0] == 1:
                        # fill odd indexes for CH1; step in the cycle is 2
                        for i in range (1 + 2 * self.segment_memsize*index2, 1 + 2 * self.segment_memsize*(index2 + 1), 2):
                            if element2[1] == 0: # SINE; [channel, function, frequency (MHz), phase, length (samples), sigma (samples)]
                                if (i - 1) <= ( 2 * element2[4] + 2 * self.segment_memsize*index2 ):
                                    # Sine Signal CH_1; i/2 in order to keep the frequency
                                    buffer[i] = sin(2*pi*(( (i - 1)/2 - self.segment_memsize*index2 ))*element2[2] / self.sample_rate + element2[3])
                                else:
                                    pass
                            elif element2[1] == 1: # GAUSS
                                if (i - 1) <= ( 2 * element2[4] + 2 * self.segment_memsize*index2 ):
                                    buffer[i] = exp(-((( (i - 1)/2 - self.segment_memsize*index2) - mid_point)**2)*(1/(2*element2[5]**2)))*\
                                        sin(2*pi*(( (i - 1)/2 - self.segment_memsize*index2))*element2[2] / self.sample_rate + element2[3])
                                else:
                                    pass
                            elif element2[1] == 2: # SINC
                                if (i - 1) <= ( 2 * element2[4] + 2 * self.segment_memsize*index2 ):
                                    buffer[i] = np.sinc(2*(( (i - 1)/2 - self.segment_memsize*index2) - mid_point) / (element2[5]) )*\
                                        sin(2*pi*( (i - 1)/2 - self.segment_memsize*index2)*element2[2] / self.sample_rate + element2[3])
                                else:
                                    pass

            return buffer

    def preparing_buffer_single(self):
        """
        A function to prepare everything for buffer filling in the 'Single' mode
        Check of 'Single' card mode.
        Check of number of segments (should be  1).
        Find a pulse with the maximum length. Determine the memory size.
        Return memory_size, pulses
        """
        if test_flag != 'test':
            
            max_length_array = []
            pulses = self.splitting_acc_to_channel( self.convertion_to_numpy(self.pulse_array) )

            # Max pulse length
            for index, element in enumerate(pulses):
                max_length_array.append( max( element[:,4] ))

            # finding the maximum pulse length to create a buffer
            max_pulse_length = max( max_length_array )
            buffer_per_max_pulse = self.closest_power_of_two( max_pulse_length )
            if buffer_per_max_pulse < 32:
                buffer_per_max_pulse = 32
                general.message('Buffer size was rounded to the minimal available value (32 samples)')

            # determine the memory size (buffer size will be doubled if two channels are enabled)
            memsize = buffer_per_max_pulse

            return memsize, pulses

        elif test_flag == 'test':
            
            #checks
            assert( self.card_mode == 32768 ), 'You are not in Single mode'
            assert( self.num_segments == 1 ), 'More than one segment is declared in Single mode. Please, use Multi mode'

            max_length_array = []
            pulses = self.splitting_acc_to_channel( self.convertion_to_numpy(self.pulse_array) )

            # finding the maximum pulse length to create a buffer
            for index, element in enumerate(pulses):
                max_length_array.append( max( element[:,4] ))

            max_pulse_length = max( max_length_array )
            buffer_per_max_pulse = self.closest_power_of_two( max_pulse_length )
            if buffer_per_max_pulse < 32:
                buffer_per_max_pulse = 32
                general.message('Buffer size was rounded to the minimal available value (32 samples)')

            # check number of channels and determine the memory size 
            # (buffer size will be doubled if two channels are enabled)
            num_ch = len(pulses)
            assert( (num_ch == 1 and ( self.channel == 1 or self.channel == 2)) or \
                num_ch == 2 and ( self.channel == 3 ) ), 'Number of enabled channels are not equal to the number of channels in AWG pulses'

            memsize = buffer_per_max_pulse

            return memsize, pulses

    def define_buffer_single(self):
        """
        Define and fill the buffer in 'Single' mode;
        
        If a number of enabled channels is 1:
        Each index is a new data sample
        
        If a number of enabled channels are 2:
        Every even index is a new data sample for CH0,
        Every odd index is a new data sample for CH1.
        """

        self.memsize, pulses = self.preparing_buffer_single()

        # define buffer differently for only one or two channels enabled
        if self.channel == 1 or self.channel == 2:
            # two bytes per sample; multiply by number of enabled channels
            self.buffer_size = np.zeros(2 * self.memsize * 1)
            buffer = np.zeros(self.memsize * 1, dtype = np.float64 )

            # pulses for different channel
            for element in pulses:
                # individual pulses at each channel
                for index2, element2 in enumerate( element ):
                    # mid_point for GAUSS and SINC
                    mid_point = int( element2[4]/2 )

                    for i in range (0, self.memsize, 1):
                        if element2[1] == 0: # SINE; [channel, function, frequency (MHz), phase, length (samples), sigma (samples)]
                            if i <= ( element2[4] ):
                                buffer[i] = sin(2*pi*(( i ))*element2[2] / self.sample_rate + element2[3])
                            else:
                                pass
                        elif element2[1] == 1: # GAUSS
                            if i <= ( element2[4] ):
                                buffer[i] = exp(-((( i ) - mid_point)**2)*(1/(2*element2[5]**2)))*\
                                    sin(2*pi*(( i ))*element2[2] / self.sample_rate + element2[3])
                            else:
                                pass
                        elif element2[1] == 2: # SINC
                            if i <= ( element2[4] ):
                                buffer[i] = np.sinc(2*(( i ) - mid_point) / (element2[5]) )*\
                                    sin(2*pi*( i )*element2[2] / self.sample_rate + element2[3])
                            else:
                                pass

            return buffer

        elif self.channel == 3:
            # two bytes per sample; multiply by number of enabled channels
            self.buffer_size = np.zeros(2 * self.memsize * 1)
            buffer = np.zeros(self.memsize * 2)

            # pulses for different channel
            for element in pulses:
                # individual pulses at each channel
                for index2, element2 in enumerate( element ):
                    # mid_point for GAUSS and SINC
                    mid_point = int( element2[4]/2 )
                    
                    if element2[0] == 0:
                        # fill even indexes for CH0; step in the cycle is 2
                        for i in range (0, 2 * self.memsize, 2):
                            if element2[1] == 0: # SINE; [channel, function, frequency (MHz), phase, length (samples), sigma (samples)]
                                if i <= ( 2 * element2[4] ):
                                    # Sine Signal CH_0; i/2 in order to keep the frequency
                                    buffer[i] = sin(2*pi*(( i/2 ))*element2[2] / self.sample_rate + element2[3])
                                else:
                                    pass
                            elif element2[1] == 1: # GAUSS
                                if i <= ( 2 * element2[4] ):
                                    buffer[i] = exp(-((( i/2 ) - mid_point)**2)*(1/(2*element2[5]**2)))*\
                                        sin(2*pi*(( i/2 ))*element2[2] / self.sample_rate + element2[3])
                                else:
                                    pass
                            elif element2[1] == 2: # SINC
                                if i <= ( 2 * element2[4] ):
                                    buffer[i] = np.sinc(2*(( i/2 ) - mid_point) / (element2[5]) )*\
                                        sin(2*pi*( i/2 )*element2[2] / self.sample_rate + element2[3])
                                else:
                                    pass

                    elif element2[0] == 1:
                        # fill odd indexes for CH1; step in the cycle is 2
                        for i in range (1 , 1 + 2 * self.memsize, 2):
                            if element2[1] == 0: # SINE; [channel, function, frequency (MHz), phase, length (samples), sigma (samples)]
                                if (i - 1) <= ( 2 * element2[4] ):
                                    # Sine Signal CH_1; i/2 in order to keep the frequency
                                    buffer[i] = sin(2*pi*(( (i - 1)/2 ))*element2[2] / self.sample_rate + element2[3])
                                else:
                                    pass
                            elif element2[1] == 1: # GAUSS
                                if (i - 1) <= ( 2 * element2[4] ):
                                    buffer[i] = exp(-((( (i - 1)/2 ) - mid_point)**2)*(1/(2*element2[5]**2)))*\
                                        sin(2*pi*(( (i - 1)/2 ))*element2[2] / self.sample_rate + element2[3])
                                else:
                                    pass
                            elif element2[1] == 2: # SINC
                                if (i - 1) <= ( 2 * element2[4] ):
                                    buffer[i] = np.sinc(2*(( (i - 1)/2 ) - mid_point) / (element2[5]) )*\
                                        sin(2*pi*( (i - 1)/2 )*element2[2] / self.sample_rate + element2[3])
                                else:
                                    pass

            return buffer        

    def closest_power_of_two(self, x):
        """
        A function to round card memory
        """
        return 2**int(log2(x - 1) + 1 )

def main():
    pass

if __name__ == "__main__":
    main()

