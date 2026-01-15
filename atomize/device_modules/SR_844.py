#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import gc
import sys
import pyvisa
import pyqtgraph as pg
from pyvisa.constants import StopBits, Parity
import atomize.main.local_config as lconf
import atomize.device_modules.config.config_utils as cutil
import atomize.general_modules.general_functions as general

class SR_844:
    #### Basic interaction functions
    def __init__(self):

        #### Inizialization
        # setting path to *.ini file
        self.path_current_directory = lconf.load_config_device()
        self.path_config_file = os.path.join(self.path_current_directory, 'SR_844_config.ini')

        # configuration data
        self.config = cutil.read_conf_util(self.path_config_file)
        self.specific_parameters = cutil.read_specific_parameters(self.path_config_file)

        # auxilary dictionaries
        self.sensitivity_dict = {'100 nV': 0, '300 nV': 1, '1 uV': 2, '3 uV': 3, 
                            '10 uV': 4, '30 uV': 5, '100 uV': 6, '300 uV': 7,  
                            '1 mV': 8, '3 mV': 9, '10 mV': 10, '30 mV': 11, '100 mV': 12, '300 mV': 13,
                            '1 V': 14};
        self.helper_sens_list = [1, 3, 10, 100, 300, 1000]
        self.timeconstant_dict = {'100 us': 0, '300 us': 1,
                            '1 ms': 2, '3 ms': 3, '10 ms': 4, '30 ms': 5, '100 ms': 6, '300 ms': 7,
                            '1 s': 8, '3 s': 9, '10 s': 10, '30 s': 11, '100 s': 12, '300 s': 13, 
                            '1 ks': 14, '3 ks': 15, '10 ks': 16, '30 ks': 17};
        self.helper_tc_list = [1, 3, 10, 30, 100, 300, 1000]
        self.lp_fil_dict = {'No': 0, '6 dB': 1, '12 dB': 2, "18 dB": 3, "24 dB":4}
        self.ref_mode_dict = {'Internal': 0, 'External': 1}

        # Ranges and limits
        self.ref_freq_min = 25000
        self.ref_freq_2f_min = 50000
        self.ref_freq_max = 200000000
        self.ref_ampl_min = 0.004
        self.ref_ampl_max = 5
        self.harm_max = 2
        self.harm_min = 1
        self.ref_freq = 50
        self.mode_2f = 0

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
                        self.status_flag = 1
                        self.device_write('*CLS')
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
                    self.device.timeout = self.config['timeout'] # in ms
                    try:
                        # test should be here
                        self.status_flag = 1
                        self.device_write('*CLS')
                        self.ref_freq = float( self.device_query( 'FREQ?' ) )
                        self.mode_2f = int( self.device_query( 'HARM?' ) )
                    except (pyvisa.VisaIOError, BrokenPipeError):
                        self.status_flag = 0
                        general.message(f"No connection {self.__class__.__name__}")
                        sys.exit();

                except (pyvisa.VisaIOError, BrokenPipeError):
                    general.message(f"No connection {self.__class__.__name__}")
                    self.status_flag = 0
                    sys.exit()

        elif self.test_flag == 'test':
            self.test_signal = 0.001
            self.test_frequency = '10 kHz'
            self.test_phase = '10 deg'
            self.test_timeconstant = '10 ms'
            self.test_amplitude = '300 mV'
            self.test_sensitivity = '100 mV'
            self.test_lp_filter = '6 dB'
            self.test_ref_mode = 'Internal'

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
        min_f = pg.siFormat( self.ref_freq_min, suffix = 'Hz', precision = 3, allowUnicode = False)
        max_f = pg.siFormat( self.ref_freq_max, suffix = 'Hz', precision = 3, allowUnicode = False)
        min_2f = pg.siFormat( self.ref_freq_2f_min, suffix = 'Hz', precision = 3, allowUnicode = False)

        if self.test_flag != 'test':
            if len(frequency) == 1:
                freq_str = str(frequency[0])
                freq = pg.siEval( freq_str )

                if self.mode_2f == 0:
                    assert( freq >= self.ref_freq_min and freq <= self.ref_freq_max ), \
                            f"Incorrect reference frequency. The available range is from {min_f} to {max_f}"
                    self.device_write('FREQ '+ str(freq))

                elif self.mode_2f == 1:
                    assert( freq >= self.ref_freq_2f_min and freq <= self.ref_freq_max ), \
                            f"Incorrect reference frequency in 2F mode.  The available range is from {min_2f} to {max_f}"
                    self.device_write('FREQ '+ str(freq))

            elif len(frequency) == 0:
                self.ref_freq = float(self.device_query('FREQ?'))
                answer = pg.siFormat( self.ref_freq, suffix = 'Hz', precision = 7, allowUnicode = False)
                return raw_answer

        elif self.test_flag == 'test':
            if len(frequency) == 1:
                freq = float(frequency[0])
                assert(freq >= self.ref_freq_min and freq <= self.ref_freq_max), \
                            f"Incorrect frequency. The available range is from {min_f} to {max_f}"
            elif len(frequency) == 0:
                answer = self.test_frequency
                return answer
            else:
                assert( 1 == 2 ), "Incorrect argument; frequency: float + [' MHz', ' kHz', ' Hz', ' mHz']"

    def lock_in_phase(self, *degree):
        if self.test_flag != 'test':
            if len(degree) == 1:
                degs = float(degree[0])
                if degs >= -360 and degs <= 360:
                    self.device_write('PHAS '+str(degs))

            elif len(degree) == 0:
                answer = float(self.device_query('PHAS?'))
                return f"{answer} deg"

        elif self.test_flag == 'test':
            if len(degree) == 1:
                degs = float(degree[0])
                assert(degs >= -360 and degs <= 360), f"Incorrect phase. The available range is from {-360} to {360}"
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
                val, val_key, b = cutil.search_and_limit_keys_dictionary( self.timeconstant_dict, parsed_value, 100e-6, 30e3 )
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
                                    cutil.parse_pg(tc, self.helper_tc_list)[0], 100e-6, 30e3 )
                assert( val_key in self.timeconstant_dict ), "Incorrect argument; time_constant: int + [' us', ' ms', ' s', ' ks']"

            elif len(timeconstant) == 0:
                answer = self.test_timeconstant
                return answer
            else:
                assert( 1 == 2), "Incorrect argument; time_constant: int + [' us', ' ms', ' s', ' ks']"

    def lock_in_get_data(self, *channel):
        if self.test_flag != 'test':
            if len(channel) == 0:
                answer = float(self.device_query('OUTP? 1'))
                return answer
            elif len(channel) == 1 and int(channel[0]) == 1:
                answer = float(self.device_query('OUTP? 1'))
                return answer
            elif len(channel) == 1 and int(channel[0]) == 2:
                answer = float(self.device_query('OUTP? 2'))
                return answer
            elif len(channel) == 1 and int(channel[0]) == 3:
                answer = float(self.device_query('OUTP? 3'))
                return answer
            elif len(channel) == 1 and int(channel[0]) == 4:
                answer = float(self.device_query('OUTP? 5'))
                return answer
            elif len(channel) == 2 and int(channel[0]) == 1 and int(channel[1]) == 2:
                answer_string = self.device_query('SNAP? 1,2')
                answer_list = answer_string.split(',')
                list_of_floats = [float(item) for item in answer_list]
                x = list_of_floats[0]
                y = list_of_floats[1]
                return x, y
            elif len(channel) == 3 and int(channel[0]) == 1 and int(channel[1]) == 2 and int(channel[2]) == 3:
                answer_string = self.device_query('SNAP? 1,2,3')
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
                val, val_key, b = cutil.search_and_limit_keys_dictionary( self.sensitivity_dict, parsed_value, 100e-9, 1e0 )
                self.device_write("SENS "+ str(val))
           
                if ( a == 1 ) or ( b == 1 ):
                    general.message(f"Desired sensitivity cannot be set, the nearest available value of {val_key} is used")

            elif len(sensitivity) == 0:
                raw_answer = int(self.device_query("SENS?"))
                answer = cutil.search_keys_dictionary(self.sensitivity_dict, raw_answer)
                return answer

        elif self.test_flag == 'test':
            if len(sensitivity) == 1:
                sens = sensitivity[0]
                assert( isinstance(sens, str) ), "Incorrect argument; sensitivity: int + [' nV', ' uV', ' mV', ' V']"
                val, val_key, b = cutil.search_and_limit_keys_dictionary( self.sensitivity_dict, \
                                    cutil.parse_pg(sens, self.helper_sens_list)[0], 100e-9, 1e0 )
                assert( val_key in self.sensitivity_dict ), "Incorrect argument; sensitivity: int + [' nV', ' uV', ' mV', ' V']"

            elif len(sensitivity) == 0:
                answer = self.test_sensitivity
                return answer
            else:
                assert( 1 == 2), "Incorrect argument; sensitivity: int + [' nV', ' uV', ' mV', ' V']"

    def lock_in_auto_sensitivity(self):
        """
        The AGAN command performs the Auto Sensitivity function. This command is the
        same as pressing Shift–SensUp. AGAN automatically sets the Sensitivity of the
        instrument.
        This function may take some time if the time constant is long. This function does
        nothing if the time constant is greater than one second. Check the Interface Ready
        bit (bit 1) in the Serial Poll Status to determine when the command is finished.
        """
        if self.test_flag != 'test':
            self.device_write('AGAN')

        elif self.test_flag == 'test':
            pass

    def lock_in_auto_phase(self):
        """
        This command adjusts the reference phase so that the
        current measurement has a Y value of zero and an X value equal to the signal
        magnitude, R. The outputs will take many time constants to reach their
        new values.
        """
        if self.test_flag != 'test':
            self.device_write('APHS')

        elif self.test_flag == 'test':
            pass

    def lock_in_ref_mode(self, *mode):
        if self.test_flag != 'test':
            if  len(mode) == 1:
                md = str(mode[0])
                if md in self.ref_mode_dict:
                    flag = self.ref_mode_dict[md]
                    self.device_write("FMOD "+ str(flag))

            elif len(mode) == 0:
                raw_answer = int(self.device_query("FMOD?"))
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
        min_f = pg.siFormat( self.ref_freq_min, suffix = 'Hz', precision = 3, allowUnicode = False)
        max_f = pg.siFormat( self.ref_freq_max, suffix = 'Hz', precision = 3, allowUnicode = False)
        min_2f = pg.siFormat( self.ref_freq_2f_min, suffix = 'Hz', precision = 3, allowUnicode = False)

        if self.test_flag != 'test':
            if len(harmonic) == 1:
                harm = int(harmonic[0]) - 1

                if harm == 1:
                    assert( self.ref_freq <= self.ref_freq_max and  self.ref_freq >= self.ref_freq_2f_min ), \
                            f"Incorrect reference frequency. The available range is from {min_2f} to {max_f}"
                elif harm == 0:
                    assert( self.ref_freq <= self.ref_freq_max and self.ref_freq >= self.ref_freq_min ), \
                           f"Incorrect reference frequency. The available range is from {min_f} to {max_f}"

                self.device_write('HARM '+ str(harm))

            elif len(harmonic) == 0:
                self.mode_2f = int(self.device_query("HARM?"))
                return self.mode_2f

        elif self.test_flag == 'test':
            if len(harmonic) == 1:
                harm = int(harmonic[0])
                assert(harm <= self.harm_max and harm >= self.harm_min), \
                    f"Incorrect harmonic. The available range is from {self.harm_min} to {self.harm_max}"
            elif len(harmonic) == 0:
                answer = self.mode_2f
                return answer
            else:
                assert( 1 == 2 ), f"Incorrect argument; harmonic: int [{self.harm_min}-{self.harm_max}]"
    
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

