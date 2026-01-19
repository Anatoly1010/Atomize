#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import gc
import sys
import pyvisa
import struct
import numpy as np 
import pyqtgraph as pg
import atomize.main.local_config as lconf
import atomize.device_modules.config.config_utils as cutil
import atomize.general_modules.general_functions as general


class SR_DS345:
    #### Basic interaction functions
    def __init__(self):

        #### Inizialization
        # setting path to *.ini file
        self.path_current_directory = lconf.load_config_device()
        self.path_config_file = os.path.join(self.path_current_directory, 'SR_DS345_config.ini')

        # configuration data
        self.config = cutil.read_conf_util(self.path_config_file)
        self.specific_parameters = cutil.read_specific_parameters(self.path_config_file)

        # auxilary dictionaries
        self.trigger_channel_dict = {'CH1': 'CHAN1', 'CH2': 'CHAN2', 'CH3': 'CHAN3', 'CH4': 'CHAN4',                 'Ext': 'EXTernal', 'Line': 'LINE', 'WGen1': 'WGEN1', 'WGen2': 'WGEN2'}
        self.wavefunction_dict = {'Sin': 0, 'Sq': 1, 'Triangle': 2, 'Ramp': 3, 'Noise': 4, 'Arb': 5}
        self.modulation_wavefunction_dict = {'Single': 0, 'Ramp': 1, 'Triangle': 2, 'Sin': 3, 'Sq': 4, 'Arb': 5, 'None': 6}
        self.modulation_type_dict = {'Lin Sweep': 0, 'Log Sweep': 1, 'AM': 2, 'FM': 3, 'PM': 4, 'Burst': 5}
        self.status_dict = {'Off': 0, 'On': 1}
        self.modulation_trigger_dict = {'Single': 0, 'Internal': 1, 'External Pos': 2, 'External Neg': 3, 'Line': 4}

        self.freq_list = ['MHz', 'kHz', 'Hz', 'mHz', 'uHz']
        self.rate_freq_list = ['kHz', 'Hz', 'mHz']
        self.ampl_mode_list = ['TTL', 'ECL']

        # Limits and Ranges (depends on the exact model):
        self.wave_gen_freq_max = float(self.specific_parameters['freq_max'])
        self.wave_gen_freq_min = float(self.specific_parameters['freq_min'])

        self.f_min = pg.siFormat( self.wave_gen_freq_min, suffix = 'Hz', precision = 3, allowUnicode = False)
        self.f_max = pg.siFormat( self.wave_gen_freq_max, suffix = 'Hz', precision = 3, allowUnicode = False)

        self.max_freq_dict = {0: 30e6, 1: 30e6, 2: 100e3, 3: 100e3, 4: 10e6, 5: 10e6}


        self.ampl_max = float(self.specific_parameters['ampl_max'])
        self.ampl_min = float(self.specific_parameters['ampl_min'])
        
        self.ph_span = 0
        self.func_type = 0
        self.max_arb_points = 16300
        self.max_am_points = 10000
        self.max_fm_points = 1500
        self.max_pm_points = 4000
        self.length = 0
        self.offset = 0
        self.freq = 1e-6

        self.gpib_be = 0
        # Test run parameters
        # These values are returned by the modules in the test run 
        if len(sys.argv) > 1:
            self.test_flag = sys.argv[1]
        else:
            self.test_flag = 'None'

        if self.test_flag != 'test':
            if self.config['interface'] == 'rs232':
                try:
                    self.status_flag = 1
                    rm = pyvisa.ResourceManager()
                    self.device = rm.open_resource(self.config['serial_address'], read_termination=self.config['read_termination'],
                    write_termination=self.config['write_termination'], baud_rate=self.config['baudrate'],
                    data_bits=self.config['databits'], parity=self.config['parity'], stop_bits=self.config['stopbits'])
                    self.device.timeout = self.config['timeout'] # in ms
                    
                    try:
                        # test should be here
                        self.device_write('*CLS')
                        general.wait('50 ms')

                        """
                        # run-time checks
                        self.ampl = float(self.device_query( f"AMPL? VP" ).split("VP")[0] ) / 2
                        self.offset = float(self.device_query( f"OFFS?" ) )
                        self.freq = float(self.device_query("FREQ?"))
                        self.tr_source = int(self.device_query('TSRC?'))
                        self.func_type = int(self.device_query('FUNC?'))
                        
                        # Modulation sweep
                        self.start_freq = float(self.device_query("STFR?"))
                        self.stop_freq = float(self.device_query("SPFR?"))
                        """

                    except (pyvisa.VisaIOError, BrokenPipeError):
                        self.status_flag = 0
                        general.message(f"No connection {self.__class__.__name__}")
                        sys.exit()

                except (pyvisa.VisaIOError, BrokenPipeError):
                    general.message(f"No connection {self.__class__.__name__}")
                    self.status_flag = 0
                    sys.exit()
            elif self.config['interface'] == 'gpib':
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
                        # test should be here
                        self.status_flag = 1
                        self.device_write('*CLS')
                        general.wait('50 ms')

                        # run-time checks
                        self.ampl = float(self.device_query( f"AMPL? VP" ).split("VP")[0] ) / 2
                        self.offset = float(self.device_query( f"OFFS?" ) )
                        self.freq = float(self.device_query("FREQ?"))
                        self.tr_source = int(self.device_query('TSRC?'))
                        self.func_type = int(self.device_query('FUNC?'))
                        
                        # Modulation sweep
                        self.start_freq = float(self.device_query("STFR?"))
                        self.stop_freq = float(self.device_query("SPFR?"))

                        self.mod_type = cutil.search_keys_dictionary(self.modulation_type_dict, int(self.device_query('MTYP?')))
                        self.mod_func = cutil.search_keys_dictionary(self.modulation_wavefunction_dict, int(self.device_query('MDWF?')))

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
                sys.exit()

        elif self.test_flag == 'test':
            self.test_frequency = '500 Hz'
            self.test_arb_frequency = '1 kHz'
            self.test_mod_span_frequency = '50 Hz'
            self.function = 'Sin'
            self.mod_function = 'Sin'
            self.test_amplitude = '3 V'
            self.test_offset = '0 V'
            self.test_phase = '15 deg'
            self.mod_type = 'Lin Sweep'
            self.mod_depth = '50 %'
            self.mod_status = 'Off'
            self.test_mod_rate = '100 Hz'
            self.mod_trigger = 'Line'
            self.test_trigger_rate = '100 Hz'
            self.test_burst_count = 10
            self.test_mod_rate_divider = 10

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
                    answer = self.device.query(command)

            elif self.config['interface'] == 'rs232':
                answer = self.device.query(command)
            return answer
        else:
            general.message(f"No connection {self.__class__.__name__}")
            self.status_flag = 0
            sys.exit()

    # change for gpib
    def device_write_binary(self, value):
        if self.status_flag == 1:
            if self.config['interface'] == 'gpib':
                if self.gpib_be == 0:
                    self.device.write(value)
                else:
                    self.device.write_raw(value)
        else:
            general.message(f"No connection {self.__class__.__name__}")
            self.status_flag = 0
            sys.exit()

    #### device specific functions
    # GENERAL
    def wave_gen_name(self):
        if self.test_flag != 'test':
            answer = self.device_query('*IDN?').split('\n')[0]
            return answer
        elif self.test_flag == 'test':
            answer = self.config['name']
            return answer

    def wave_gen_frequency(self, *frequency):
        """
        FREQ // FREQ?
        1 uHz resolution. If the current waveform is NOISE an error will
        be generated and the frequency will not be changed
        """
        f_max = pg.siFormat( self.max_freq_dict[self.func_type], suffix = 'Hz', precision = 3, allowUnicode = False)
        if self.test_flag != 'test':
            if len(frequency) == 1:
                freq = pg.siEval( frequency[0] )

                if freq >= self.wave_gen_freq_min and freq <= self.max_freq_dict[self.func_type]:
                    self.device_write(f"FREQ {freq}")
                    self.freq = freq
                else:
                    general.message(f"Incorrect frequency range for {cutil.search_keys_dictionary(self.wavefunction_dict, self.func_type)}. The available range is from {self.f_min} to {f_max}")


            elif len(frequency) == 0:
                raw_answer = float(self.device_query("FREQ?"))
                self.freq = raw_answer
                answer = pg.siFormat( raw_answer, suffix = 'Hz', precision = 12, allowUnicode = False)
                return answer

        elif self.test_flag == 'test':
            if len(frequency) == 1:
                freq = pg.siEval( frequency[0] )
                temp = frequency[0].split(" ")
                scaling = temp[1]

                assert(scaling in self.freq_list), f"Incorrect SI suffix. Available options are {self.freq_list}"

                assert( freq >= self.wave_gen_freq_min and freq <= self.max_freq_dict[self.func_type]), f"Incorrect frequency range for {cutil.search_keys_dictionary(self.wavefunction_dict, self.func_type)}. The available range is from {self.f_min} to {f_max}"
                self.freq = freq

            elif len(frequency) == 0:
                answer = self.test_frequency
                return answer
            else:
                assert(1 == 2), "Incorrect argument; frequency: float + [' MHz', ' kHz', ' Hz', ' mHz', ' uHz']"

    def wave_gen_function(self, *function):
        """
        FUNC i
        FUNC?
        'Sin': 0, 'Sq': 1, 'Triangle': 2, 'Ramp': 3, 'Noise': 4, 'Arb': 5
        """

        if self.test_flag != 'test':
            if len(function) == 1:
                func = str(function[0])
                flag = self.wavefunction_dict[func]
                f_max = pg.siFormat( self.max_freq_dict[flag], suffix = 'Hz', precision = 3, allowUnicode = False)

                if self.freq >= self.wave_gen_freq_min and self.freq <= self.max_freq_dict[self.func_type]:
                    self.device_write(f"FUNC {flag}")
                    self.func_type = flag
                else:
                    general.message(f"Incorrect frequency range for {cutil.search_keys_dictionary(self.wavefunction_dict, flag)}. The available range is from {self.f_min} to {f_max}")

            elif len(function) == 0:
                raw_answer = int(self.device_query('FUNC?'))
                self.func_type = raw_answer
                answer = cutil.search_keys_dictionary(self.wavefunction_dict, raw_answer)
                return answer

        elif self.test_flag == 'test':
            if  len(function) == 1:
                func = str(function[0])
                flag = self.wavefunction_dict[func]
                f_max = pg.siFormat( self.max_freq_dict[flag], suffix = 'Hz', precision = 3, allowUnicode = False)

                assert(func in self.wavefunction_dict), f"Invalid waveform generator function. Available options are {list(self.wavefunction_dict.keys())}"

                assert( self.freq >= self.wave_gen_freq_min and self.freq <= self.max_freq_dict[flag]), f"Incorrect frequency range for {cutil.search_keys_dictionary(self.wavefunction_dict, flag)}. The available range is from {self.f_min} to {f_max}"

                self.func_type = flag

            elif len(function) == 0:
                answer = self.function
                return answer
            else:
                assert(1 == 2), f"Invalid argument; function: {list(self.wavefunction_dict.keys())}"

    def wave_gen_amplitude(self, *amplitude):
        """
        VPP amplitude
        Note that the peak AC voltage (Vpp/2)
        plus the DC offset voltage must be less than 5 Volts
        AMPL? VP
        AMPL 1.00VP
        """
        if self.test_flag != 'test':
            ampl_max = pg.siFormat( self.ampl_max, suffix = 'V', precision = 3, allowUnicode = False)
            ampl_min = pg.siFormat( self.ampl_min, suffix = 'V', precision = 3, allowUnicode = False)
            if len(amplitude) == 1:
                temp = amplitude[0]
                try:
                    val = pg.siEval(temp)
                    self.ampl = val / 2
                    if (( self.ampl + self.offset ) <= self.ampl_max) and (( self.ampl + self.offset ) >= self.ampl_min):
                        self.device_write(f"AMPL {val}VP")
                    else:
                        general.message(f"Invalid amplitude range. The available range is from {ampl_min} to {ampl_max}. Check the amplitude and offset")
                except ValueError:
                    self.device_write(f"A{temp}")
                    if temp == 'TTL':
                        self.ampl = 5
                        self.offset = 2.5
                    elif temp == 'ECL':
                        self.ampl = 1
                        self.offset = -1.3

            elif len(amplitude) == 0:
                raw_answer = float(self.device_query( f"AMPL? VP" ).split("VP")[0] )
                answer = pg.siFormat( raw_answer, suffix = 'V', precision = 3, allowUnicode = False)
                self.ampl = raw_answer / 2
                return answer

        elif self.test_flag == 'test':
            if len(amplitude) == 1:
                temp = amplitude[0]
                try:
                    val = pg.siEval(temp)
                    self.ampl = val / 2
                    assert(( self.ampl + self.offset ) <= self.ampl_max) and (( self.ampl + self.offset ) >= self.ampl_min), f"Invalid amplitude range. The available range is from {ampl_min} to {ampl_max}. Check the amplitude and offset"
                except ValueError:
                    assert( temp in self.ampl_mode_list ), f"Invalid argument; amplitude: float + [' V', ' mV'] or amplitude: ['TTL', 'ECL']"
                    if temp == 'TTL':
                        self.ampl = 5
                        self.offset = 2.5
                    elif temp == 'ECL':
                        self.ampl = 1
                        self.offset = -1.3

            elif len(amplitude) == 0:
                answer = self.test_amplitude
                return answer
            else:
                assert(1 == 2), f"Invalid argument; amplitude: float + [' V', ' mV'] or amplitude: ['TTL', 'ECL']"

    def wave_gen_offset(self, *offset):
        """
        Note that the peak AC voltage (Vpp/2)
        plus the DC offset voltage must be less than 5 Volts
        OFFS?
        OFFS 1.00
        """
        if self.test_flag != 'test':
            if len(offset) == 1:
                temp = offset[0].split(" ")
                val = pg.siEval(temp)
                self.offset = val
                if (( self.ampl + self.offset ) <= self.ampl_max) and (( self.ampl + self.offset ) >= self.ampl_min):
                    self.device_write(f"OFFS {val}")
                else:
                    general.message(f"Invalid amplitude range. The available range is from {ampl_min} to {ampl_max}. Check the amplitude and offset")

            elif len(offset) == 0:
                raw_answer = float(self.device_query( "OFFS?" ) )
                answer = pg.siFormat( raw_answer, suffix = 'V', precision = 3, allowUnicode = False)
                self.offset = raw_answer
                return answer

        elif self.test_flag == 'test':
            if len(offset) == 1:
                temp = offset[0].split(" ")
                val = pg.siEval(temp)
                self.offset = val
                assert(( self.ampl + self.offset ) <= self.ampl_max) and (( self.ampl + self.offset ) >= self.ampl_min), f"Invalid amplitude range. The available range is from {ampl_min} to {ampl_max}. Check the amplitude and offset"

            elif len(offset) == 0:
                answer = self.test_offset
                return answer
            else:
                assert(1 == 2), "Incorrect argument; offset: float + [' V', ' mV']"

    def wave_gen_phase(self, *phase):
        """
        PCLR -> 0
        PHSE x
        PHSE?
        0.001 degree resolution and may range from 0.001 to 7199.999 degrees.
        This command will produce an error if the function is set to either NOISE or
        ARB, or if a frequency sweep, FM, or phase modulation is enabled.
        """
        if len(phase) == 1:
            ph = round( float(phase[0]), 3 )
            if self.test_flag != 'test':
                if ph == 0:
                    self.device_write( f"PCLR" )
                else:
                    self.device_write( f"PHSE {ph}" )
            elif self.test_flag == 'test':
                assert( ph >= 0 and ph <= 7199.999 ), f"Incorrect phase. The available range is from 0 deg to 7199.999 deg"

        elif len(phase) == 0:
            if self.test_flag != 'test':
                raw_answer = float( self.device_query( f"PHSE?" ) )
            elif self.test_flag == 'test':
                raw_answer = self.test_phase
            
            return f"{raw_answer} deg"

        else:
            if self.test_flag == 'test':
                assert( 1 == 2 ), f"Incorrect argument; phase: float [0 - 7199.999]"

    # MODULATION
    def wave_gen_modulation_function(self, *function):
        """
        MDWF i
        MDWF?
        Not all functions are available for all modulation types
        """
        if len(function) == 1:
            func = str(function[0])
            flag = self.modulation_wavefunction_dict[func]
            if self.test_flag != 'test':

                if func == 'Sin' or func == 'Sq' or func == 'Arb':
                    if self.mod_type != 'Lin Sweep' or self.mod_type != 'Log Sweep':
                        self.device_write(f"MDWF {flag}")
                    else:
                        general.message(f"Incorrect modulation function for {self.mod_type} modulation type. ['Single': 'Lin Sweep', 'Log Sweep']; ['Ramp', 'Triangle': 'Lin Sweep', 'Log Sweep', 'AM', 'FM', 'PM']; ['Sin', 'Sq', 'Arb': 'AM', 'FM', 'PM']; ['None': 'Burst']")
                elif func == 'Single':
                    if self.mod_type != 'AM' or self.mod_type != 'FM' or self.mod_type != 'PM':
                        self.device_write(f"MDWF {flag}")
                    else:
                        general.message(f"Incorrect modulation function for {self.mod_type} modulation type. ['Single': 'Lin Sweep', 'Log Sweep']; ['Ramp', 'Triangle': 'Lin Sweep', 'Log Sweep', 'AM', 'FM', 'PM']; ['Sin', 'Sq', 'Arb': 'AM', 'FM', 'PM']; ['None': 'Burst']")
                elif self.mod_type == 'Burst':
                    self.device_write(f"MDWF {6}")
                else:
                    self.device_write(f"MDWF {flag}")

            elif self.test_flag == 'test':
                assert(func in self.modulation_wavefunction_dict), f"Invalid modulation function. Available options are {list(self.modulation_wavefunction_dict.keys())}"

            self.mod_func = func

        elif len(function) == 0:
            if self.test_flag != 'test':            
                raw_answer = int(self.device_query('MDWF?'))
                
                answer = cutil.search_keys_dictionary(self.modulation_wavefunction_dict, raw_answer)
                self.mod_func_flag = answer
                return answer
            elif self.test_flag == 'test':
                answer = self.mod_function
                return answer
        else:
            if self.test_flag == 'test':
                assert( 1 == 2 ), f"Incorrect argument; function: {list(self.modulation_wavefunction_dict.keys())}"

    def wave_gen_modulation_type(self, *type):
        """
        MTYP i
        MTYP?
        ['Lin Sweep', 'Log Sweep', 'AM', 'FM', 'PM', 'Burst']
        """
        if len(type) == 1:
            func = str(type[0])
            flag = self.modulation_type_dict[func]
            if self.test_flag != 'test':

                if func == 'Lin Sweep' or func == 'Log Sweep':
                    if self.mod_func == 'Single' or self.mod_func == 'Ramp' or self.mod_func == 'Triangle':
                        self.device_write(f"MTYP {flag}")
                    else:
                        general.message(f"Incorrect modulation function for {self.mod_func} modulation type. ['Lin Sweep', 'Log Sweep': 'Single']; ['Lin Sweep', 'Log Sweep', 'AM', 'FM', 'PM': 'Ramp', 'Triangle']; ['AM', 'FM', 'PM': 'Sin', 'Sq', 'Arb']; ['Burst': 'None']")
                elif func == 'AM' or func == 'FM' or func == 'PM':
                    if self.mod_func != 'Single':
                        self.device_write(f"MTYP {flag}")
                    else:
                        general.message(f"Incorrect modulation function for {self.mod_func} modulation type. ['Lin Sweep', 'Log Sweep': 'Single']; ['Lin Sweep', 'Log Sweep', 'AM', 'FM', 'PM': 'Ramp', 'Triangle']; ['AM', 'FM', 'PM': 'Sin', 'Sq', 'Arb']; ['Burst': 'None']")
                elif func == 'Burst':
                    self.device_write(f"MTYP {flag}")
                    self.device_write(f"MDWF {6}")
                else:
                    self.device_write(f"MTYP {flag}")

            elif self.test_flag == 'test':
                assert(func in self.modulation_type_dict), f"Invalid modulation function. Available options are {list(self.modulation_type_dict.keys())}"
            
            self.mod_type = func

        elif len(type) == 0:
            if self.test_flag != 'test':            
                raw_answer = int(self.device_query('MTYP?'))
                answer = cutil.search_keys_dictionary(self.modulation_type_dict, raw_answer)
                return answer
            elif self.test_flag == 'test':
                answer = self.mod_type
                return answer

        else:
            if self.test_flag == 'test':
                assert( 1 == 2 ), f"Incorrect argument; type: {list(self.modulation_type_dict.keys())}"

    def wave_gen_modulation_depth(self, *depth):
        """
        sets the AM modulation depth to i percent ( 0 to 100
        %). If i is negative the modulation is set to double sideband suppressed carrier modulation (DSBSC) with i % modulation
        DPTH
        DPTH?
        """
        if len(function) == 1:
            val = int(depth[0])
            if self.test_flag != 'test':
                self.device_write(f"DPTH {val}")
            elif self.test_flag == 'test':
                assert( (val >= -100) and (val <= 100) ), f"Invalid modulation depth range. The available range is from -100 % to 100 %"

        elif len(type) == 0:
            if self.test_flag != 'test':            
                raw_answer = int(self.device_query('DPTH?'))
                return f"{raw_answer} %"
            elif self.test_flag == 'test':
                answer = self.mod_depth
                return answer

        else:
            if self.test_flag == 'test':
                assert( 1 == 2 ), f"Incorrect argument; depth: int [-100 - 100]"

    def wave_gen_modulation_frequency_span(self, *span):
        """
        The maximum value of x
        is limited so that the frequency is never less than or equal to zero or greater
        than that allowed for the selected function. The FM waveform will be centered at the front panel frequency and have a deviation of ±span/2. 

        FDEV x
        FDEV?
        """
        if len(span) == 1:
            freq = pg.siEval( span[0] )

            if self.test_flag != 'test':
                if self.func_type == 0 or self.func_type == 1:
                    self.device_write( f"FDEV {freq}" )
                elif self.func_type == 2 or self.func_type == 3:
                    if ((self.freq - freq/2) >= self.wave_gen_freq_min and (self.freq + freq/2) <= self.freq_max_ramp_tri):
                        self.device_write( f"FDEV {freq}" )
                    else:
                        general.message(f"Incorrect frequency range. The available range is from {self.f_min} to {self.f_max_r_tri}")
                elif self.func_type == 4 or self.func_type == 5:
                    if ((self.freq - freq/2) >= self.wave_gen_freq_min and (self.freq + freq/2) <= self.freq_max_noise_arb):
                        self.device_write( f"FDEV {freq}" )
                    else:
                        general.message(f"Incorrect frequency range. The available range is from {self.f_min} to {self.f_max_n_arb}")

            elif self.test_flag == 'test':
                temp = span[0].split(" ")
                scaling = temp[1]
                assert(scaling in self.freq_list), f"Incorrect SI suffix. Available options are {self.freq_list}"
                assert( (self.freq - freq/2) >= self.wave_gen_freq_min and (self.freq + freq/2) <= self.wave_gen_freq_max), f"Incorrect frequency range. The available range is from {self.f_min} to {self.f_max}"

        elif len(span) == 0:
            if self.test_flag != 'test':
                raw_answer = float(self.device_query("FDEV?"))
                answer = pg.siFormat( raw_answer, suffix = 'Hz', precision = 12, allowUnicode = False)
                return answer
            elif self.test_flag == 'test':
                return self.test_mod_span_frequency

        else:
            if self.test_flag == 'test':
                assert(1 == 2), "Incorrect argument; span: float + [' MHz', ' kHz', ' Hz', ' mHz', ' uHz']"

    def wave_gen_modulation_phase_span(self, *span):
        """
        The PDEV command sets the span of the phase modulation to x degrees. x
        may range from 0 to 7199.999 degrees. Note that the phase shift ranges
        from -span/2 to span/2. The PDEV? query returns the current phase shift.

        PDEV x
        'float deg'
        """
        if len(span) == 1:
            ph = round( float(phase[0]), 3 )
            self.ph_span = ph
            if self.test_flag != 'test':
                self.device_write( f"PDEV {ph}" )
            elif self.test_flag == 'test':
                assert( ph >= 0 and ph <= 7199.999 ), f"Incorrect phase span. The available range is from 0 deg to 7199.999 deg"
        
        elif len(span) == 0:
            if self.test_flag != 'test':
                raw_answer = self.ph_span
            elif self.test_flag == 'test':
                raw_answer = self.ph_span
            return f"{raw_answer} deg"

        else:
            if self.test_flag == 'test':
                assert( 1 == 2 ), f"Incorrect argument; span: float [0 - 7199.999]"

    def wave_gen_modulation_status(self, *status):
        """
        The MENA command enables modulation if i=1 and disables modulation if i =
        0. If any of the modulation parameters are incompatible with the current instrument settings an error will be generated.
        ['On', 'Off']
        MENA
        MENA?
        """
        if len(status) == 1:
            func = str(status[0])
            flag = self.status_dict[func]
            if self.test_flag != 'test':
                if self.func_type != 4:
                    self.device_write(f"MENA {flag}")
                else:
                    general.message(f"Modulation is not available for [Noise']. The current function is {cutil.search_keys_dictionary(self.wavefunction_dic, self.func_type)}")

            elif self.test_flag == 'test':
                assert(func in self.status_dict), f"Invalid modulation regime. Available options are {list(self.status_dict.keys())}"

        elif len(status) == 0:
            if self.test_flag != 'test':            
                raw_answer = int(self.device_query('MENA?'))
                answer = cutil.search_keys_dictionary(self.status_dict, raw_answer)
                return answer
            elif self.test_flag == 'test':
                answer = self.mod_status
                return answer

        else:
            if self.test_flag == 'test':
                assert( 1 == 2 ), f"Incorrect argument; status: {list(self.status_dict.keys())}"

    def wave_gen_modulation_frequency_sweep(self, **kargs):
        """
        start   STFR x
        stop    SPFR x 
        center  SPCF x

        If the stop frequency is less than the start frequency
        (the STFR command) a downward sweep from maximum to minimum frequency will be generated.

        'start' = 'float + SI suffix'
        'stop' = 'float + SI suffix'
        f"START FREQ: {f_start}; STOP FREQ: {f_stop}"
        """
        if len(kargs) == 3:
            self.start_freq = pg.siEval( kargs['start'] )
            self.stop_freq = pg.siEval( kargs['stop'] )
            if self.test_flag != 'test':
                if self.func_type == 0 or self.func_type == 1:
                    self.device_write( f"STFR {self.start_freq}" )
                    self.device_write( f"SPFR {self.stop_freq}" )
                elif self.func_type == 2 or self.func_type == 3:
                    if ((self.start_freq >= self.wave_gen_freq_min) and (self.start_freq <= self.freq_max_ramp_tri)) and ((self.stop_freq >= self.wave_gen_freq_min) and (self.stop_freq <= self.freq_max_ramp_tri)):
                        self.device_write( f"STFR {self.start_freq}" )
                        self.device_write( f"SPFR {self.stop_freq}" )
                    else:
                        general.message(f"Incorrect frequency range. The available range is from {self.f_min} to {self.f_max_r_tri}")
                elif self.func_type == 4 or self.func_type == 5:
                    if ((self.start_freq >= self.wave_gen_freq_min) and (self.start_freq <= self.freq_max_noise_arb)) and ((self.stop_freq >= self.wave_gen_freq_min) and (self.stop_freq <= self.freq_max_noise_arb)):
                        self.device_write( f"STFR {self.start_freq}" )
                        self.device_write( f"SPFR {self.stop_freq}" )
                    else:
                        general.message(f"Incorrect frequency range. The available range is from {self.f_min} to {self.f_max_n_arb}")

            elif self.test_flag == 'test':
                temp_1 = kargs['start'].split(" ")
                temp_2 = kargs['stop'].split(" ")
                scaling_1 = temp_1[1]
                scaling_2 = temp_2[1]
                assert( (scaling_1 and scaling_2) in self.freq_list ), f"Incorrect SI suffix. Available options are {self.freq_list}"

                assert(self.start_freq >= self.wave_gen_freq_min and self.start_freq <= self.wave_gen_freq_max), f"Incorrect start frequency. The available range is from {self.f_min} to {self.f_max}"
                assert(self.stop_freq >= self.wave_gen_freq_min and self.stop_freq <= self.wave_gen_freq_max), f"Incorrect stop frequency. The available range is from {self.f_min} to {self.f_max}"

        elif len(kargs) == 0:
            f_start = pg.siFormat( self.start_freq, suffix = 'Hz', precision = 12, allowUnicode = False)
            f_stop = pg.siFormat( self.stop_freq, suffix = 'Hz', precision = 12, allowUnicode = False)
            return f"START FREQ: {f_start}; STOP FREQ: {f_stop}"
        else:
            if self.test_flag == 'test':
                assert( 1 == 2 ), f"Incorrect kargs; start: float + [' MHz', ' kHz', ' Hz', ' mHz', ' uHz'] , stop: float + [' MHz', ' kHz', ' Hz', ' mHz', ' uHz']"

    def wave_gen_modulation_rate(self, *rate):
        """
        The RATE command sets the modulation rate to x Hertz. x is rounded to 2
        significant digits and may range from 0.001 Hz to 10 kHz. The RATE? query
        returns the current modulation rate.
        RATE x
        RATE?
        'float SI suffix'
        """
        if len(rate) == 1:
            freq = pg.siEval( rate[0] )

            if self.test_flag != 'test':
                self.device_write( f"RATE {freq}" )

            elif self.test_flag == 'test':
                temp = rate[0].split(" ")
                scaling = temp[1]
                assert(scaling in self.rate_freq_list), f"Incorrect SI suffix. Available options are {self.rate_freq_list}"
                assert( freq >= 0.001 and freq <= 10e3 ), f"Incorrect frequency rate range. The available range is from 1 mHz to 10 kHz"

        elif len(rate) == 0:
            if self.test_flag != 'test':
                raw_answer = float(self.device_query("RATE?"))
                answer = pg.siFormat( raw_answer, suffix = 'Hz', precision = 7, allowUnicode = False)
                return answer
            elif self.test_flag == 'test':
                return self.test_mod_rate

        else:
            if self.test_flag == 'test':
                assert(1 == 2), "Incorrect argument; rate: float + [' kHz', ' Hz', ' mHz']"

    def wave_gen_modulation_trigger_source(self, *tr_type):
        """
        The TSRC command sets the trigger source for bursts and sweeps to i. 
        TSRC i
        TSRC?
        """
        if len(function) == 1:
            func = str(function[0])
            flag = self.modulation_trigger_dict[func]
            self.tr_source = flag
            if self.test_flag != 'test':
                self.device_write(f"TSRC {flag}")
            elif self.test_flag == 'test':
                assert(func in self.modulation_trigger_dict), f"Invalid trigger source. Available options are {list(self.modulation_trigger_dict.keys())}"

        elif len(function) == 0:
            if self.test_flag != 'test':            
                raw_answer = int(self.device_query('TSRC?'))
                self.tr_source = raw_answer
                answer = cutil.search_keys_dictionary(self.modulation_trigger_dict, raw_answer)
                return answer
            elif self.test_flag == 'test':
                answer = self.mod_trigger
                return answer
        else:
            if self.test_flag == 'test':
                assert( 1 == 2 ), f"Incorrect argument; tr_type: {list(self.modulation_trigger_dict.keys())}"

    def wave_gen_modulation_trigger_rate(self, *rate):
        """
        The TRAT command sets the trigger rate for internally triggered single
        sweeps and bursts to x Hertz. x is rounded to two significant digits and may
        range from 0.001 Hz to 10 kHz. The TRAT? query returns the current trigger
        rate.
        TRAT // TRAT?
        'float + SI suffix'
        """
        if len(rate) == 1:
            freq = pg.siEval( rate[0] )

            if self.test_flag != 'test':
                self.device_write( f"TRAT {freq}" )

            elif self.test_flag == 'test':
                temp = rate[0].split(" ")
                scaling = temp[1]
                assert(scaling in self.rate_freq_list), f"Incorrect SI suffix. Available options are {self.rate_freq_list}"
                assert( freq >= 0.001 and freq <= 10e3 ), f"Incorrect trigger rate range. The available range is from 1 mHz to 10 kHz"

        elif len(rate) == 0:
            if self.test_flag != 'test':
                raw_answer = float(self.device_query("TRAT?"))
                answer = pg.siFormat( raw_answer, suffix = 'Hz', precision = 3, allowUnicode = False)
                return answer
            elif self.test_flag == 'test':
                return self.test_trigger_rate

        else:
            if self.test_flag == 'test':
                assert(1 == 2), "Incorrect argument; rate: float + [' kHz', ' Hz', ' mHz']"

    def wave_gen_modulation_trigger(self):
        """
        The *TRG command triggers a burst or single sweep. The trigger source
        must be set to SINGLE.
        """
        if self.test_flag != 'test':
            if self.tr_source == 0:
                self.device_write( "*TRG" )
            else:
                general.message( "The trigger source should be set to 'Single" )

    def wave_gen_modulation_burst_count(self, *count):
        """
        The BCNT command sets the burst count to i (1 to 30000). The maximum
        value of i is limited such that the burst time does not exceed 500s (that is, the
        burst count * waveform period <= 500s). The BCNT? query returns the current burst count.
        """
        if len(count) == 1:
            b_count = int(count[0])
            if self.test_flag != 'test':
                self.device_write( f"BCNT {b_count}" )
            elif self.test_flag == 'test':
                assert( b_count >= 1 and b_count <= 30000 ), f"Incorrect burst count. The available range is from 1 to 30000"
                assert( b_count * 1 / self.freq <= 500 ), f"The burst count * waveform period should be less than 500 s. Current value is {round( b_count / self.freq, 2 )}"

        elif len(count) == 0:
            if self.test_flag != 'test':
                raw_answer = int( self.device_query( f"BCNT?" ) )
            elif self.test_flag == 'test':
                raw_answer = self.test_burst_count
            
            return raw_answer

        else:
            if self.test_flag == 'test':
                assert( 1 == 2 ), f"Incorrect argument; count: int [1 - 30000]"

    # ARBITRARY
    def wave_gen_arbitrary_function_data(self, p_list):
        """
        The data is sent as 16 bit binary data words. The data
        must be followed by a 16 bit checksum to ensure data integrity
        The checksum is the 16bit sum of the data words that have been sent. If the data sent is valid and the DS345's function is set to ARB the
        waveform will automatically be output. Otherwise, the function must be set to
        ARB to output the downloaded waveform.
        1) LDWF? 0,points
        2) Wait until the DS345 returns "1" indicating that it is ready to receive data.
        3) Send the waveform data (discussed below). There should be j data points sent
        4) Send the 16 bit checksum (the sum of j data points).

        The waveform data is send as 16 bit binary data. In point mode each data
        point consists of a 16 bit amplitude word. Each value should be in the range
        -2047 to +2047

        """
        self.length = len(p_list)
        if self.test_flag != 'test':
            p_list_int = np.asarray( np.asarray(p_list) * 2047, dtype = np.int16)
            total = np.sum(p_list_int, dtype = np.int16)
            
            total = total & 0xFFFF

            esb_answer = self._error_check()

            binary_payload = struct.pack(f'<{self.length}h', *(p_list_int))
            binary_payload += struct.pack('<h', total)

            answer = int( self.device_query(f"LDWF? 0,{self.length}" ) )

            if answer == 1:
                #self.device_write_binary_16_sign('', np.append(p_list_int, total))
                self.device_write_binary(binary_payload)

            esb_answer = self._error_check()
            if esb_answer == 0:
                pass
            else:
                general.message("Incorrect arbitrary waveform")

        elif self.test_flag == 'test':
            assert( self.length <= self.max_arb_points), f"Incorrect number of points. The maximum available value is {self.max_arb_points}"
            for i in range( self.length ):
                assert( p_list[i] >= -1 and p_list[i] <= 1 ), f"Incorrect point {i}. The available range is from -1 to 1"

    def wave_gen_arbitrary_frequency(self, *frequency):
        """
        The FSMP command sets the arbitrary waveform sampling frequency to x.
        This frequency determines the rate at which each arbitrary waveform point is
        output. That is, each point in the waveform is played for a time equal to 1/
        FSMP. The allowed values are 40 MHz/N where N is an integer between 1
        and 2^34-1. If x is not an exact divisor of 40 MHz the value will be rounded to
        the nearest exact frequency.. The FSMP? query returns the current arbitrary
        waveform sampling frequency.
        """
        if len(frequency) == 1:
            freq = pg.siEval( frequency[0] )
            if self.test_flag != 'test':
                self.device_write( f"FSMP {freq}" )
            elif self.test_flag == 'test':
                temp = span[0].split(" ")
                scaling = temp[1]
                assert(scaling in self.freq_list), f"Incorrect SI suffix. Available options are {self.freq_list}"
                assert( (freq >= 0.01) and (freq <= self.wave_gen_freq_max)), f"Incorrect frequency range. The available range is from 10 mHz to {self.f_max}"

        elif len(span) == 0:
            if self.test_flag != 'test':
                raw_answer = float(self.device_query("FSMP?"))
                answer = pg.siFormat( raw_answer, suffix = 'Hz', precision = 12, allowUnicode = False)
                return answer
            elif self.test_flag == 'test':
                return self.test_arb_frequency

        else:
            if self.test_flag == 'test':
                assert(1 == 2), "Incorrect argument; span: float + [' MHz', ' kHz', ' Hz', ' mHz', ' uHz']"            

    def wave_gen_arbitrary_number_of_points(self):
        return self.length

    def wave_gen_arbitrary_amplitude_modulation(self, p_list):
        """
        This value is the fraction of front panel amplitude to be output.
        16 bit integer
        When modulation is enabled each modulation point takes N*0.3µs to execute, where N is the arbitrary modulation rate divider (see the AMRT command

        The arbitrary
        waveform must be downloaded via the AMOD? query. If no waveform has
        been downloaded and modulation is enabled with the waveform set to ARB
        an error will be generated
        """
        if self.test_flag != 'test':
            p_list_int = np.asarray( np.asarray(p_list) * 2**15, dtype = np.int16 )
            total = np.sum(p_list_int)

            total = total & 0xFFFF

            binary_payload = struct.pack(f'<{self.length}h', *(p_list_int))
            binary_payload += struct.pack('<h', total)

            answer = int( self.device_query(f"AMOD? {len(p_list)}" ) )
            if answer == 1:
                self.device_write_binary(binary_payload)

            esb_answer = self._error_check()

            if esb_answer == 0:
                pass
            else:
                general.message("Incorrect arbitrary amplitude modulation")

        elif self.test_flag == 'test':
            assert( len(p_list) <= self.max_am_points), f"Incorrect number of points. The maximum available value is {self.max_am_points}"
            for i in range( len(p_list) ):
                assert( p_list[i] >= -1 and p_list[i] <= 1 ), f"Incorrect point {i}. The available range is from -1 to 1"

    def wave_gen_arbitrary_frequency_modulation(self, p_list):
        """
        This value is the fraction of front panel amplitude to be output.
        32 bit integer
        value = 232*(frequency/40 MHz)
        0 to 2**32
        When modulation is enabled each modulation point
        takes N*2.0µs to execute, where N is the arbitrary modulation rate divider
        (see the AMRT command)
        """
        if self.test_flag != 'test':
            p_list_int = np.asarray( np.asarray(p_list) * 2**32, dtype = np.int32 )
            total = np.sum(p_list_int)

            total = total & (2**32 - 1)

            binary_payload = struct.pack(f'<{self.length}h', *(p_list_int))
            binary_payload += struct.pack('<h', total)

            answer = int( self.device_query(f"AMOD? {len(p_list)}" ) )
            if answer == 1:
                self.device_write_binary(binary_payload)

            esb_answer = self._error_check()

            if esb_answer == 0:
                pass
            else:
                general.message("Incorrect arbitrary frequency modulation")

        elif self.test_flag == 'test':
            assert( len(p_list) <= self.max_fm_points), f"Incorrect number of points. The maximum available value is {self.max_fm_points}"
            for i in range( len(p_list) ):
                assert( p_list[i] >= 0 and p_list[i] <= 1 ), f"Incorrect point {i}. The available range is from 0 to 1"

    def wave_gen_arbitrary_phase_modulation(self, p_list):
        """
        This value is the phase shift
        to be made relative to the current phase. The values may range from -180°
        to +180°.
        32 bit integer
        When modulation is enabled each modulation point takes
        N*0.5µs to execute, where N is the arbitrary modulation rate divider (see the
        AMRT command
        """
        if self.test_flag != 'test':
            p_list_int = np.asarray( np.asarray(p_list) * 2**31, dtype = np.int32 )
            total = np.sum(p_list_int)
            
            total = total & (2**32 - 1)

            binary_payload = struct.pack(f'<{self.length}h', *(p_list_int))
            binary_payload += struct.pack('<h', total)

            answer = int( self.device_query(f"AMOD? {len(p_list)}" ) )
            if answer == 1:
                self.device_write_binary(binary_payload)

            esb_answer = self._error_check()

            if esb_answer == 0:
                pass
            else:
                general.message("Incorrect arbitrary phase modulation")

        elif self.test_flag == 'test':
            assert( len(p_list) <= self.max_pm_points), f"Incorrect number of points. The maximum available value is {self.max_pm_points}"
            for i in range( len(p_list) ):
                assert( p_list[i] >= -1 and p_list[i] <= 1 ), f"Incorrect point {i}. The available range is from -1 to 1"

    def wave_gen_arbitrary_modulation_rate_divider(self, *rate):
        """
        The AMRT command sets the arbitrary modulation rate divider to i.
        i may range from 1 to 2^23-1. This controls the rate at which arbitrary modulations
        are generated. Arbitrary AM takes 0.3 µs per point, arb FM takes 2 µs per
        point, and arb PM takes 0.5 µs per point
        When modulation is enabled each modulation point takes N*0.5µs to execute
        """
        if len(rate) == 1:
            rt = int(rate[0])
            if self.test_flag != 'test':
                self.device_write( f"AMRT {rt}" )
            elif self.test_flag == 'test':
                assert( rt >= 1 and rt <= (2**23 - 1) ), f"Incorrect rate divider. The available range is from 1 to (2^23 - 1)"

        elif len(rate) == 0:
            if self.test_flag != 'test':
                raw_answer = int( self.device_query( f"AMRT?" ) )
            elif self.test_flag == 'test':
                raw_answer = self.test_mod_rate_divider
            return raw_answer

        else:
            if self.test_flag == 'test':
                assert( 1 == 2 ), f"Incorrect argument; rate: int [1 - 2^23 ]"

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

    def _error_check(self):
        """
        The *ESR common command reads the value of the standard event status
        register. If the parameter i is present the value of bit i is returned (0 or 1).
        Reading this register will clear it while reading bit i will clear just bit i.
        bit 4: Execution err Set by an out of range parameter, or non-completion of
        some command due a condition such as an incorrect waveform type
        """
        if self.test_flag != 'test':
            return int( self.device_query("*ESR? 4").split('\n')[0] )


def main():
    pass

if __name__ == "__main__":
    main()
