#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import math
from copy import deepcopy
from itertools import groupby
import numpy as np
import atomize.device_modules.config.config_utils as cutil
import atomize.general_modules.general_functions as general
import atomize.general_modules.spinapi as spinapi

# Initialization of the SpinAPI PB library
sp = spinapi.SpinAPI()

#### Inizialization
# setting path to *.ini file
path_current_directory = os.path.dirname(__file__)
path_config_file = os.path.join(path_current_directory, 'config','PB_ESR_500_pro_config.ini')

# configuration data
#config = cutil.read_conf_util(path_config_file)
specific_parameters = cutil.read_specific_parameters(path_config_file)

# TO DO
# awg pulses

# Channel assignments
ch0 = specific_parameters['ch0'] # TRIGGER
ch1 = specific_parameters['ch1'] # AMP_ON
ch2 = specific_parameters['ch2'] # LNA_PROTCT
ch3 = specific_parameters['ch3'] # MW
ch4 = specific_parameters['ch4'] # -X
ch5 = specific_parameters['ch5'] # +Y

timebase_dict = {'s': 1000000000, 'ms': 1000000, 'us': 1000, 'ns': 1,}
# -Y for Mikran bridge is simutaneously turned on -X; +Y
# that is why there is no -Y channel instead we add both -X and +Y pulses
channel_dict = {ch0: 0, ch1: 1, ch2: 2, ch3: 3, ch4: 4, ch5: 5, \
                'CH6': 6, 'CH7': 7, 'CH8': 8, 'CH9': 9, 'CH10': 10, 'CH11': 11,\
                'CH12': 12, 'CH13': 13, 'CH14': 14, 'CH15': 15, 'CH16': 16, 'CH17': 17,\
                'CH18': 18, 'CH19': 19, 'CH20': 20, 'CH21': 21, }

# Limits and Ranges (depends on the exact model):
clock = float(specific_parameters['clock'])
timebase = int(float(specific_parameters['timebase'])) # in ns/clock; convertion of clock to ns
repetition_rate = specific_parameters['default_rep_rate']
auto_defense = specific_parameters['auto_defense']
max_pulse_length = int(float(specific_parameters['max_pulse_length'])) # in ns
min_pulse_length = int(float(specific_parameters['min_pulse_length'])) # in ns

# minimal distance between two pulses of MW
# pulse blaster restriction
minimal_distance = int(float(specific_parameters['minimal_distance'])/timebase) # in clock

# a constant that use to overcome short instruction for our diagonal amp_on and mw pulses
# see also add_amp_on_pulses() function; looking for pulses with +-overlap_amp_lna_mw overlap
overlap_amp_lna_mw = 5 # in clock

# after all manupulations with diagonal amp_on pulses there is a variant
# when we use several mw pulses with app. 40 ns distance and with the phase different from
# +x. In this case two phase pulses start to be at the distance less than current minimal distance
# in 40 ns. That is why a different minimal distance (10 ns) is added for phase pulses
# see also preparing_to_bit_pulse() function
minimal_distance_phase = 5 # in clock

# minimal distance for joining AMP_ON and LNA_PROTECT pulses
# decided to keep it as 12 ns, while for MW pulses the limit is 40 ns
minimal_distance_amp_lna = 6 # in clock

# Delays and restrictions
constant_shift = int(250/timebase) # in clock; shift of all sequence for not getting negative start times
switch_delay = int(float(specific_parameters['switch_delay'])/timebase) # in clock; delay for AMP_ON turning on; switch_delay BEFORE MW pulse
amp_delay = int(float(specific_parameters['amp_delay'])/timebase) # in clock; delay for AMP_ON turning off; amp_delay AFTER MW pulse
protect_delay = int(float(specific_parameters['protect_delay'])/timebase) # in clock; delay for LNA_PROTECT turning off; protect_delay AFTER MW pulse
switch_phase_delay = int(float(specific_parameters['switch_phase_delay'])) # in ns; delay for FAST_PHASE turning on; switch_phase_delay BEFORE MW pulse
phase_delay = int(float(specific_parameters['phase_delay'])) # in ns; delay for FAST_PHASE turning off; phase_delay AFTER MW pulse

# interval that shift the first pulse in the sequence
# start times of other pulses can be calculated from this time.
# I. E. first pulse: 
# pb.pulser_pulse(name ='P0', channel = 'MW', start = '100 ns', length = '20 ns')
# second: pb.pulser_pulse(name ='P1', channel = 'MW', start = '330 ns', length = '30 ns', delta_start = '10 ns')
# we will have first pulse at 50 ns (add_shft*2)
# second at (330 - 100) + 50 = 280 ns
# if there is no AMP_ON/LNA_PROTECT pulses
add_shift = int(25) # in ns; *timebase

# Test run parameters
# These values are returned by the modules in the test run 
if len(sys.argv) > 1:
    test_flag = sys.argv[1]
else:
    test_flag = 'None'

test_rep_rate = '2 Hz'

class PB_ESR_500_Pro:
    def __init__(self):
        if test_flag != 'test':
            #pb_core_clock(clock)
            self.pulse_array = []
            self.phase_array_length = []
            self.pulse_name_array = []
            self.pulse_array_init = []
            self.rep_rate = (repetition_rate, )
            self.shift_count = 0
            self.rep_rate_count = 0
            self.increment_count = 0
            self.reset_count = 0
            self.current_phase_index = 0
        
        elif test_flag == 'test':
            self.pulse_array = []
            self.phase_array_length = []
            self.pulse_name_array = []
            self.pulse_array_init = []
            self.rep_rate = (repetition_rate, )
            self.shift_count = 0
            self.rep_rate_count = 0
            self.increment_count = 0
            self.reset_count = 0
            self.current_phase_index = 0

    # Module functions
    def pulser_name(self):
        answer = 'PB ESR 500 Pro'
        return answer

    def pulser_pulse(self, name = 'P0', channel = 'TRIGGER', start = '0 ns', length = '100 ns', \
        delta_start = '0 ns', length_increment = '0 ns', phase_list = []):
        """
        A function that added a new pulse at specified channel. The possible arguments:
        NAME, CHANNEL, START, LENGTH, DELTA_START, LENGTH_INCREMENT, PHASE_SEQUENCE
        """
        if test_flag != 'test':
            pulse = {'name': name, 'channel': channel, 'start': start, 'length': length, 'delta_start' : delta_start,\
             'length_increment': length_increment, 'phase_list': phase_list}

            self.pulse_array.append( pulse )
            # for saving the initial pulse_array without increments
            # deepcopy helps to create a TRULY NEW array and not a link to the object
            self.pulse_array_init = deepcopy( self.pulse_array )
            # pulse_name array
            self.pulse_name_array.append( pulse['name'] )
            # for correcting AMP_ON (PB restriction in 10 ns minimal instruction) according to phase pulses
            if channel == 'MW':
                self.phase_array_length.append(len(list(phase_list)))

        elif test_flag == 'test':

            pulse = {'name': name, 'channel': channel, 'start': start, \
                'length': length, 'delta_start' : delta_start, 'length_increment': length_increment, 'phase_list': phase_list}
            
            # phase_list's length
            if channel == 'MW':
                self.phase_array_length.append(len(list(phase_list)))

            # Checks
            # two equal names
            temp_name = str(name)
            set_from_list = set(self.pulse_name_array)          
            if temp_name in set_from_list:
                assert (1 == 2), 'Two pulses have the same name. Please, rename'

            self.pulse_name_array.append( pulse['name'] )

            temp_length = length.split(" ")
            if temp_length[1] in timebase_dict:
                coef = timebase_dict[temp_length[1]]
                p_length = coef*float(temp_length[0])
                assert(p_length % 2 == 0), 'Pulse length should be divisible by 2'
                assert(p_length >= min_pulse_length), 'Pulse is shorter than minimum available length (' + str(min_pulse_length) +' ns)'
                assert(p_length < max_pulse_length), 'Pulse is longer than maximum available length (' + str(max_pulse_length) +' ns)'
            else:
                assert( 1 == 2 ), 'Incorrect time dimension (s, ms, us, ns)'

            temp_start = start.split(" ")
            if temp_start[1] in timebase_dict:
                coef = timebase_dict[temp_start[1]]
                p_start = coef*float(temp_start[0])
                assert(p_start % 2 == 0), 'Pulse start should be divisible by 2'
                assert(p_start >= 0), 'Pulse start is a negative number'
            else:
                assert( 1 == 2 ), 'Incorrect time dimension (s, ms, us, ns)'

            temp_delta_start = delta_start.split(" ")
            if temp_delta_start[1] in timebase_dict:
                coef = timebase_dict[temp_delta_start[1]]
                p_delta_start = coef*float(temp_delta_start[0])
                assert(p_delta_start % 2 == 0), 'Pulse delta start should be divisible by 2'
                assert(p_delta_start >= 0), 'Pulse delta start is a negative number'
            else:
                assert( 1 == 2 ), 'Incorrect time dimension (s, ms, us, ns)'

            temp_length_increment = length_increment.split(" ")
            if temp_length_increment[1] in timebase_dict:
                coef = timebase_dict[temp_length_increment[1]]
                p_length_increment = coef*float(temp_length_increment[0])
                assert(p_length_increment % 2 == 0), 'Pulse length increment should be divisible by 2'
                assert (p_length_increment >= 0 and p_length_increment < max_pulse_length), \
                'Pulse length increment is longer than maximum available length or negative'
            else:
                assert( 1 == 2 ), 'Incorrect time dimension (s, ms, us, ns)'

            if channel in channel_dict:
                if auto_defense == 'False':
                    self.pulse_array.append( pulse )
                    # for saving the initial pulse_array without increments
                    # deepcopy helps to create a TRULY NEW array and not a link to the object
                    self.pulse_array_init = deepcopy(self.pulse_array)
                elif auto_defense == 'True':
                    if channel == 'AMP_ON' or channel == 'LNA_PROTECT':
                        assert( 1 == 2), 'In auto_defense mode AMP_ON and LNA_PROTECT pulses are set automatically'
                    else:
                        self.pulse_array.append( pulse )
                        # for saving the initial pulse_array without increments
                        # deepcopy helps to create a TRULY NEW array and not a link to the object
                        self.pulse_array_init = deepcopy(self.pulse_array)                        
                else:
                    assert(1 == 2), 'Incorrect auto_defense setting'
            else:
                assert (1 == 2), 'Incorrect channel name'

    def pulser_next_phase(self):
        """
        A function for phase cycling. It works using phase_list decleared in pulser_pulse():
        phase_list = ['-y', '+x', '-x', '+x']
        self.current_phase_index is an iterator of the current phase
        functions pulser_shift() and pulser_increment() reset the iterator

        after calling pulser_next_phase() the next phase is taken from phase_list and a 
        corresponding trigger pulse is added to self.pulse_array

        the length of all phase lists specified for different MW pulses has to be the same
        
        the function also immediately sends intructions to pulse blaster as
        a function pulser_update() does. 
        """
        if test_flag != 'test':
            # deleting old phase switch pulses from self.pulse_array
            # before adding new ones
            for index, element in enumerate(self.pulse_array):
                if element['channel'] == '-X' or element['channel'] == '+Y' or element['channel'] == '-Y':
                    del self.pulse_array[index]

            # we should check the list twice since -Y phase adds two pulses
            for index, element in enumerate(self.pulse_array):
                if element['channel'] == '-X' or element['channel'] == '+Y' or element['channel'] == '-Y':
                    del self.pulse_array[index]

            # adding phase switch pulses
            for index, element in enumerate(self.pulse_array):
                if len(list(element['phase_list'])) != 0:
                    if element['phase_list'][self.current_phase_index] == '+x':
                        pass
                    elif element['phase_list'][self.current_phase_index] == '-x':
                        name = element['name'] + '_ph_seq-x'
                        # taking into account delays of phase switching
                        start = self.change_pulse_settings(element['start'], -switch_phase_delay)
                        length = self.change_pulse_settings(element['length'], phase_delay + switch_phase_delay)

                        self.pulse_array.append({'name': name, 'channel': '-X', 'start': start, \
                            'length': length, 'delta_start' : '0 ns', 'length_increment': '0 ns', 'phase_list': []})

                        self.reset_count = 0

                    elif element['phase_list'][self.current_phase_index] == '+y':
                        name = element['name'] + '_ph_seq+y'
                        # taking into account delays of phase switching
                        start = self.change_pulse_settings(element['start'], -switch_phase_delay)
                        length = self.change_pulse_settings(element['length'], phase_delay + switch_phase_delay)

                        self.pulse_array.append({'name': name, 'channel': '+Y', 'start': start, \
                            'length': length, 'delta_start' : '0 ns', 'length_increment': '0 ns', 'phase_list': []})

                        self.reset_count = 0

                    elif element['phase_list'][self.current_phase_index] == '-y':
                        name = element['name'] + '_ph_seq-y'
                        # taking into account delays of phase switching
                        start = self.change_pulse_settings(element['start'], -switch_phase_delay)
                        length = self.change_pulse_settings(element['length'], phase_delay + switch_phase_delay)

                        # -Y for Mikran bridge is simutaneously turned on -X; +Y
                        # that is why there is no -Y channel
                        self.pulse_array.append({'name': name, 'channel': '-X', 'start': start, \
                            'length': length, 'delta_start' : '0 ns', 'length_increment': '0 ns', 'phase_list': []})
                        self.pulse_array.append({'name': name, 'channel': '+Y', 'start': start, \
                            'length': length, 'delta_start' : '0 ns', 'length_increment': '0 ns', 'phase_list': []})

                        self.reset_count = 0

            self.current_phase_index += 1

            # update pulses
            # get repetition rate
            rep_rate = self.rep_rate[0]
            if rep_rate[-3:] == ' Hz':
                rep_time = int(1000000000/float(rep_rate[:-3]))
            elif rep_rate[-3:] == 'kHz':
                rep_time = int(1000000/float(rep_rate[:-4]))
            elif rep_rate[-3:] == 'MHz':
                rep_time = int(1000/float(rep_rate[:-4]))

            self.pulser_update(rep_rate)

        elif test_flag == 'test':

            # check that the length is equal (compare all elements in self.phase_array_length)
            gr = groupby(self.phase_array_length)
            if (next(gr, True) and not next(gr, False)) == False:
                assert(1 == 2), 'Phase sequence does not have equal length'

            for index, element in enumerate(self.pulse_array):
                if element['channel'] == '-X' or element['channel'] == '+Y' or element['channel'] == '-Y':
                    del self.pulse_array[index]

            # we should check the list twice since -Y phase adds two pulses
            for index, element in enumerate(self.pulse_array):
                if element['channel'] == '-X' or element['channel'] == '+Y' or element['channel'] == '-Y':
                    del self.pulse_array[index]

            for index, element in enumerate(self.pulse_array):
                if len(list(element['phase_list'])) != 0:
                    if element['phase_list'][self.current_phase_index] == '+x':
                        pass
                    elif element['phase_list'][self.current_phase_index] == '-x':
                        name = element['name'] + '_ph_seq-x'
                        # taking into account delays
                        start = self.change_pulse_settings(element['start'], -switch_phase_delay)
                        length = self.change_pulse_settings(element['length'], phase_delay + switch_phase_delay)

                        self.pulse_array.append({'name': name, 'channel': '-X', 'start': start, \
                            'length': length, 'delta_start' : '0 ns', 'length_increment': '0 ns', 'phase_list': []})

                        # check that we still have a next phase to switch
                        self.reset_count = 0

                    elif element['phase_list'][self.current_phase_index] == '+y':
                        name = element['name'] + '_ph_seq+y'
                        # taking into account delays
                        start = self.change_pulse_settings(element['start'], -switch_phase_delay)
                        length = self.change_pulse_settings(element['length'], phase_delay + switch_phase_delay)

                        self.pulse_array.append({'name': name, 'channel': '+Y', 'start': start, \
                            'length': length, 'delta_start' : '0 ns', 'length_increment': '0 ns', 'phase_list': []})

                        # check that we still have a next phase to switch
                        self.reset_count = 0

                    elif element['phase_list'][self.current_phase_index] == '-y':
                        name = element['name'] + '_ph_seq-y'
                        # taking into account delays
                        start = self.change_pulse_settings(element['start'], -switch_phase_delay)
                        length = self.change_pulse_settings(element['length'], phase_delay + switch_phase_delay)

                        # -Y for Mikran bridge is simutaneously turned on -X; +Y
                        # that is why there is no -Y channel
                        self.pulse_array.append({'name': name, 'channel': '-X', 'start': start, \
                            'length': length, 'delta_start' : '0 ns', 'length_increment': '0 ns', 'phase_list': []})
                        self.pulse_array.append({'name': name, 'channel': '+Y', 'start': start, \
                            'length': length, 'delta_start' : '0 ns', 'length_increment': '0 ns', 'phase_list': []})

                        # check that we still have a next phase to switch
                        self.reset_count = 0

                    else:
                        assert( 1 == 2 ), 'Incorrect phase name (+x, -x, +y, -y)'
                else:
                    pass

            self.current_phase_index += 1

            # update pulses
            # get repetition rate
            rep_rate = self.rep_rate[0]
            if rep_rate[-3:] == ' Hz':
                rep_time = int(1000000000/float(rep_rate[:-3]))
            elif rep_rate[-3:] == 'kHz':
                rep_time = int(1000000/float(rep_rate[:-4]))
            elif rep_rate[-3:] == 'MHz':
                rep_time = int(1000/float(rep_rate[:-4]))

            self.pulser_update(rep_rate)

    def pulser_update(self, rep_rate = repetition_rate):
        """
        A function that write instructions to SpinAPI. 
        Repetition rate is taking into account by adding
        a last pulse with delay.
        Currently, all pulses are cycled using BRANCH.
        """
        if test_flag != 'test':
            # get repetition rate
            rep_rate = self.rep_rate[0]
            if rep_rate[-3:] == ' Hz':
                rep_time = int(1000000000/float(rep_rate[:-3]))
            elif rep_rate[-3:] == 'kHz':
                rep_time = int(1000000/float(rep_rate[:-4]))
            elif rep_rate[-3:] == 'MHz':
                rep_time = int(1000/float(rep_rate[:-4]))

            if self.reset_count == 0 or self.shift_count == 1 or self.increment_count == 1 or self.rep_rate_count == 1:
                # using a special functions for convertion to instructions
                # we get two return arrays because of pulser_visualizer. It is not the case for test flag.
                #temp, visualizer = self.convert_to_bit_pulse( self.pulse_array )
                
                #to_spinapi = self.instruction_pulse( temp, rep_time )
                to_spinapi = self.split_into_parts( self.pulse_array, rep_time )
                general.message(to_spinapi)
                for element in to_spinapi:
                    if element[2] < 10:
                        ###general.message('Incorrect instruction are found')
                        general.message('ALARM')
                        ###self.pulser_stop()

                #general.message( to_spinapi )
                #self.pulser_stop()
                # initialization
                #pb_init()
                #pb.core_clock(clock)
                ###sp.pb_init()
                ###sp.pb_core_clock(clock)

                #pb_start_programming(PULSE_PROGRAM)
                ###sp.pb_start_programming(0)
                i = 0
                while i < len( to_spinapi) - 1:
                    ###if i == 0: 
                        # to create a link for BRANCH
                        # start = pb_inst(ON | "0x%X" % to_spinapi[i][0], CONTINUE, 0, "0x%X" % to_spinapi[i][2])
                        
                        # CONTINUE is 0
                        # ON is 111 in the first three bits of the Output/Control Word (24 bits)
                        # it is 14680064 or 0xE00000
                        ###start = sp.pb_inst(14680064 + to_spinapi[i][0], 0, 0, to_spinapi[i][2])
                    ###else:
                        #pb_inst(ON | "0x%X" % to_spinapi[i, 0], CONTINUE, 0, "0x%X" % to_spinapi[i][2])
                        ###sp.pb_inst(14680064 + to_spinapi[i][0], 0, 0, to_spinapi[i][2])
                    if i == 0:
                        pass
                        #print('ON | ' + "0x%X" % to_spinapi[i][0] + ', CONTINUE, 0, ' + "0x%X" % to_spinapi[i][2] )
                    else:
                        pass
                        #print('ON | ' + "0x%X" % to_spinapi[i][0] + ', CONTINUE, 0, ' + "0x%X" % to_spinapi[i][2] )

                    i += 1

                # last instruction for delay
                #pb_inst(ON | "0x%X" % to_spinapi[i][0], BRANCH, 0, "0x%X" % to_spinapi[i][2])
                #print('ON | ' + "0x%X" % to_spinapi[i][0] + ', BRANCH, start, ' + "0x%X" % to_spinapi[i][2] )
                # BRANCH is 6
                ###sp.pb_inst(14680064 + to_spinapi[i][0], 6, start, to_spinapi[i][2])

                #pb_stop_programming()
                #pb_reset()
                #pb_start()
                
                ###sp.pb_stop_programming()
                ###sp.pb_reset()
                ###sp.pb_start()

                #pb_close()
                ###sp.pb_close()

                self.reset_count = 1
                self.shift_count = 0
                self.increment_count = 0
                self.rep_rate_count = 0
            else:
                pass

        elif test_flag == 'test':
            # get repetition rate
            rep_rate = self.rep_rate[0]
            if rep_rate[-3:] == ' Hz':
                rep_time = int(1000000000/float(rep_rate[:-3]))
            elif rep_rate[-3:] == 'kHz':
                rep_time = int(1000000/float(rep_rate[:-4]))
            elif rep_rate[-3:] == 'MHz':
                rep_time = int(1000/float(rep_rate[:-4]))
            else:
                assert(1 == 2), "Incorrect repetition rate dimension (Hz, kHz, MHz)"

            if self.reset_count == 0 or self.shift_count == 1 or self.increment_count == 1:
                # using a special functions for convertion to instructions
                #to_spinapi = self.instruction_pulse( self.convert_to_bit_pulse( self.pulse_array ) )
                to_spinapi = self.split_into_parts( self.pulse_array, rep_time )
                for element in to_spinapi:
                    if element[2] < 10:
                        assert( 1 == 2), 'Incorrect instruction are found'

                self.reset_count = 1
                self.shift_count = 0
                self.increment_count = 0
                self.rep_rate_count = 0
            else:
                pass

    def pulser_repetitoin_rate(self, *r_rate):
        """
        A function to get or set repetition rate.
        Repetition rate specifies the delay of the last
        SpinAPI instructions
        """
        if test_flag != 'test':
            if  len(r_rate) == 1:
                self.rep_rate = r_rate
                self.rep_rate_count = 1
            elif len(r_rate) == 0:
                general.message(self.rep_rate[0])

        elif test_flag == 'test':
            if  len(r_rate) == 1:
                self.rep_rate = r_rate
                self.rep_rate_count = 1
            elif len(r_rate) == 0:
                pass

    def pulser_shift(self, *pulses):
        """
        A function to shift the start of the pulses.
        The function directly affects the pulse_array.
        """
        if test_flag != 'test':
            if len(pulses) == 0:
                i = 0
                while i < len( self.pulse_array ):
                    if int( self.pulse_array[i]['delta_start'][:-3] ) == 0:
                        pass
                    else:
                        # convertion to ns
                        temp = self.pulse_array[i]['delta_start'].split(' ')
                        if temp[1] in timebase_dict:
                            flag = timebase_dict[temp[1]]
                            d_start = int((temp[0]))*flag
                        else:
                            pass

                        temp2 = self.pulse_array[i]['start'].split(' ')
                        if temp2[1] in timebase_dict:
                            flag2 = timebase_dict[temp2[1]]
                            st = int((temp2[0]))*flag2
                        else:
                            pass
                                
                        self.pulse_array[i]['start'] = str( st + d_start ) + ' ns'
 
                    i += 1

                self.shift_count = 1
                self.current_phase_index = 0

            else:
                set_from_list = set(pulses)
                for element in set_from_list:
                    if element in self.pulse_name_array:
                        pulse_index = self.pulse_name_array.index(element)

                        if int( self.pulse_array[pulse_index]['delta_start'][:-3] ) == 0:
                            pass
                        else:
                            # convertion to ns
                            temp = self.pulse_array[pulse_index]['delta_start'].split(' ')
                            if temp[1] in timebase_dict:
                                flag = timebase_dict[temp[1]]
                                d_start = int((temp[0]))*flag
                            else:
                                pass

                            temp2 = self.pulse_array[pulse_index]['start'].split(' ')
                            if temp2[1] in timebase_dict:
                                flag2 = timebase_dict[temp2[1]]
                                st = int((temp2[0]))*flag2
                            else:
                                pass
                                    
                            self.pulse_array[pulse_index]['start'] = str( st + d_start ) + ' ns'

                        self.shift_count = 1
                        self.current_phase_index = 0

        elif test_flag == 'test':
            if len(pulses) == 0:
                i = 0
                while i < len( self.pulse_array ):
                    if int( self.pulse_array[i]['delta_start'][:-3] ) == 0:
                        pass
                    else:
                        # convertion to ns
                        temp = self.pulse_array[i]['delta_start'].split(' ')
                        if temp[1] in timebase_dict:
                            flag = timebase_dict[temp[1]]
                            d_start = int((temp[0]))*flag
                        else:
                            assert(1 == 2), "Incorrect time dimension (ns, us, ms, s)"

                        temp2 = self.pulse_array[i]['start'].split(' ')
                        if temp2[1] in timebase_dict:
                            flag2 = timebase_dict[temp2[1]]
                            st = int((temp2[0]))*flag2
                        else:
                            assert(1 == 2), "Incorrect time dimension (ns, us, ms, s)"
                                
                        self.pulse_array[i]['start'] = str( st + d_start ) + ' ns'

                    i += 1

                self.shift_count = 1
                self.current_phase_index = 0

            else:
                set_from_list = set(pulses)
                for element in set_from_list:
                    if element in self.pulse_name_array:

                        pulse_index = self.pulse_name_array.index(element)
                        if int( self.pulse_array[pulse_index]['delta_start'][:-3] ) == 0:
                            pass
                        else:
                            # convertion to ns
                            temp = self.pulse_array[pulse_index]['delta_start'].split(' ')
                            if temp[1] in timebase_dict:
                                flag = timebase_dict[temp[1]]
                                d_start = int((temp[0]))*flag
                            else:
                                assert(1 == 2), "Incorrect time dimension (ns, us, ms, s)"

                            temp2 = self.pulse_array[pulse_index]['start'].split(' ')
                            if temp2[1] in timebase_dict:
                                flag2 = timebase_dict[temp2[1]]
                                st = int((temp2[0]))*flag2
                            else:
                                assert(1 == 2), "Incorrect time dimension (ns, us, ms, s)"
                                    
                            self.pulse_array[pulse_index]['start'] = str( st + d_start ) + ' ns'

                        self.shift_count = 1
                        self.current_phase_index = 0

                    else:
                        assert(1 == 2), "There is no pulse with the specified name"

    def pulser_increment(self, *pulses):
        """
        A function to increment the length of the pulses.
        The function directly affects the pulse_array.
        """
        if test_flag != 'test':
            if len(pulses) == 0:
                i = 0
                while i < len( self.pulse_array ):
                    if int( self.pulse_array[i]['length_increment'][:-3] ) == 0:
                        pass
                    else:
                        # convertion to ns
                        temp = self.pulse_array[i]['length_increment'].split(' ')
                        if temp[1] in timebase_dict:
                            flag = timebase_dict[temp[1]]
                            d_length = int((temp[0]))*flag
                        else:
                            pass

                        temp2 = self.pulse_array[i]['length'].split(' ')
                        if temp2[1] in timebase_dict:
                            flag2 = timebase_dict[temp2[1]]
                            leng = int((temp2[0]))*flag2
                        else:
                            pass

                        self.pulse_array[i]['length'] = str( leng + d_length ) + ' ns'
 
                    i += 1

                self.shift_count = 1
                self.current_phase_index = 0

            else:
                set_from_list = set(pulses)
                for element in set_from_list:
                    if element in self.pulse_name_array:
                        pulse_index = self.pulse_name_array.index(element)

                        if int( self.pulse_array[pulse_index]['length_increment'][:-3] ) == 0:
                            pass
                        else:
                            # convertion to ns
                            temp = self.pulse_array[pulse_index]['length_increment'].split(' ')
                            if temp[1] in timebase_dict:
                                flag = timebase_dict[temp[1]]
                                d_length = int((temp[0]))*flag
                            else:
                                pass

                            temp2 = self.pulse_array[pulse_index]['length'].split(' ')
                            if temp2[1] in timebase_dict:
                                flag2 = timebase_dict[temp2[1]]
                                leng = int((temp2[0]))*flag2
                            else:
                                pass
                            
                            self.pulse_array[pulse_index]['length'] = str( leng + d_length ) + ' ns'

                        self.shift_count = 1
                        self.current_phase_index = 0

        elif test_flag == 'test':
            if len(pulses) == 0:
                i = 0
                while i < len( self.pulse_array ):
                    if int( self.pulse_array[i]['length_increment'][:-3] ) == 0:
                        pass
                    else:
                        # convertion to ns
                        temp = self.pulse_array[i]['length_increment'].split(' ')
                        if temp[1] in timebase_dict:
                            flag = timebase_dict[temp[1]]
                            d_length = int((temp[0]))*flag
                        else:
                            assert(1 == 2), "Incorrect time dimension (ns, us, ms, s)"

                        temp2 = self.pulse_array[i]['length'].split(' ')
                        if temp2[1] in timebase_dict:
                            flag2 = timebase_dict[temp2[1]]
                            leng = int((temp2[0]))*flag2
                        else:
                            assert(1 == 2), "Incorrect time dimension (ns, us, ms, s)"
                        
                        if ( leng + d_length ) <= max_pulse_length:
                            self.pulse_array[i]['length'] = str( leng + d_length ) + ' ns'
                        else:
                            assert(1 == 2), 'Exceeded maximum pulse length (1900 ns) when increment the pulse'

                    i += 1

                self.shift_count = 1
                self.current_phase_index = 0

            else:
                set_from_list = set(pulses)
                for element in set_from_list:
                    if element in self.pulse_name_array:

                        pulse_index = self.pulse_name_array.index(element)
                        if int( self.pulse_array[pulse_index]['length_increment'][:-3] ) == 0:
                            pass
                        else:
                            # convertion to ns
                            temp = self.pulse_array[pulse_index]['length_increment'].split(' ')
                            if temp[1] in timebase_dict:
                                flag = timebase_dict[temp[1]]
                                d_length = int((temp[0]))*flag
                            else:
                                assert(1 == 2), "Incorrect time dimension (ns, us, ms, s)"

                            temp2 = self.pulse_array[pulse_index]['length'].split(' ')
                            if temp2[1] in timebase_dict:
                                flag2 = timebase_dict[temp2[1]]
                                leng = int((temp2[0]))*flag2
                            else:
                                assert(1 == 2), "Incorrect time dimension (ns, us, ms, s)"
                                    
                            if ( leng + d_length ) <= max_pulse_length:
                                self.pulse_array[pulse_index]['length'] = str( leng + d_length ) + ' ns'
                            else:
                                assert(1 == 2), 'Exceeded maximum pulse length (1900 ns) when increment the pulse'

                        self.shift_count = 1
                        self.current_phase_index = 0

                    else:
                        assert(1 == 2), "There is no pulse with the specified name"

    def pulser_reset(self, rep_rate = repetition_rate):
        """
        Reset all pulses to the initial state it was in at the start of the experiment.
        It includes the complete functionality of pulser_pulse_reset(), but also immediately
        updates the pulser as it is done by calling pulser_update().
        """
        if test_flag != 'test':
            # get repetition rate
            rep_rate = self.rep_rate[0]
            if rep_rate[-3:] == ' Hz':
                rep_time = int(1000000000/float(rep_rate[:-3]))
            elif rep_rate[-3:] == 'kHz':
                rep_time = int(1000000/float(rep_rate[:-4]))
            elif rep_rate[-3:] == 'MHz':
                rep_time = int(1000/float(rep_rate[:-4]))

            # reset the pulses; deepcopy helps to create a TRULY NEW array
            self.pulse_array = deepcopy( self.pulse_array_init )
            # using a special functions for convertion to instructions
            # we get two return arrays because of pulser_visualizer. It is not the case for test flag.
            #temp, visualizer = self.convert_to_bit_pulse( self.pulse_array )
            to_spinapi = self.split_into_parts( self.pulse_array, rep_time )
            general.message( to_spinapi )

            # initialization
            #pb_init()
            #pb.core_clock(clock)
            sp.pb_init()
            sp.pb_core_clock(clock)

            #pb_start_programming(0)
            sp.pb_start_programming(0)
            i = 0
            while i < len( to_spinapi) - 1:
                if i == 0: 
                    # to create a link for BRANCH
                    #start = pb_inst(ON | "0x%X" % to_spinapi[i][0], CONTINUE, 0, "0x%X" % to_spinapi[i][2])
                    start = sp.pb_inst(14680064 + to_spinapi[i][0], 0, 0, to_spinapi[i][2])
                else:
                    #pb_inst(ON | "0x%X" % to_spinapi[i][0], CONTINUE, 0, "0x%X" % to_spinapi[i][2])
                    sp.pb_inst(14680064 + to_spinapi[i][0], 0, 0, to_spinapi[i][2])
                ###if i == 0:
                    ###pass
                    #print('ON | ' + "0x%X" % to_spinapi[i][0] + ', CONTINUE, 0, ' + "0x%X" % to_spinapi[i][2] )
                ###else:
                    ###pass
                    #print('ON | ' + "0x%X" % to_spinapi[i][0] + ', CONTINUE, 0, ' + "0x%X" % to_spinapi[i][2] )

                i += 1

            # last instruction for delay
            #pb_inst(ON | "0x%X" % to_spinapi[i][0], BRANCH, 0, "0x%X" % to_spinapi[i][2])
            sp.pb_inst(14680064 + to_spinapi[i][0], 6, 0, to_spinapi[i][2])
            #print('ON | ' + "0x%X" % to_spinapi[i][0] + ', BRANCH, start, ' + "0x%X" % to_spinapi[i][2] )

            #pb_stop_programming()
            #pb_reset()
            #pb_start()

            sp.pb_stop_programming()
            sp.pb_reset()
            sp.pb_start()

            #pb_close()
            sp.pb_close()

            self.reset_count = 1
            self.increment_count = 0
            self.shift_count = 0
            self.current_phase_index = 0

        elif test_flag == 'test':
            # get repetition rate
            rep_rate = self.rep_rate[0]
            if rep_rate[-3:] == ' Hz':
                rep_time = int(1000000000/float(rep_rate[:-3]))
            elif rep_rate[-3:] == 'kHz':
                rep_time = int(1000000/float(rep_rate[:-4]))
            elif rep_rate[-3:] == 'MHz':
                rep_time = int(1000/float(rep_rate[:-4]))
            else:
                assert( 1 == 2 ), 'Incorrect dimension of repetition rate (Hz, kHz, MHz)'

            # reset the pulses; deepcopy helps to create a TRULY NEW array
            self.pulse_array = deepcopy( self.pulse_array_init )
            # using a special functions for convertion to instructions
            #to_spinapi = self.instruction_pulse( self.convert_to_bit_pulse( self.pulse_array ), rep_time )
            to_spinapi = self.split_into_parts( self.pulse_array, rep_time )

            self.reset_count = 1
            self.increment_count = 0
            self.shift_count = 0
            self.current_phase_index = 0

    def pulser_pulse_reset(self, *pulses):
        """
        Reset all pulses to the initial state it was in at the start of the experiment.
        It does not update the pulser, if you want to reset all pulses and and also update 
        the pulser use the function pulser_reset() instead.
        """
        if test_flag != 'test':
            if len(pulses) == 0:
                self.pulse_array = deepcopy(self.pulse_array_init)
                self.reset_count = 0
                self.increment_count = 0
                self.shift_count = 0
                self.current_phase_index = 0
            else:
                set_from_list = set(pulses)
                for element in set_from_list:
                    if element in self.pulse_name_array:
                        pulse_index = self.pulse_name_array.index(element)

                        self.pulse_array[pulse_index]['start'] = self.pulse_array_init[pulse_index]['start']
                        self.pulse_array[pulse_index]['length'] = self.pulse_array_init[pulse_index]['length']

                        self.reset_count = 0
                        self.increment_count = 0
                        self.shift_count = 0

        elif test_flag == 'test':
            if len(pulses) == 0:
                self.pulse_array = deepcopy(self.pulse_array_init)
                self.reset_count = 0
                self.increment_count = 0
                self.shift_count = 0
                self.current_phase_index = 0
            else:
                set_from_list = set(pulses)
                for element in set_from_list:
                    if element in self.pulse_name_array:
                        pulse_index = self.pulse_name_array.index(element)

                        self.pulse_array[pulse_index]['start'] = self.pulse_array_init[pulse_index]['start']
                        self.pulse_array[pulse_index]['length'] = self.pulse_array_init[pulse_index]['length']

                        self.reset_count = 0
                        self.increment_count = 0
                        self.shift_count = 0

    def pulser_stop(self):
        """
        A function to stop pulse sequence
        """
        if test_flag != 'test':

            # initialization
            #pb_init()
            #pb.core_clock(clock)
            ###sp.pb_init()
            ###sp.pb_core_clock(clock)

            #pb_start_programming(PULSE_PROGRAM)
            #pb_inst(ON | "0x%X" % 0, CONTINUE, 0, "0x%X" % 16)
            ###sp.pb_start_programming(0)
            ###sp.pb_inst(14680064, 0, 0, 16)

            #general.message('ON | ', "0x%X" % 0, ', CONTINUE, 0, ', "0x%X" % 12)
            #pb_inst(ON | "0x%X" % 0, STOP, 0, "0x%X" % 16)
            # STOP is 1
            ###sp.pb_inst(14680064, 1, 0, 16)
            #general.message('ON | ', "0x%X" % 0, ', STOP, 0, ', "0x%X" % 16)

            #pb_stop_programming()
            #pb_reset()
            #pb_start()
            
            #pb_close()

            ###sp.pb_stop_programming()
            ###sp.pb_reset()
            ###sp.pb_start()
            pass
            ###sp.pb_close()

            #return to_spinapi

        elif test_flag == 'test':
            pass

    def pulser_state(self):
        if test_flag != 'test':
            sp.pb_init()
            answer = sp.pb_read_status()
            #pass
            return answer
        elif test_flag == 'test':
            pass

    def pulser_visualize(self):
        """
        Function for visualization of pulse sequence.
        There are two possibilities:
        1) Real final instructions with already summed up channel numbers
        2) Individual pulses
        """
        if test_flag != 'test':
            rep_rate = self.rep_rate[0]
            if rep_rate[-3:] == ' Hz':
                rep_time = int(1000000000/float(rep_rate[:-3]))
            elif rep_rate[-3:] == 'kHz':
                rep_time = int(1000000/float(rep_rate[:-4]))
            elif rep_rate[-3:] == 'MHz':
                rep_time = int(1000/float(rep_rate[:-4]))

            # Real final instructions with already summed up channel numbers
            #preparation = self.split_into_parts( self.pulse_array, rep_time )
            #visualizer = self.convert_to_bit_pulse_visualizer_final_instructions( np.asarray(preparation[:-1] ))

            # Individual pulses
            visualizer = self.convert_to_bit_pulse_visualizer(self.pulse_array )

            #general.plot_1d('Plot XY Test', np.arange(len(to_spinapi)), to_spinapi, label='test data1', timeaxis = 'False')
            general.plot_2d('Pulses Visualizer', visualizer, \
                start_step=( (0, 1), (0, 1) ), xname='Time',\
                xscale='ns', yname='Pulse Number', yscale='', zname='2**(channel)', zscale='')

        elif test_flag == 'test':
            pass

    # Auxilary functions
    def convertion_to_numpy(self, p_array):
        """
        Convertion the pulse_array into numpy array in the form of
        [channel_number, start, end, delta_start, length_increment]
        channel_number is an integer: 2**(ch), where ch from channel_dict
        start is a pulse start in a pulser clock sample rate
        end is a pulse end in a pulser clock sample rate
        delta_start is a pulse delta_start in a pulser clock sample rate
        length_increment is a pulse length_increment in a pulser clock sample rate
        The numpy array is shifted (250 ns) and sorted according to channel number
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
                # get start
                st = p_array[i]['start']
                if st[-2:] == 'ns':
                    st_time = int(float(st[:-3])/timebase)
                elif st[-2:] == 'us':
                    st_time = int(float(st[:-3])*1000/timebase)
                elif st[-2:] == 'ms':
                    st_time = int(float(st[:-3])*1000000/timebase)
                elif st[-2:] == 's':
                    st_time = int(float(st[:-3])*1000000000/timebase)
                # get length
                leng = p_array[i]['length']
                if leng[-2:] == 'ns':
                    leng_time = int(float(leng[:-3])/timebase)
                elif leng[-2:] == 'us':
                    leng_time = int(float(leng[:-3])*1000/timebase)
                elif leng[-2:] == 'ms':
                    leng_time = int(float(leng[:-3])*1000000/timebase)
                elif leng[-2:] == 's':
                    leng_time = int(float(leng[:-3])*1000000000/timebase)

                # get delta start
                del_st = p_array[i]['delta_start']
                if del_st[-2:] == 'ns':
                    delta_start = int(float(del_st[:-3])/timebase)
                elif del_st[-2:] == 'us':
                    delta_start = int(float(del_st[:-3])*1000/timebase)
                elif del_st[-2:] == 'ms':
                    delta_start = int(float(del_st[:-3])*1000000/timebase)
                elif del_st[-2:] == 's':
                    delta_start = int(float(del_st[:-3])*1000000000/timebase)

                # get length_incremetn
                len_in = p_array[i]['length_increment']
                if len_in[-2:] == 'ns':
                    length_increment = int(float(len_in[:-3])/timebase)
                elif len_in[-2:] == 'us':
                    length_increment = int(float(len_in[:-3])*1000/timebase)
                elif len_in[-2:] == 'ms':
                    length_increment = int(float(len_in[:-3])*1000000/timebase)
                elif len_in[-2:] == 's':
                    length_increment = int(float(len_in[:-3])*1000000000/timebase)

                # creating converted array
                # in terms of bits the number of channel is 2**(ch_num - 1)
                #pulse_temp_array.append( (2**(ch_num), st_time, st_time + leng_time, delta_start, length_increment) )
                pulse_temp_array.append( (2**(ch_num), st_time + constant_shift, constant_shift + st_time + leng_time) )

                i += 1

            # should be sorted according to channel number for corecct splitting into subarrays
            return np.asarray(sorted(pulse_temp_array, key = lambda x: int(x[0])), dtype = np.int64)

        elif test_flag == 'test':
            i = 0
            pulse_temp_array = []
            num_pulses = len( p_array )
            while i < num_pulses:
                # get channel number
                ch = p_array[i]['channel']
                if ch in channel_dict:
                    ch_num = channel_dict[ch]
                # get start
                st = p_array[i]['start']
                if st[-2:] == 'ns':
                    st_time = int(float(st[:-3])/timebase)
                elif st[-2:] == 'us':
                    st_time = int(float(st[:-3])*1000/timebase)
                elif st[-2:] == 'ms':
                    st_time = int(float(st[:-3])*1000000/timebase)
                elif st[-2:] == 's':
                    st_time = int(float(st[:-3])*1000000000/timebase)
                # get length
                leng = p_array[i]['length']
                if leng[-2:] == 'ns':
                    leng_time = int(float(leng[:-3])/timebase)
                elif leng[-2:] == 'us':
                    leng_time = int(float(leng[:-3])*1000/timebase)
                elif leng[-2:] == 'ms':
                    leng_time = int(float(leng[:-3])*1000000/timebase)
                elif leng[-2:] == 's':
                    leng_time = int(float(leng[:-3])*1000000000/timebase)

                # get delta start
                del_st = p_array[i]['delta_start']
                if del_st[-2:] == 'ns':
                    delta_start = int(float(del_st[:-3])/timebase)
                elif del_st[-2:] == 'us':
                    delta_start = int(float(del_st[:-3])*1000/timebase)
                elif del_st[-2:] == 'ms':
                    delta_start = int(float(del_st[:-3])*1000000/timebase)
                elif del_st[-2:] == 's':
                    delta_start = int(float(del_st[:-3])*1000000000/timebase)

                # get length_increment
                len_in = p_array[i]['length_increment']
                if len_in[-2:] == 'ns':
                    length_increment = int(float(len_in[:-3])/timebase)
                elif len_in[-2:] == 'us':
                    length_increment = int(float(len_in[:-3])*1000/timebase)
                elif len_in[-2:] == 'ms':
                    length_increment = int(float(len_in[:-3])*1000000/timebase)
                elif len_in[-2:] == 's':
                    length_increment = int(float(len_in[:-3])*1000000000/timebase)

                # creating converted array
                # in terms of bits the number of channel is 2**(ch_num - 1)
                pulse_temp_array.append( (2**(ch_num), constant_shift + st_time, constant_shift + st_time + leng_time ) )

                i += 1

            # should be sorted according to channel number for corecct splitting into subarrays
            return np.asarray(sorted(pulse_temp_array, key = lambda x: int(x[0])), dtype = np.int64)

    def splitting_acc_to_channel(self, np_array):
        """
        A function that splits pulse array into
        several array that have the same channel
        I.E. [[1, 10, 100], [8, 100, 40], [8, 200, 20], [8, 300, 20] 
        -> [array([[1, 10, 100]]) , array([[8, 100, 40], [8, 200, 20], [8, 300, 20]])]
        Input array should be sorted
        """
        if test_flag != 'test':
            # according to 0 element (channel number)
            answer = np.split(np_array, np.where(np.diff(np_array[:,0]))[0] + 1)
            return answer

        elif test_flag == 'test':
            # according to 0 element (channel number)
            answer = np.split(np_array, np.where(np.diff(np_array[:,0]))[0] + 1)
            return answer

    def check_problem_pulses(self, np_array):
        """
        A function for checking whether there is a two
        close to each other pulses (less than 40 ns)
        In Auto_defense = True we checked everything except
        AMN_ON and LNA_PROTECT
        """
        if test_flag != 'test':
            # sorted pulse list in order to be able to have an arbitrary pulse order inside
            # the definition in the experimental script
            sorted_np_array = np.asarray(sorted(np_array, key = lambda x: int(x[1])), dtype = np.int64)

            # compare the end time with the start time for each couple of pulses
            for index, element in enumerate(sorted_np_array[:-1]):
                # minimal_distance is 40 ns now
                if sorted_np_array[index + 1][1] - element[2] < minimal_distance:
                    assert(1 == 2), 'Overlapping pulses or two pulses with less than ' + str(minimal_distance*2) + ' ns distance'
                else:
                    pass

            return sorted_np_array

        elif test_flag == 'test':
            sorted_np_array = np.asarray(sorted(np_array, key = lambda x: int(x[1])), dtype = np.int64)

            # compare the end time with the start time for each couple of pulses
            for index, element in enumerate(sorted_np_array[:-1]):
                # minimal_distance is 40 ns now
                if sorted_np_array[index + 1][1] - element[2] < minimal_distance:
                    assert(1 == 2), 'Overlapping pulses or two pulses with less than ' + str(minimal_distance*2) + ' ns distance'
                else:
                    pass

            return np_array

    def check_problem_pulses_phase(self, np_array):
        """
        A function for checking whether there is a two
        close to each other pulses (less than 10 ns)
        In Auto_defense = True by this function we checked only 
        -X +Y -Y pulses since they have different minimal distance
        """
        if test_flag != 'test':
            # sorted pulse list in order to be able to have an arbitrary pulse order inside
            # the definition in the experimental script
            sorted_np_array = np.asarray(sorted(np_array, key = lambda x: int(x[1])), dtype = np.int64)

            # compare the end time with the start time for each couple of pulses
            for index, element in enumerate(sorted_np_array[:-1]):
                # minimal_distance is 10 ns now
                if sorted_np_array[index + 1][1] - element[2] < minimal_distance_phase:
                    assert(1 == 2), 'Overlapping pulses or two pulses with less than ' + str(minimal_distance_phase*2) + ' ns distance'
                else:
                    pass

            return sorted_np_array

        elif test_flag == 'test':
            sorted_np_array = np.asarray(sorted(np_array, key = lambda x: int(x[1])), dtype = np.int64)

            # compare the end time with the start time for each couple of pulses
            for index, element in enumerate(sorted_np_array[:-1]):
                # minimal_distance is 10 ns now
                if sorted_np_array[index + 1][1] - element[2] < minimal_distance_phase:
                    assert(1 == 2), 'Overlapping pulses or two pulses with less than ' + str(minimal_distance_phase*2) + ' ns distance'
                else:
                    pass

            return np_array

    def delete_duplicates(self, np_array):
        """
        Auxilary function that delete duplicates from numpy array
        It is used when we deal with AMP_ON and LNA_PROTECT pulses
        with less than 12 ns distance
        """
        if test_flag != 'test':
            no_duplicate_array = np.unique(np_array, axis = 0)
            return no_duplicate_array

        elif test_flag == 'test':
            no_duplicate_array = np.unique(np_array, axis = 0)
            return no_duplicate_array

    def preparing_to_bit_pulse(self, np_array):
        """
        For pulses at each channel we check whether there is overlapping pulses using 
        check_problem_pulses()

        This function also automatically adds LNA_PROTECT and AMP_ON pulses 
        using add_amp_on_pulses() / add_lna_protect_pulses() and check
        them on the distance < 12 ns, if so they are combined in one pulse inside 
        instruction_pulse_short_lna_amp() function

        for phase pulses the minimal distance for checking is 10 ns
        for mw - 40 ns
        """
        if test_flag != 'test':
            if auto_defense == 'False':
                split_pulse_array = self.splitting_acc_to_channel( self.convertion_to_numpy( np_array ) )

                # iterate over all pulses at different channels
                for index, element in enumerate(split_pulse_array):
                    # for all pulses just check 40 ns distance
                    self.check_problem_pulses(element)
                    # get assertion error if the distance < 40 ns
                    
                return self.convertion_to_numpy( np_array )

            elif auto_defense == 'True':
                split_pulse_array = self.splitting_acc_to_channel( self.convertion_to_numpy( np_array ) )

                # iterate over all pulses at different channels
                for index, element in enumerate(split_pulse_array):
                    if element[0, 0] == 2**channel_dict['MW']:

                        # for MW pulses check 40 ns distance and add AMP_ON, LNA_PROTECT pulses
                        self.check_problem_pulses(element)
                        # add AMP_ON and LNA_PROTECT
                        amp_on_pulses = self.add_amp_on_pulses(element)
                        lna_pulses = self.add_lna_protect_pulses(element)
                        # check AMP_ON, LNA_PROTECT pulses on < 12 ns distance
                        cor_pulses_amp, prob_pulses_amp = self.check_problem_pulses_amp_lna(amp_on_pulses)
                        cor_pulses_lna, prob_pulses_lna = self.check_problem_pulses_amp_lna(lna_pulses)

                        # combining short distance AMP_ON pulses; the action depends on
                        # whether there are "problenatic pulses" (prob_pulses_amp)
                        # cor_pulses_amp - pulses with > 12 ns distance
                        # problenatic pulses are joined by convertion to bit array, applying 
                        # check_short_pulses() / joining_pulses() inside convert_to_bit_pulse_amp_lna()
                        # and back to instruction instruction_pulse_short_lna_amp()
                        if prob_pulses_amp[0][0] == 0:
                            cor_pulses_amp_final = cor_pulses_amp
                        elif cor_pulses_amp[0][0] == 0:
                            # nothing to concatenate
                            cor_pulses_amp_final = self.instruction_pulse_short_lna_amp(self.convert_to_bit_pulse_amp_lna(prob_pulses_amp, \
                                channel_dict['AMP_ON']))                   
                        else:
                            cor_pulses_amp_final = np.concatenate((cor_pulses_amp, self.instruction_pulse_short_lna_amp(self.convert_to_bit_pulse_amp_lna(prob_pulses_amp, \
                                channel_dict['AMP_ON']))), axis = 0)

                        # combining short distance LNA_PROTECT pulses
                        if prob_pulses_lna[0][0] == 0:
                            cor_pulses_lna_final = cor_pulses_lna
                        elif cor_pulses_lna[0][0] == 0:
                            # nothing to concatenate
                            cor_pulses_lna_final =  self.instruction_pulse_short_lna_amp(self.convert_to_bit_pulse_amp_lna(prob_pulses_lna, \
                                channel_dict['LNA_PROTECT']))
                        else:
                            cor_pulses_lna_final =  np.concatenate((cor_pulses_lna, self.instruction_pulse_short_lna_amp(self.convert_to_bit_pulse_amp_lna(prob_pulses_lna, \
                                channel_dict['LNA_PROTECT']))), axis = 0)

                    elif element[0, 0] == 2**channel_dict['-X'] or element[0, 0] == 2**channel_dict['+Y']:
                        pass
                        # for phase pulses just check 10 ns distance
                        # self.check_problem_pulses(element)
                        # get assertion error if the distance < 10 ns
                    else:
                        pass
                        # for non-MW pulses just check 40 ns distance
                        #self.check_problem_pulses(element)
                        # get assertion error if the distance < 40 ns

                # combine all pulses
                #np.concatenate( (self.convertion_to_numpy( self.pulse_array ), cor_pulses_amp_final, cor_pulses_lna_final), axis = None)
                return np.row_stack( (self.convertion_to_numpy( self.pulse_array ), cor_pulses_amp_final, cor_pulses_lna_final))

        elif test_flag == 'test':
            if auto_defense == 'False':
                split_pulse_array = self.splitting_acc_to_channel( self.convertion_to_numpy( np_array ) )

                # iterate over all pulses at different channels
                for index, element in enumerate(split_pulse_array):
                    # for all pulses just check 40 ns distance
                    self.check_problem_pulses(element)
                    # get assertion error if the distance < 40 ns
                    
                return self.convertion_to_numpy( np_array )

            elif auto_defense == 'True':
                split_pulse_array = self.splitting_acc_to_channel( self.convertion_to_numpy( np_array ) )

                for index, element in enumerate(split_pulse_array):
                    if element[0, 0] == 2**channel_dict['MW']:

                        self.check_problem_pulses(element)
                        amp_on_pulses = self.add_amp_on_pulses(element)
                        lna_pulses = self.add_lna_protect_pulses(element)

                        # check AMP_ON, LNA_PROTECT pulses
                        cor_pulses_amp, prob_pulses_amp = self.check_problem_pulses_amp_lna(amp_on_pulses)
                        cor_pulses_lna, prob_pulses_lna = self.check_problem_pulses_amp_lna(lna_pulses)

                        # combining short distance AMP_ON pulses
                        if prob_pulses_amp[0][0] == 0:
                            cor_pulses_amp_final = cor_pulses_amp
                        elif cor_pulses_amp[0][0] == 0:
                            cor_pulses_amp_final = self.instruction_pulse_short_lna_amp(self.convert_to_bit_pulse_amp_lna(prob_pulses_amp, \
                                channel_dict['AMP_ON']))
                        else:
                            cor_pulses_amp_final = np.concatenate((cor_pulses_amp, self.instruction_pulse_short_lna_amp(self.convert_to_bit_pulse_amp_lna(prob_pulses_amp, \
                                channel_dict['AMP_ON']))), axis = 0)

                        # combining short distance LNA_PROTECT pulses
                        if prob_pulses_lna[0][0] == 0:
                            cor_pulses_lna_final = cor_pulses_lna
                        elif cor_pulses_lna[0][0] == 0:
                            cor_pulses_lna_final = self.instruction_pulse_short_lna_amp(self.convert_to_bit_pulse_amp_lna(prob_pulses_lna, \
                                channel_dict['LNA_PROTECT']))
                        else:
                            cor_pulses_lna_final =  np.concatenate((cor_pulses_lna, self.instruction_pulse_short_lna_amp(self.convert_to_bit_pulse_amp_lna(prob_pulses_lna, \
                                channel_dict['LNA_PROTECT']))), axis = 0)
                    
                    elif element[0, 0] == 2**channel_dict['-X'] or element[0, 0] == 2**channel_dict['+Y']:
                        # for phases pulses just check 10 ns distance
                        self.check_problem_pulses_phase(element)
                    else:
                        # for non-MW pulses just check 40 ns distance
                        self.check_problem_pulses(element)

                # combine all pulses
                #np.concatenate( (self.convertion_to_numpy( self.pulse_array ), cor_pulses_amp_final, cor_pulses_lna_final), axis = None) 
                return np.row_stack( (self.convertion_to_numpy( self.pulse_array ), cor_pulses_amp_final, cor_pulses_lna_final)) 

    def split_into_parts(self, np_array, rep_time):
        """
        When we have situatuin with a big distance (> 2000 ns) between
        two pulses it is time and memory efficient to treat this areas separately.
        To do it we:
        - Sort pulses using start time
        - Find indexes jump
        - Apply the obtained mask on initial pulse array
        After that each area are treated separately by convert_to_bit_pulse() and
        instruction_pulse()
        """
        if test_flag != 'test':
            answer = []
            min_list = []
            pulses = self.preparing_to_bit_pulse(np_array)

            sorted_pulses_start = np.asarray(sorted(pulses, key = lambda x: int(x[1])), dtype = np.int64)
            # max_pulse_length is 2000 ns now
            index_jump = np.where(np.diff(sorted_pulses_start[:,1], axis = 0) > max_pulse_length )[0]
            sorted_arrays_parts = np.split(sorted_pulses_start, index_jump + 1)

            for index, element in enumerate(sorted_arrays_parts):
                temp, min_value = self.convert_to_bit_pulse(element)
                answer.append(self.instruction_pulse(temp))
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
                        # - min_list[0]*timebase common shifting of the first pulse
                        if index2 == 0:
                            element2[1] = shift_region
                            element2[2] = min_list[index]*timebase + element2[2] - shift_region - min_list[0]*timebase
                        elif index2 > 0:
                            element2[1] = element2[1] + min_list[index]*timebase - min_list[0]*timebase
                        
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

            if rep_time - one_array[-1][2] - one_array[-1][1] > (minimal_distance + 4):
                one_array.append( [0, one_array[-1][1] + one_array[-1][2], \
                    rep_time - one_array[-1][2] - one_array[-1][1]] )
                return one_array
            else:
                general.message('Pulse sequence is longer than one period of the repetition rate')
                sys.exit()

        elif test_flag == 'test':
            answer = []
            min_list = []
            pulses = self.preparing_to_bit_pulse(np_array)

            sorted_pulses_start = np.asarray(sorted(pulses, key = lambda x: int(x[1])), dtype = np.int64)
            # max_pulse_length is 2000 ns now
            index_jump = np.where(np.diff(sorted_pulses_start[:,1], axis = 0) > max_pulse_length/timebase )[0]
            sorted_arrays_parts = np.split(sorted_pulses_start, index_jump + 1)


            for index, element in enumerate(sorted_arrays_parts):
                temp, min_value = self.convert_to_bit_pulse(element)
                answer.append(self.instruction_pulse(temp))
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
                            element2[2] = min_list[index]*timebase + element2[2] - shift_region - min_list[0]*timebase
                        elif index2 > 0:
                            element2[1] = element2[1] + min_list[index]*timebase - min_list[0]*timebase
                        
                    #shift_region = element[-1][1] + element[-1][2]
                    #general.message(shift_region)

                        #general.message(element)
                        #element[0][1] = answer[index - 1][-1][1] + answer[index - 1][-1][2]
                        #element[0][2] = element[0][2] - element[0][1]

            one_array = sum(answer, [])
            
            if rep_time - one_array[-1][2] - one_array[-1][1] > (minimal_distance + 4):
                one_array.append( [0, one_array[-1][1] + one_array[-1][2], \
                    rep_time - one_array[-1][2] - one_array[-1][1]] )
                return one_array
            else:
                assert(1 == 2), 'Pulse sequence is longer than one period of the repetition rate'            

    def convert_to_bit_pulse(self, np_array):
        """
        A function to calculate in which time interval
        two or more different channels are on.
        All the pulses converted in an bit_array of 0 and 1, where
        1 corresponds to the time interval when the channel is on.
        The size of the bit_array is determined by the total length
        of the full pulse sequence.
        Finally, a bit_array is multiplied by a 2**ch in order to
        calculate CH instructions for SpinAPI.

        It is optimized for using at subarrays inside split_into_parts()
        """

        if test_flag != 'test':
            #pulses = self.preparing_to_bit_pulse(np_array)
            pulses = np_array
            max_pulse = np.amax(pulses[:,2])
            # we get rid of constant shift in the first pulse, since
            # it is useless in terms of pulse bluster instructions
            # the first pulse in sequence will start at 50 ns all other shifted accordingly
            # this value can be adjust by add_shift parameter (multiplited by timebase)
            min_pulse = np.amin(pulses[:,1]) - add_shift

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

                i += 1

            return bit_array, min_pulse

        elif test_flag == 'test':
            #pulses = self.preparing_to_bit_pulse(np_array)
            pulses = np_array

            max_pulse = np.amax(pulses[:,2])
            min_pulse = np.amin(pulses[:,1]) - add_shift

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

                i += 1

            return bit_array, min_pulse

    def convert_to_bit_pulse_visualizer(self, np_array):
        """
        The same function optimized for using in pulser_visualize()
        in which we DO NOT split all area into subarrays if 
        there are > 2000 ns distance between pulses
        
        A constant shift in the first pulse is omitted

        Note that this function provides a different treatment of
        pulse sequence. It order to check what EXACTLY we havw after
        convert_to_bit_pulse() use convert_to_bit_pulse_visualizer_final_instructions()
        """

        if test_flag != 'test':
            pulses = self.preparing_to_bit_pulse(np_array)
            #pulses = np_array
            #for index, element in enumerate(pulses):
            #    element[2] = element[1] + element[2]  

            max_pulse = np.amax(pulses[:,2])
            min_pulse = np.amin(pulses[:,1]) - add_shift

            bit_array = np.zeros( 2*(max_pulse - min_pulse), dtype = np.int64 )
            bit_array_pulses = []

            i = 0
            while i < len(pulses):
                # convert each pulse in an array of 0 and 1,
                # 1 corresponds to the time interval, where the channel is on
                if pulses[i, 0] != 0:
                    translation_array = pulses[i, 0]*np.concatenate( (np.zeros( 2*(pulses[i, 1] - min_pulse), dtype = np.int64), \
                        np.ones(2*(pulses[i, 2] - pulses[i, 1]), dtype = np.int64), \
                        np.zeros(2*(max_pulse - pulses[i, 2]), dtype = np.int64)), axis = None)
                
                    # appending each pulses individually
                    bit_array_pulses.append(translation_array)

                i += 1

            return bit_array_pulses

        elif test_flag == 'test':
            pulses = self.preparing_to_bit_pulse(np_array)
            #pulses = np_array
            #for index, element in enumerate(pulses):
            #    element[2] = element[1] + element[2]  

            max_pulse = np.amax(pulses[:,1])
            min_pulse = np.amin(pulses[:,1]) - add_shift*0

            bit_array = np.zeros( max_pulse - 0*min_pulse, dtype = np.int64 )
            bit_array_pulses = []

            i = 0
            while i < len(pulses):
                # convert each pulse in an array of 0 and 1,
                # 1 corresponds to the time interval, where the channel is on
                if pulses[i, 0] != 0:
                    translation_array = pulses[i, 0]*np.concatenate( (np.zeros( pulses[i, 1] - 0*min_pulse, dtype = np.int64), \
                        np.ones(pulses[i, 2] - pulses[i, 1], dtype = np.int64), \
                        np.zeros(max_pulse - pulses[i, 2], dtype = np.int64)), axis = None)
                
                # summing arrays for each pulse into the finalbit_array
                    bit_array_pulses.append(translation_array)

                i += 1

            return bit_array_pulses

    def convert_to_bit_pulse_visualizer_final_instructions(self, np_array):
        """
        The same function optimized for using in pulser_visualize()
        in which we DO NOT split all area into subarrays if 
        there are > 2000 ns distance between pulses
        
        A constant shift in the first pulse is omitted.

        It is shown exactly the pulses we will have after convert_to_bit_pulse()

        Please note that channel numbers will be already joined if two channels are turned on
        simultaneously
        """

        if test_flag != 'test':
            #pulses = self.preparing_to_bit_pulse(np_array)
            pulses = np_array
            # convert back to channel, start, end
            # from channel, start, length
            for index, element in enumerate(pulses):
                element[2] = element[1] + element[2]  

            max_pulse = np.amax(pulses[:,2])
            min_pulse = np.amin(pulses[:,1]) - add_shift*0

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

        elif test_flag == 'test':
            #pulses = self.preparing_to_bit_pulse(np_array)
            pulses = np_array
            for index, element in enumerate(pulses):
                element[2] = element[1] + element[2]  

            max_pulse = np.amax(pulses[:,1])
            min_pulse = np.amin(pulses[:,1]) - add_shift*0

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

    def instruction_pulse(self, np_array):
        """
        Final convertion to the pulse blaster instruction pulses
        It splits the bit_array into sequence of bit_arrays for individual pulses
        After that convert them into instructions [channel, start, length]
        
        Bit array should not start with nonzero elements

        It is used inside convert_to_bit_pulse()
        """
        if test_flag != 'test':
            final_pulse_array = []

            # Create an array that is 1 where a is 0, and pad each end with an extra 0.
            iszero = np.concatenate(([0], np_array, [0]))
            absdiff = np.abs(np.diff(iszero))

            # creating a mask to split bit array
            ranges = np.where(absdiff != 0)[0]
            # using a mask
            pulse_array = np.split(np_array, ranges)
            pulse_info = np.concatenate(([0], ranges))

            # return back timebase; convert to instructions
            for index, element in enumerate(pulse_info[:-1]):
                final_pulse_array.append( [pulse_array[index][0], timebase*pulse_info[index], timebase*(pulse_info[index + 1] - pulse_info[index])] )

            return final_pulse_array

        elif test_flag == 'test':
            final_pulse_array = []

            # Create an array that is 1 where a is 0, and pad each end with an extra 0.
            iszero = np.concatenate(([0], np_array, [0]))
            absdiff = np.abs(np.diff(iszero))

            ranges = np.where(absdiff != 0)[0]
            pulse_array = np.split(np_array, ranges)
            pulse_info = np.concatenate(([0], ranges))

            for index, element in enumerate(pulse_info[:-1]):
                final_pulse_array.append( [pulse_array[index][0], timebase*pulse_info[index], timebase*(pulse_info[index + 1] - pulse_info[index])] )

            return final_pulse_array

    def add_amp_on_pulses(self, p_list):
        """
        A function that automatically add AMP_ON pulses with corresponding delays
        specified by switch_delay and amp_delay
        """
        if test_flag != 'test':
            if auto_defense == 'False':
                pass
            elif auto_defense == 'True':
                amp_on_list = []
                #general.message( p_list )
                for index, element in enumerate(p_list):
                    if element[0] == 2**(channel_dict['MW']):
                        amp_on_list.append( [2**(channel_dict['AMP_ON']), element[1] - switch_delay, element[2] + amp_delay] )
                    else:
                        pass

                # additional checking and correcting amp_on pulse in the case
                # when amp_on pulses are diagonally shifted to mw pulses
                # in this case there can be nasty short overpal of amp_on pulse 2
                # and mw pulse 1 and so on
                for element in amp_on_list:
                    for element_mw in p_list:
                        if (element_mw[1] - element[1] <= overlap_amp_lna_mw) and (element_mw[1] - element[1] > 0):
                            element[1] = element[1] - overlap_amp_lna_mw
                        elif (element_mw[1] - element[1] >= -overlap_amp_lna_mw) and (element_mw[1] - element[1] < 0):
                            element[1] = element_mw[1]
                        elif (element_mw[1] - element[2]) <= overlap_amp_lna_mw and (element_mw[1] - element[2] > 0):
                            element[2] = element_mw[1]
                        elif (element_mw[1] - element[2]) >= -overlap_amp_lna_mw and (element_mw[1] - element[2] < 0):
                            # restriction on the pulse length in order to not jump into another restriction....
                            if element_mw[2] - element_mw[1] <= 30:
                                element[2] = element_mw[2]
                            else:
                                element[2] = element[2] + overlap_amp_lna_mw

                        # checking of start and end should be splitted into two checks
                        # in case of double start/end restriction
                        if (element_mw[2] - element[2] <= overlap_amp_lna_mw) and (element_mw[2] - element[2] > 0):
                            element[2] = element_mw[2]
                        elif (element_mw[2] - element[2] >= -overlap_amp_lna_mw) and (element_mw[2] - element[2] < 0):
                            element[2] = element[2] + overlap_amp_lna_mw
                        elif (element_mw[2] - element[1]) <= overlap_amp_lna_mw and (element_mw[2] - element[1] > 0):
                            # restriction on the pulse length in order to not jump into another restriction....
                            if element_mw[2] - element_mw[1] <= 30:
                                element[1] = element_mw[1]
                            else:
                                element[1] = element[1] - overlap_amp_lna_mw
                        elif (element_mw[2] - element[1]) >= -overlap_amp_lna_mw and (element_mw[2] - element[1] < 0):
                            element[1] = element_mw[2]

                # additional checking for phase and amp_on pulses after
                # overlap correction
                if len(self.phase_array_length) > 0:
                    split_pulse_array = self.splitting_acc_to_channel( self.convertion_to_numpy( self.pulse_array ) )
                    # iterate over all pulses at different channels and taking phase pulses
                    for index, element in enumerate(split_pulse_array):
                        if ( element[0, 0] == 2**channel_dict['-X'] ) or ( element[0, 0] == 2**channel_dict['+Y'] ):
                            for element_phase in element:
                                for element_amp in amp_on_list:
                                    if (element_phase[1] - element_amp[2] <= overlap_amp_lna_mw) and (element_phase[1] - element_amp[2] > 0):
                                        element_amp[2] = element_phase[1] + overlap_amp_lna_mw
                                    elif (element_phase[1] - element_amp[2] >= -overlap_amp_lna_mw) and (element_phase[1] - element_amp[2] < 0):
                                        element_amp[2] = element_amp[2] + overlap_amp_lna_mw
                                    # checking of start and end should be splitted into two checks
                                    # in case of double start/end restriction
                                    if (element_phase[1] - element_amp[1] <= overlap_amp_lna_mw) and (element_phase[1] - element_amp[1] > 0):
                                        element_amp[1] = element_amp[1] - overlap_amp_lna_mw
                                    elif (element_phase[1] - element_amp[1] >= -overlap_amp_lna_mw) and (element_phase[1] - element_amp[1] < 0):
                                        element_amp[1] = element_phase[1]                                
                        else:
                            pass

                return np.asarray(amp_on_list)

        elif test_flag == 'test':
            if auto_defense == 'False':
                pass
            elif auto_defense == 'True':
                amp_on_list = []
                for index, element in enumerate(p_list):
                    if element[0] == 2**(channel_dict['MW']):
                        if (element[2] + amp_delay) - (element[1] - switch_delay) <= max_pulse_length/2:
                            amp_on_list.append( [2**(channel_dict['AMP_ON']), element[1] - switch_delay, element[2] + amp_delay] )
                        else:
                            assert(1 == 2), 'Maximum available length (1900 ns) for AMP_ON pulse is reached'
                    else:
                        pass

                for element in amp_on_list:
                    for element_mw in p_list:
                        if (element_mw[1] - element[1] <= overlap_amp_lna_mw) and (element_mw[1] - element[1] > 0):
                            element[1] = element[1] - overlap_amp_lna_mw
                        elif (element_mw[1] - element[1] >= -overlap_amp_lna_mw) and (element_mw[1] - element[1] < 0):
                            element[1] = element_mw[1]
                        elif (element_mw[1] - element[2]) <= overlap_amp_lna_mw and (element_mw[1] - element[2] > 0):
                            element[2] = element_mw[1]
                        elif (element_mw[1] - element[2]) >= -overlap_amp_lna_mw and (element_mw[1] - element[2] < 0):
                            if element_mw[2] - element_mw[1] <= 30:
                                element[2] = element_mw[2]
                            else:
                                element[2] = element[2] + overlap_amp_lna_mw
                        # checking of start and end should be splitted into two checks
                        # in case of double start/end restriction
                        if (element_mw[2] - element[2] <= overlap_amp_lna_mw) and (element_mw[2] - element[2] > 0):
                            element[2] = element_mw[2]
                        elif (element_mw[2] - element[2] >= -overlap_amp_lna_mw) and (element_mw[2] - element[2] < 0):
                            element[2] = element[2] + overlap_amp_lna_mw
                        elif (element_mw[2] - element[1]) <= overlap_amp_lna_mw and (element_mw[2] - element[1] > 0):
                            if element_mw[2] - element_mw[1] <= 30:
                                element[1] = element_mw[1]
                            else:
                                element[1] = element[1] - overlap_amp_lna_mw
                        elif (element_mw[2] - element[1]) >= -overlap_amp_lna_mw and (element_mw[2] - element[1] < 0):
                            element[1] = element_mw[2]

                if len(self.phase_array_length) > 0:
                    split_pulse_array = self.splitting_acc_to_channel( self.convertion_to_numpy( self.pulse_array ) )
                    # iterate over all pulses at different channels and taking phase pulses
                    for index, element in enumerate(split_pulse_array):
                        if ( element[0, 0] == 2**channel_dict['-X'] ) or ( element[0, 0] == 2**channel_dict['+Y'] ):
                            for element_phase in element:
                                for element_amp in amp_on_list:
                                    if (element_phase[1] - element_amp[2] <= overlap_amp_lna_mw) and (element_phase[1] - element_amp[2] > 0):
                                        element_amp[2] = element_phase[1] + overlap_amp_lna_mw
                                    elif (element_phase[1] - element_amp[2] >= -overlap_amp_lna_mw) and (element_phase[1] - element_amp[2] < 0):
                                        element_amp[2] = element_amp[2] + overlap_amp_lna_mw

                                    if (element_phase[1] - element_amp[1] <= overlap_amp_lna_mw) and (element_phase[1] - element_amp[1] > 0):
                                        element_amp[1] = element_amp[1] - overlap_amp_lna_mw
                                    elif (element_phase[1] - element_amp[1] >= -overlap_amp_lna_mw) and (element_phase[1] - element_amp[1] < 0):
                                        element_amp[1] = element_phase[1]                                
                        else:
                            pass

                return np.asarray(amp_on_list)

    def add_lna_protect_pulses(self, p_list):
        """
        A function that automatically add LNA_PROTECT pulses with corresponding delays
        specified by switch_delay and protect_delay
        """
        if test_flag != 'test':
            if auto_defense == 'False':
                pass
            elif auto_defense == 'True':
                lna_protect_list = []
                for index, element in enumerate(p_list):
                    if element[0] == 2**(channel_dict['MW']):
                        lna_protect_list.append( [2**(channel_dict['LNA_PROTECT']), element[1] - switch_delay, element[2] + protect_delay] )
                    else:
                        pass
                # additional checking and correcting lna_protect pulse in the case
                # when lna_protect pulses are diagonally shifted to mw pulses
                # in this case there can be nasty short overpal of lna_protect pulse 2
                # and mw pulse 1 and so on
                for element in lna_protect_list:
                    for element_mw in p_list:
                        if (element_mw[1] - element[1] <= overlap_amp_lna_mw) and (element_mw[1] - element[1] > 0):
                            element[1] = element[1] - overlap_amp_lna_mw
                        elif (element_mw[1] - element[1] >= -overlap_amp_lna_mw) and (element_mw[1] - element[1] < 0):
                            element[1] = element_mw[1]
                        elif (element_mw[1] - element[2]) <= overlap_amp_lna_mw and (element_mw[1] - element[2] > 0):
                            element[2] = element_mw[1]
                        elif (element_mw[1] - element[2]) >= -overlap_amp_lna_mw and (element_mw[1] - element[2] < 0):
                            # restriction on the pulse length in order to not jump into another restriction....
                            if element_mw[2] - element_mw[1] <= 30:
                                element[2] = element_mw[2]
                            else:
                                element[2] = element[2] + overlap_amp_lna_mw
                        # checking of start and end should be splitted into two checks
                        # in case of double start/end restriction
                        if (element_mw[2] - element[2] <= overlap_amp_lna_mw) and (element_mw[2] - element[2] > 0):
                            element[2] = element_mw[2]
                        elif (element_mw[2] - element[2] >= -overlap_amp_lna_mw) and (element_mw[2] - element[2] < 0):
                            element[2] = element[2] + overlap_amp_lna_mw
                        elif (element_mw[2] - element[1]) <= overlap_amp_lna_mw and (element_mw[2] - element[1] > 0):
                            # restriction on the pulse length in order to not jump into another restriction....
                            if element_mw[2] - element_mw[1] <= 30:
                                element[1] = element_mw[1]
                            else:
                                element[1] = element[1] - overlap_amp_lna_mw
                        elif (element_mw[2] - element[1]) >= -overlap_amp_lna_mw and (element_mw[2] - element[1] < 0):
                            element[1] = element_mw[2]

                # additional checking for phase and lna_protect pulses after
                # overlap correction
                if len(self.phase_array_length) > 0:
                    split_pulse_array = self.splitting_acc_to_channel( self.convertion_to_numpy( self.pulse_array ) )
                    # iterate over all pulses at different channels and taking phase pulses
                    for index, element in enumerate(split_pulse_array):
                        if ( element[0, 0] == 2**channel_dict['-X'] ) or ( element[0, 0] == 2**channel_dict['+Y'] ):
                            for element_phase in element:
                                for element_lna in lna_protect_list:
                                    if (element_phase[1] - element_lna[2] <= overlap_amp_lna_mw) and (element_phase[1] - element_lna[2] > 0):
                                        element_lna[2] = element_phase[1] + overlap_amp_lna_mw
                                    elif (element_phase[1] - element_lna[2] >= -overlap_amp_lna_mw) and (element_phase[1] - element_lna[2] < 0):
                                        element_lna[2] = element_lna[2] + overlap_amp_lna_mw
                                    # checking of start and end should be splitted into two checks
                                    # in case of double start/end restriction
                                    if (element_phase[1] - element_lna[1] <= overlap_amp_lna_mw) and (element_phase[1] - element_lna[1] > 0):
                                        element_lna[1] = element_lna[1] - overlap_amp_lna_mw
                                    elif (element_phase[1] - element_lna[1] >= -overlap_amp_lna_mw) and (element_phase[1] - element_lna[1] < 0):
                                        element_lna[1] = element_phase[1]                                
                        else:
                            pass

            return np.asarray(lna_protect_list)

        elif test_flag == 'test':
            if auto_defense == 'False':
                pass
            elif auto_defense == 'True':
                lna_protect_list = []
                for index, element in enumerate(p_list):
                    if element[0] == 2**(channel_dict['MW']):
                        lna_protect_list.append( [2**(channel_dict['LNA_PROTECT']), element[1] - switch_delay, element[2] + protect_delay] )
                    else:
                        pass

                for element in lna_protect_list:
                    for element_mw in p_list:
                        if (element_mw[1] - element[1] <= overlap_amp_lna_mw) and (element_mw[1] - element[1] > 0):
                            element[1] = element[1] - overlap_amp_lna_mw
                        elif (element_mw[1] - element[1] >= -overlap_amp_lna_mw) and (element_mw[1] - element[1] < 0):
                            element[1] = element_mw[1]
                        elif (element_mw[1] - element[2]) <= overlap_amp_lna_mw and (element_mw[1] - element[2] > 0):
                            element[2] = element_mw[1]
                        elif (element_mw[1] - element[2]) >= -overlap_amp_lna_mw and (element_mw[1] - element[2] < 0):
                            if element_mw[2] - element_mw[1] <= 30:
                                element[2] = element_mw[2]
                            else:
                                element[2] = element[2] + overlap_amp_lna_mw
                        # checking of start and end should be splitted into two checks
                        # in case of double start/end restriction
                        if (element_mw[2] - element[2] <= overlap_amp_lna_mw) and (element_mw[2] - element[2] > 0):
                            element[2] = element_mw[2]
                        elif (element_mw[2] - element[2] >= -overlap_amp_lna_mw) and (element_mw[2] - element[2] < 0):
                            element[2] = element[2] + overlap_amp_lna_mw
                        elif (element_mw[2] - element[1]) <= overlap_amp_lna_mw and (element_mw[2] - element[1] > 0):
                            if element_mw[2] - element_mw[1] <= 30:
                                element[1] = element_mw[1]
                            else:
                                element[1] = element[1] - overlap_amp_lna_mw
                        elif (element_mw[2] - element[1]) >= -overlap_amp_lna_mw and (element_mw[2] - element[1] < 0):
                            element[1] = element_mw[2]

                if len(self.phase_array_length) > 0:
                    split_pulse_array = self.splitting_acc_to_channel( self.convertion_to_numpy( self.pulse_array ) )
                    # iterate over all pulses at different channels and taking phase pulses
                    for index, element in enumerate(split_pulse_array):
                        if ( element[0, 0] == 2**channel_dict['-X'] ) or ( element[0, 0] == 2**channel_dict['+Y'] ):
                            for element_phase in element:
                                for element_lna in lna_protect_list:
                                    if (element_phase[1] - element_lna[2] <= overlap_amp_lna_mw) and (element_phase[1] - element_lna[2] > 0):
                                        element_lna[2] = element_phase[1] + overlap_amp_lna_mw
                                    elif (element_phase[1] - element_lna[2] >= -overlap_amp_lna_mw) and (element_phase[1] - element_lna[2] < 0):
                                        element_lna[2] = element_lna[2] + overlap_amp_lna_mw

                                    if (element_phase[1] - element_lna[1] <= overlap_amp_lna_mw) and (element_phase[1] - element_lna[1] > 0):
                                        element_lna[1] = element_lna[1] - overlap_amp_lna_mw
                                    elif (element_phase[1] - element_lna[1] >= -overlap_amp_lna_mw) and (element_phase[1] - element_lna[1] < 0):
                                        element_lna[1] = element_phase[1]                                
                        else:
                            pass

                return np.asarray(lna_protect_list)

    def check_problem_pulses_amp_lna(self, p_list):
        """
        A function for checking whether there is a two
        close to each other AMP_ON or LNA_PROTECT pulses (less than 12 ns)
        If so pulse array is splitted into the problematic part and correct part

        Returns both specified parts for further convertion in shich problematic part
        are joined using check_short_pulses() and joining_pulses()
        """
        if test_flag != 'test':
            if auto_defense == 'False':
                pass
            elif auto_defense == 'True':
                problem_list = []
                # memorize index of problem elements
                problem_index = []
                # numpy arrays don't support element deletion
                no_problem_list = deepcopy(p_list.tolist())

                # there STILL can be errors
                # now compare two consequnce pulses (end and start + 1)
                for index, element in enumerate(p_list[:-1]):

                    # minimal_distance_amp_lna is 12 ns now
                    if p_list[index + 1][1] - element[2] < minimal_distance_amp_lna:
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
                # the same conditions are used in preparing_to_bit_pulse()
                if len(problem_list) == 0:
                    return self.delete_duplicates(np.asarray(no_problem_list)), np.array([[0]])
                elif len(no_problem_list) == 0:
                    return np.array([[0]]), self.delete_duplicates(np.asarray(problem_list))
                else:
                    return self.delete_duplicates(np.asarray(no_problem_list)), self.delete_duplicates(np.asarray(problem_list))

        elif test_flag == 'test':
            if auto_defense == 'False':
                pass
            elif auto_defense == 'True':            
                problem_list = []
                problem_index = []
                # numpy arrays don't support element deletion
                no_problem_list = deepcopy(p_list.tolist())

                for index, element in enumerate(p_list[:-1]):
                    # minimal_distance_amp_lna is 12 ns now
                    if p_list[index + 1][1] - element[2] < (minimal_distance_amp_lna):
                        problem_list.append(element)
                        problem_list.append(p_list[index + 1])
                        # memorize indexes of the problem pulses
                        problem_index.append(index)
                        problem_index.append(index + 1)

                no_problem_list = np.delete( no_problem_list, list(dict.fromkeys(problem_index)), axis = 0 ).tolist()

                if len(problem_list) == 0:
                    return self.delete_duplicates(np.asarray(no_problem_list)), np.array([[0]])
                elif len(no_problem_list) == 0:
                    return np.array([[0]]), self.delete_duplicates(np.asarray(problem_list))
                else:
                    return self.delete_duplicates(np.asarray(no_problem_list)), self.delete_duplicates(np.asarray(problem_list))

    def convert_to_bit_pulse_amp_lna(self, p_list, channel):
        """
        A function to calculate in which time interval
        two or more different channels are on.
        All the pulses converted in an bit_array of 0 and 1, where
        1 corresponds to the time interval when the channel is on.
        The size of the bit_array is determined by the total length
        of the full pulse sequence.
        Finally, a bit_array is multiplied by a 2**ch in order to
        calculate CH instructions for SpinAPI.
        
        It is used to check (check_short_pulses()) whether there are two AMP_ON or LNA_PROTECT pulses
        with the distanse less than 12 ns between them
        If so they are combined in one pulse by joining_pulses()

        Generally, this function is close to convert_to_bit_pulse() and other convertion
        functions
        """
        if test_flag != 'test':
            if auto_defense == 'False':
                pass
            elif auto_defense == 'True':
                max_pulse = np.amax(p_list[:,2]) 
                bit_array = np.zeros(max_pulse, dtype = np.int64)
                i = 0
                while i < len(p_list):
                    # convert each pulse in an array of 0 and 1,
                    # 1 corresponds to the time interval, where the channel is on
                    translation_array = np.concatenate( (np.zeros(p_list[i, 1], dtype = np.int64), \
                            np.ones(p_list[i, 2] - p_list[i, 1], dtype = np.int64), \
                            np.zeros(max_pulse - p_list[i, 2], dtype = np.int64)), axis = None)

                    bit_array = bit_array | translation_array

                    i += 1

                bit_array = 2**(channel)*self.check_short_pulses(bit_array, channel)

                return bit_array

        elif test_flag == 'test':
            if auto_defense == 'False':
                pass
            elif auto_defense == 'True':            
                max_pulse = np.amax(p_list[:,2])
                bit_array = np.zeros(max_pulse, dtype = np.int64)
                i = 0
                while i < len(p_list):
                    # convert each pulse in an array of 0 and 1,
                    # 1 corresponds to the time interval, where the channel is on
                    translation_array = np.concatenate( (np.zeros(p_list[i, 1], dtype = np.int64), \
                            np.ones(p_list[i, 2] - p_list[i, 1], dtype = np.int64), \
                            np.zeros(max_pulse - p_list[i, 2], dtype = np.int64)), axis = None)

                    bit_array = bit_array | translation_array

                    i += 1

                bit_array = 2**(channel)*self.check_short_pulses(bit_array, channel)

                return bit_array

    def instruction_pulse_short_lna_amp(self, np_array):
        """
        Final convertion to the pulse blaster instruction pulses
        It splits the bit_array into sequence of bit_arrays for individual pulses
        after that converts them into instructions

        We can drop pulses with channel 0 for AMP_ON and LNA_PROTECT case

        Generally, this function is close to instruction_pulse() 
        """
        if test_flag != 'test':
            if auto_defense == 'False':
                pass
            elif auto_defense == 'True':
                final_pulse_array = []

                # Create an array that is 1 where a is 0, and pad each end with an extra 0.
                iszero = np.concatenate(([0], np_array, [0]))
                absdiff = np.abs(np.diff(iszero))

                # creating a mask to split bit array
                ranges = np.where(absdiff != 0)[0]
                # split using a mask
                pulse_array = np.split(np_array, ranges)
                pulse_info = np.concatenate(([0], ranges))

                for index, element in enumerate(pulse_info[:-1]):
                    # we can drop pulses with channel 0 for AMP_ON and LNA_PROTECT case
                    if pulse_array[index][0] != 0:
                        final_pulse_array.append( [pulse_array[index][0], pulse_info[index], pulse_info[index + 1]] )
                    else:
                        pass

                return final_pulse_array

        elif test_flag == 'test':
            if auto_defense == 'False':
                pass
            elif auto_defense == 'True':
                final_pulse_array = []

                # Create an array that is 1 where a is 0, and pad each end with an extra 0.
                iszero = np.concatenate(([0], np_array, [0]))
                absdiff = np.abs(np.diff(iszero))

                ranges = np.where(absdiff != 0)[0]
                pulse_array = np.split(np_array, ranges)
                pulse_info = np.concatenate(([0], ranges))

                for index, element in enumerate(pulse_info[:-1]):
                    if pulse_array[index][0] != 0:
                        final_pulse_array.append( [pulse_array[index][0], pulse_info[index], pulse_info[index + 1]] )
                    else:
                        pass

                return final_pulse_array

    def check_short_pulses(self, np_array, channel):
        """
        A function for checking whether there is two pulses with
        the distance between them shorther than 40 ns

        If there are such pulses on MW channel an error will be raised
        LNA_PROTECT and AMP_ON pulsess will be combined in one pulse

        """
        if test_flag != 'test':
            # checking where the pulses are
            one_indexes = np.argwhere(np_array == 1).flatten()
            difference = np.diff(one_indexes)

            if channel != channel_dict['LNA_PROTECT'] and channel != channel_dict['AMP_ON']:
                # (minimal_distance + 1) is 13 now
                if any(1 < element < (minimal_distance + 1) for element in difference) == False:
                    pass
                else:
                    general.message('There are two pulses with shorter than ' + str(minimal_distance*2) + ' ns distance between them')
                    sys.exit()
            else:
                if any(1 < element < (minimal_distance + 1) for element in difference) == False:
                    return np_array
                else:
                    final_array = self.joining_pulses(np_array)
                    return final_array

        if test_flag == 'test':
            # checking where the pulses are
            one_indexes = np.argwhere(np_array == 1).flatten()
            difference = np.diff(one_indexes)

            if channel != channel_dict['LNA_PROTECT'] and channel != channel_dict['AMP_ON']:
                if any(1 < element < (minimal_distance + 1) for element in difference) == False:
                    pass
                else:
                    assert(1 == 2), 'There are two pulses with shorter than ' + str(minimal_distance*2) + ' ns distance between them'
            else:
                if any(1 < element < (minimal_distance + 1) for element in difference) == False:
                    return np_array
                else:
                    final_array = self.joining_pulses(np_array)
                    return final_array
    
    def joining_pulses(self, np_array):
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
                    if counter < (minimal_distance + 1):
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

    def change_pulse_settings(self, parameter, delay):
        """
        A special function for parsing some parameter (i.e. start, length) value from the pulse
        and changing them according to specified delay

        It is used in phase cycling
        """
        if test_flag != 'test':
            temp = parameter.split(' ')
            if temp[1] in timebase_dict:
                flag = timebase_dict[temp[1]]
                par_st = int(int((temp[0]))*flag + delay)
                new_parameter = str( par_st ) + ' ns'

            return new_parameter

        elif test_flag == 'test':
            temp = parameter.split(' ')
            if temp[1] in timebase_dict:
                flag = timebase_dict[temp[1]]
                par_st = int(int((temp[0]))*flag + delay)
                new_parameter = str( par_st ) + ' ns'
            else:
                assert(1 == 2), 'Incorrect time dimension (ns, us, ms, s)'

            return new_parameter

def main():
    pass

if __name__ == "__main__":
    main()
