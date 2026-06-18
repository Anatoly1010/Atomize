#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import gc
import sys
import pyvisa
import numpy as np
import pyqtgraph as pg
from pyvisa.constants import StopBits, Parity
import atomize.main.local_config as lconf
import atomize.device_modules.config.config_utils as cutil
import atomize.general_modules.general_functions as general

class SR_865a:
    #### Basic interaction functions
    def __init__(self):

        #### Inizialization
        # setting path to *.ini file
        self.path_current_directory = lconf.load_config_device()
        self.path_config_file = os.path.join(self.path_current_directory, 'SR_865a_config.ini')

        # configuration data
        self.config = cutil.read_conf_util(self.path_config_file)
        self.specific_parameters = cutil.read_specific_parameters(self.path_config_file)

        # auxilary dictionaries
        self.sensitivity_dict = {'1 nV': 27, '2 nV': 26, '5 nV': 25, '10 nV': 24, '20 nV': 23, '50 nV': 22,
                            '100 nV': 21, '200 nV': 20, '500 nV': 19, '1 uV': 18, '2 uV': 17, '5 uV': 16,
                            '10 uV': 15, '20 uV': 14, '50 uV': 13, '100 uV': 12, '200 uV': 11, '500 uV': 10, 
                            '1 mV': 9, '2 mV': 8, '5 mV': 7, '10 mV': 6, '20 mV': 5, '50 mV': 4,
                            '100 mV': 3, '200 mV': 2, '500 mV': 1, '1 V': 0};
        self.helper_sens_list = [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000]
        self.timeconstant_dict = {'1 us': 0, '3 us': 1, '10 us': 2, '30 us': 3, '100 us': 4, '300 us': 5,
                            '1 ms': 6, '3 ms': 7, '10 ms': 8, '30 ms': 9, '100 ms': 10, '300 ms': 11,
                            '1 s': 12, '3 s': 13, '10 s': 14, '30 s': 15, '100 s': 16, '300 s': 17, 
                            '1 ks': 18, '3 ks': 19, '10 ks': 20, '30 ks': 21};
        self.helper_tc_list = [1, 3, 10, 30, 100, 300, 1000]
        self.ref_mode_dict = {'Internal': 0, 'External': 1, 'Dual': 2, 'Chop': 3}
        self.ref_slope_dict = {'Sine': 0, 'PosTTL': 1, 'NegTTL': 2}
        self.sync_dict = {'Off': 0, 'On': 1}
        self.lp_fil_dict = {'6 dB': 0, '12 dB': 1, "18 dB": 2, "24 dB": 3}
        # Internal capture-buffer settings (CAPTURE* subsystem)
        self.capture_config_dict = {'X': 0, 'XY': 1, 'RT': 2, 'XYRT': 3}
        self.capture_acq_dict = {'OneShot': 0, 'Continuous': 1}
        self.capture_trig_dict = {'Immediate': 0, 'TrigStart': 1, 'SampPerTrig': 2}
        self.capture_len_min = 1
        self.capture_len_max = 4096
        self.capture_rate_n_min = 0
        self.capture_rate_n_max = 20

        # Ranges and limits
        self.ref_freq_min = 0.001
        self.ref_freq_max = 4000000
        self.ref_ampl_min = 0.000000001
        self.ref_ampl_max = 2
        self.harm_max = 99
        self.harm_min = 1
        self.ref_freq = 50
        self.harm = 1

        # Test run parameters
        # These values are returned by the modules in the test run 
        if len(sys.argv) > 1:
            self.test_flag = sys.argv[1]
        else:
            self.test_flag = 'None'

        if self.test_flag != 'test':
            if self.config['interface'] == 'gpib':
                try:
                    import Gpib
                    self.status_flag = 1
                    self.device = Gpib.Gpib(self.config['board_address'], self.config['gpib_address'], \
                                            timeout = self.config['timeout'])
                    try:
                        # test should be here
                        self.device_write('*CLS')
                        answer = int(float(self.device_query('*TST?')))
                        if answer == 0:
                            self.status_flag = 1
                        else:
                            general.message(f'During internal device test errors were found {self.__class__.__name__}')
                            self.status_flag = 0
                            sys.exit()
                    except BrokenPipeError:
                        general.message(f"No connection {self.__class__.__name__}")
                        self.status_flag = 0
                        sys.exit()
                except BrokenPipeError:
                    general.message(f"No connection {self.__class__.__name__}")
                    self.status_flag = 0
                    sys.exit()
            elif self.config['interface'] == 'rs232':
                try:
                    self.status_flag = 1
                    rm = pyvisa.ResourceManager()
                    self.device = rm.open_resource(self.config['serial_address'], read_termination=self.config['read_termination'],
                    write_termination=self.config['write_termination'], baud_rate=self.config['baudrate'],
                    data_bits=self.config['databits'], parity=self.config['parity'], stop_bits=self.config['stopbits'])
                    self.device.timeout = self.config['timeout']; # in ms
                    try:
                        # test should be here
                        self.device_write('*CLS')
                        answer = int(self.device_query('*TST?'))
                        if answer == 0:
                            self.status_flag = 1
                        else:
                            general.message(f'During internal device test errors are found {self.__class__.__name__}')
                            self.status_flag = 0
                            sys.exit()
                    except (pyvisa.VisaIOError, BrokenPipeError):
                        self.status_flag = 0
                        general.message(f"No connection {self.__class__.__name__}")
                        sys.exit()

                except (pyvisa.VisaIOError, BrokenPipeError):
                    general.message(f"No connection {self.__class__.__name__}")
                    self.status_flag = 0
                    sys.exit()

            elif self.config['interface'] == 'ethernet':
                try:
                    self.status_flag = 1
                    rm = pyvisa.ResourceManager()
                    self.device = rm.open_resource(self.config['ethernet_address'])
                    self.device.timeout = self.config['timeout'] # in ms
                    try:
                        # test should be here
                        self.device_write('*CLS')
                        answer = int(self.device_query('*TST?'))
                        if answer == 0:
                            self.status_flag = 1
                        else:
                            general.message(f'During internal device test errors are found {self.__class__.__name__}')
                            self.status_flag = 0
                            sys.exit()
                    except (pyvisa.VisaIOError, BrokenPipeError):
                        general.message(f"No connection {self.__class__.__name__}")
                        self.status_flag = 0
                        sys.exit()

                except (pyvisa.VisaIOError, BrokenPipeError):
                    general.message(f"No connection {self.__class__.__name__}")
                    self.status_flag = 0
                    sys.exit()

            self.ref_freq = float( self.device_query( 'FREQ?' ) )
            self.harm = int(self.device_query("HARM?"))

        elif self.test_flag == 'test':
            self.test_signal = 0.001
            self.test_frequency = '10 kHz'
            self.test_phase = '10 deg'
            self.test_timeconstant = '10 ms'
            self.test_amplitude = '300 mV'
            self.test_sensitivity = '100 mV'
            self.test_ref_mode = 'Internal'
            self.test_ref_slope = 'Sine'
            self.test_sync = 'On'
            self.test_lp_filter = '6 dB'
            self.test_harmonic = 1
            self.test_capture_length = 256
            self.test_capture_config = 'XY'
            self.test_capture_rate = 1250000.0
            self.test_capture_rate_max = 1250000.0
            self.test_capture_state = 0
            self.test_capture_bytes = 0
            self.test_capture_progress = 0

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
                self.device.write(command)
                general.wait('50 ms')
                answer = self.device.read().decode()
            elif self.config['interface'] == 'rs232':
                answer = self.device.query(command)
            elif self.config['interface'] == 'ethernet':
                answer = self.device.query(command)
            return answer
        else:
            general.message(f"No connection {self.__class__.__name__}")
            self.status_flag = 0
            sys.exit()

    #### device specific functions
    def lock_in_name(self):
        if self.test_flag != 'test':
            answer = self.device_query('*IDN?')
            return answer
        elif self.test_flag == 'test':
            answer = self.config['name']
            return answer

    def lock_in_ref_frequency(self, *frequency):
        if self.test_flag != 'test':
            if len(frequency) == 1:
                freq_str = str(frequency[0])
                freq = pg.siEval( freq_str )
                if (freq >= self.ref_freq_min and freq <= self.ref_freq_max and self.harm * freq <= self.ref_freq_max ):
                    self.device_write('FREQ '+ str(freq))
                    self.ref_freq = freq
                else:
                    general.message(f"Incorrect reference frequency. The maximum value of the product of the harmonic and the current reference frequency is {self.ref_freq_max}. The current harmonic is { self.harm}")
                    
            elif len(frequency) == 0:
                raw_answer = float(self.device_query('FREQ?'))
                self.ref_freq = raw_answer
                answer = pg.siFormat( raw_answer, suffix = 'Hz', precision = 7, allowUnicode = False)
                return answer

        elif self.test_flag == 'test':
            if len(frequency) == 1:
                freq_str = str(frequency[0])
                freq = pg.siEval( freq_str )
                min_f = pg.siFormat( self.ref_freq_min, suffix = 'Hz', precision = 3, allowUnicode = False)
                max_f = pg.siFormat( self.ref_freq_max, suffix = 'Hz', precision = 3, allowUnicode = False)
                assert(freq >= self.ref_freq_min and freq <= self.ref_freq_max), \
                            f"Incorrect frequency. The available range is from {min_f} to {max_f}"
                assert( self.harm * freq <= self.ref_freq_max ), f"Incorrect reference frequency. The maximum value of the product of the harmonic and the current reference frequency is {self.ref_freq_max}. The current harmonic is { self.harm}"
                self.ref_freq = freq

            elif len(frequency) == 0:
                answer = self.test_frequency
                return answer
            else:
                assert( 1 == 2 ), "Incorrect argument; frequency: float + [' MHz', ' kHz', ' Hz', ' mHz']"

    def lock_in_phase(self, *degree):
        if self.test_flag != 'test':
            if len(degree) == 1:
                degs = float(degree[0])
                if degs >= -360000 and degs <= 360000:
                    self.device_write('PHAS '+str(degs))

            elif len(degree) == 0:
                answer = float(self.device_query('PHAS?'))
                return f"{answer} deg"

        elif self.test_flag == 'test':
            if len(degree) == 1:
                degs = float(degree[0])
                assert(degs >= -360000 and degs <= 360000), f"Incorrect phase. The available range is from {-360000} to {360000}"
            elif len(degree) == 0:
                answer = self.test_phase
                return answer
            else:
                assert( 1 == 2 ), "Incorrect argument; phase: float"

    def lock_in_auto_phase(self):
        """
        The APHS command performs the Auto Phase function. This command is the same
        as pressing Shift−Phase. This command adjusts the reference phase so that the
        current measurement has a Y value of zero and an X value equal to the signal
        magnitude, R.
        """
        if self.test_flag != 'test':
            self.device_write('APHS')

        elif self.test_flag == 'test':
            pass

    def lock_in_time_constant(self, *timeconstant):
        if self.test_flag != 'test':
            if len(timeconstant) == 1:
                tc = timeconstant[0]
                parsed_value, int_value, a = cutil.parse_pg(tc, self.helper_tc_list)
                val, val_key, b = cutil.search_and_limit_keys_dictionary( self.timeconstant_dict, parsed_value, 1e-6, 30e3 )
                self.device_write("OFLT "+ str(val))
                
                if ( a == 1 ) or ( b == 1 ):
                    general.message(f"Desired time constant cannot be set, the nearest available value of {val_key} is used")

            elif len(timeconstant) == 0:
                raw_answer = int(self.device_query("OFLT?"))
                answer = cutil.search_keys_dictionary(self.timeconstant_dict, raw_answer)
                return answer

        elif self.test_flag == 'test':
            if len(timeconstant) == 1:
                tc = timeconstant[0]
                assert( isinstance(tc, str) ), "Incorrect argument; time_constant: int + [' us', ' ms', ' s', ' ks']"
                val, val_key, b = cutil.search_and_limit_keys_dictionary( self.timeconstant_dict, \
                                    cutil.parse_pg(tc, self.helper_tc_list)[0], 1e-6, 30e3 )
                assert( val_key in self.timeconstant_dict ), "Incorrect argument; time_constant: int + [' us', ' ms', ' s', ' ks']"

            elif len(timeconstant) == 0:
                answer = self.test_timeconstant
                return answer
            else:
                assert( 1 == 2), "Incorrect argument; time_constant: int + [' us', ' ms', ' s', ' ks']"

    def lock_in_ref_amplitude(self, *amplitude):
        if self.test_flag != 'test':
            if len(amplitude) == 1:
                ampl_str = str(amplitude[0])
                ampl = pg.siEval( ampl_str )
                if ampl <= self.ref_ampl_max and ampl >= self.ref_ampl_min:
                    self.device_write('SLVL '+ str(ampl))
            elif len(amplitude) == 0:
                raw_answer = float(self.device_query("SLVL?"))
                answer = pg.siFormat( raw_answer, suffix = 'V', precision = 4, allowUnicode = False)
                return answer

        elif self.test_flag == 'test':
            if len(amplitude) == 1:
                ampl_str = str(amplitude[0])
                ampl = pg.siEval( ampl_str )
                min_a = pg.siFormat( self.ref_ampl_min, suffix = 'V', precision = 3, allowUnicode = False)
                max_a = pg.siFormat( self.ref_ampl_max, suffix = 'V', precision = 3, allowUnicode = False)
                assert(ampl <= self.ref_ampl_max and ampl >= self.ref_ampl_min), \
                            f"Incorrect amplitude. The available range is from {min_a} to {max_a}"
            elif len(amplitude) == 0:
                answer = self.test_amplitude
                return answer
            else:
                assert( 1 == 2 ), "Incorrect argument; amplitude: float + [' mV', ' V']"

    def lock_in_get_data(self, *channel):
        if self.test_flag != 'test':
            if len(channel) == 0:
                answer = float(self.device_query('OUTP? 0'))
                return answer
            elif len(channel) == 1 and int(channel[0]) == 1:
                answer = float(self.device_query('OUTP? 0'))
                return answer
            elif len(channel) == 1 and int(channel[0]) == 2:
                answer = float(self.device_query('OUTP? 1'))
                return answer
            elif len(channel) == 1 and int(channel[0]) == 3:
                answer = float(self.device_query('OUTP? 2'))
                return answer
            elif len(channel) == 1 and int(channel[0]) == 4:
                answer = float(self.device_query('OUTP? 3'))
                return answer
            elif len(channel) == 2 and int(channel[0]) == 1 and int(channel[1]) == 2:
                answer_string = self.device_query('SNAP? 0,1')
                answer_list = answer_string.split(',')
                list_of_floats = [float(item) for item in answer_list]
                x = list_of_floats[0]
                y = list_of_floats[1]
                return x, y
            elif len(channel) == 3 and int(channel[0]) == 1 and int(channel[1]) == 2 and int(channel[2]) == 3:
                answer_string = self.device_query('SNAP? 0,1,2')
                answer_list = answer_string.split(',')
                list_of_floats = [float(item) for item in answer_list]
                x = list_of_floats[0]
                y = list_of_floats[1]
                r = list_of_floats[2]
                return x, y, r
        elif self.test_flag == 'test':
            if len(channel) == 0:
                answer = self.test_signal
                return answer
            elif len(channel) == 1:
                assert(int(channel[0]) == 1 or int(channel[0]) == 2 or \
                    int(channel[0]) == 3 or int(channel[0]) == 4), "Invalid channel; channel: ['1', '2', '3', '4']"
                answer = self.test_signal
                return answer
            elif len(channel) == 2 and int(channel[0]) == 1 and int(channel[1]) == 2:
                x = y = self.test_signal
                return x, y
            elif len(channel) == 3 and int(channel[0]) == 1 and int(channel[1]) == 2 and int(channel[2]) == 3:
                x = y = r = self.test_signal
                return x, y, r
            else:
                assert( 1 == 2 ), "Incorrect argument; channel1: int, channel2: int, channel3: int"

    def lock_in_sensitivity(self, *sensitivity):
        if self.test_flag != 'test':
            if len(sensitivity) == 1:
                sens = sensitivity[0]
                parsed_value, int_value, a = cutil.parse_pg(sens, self.helper_sens_list)
                val, val_key, b = cutil.search_and_limit_keys_dictionary( self.sensitivity_dict, parsed_value, 1e-9, 1e0 )
                self.device_write("SCAL "+ str(val))
           
                if ( a == 1 ) or ( b == 1 ):
                    general.message(f"Desired sensitivity cannot be set, the nearest available value of {val_key} is used")

            elif len(sensitivity) == 0:
                raw_answer = int(self.device_query("SCAL?"))
                answer = cutil.search_keys_dictionary(self.sensitivity_dict, raw_answer)
                return answer

        elif self.test_flag == 'test':
            if len(sensitivity) == 1:
                sens = sensitivity[0]
                assert( isinstance(sens, str) ), "Incorrect argument; sensitivity: int + [' nV', ' uV', ' mV', ' V']"
                val, val_key, b = cutil.search_and_limit_keys_dictionary( self.sensitivity_dict, \
                                    cutil.parse_pg(sens, self.helper_sens_list)[0], 1e-9, 1e0 )
                assert( val_key in self.sensitivity_dict ), "Incorrect argument; sensitivity: int + [' nV', ' uV', ' mV', ' V']"

            elif len(sensitivity) == 0:
                answer = self.test_sensitivity
                return answer
            else:
                assert( 1 == 2), "Incorrect argument; sensitivity: int + [' nV', ' uV', ' mV', ' V']"

    def lock_in_auto_sensitivity(self):
        """
        The ASCL command performs the Auto Scale function
        This function may take some time if the time constant is long. This function does
        nothing if the time constant is greater than one second.
        """
        if self.test_flag != 'test':
            self.device_write('ASCL')

        elif self.test_flag == 'test':
            pass

    def lock_in_ref_mode(self, *mode):
        if self.test_flag != 'test':
            if  len(mode) == 1:
                md = str(mode[0])
                if md in self.ref_mode_dict:
                    flag = self.ref_mode_dict[md]
                    self.device_write("RSRC "+ str(flag))

            elif len(mode) == 0:
                raw_answer = int(self.device_query("RSRC?"))
                answer = cutil.search_keys_dictionary(self.ref_mode_dict, raw_answer)
                return answer

        elif self.test_flag == 'test':
            if len(mode) == 1:
                md = str(mode[0])
                if md in self.ref_mode_dict:
                    pass
                else:
                    assert(1 == 2), f"Incorrect mode; mode: {list(self.ref_mode_dict.keys())}"
            elif len(mode) == 0:
                answer = self.test_ref_mode
                return answer
            else:
                assert( 1 == 2 ), f"Incorrect argument; mode: {list(self.ref_mode_dict.keys())}"

    def lock_in_ref_slope(self, *mode):
        if self.test_flag != 'test':
            if len(mode) == 1:
                md = str(mode[0])
                if md in self.ref_slope_dict:
                    flag = self.ref_slope_dict[md]
                    self.device_write("RTRG "+ str(flag))

            elif len(mode) == 0:
                raw_answer = int(self.device_query("RTRG?"))
                answer = cutil.search_keys_dictionary(self.ref_slope_dict, raw_answer)
                return answer

        elif self.test_flag == 'test':
            if  len(mode) == 1:
                md = str(mode[0])
                if md in self.ref_slope_dict:
                    pass
                else:
                    assert(1 == 2), f"Incorrect slope; slope: {list(self.ref_slope_dict.keys())}"
            elif len(mode) == 0:
                answer = self.test_ref_slope
                return answer             
            else:
                assert( 1 == 2 ), f"Incorrect argument; slope: {list(self.ref_slope_dict.keys())}"

    def lock_in_sync_filter(self, *mode):
        if self.test_flag != 'test':
            if len(mode) == 1:
                md = str(mode[0])
                if md in self.sync_dict:
                    flag = self.sync_dict[md]
                    self.device_write("SYNC "+ str(flag))

            elif len(mode) == 0:
                raw_answer = int(self.device_query("SYNC?"))
                answer = cutil.search_keys_dictionary(self.sync_dict, raw_answer)
                return answer

        elif self.test_flag == 'test':
            if len(mode) == 1:
                md = str(mode[0])
                if md in self.sync_dict:
                    pass
                else:
                    assert(1 == 2), f"Incorrect sync filter; filter: {list(self.sync_dict.keys())}"
            elif len(mode) == 0:
                answer = self.test_sync
                return answer   
            else:
                assert( 1 == 2 ), f"Incorrect argument; filter: {list(self.sync_dict.keys())}"

    def lock_in_lp_filter(self, *mode):
        if self.test_flag != 'test':
            if len(mode) == 1:
                md = str(mode[0])
                if md in self.lp_fil_dict:
                    flag = self.lp_fil_dict[md]
                    self.device_write("OFSL "+ str(flag))

            elif len(mode) == 0:
                raw_answer = int(self.device_query("OFSL?"))
                answer = cutil.search_keys_dictionary(self.lp_fil_dict, raw_answer)
                return answer

        elif self.test_flag == 'test':
            if len(mode) == 1:
                md = str(mode[0])
                if md in self.lp_fil_dict:
                    pass
                else:
                    assert(1 == 2), f"Incorrect low pass filter; filter: {list(self.lp_fil_dict.keys())}"
            elif len(mode) == 0:
                answer = self.test_lp_filter
                return answer   
            else:
                assert( 1 == 2 ), f"Incorrect argument; filter: {list(self.lp_fil_dict.keys())}"

    def lock_in_harmonic(self, *harmonic):
        if self.test_flag != 'test':
            if len(harmonic) == 1:
                harm = int(harmonic[0]);
                if harm <= self.harm_max and harm >= self.harm_min:
                    if  (harm * self.ref_freq <= self.ref_freq_max ):
                        self.device_write('HARM '+ str(harm))
                        self.harm = harm
                    else:
                        general.message(f"Incorrect harmonic. The maximum value of the product of the harmonic and the current reference frequency is {self.ref_freq_max}. The current reference frequency is { pg.siFormat( self.ref_freq_max, suffix = 'Hz', precision = 3, allowUnicode = False)}")

            elif len(harmonic) == 0:
                answer = int(self.device_query("HARM?"))
                return answer

        elif self.test_flag == 'test':
            if len(harmonic) == 1:
                harm = int(harmonic[0])
                assert(harm <= self.harm_max and harm >= self.harm_min), \
                    f"Incorrect harmonic. The available range is from {self.harm_min} to {self.harm_max}"
                assert( harm * self.ref_freq <= self.ref_freq_max ), f"Incorrect harmonic. The maximum value of the product of the harmonic and the current reference frequency is {self.ref_freq_max}. The current reference frequency is { pg.siFormat( self.ref_freq_max, suffix = 'Hz', precision = 3, allowUnicode = False)}"
                self.harm = harm

            elif len(harmonic) == 0:
                answer = self.test_harmonic
                return answer
            else:
                assert( 1 == 2 ), f"Incorrect argument; harmonic: int [{self.harm_min} {self.harm_max}]"
    
    #### Internal capture-buffer functions (CAPTURE* subsystem)
    def lock_in_capture_length(self, *length):
        # CAPTURELEN: capture-buffer length in kB (256 data points per kB)
        if self.test_flag != 'test':
            if len(length) == 1:
                n = int(length[0])
                if n >= self.capture_len_min and n <= self.capture_len_max:
                    self.device_write("CAPTURELEN " + str(n))
                else:
                    general.message(f"Incorrect capture length. The available range is from {self.capture_len_min} to {self.capture_len_max} kB")

            elif len(length) == 0:
                answer = int(self.device_query("CAPTURELEN?"))
                return answer

        elif self.test_flag == 'test':
            if len(length) == 1:
                n = int(length[0])
                assert(n >= self.capture_len_min and n <= self.capture_len_max), \
                    f"Incorrect capture length. The available range is from {self.capture_len_min} to {self.capture_len_max} kB"
            elif len(length) == 0:
                answer = self.test_capture_length
                return answer
            else:
                assert( 1 == 2 ), "Incorrect argument; length: int (kB)"

    def lock_in_capture_config(self, *config):
        # CAPTURECFG: which quantities are captured ('X', 'XY', 'RT', 'XYRT')
        if self.test_flag != 'test':
            if len(config) == 1:
                cfg = str(config[0])
                if cfg in self.capture_config_dict:
                    self.device_write("CAPTURECFG " + str(self.capture_config_dict[cfg]))
                else:
                    general.message(f"Incorrect capture config; config: {list(self.capture_config_dict.keys())}")

            elif len(config) == 0:
                raw_answer = int(self.device_query("CAPTURECFG?"))
                answer = cutil.search_keys_dictionary(self.capture_config_dict, raw_answer)
                return answer

        elif self.test_flag == 'test':
            if len(config) == 1:
                cfg = str(config[0])
                assert(cfg in self.capture_config_dict), \
                    f"Incorrect capture config; config: {list(self.capture_config_dict.keys())}"
            elif len(config) == 0:
                answer = self.test_capture_config
                return answer
            else:
                assert( 1 == 2 ), f"Incorrect argument; config: {list(self.capture_config_dict.keys())}"

    def lock_in_capture_rate_max(self):
        # CAPTURERATEMAX?: maximum allowed capture rate in Hz at the current time constant
        if self.test_flag != 'test':
            answer = float(self.device_query("CAPTURERATEMAX?"))
            return answer
        elif self.test_flag == 'test':
            answer = self.test_capture_rate_max
            return answer

    def lock_in_capture_rate(self, *n):
        # CAPTURERATE: set the rate to (max rate)/2**n, n in [0, 20]; the query returns the actual rate in Hz
        if self.test_flag != 'test':
            if len(n) == 1:
                exponent = int(n[0])
                if exponent >= self.capture_rate_n_min and exponent <= self.capture_rate_n_max:
                    self.device_write("CAPTURERATE " + str(exponent))
                else:
                    general.message(f"Incorrect capture rate divisor. The available range is from {self.capture_rate_n_min} to {self.capture_rate_n_max}")

            elif len(n) == 0:
                answer = float(self.device_query("CAPTURERATE?"))
                return answer

        elif self.test_flag == 'test':
            if len(n) == 1:
                exponent = int(n[0])
                assert(exponent >= self.capture_rate_n_min and exponent <= self.capture_rate_n_max), \
                    f"Incorrect capture rate divisor. The available range is from {self.capture_rate_n_min} to {self.capture_rate_n_max}"
            elif len(n) == 0:
                answer = self.test_capture_rate
                return answer
            else:
                assert( 1 == 2 ), "Incorrect argument; n: int [0, 20]"

    def lock_in_capture_start(self, acquisition, trigger):
        # CAPTURESTART: start a new capture; clears previously captured data
        # acquisition: 'OneShot' / 'Continuous'; trigger: 'Immediate' / 'TrigStart' / 'SampPerTrig'
        if self.test_flag != 'test':
            acq = str(acquisition)
            trg = str(trigger)
            if acq in self.capture_acq_dict and trg in self.capture_trig_dict:
                self.device_write("CAPTURESTART " + str(self.capture_acq_dict[acq]) + ',' + str(self.capture_trig_dict[trg]))
            else:
                general.message(f"Incorrect capture start; acquisition: {list(self.capture_acq_dict.keys())}, trigger: {list(self.capture_trig_dict.keys())}")

        elif self.test_flag == 'test':
            acq = str(acquisition)
            trg = str(trigger)
            assert(acq in self.capture_acq_dict), f"Incorrect acquisition; acquisition: {list(self.capture_acq_dict.keys())}"
            assert(trg in self.capture_trig_dict), f"Incorrect trigger; trigger: {list(self.capture_trig_dict.keys())}"

    def lock_in_capture_stop(self):
        # CAPTURESTOP: stop data capture in any mode
        if self.test_flag != 'test':
            self.device_write("CAPTURESTOP")
        elif self.test_flag == 'test':
            pass

    def lock_in_capture_state(self):
        # CAPTURESTAT?: 3-bit state word (bit0 in progress, bit1 triggered, bit2 wrapped)
        if self.test_flag != 'test':
            answer = int(self.device_query("CAPTURESTAT?"))
            return answer
        elif self.test_flag == 'test':
            answer = self.test_capture_state
            return answer

    def lock_in_capture_bytes(self):
        # CAPTUREBYTES?: number of non-zero data bytes captured so far
        if self.test_flag != 'test':
            answer = int(self.device_query("CAPTUREBYTES?"))
            return answer
        elif self.test_flag == 'test':
            answer = self.test_capture_bytes
            return answer

    def lock_in_capture_progress(self):
        # CAPTUREPROG?: amount of captured data in kB (capture must be stopped)
        if self.test_flag != 'test':
            answer = int(self.device_query("CAPTUREPROG?"))
            return answer
        elif self.test_flag == 'test':
            answer = self.test_capture_progress
            return answer

    def lock_in_capture_value(self, sample):
        # CAPTUREVAL?: read the 1, 2 or 4 values (per CAPTURECFG) of sample number 'sample' in ASCII
        if self.test_flag != 'test':
            raw_answer = self.device_query("CAPTUREVAL? " + str(int(sample)))
            data = np.array([float(item) for item in raw_answer.strip().rstrip(',').split(',')])
            return data
        elif self.test_flag == 'test':
            return np.array([self.test_signal])

    def lock_in_read_capture(self, offset, length):
        # CAPTUREGET?: download 'length' kB of the capture buffer starting at offset 'offset' kB
        # as a NumPy float32 array (little-endian binary block). Capture must be stopped.
        # Not available over the RS-232 interface.
        if self.test_flag != 'test':
            off = int(offset)
            ln = int(length)
            assert(ln >= 1 and ln <= 64), "Invalid length; 1 <= length_kb <= 64"
            command = "CAPTUREGET? " + str(off) + ',' + str(ln)
            if self.config['interface'] == 'rs232':
                general.message("CAPTUREGET? is not available over the RS-232 interface; use lock_in_capture_value()")
                return np.array([], dtype = np.float32)
            elif self.config['interface'] == 'gpib':
                self.device.write(command)
                general.wait('50 ms')
                raw = self.device.read(ln * 1024 + 16)
                if raw[0:1] != b'#':
                    return np.array([], dtype = np.float32)
                ndig = int(raw[1:2])
                count = int(raw[2:2 + ndig])
                start = 2 + ndig
                data = np.frombuffer(raw[start:start + count], dtype = '<f4')
                return data
            else:
                data = self.device.query_binary_values(command, datatype = 'f', is_big_endian = False, container = np.array)
                return np.asarray(data, dtype = np.float32)

        elif self.test_flag == 'test':
            off = int(offset)
            ln = int(length)
            assert(ln >= 1 and ln <= 64), "Invalid length; 1 <= length_kb <= 64"
            return np.array([self.test_signal], dtype = np.float32)

    def lock_in_command(self, command):
        if self.test_flag != 'test':
            self.device_write(command)
        elif self.test_flag == 'test':
            pass

    def lock_in_query(self, command):
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

