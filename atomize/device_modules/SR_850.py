#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import gc
import sys
import pyvisa
from pyvisa.constants import StopBits, Parity
import atomize.device_modules.config.config_utils as cutil
import atomize.general_modules.general_functions as general

class SR_850:
    #### Basic interaction functions
    def __init__(self):

        #### Inizialization
        # setting path to *.ini file
        self.path_current_directory = os.path.dirname(__file__)
        self.path_config_file = os.path.join(self.path_current_directory, 'config','SR_850_config.ini')

        # configuration data
        self.config = cutil.read_conf_util(self.path_config_file)
        self.specific_parameters = cutil.read_specific_parameters(self.path_config_file)

        # auxilary dictionaries
        self.sensitivity_dict = {'2 nV': 0, '5 nV': 1, '10 nV': 2, '20 nV': 3, '50 nV': 4,
                            '100 nV': 5, '200 nV': 6, '500 nV': 7, '1 uV': 8, '2 uV': 9, '5 uV': 10,
                            '10 uV': 11, '20 uV': 12, '50 uV': 13, '100 uV': 14, '200 uV': 15, '500 uV': 16, 
                            '1 mV': 17, '2 mV': 18, '5 mV': 19, '10 mV': 20, '20 mV': 21, '50 mV': 22,
                            '100 mV': 23, '200 mV': 24, '500 mV': 25, '1 V': 26};
        self.helper_sens_list = [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000]
        self.timeconstant_dict = {'10 us': 0, '30 us': 1, '100 us': 2, '300 us': 3,
                            '1 ms': 4, '3 ms': 5, '10 ms': 6, '30 ms': 7, '100 ms': 8, '300 ms': 9,
                            '1 s': 10, '3 s': 11, '10 s': 12, '30 s': 13, '100 s': 14, '300 s': 15, 
                            '1 ks': 16, '3 ks': 17, '10 ks': 18, '30 ks': 19};
        self.helper_tc_list = [1, 3, 10, 30, 100, 300, 1000]
        self.ref_mode_dict = {'Internal': 0, 'External': 2,}
        self.ref_slope_dict = {'Sine': 0, 'PosTTL': 1, 'NegTTL': 2}
        self.sync_dict = {'Off': 0, 'On': 1}
        self.lp_fil_dict = {'6 db': 0, '12 dB': 1, "18 dB": 2, "24 dB": 3}

        # Ranges and limits
        self.ref_freq_min = 0.001
        self.ref_freq_max = 102000
        self.ref_ampl_min = 0.004
        self.ref_ampl_max = 5
        self.harm_max = 32767
        self.harm_min = 1

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
                        general.message("No connection")
                        self.status_flag = 0
                        sys.exit()
                except BrokenPipeError:
                    general.message("No connection")
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
                    except pyvisa.VisaIOError:
                        self.status_flag = 0
                        general.message("No connection")
                        sys.exit();
                    except BrokenPipeError:
                        general.message("No connection")
                        self.status_flag = 0
                        sys.exit()
                except pyvisa.VisaIOError:
                    general.message("No connection")
                    self.status_flag = 0
                    sys.exit()
                except BrokenPipeError:
                    general.message("No connection")
                    self.status_flag = 0
                    sys.exit()
        elif self.test_flag == 'test':
            self.test_signal = 0.001
            self.test_frequency = 10000
            self.test_phase = 10
            self.test_timeconstant = '10 ms'
            self.test_amplitude = 0.3
            self.test_sensitivity = '100 mV'
            self.test_ref_mode = 'Internal'
            self.test_ref_slope = 'Sine'
            self.test_sync = 'On'
            self.test_lp_filter = '6 dB'
            self.test_harmonic = 1

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
            general.message("No Connection")
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
            general.message("No Connection")
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
                freq = float(frequency[0])
                if freq >= self.ref_freq_min and freq <= self.ref_freq_max:
                    self.device_write('FREQ '+ str(freq))
                else:
                    general.message("Incorrect frequency")
                    sys.exit()
            elif len(frequency) == 0:
                answer = float(self.device_query('FREQ?'))
                return answer
            else:
                general.message("Invalid Argument")
                sys.exit()

        elif self.test_flag == 'test':
            if len(frequency) == 1:
                freq = float(frequency[0])
                assert(freq >= self.ref_freq_min and freq <= self.ref_freq_max), "Incorrect frequency is reached"
            elif len(frequency) == 0:
                answer = self.test_frequency
                return answer

    def lock_in_phase(self, *degree):
        if self.test_flag != 'test':
            if len(degree) == 1:
                degs = float(degree[0])
                if degs >= -360 and degs <= 719:
                    self.device_write('PHAS '+str(degs))
                else:
                    general.message("Incorrect phase")
                    sys.exit()
            elif len(degree) == 0:
                answer = float(self.device_query('PHAS?'))
                return answer
            else:
                general.message("Invalid Argument")
                sys.exit()

        elif self.test_flag == 'test':
            if len(degree) == 1:
                degs = float(degree[0])
                assert(degs >= -360 and degs <= 719), "Incorrect phase is reached"
            elif len(degree) == 0:
                answer = self.test_phase
                return answer

    def lock_in_time_constant(self, *timeconstant):
        if self.test_flag != 'test':
            if  len(timeconstant) == 1:
                temp = timeconstant[0].split(' ')
                if float(temp[0]) < 10 and temp[1] == 'us':
                    send.message("Desired time constant cannot be set, the nearest available value is used")
                    self.device_write("OFLT "+ str(0))
                elif float(temp[0]) > 30 and temp[1] == 'ks':
                    general.message("Desired sensitivity cannot be set, the nearest available value is used")
                    self.device_write("OFLT "+ str(19))
                else:
                    number_tc = min(self.helper_tc_list, key=lambda x: abs(x - int(temp[0])))
                    if int(number_tc) == 1000 and temp[1] == 'us':
                        number_tc = 1
                        temp[1] = 'ms'
                    elif int(number_tc) == 1000 and temp[1] == 'ms':
                        number_tc = 1
                        temp[1] = 's'
                    elif int(number_tc) == 1000 and temp[1] == 's':
                        number_tc = 1
                        temp[1] = 'ks'
                    if int(number_tc) != int(temp[0]):
                        general.message("Desired time constant cannot be set, the nearest available value is used")
                    tc = str(number_tc) + ' ' + temp[1]
                    if tc in self.timeconstant_dict:
                        flag = self.timeconstant_dict[tc]
                        self.device_write("OFLT "+ str(flag))
                    else:
                        general.message("Invalid time constant value (too high/too low)")
                        sys.exit()
            elif len(timeconstant) == 0:
                raw_answer = int(self.device_query("OFLT?"))
                answer = cutil.search_keys_dictionary(self.timeconstant_dict, raw_answer)
                return answer
            else:
                general.message("Invalid Argument")
                sys.exit()

        elif self.test_flag == 'test':
            if  len(timeconstant) == 1:
                temp = timeconstant[0].split(' ')
                if float(temp[0]) < 10 and temp[1] == 'us':
                    tc = '10 us'
                if float(temp[0]) > 30 and temp[1] == 'ks':
                    tc = '30 ks'
                else:
                    number_tc = min(self.helper_tc_list, key=lambda x: abs(x - int(temp[0])))
                    if int(number_tc) == 1000 and temp[1] == 'us':
                        number_tc = 1
                        temp[1] = 'ms'
                    elif int(number_tc) == 1000 and temp[1] == 'ms':
                        number_tc = 1
                        temp[1] = 's'
                    elif int(number_tc) == 1000 and temp[1] == 's':
                        number_tc = 1
                        temp[1] = 'ks'
                    tc = str(number_tc) + ' ' + temp[1]
                    if tc in self.timeconstant_dict:
                        pass
                    else:
                        assert(1 == 2), "Incorrect time constant is used"
            elif len(timeconstant) == 0:
                answer = self.test_timeconstant
                return answer

    def lock_in_ref_amplitude(self, *amplitude):
        if self.test_flag != 'test':
            if len(amplitude) == 1:
                ampl = float(amplitude[0]);
                if ampl <= self.ref_ampl_max and ampl >= self.ref_ampl_min:
                    self.device_write('SLVL '+ str(ampl))
                else:
                    self.device_write('SLVL '+ str(self.ref_ampl_min))
                    general.message("Invalid Argument")
                    sys.exit()
            elif len(amplitude) == 0:
                answer = float(self.device_query("SLVL?"))
                return answer
            else:
                general.message("Invalid Argument")
                sys.exit()

        elif self.test_flag == 'test':
            if len(amplitude) == 1:
                ampl = float(amplitude[0]);
                assert(ampl <= self.ref_ampl_max and ampl >= self.ref_ampl_min), "Incorrect amplitude is reached"
            elif len(amplitude) == 0:
                answer = self.test_amplitude
                return answer

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
                answer = float(self.device_query('OUTP? 4'))
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
                    int(channel[0]) == 3 or int(channel[0]) == 4), 'Invalid channel is given'
                answer = self.test_signal
                return answer
            elif len(channel) == 2 and int(channel[0]) == 1 and int(channel[1]) == 2:
                x = y = self.test_signal
                return x, y
            elif len(channel) == 3 and int(channel[0]) == 1 and int(channel[1]) == 2 and int(channel[2]) == 3:
                x = y = r = self.test_signal
                return x, y, r

    def lock_in_sensitivity(self, *sensitivity):
        if self.test_flag != 'test':
            if len(sensitivity) == 1:
                temp = sensitivity[0].split(' ')
                if float(temp[0]) < 2 and temp[1] == 'nV':
                    send.message("Desired sensitivity cannot be set, the nearest available value is used")
                    self.device_write("SENS "+ str(0))
                elif float(temp[0]) > 1 and temp[1] == 'V':
                    general.message("Desired sensitivity cannot be set, the nearest available value is used")
                    self.device_write("SENS "+ str(26))
                else:
                    number_sens = min(self.helper_sens_list, key=lambda x: abs(x - int(temp[0])))
                    if int(number_sens) == 1000 and temp[1] == 'nV':
                        number_sens = 1
                        temp[1] = 'uV'
                    elif int(number_sens) == 1000 and temp[1] == 'uV':
                        number_sens = 1
                        temp[1] = 'mV'
                    elif int(number_sens) == 1000 and temp[1] == 'mV':
                        number_sens = 1
                        temp[1] = 'V'
                    sens = str(number_sens) + ' ' + temp[1]
                    if int(number_sens) != int(temp[0]):
                        general.message("Desired sensitivity cannot be set, the nearest available value is used")
                    if sens in self.sensitivity_dict:
                        flag = self.sensitivity_dict[sens]
                        self.device_write("SENS "+ str(flag))
                    else:
                        general.message("Invalid sensitivity value (too high/too low)")
                        sys.exit()
            elif len(sensitivity) == 0:
                raw_answer = int(self.device_query("SENS?"))
                answer = cutil.search_keys_dictionary(self.sensitivity_dict, raw_answer)
                return answer
            else:
                general.message("Invalid Argument")
                sys.exit()

        elif self.test_flag == 'test':
            if  len(sensitivity) == 1:
                temp = sensitivity[0].split(' ')
                if float(temp[0]) < 2 and temp[1] == 'nV':
                    sens = '2 nV'
                elif float(temp[0]) > 1 and temp[1] == 'V':
                    sens = '1 V'
                else:
                    number_sens = min(self.helper_sens_list, key=lambda x: abs(x - int(temp[0])))
                    if int(number_sens) == 1000 and temp[1] == 'nV':
                        number_sens = 1
                        temp[1] = 'uV'
                    elif int(number_sens) == 1000 and temp[1] == 'uV':
                        number_sens = 1
                        temp[1] = 'mV'
                    elif int(number_sens) == 1000 and temp[1] == 'mV':
                        number_sens = 1
                        temp[1] = 'V'
                    tc = str(number_sens) + ' ' + temp[1]
                    if tc in self.sensitivity_dict:
                        pass
                    else:
                        assert(1 == 2), "Incorrect sensitivity is used"
            elif len(sensitivity) == 0:
                answer = self.test_sensitivity
                return answer

    def lock_in_ref_mode(self, *mode):
        if self.test_flag != 'test':
            if  len(mode) == 1:
                md = str(mode[0])
                if md in self.ref_mode_dict:
                    flag = self.ref_mode_dict[md]
                    self.device_write("FMOD "+ str(flag))
                else:
                    general.message("Invalid mode")
                    sys.exit()
            elif len(mode) == 0:
                raw_answer = int(self.device_query("FMOD?"))
                answer = cutil.search_keys_dictionary(self.ref_mode_dict, raw_answer)
                return answer
            else:
                general.message("Invalid argumnet")
                sys.exit()

        elif self.test_flag == 'test':
            if len(mode) == 1:
                md = str(mode[0])
                if md in self.ref_mode_dict:
                    pass
                else:
                    assert(1 == 2), "Incorrect ref mode is used"
            elif len(mode) == 0:
                answer = self.test_ref_mode
                return answer

    def lock_in_ref_slope(self, *mode):
        if self.test_flag != 'test':
            if len(mode) == 1:
                md = str(mode[0])
                if md in self.ref_slope_dict:
                    flag = self.ref_slope_dict[md]
                    self.device_write("RSLP "+ str(flag))
                else:
                    general.message("Invalid mode")
                    sys.exit()
            elif len(mode) == 0:
                raw_answer = int(self.device_query("RSLP?"))
                answer = cutil.search_keys_dictionary(self.ref_slope_dict, raw_answer)
                return answer
            else:
                general.message("Invalid argumnet")
                sys.exit()

        elif self.test_flag == 'test':
            if  len(mode) == 1:
                md = str(mode[0])
                if md in self.ref_slope_dict:
                    pass
                else:
                    assert(1 == 2), "Incorrect ref slope is used"
            elif len(mode) == 0:
                answer = self.test_ref_slope
                return answer             

    def lock_in_sync_filter(self, *mode):
        if self.test_flag != 'test':
            if len(mode) == 1:
                md = str(mode[0])
                if md in self.sync_dict:
                    flag = self.sync_dict[md]
                    self.device_write("SYNC "+ str(flag))
                else:
                    general.message("Invalid argument")
                    sys.exit()
            elif len(mode) == 0:
                raw_answer = int(self.device_query("SYNC?"))
                answer = cutil.search_keys_dictionary(self.sync_dict, raw_answer)
                return answer
            else:
                general.message("Invalid argumnet")
                sys.exit()

        elif self.test_flag == 'test':
            if len(mode) == 1:
                md = str(mode[0])
                if md in self.sync_dict:
                    pass
                else:
                    assert(1 == 2), "Incorrect sync filter parameter"
            elif len(mode) == 0:
                answer = self.test_sync
                return answer   

    def lock_in_lp_filter(self, *mode):
        if self.test_flag != 'test':
            if len(mode) == 1:
                md = str(mode[0])
                if md in self.lp_fil_dict:
                    flag = self.lp_fil_dict[md]
                    self.device_write("OFSL "+ str(flag))
                else:
                    general.message("Invalid mode")
                    sys.exit()
            elif len(mode) == 0:
                raw_answer = int(self.device_query("OFSL?"))
                answer = cutil.search_keys_dictionary(self.lp_fil_dict, raw_answer)
                return answer
            else:
                general.message("Invalid argumnet")
                sys.exit()

        elif self.test_flag == 'test':
            if len(mode) == 1:
                md = str(mode[0])
                if md in self.lp_fil_dict:
                    pass
                else:
                    assert(1 == 2), "Incorrect low pass filter is used"
            elif len(mode) == 0:
                answer = self.test_lp_filter
                return answer   

    def lock_in_harmonic(self, *harmonic):
        if self.test_flag != 'test':
            if len(harmonic) == 1:
                harm = int(harmonic[0]);
                if harm <= self.harm_max and harm >= self.harm_min:
                    self.device_write('HARM '+ str(harm))
                else:
                    self.device_write('HARM '+ str(self.harm_min))
                    general.message("Invalid Argument")
                    sys.exit()
            elif len(harmonic) == 0:
                answer = int(self.device_query("HARM?"))
                return answer
            else:
                general.message("Invalid Argument")
                sys.exit()

        elif self.test_flag == 'test':
            if len(harmonic) == 1:
                harm = float(harmonic[0])
                assert(harm <= self.harm_max and harm >= self.harm_min), "Incorrect harmonic is reached"
            elif len(harmonic) == 0:
                answer = self.test_harmonic
                return answer

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

