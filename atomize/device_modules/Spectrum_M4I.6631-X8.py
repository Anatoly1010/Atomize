#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import math
import numpy as np
#from pyspcm import *
#from spcm_tools import *
import atomize.device_modules.config.config_utils as cutil
import atomize.general_modules.general_functions as general
#import atomize.general_modules.spinapi as spinapi

# Initialization of the Spectrum library
#sp = spinapi.SpinAPI()

#### Inizialization
# setting path to *.ini file
path_current_directory = os.path.dirname(__file__)
path_config_file = os.path.join(path_current_directory, 'config','Spectrum_M4I.6631-X8_config.ini')

# configuration data
#config = cutil.read_conf_util(path_config_file)
specific_parameters = cutil.read_specific_parameters(path_config_file)

# TO DO

# Channel assignments
ch0 = specific_parameters['ch0'] # TRIGGER
ch1 = specific_parameters['ch1'] # AMP_ON

timebase_dict = {'s': 1000000000, 'ms': 1000000, 'us': 1000, 'ns': 1,}
# -Y for Mikran bridge is simutaneously turned on -X; +Y
# that is why there is no -Y channel instead we add both -X and +Y pulses
channel_dict = {ch0: 0, ch1: 1, ch2: 2, ch3: 3, ch4: 4, ch5: 5, \
                'CH6': 6, 'CH7': 7, 'CH8': 8, 'CH9': 9, 'CH10': 10, 'CH11': 11,\
                'CH12': 12, 'CH13': 13, 'CH14': 14, 'CH15': 15, 'CH16': 16, 'CH17': 17,\
                'CH18': 18, 'CH19': 19, 'CH20': 20, 'CH21': 21, }

# Limits and Ranges (depends on the exact model):
clock = float(specific_parameters['clock'])

# Delays and restrictions

# Test run parameters
# These values are returned by the modules in the test run 
if len(sys.argv) > 1:
    test_flag = sys.argv[1]
else:
    test_flag = 'None'

test_sample_rate = 1250

class Spectrum_M4I_6631_X8:
    def __init__(self):
        if test_flag != 'test':
            pass
        
        elif test_flag == 'test':
            pass

    # Module functions
    def awg_name(self):
        answer = 'Spectrum M4I.6631-X8'
        return answer

    def awg_open(self):
        if test_flag != 'test':
            self.hCard = spcm_hOpen( create_string_buffer (b'/dev/spcm0') )
            if self.hCard == None:
                general.message( "No card found" )
                sys.exit()

        elif test_flag == 'test':
            pass

    def awg_close(self):
        if test_flag != 'test':
            spcm_vClose(self.hCard)

        elif test_flag == 'test':
            pass

    def awg_sample_rate(self, *s_rate):
        # '1000 MHz'; in MHz
        if test_flag != 'test':
            if len(s_rate) == 1:
                temp = s_rate[0].split(' ')
                rate = int(temp[0])
                dimen = str(temp[1])
                spcm_dwSetParam_i64 (self.hCard, SPC_SAMPLERATE, MEGA(rate))

            elif len(s_rate) == 0:
                answer = int32 (0)
                spcm_dwGetParam_i32 (self.hCard, SPC_CHCOUNT, byref (answer))
                return answer

        elif test_flag == 'test':
            if len(s_rate) == 1:
                temp = s_rate[0].split(' ')
                rate = int(temp[0])
                dimen = str(temp[1])
                assert(dimen == 'MHz'), "Incorrect sample rate dimension (MHz)"

            elif len(s_rate) == 0:
                return test_sample_rate


    def awg_card_mode(self, mode):


def main():
    pass

if __name__ == "__main__":
    main()

