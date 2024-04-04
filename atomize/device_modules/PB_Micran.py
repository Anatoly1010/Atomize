#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import math
import fcntl
import array
import struct
import termios
from copy import deepcopy
import operator
from operator import iconcat
from functools import reduce
from itertools import groupby, chain
import numpy as np
import atomize.device_modules.config.config_utils as cutil
import atomize.general_modules.general_functions as general

class PB_Micran:
    def __init__(self):

        #### Inizialization
        # setting path to *.ini file
        self.path_current_directory = os.path.dirname(__file__)
        self.path_config_file = os.path.join(self.path_current_directory, 'config','PB_Micran_config.ini')

        # configuration data
        #config = cutil.read_conf_util(self.path_config_file)
        self.specific_parameters = cutil.read_specific_parameters(self.path_config_file)

        # Channel assignments
        self.ch1 = self.specific_parameters['ch1'] # TRIGGER
        self.ch2 = self.specific_parameters['ch2'] # AMP_ON
        self.ch3 = self.specific_parameters['ch3'] # LNA_PROTECT
        self.ch4 = self.specific_parameters['ch4'] # MW
        self.ch5 = self.specific_parameters['ch5'] # -X
        self.ch6 = self.specific_parameters['ch6'] # +Y
        self.ch7 = self.specific_parameters['ch7'] # TRIGGER_AWG
        self.ch8 = self.specific_parameters['ch8'] # AWG
        self.ch9 = self.specific_parameters['ch9'] # LASER
        self.ch10 = self.specific_parameters['ch10'] # SHAPER
        self.ch11 = self.specific_parameters['ch11'] # VIDEO_PROTECT
        self.ch12 = self.specific_parameters['ch12'] # LASER_2

        # AWG pulse will be substitued by a shifted RECT_AWG pulse and AMP_ON pulse
        # TRIGGER_AWG is used to trigger AWG card

        self.timebase_dict = {'s': 1000000000, 'ms': 1000000, 'us': 1000, 'ns': 1, }
        # -Y for Mikran bridge is simutaneously turned on -X; +Y
        # that is why there is no -Y channel instead we add both -X and +Y pulses
        self.channel_dict = {self.ch1: 1, self.ch2: 2, self.ch3: 3, self.ch4: 4, self.ch5: 5, self.ch6: 6, \
                        self.ch7: 7, self.ch8: 8, self.ch9: 9, self.ch10: 10, self.ch11: 11, self.ch12: 12,\
                        'CH12': 12, 'CH13': 13, 'CH14': 14, 'CH15': 15, 'CH16': 16, 'CH17': 17,\
                        'CH18': 18, 'CH19': 19, 'CH20': 20, 'CH21': 21, }

        # Limits and Ranges (depends on the exact model):
        self.clock = float(self.specific_parameters['clock'])
        self.timebase = int(float(self.specific_parameters['timebase'])) # in ns/clock; convertion of clock to ns
        self.repetition_rate = self.specific_parameters['default_rep_rate']
        self.auto_defense = self.specific_parameters['auto_defense']
        self.max_pulse_length = int(float(self.specific_parameters['max_pulse_length'])) # in ns
        self.min_pulse_length = int(float(self.specific_parameters['min_pulse_length'])) # in ns

        # minimal distance between two pulses of MW
        # pulse blaster restriction
        self.minimal_distance = int(float(self.specific_parameters['minimal_distance'])/self.timebase) # in clock

        # a constant that use to overcome short instruction for our diagonal amp_on and mw pulses
        # see also add_amp_on_pulses() function; looking for pulses with +-overlap_amp_lna_mw overlap
        self.overlap_amp_lna_mw = 0 # in clock

        self.minimal_distance_phase = 0 # in clock

        # minimal distance for joining AMP_ON and LNA_PROTECT pulses
        self.minimal_distance_amp_lna = 5 # in clock

        # Delays and restrictions
        self.constant_shift = int(400 / self.timebase) # in clock; shift of all sequence for not getting negative start times
        self.switch_delay = int(float(self.specific_parameters['switch_amp_delay'])/self.timebase) # in clock; delay for AMP_ON turning on; switch_delay BEFORE MW pulse
        self.switch_protect_delay = int(float(self.specific_parameters['switch_protect_delay'])/self.timebase) # in clock; delay for LNA_PROTECT turning on; switch_protect_delay BEFORE MW pulse
        self.amp_delay = int(float(self.specific_parameters['amp_delay'])/self.timebase) # in clock; delay for AMP_ON turning off; amp_delay AFTER MW pulse
        self.protect_delay = int(float(self.specific_parameters['protect_delay'])/self.timebase) # in clock; delay for LNA_PROTECT turning off; protect_delay AFTER MW pulse
        self.switch_phase_delay = int(float(self.specific_parameters['switch_phase_delay'])) # in ns; delay for FAST_PHASE turning on; switch_phase_delay BEFORE MW pulse
        self.phase_delay = int(float(self.specific_parameters['phase_delay'])) # in ns; delay for FAST_PHASE turning off; phase_delay AFTER MW pulse
        
        self.switch_shaper_delay = int(float(self.specific_parameters['switch_shaper_delay'])/self.timebase) # in clock; delay for SHAPER turning on; switch_shaper_delay BEFORE MW pulse
        self.shaper_delay = int(float(self.specific_parameters['shaper_delay'])/self.timebase) # in clock; delay for SHAPER turning off; shaper_delay AFTER MW pulse
        
        # currently RECT_AWG is coincide with AMP_ON pulse;
        self.rect_awg_switch_delay = int(float(self.specific_parameters['rect_awg_switch_delay'])/self.timebase) # in ns; delay for RECT_AWG turning on; rect_awg_switch_delay BEFORE MW pulse
        self.rect_awg_delay = int(float(self.specific_parameters['rect_awg_delay'])/self.timebase) # in clock; delay for RECT_AWG turning off; rect_awg_delay AFTER MW pulse
        self.protect_awg_delay = int(float(self.specific_parameters['protect_awg_delay'])/self.timebase) # in clock; delay for LNA_PROTECT turning off; because of shift a 
        # combination of rect_awg_delay and protect_awg_delay is used

        assert( (self.switch_protect_delay - self.switch_delay) * self.timebase > 80 ), f'(LNA - HPA) should be more than {80} ns'
        assert( (self.protect_delay - self.amp_delay) * self.timebase > 220 ), f'(LNA - HPA) should be more than {220} ns'
        assert( (self.protect_awg_delay - self.amp_delay) * self.timebase > 220 ), f'(LNA - HPA) should be more than {220} ns'
        self.internal_pause = '0 us'

        # interval that shift the first pulse in the sequence
        # start times of other pulses can be calculated from this time.
        # I. E. first pulse: 
        # pb.pulser_pulse(name ='P0', channel = 'MW', start = '100 ns', length = '20 ns')
        # second: pb.pulser_pulse(name ='P1', channel = 'MW', start = '330 ns', length = '30 ns', delta_start = '10 ns')
        # we will have first pulse at 50 ns (add_shft*2)
        # second at (330 - 100) + 50 = 280 ns
        # if there is no AMP_ON/LNA_PROTECT pulses
        self.add_shift = int(0) # in ns; *self.timebase

        self.state = 0
        self.dataio = array.array('L', [0, 0, 0])
        
        self.READ_BAR = 21
        self.WRITE_BAR = 22

        self.i_trigger_prev = 0
        self.i_amp_on_prev = 0
        self.i_lna_prev = 0
        self.i_mw_prev = 0
        self.i_x_prev = 0
        self.i_y_prev = 0
        self.i_trigger_awg_prev = 0
        self.i_awg_prev = 0
        self.i_laser_prev = 0
        self.i_shaper_prev = 0
        self.i_video_prev = 0
        self.i_laser_2_prev = 0

        # Test run parameters
        # These values are returned by the modules in the test run 
        if len(sys.argv) > 1:
            self.test_flag = sys.argv[1]
        else:
            self.test_flag = 'None'

        if self.test_flag != 'test':
            #pb_core_clock(self.clock)
            self.pulse_array = []
            self.phase_array_length = []
            self.pulse_name_array = []
            self.pulse_array_init = []
            self.rep_rate = (self.repetition_rate, )
            self.shift_count = 0
            self.rep_rate_count = 0
            self.increment_count = 0
            self.reset_count = 0
            self.current_phase_index = 0
            self.awg_pulses = 0
            self.phase_pulses = 0
            self.instr_from_file = 0
            self.iterator_of_updates = 0

        elif self.test_flag == 'test':
            open('instructions.out', 'w').close()
            self.test_rep_rate = '200 Hz'
            
            self.pulse_array = []
            self.phase_array_length = []
            self.pulse_name_array = []
            self.pulse_array_init = []
            self.rep_rate = (self.repetition_rate, )
            self.shift_count = 0
            self.rep_rate_count = 0
            self.increment_count = 0
            self.reset_count = 0
            self.current_phase_index = 0
            self.awg_pulses = 0
            self.phase_pulses = 0
            self.instr_from_file = 0

    # Module functions
    def pulser_name(self):
        answer = 'PB Micran'
        return answer

    def pulser_pulse(self, name = 'P0', channel = 'TRIGGER', start = '0 ns', length = '100 ns', \
        delta_start = '0 ns', length_increment = '0 ns', phase_list = []):
        """
        A function that added a new pulse at specified channel. The possible arguments:
        NAME, CHANNEL, START, LENGTH, DELTA_START, LENGTH_INCREMENT, PHASE_SEQUENCE
        """
        if self.test_flag != 'test':
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

        elif self.test_flag == 'test':

            pulse = {'name': name, 'channel': channel, 'start': start, \
                'length': length, 'delta_start' : delta_start, 'length_increment': length_increment, 'phase_list': phase_list}
            
            # phase_list's length
            if channel == 'MW':
                self.phase_array_length.append(len(list(phase_list)))
            elif channel == 'TRIGGER':
                assert( len(list(phase_list)) ) == 0, 'TRIGGER pulse should not have phase'

            # Checks
            # two equal names
            temp_name = str(name)
            set_from_list = set(self.pulse_name_array)          
            if temp_name in set_from_list:
                assert (1 == 2), 'Two pulses have the same name. Please, rename'

            self.pulse_name_array.append( pulse['name'] )

            temp_length = length.split(" ")
            if temp_length[1] in self.timebase_dict:
                coef = self.timebase_dict[temp_length[1]]
                p_length = coef*float(temp_length[0])
                assert(p_length % 4 == 0), 'Pulse length should be divisible by 4'
                assert(p_length >= self.min_pulse_length), 'Pulse is shorter than minimum available length (' + str(self.min_pulse_length) +' ns)'
                assert(p_length < self.max_pulse_length), 'Pulse is longer than maximum available length (' + str(self.max_pulse_length) +' ns)'
            else:
                assert( 1 == 2 ), 'Incorrect time dimension (s, ms, us, ns)'

            temp_start = start.split(" ")
            if temp_start[1] in self.timebase_dict:
                coef = self.timebase_dict[temp_start[1]]
                p_start = coef*float(temp_start[0])
                assert(p_start % 4 == 0), 'Pulse start should be divisible by 4'
                assert(p_start >= 0), 'Pulse start is a negative number'
            else:
                assert( 1 == 2 ), 'Incorrect time dimension (s, ms, us, ns)'

            temp_delta_start = delta_start.split(" ")
            if temp_delta_start[1] in self.timebase_dict:
                coef = self.timebase_dict[temp_delta_start[1]]
                p_delta_start = coef*float(temp_delta_start[0])
                assert(p_delta_start % 4 == 0), 'Pulse delta start should be divisible by 4'
                assert(p_delta_start >= 0), 'Pulse delta start is a negative number'
            else:
                assert( 1 == 2 ), 'Incorrect time dimension (s, ms, us, ns)'

            temp_length_increment = length_increment.split(" ")
            if temp_length_increment[1] in self.timebase_dict:
                coef = self.timebase_dict[temp_length_increment[1]]
                p_length_increment = coef*float(temp_length_increment[0])
                assert(p_length_increment % 4 == 0), 'Pulse length increment should be divisible by 4'
                assert (p_length_increment >= 0 and p_length_increment < self.max_pulse_length), \
                'Pulse length increment is longer than maximum available length or negative'
            else:
                assert( 1 == 2 ), 'Incorrect time dimension (s, ms, us, ns)'

            if channel in self.channel_dict:
                if self.auto_defense == 'False':
                    self.pulse_array.append( pulse )
                    # for saving the initial pulse_array without increments
                    # deepcopy helps to create a TRULY NEW array and not a link to the object
                    self.pulse_array_init = deepcopy(self.pulse_array)
                elif self.auto_defense == 'True':
                    if channel == 'AMP_ON' or channel == 'LNA_PROTECT' or channel == 'SHAPER' or channel == 'VIDEO_PROTECT':
                        assert( 1 == 2), 'In auto_defense mode AMP_ON, SHAPER, VIDEO_PROTECT, and LNA_PROTECT pulses are set automatically'
                    else:
                        self.pulse_array.append( pulse )
                        # for saving the initial pulse_array without increments
                        # deepcopy helps to create a TRULY NEW array and not a link to the object
                        self.pulse_array_init = deepcopy(self.pulse_array)
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

            while i < len( self.pulse_array ):
                if name == self.pulse_array[i]['name']:
                    self.pulse_array[i]['start'] = str(start)
                    self.shift_count = 1
                else:
                    pass

                i += 1

        elif self.test_flag == 'test':
            i = 0
            assert( name in self.pulse_name_array ), 'Pulse with the specified name is not defined'

            while i < len( self.pulse_array ):
                if name == self.pulse_array[i]['name']:

                    # checks
                    temp_start = start.split(" ")
                    if temp_start[1] in self.timebase_dict:
                        coef = self.timebase_dict[temp_start[1]]
                        p_start = coef*float(temp_start[0])
                        assert(p_start % 2 == 0), 'Pulse start should be divisible by 2'
                        assert(p_start >= 0), 'Pulse start is a negative number'
                    else:
                        assert( 1 == 2 ), 'Incorrect time dimension (s, ms, us, ns)'

                    self.pulse_array[i]['start'] = str(start)
                    self.shift_count = 1
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

            while i < len( self.pulse_array ):
                if name == self.pulse_array[i]['name']:
                    self.pulse_array[i]['delta_start'] = str(delta_start)
                    self.shift_count = 1
                else:
                    pass

                i += 1

        elif self.test_flag == 'test':
            i = 0
            assert( name in self.pulse_name_array ), 'Pulse with the specified name is not defined'

            while i < len( self.pulse_array ):
                if name == self.pulse_array[i]['name']:

                    # checks
                    temp_delta_start = delta_start.split(" ")
                    if temp_delta_start[1] in self.timebase_dict:
                        coef = self.timebase_dict[temp_delta_start[1]]
                        p_delta_start = coef*float(temp_delta_start[0])
                        assert(p_delta_start % 2 == 0), 'Pulse delta start should be divisible by 2'
                        assert(p_delta_start >= 0), 'Pulse delta start is a negative number'
                    else:
                        assert( 1 == 2 ), 'Incorrect time dimension (s, ms, us, ns)'

                    self.pulse_array[i]['delta_start'] = str(delta_start)
                    self.shift_count = 1
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

            while i < len( self.pulse_array ):
                if name == self.pulse_array[i]['name']:
                    self.pulse_array[i]['length_increment'] = str(length_increment)
                    self.increment_count = 1
                else:
                    pass

                i += 1

        elif self.test_flag == 'test':
            i = 0

            assert( name in self.pulse_name_array ), 'Pulse with the specified name is not defined'

            while i < len( self.pulse_array ):
                if name == self.pulse_array[i]['name']:
                    # checks
                    temp_length_increment = length_increment.split(" ")
                    if temp_length_increment[1] in self.timebase_dict:
                        coef = self.timebase_dict[temp_length_increment[1]]
                        p_length_increment = coef*float(temp_length_increment[0])
                        assert(p_length_increment % 2 == 0), 'Pulse length increment should be divisible by 2'
                        assert (p_length_increment >= 0 and p_length_increment < self.max_pulse_length), \
                        'Pulse length increment is longer than maximum available length or negative'
                    else:
                        assert( 1 == 2 ), 'Incorrect time dimension (s, ms, us, ns)'

                    self.pulse_array[i]['length_increment'] = str(length_increment)
                    self.increment_count = 1
                else:
                    pass

                i += 1

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
        if self.test_flag != 'test':
            # deleting old phase switch pulses from self.pulse_array
            # before adding new ones
            for i in range(self.phase_pulses):
                for index, element in enumerate(self.pulse_array):
                    if element['channel'] == '-X' or element['channel'] == '+Y':
                        del self.pulse_array[index]
                        break

            self.phase_pulses = 0
            # adding phase switch pulses
            for index, element in enumerate(self.pulse_array):
                if len(list(element['phase_list'])) != 0:
                    if element['phase_list'][self.current_phase_index] == '+x':
                        #pass
                        # 21-08-2021; Correction of non updating case for ['-x', '+x']
                        self.reset_count = 0

                    elif element['phase_list'][self.current_phase_index] == '-x':
                        name = element['name'] + '_ph_seq-x'
                        # taking into account delays of phase switching
                        start = self.change_pulse_settings(element['start'], -self.switch_phase_delay)
                        length = self.change_pulse_settings(element['length'], self.phase_delay + self.switch_phase_delay)

                        self.pulse_array.append({'name': name, 'channel': '-X', 'start': start, \
                            'length': length, 'delta_start' : '0 ns', 'length_increment': '0 ns', 'phase_list': []})

                        self.reset_count = 0
                        self.phase_pulses += 1

                    elif element['phase_list'][self.current_phase_index] == '+y':
                        name = element['name'] + '_ph_seq+y'
                        # taking into account delays of phase switching
                        start = self.change_pulse_settings(element['start'], -self.switch_phase_delay)
                        length = self.change_pulse_settings(element['length'], self.phase_delay + self.switch_phase_delay)

                        self.pulse_array.append({'name': name, 'channel': '+Y', 'start': start, \
                            'length': length, 'delta_start' : '0 ns', 'length_increment': '0 ns', 'phase_list': []})

                        self.reset_count = 0
                        self.phase_pulses += 1

                    elif element['phase_list'][self.current_phase_index] == '-y':
                        name = element['name'] + '_ph_seq-y'
                        # taking into account delays of phase switching
                        start = self.change_pulse_settings(element['start'], -self.switch_phase_delay)
                        length = self.change_pulse_settings(element['length'], self.phase_delay + self.switch_phase_delay)

                        # -Y for Mikran bridge is simutaneously turned on -X; +Y
                        # that is why there is no -Y channel
                        self.pulse_array.append({'name': name, 'channel': '-X', 'start': start, \
                            'length': length, 'delta_start' : '0 ns', 'length_increment': '0 ns', 'phase_list': []})
                        self.pulse_array.append({'name': name, 'channel': '+Y', 'start': start, \
                            'length': length, 'delta_start' : '0 ns', 'length_increment': '0 ns', 'phase_list': []})

                        self.reset_count = 0
                        self.phase_pulses += 2

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

            self.pulser_update()

        elif self.test_flag == 'test':

            # check that the length is equal (compare all elements in self.phase_array_length)
            gr = groupby(self.phase_array_length)
            if (next(gr, True) and not next(gr, False)) == False:
                assert(1 == 2), 'Phase sequence does not have equal length'

            for i in range(self.phase_pulses):
                for index, element in enumerate(self.pulse_array):
                    if element['channel'] == '-X' or element['channel'] == '+Y':
                        del self.pulse_array[index]
                        break

            self.phase_pulses = 0
            for index, element in enumerate(self.pulse_array):
                if len(list(element['phase_list'])) != 0:
                    if element['phase_list'][self.current_phase_index] == '+x':
                        #pass
                        # 21-08-2021; Correction of non updating case for ['-x', '+x']
                        self.reset_count = 0

                    elif element['phase_list'][self.current_phase_index] == '-x':
                        name = element['name'] + '_ph_seq-x'
                        # taking into account delays
                        start = self.change_pulse_settings(element['start'], -self.switch_phase_delay)
                        length = self.change_pulse_settings(element['length'], self.phase_delay + self.switch_phase_delay)

                        self.pulse_array.append({'name': name, 'channel': '-X', 'start': start, \
                            'length': length, 'delta_start' : '0 ns', 'length_increment': '0 ns', 'phase_list': []})

                        # check that we still have a next phase to switch
                        self.reset_count = 0
                        self.phase_pulses += 1

                    elif element['phase_list'][self.current_phase_index] == '+y':
                        name = element['name'] + '_ph_seq+y'
                        # taking into account delays
                        start = self.change_pulse_settings(element['start'], -self.switch_phase_delay)
                        length = self.change_pulse_settings(element['length'], self.phase_delay + self.switch_phase_delay)

                        self.pulse_array.append({'name': name, 'channel': '+Y', 'start': start, \
                            'length': length, 'delta_start' : '0 ns', 'length_increment': '0 ns', 'phase_list': []})

                        # check that we still have a next phase to switch
                        self.reset_count = 0
                        self.phase_pulses += 1

                    elif element['phase_list'][self.current_phase_index] == '-y':
                        name = element['name'] + '_ph_seq-y'
                        # taking into account delays
                        start = self.change_pulse_settings(element['start'], -self.switch_phase_delay)
                        length = self.change_pulse_settings(element['length'], self.phase_delay + self.switch_phase_delay)

                        # -Y for Mikran bridge is simutaneously turned on -X; +Y
                        # that is why there is no -Y channel
                        self.pulse_array.append({'name': name, 'channel': '-X', 'start': start, \
                            'length': length, 'delta_start' : '0 ns', 'length_increment': '0 ns', 'phase_list': []})
                        self.pulse_array.append({'name': name, 'channel': '+Y', 'start': start, \
                            'length': length, 'delta_start' : '0 ns', 'length_increment': '0 ns', 'phase_list': []})

                        # check that we still have a next phase to switch
                        self.reset_count = 0
                        self.phase_pulses += 2

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

            self.pulser_update()

    def pulser_update(self):
        """
        A function that write instructions to PB. 
        Repetition rate is taking into account by adding a last pulse with delay.
        Currently, all pulses are cycled using BRANCH.
        """
        if self.test_flag != 'test':
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
                if self.instr_from_file == 0:
                    to_spinapi = self.split_into_parts( self.pulse_array, rep_time )
                elif self.instr_from_file == 1:
                    raw_data = np.fromstring( self.raw_instructions[self.iterator_of_updates], dtype = int, sep = ',' )
                    to_spinapi = raw_data.reshape( ( int(len(raw_data)/3), 3 ) ).tolist()
                
                # Duty cycle checking
                amp_on_duration = 0
                shaper_duration = 0
                for element in to_spinapi:
                    if element[0] == self.channel_dict['AMP_ON']:
                        amp_on_duration = amp_on_duration + element[2] - element[1]
                    elif element[0] == self.channel_dict['SHAPER']:
                        shaper_duration = shaper_duration + element[2] - element[1]

                assert( (amp_on_duration * self.timebase) <= self.max_pulse_length ), f'The duration of AMP_ON cannot exceed {self.max_pulse_length} ns. Reduce pulse duration'
                assert( (shaper_duration * self.timebase) <= 1000 ), f'The duration of SHAPER cannot exceed {1000} ns. Reduce pulse duration'
                assert( 1/10**(-9)/(shaper_duration * self.timebase * float(self.rep_rate[0].split(" ")[0]) ) > 1100 ), \
                        'The duty cycle of SHAPER cannot exceed 1100. Reduce pulse duration'

                #general.message(to_spinapi)

                self.i_trigger = 0
                self.i_amp_on = 0
                self.i_lna = 0
                self.i_mw = 0
                self.i_x= 0
                self.i_y = 0
                self.i_trigger_awg = 0
                self.i_awg = 0
                self.i_laser = 0
                self.i_shaper = 0
                self.i_video = 0
                self.i_laser_2 = 0

                self.pulser_open()


                # Stop pulses
                self.device_write( 4, byte_to_write = 4, data_to_write = 56, type_of_systems = 2, shift = 0 )
                # rep rate in clock
                rep_time = rep_time // 4
                self.device_write( 3, byte_to_write = 4, data_to_write = rep_time, type_of_systems = 10 )


                self.pulse_write_stop(48, 0, 0, self.i_x , self.i_x_prev)
                self.pulse_write_stop(16, 0, 0, self.i_y , self.i_y_prev)

                for element in to_spinapi:
                    if element[0] == self.channel_dict['TRIGGER']:
                        self.i_trigger = self.i_trigger + 1
                        assert( self.i_trigger <= 1 ), 'Only 1 TRIGGER pulse allowed' 

                        self.pulse_write(320, element[1], element[2], self.i_trigger , self.i_trigger_prev)


                    elif element[0] == self.channel_dict['AMP_ON']:
                        self.i_amp_on = self.i_amp_on + 1
                        assert( self.i_amp_on <= 16 ), 'Only 16 AMP_ON pulses allowed'

                        self.pulse_write(176, element[1], element[2], self.i_amp_on , self.i_amp_on_prev)

                    elif element[0] == self.channel_dict['LNA_PROTECT']:
                        self.i_lna = self.i_lna + 1
                        assert( self.i_lna <= 16 ), 'Only 16 LNA_PROTECT pulses allowed'

                        self.pulse_write(80, element[1], element[2], self.i_lna , self.i_lna_prev)

                    elif element[0] == self.channel_dict['MW']:

                        self.i_mw = self.i_mw + 1
                        assert( self.i_mw <= 16 ), 'Only 16 MW pulses allowed'

                        self.pulse_write(112, element[1], element[2], self.i_mw , self.i_mw_prev)

                    elif element[0] == self.channel_dict['-X']:
                        self.i_x = self.i_x + 1
                        assert( self.i_x <= 16 ), 'Only 16 -X pulses allowed'

                        self.pulse_write(48, element[1], element[2], self.i_x , self.i_x_prev)

                    elif element[0] == self.channel_dict['+Y']:
                        self.i_y = self.i_y + 1
                        assert( self.i_y <= 16 ), 'Only 16 +Y pulses allowed'
                        self.pulse_write(16, element[1], element[2], self.i_y , self.i_y_prev)

                    elif element[0] == self.channel_dict['TRIGGER_AWG']:
                        self.i_trigger_awg = self.i_trigger_awg + 1
                        assert( self.i_trigger_awg <= 1 ), 'Only 1 TRIGGER AWG pulse allowed'

                        self.pulse_write(304, element[1], element[2], self.i_trigger_awg , self.i_trigger_awg_prev)


                    elif element[0] == self.channel_dict['AWG']:
                        self.i_awg = self.i_awg + 1
                        assert( self.i_awg <= 16 ), 'Only 16 AWG pulses allowed'

                        self.pulse_write(144, element[1], element[2], self.i_awg , self.i_awg_prev)


                    elif element[0] == self.channel_dict['LASER']:
                        self.i_laser = self.i_laser + 1
                        assert( self.i_laser <= 1 ), 'Only 1 LASER pulse allowed'
                        
                        self.pulse_write(272, element[1], element[2], self.i_laser , self.i_laser_prev)

                    elif element[0] == self.channel_dict['SHAPER']:
                        self.i_shaper = self.i_shaper + 1
                        assert( self.i_shaper <= 16 ), 'Only 16 SHAPER pulses allowed'

                        self.pulse_write(208, element[1], element[2], self.i_shaper , self.i_shaper_prev)

                    elif element[0] == self.channel_dict['VIDEO_PROTECT']:
                        self.i_video = self.i_video + 1
                        assert( self.i_video <= 16 ), 'Only 16 VIDEO_PROTECT pulses allowed'

                        self.pulse_write(240, element[1], element[2], self.i_video , self.i_video_prev)

                    elif element[0] == self.channel_dict['LASER_2']:
                        self.i_laser_2 = self.i_laser_2 + 1
                        assert( self.i_laser_2 <= 1 ), 'Only 1 LASER_2 pulses allowed'

                        self.pulse_write(288, element[1], element[2], self.i_laser_2 , self.i_laser_2_prev)


                # Set params
                self.device_write( 2, byte_to_write = 4, data_to_write = 1, type_of_systems = 2, shift = 0 )

                while True:
                    # Check register
                    self.device_read( 531, byte_to_read = 4 )
                    # split on registers
                    ans_reg = [self.dataio[2] >> i & 1 for i in range(9)]
                    x = int( ans_reg[1] )

                    if x == 1:
                        break

                # Start pulses
                self.device_write( 4, byte_to_write = 4, data_to_write = 58, type_of_systems = 2, shift = 0 )
                self.pulser_close()

                self.i_trigger_prev = self.i_trigger
                self.i_amp_on_prev = self.i_amp_on
                self.i_lna_prev = self.i_lna
                self.i_mw_prev = self.i_mw
                self.i_x_prev = self.i_x
                self.i_y_prev = self.i_y
                self.i_trigger_awg_prev = self.i_trigger_awg
                self.i_awg_prev = self.i_awg
                self.i_laser_prev = self.i_laser
                self.i_shaper_prev = self.i_shaper
                self.i_video_prev = self.i_video
                self.i_laser_2_prev = self.i_laser_2


                #[[      2      80     160]
                #[      2     210     290]
                #[      3      80     180]
                #[      3     210     310]
                #[      8     130     180]
                #[      8     260     310]
                #[     10     105     205]
                #[     10     235     335]
                #[     11      80     180]
                #[     11     210     310]
                #[      0     520 4999480]] 

                self.reset_count = 1
                self.shift_count = 0
                self.increment_count = 0
                self.rep_rate_count = 0

                self.iterator_of_updates += 1
            else:
                pass

        elif self.test_flag == 'test':
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

            assert( float(self.rep_rate[0].split(" ")[0]) < 12000 ), f'Repetition rate cannot exceed {12} kHz'

            if self.reset_count == 0 or self.shift_count == 1 or self.increment_count == 1:
                # using a special functions for convertion to instructions
                #to_spinapi = self.instruction_pulse( self.convert_to_bit_pulse( self.pulse_array ) )
                to_spinapi = self.split_into_parts( self.pulse_array, rep_time )
                
                # instructions from file:
                if self.instr_from_file == 1:
                    with open("instructions.out", "a") as f:
                        np.savetxt(f, [reduce(iconcat, to_spinapi, [])], delimiter = ',', fmt = '%u') 
                
                    f.close()

                amp_on_duration = 0
                shaper_duration = 0
                for element in to_spinapi:
                    if element[0] == self.channel_dict['AMP_ON']:
                        amp_on_duration = amp_on_duration + element[2] - element[1]
                    elif element[0] == self.channel_dict['SHAPER']:
                        shaper_duration = shaper_duration + element[2] - element[1]

                assert( (amp_on_duration * self.timebase) <= self.max_pulse_length ), f'The duration of AMP_ON cannot exceed {self.max_pulse_length} ns. Reduce pulse duration'
                assert( (shaper_duration * self.timebase) <= 1000 ), f'The duration of SHAPER cannot exceed {1000} ns. Reduce pulse duration'
                assert( 1/10**(-9)/(shaper_duration * self.timebase * float(self.rep_rate[0].split(" ")[0]) ) > 1100 ), \
                        'The duty cycle of SHAPER cannot exceed 1100. Reduce pulse duration'

                self.i_trigger = 0
                self.i_amp_on = 0
                self.i_lna = 0
                self.i_mw = 0
                self.i_x= 0
                self.i_y = 0
                self.i_trigger_awg = 0
                self.i_awg = 0
                self.i_laser = 0
                self.i_shaper = 0
                self.i_video = 0
                self.i_laser_2 = 0
                
                for element in to_spinapi:
                    if element[0] == self.channel_dict['TRIGGER']:
                        self.i_trigger = self.i_trigger + 1
                        assert( self.i_trigger <= 1 ), 'Only 1 TRIGGER pulse allowed' 

                        #self.pulse_write(320, element[1], element[2], self.i_trigger , self.i_trigger_prev)


                    elif element[0] == self.channel_dict['AMP_ON']:
                        self.i_amp_on = self.i_amp_on + 1
                        assert( self.i_amp_on <= 16 ), 'Only 16 AMP_ON pulses allowed'

                        #self.pulse_write(176, element[1], element[2], self.i_amp_on , self.i_amp_on_prev)

                    elif element[0] == self.channel_dict['LNA_PROTECT']:
                        self.i_lna = self.i_lna + 1
                        assert( self.i_lna <= 16 ), 'Only 16 LNA_PROTECT pulses allowed'

                        #self.pulse_write(80, element[1], element[2], self.i_lna , self.i_lna_prev)

                    elif element[0] == self.channel_dict['MW']:

                        self.i_mw = self.i_mw + 1
                        assert( self.i_mw <= 16 ), 'Only 16 MW pulses allowed'

                        #self.pulse_write(112, element[1], element[2], self.i_mw , self.i_mw_prev)

                    elif element[0] == self.channel_dict['-X']:
                        self.i_x = self.i_x + 1
                        assert( self.i_x <= 16 ), 'Only 16 -X pulses allowed'

                        #self.pulse_write(48, element[1], element[2], self.i_x , self.i_x_prev)

                    elif element[0] == self.channel_dict['+Y']:
                        self.i_y = self.i_y + 1
                        assert( self.i_y <= 16 ), 'Only 16 +Y pulses allowed'
                        #self.pulse_write(16, element[1], element[2], self.i_y , self.i_y_prev)

                    elif element[0] == self.channel_dict['TRIGGER_AWG']:
                        self.i_trigger_awg = self.i_trigger_awg + 1
                        assert( self.i_trigger_awg <= 1 ), 'Only 1 TRIGGER AWG pulse allowed'

                        #self.pulse_write(304, element[1], element[2], self.i_trigger_awg , self.i_trigger_awg_prev)


                    elif element[0] == self.channel_dict['AWG']:
                        self.i_awg = self.i_awg + 1
                        assert( self.i_awg <= 16 ), 'Only 16 AWG pulses allowed'

                        #self.pulse_write(144, element[1], element[2], self.i_awg , self.i_awg_prev)


                    elif element[0] == self.channel_dict['LASER']:
                        self.i_laser = self.i_laser + 1
                        assert( self.i_laser <= 1 ), 'Only 1 LASER pulse allowed'
                        
                        #self.pulse_write(272, element[1], element[2], self.i_laser , self.i_laser_prev)

                    elif element[0] == self.channel_dict['SHAPER']:
                        self.i_shaper = self.i_shaper + 1
                        assert( self.i_shaper <= 16 ), 'Only 16 SHAPER pulses allowed'

                        #self.pulse_write(208, element[1], element[2], self.i_shaper , self.i_shaper_prev)

                    elif element[0] == self.channel_dict['VIDEO_PROTECT']:
                        self.i_video = self.i_video + 1
                        assert( self.i_video <= 16 ), 'Only 16 VIDEO_PROTECT pulses allowed'

                        #self.pulse_write(240, element[1], element[2], self.i_video , self.i_video_prev)

                    elif element[0] == self.channel_dict['LASER_2']:
                        self.i_laser_2 = self.i_laser_2 + 1
                        assert( self.i_laser_2 <= 1 ), 'Only 1 LASER_2 pulses allowed'

                        #self.pulse_write(288, element[1], element[2], self.i_laser_2 , self.i_laser_2_prev)

                self.i_trigger_prev = self.i_trigger
                self.i_amp_on_prev = self.i_amp_on
                self.i_lna_prev = self.i_lna
                self.i_mw_prev = self.i_mw
                self.i_x_prev = self.i_x
                self.i_y_prev = self.i_y
                self.i_trigger_awg_prev = self.i_trigger_awg
                self.i_awg_prev = self.i_awg
                self.i_laser_prev = self.i_laser
                self.i_shaper_prev = self.i_shaper
                self.i_video_prev = self.i_video
                self.i_laser_2_prev = self.i_laser_2

                self.reset_count = 1
                self.shift_count = 0
                self.increment_count = 0
                self.rep_rate_count = 0

            else:
                pass

    def pulser_repetition_rate(self, *r_rate):
        """
        A function to get or set repetition rate.
        Repetition rate specifies the delay of the last
        SpinAPI instructions
        """
        if self.test_flag != 'test':
            if  len(r_rate) == 1:
                self.rep_rate = r_rate
                self.rep_rate_count = 1
            elif len(r_rate) == 0:
                return self.rep_rate[0]

        elif self.test_flag == 'test':
            if  len(r_rate) == 1:
                self.rep_rate = r_rate
                self.rep_rate_count = 1
            elif len(r_rate) == 0:
                return self.rep_rate[0]

    def pulser_shift(self, *pulses):
        """
        A function to shift the start of the pulses.
        The function directly affects the pulse_array.
        """
        if self.test_flag != 'test':
            if len(pulses) == 0:
                i = 0
                while i < len( self.pulse_array ):
                    if int( self.pulse_array[i]['delta_start'][:-3] ) == 0:
                        pass
                    else:
                        # convertion to ns
                        temp = self.pulse_array[i]['delta_start'].split(' ')
                        if temp[1] in self.timebase_dict:
                            flag = self.timebase_dict[temp[1]]
                            d_start = int((temp[0]))*flag
                        else:
                            pass

                        temp2 = self.pulse_array[i]['start'].split(' ')
                        if temp2[1] in self.timebase_dict:
                            flag2 = self.timebase_dict[temp2[1]]
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
                            if temp[1] in self.timebase_dict:
                                flag = self.timebase_dict[temp[1]]
                                d_start = int((temp[0]))*flag
                            else:
                                pass

                            temp2 = self.pulse_array[pulse_index]['start'].split(' ')
                            if temp2[1] in self.timebase_dict:
                                flag2 = self.timebase_dict[temp2[1]]
                                st = int((temp2[0]))*flag2
                            else:
                                pass
                                    
                            self.pulse_array[pulse_index]['start'] = str( st + d_start ) + ' ns'

                        self.shift_count = 1
                        self.current_phase_index = 0

        elif self.test_flag == 'test':
            if len(pulses) == 0:
                i = 0
                while i < len( self.pulse_array ):
                    if int( self.pulse_array[i]['delta_start'][:-3] ) == 0:
                        pass
                    else:
                        # convertion to ns
                        temp = self.pulse_array[i]['delta_start'].split(' ')
                        if temp[1] in self.timebase_dict:
                            flag = self.timebase_dict[temp[1]]
                            d_start = int((temp[0]))*flag
                        else:
                            assert(1 == 2), "Incorrect time dimension (ns, us, ms, s)"

                        temp2 = self.pulse_array[i]['start'].split(' ')
                        if temp2[1] in self.timebase_dict:
                            flag2 = self.timebase_dict[temp2[1]]
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
                            if temp[1] in self.timebase_dict:
                                flag = self.timebase_dict[temp[1]]
                                d_start = int((temp[0]))*flag
                            else:
                                assert(1 == 2), "Incorrect time dimension (ns, us, ms, s)"

                            temp2 = self.pulse_array[pulse_index]['start'].split(' ')
                            if temp2[1] in self.timebase_dict:
                                flag2 = self.timebase_dict[temp2[1]]
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
        if self.test_flag != 'test':
            if len(pulses) == 0:
                i = 0
                while i < len( self.pulse_array ):
                    if int( self.pulse_array[i]['length_increment'][:-3] ) == 0:
                        pass
                    else:
                        # convertion to ns
                        temp = self.pulse_array[i]['length_increment'].split(' ')
                        if temp[1] in self.timebase_dict:
                            flag = self.timebase_dict[temp[1]]
                            d_length = int(float(temp[0]))*flag
                        else:
                            pass

                        temp2 = self.pulse_array[i]['length'].split(' ')
                        if temp2[1] in self.timebase_dict:
                            flag2 = self.timebase_dict[temp2[1]]
                            leng = int(float(temp2[0]))*flag2
                        else:
                            pass

                        self.pulse_array[i]['length'] = str( leng + d_length ) + ' ns'
 
                    i += 1

                self.increment_count = 1
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
                            if temp[1] in self.timebase_dict:
                                flag = self.timebase_dict[temp[1]]
                                d_length = int(float(temp[0]))*flag
                            else:
                                pass

                            temp2 = self.pulse_array[pulse_index]['length'].split(' ')
                            if temp2[1] in self.timebase_dict:
                                flag2 = self.timebase_dict[temp2[1]]
                                leng = int(float(temp2[0]))*flag2
                            else:
                                pass
                            
                            self.pulse_array[pulse_index]['length'] = str( leng + d_length ) + ' ns'

                        self.increment_count = 1
                        self.current_phase_index = 0

        elif self.test_flag == 'test':
            if len(pulses) == 0:
                i = 0
                while i < len( self.pulse_array ):
                    if int( self.pulse_array[i]['length_increment'][:-3] ) == 0:
                        pass
                    else:
                        # convertion to ns
                        temp = self.pulse_array[i]['length_increment'].split(' ')
                        if temp[1] in self.timebase_dict:
                            flag = self.timebase_dict[temp[1]]
                            d_length = int(float(temp[0]))*flag
                        else:
                            assert(1 == 2), "Incorrect time dimension (ns, us, ms, s)"

                        temp2 = self.pulse_array[i]['length'].split(' ')
                        if temp2[1] in self.timebase_dict:
                            flag2 = self.timebase_dict[temp2[1]]
                            leng = int(float(temp2[0]))*flag2
                        else:
                            assert(1 == 2), "Incorrect time dimension (ns, us, ms, s)"
                        
                        if ( leng + d_length ) <= self.max_pulse_length:
                            self.pulse_array[i]['length'] = str( leng + d_length ) + ' ns'
                        else:
                            assert(1 == 2), 'Exceeded maximum pulse length (1900 ns) when increment the pulse'

                    i += 1

                self.increment_count = 1
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
                            if temp[1] in self.timebase_dict:
                                flag = self.timebase_dict[temp[1]]
                                d_length = int(float(temp[0]))*flag
                            else:
                                assert(1 == 2), "Incorrect time dimension (ns, us, ms, s)"

                            temp2 = self.pulse_array[pulse_index]['length'].split(' ')
                            if temp2[1] in self.timebase_dict:
                                flag2 = self.timebase_dict[temp2[1]]
                                leng = int(float(temp2[0]))*flag2
                            else:
                                assert(1 == 2), "Incorrect time dimension (ns, us, ms, s)"
                                    
                            if ( leng + d_length ) <= self.max_pulse_length:
                                self.pulse_array[pulse_index]['length'] = str( leng + d_length ) + ' ns'
                            else:
                                assert(1 == 2), 'Exceeded maximum pulse length (1900 ns) when increment the pulse'

                        self.increment_count = 1
                        self.current_phase_index = 0

                    else:
                        assert(1 == 2), "There is no pulse with the specified name"

    #UNDOCUMENTED
    def pulser_phase_reset(self):
        """
        Reset phase index to zero in order to start phase cycling once again
        """
        self.current_phase_index = 0

    def pulser_reset(self, interal_cycle = 'False'):
        """
        Reset all pulses to the initial state it was in at the start of the experiment.
        It includes the complete functionality of pulser_pulse_reset(), but also immediately
        updates the pulser as it is done by calling pulser_update().
        """
        if self.test_flag != 'test':
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
            if interal_cycle == 'False':
                self.iterator_of_updates = 0
            elif interal_cycle == 'True':
                pass

            if self.instr_from_file == 0:
                to_spinapi = self.split_into_parts( self.pulse_array, rep_time )
            elif self.instr_from_file == 1:
                #self.iterator_of_updates = 0
                raw_data = np.fromstring( self.raw_instructions[self.iterator_of_updates], dtype = int, sep = ',' )
                to_spinapi = raw_data.reshape( (int(len(raw_data)/3), 3 ) ).tolist()

            # Duty cycle checking
            amp_on_duration = 0
            shaper_duration = 0
            for element in to_spinapi:
                if element[0] == self.channel_dict['AMP_ON']:
                    amp_on_duration = amp_on_duration + element[2] - element[1]
                elif element[0] == self.channel_dict['SHAPER']:
                    shaper_duration = shaper_duration + element[2] - element[1]

            assert( (amp_on_duration * self.timebase) <= self.max_pulse_length ), f'The duration of AMP_ON cannot exceed {self.max_pulse_length} ns. Reduce pulse duration'
            assert( (shaper_duration * self.timebase) <= 1000 ), f'The duration of SHAPER cannot exceed {1000} ns. Reduce pulse duration'
            assert( 1/10**(-9)/(shaper_duration * self.timebase * float(self.rep_rate[0].split(" ")[0]) ) > 1100 ), \
                    'The duty cycle of SHAPER cannot exceed 1100. Reduce pulse duration'

            self.i_trigger = 0
            self.i_amp_on = 0
            self.i_lna = 0
            self.i_mw = 0
            self.i_x= 0
            self.i_y = 0
            self.i_trigger_awg = 0
            self.i_awg = 0
            self.i_laser = 0
            self.i_shaper = 0
            self.i_video = 0
            self.i_laser_2 = 0

            self.pulser_open()
            
            # Stop pulses
            self.device_write( 4, byte_to_write = 4, data_to_write = 56, type_of_systems = 2, shift = 0 )
            # rep rate in clock
            rep_time = rep_time // 4
            self.device_write( 3, byte_to_write = 4, data_to_write = rep_time, type_of_systems = 10 )

            self.pulse_write_stop(48, 0, 0, self.i_x , self.i_x_prev)
            self.pulse_write_stop(16, 0, 0, self.i_y , self.i_y_prev)

            for element in to_spinapi:
                if element[0] == self.channel_dict['TRIGGER']:
                    self.i_trigger = self.i_trigger + 1
                    assert( self.i_trigger <= 1 ), 'Only 1 TRIGGER pulse allowed' 

                    self.pulse_write(320, element[1], element[2], self.i_trigger , self.i_trigger_prev)


                elif element[0] == self.channel_dict['AMP_ON']:
                    self.i_amp_on = self.i_amp_on + 1
                    assert( self.i_amp_on <= 16 ), 'Only 16 AMP_ON pulses allowed'

                    self.pulse_write(176, element[1], element[2], self.i_amp_on , self.i_amp_on_prev)

                elif element[0] == self.channel_dict['LNA_PROTECT']:
                    self.i_lna = self.i_lna + 1
                    assert( self.i_lna <= 16 ), 'Only 16 LNA_PROTECT pulses allowed'

                    self.pulse_write(80, element[1], element[2], self.i_lna , self.i_lna_prev)

                elif element[0] == self.channel_dict['MW']:

                    self.i_mw = self.i_mw + 1
                    assert( self.i_mw <= 16 ), 'Only 16 MW pulses allowed'

                    self.pulse_write(112, element[1], element[2], self.i_mw , self.i_mw_prev)

                elif element[0] == self.channel_dict['-X']:
                    self.i_x = self.i_x + 1
                    assert( self.i_x <= 16 ), 'Only 16 -X pulses allowed'

                    self.pulse_write(48, element[1], element[2], self.i_x , self.i_x_prev)

                elif element[0] == self.channel_dict['+Y']:
                    self.i_y = self.i_y + 1
                    assert( self.i_y <= 16 ), 'Only 16 +Y pulses allowed'
                    self.pulse_write(16, element[1], element[2], self.i_y , self.i_y_prev)

                elif element[0] == self.channel_dict['TRIGGER_AWG']:
                    self.i_trigger_awg = self.i_trigger_awg + 1
                    assert( self.i_trigger_awg <= 1 ), 'Only 1 TRIGGER AWG pulse allowed'

                    self.pulse_write(304, element[1], element[2], self.i_trigger_awg , self.i_trigger_awg_prev)


                elif element[0] == self.channel_dict['AWG']:
                    self.i_awg = self.i_awg + 1
                    assert( self.i_awg <= 16 ), 'Only 16 AWG pulses allowed'

                    self.pulse_write(144, element[1], element[2], self.i_awg , self.i_awg_prev)


                elif element[0] == self.channel_dict['LASER']:
                    self.i_laser = self.i_laser + 1
                    assert( self.i_laser <= 1 ), 'Only 1 LASER pulse allowed'
                    
                    self.pulse_write(272, element[1], element[2], self.i_laser , self.i_laser_prev)

                elif element[0] == self.channel_dict['SHAPER']:
                    self.i_shaper = self.i_shaper + 1
                    assert( self.i_shaper <= 16 ), 'Only 16 SHAPER pulses allowed'

                    self.pulse_write(208, element[1], element[2], self.i_shaper , self.i_shaper_prev)

                elif element[0] == self.channel_dict['VIDEO_PROTECT']:
                    self.i_video = self.i_video + 1
                    assert( self.i_video <= 16 ), 'Only 16 VIDEO_PROTECT pulses allowed'

                    self.pulse_write(240, element[1], element[2], self.i_video , self.i_video_prev)

                elif element[0] == self.channel_dict['LASER_2']:
                    self.i_laser_2 = self.i_laser_2 + 1
                    assert( self.i_laser_2 <= 1 ), 'Only 1 LASER_2 pulses allowed'

                    self.pulse_write(288, element[1], element[2], self.i_laser_2 , self.i_laser_2_prev)


            # Set params
            self.device_write( 2, byte_to_write = 4, data_to_write = 1, type_of_systems = 2, shift = 0 )

            while True:
                # Check register
                self.device_read( 531, byte_to_read = 4 )
                # split on registers
                ans_reg = [self.dataio[2] >> i & 1 for i in range(9)]
                x = int( ans_reg[1] )

                if x == 1:
                    break

            # Start pulses
            self.device_write( 4, byte_to_write = 4, data_to_write = 58, type_of_systems = 2, shift = 0 )
            self.pulser_close()

            self.i_trigger_prev = self.i_trigger
            self.i_amp_on_prev = self.i_amp_on
            self.i_lna_prev = self.i_lna
            self.i_mw_prev = self.i_mw
            self.i_x_prev = self.i_x
            self.i_y_prev = self.i_y
            self.i_trigger_awg_prev = self.i_trigger_awg
            self.i_awg_prev = self.i_awg
            self.i_laser_prev = self.i_laser
            self.i_shaper_prev = self.i_shaper
            self.i_video_prev = self.i_video
            self.i_laser_2_prev = self.i_laser_2
            
            self.reset_count = 1
            self.increment_count = 0
            self.shift_count = 0
            self.current_phase_index = 0

            self.iterator_of_updates += 1

        elif self.test_flag == 'test':
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

            # instructions from file:
            if self.instr_from_file == 1:
                with open("instructions.out", "a") as f:
                    np.savetxt(f, [reduce(iconcat, to_spinapi, [])], delimiter = ',', fmt = '%u') 
            
                f.close()

            amp_on_duration = 0
            shaper_duration = 0
            for element in to_spinapi:
                if element[0] == self.channel_dict['AMP_ON']:
                    amp_on_duration = amp_on_duration + element[2] - element[1]
                elif element[0] == self.channel_dict['SHAPER']:
                    shaper_duration = shaper_duration + element[2] - element[1]

            assert( (amp_on_duration * self.timebase) <= self.max_pulse_length ), f'The duration of AMP_ON cannot exceed {self.max_pulse_length} ns. Reduce pulse duration'
            assert( (shaper_duration * self.timebase) <= 1000 ), f'The duration of SHAPER cannot exceed {1000} ns. Reduce pulse duration'
            assert( 1/10**(-9)/(shaper_duration * self.timebase * float(self.rep_rate[0].split(" ")[0]) ) > 1100 ), \
                    'The duty cycle of SHAPER cannot exceed 1100. Reduce pulse duration'

            self.i_trigger = 0
            self.i_amp_on = 0
            self.i_lna = 0
            self.i_mw = 0
            self.i_x= 0
            self.i_y = 0
            self.i_trigger_awg = 0
            self.i_awg = 0
            self.i_laser = 0
            self.i_shaper = 0
            self.i_video = 0
            self.i_laser_2 = 0
    
            for element in to_spinapi:
                if element[0] == self.channel_dict['TRIGGER']:
                    self.i_trigger = self.i_trigger + 1
                    assert( self.i_trigger <= 1 ), 'Only 1 TRIGGER pulse allowed' 

                    #self.pulse_write(320, element[1], element[2], self.i_trigger , self.i_trigger_prev)


                elif element[0] == self.channel_dict['AMP_ON']:
                    self.i_amp_on = self.i_amp_on + 1
                    assert( self.i_amp_on <= 16 ), 'Only 16 AMP_ON pulses allowed'

                    #self.pulse_write(176, element[1], element[2], self.i_amp_on , self.i_amp_on_prev)

                elif element[0] == self.channel_dict['LNA_PROTECT']:
                    self.i_lna = self.i_lna + 1
                    assert( self.i_lna <= 16 ), 'Only 16 LNA_PROTECT pulses allowed'

                    #self.pulse_write(80, element[1], element[2], self.i_lna , self.i_lna_prev)

                elif element[0] == self.channel_dict['MW']:

                    self.i_mw = self.i_mw + 1
                    assert( self.i_mw <= 16 ), 'Only 16 MW pulses allowed'

                    #self.pulse_write(112, element[1], element[2], self.i_mw , self.i_mw_prev)

                elif element[0] == self.channel_dict['-X']:
                    self.i_x = self.i_x + 1
                    assert( self.i_x <= 16 ), 'Only 16 -X pulses allowed'

                    #self.pulse_write(48, element[1], element[2], self.i_x , self.i_x_prev)

                elif element[0] == self.channel_dict['+Y']:
                    self.i_y = self.i_y + 1
                    assert( self.i_y <= 16 ), 'Only 16 +Y pulses allowed'
                    self.pulse_write(16, element[1], element[2], self.i_y , self.i_y_prev)

                elif element[0] == self.channel_dict['TRIGGER_AWG']:
                    self.i_trigger_awg = self.i_trigger_awg + 1
                    assert( self.i_trigger_awg <= 1 ), 'Only 1 TRIGGER AWG pulse allowed'

                    #self.pulse_write(304, element[1], element[2], self.i_trigger_awg , self.i_trigger_awg_prev)


                elif element[0] == self.channel_dict['AWG']:
                    self.i_awg = self.i_awg + 1
                    assert( self.i_awg <= 16 ), 'Only 16 AWG pulses allowed'

                    #self.pulse_write(144, element[1], element[2], self.i_awg , self.i_awg_prev)


                elif element[0] == self.channel_dict['LASER']:
                    self.i_laser = self.i_laser + 1
                    assert( self.i_laser <= 1 ), 'Only 1 LASER pulse allowed'
                    
                    #self.pulse_write(272, element[1], element[2], self.i_laser , self.i_laser_prev)

                elif element[0] == self.channel_dict['SHAPER']:
                    self.i_shaper = self.i_shaper + 1
                    assert( self.i_shaper <= 16 ), 'Only 16 SHAPER pulses allowed'

                    #self.pulse_write(208, element[1], element[2], self.i_shaper , self.i_shaper_prev)

                elif element[0] == self.channel_dict['VIDEO_PROTECT']:
                    self.i_video = self.i_video + 1
                    assert( self.i_video <= 16 ), 'Only 16 VIDEO_PROTECT pulses allowed'

                    #self.pulse_write(240, element[1], element[2], self.i_video , self.i_video_prev)

                elif element[0] == self.channel_dict['LASER_2']:
                    self.i_laser_2 = self.i_laser_2 + 1
                    assert( self.i_laser_2 <= 1 ), 'Only 1 LASER_2 pulses allowed'

                    #self.pulse_write(288, element[1], element[2], self.i_laser_2 , self.i_laser_2_prev)

                #self.pulse_write(48, 0, 0, self.i_x , self.i_x_prev)
                #self.pulse_write(16, 0, 0, self.i_y , self.i_y_prev)

            self.i_trigger_prev = self.i_trigger
            self.i_amp_on_prev = self.i_amp_on
            self.i_lna_prev = self.i_lna
            self.i_mw_prev = self.i_mw
            self.i_x_prev = self.i_x
            self.i_y_prev = self.i_y
            self.i_trigger_awg_prev = self.i_trigger_awg
            self.i_awg_prev = self.i_awg
            self.i_laser_prev = self.i_laser
            self.i_shaper_prev = self.i_shaper
            self.i_video_prev = self.i_video
            self.i_laser_2_prev = self.i_laser_2

            self.reset_count = 1
            self.increment_count = 0
            self.shift_count = 0
            self.current_phase_index = 0

    def pulser_pulse_reset(self, *pulses, interal_cycle = 'False'):
        """
        Reset all pulses to the initial state it was in at the start of the experiment.
        It does not update the pulser, if you want to reset all pulses and and also update 
        the pulser use the function pulser_reset() instead.
        """
        if self.test_flag != 'test':

            self.pulser_stop()
            
            if len(pulses) == 0:
                self.pulse_array = deepcopy(self.pulse_array_init)
                self.reset_count = 0
                self.increment_count = 0
                self.shift_count = 0
                self.current_phase_index = 0
                if interal_cycle == 'False':
                    self.iterator_of_updates = 0
                elif interal_cycle == 'True':
                    pass

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
                        self.current_phase_index = 0

                        #self.iterator_of_updates = 0

        elif self.test_flag == 'test':

            self.pulser_stop()

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
                        self.current_phase_index = 0

    def pulser_full_stop(self):
        """
        A function to stop pulse sequence
        """
        if self.test_flag != 'test':
            self.pulser_open()
            self.device_write( 4, byte_to_write = 4, data_to_write = 56, type_of_systems = 2, shift = 0 )

            self.pulse_write_full_stop(320, 0, 0, 1)
            self.pulse_write_full_stop(176, 0, 0, 16)
            self.pulse_write_full_stop(80, 0, 0, 16)
            self.pulse_write_full_stop(112, 0, 0, 16)
            self.pulse_write_full_stop(48, 0, 0, 16)
            self.pulse_write_full_stop(16, 0, 0, 16)
            self.pulse_write_full_stop(304, 0, 0, 1)
            self.pulse_write_full_stop(144, 0, 0, 16)
            self.pulse_write_full_stop(272, 0, 0, 1)
            self.pulse_write_full_stop(208, 0, 0, 16)
            self.pulse_write_full_stop(240, 0, 0, 16)
            self.pulse_write_full_stop(288, 0, 0, 1)
            self.pulser_close()

        elif self.test_flag == 'test':
            self.pulse_write_full_stop(320, 0, 0, 1)
            self.pulse_write_full_stop(176, 0, 0, 16)
            self.pulse_write_full_stop(80, 0, 0, 16)
            self.pulse_write_full_stop(112, 0, 0, 16)
            self.pulse_write_full_stop(48, 0, 0, 16)
            self.pulse_write_full_stop(16, 0, 0, 16)
            self.pulse_write_full_stop(304, 0, 0, 1)
            self.pulse_write_full_stop(144, 0, 0, 16)
            self.pulse_write_full_stop(272, 0, 0, 1)
            self.pulse_write_full_stop(208, 0, 0, 16)
            self.pulse_write_full_stop(240, 0, 0, 16)
            self.pulse_write_full_stop(288, 0, 0, 1)

    def pulser_stop(self):
        """
        A function to stop pulse sequence
        """
        if self.test_flag != 'test':
            # get repetition rate
            rep_rate = self.rep_rate[0]
            if rep_rate[-3:] == ' Hz':
                rep_time = int(1000000000/float(rep_rate[:-3]))
            elif rep_rate[-3:] == 'kHz':
                rep_time = int(1000000/float(rep_rate[:-4]))
            elif rep_rate[-3:] == 'MHz':
                rep_time = int(1000/float(rep_rate[:-4]))

            self.pulser_open()
            self.device_write( 4, byte_to_write = 4, data_to_write = 56, type_of_systems = 2, shift = 0 )

            to_spinapi = self.split_into_parts( self.pulse_array, rep_time )
            
            # instructions from file:
            if self.instr_from_file == 1:
                with open("instructions.out", "a") as f:
                    np.savetxt(f, [reduce(iconcat, to_spinapi, [])], delimiter = ',', fmt = '%u') 
            
                f.close()
            
            self.i_trigger = 0
            self.i_amp_on = 0
            self.i_lna = 0
            self.i_mw = 0
            self.i_x= 0
            self.i_y = 0
            self.i_trigger_awg = 0
            self.i_awg = 0
            self.i_laser = 0
            self.i_shaper = 0
            self.i_video = 0
            self.i_laser_2 = 0

            self.pulse_write_stop(48, 0, 0, self.i_x , self.i_x_prev)
            self.pulse_write_stop(16, 0, 0, self.i_y , self.i_y_prev)

            for element in to_spinapi:
                if element[0] == self.channel_dict['TRIGGER']:
                    self.i_trigger = self.i_trigger + 1
                    assert( self.i_trigger <= 1 ), 'Only 1 TRIGGER pulse allowed' 

                    self.pulse_write_stop(320, element[1], element[2], self.i_trigger , self.i_trigger_prev)

                elif element[0] == self.channel_dict['AMP_ON']:
                    self.i_amp_on = self.i_amp_on + 1
                    assert( self.i_amp_on <= 16 ), 'Only 16 AMP_ON pulses allowed'

                    self.pulse_write_stop(176, element[1], element[2], self.i_amp_on , self.i_amp_on_prev)

                elif element[0] == self.channel_dict['LNA_PROTECT']:
                    self.i_lna = self.i_lna + 1
                    assert( self.i_lna <= 16 ), 'Only 16 LNA_PROTECT pulses allowed'

                    self.pulse_write_stop(80, element[1], element[2], self.i_lna , self.i_lna_prev)

                elif element[0] == self.channel_dict['MW']:

                    self.i_mw = self.i_mw + 1
                    assert( self.i_mw <= 16 ), 'Only 16 MW pulses allowed'

                    self.pulse_write_stop(112, element[1], element[2], self.i_mw , self.i_mw_prev)

                elif element[0] == self.channel_dict['-X']:
                    self.i_x = self.i_x + 1
                    assert( self.i_x <= 16 ), 'Only 16 -X pulses allowed'

                    self.pulse_write_stop(48, element[1], element[2], self.i_x , self.i_x_prev)

                elif element[0] == self.channel_dict['+Y']:
                    self.i_y = self.i_y + 1
                    assert( self.i_y <= 16 ), 'Only 16 +Y pulses allowed'
                    self.pulse_write_stop(16, element[1], element[2], self.i_y , self.i_y_prev)

                elif element[0] == self.channel_dict['TRIGGER_AWG']:
                    self.i_trigger_awg = self.i_trigger_awg + 1
                    assert( self.i_trigger_awg <= 1 ), 'Only 1 TRIGGER AWG pulse allowed'

                    self.pulse_write_stop(304, element[1], element[2], self.i_trigger_awg , self.i_trigger_awg_prev)


                elif element[0] == self.channel_dict['AWG']:
                    self.i_awg = self.i_awg + 1
                    assert( self.i_awg <= 16 ), 'Only 16 AWG pulses allowed'

                    self.pulse_write_stop(144, element[1], element[2], self.i_awg , self.i_awg_prev)

                elif element[0] == self.channel_dict['LASER']:
                    self.i_laser = self.i_laser + 1
                    assert( self.i_laser <= 1 ), 'Only 1 LASER pulse allowed'
                    
                    self.pulse_write_stop(272, element[1], element[2], self.i_laser , self.i_laser_prev)

                elif element[0] == self.channel_dict['SHAPER']:
                    self.i_shaper = self.i_shaper + 1
                    assert( self.i_shaper <= 16 ), 'Only 16 SHAPER pulses allowed'

                    self.pulse_write_stop(208, element[1], element[2], self.i_shaper , self.i_shaper_prev)

                elif element[0] == self.channel_dict['VIDEO_PROTECT']:
                    self.i_video = self.i_video + 1
                    assert( self.i_video <= 16 ), 'Only 16 VIDEO_PROTECT pulses allowed'

                    self.pulse_write_stop(240, element[1], element[2], self.i_video , self.i_video_prev)

                elif element[0] == self.channel_dict['LASER_2']:
                    self.i_laser_2 = self.i_laser_2 + 1
                    assert( self.i_laser_2 <= 1 ), 'Only 1 LASER_2 pulses allowed'

                    self.pulse_write_stop(288, element[1], element[2], self.i_laser_2 , self.i_laser_2_prev)

            self.i_trigger = 0
            self.i_amp_on = 0
            self.i_lna = 0
            self.i_mw = 0
            self.i_x= 0
            self.i_y = 0
            self.i_trigger_awg = 0
            self.i_awg = 0
            self.i_laser = 0
            self.i_shaper = 0
            self.i_video = 0
            self.i_laser_2 = 0

            self.i_trigger_prev = 0
            self.i_amp_on_prev = 0
            self.i_lna_prev = 0
            self.i_mw_prev = 0
            self.i_x_prev = 0
            self.i_y_prev = 0
            self.i_trigger_awg_prev = 0
            self.i_awg_prev = 0
            self.i_laser_prev = 0
            self.i_shaper_prev = 0
            self.i_video_prev = 0
            self.i_laser_2_prev = 0

            self.pulser_close()

        elif self.test_flag == 'test':
            # get repetition rate
            rep_rate = self.rep_rate[0]
            if rep_rate[-3:] == ' Hz':
                rep_time = int(1000000000/float(rep_rate[:-3]))
            elif rep_rate[-3:] == 'kHz':
                rep_time = int(1000000/float(rep_rate[:-4]))
            elif rep_rate[-3:] == 'MHz':
                rep_time = int(1000/float(rep_rate[:-4]))

            to_spinapi = self.split_into_parts( self.pulse_array, rep_time )
            
            # instructions from file:
            if self.instr_from_file == 1:
                with open("instructions.out", "a") as f:
                    np.savetxt(f, [reduce(iconcat, to_spinapi, [])], delimiter = ',', fmt = '%u') 
            
                f.close()
            
            self.i_trigger = 0
            self.i_amp_on = 0
            self.i_lna = 0
            self.i_mw = 0
            self.i_x= 0
            self.i_y = 0
            self.i_trigger_awg = 0
            self.i_awg = 0
            self.i_laser = 0
            self.i_shaper = 0
            self.i_video = 0
            self.i_laser_2 = 0

            for element in to_spinapi:
                if element[0] == self.channel_dict['TRIGGER']:
                    self.i_trigger = self.i_trigger + 1
                    assert( self.i_trigger <= 1 ), 'Only 1 TRIGGER pulse allowed' 

                    #self.pulse_write_stop(320, element[1], element[2], self.i_trigger , self.i_trigger_prev)

                elif element[0] == self.channel_dict['AMP_ON']:
                    self.i_amp_on = self.i_amp_on + 1
                    assert( self.i_amp_on <= 16 ), 'Only 16 AMP_ON pulses allowed'

                    #self.pulse_write_stop(176, element[1], element[2], self.i_amp_on , self.i_amp_on_prev)

                elif element[0] == self.channel_dict['LNA_PROTECT']:
                    self.i_lna = self.i_lna + 1
                    assert( self.i_lna <= 16 ), 'Only 16 LNA_PROTECT pulses allowed'

                    #self.pulse_write_stop(80, element[1], element[2], self.i_lna , self.i_lna_prev)

                elif element[0] == self.channel_dict['MW']:

                    self.i_mw = self.i_mw + 1
                    assert( self.i_mw <= 16 ), 'Only 16 MW pulses allowed'

                    #self.pulse_write_stop(112, element[1], element[2], self.i_mw , self.i_mw_prev)

                elif element[0] == self.channel_dict['-X']:
                    self.i_x = self.i_x + 1
                    assert( self.i_x <= 16 ), 'Only 16 -X pulses allowed'

                    #self.pulse_write_stop(48, element[1], element[2], self.i_x , self.i_x_prev)

                elif element[0] == self.channel_dict['+Y']:
                    self.i_y = self.i_y + 1
                    assert( self.i_y <= 16 ), 'Only 16 +Y pulses allowed'
                    #self.pulse_write_stop(16, element[1], element[2], self.i_y , self.i_y_prev)

                elif element[0] == self.channel_dict['TRIGGER_AWG']:
                    self.i_trigger_awg = self.i_trigger_awg + 1
                    assert( self.i_trigger_awg <= 1 ), 'Only 1 TRIGGER AWG pulse allowed'

                    #self.pulse_write_stop(304, element[1], element[2], self.i_trigger_awg , self.i_trigger_awg_prev)


                elif element[0] == self.channel_dict['AWG']:
                    self.i_awg = self.i_awg + 1
                    assert( self.i_awg <= 16 ), 'Only 16 AWG pulses allowed'

                    #self.pulse_write_stop(144, element[1], element[2], self.i_awg , self.i_awg_prev)

                elif element[0] == self.channel_dict['LASER']:
                    self.i_laser = self.i_laser + 1
                    assert( self.i_laser <= 1 ), 'Only 1 LASER pulse allowed'
                    
                    #self.pulse_write_stop(272, element[1], element[2], self.i_laser , self.i_laser_prev)

                elif element[0] == self.channel_dict['SHAPER']:
                    self.i_shaper = self.i_shaper + 1
                    assert( self.i_shaper <= 16 ), 'Only 16 SHAPER pulses allowed'

                    #self.pulse_write_stop(208, element[1], element[2], self.i_shaper , self.i_shaper_prev)

                elif element[0] == self.channel_dict['VIDEO_PROTECT']:
                    self.i_video = self.i_video + 1
                    assert( self.i_video <= 16 ), 'Only 16 VIDEO_PROTECT pulses allowed'

                    #self.pulse_write_stop(240, element[1], element[2], self.i_video , self.i_video_prev)

                elif element[0] == self.channel_dict['LASER_2']:
                    self.i_laser_2 = self.i_laser_2 + 1
                    assert( self.i_laser_2 <= 1 ), 'Only 1 LASER_2 pulses allowed'

                    #self.pulse_write_stop(288, element[1], element[2], self.i_laser_2 , self.i_laser_2_prev)

                #self.pulse_write_stop(48, 0, 0, self.i_x , self.i_x_prev)
               # self.pulse_write_stop(16, 0, 0, self.i_y , self.i_y_prev)

            self.i_trigger = 0
            self.i_amp_on = 0
            self.i_lna = 0
            self.i_mw = 0
            self.i_x= 0
            self.i_y = 0
            self.i_trigger_awg = 0
            self.i_awg = 0
            self.i_laser = 0
            self.i_shaper = 0
            self.i_video = 0
            self.i_laser_2 = 0

            self.i_trigger_prev = 0
            self.i_amp_on_prev = 0
            self.i_lna_prev = 0
            self.i_mw_prev = 0
            self.i_x_prev = 0
            self.i_y_prev = 0
            self.i_trigger_awg_prev = 0
            self.i_awg_prev = 0
            self.i_laser_prev = 0
            self.i_shaper_prev = 0
            self.i_video_prev = 0
            self.i_laser_2_prev = 0

    def pulser_visualize(self):
        """
        Function for visualization of pulse sequence.
        There are two possibilities:
        1) Real final instructions with already summed up channel numbers
        2) Individual pulses
        """
        if self.test_flag != 'test':
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
            visualizer = self.convert_to_bit_pulse_visualizer( self.pulse_array )

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
        for element in self.pulse_array_init:
            pulse_list_mod = pulse_list_mod + str(element) + '\n'

        return pulse_list_mod
    
    def pulser_clear(self):
        """
        A special function for Pulse Control module
        It clear self.pulse_array and other status flags
        """
        self.pulse_array = []
        self.phase_array_length = []
        self.pulse_name_array = []
        self.pulse_array_init = []
        self.rep_rate = (self.repetition_rate, )
        self.shift_count = 0
        self.rep_rate_count = 0
        self.increment_count = 0
        self.reset_count = 0
        self.current_phase_index = 0
        self.awg_pulses = 0
        self.phase_pulses = 0

    def pulser_test_flag(self, flag):
        """
        A special function for Pulse Control module
        It runs TEST mode
        """
        self.test_flag = flag

    def pulser_acquisition_cycle(self, data1, data2, acq_cycle = []):
        if self.test_flag != 'test':
            answer = np.zeros( data1.shape ) + 1j*np.zeros( data2.shape )

            for index, element in enumerate(acq_cycle):
                if element == '+' or element == '+x':
                    answer = answer + data1[index] + 1j*data2[index]
                elif element == '-' or element == '-x':
                    answer = answer - data1[index] - 1j*data2[index]
                elif element == '+i' or element == '+y':
                    answer = answer + 1j*data1[index] - data2[index]
                elif element == '-i' or element == '-y':
                    answer = answer - 1j*data1[index] + data2[index]

            return (answer.real / len(acq_cycle))[0], (answer.imag / len(acq_cycle))[0]

        elif self.test_flag == 'test':

            assert( len(acq_cycle) == len(data1) ), 'Acquisition cycle and Data 1 have incompatible size'
            assert( len(acq_cycle) == len(data2) ), 'Acquisition cycle and Data 2 have incompatible size'

            answer = np.zeros( data1.shape ) + 1j*np.zeros( data2.shape )

            ##for index, element in enumerate(acq_cycle):
            ##    if element == '+':
            ##        answer = answer + data1[index] + 1j*data2[index]
            ##    elif element == '-':
            ##        answer = answer - data1[index] - 1j*data2[index]
            ##    elif element == '+i':
            ##        answer = answer + 1j*data1[index] - data2[index]
            ##    elif element == '-i':
            ##        answer = answer - 1j*data1[index] + data2[index]
            ##    else:
            ##        assert (1 == 2), 'Incorrect operation in the acquisition cycle'

            return (answer.real / len(acq_cycle))[0], (answer.imag / len(acq_cycle))[0]
    
    #UNDOCUMENTED
    def pulser_instruction_from_file(self, flag, filename = 'instructions.out'):
        """
        Special function to read instructions from the .txt file
        """
        if self.test_flag != 'test':
            if flag == 1:
                self.instr_from_file = 1
                f = open(filename)
                self.raw_instructions = f.read().splitlines()
                f.close()
            elif flag == 0:
                self.instr_from_file = 0

        elif self.test_flag == 'test':
            if flag == 1:
                self.instr_from_file = 1
            elif flag == 0:
                self.instr_from_file = 0

    # Auxilary functions
    def pulser_open(self):
        if self.state == 0: 
            dev = '/dev/devfmc' 
            mode = 0o666 
            flags = os.O_RDWR #| os.O_CREAT
            self.m_device_fd = os.open(dev, flags, mode)

            if self.m_device_fd < 0:
               return 'ERROR open device - DEVICE NOT FOUND'
               self.state = 0
            else:
                self.state = 1

                return 'DEVICE OPENED'

    # NEW
    def pulser_close(self):
        if self.test_flag != 'test':
            if self.m_device_fd >= 0:
               os.close( self.m_device_fd )
               self.m_device_fd = -1
               self.state = 0
               return 'DEVICE CLOSED'
            else:
                pass
        elif self.test_flag == 'test':
            pass

    def device_read(self, address, byte_to_read = 4):
        if self.test_flag != 'test':
            self.dataio[1] = int( byte_to_read )
            self.dataio[0] = int( address * 4 )
            
            general.wait( self.internal_pause )
            fcntl.ioctl(self.m_device_fd, self.READ_BAR, self.dataio, 1)
            
        elif self.test_flag == 'test':
            pass
    
    def device_write(self, address, byte_to_write = 4, data_to_write = 1, type_of_systems = 10, shift = 0):
        if self.test_flag != 'test':    
            if type_of_systems == 2:
                self.dataio[2] = data_to_write << shift
            elif type_of_systems == 16:
                self.dataio[2] = int( data_to_write, 16 )
            elif type_of_systems == 10:
                self.dataio[2] = int( data_to_write )

            self.dataio[1] = int( byte_to_write )
            self.dataio[0] = int( address * 4 )

            general.wait( self.internal_pause )
            fcntl.ioctl(self.m_device_fd, self.WRITE_BAR, self.dataio, 1)
        
        elif self.test_flag == 'test':
            pass

    def convertion_to_numpy(self, p_array):
        """
        Convertion of the pulse_array into numpy array in the form of
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
                if ch in self.channel_dict:
                    ch_num = self.channel_dict[ch]

                # get start
                if ch != 'AWG':
                    st = p_array[i]['start']
                else:
                    # shift AWG pulse to get RECT_AWG
                    st = self.change_pulse_settings(p_array[i]['start'], -self.rect_awg_switch_delay)
                    self.awg_pulses = 1

                if st[-2:] == 'ns':
                    st_time = int(float(st[:-3])/self.timebase)
                elif st[-2:] == 'us':
                    st_time = int(float(st[:-3])*1000/self.timebase)
                elif st[-2:] == 'ms':
                    st_time = int(float(st[:-3])*1000000/self.timebase)
                elif st[-2:] == 's':
                    st_time = int(float(st[:-3])*1000000000/self.timebase)
                
                # get length
                if ch != 'AWG':
                    leng = p_array[i]['length']
                else:
                    # shift AWG pulse to get RECT_AWG
                    leng = self.change_pulse_settings(p_array[i]['length'], self.rect_awg_switch_delay + self.rect_awg_delay)
                    self.awg_pulses = 1

                if leng[-2:] == 'ns':
                    leng_time = int(float(leng[:-3])/self.timebase)
                elif leng[-2:] == 'us':
                    leng_time = int(float(leng[:-3])*1000/self.timebase)
                elif leng[-2:] == 'ms':
                    leng_time = int(float(leng[:-3])*1000000/self.timebase)
                elif leng[-2:] == 's':
                    leng_time = int(float(leng[:-3])*1000000000/self.timebase)

                # get delta start
                del_st = p_array[i]['delta_start']
                if del_st[-2:] == 'ns':
                    delta_start = int(float(del_st[:-3])/self.timebase)
                elif del_st[-2:] == 'us':
                    delta_start = int(float(del_st[:-3])*1000/self.timebase)
                elif del_st[-2:] == 'ms':
                    delta_start = int(float(del_st[:-3])*1000000/self.timebase)
                elif del_st[-2:] == 's':
                    delta_start = int(float(del_st[:-3])*1000000000/self.timebase)

                # get length_increment
                len_in = p_array[i]['length_increment']
                if len_in[-2:] == 'ns':
                    length_increment = int(float(len_in[:-3])/self.timebase)
                elif len_in[-2:] == 'us':
                    length_increment = int(float(len_in[:-3])*1000/self.timebase)
                elif len_in[-2:] == 'ms':
                    length_increment = int(float(len_in[:-3])*1000000/self.timebase)
                elif len_in[-2:] == 's':
                    length_increment = int(float(len_in[:-3])*1000000000/self.timebase)

                # creating converted array
                # in terms of bits the number of channel is 2**(ch_num - 1)
                #pulse_temp_array.append( (2**(ch_num), st_time, st_time + leng_time, delta_start, length_increment) )
                pulse_temp_array.append( (ch_num, st_time + self.constant_shift, self.constant_shift + st_time + leng_time) )

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
                if ch in self.channel_dict:
                    ch_num = self.channel_dict[ch]

                # get start
                if ch != 'AWG':
                    st = p_array[i]['start']
                else:
                    st = self.change_pulse_settings(p_array[i]['start'], -self.rect_awg_switch_delay)
                    self.awg_pulses = 1

                if st[-2:] == 'ns':
                    st_time = int(float(st[:-3])/self.timebase)
                elif st[-2:] == 'us':
                    st_time = int(float(st[:-3])*1000/self.timebase)
                elif st[-2:] == 'ms':
                    st_time = int(float(st[:-3])*1000000/self.timebase)
                elif st[-2:] == 's':
                    st_time = int(float(st[:-3])*1000000000/self.timebase)

                # get length
                if ch != 'AWG':
                    leng = p_array[i]['length']
                else:
                    # shift AWG pulse to get RECT_AWG
                    leng = self.change_pulse_settings(p_array[i]['length'], self.rect_awg_switch_delay + self.rect_awg_delay)
                    self.awg_pulses = 1
                
                if leng[-2:] == 'ns':
                    leng_time = int(float(leng[:-3])/self.timebase)
                elif leng[-2:] == 'us':
                    leng_time = int(float(leng[:-3])*1000/self.timebase)
                elif leng[-2:] == 'ms':
                    leng_time = int(float(leng[:-3])*1000000/self.timebase)
                elif leng[-2:] == 's':
                    leng_time = int(float(leng[:-3])*1000000000/self.timebase)

                # get delta start
                del_st = p_array[i]['delta_start']
                if del_st[-2:] == 'ns':
                    delta_start = int(float(del_st[:-3])/self.timebase)
                elif del_st[-2:] == 'us':
                    delta_start = int(float(del_st[:-3])*1000/self.timebase)
                elif del_st[-2:] == 'ms':
                    delta_start = int(float(del_st[:-3])*1000000/self.timebase)
                elif del_st[-2:] == 's':
                    delta_start = int(float(del_st[:-3])*1000000000/self.timebase)

                # get length_increment
                len_in = p_array[i]['length_increment']
                if len_in[-2:] == 'ns':
                    length_increment = int(float(len_in[:-3])/self.timebase)
                elif len_in[-2:] == 'us':
                    length_increment = int(float(len_in[:-3])*1000/self.timebase)
                elif len_in[-2:] == 'ms':
                    length_increment = int(float(len_in[:-3])*1000000/self.timebase)
                elif len_in[-2:] == 's':
                    length_increment = int(float(len_in[:-3])*1000000000/self.timebase)

                # creating converted array
                # in terms of bits the number of channel is 2**(ch_num - 1)
                pulse_temp_array.append( (ch_num, self.constant_shift + st_time, self.constant_shift + st_time + leng_time ) )

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

        RECT_AWG pulses are combined with MW pulses in the same array, since for
        both of them AMP_ON and LNA_PROTECT pulses are needed
        """
        if self.test_flag != 'test':
            # according to 0 element (channel number)
            answer = np.split(np_array, np.where(np.diff(np_array[:,0]))[0] + 1)

            # to save time if there is no AWG pulses
            if self.awg_pulses == 0:
                pass
            elif self.awg_pulses == 1:
                # join AWG and MW pulses in order to add AMP_ON and LNA_PROTECT for them together
                for index, element in enumerate(answer):
                    # memorize indexes
                    if element[0, 0] == self.channel_dict['MW']:
                        mw_index = index
                    elif element[0, 0] == self.channel_dict['AWG']:
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

            if self.awg_pulses == 0:
                pass
            elif self.awg_pulses == 1:
                # attempt to join AWG and MW pulses in order to add AMP_ON and LNA_PROTECT for them together
                for index, element in enumerate(answer):
                    # memorize indexes
                    if element[0, 0] == self.channel_dict['MW']:
                        mw_index = index
                    elif element[0, 0] == self.channel_dict['AWG']:
                        awg_index = index

                # combines arrays if there is MW and AWG pulses
                try:
                    answer[mw_index] = np.concatenate((answer[mw_index], answer[awg_index]), axis = 0)
                    # delete duplicated AWG pulses; answer is python list -> pop
                    answer.pop(awg_index)

                except UnboundLocalError:
                    pass

            return answer

    def extending_rect_awg(self, np_array):
        """
        Replace RECT_AWG pulse with the extending one (in the same way as AMP_ON and LNA_PROTECT)
        
        Instead of directly changing self.pulse_array we change the output of 
        self.splitting_acc_to_channel() and use this function in the output of preparing_to_bit_pulse()


        """
        if self.test_flag != 'test':
            answer = self.splitting_acc_to_channel( self.convertion_to_numpy( np_array ) )
            # return flatten np.array of pulses that has the same format as self.convertion_to_numpy( np_array )
            # but with extended RECT_AWG pulse
            return np.asarray(list(chain(*answer)))

        elif self.test_flag == 'test':
            answer = self.splitting_acc_to_channel( self.convertion_to_numpy( np_array ) )
            
            return np.asarray(list(chain(*answer)))

    def check_problem_pulses(self, np_array):
        """
        A function for checking whether there is a two
        close to each other pulses (less than 40 ns)
        In Auto_defense = True we checked everything except
        AMN_ON and LNA_PROTECT
        """
        if self.test_flag != 'test':
            # sorted pulse list in order to be able to have an arbitrary pulse order inside
            # the definition in the experimental script
            sorted_np_array = np.asarray(sorted(np_array, key = lambda x: int(x[1])), dtype = np.int64)
            ## 16-09-2021; An attempt to optimize the speed; all pulses should be already checked in the TEST RUN
            ## Uncomment everything starting with ## if needed

            ### compare the end time with the start time for each couple of pulses
            ##for index, element in enumerate(sorted_np_array[:-1]):
            ##    # minimal_distance is 40 ns now
            ##    if sorted_np_array[index + 1][1] - element[2] < self.min_pulse_length:
            ##        assert(1 == 2), 'Overlapping pulses or two pulses with less than ' + str(self.min_pulse_length) + ' ns distance'
            ##    else:
            ##        pass

            return sorted_np_array

        elif self.test_flag == 'test':
            sorted_np_array = np.asarray(sorted(np_array, key = lambda x: int(x[1])), dtype = np.int64)

            # compare the end time with the start time for each couple of pulses
            for index, element in enumerate(sorted_np_array[:-1]):
                # minimal_distance is 40 ns now
                if sorted_np_array[index + 1][1] - element[2] < self.min_pulse_length:
                    assert(1 == 2), 'Overlapping pulses or two pulses with less than ' + str(self.min_pulse_length) + ' ns distance'
                else:
                    pass

            return sorted_np_array

    def check_problem_pulses_phase(self, np_array):
        """
        A function for checking whether there is a two
        close to each other pulses (less than 12 ns)
        In Auto_defense = True by this function we checked only 
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
            ##    if sorted_np_array[index + 1][1] - element[2] < self.minimal_distance_phase:
            ##        assert(1 == 2), 'Overlapping pulses or two pulses with less than ' + str(self.minimal_distance_phase * self.timebase) + ' ns distance'
            ##    else:
            ##        pass

            return sorted_np_array

        elif self.test_flag == 'test':
            sorted_np_array = np.asarray(sorted(np_array, key = lambda x: int(x[1])), dtype = np.int64)

            # compare the end time with the start time for each couple of pulses
            for index, element in enumerate(sorted_np_array[:-1]):
                if sorted_np_array[index + 1][1] - element[2] < self.minimal_distance_phase:
                    assert(1 == 2), 'Overlapping pulses or two pulses with less than ' + str(self.minimal_distance_phase * self.timebase) + ' ns distance'
                else:
                    pass

            return np_array

    def delete_duplicates(self, np_array):
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

    def preparing_to_bit_pulse(self, np_array):
        """
        For pulses at each channel we check whether there is overlapping pulses using 
        check_problem_pulses()

        This function also automatically adds LNA_PROTECT and AMP_ON pulses 
        using add_amp_on_pulses() / add_lna_protect_pulses() and check
        them on the distance < 12 ns, if so they are combined in one pulse inside 
        instruction_pulse_short_lna_amp() function

        for phase pulses the minimal distance for checking is 10 ns
        for mw, awg or cross mw-awg - 40 ns

        RECT_AWG pulses are shifted back in order to compare their distance with MW pulses

        """
        if self.test_flag != 'test':
            if self.auto_defense == 'False':
                split_pulse_array = self.splitting_acc_to_channel( self.convertion_to_numpy( np_array ) )
                # iterate over all pulses at different channels
                for index, element in enumerate(split_pulse_array):
                    # for all pulses just check 40 ns distance
                    self.check_problem_pulses(element)
                    # get assertion error if the distance < 40 ns
                    
                return self.convertion_to_numpy( np_array )

            elif self.auto_defense == 'True':
                # for delete AWG pulses before overlap check; and for checking only AWG pulses
                awg_index = []
                mw_index = []
                # for checking of overlap MW and non-shifted AWG; in the real pulse sequence AWG is converted to shifter RECT_AWG
                shifted_back_awg_pulses = []

                split_pulse_array = self.splitting_acc_to_channel( self.convertion_to_numpy( np_array ) )

                # iterate over all pulses at different channels
                for index, element in enumerate(split_pulse_array):
                    if element[0, 0] == self.channel_dict['MW'] or element[0, 0] == self.channel_dict['AWG']:

                        self.check_problem_pulses(element)
                        
                        #if self.awg_pulses != 1:
                        #    # for MW pulses check 40 ns distance and add AMP_ON, LNA_PROTECT pulses
                        #    self.check_problem_pulses(element)
                        #else:
                        #    # for AWG we do not check 40 ns distance, since RECT_AWG will be extended in the same way as AMP_ON
                        #    for index_awg_mw, element_awg_mw in enumerate(element):
                        #        if element_awg_mw[0] == self.channel_dict['AWG']:
                        #            # shift back RECT_AWG to AWG
                        #            shifted_back_awg_pulses.append([element_awg_mw[0], element_awg_mw[1] + 0*int(self.rect_awg_switch_delay/self.timebase), \
                        #                element_awg_mw[2] + 0*int(self.rect_awg_switch_delay/self.timebase) - 0*int(self.rect_awg_switch_delay/self.timebase) - 0*int(self.rect_awg_delay/self.timebase)])
                        #
                        #            awg_index.append(index_awg_mw)
                        #
                        #        elif element_awg_mw[0] == self.channel_dict['MW']:
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
                        #    self.check_problem_pulses(no_awg_element)
                        #    self.check_problem_pulses(no_mw_element)
                        #    self.check_problem_pulses(shifted_back_awg_mw)

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
                            amp_on_pulses, shaper_pulses = self.convert_to_bit_pulse_amp_lna(prob_pulses_amp)
                            cor_pulses_amp_final = np.concatenate((self.instruction_pulse_short_lna_amp(amp_on_pulses), self.instruction_pulse_short_lna_amp(shaper_pulses)), axis = 0)
                        else:
                            amp_on_pulses, shaper_pulses = self.convert_to_bit_pulse_amp_lna(prob_pulses_amp)
                            try:
                                cor_pulses_amp_final = np.concatenate((cor_pulses_amp, self.instruction_pulse_short_lna_amp(amp_on_pulses), self.instruction_pulse_short_lna_amp(shaper_pulses)), axis = 0)
                            except ValueError:
                                cor_pulses_amp_final = np.concatenate((cor_pulses_amp, self.instruction_pulse_short_lna_amp(amp_on_pulses)), axis = 0)

                        # combining short distance LNA_PROTECT pulses
                        if prob_pulses_lna[0][0] == 0:
                            cor_pulses_lna_final = cor_pulses_lna
                        elif cor_pulses_lna[0][0] == 0:
                            # nothing to concatenate
                            lna_pulses, video_pulses = self.convert_to_bit_pulse_amp_lna(prob_pulses_lna)
                            cor_pulses_lna_final =  np.concatenate((self.instruction_pulse_short_lna_amp(lna_pulses), self.instruction_pulse_short_lna_amp(video_pulses)), axis = 0)
                        else:
                            lna_pulses, video_pulses = self.convert_to_bit_pulse_amp_lna(prob_pulses_lna)
                            cor_pulses_lna_final =  np.concatenate((cor_pulses_lna, self.instruction_pulse_short_lna_amp(lna_pulses), self.instruction_pulse_short_lna_amp(video_pulses)), axis = 0)

                    elif element[0, 0] == self.channel_dict['-X'] or element[0, 0] == self.channel_dict['+Y']:
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
                try:
                    #return np.row_stack( (self.convertion_to_numpy( self.pulse_array ), cor_pulses_amp_final, cor_pulses_lna_final))
                    # self.extending_rect_awg( self.pulse_array ) is for extendind RECT_AWG pulses
                    # see self.extending_rect_awg()
                    return np.row_stack( (self.extending_rect_awg( self.pulse_array ), cor_pulses_amp_final, cor_pulses_lna_final))

                # when we do not MW pulses at all
                except UnboundLocalError:
                    #return self.convertion_to_numpy( self.pulse_array )
                    return self.extending_rect_awg( self.pulse_array )

        elif self.test_flag == 'test':
            if self.auto_defense == 'False':
                split_pulse_array = self.splitting_acc_to_channel( self.convertion_to_numpy( np_array ) )

                # iterate over all pulses at different channels
                for index, element in enumerate(split_pulse_array):
                    # for all pulses just check 40 ns distance
                    self.check_problem_pulses(element)
                    # get assertion error if the distance < 40 ns
                    
                return self.convertion_to_numpy( np_array )

            elif self.auto_defense == 'True':
                awg_index = []
                mw_index = []
                shifted_back_awg_pulses = []

                split_pulse_array = self.splitting_acc_to_channel( self.convertion_to_numpy( np_array ) )

                for index, element in enumerate(split_pulse_array):
                    if element[0, 0] == self.channel_dict['MW'] or element[0, 0] == self.channel_dict['AWG']:

                        self.check_problem_pulses(element)

                        #if self.awg_pulses != 1:
                        #    # for MW pulses check 40 ns distance and add AMP_ON, LNA_PROTECT pulses
                        #    self.check_problem_pulses(element)
                        #else:
                        #    # for AWG we do not check 40 ns distance, since RECT_AWG will be extended in the same way as AMP_ON
                        #   for index_awg_mw, element_awg_mw in enumerate(element):
                        #        if element_awg_mw[0] == self.channel_dict['AWG']:
                        #            # shift back RECT_AWG to AWG
                        #            shifted_back_awg_pulses.append([element_awg_mw[0], element_awg_mw[1] + 0*int(self.rect_awg_switch_delay/self.timebase), \
                        #                element_awg_mw[2] + 0*int(self.rect_awg_switch_delay/self.timebase) - 0*int(self.rect_awg_switch_delay/self.timebase) - 0*int(self.rect_awg_delay/self.timebase)])
                        #
                        #            awg_index.append(index_awg_mw)
                        #
                        #        elif element_awg_mw[0] == self.channel_dict['MW']:
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
                        #    self.check_problem_pulses(no_awg_element)
                        #    # 09-10-2021 Commented next line for full AWG ESEEM
                        #    # uncomment in case of problems
                        #    self.check_problem_pulses(no_mw_element)
                        #    self.check_problem_pulses(shifted_back_awg_mw)

                            ##with open("test.out", "a") as f:
                            ##    np.savetxt(f, no_mw_element, delimiter=',', fmt = '%u') 
                            
                            ##f.close()

                        amp_on_pulses = self.add_amp_on_pulses(element)
                        lna_pulses = self.add_lna_protect_pulses(element)

                        # check AMP_ON, LNA_PROTECT pulses
                        cor_pulses_amp, prob_pulses_amp = self.check_problem_pulses_amp_lna(amp_on_pulses)
                        cor_pulses_lna, prob_pulses_lna = self.check_problem_pulses_amp_lna(lna_pulses)

                        # combining short distance AMP_ON pulses
                        if prob_pulses_amp[0][0] == 0:
                            cor_pulses_amp_final = cor_pulses_amp
                        elif cor_pulses_amp[0][0] == 0:
                            # nothing to concatenate
                            amp_on_pulses, shaper_pulses = self.convert_to_bit_pulse_amp_lna(prob_pulses_amp)
                            cor_pulses_amp_final = np.concatenate((self.instruction_pulse_short_lna_amp(amp_on_pulses), self.instruction_pulse_short_lna_amp(shaper_pulses)), axis = 0)
                        else:
                            amp_on_pulses, shaper_pulses = self.convert_to_bit_pulse_amp_lna(prob_pulses_amp)
                            try:
                                cor_pulses_amp_final = np.concatenate((cor_pulses_amp, self.instruction_pulse_short_lna_amp(amp_on_pulses), self.instruction_pulse_short_lna_amp(shaper_pulses)), axis = 0)
                            except ValueError:
                                cor_pulses_amp_final = np.concatenate((cor_pulses_amp, self.instruction_pulse_short_lna_amp(amp_on_pulses)), axis = 0)

                        # combining short distance LNA_PROTECT pulses
                        if prob_pulses_lna[0][0] == 0:
                            cor_pulses_lna_final = cor_pulses_lna
                        elif cor_pulses_lna[0][0] == 0:
                            # nothing to concatenate
                            lna_pulses, video_pulses = self.convert_to_bit_pulse_amp_lna(prob_pulses_lna)
                            cor_pulses_lna_final =  np.concatenate((self.instruction_pulse_short_lna_amp(lna_pulses), self.instruction_pulse_short_lna_amp(video_pulses)), axis = 0)
                        else:
                            lna_pulses, video_pulses = self.convert_to_bit_pulse_amp_lna(prob_pulses_lna)
                            cor_pulses_lna_final =  np.concatenate((cor_pulses_lna, self.instruction_pulse_short_lna_amp(lna_pulses), self.instruction_pulse_short_lna_amp(video_pulses)), axis = 0)

                    elif element[0, 0] == self.channel_dict['-X'] or element[0, 0] == self.channel_dict['+Y']:
                        # for phases pulses just check 10 ns distance
                        self.check_problem_pulses_phase(element)
                    else:
                        # for non-MW pulses just check 40 ns distance
                        self.check_problem_pulses(element)

                # combine all pulses
                #np.concatenate( (self.convertion_to_numpy( self.pulse_array ), cor_pulses_amp_final, cor_pulses_lna_final), axis = None) 
                try:
                    return np.row_stack( (self.extending_rect_awg( self.pulse_array ), cor_pulses_amp_final, cor_pulses_lna_final))
                except UnboundLocalError:
                    return self.extending_rect_awg( self.pulse_array )

    def split_into_parts(self, np_array, rep_time):
        """
        This function is adapted for using with Micran pulse generator instructions
        """
        if self.test_flag != 'test':
            answer = []
            min_list = []
            pulses = self.preparing_to_bit_pulse(np_array)

            # switch MW to SHAPER and vice versa for RECT channel
            # switch AWG to SHAPER and vice versa for RECT channel
            for element in pulses:
                if self.awg_pulses == 0:
                    if element[0] == self.channel_dict['MW']:
                        element[0] = self.channel_dict['SHAPER']
                    elif element[0] == self.channel_dict['SHAPER']:
                        element[0] = self.channel_dict['MW']
                elif self.awg_pulses == 1:
                    if element[0] == self.channel_dict['AWG']:
                        element[0] = self.channel_dict['SHAPER']
                    elif element[0] == self.channel_dict['SHAPER']:
                        element[0] = self.channel_dict['AWG']

            sorted_pulses_start = np.asarray(sorted(pulses, key = operator.itemgetter(1)), dtype = np.int64)

            #LASER HERE
            #general.message( sorted_pulses_start )
            # [[256 125 145] [  2 160 188] [  4 160 238] [  8 245 253] [  2 260 296] [  4 260 361] [ 16 330 361] [  8 345 361] [  1 455 505]]
           
            if rep_time - sorted_pulses_start[-1][2] - sorted_pulses_start[-1][1] > (self.min_pulse_length + 4):
                sorted_pulses_r_rate = np.append( sorted_pulses_start, np.asarray( [[0, sorted_pulses_start[-1][2], \
                    rep_time - sorted_pulses_start[-1][2] ]] ), axis = 0 )
                sorted_pulses_r_rate_start = np.asarray(sorted(sorted_pulses_r_rate, key = operator.itemgetter(0, 1)), dtype = np.int64)
                return sorted_pulses_r_rate_start
            else:
                general.message('Pulse sequence is longer than one period of the repetition rate')
                sys.exit()

        elif self.test_flag == 'test':
            answer = []
            min_list = []
            pulses = self.preparing_to_bit_pulse(np_array)

            for element in pulses:
                if self.awg_pulses == 0:
                    if element[0] == self.channel_dict['MW']:
                        element[0] = self.channel_dict['SHAPER']
                    elif element[0] == self.channel_dict['SHAPER']:
                        element[0] = self.channel_dict['MW']
                elif self.awg_pulses == 1:
                    if element[0] == self.channel_dict['MW']:
                        assert( 1 == 2 ), 'No RECT MW pulses allowed with AWG pulses'
                    elif element[0] == self.channel_dict['AWG']:
                        element[0] = self.channel_dict['SHAPER']
                    elif element[0] == self.channel_dict['SHAPER']:
                        element[0] = self.channel_dict['AWG']

            sorted_pulses_start = np.asarray(sorted(pulses, key = operator.itemgetter(1)), dtype = np.int64)
            
            if rep_time - sorted_pulses_start[-1][2] - sorted_pulses_start[-1][1] > (self.min_pulse_length + 4):
                sorted_pulses_r_rate = np.append( sorted_pulses_start, np.asarray( [[0, sorted_pulses_start[-1][2], \
                    rep_time - sorted_pulses_start[-1][2]]] ), axis = 0 )
                sorted_pulses_r_rate_start = np.asarray(sorted(sorted_pulses_r_rate, key = operator.itemgetter(0, 1)), dtype = np.int64)
                return sorted_pulses_r_rate_start
            else:
                general.message('Pulse sequence is longer than one period of the repetition rate')
                sys.exit()   

    def convert_to_bit_pulse(self, np_array):
        """
        A function to calculate in which time interval
        two or more different channels are on.
        All the pulses converted in an bit_array of 0 and 1, where
        1 corresponds to the time interval when the channel is on.
        The size of the bit_array is determined by the total length
        of the full pulse sequence.
        Finally, a bit_array is multiplied by a ch in order to
        calculate CH instructions.

        It is optimized for using at subarrays inside split_into_parts()
        """

        if self.test_flag != 'test':
            #pulses = self.preparing_to_bit_pulse(np_array)
            pulses = np_array
            max_pulse = np.amax(pulses[:,2])
            # we get rid of constant shift in the first pulse, since
            # it is useless in terms of pulse bluster instructions
            # the first pulse in sequence will start at 50 ns all other shifted accordingly
            # this value can be adjust by add_shift parameter (multiplited by self.timebase)
            min_pulse = np.amin(pulses[:,1]) - self.add_shift
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

        elif self.test_flag == 'test':
            #pulses = self.preparing_to_bit_pulse(np_array)
            pulses = np_array

            max_pulse = np.amax(pulses[:,2])
            min_pulse = np.amin(pulses[:,1]) - self.add_shift

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

        if self.test_flag != 'test':
            pulses = self.preparing_to_bit_pulse(np_array)
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
                    if self.awg_pulses == 0:
                        if pulses[i, 0] == self.channel_dict['MW']:
                            pulses[i, 0] = self.channel_dict['SHAPER']
                        elif pulses[i, 0] == self.channel_dict['SHAPER']:
                            pulses[i, 0] = self.channel_dict['MW']
                    elif self.awg_pulses == 1:
                        if pulses[i, 0] == self.channel_dict['AWG']:
                            pulses[i, 0] = self.channel_dict['SHAPER']
                        elif pulses[i, 0] == self.channel_dict['SHAPER']:
                            pulses[i, 0] = self.channel_dict['AWG']

                    translation_array = pulses[i, 0]*np.concatenate( (np.zeros( self.timebase*(pulses[i, 1] - min_pulse), dtype = np.int64), \
                        np.ones(self.timebase*(pulses[i, 2] - pulses[i, 1]), dtype = np.int64), \
                        np.zeros(self.timebase*(max_pulse - pulses[i, 2]), dtype = np.int64)), axis = None)
                
                    # appending each pulses individually
                    bit_array_pulses.append(translation_array)

                i += 1

            return bit_array_pulses

        elif self.test_flag == 'test':
            pulses = self.preparing_to_bit_pulse(np_array)
            #pulses = np_array
            #for index, element in enumerate(pulses):
            #    element[2] = element[1] + element[2]  

            max_pulse = np.amax(pulses[:,1])
            min_pulse = np.amin(pulses[:,1])

            #bit_array = np.zeros( max_pulse - 0*min_pulse, dtype = np.int64 )
            bit_array_pulses = []

            i = 0
            while i < len(pulses):
                # convert each pulse in an array of 0 and 1,
                # 1 corresponds to the time interval, where the channel is on
                if pulses[i, 0] != 0:
                    if self.awg_pulses == 0:
                        if pulses[i, 0] == self.channel_dict['MW']:
                            pulses[i, 0] = self.channel_dict['SHAPER']
                        elif pulses[i, 0] == self.channel_dict['SHAPER']:
                            pulses[i, 0] = self.channel_dict['MW']
                    elif self.awg_pulses == 1:
                        if pulses[i, 0] == 4:
                            assert( 1 == 2 ), 'No RECT MW pulses allowed with AWG pulses'
                        elif pulses[i, 0] == self.channel_dict['AWG']:
                            pulses[i, 0] = self.channel_dict['SHAPER']
                        elif pulses[i, 0] == self.channel_dict['SHAPER']:
                            pulses[i, 0] = self.channel_dict['AWG']

                    translation_array = pulses[i, 0]*np.concatenate( (np.zeros( pulses[i, 1] - min_pulse, dtype = np.int64), \
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

        if self.test_flag != 'test':
            #pulses = self.preparing_to_bit_pulse(np_array)
            pulses = np_array
            # convert back to channel, start, end
            # from channel, start, length
            for index, element in enumerate(pulses):
                element[2] = element[1] + element[2]  

            max_pulse = np.amax(pulses[:,2])
            min_pulse = np.amin(pulses[:,1]) - self.add_shift*0

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
            #pulses = self.preparing_to_bit_pulse(np_array)
            pulses = np_array
            for index, element in enumerate(pulses):
                element[2] = element[1] + element[2]  

            max_pulse = np.amax(pulses[:,1])
            min_pulse = np.amin(pulses[:,1]) - self.add_shift*0

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
        if self.test_flag != 'test':
            final_pulse_array = []

            # Create an array that is 1 where a is 0, and pad each end with an extra 0.
            iszero = np.concatenate(([0], np_array, [0]))
            absdiff = np.abs(np.diff(iszero))

            # creating a mask to split bit array
            ranges = np.where(absdiff != 0)[0]
            # using a mask
            pulse_array = np.split(np_array, ranges)
            pulse_info = np.concatenate(([0], ranges))

            # return back self.timebase; convert to instructions
            for index, element in enumerate(pulse_info[:-1]):
                final_pulse_array.append( [pulse_array[index][0], self.timebase*pulse_info[index], self.timebase*(pulse_info[index + 1] )] )

            return final_pulse_array

        elif self.test_flag == 'test':
            final_pulse_array = []

            # Create an array that is 1 where a is 0, and pad each end with an extra 0.
            iszero = np.concatenate(([0], np_array, [0]))
            absdiff = np.abs(np.diff(iszero))

            ranges = np.where(absdiff != 0)[0]
            pulse_array = np.split(np_array, ranges)
            pulse_info = np.concatenate(([0], ranges))

            for index, element in enumerate(pulse_info[:-1]):
                final_pulse_array.append( [pulse_array[index][0], self.timebase*pulse_info[index], self.timebase*(pulse_info[index + 1] )] )

            return final_pulse_array

    def add_amp_on_pulses(self, p_list):
        """
        A function that automatically add AMP_ON pulses with corresponding delays
        specified by switch_delay and amp_delay
        """
        if self.test_flag != 'test':
            if self.auto_defense == 'False':
                pass
            elif self.auto_defense == 'True':
                amp_on_list = []
                # for dealing with overlap of RECT_AWG pulse with MW; RECT_AWG should behaves the same as AMP_ON

                for index, element in enumerate(p_list):
                    if element[0] == self.channel_dict['MW']:
                        amp_on_list.append( [self.channel_dict['AMP_ON'], element[1] - self.switch_delay, element[2] + self.amp_delay] )
                        amp_on_list.append( [self.channel_dict['SHAPER'], element[1] - self.switch_shaper_delay, element[2] + self.shaper_delay] )
                    # AMP_ON and RECT_AWG coincide now
                    elif element[0] == self.channel_dict['AWG']:
                        amp_on_list.append( [self.channel_dict['AMP_ON'], element[1] - self.switch_delay, element[2] + self.amp_delay] )
                        amp_on_list.append( [self.channel_dict['SHAPER'], element[1] - self.switch_shaper_delay, element[2] + self.shaper_delay] )
                    else:
                        pass

                return np.asarray(amp_on_list)

        elif self.test_flag == 'test':
            if self.auto_defense == 'False':
                pass
            elif self.auto_defense == 'True':
                amp_on_list = []

                for index, element in enumerate(p_list):
                    if element[0] == self.channel_dict['MW']:
                        if (element[2] + self.amp_delay) - (element[1] - self.switch_delay) <= self.max_pulse_length:
                            amp_on_list.append( [self.channel_dict['AMP_ON'], element[1] - self.switch_delay, element[2] + self.amp_delay] )
                            amp_on_list.append( [self.channel_dict['SHAPER'], element[1] - self.switch_shaper_delay, element[2] + self.shaper_delay] )
                        else:
                            assert(1 == 2), 'Maximum available length (4980 ns) for AMP_ON pulse is reached'
                    # AMP_ON and RECT_AWG coincide now
                    elif element[0] == self.channel_dict['AWG']:
                        if element[2] - element[1]  <= self.max_pulse_length/2:
                            amp_on_list.append( [self.channel_dict['AMP_ON'], element[1] - self.switch_delay, element[2] + self.amp_delay] )
                            amp_on_list.append( [self.channel_dict['SHAPER'], element[1] - self.switch_shaper_delay, element[2] + self.shaper_delay] )
                        else:
                            assert(1 == 2), 'Maximum available length (4980 ns) for AMP_ON pulse is reached'

                    else:
                        pass

                return np.asarray(amp_on_list)

    def add_lna_protect_pulses(self, p_list):
        """
        A function that automatically add LNA_PROTECT and HPA_PROTECT pulses with corresponding delays
        specified by switch_delay and protect_delay
        """
        if self.test_flag != 'test':
            if self.auto_defense == 'False':
                pass
            elif self.auto_defense == 'True':
                lna_protect_list = []
                for index, element in enumerate(p_list):
                    if element[0] == self.channel_dict['MW']:
                        lna_protect_list.append( [self.channel_dict['LNA_PROTECT'], element[1] - self.switch_protect_delay, element[2] + self.protect_delay] )
                        lna_protect_list.append( [self.channel_dict['VIDEO_PROTECT'], element[1] - self.switch_protect_delay, element[2] + self.protect_delay] )
                    # LNA_PROTECT and RECT_AWG coincide in the start position but LNA is longer at protect_delay
                    elif element[0] == self.channel_dict['AWG']:
                        lna_protect_list.append( [self.channel_dict['LNA_PROTECT'], element[1] - self.switch_protect_delay, element[2] - int(self.rect_awg_delay/self.timebase) + self.protect_awg_delay] )
                        lna_protect_list.append( [self.channel_dict['VIDEO_PROTECT'], element[1] - self.switch_protect_delay, element[2] - int(self.rect_awg_delay/self.timebase) + self.protect_awg_delay] )
                    else:
                        pass

            return np.asarray(lna_protect_list)

        elif self.test_flag == 'test':
            if self.auto_defense == 'False':
                pass
            elif self.auto_defense == 'True':
                lna_protect_list = []
                for index, element in enumerate(p_list):
                    if element[0] == self.channel_dict['MW']:
                        lna_protect_list.append( [self.channel_dict['LNA_PROTECT'], element[1] - self.switch_protect_delay, element[2] + self.protect_delay] )
                        lna_protect_list.append( [self.channel_dict['VIDEO_PROTECT'], element[1] - self.switch_protect_delay, element[2] + self.protect_delay] )
                    # LNA_PROTECT and RECT_AWG coincide in the start position but LNA is longer at protect_delay
                    elif element[0] == self.channel_dict['AWG']:
                        lna_protect_list.append( [self.channel_dict['LNA_PROTECT'], element[1] - self.switch_protect_delay, element[2] - int(self.rect_awg_delay/self.timebase) + self.protect_awg_delay] )
                        lna_protect_list.append( [self.channel_dict['VIDEO_PROTECT'], element[1] - self.switch_protect_delay, element[2] - int(self.rect_awg_delay/self.timebase) + self.protect_awg_delay] )
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
        if self.test_flag != 'test':
            if self.auto_defense == 'False':
                pass
            elif self.auto_defense == 'True':
                problem_list = []
                # memorize index of problem elements
                problem_index = []
                # numpy arrays don't support element deletion
                no_problem_list = deepcopy(p_list.tolist())

                # there STILL can be errors
                # now compare two pulses with I and I+2 indexes, since there are two pulses SHAPER and AMP_ON; LNA_PROTECT and VIDEO_PROTECT
                # (end and start + 1)
                for index, element in enumerate(p_list[:-2]):

                    # minimal_distance_amp_lna is 0 ns now
                    if p_list[index + 2][1] - element[2] < self.minimal_distance_amp_lna:
                        problem_list.append(element)
                        problem_list.append(p_list[index + 2])
                        # memorize indexes of the problem pulses
                        problem_index.append(index)
                        problem_index.append(index + 2)

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

        elif self.test_flag == 'test':
            if self.auto_defense == 'False':
                pass
            elif self.auto_defense == 'True':            
                problem_list = []
                problem_index = []
                # numpy arrays don't support element deletion
                no_problem_list = deepcopy(p_list.tolist())

                for index, element in enumerate(p_list[:-2]):
                    # minimal_distance_amp_lna is 0 ns now
                    if p_list[index + 2][1] - element[2] < (self.minimal_distance_amp_lna):
                        problem_list.append(element)
                        problem_list.append(p_list[index + 2])
                        # memorize indexes of the problem pulses
                        problem_index.append(index)
                        problem_index.append(index + 2)

                no_problem_list = np.delete( no_problem_list, list(dict.fromkeys(problem_index)), axis = 0 ).tolist()

                if len(problem_list) == 0:
                    return self.delete_duplicates(np.asarray(no_problem_list)), np.array([[0]])
                elif len(no_problem_list) == 0:
                    return np.array([[0]]), self.delete_duplicates(np.asarray(problem_list))
                else:
                    return self.delete_duplicates(np.asarray(no_problem_list)), self.delete_duplicates(np.asarray(problem_list))

    def convert_to_bit_pulse_amp_lna(self, p_list):
        """
        A function to calculate in which time interval
        two or more different channels are on.
        All the pulses converted in an bit_array of 0 and 1, where
        1 corresponds to the time interval when the channel is on.
        The size of the bit_array is determined by the total length
        of the full pulse sequence.
        Finally, a bit_array is multiplied by a ch in order to
        calculate CH instructions for SpinAPI.
        
        It is used to check (check_short_pulses()) whether there are two AMP_ON or LNA_PROTECT pulses
        with the distanse less than 12 ns between them
        If so they are combined in one pulse by joining_pulses()

        Generally, this function is close to convert_to_bit_pulse() and other convertion
        functions
        """
        if self.test_flag != 'test':
            if self.auto_defense == 'False':
                pass
            elif self.auto_defense == 'True':
                max_pulse = np.amax(p_list[:,2])
                bit_array = np.zeros(max_pulse, dtype = np.int64)
                bit_array2 = np.zeros(max_pulse, dtype = np.int64)
                # two types of pulses: AMP_ON and SHAPER; LNA_PROTECT and VIDEO_PROTECT
                first_channel = p_list[1, 0]
                i = 0
                while i < len(p_list):
                    # convert each pulse in an array of 0 and 1,
                    # 1 corresponds to the time interval, where the channel is on
                    translation_array = np.concatenate( (np.zeros(p_list[i, 1], dtype = np.int64), \
                            np.ones(p_list[i, 2] - p_list[i, 1], dtype = np.int64), \
                            np.zeros(max_pulse - p_list[i, 2], dtype = np.int64)), axis = None)

                    if p_list[i, 0] == first_channel:
                        bit_array = bit_array | translation_array
                    else:
                        second_channel = p_list[i, 0]
                        bit_array2 = bit_array2 | translation_array

                    i += 1

                bit_array = (first_channel)*self.check_short_pulses(bit_array, first_channel)
                try:
                    bit_array2 = (second_channel)*self.check_short_pulses(bit_array2, second_channel)
                except UnboundLocalError:
                    return bit_array, bit_array2

                return bit_array, bit_array2

        elif self.test_flag == 'test':
            if self.auto_defense == 'False':
                pass
            elif self.auto_defense == 'True':            
                max_pulse = np.amax(p_list[:,2])
                bit_array = np.zeros(max_pulse, dtype = np.int64)
                bit_array2 = np.zeros(max_pulse, dtype = np.int64)
                # two types of pulses: AMP_ON and SHAPER; LNA_PROTECT and VIDEO_PROTECT
                first_channel = p_list[1, 0]
                i = 0
                while i < len(p_list):
                    # convert each pulse in an array of 0 and 1,
                    # 1 corresponds to the time interval, where the channel is on
                    translation_array = np.concatenate( (np.zeros(p_list[i, 1], dtype = np.int64), \
                            np.ones(p_list[i, 2] - p_list[i, 1], dtype = np.int64), \
                            np.zeros(max_pulse - p_list[i, 2], dtype = np.int64)), axis = None)

                    if p_list[i, 0] == first_channel:
                        bit_array = bit_array | translation_array
                    else:
                        second_channel = p_list[i, 0]
                        bit_array2 = bit_array2 | translation_array

                    i += 1

                bit_array = (first_channel)*self.check_short_pulses(bit_array, first_channel)
                try:
                    bit_array2 = (second_channel)*self.check_short_pulses(bit_array2, second_channel)
                except UnboundLocalError:
                    return bit_array, bit_array2

                return bit_array, bit_array2

    def instruction_pulse_short_lna_amp(self, np_array):
        """
        Final convertion to the pulse blaster instruction pulses
        It splits the bit_array into sequence of bit_arrays for individual pulses
        after that converts them into instructions

        We can drop pulses with channel 0 for AMP_ON and LNA_PROTECT case

        Generally, this function is close to instruction_pulse() 
        """
        if self.test_flag != 'test':
            if self.auto_defense == 'False':
                pass
            elif self.auto_defense == 'True':
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

        elif self.test_flag == 'test':
            if self.auto_defense == 'False':
                pass
            elif self.auto_defense == 'True':
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
            if channel == self.channel_dict['LNA_PROTECT'] or channel == self.channel_dict['AMP_ON'] or channel == self.channel_dict['VIDEO_PROTECT'] or \
                        channel == self.channel_dict['SHAPER']:
            ##if channel != self.channel_dict['LNA_PROTECT'] and channel != self.channel_dict['AMP_ON']:

            ##    # (min_pulse_length + 1) is 13 now
            ##    if any(1 < element < (self.min_pulse_length + 1) for element in difference) == False:
            ##        pass
            ##    else:
            ##        general.message('There are two pulses with shorter than ' + str(self.min_pulse_length*2) + ' ns distance between them')
            ##        sys.exit()
            ##else:
                if any(1 < element < (self.min_pulse_length + 1) for element in difference) == False:
                    return np_array
                else:
                    final_array = self.joining_pulses(np_array)
                    return final_array

        if self.test_flag == 'test':
            # checking where the pulses are
            one_indexes = np.argwhere(np_array == 1).flatten()
            difference = np.diff(one_indexes)

            if channel != self.channel_dict['LNA_PROTECT'] and channel != self.channel_dict['AMP_ON'] and channel != self.channel_dict['VIDEO_PROTECT'] and \
                            channel != self.channel_dict['SHAPER']:
                if any(1 < element < (self.min_pulse_length + 1) for element in difference) == False:
                    pass
                else:
                    assert(1 == 2), 'There are two pulses with shorter than ' + str(self.min_pulse_length) + ' ns distance between them'
            else:
                if any(1 < element < (self.min_pulse_length + 1) for element in difference) == False:
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
                    if counter < (self.min_pulse_length + 1):
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
        if self.test_flag != 'test':
            temp = parameter.split(' ')
            if temp[1] in self.timebase_dict:
                flag = self.timebase_dict[temp[1]]
                par_st = int(int((temp[0]))*flag + delay)
                new_parameter = str( par_st ) + ' ns'

            return new_parameter

        elif self.test_flag == 'test':
            temp = parameter.split(' ')
            if temp[1] in self.timebase_dict:
                flag = self.timebase_dict[temp[1]]
                par_st = int(int((temp[0]))*flag + delay)
                new_parameter = str( par_st ) + ' ns'
            else:
                assert(1 == 2), 'Incorrect time dimension (ns, us, ms, s)'

            return new_parameter

    def power_of_two(self, value):
        powers = []
        i = 1

        while i <= value:
            if i & value:
                powers.append( i )
            i <<= 1

        return np.log2( powers ).astype(int)

    def pulse_write(self, address, start, stop, j, j_prev):

        if self.test_flag != 'test':    
            self.device_write( address + 2 * (j - 1), byte_to_write = 4, data_to_write = start, type_of_systems = 10 )
            self.device_write( address + 1 + 2 * (j - 1), byte_to_write = 4, data_to_write = stop, type_of_systems = 10 )

            if (j_prev - j) > 0:
                for i in range(j_prev - j):
                    self.device_write( address + 2 * (i + j + 1), byte_to_write = 4, data_to_write = 0, type_of_systems = 10 )
                    self.device_write( address + 1 + 2 * (i + j + 1), byte_to_write = 4, data_to_write = 0, type_of_systems = 10 )

        if self.test_flag == 'test':
            pass

    def pulse_write_stop(self, address, start, stop, j, j_prev):

        if self.test_flag != 'test':    
            if (j_prev) > 0:
                for i in range( j_prev ):
                    self.device_write( address + 2 * (i), byte_to_write = 4, data_to_write = 0, type_of_systems = 10 )
                    self.device_write( address + 1 + 2 * (i), byte_to_write = 4, data_to_write = 0, type_of_systems = 10 )

        if self.test_flag == 'test':
            pass

    def pulse_write_full_stop(self, address, start, stop, j):

        if self.test_flag != 'test':    

            for i in range( j ):
                self.device_write( address + 2 * (i), byte_to_write = 4, data_to_write = 0, type_of_systems = 10 )
                self.device_write( address + 1 + 2 * (i), byte_to_write = 4, data_to_write = 0, type_of_systems = 10 )

        if self.test_flag == 'test':
            pass

def main():
    pass

if __name__ == "__main__":
    main()

