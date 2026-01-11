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

class Planar_C2220:
    #### Basic interaction functions
    def __init__(self):

        #### Inizialization
        # setting path to *.ini file
        self.path_current_directory = lconf.load_config_device()
        self.path_config_file = os.path.join(self.path_current_directory, 'Planar_C2220_config.ini')

        # configuration data
        self.config = cutil.read_conf_util(self.path_config_file)
        self.specific_parameters = cutil.read_specific_parameters(self.path_config_file)

        # auxilary dictionaries
        self.trigger_source_list = ['INT', 'EXT', 'MAN', 'BUS']
        self.trigger_mode_list = ['SINGLE', 'REP', 'OFF']
        self.meas_type = ['IQ', 'AP']
        self.meas_data_type = ['COR', 'RAW']
        self.on_off_list = [0, 1]
        self.data_source_list = ['S11', 'S12', 'S21', 'S22', 'R11', 'R12', 'R21', 'R22', 'A(1)', 'A(2)', 'B(1)', 'B(2)']
        self.helper_filter_list = [1, 1.5, 2, 3, 5, 7]
        self.frequency_dict = {'GHz': 1000000000, 'MHz': 1000000, 'kHz': 1000, 'Hz': 1, };
        self.bandwidth = [1, 2, 3, 5, 7, 10, 15, 20, 30, 50, 70, 100, \
                          150, 200, 300, 500, 700, 1000, \
                          1500, 2000, 3000, 5000, 7000, 10000, \
                          15000, 20000, 30000, 50000, 70000, 100000, \
                          150000, 200000, 300000, 500000, 700000, 1000000, \
                          1500000, 2000000 ] 

        self.helper_sens_list = [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000]

        self.t_single = 0

        # Ranges and limits
        self.channels = int(self.specific_parameters['channels'])
        self.sources = int(self.specific_parameters['sources'])
        self.freq_max = 10**6 * float(self.specific_parameters['freq_max'])
        self.freq_min = 10**6 * float(self.specific_parameters['freq_min'])
        self.power_max = float(self.specific_parameters['power_max'])
        self.power_min = float(self.specific_parameters['power_min'])
        self.points_max = int(self.specific_parameters['points_max'])
        self.points_min = int(self.specific_parameters['points_min'])

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
                    write_termination=self.config['write_termination'])
                    self.device.timeout = self.config['timeout'] # in ms
                    
                    try:
                        # test should be here
                        self.status_flag = 1
                    #    self.device_write('*CLS')
                    except (pyvisa.VisaIOError, BrokenPipeError):
                        self.status_flag = 0
                        general.message(f"No connection {self.__class__.__name__}")
                        sys.exit();

                except (pyvisa.VisaIOError, BrokenPipeError):
                    general.message(f"No connection {self.__class__.__name__}")
                    self.status_flag = 0
                    sys.exit()

        elif self.test_flag == 'test':
            self.test_power = 0.
            self.test_freq_center = '100 MHz'
            self.test_freq_span = '500 kHz'
            self.test_num_points = 1000
            self.test_trig_cource = 'INT'
            self.test_bandwidth = '1 kHz'
            self.trigger_mode = 'REP'
            self.test_data = np.random.rand( int(2 * self.test_num_points))
            self.test_freq_data = 1 + np.arange( self.test_num_points )
            self.test_meas_time = 0.2
            
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
            answer = self.device.query(command)
            return answer
        else:
            general.message(f"No connection {self.__class__.__name__}")
            self.status_flag = 0
            sys.exit()

    #### device specific functions
    def vector_analyzer_name(self):
        if self.test_flag != 'test':
            answer = self.device_query('*IDN?')
            return answer
        elif self.test_flag == 'test':
            answer = self.config['name']
            return answer

    def vector_analyzer_source_power(self, *pwr, source = 1):
        if self.test_flag != 'test':
            if len(pwr) == 1:
                power = round(float(pwr[0]), 2)
                if power >= self.power_min and power <= self.power_max:
                    self.device_write(f'SOURce{int(source)}:POWer {power}')
            elif len(pwr) == 0:
                answer = float(self.device_query(f'SOURce{source}:POWer?'))
                return answer

        elif self.test_flag == 'test':
            if len(pwr) == 1:
                power = round(float(pwr[0]), 2)
                assert(power >= self.power_min and power <= self.power_max), \
                    f"Incorrect power. The available range is from {self.power_min} dBm to {self.power_max} dBm"
                assert(source >= 1 and source <= self.sources), f"Incorrect source. The available range is from {1} to {self.sources}"
            elif len(pwr) == 0:
                assert(source >= 1 and source <= self.sources), f"Incorrect source. The available range is from {1} to {self.sources}"
                return self.test_power
            else:
                assert (1 == 2), "Invalid argument; power: float; source = int"

    def vector_analyzer_center_frequency(self, *frq, channel = 1):
        if self.test_flag != 'test':
            if len(frq) == 1:
                temp = frq[0].split(" ")
                val = float(temp[0])
                scaling = str(temp[1]);
                if scaling in self.frequency_dict:
                    coef = self.frequency_dict[scaling]
                    freq = val * coef
                if freq >= self.freq_min and freq <= self.freq_max:
                    self.device_write(f'SENSe{int(channel)}:FREQuency:CENTer {freq}')

            elif len(frq) == 0:
                #answer = str(float(self.device_query(f'SENSe{int(channel)}:FREQuency:CENTer?')) / 1000000) + ' MHz'
                raw_answer = float(self.device_query(f'SENSe{int(channel)}:FREQuency:CENTer?'))
                answer = pg.siFormat( raw_answer, suffix = 'Hz', precision = 11, allowUnicode = False)
                return answer

        elif self.test_flag == 'test':
            if len(frq) == 1:
                temp = frq[0].split(" ")
                val = float(temp[0])
                scaling = str(temp[1]);
                assert(scaling in self.frequency_dict), "Invalid argument; frequency: float + [' GHz', ' MHz', ' kHz', ' Hz']; channel = int"
                coef = self.frequency_dict[scaling]
                freq = val * coef
                assert(channel >= 1 and channel <= self.channels), f"Incorrect channel. The available range is from {1} to {self.channels}"
                min_f = pg.siFormat( self.freq_min, suffix = 'Hz', precision = 3, allowUnicode = False)
                max_f = pg.siFormat( self.freq_max, suffix = 'Hz', precision = 3, allowUnicode = False)
                assert(freq >= self.freq_min and freq <= self.freq_max), \
                    f"Incorrect frequency center. The available range is from {min_f} to {max_f}"
            elif len(frq) == 0:
                assert(channel >= 1 and channel <= self.channels), f"Incorrect channel. The available range is from {1} to {self.channels}"
                return self.test_freq_center
            else:
                assert (1 == 2), "Invalid argument; frequency: float + [' GHz', ' MHz', ' kHz', ' Hz']; channel = int"

    def vector_analyzer_frequency_range(self, *frq, channel = 1):
        if self.test_flag != 'test':
            if len(frq) == 1:
                temp = frq[0].split(" ")
                val = float(temp[0])
                scaling = str(temp[1]);
                if scaling in self.frequency_dict:
                    coef = self.frequency_dict[scaling]
                    freq = val * coef
                if freq >= 0 and freq <= self.freq_max:
                    self.device_write(f'SENSe{int(channel)}:FREQuency:SPAN {freq}')

            elif len(frq) == 0:
                #answer = str(float(self.device_query(f'SENSe{int(channel)}:FREQuency:SPAN?')) / 1000000) + ' MHz'
                raw_answer = float(self.device_query(f'SENSe{int(channel)}:FREQuency:SPAN?'))
                answer = pg.siFormat( raw_answer, suffix = 'Hz', precision = 6, allowUnicode = False)
                return answer

        elif self.test_flag == 'test':
            if len(frq) == 1:
                temp = frq[0].split(" ")
                val = float(temp[0])
                scaling = str(temp[1]);
                assert(scaling in self.frequency_dict), "Invalid argument; frequency: float + [' GHz', ' MHz', ' kHz', ' Hz']; channel = int"
                coef = self.frequency_dict[scaling]
                freq = val * coef
                assert(channel >= 1 and channel <= self.channels), f"Incorrect channel. The available range is from {1} to {self.channels}"
                max_f = pg.siFormat( self.freq_max, suffix = 'Hz', precision = 3, allowUnicode = False)
                assert(freq >= 0 and freq <= self.freq_max), f"Incorrect frequency span. The available range is from {0} Hz to {max_f}"
            elif len(frq) == 0:
                assert(channel >= 1 and channel <= self.channels), f"Incorrect channel. The available range is from {1} to {self.channels}"
                return self.test_freq_span
            else:
                assert (1 == 2), "Invalid argument; frequency: float + [' GHz', ' MHz', ' kHz', ' Hz']; channel = int"

    def vector_analyzer_points(self, *pnt, channel = 1):
        if self.test_flag != 'test':
            if len(pnt) == 1:
                val = int(pnt[0])
                if val >= self.points_min and val <= self.points_max:
                    self.device_write(f'SENSe{int(channel)}:SWEep:POINts {val}')

            elif len(pnt) == 0:
                answer = int(self.device_query(f'SENSe{int(channel)}:SWEep:POINts?'))
                return answer

        elif self.test_flag == 'test':
            if len(pnt) == 1:
                val = int(pnt[0])
                assert(channel >= 1 and channel <= self.channels), f"Incorrect channel. The available range is from {1} to {self.channels}"
                assert(val >= self.points_min and val <= self.points_max), \
                    f"Incorrect number of points. The available range is from {self.points_min } to {self.points_max }"
                self.test_num_points = val
                self.test_data = np.random.rand( int(2 * self.test_num_points))
                self.test_freq_data = 1 + np.arange( self.test_num_points )
            elif len(pnt) == 0:
                assert(channel >= 1 and channel <= self.channels), f"Incorrect channel. The available range is from {1} to {self.channels}"
                return self.test_num_points
            else:
                assert (1 == 2), "Invalid argument; number of points: int; channel = int"

    def vector_analyzer_trigger_source(self, *src):
        if self.test_flag != 'test':
            if len(src) == 1:
                source = str(src[0])
                if source in self.trigger_source_list:
                    self.device_write(f'TRIGger:SOURce {source}')

            elif len(src) == 0:
                answer = str(self.device_query(f'TRIGger:SOURce?'))
                return answer

        elif self.test_flag == 'test':
            if len(src) == 1:
                source = str(src[0])
                assert(source in self.trigger_source_list), f"Incorrect trigger source; source: {self.trigger_source_list}"
            elif len(src) == 0:
                return self.test_trig_cource
            else:
                assert (1 == 2), f"Invalid argument; source: {self.trigger_source_list}"

    def vector_analyzer_send_trigger(self):
        if self.test_flag != 'test':
            self.device_write(f'TRIG:SING')
            self.device_query("*OPC?")
        elif self.test_flag == 'test':
            pass

    def vector_analyzer_intermediate_freqiency_bandwith(self, *bnd, channel = 1 ):
        if self.test_flag != 'test': 
            if len(bnd) == 1:
                temp = bnd[0].split(" ")
                val = float(temp[0])
                scaling = str(temp[1])
                if scaling in self.frequency_dict:
                    coef = self.frequency_dict[scaling]
                    temp_bandwidth = val * coef
                bandwidth = min(self.bandwidth, key = lambda x: abs(x - temp_bandwidth))
                
                if int(bandwidth) != temp_bandwidth:
                    general.message(f"Desired IF bandwidth cannot be set, the nearest available value {bandwidth} is used.")
                self.device_write(f'SENSe1:BANDwidth {bandwidth}')
        
            elif len(bnd) == 0:
                #answer = str(float(self.device_query('SENSe1:BANDwidth?')) / 1000) + ' kHz'
                raw_answer = float(self.device_query('SENSe1:BANDwidth?'))
                answer = pg.siFormat( raw_answer, suffix = 'Hz', allowUnicode = False)
                return answer

        elif self.test_flag == 'test':
            if len(bnd) == 1:
                temp = bnd[0].split(" ")
                val = float(temp[0])
                scaling = str(temp[1])
                assert(scaling in self.frequency_dict), "Invalid argument; bandwidth: int + [' Hz', ' kHz', ' MHz']; channel = int"
                coef = self.frequency_dict[scaling]
                temp_bandwidth = val * coef
                assert(channel >= 1 and channel <= self.channels), f"Incorrect channel. The available range is from {1} to {self.channels}"
                bandwidth = min(self.bandwidth, key = lambda x: abs(x - temp_bandwidth))
        
            elif len(bnd) == 0:
                assert(channel >= 1 and channel <= self.channels), f"Incorrect channel. The available range is from {1} to {self.channels}"
                return self.test_bandwidth
            else:
                assert (1 == 2), "Invalid argument; bandwidth: int + [' Hz', ' kHz', ' MHz']; channel = int"

    def vector_analyzer_trigger_mode(self, *md, channel = 1):
        if self.test_flag != 'test':
            if len(md) == 1:
                mode = str(md[0])
                if mode in self.trigger_mode_list:
                    if mode == 'SINGLE':
                        self.t_single = 1
                        self.device_write(f"INITiate{int(channel)}:CONTinuous 0")
                        self.device_write(f'INIT{int(channel)}')
                    elif mode == 'REP':
                        self.t_single = 0
                        self.device_write(f"INITiate{int(channel)}:CONTinuous 1")
                    elif mode == 'OFF':
                        self.t_single = 0
                        self.device_write(f"INITiate{int(channel)}:CONTinuous 0")

            elif len(md) == 0:
                raw_answer = int(self.device_query(f"INITiate{int(channel)}:CONTinuous?"))
                if raw_answer == 1:
                    return 'REP'
                elif raw_answer == 0 and self.t_single == 0:
                    return 'OFF'
                elif raw_answer == 0 and self.t_single == 1:
                    return 'SINGLE'

        elif self.test_flag == 'test':
            if len(md) == 1:
                mode = str(md[0])
                assert(mode in self.trigger_mode_list), f"Incorrect trigger mode; mode: {self.trigger_mode_list}"
                if mode == 'SINGLE':
                    self.t_single = 1
                elif mode == 'REP':
                    self.t_single = 0
                elif mode == 'OFF':
                    self.t_single = 0
            
            elif len(md) == 0:
                if self.t_single == 0:
                    return self.trigger_mode
                elif self.t_single == 1:
                    return 'SINGLE'
            else:
                assert (1 == 2), f"Invalid argument; mode: {self.trigger_mode_list}; channel = int"

    def vector_analyzer_get_curve(self, s = 'S11', type = 'IQ', channel = 1, data_type = 'COR'):
        if self.test_flag != 'test':
            if data_type == 'COR':
                raw_array = np.array( self.device_query(f"SENSe{int(channel)}:DATA:CORRData? {s}").split(',') ).astype(np.float64)
            elif data_type == 'RAW':
                raw_array = np.array( self.device_query(f"SENSe{int(channel)}:DATA:RAWData? {s}").split(',') ).astype(np.float64)
            array_i = raw_array[0::2]
            array_q = raw_array[1::2]
            if type == 'IQ':
                return array_i, array_q
            elif type == 'AP':
                c_array = np.zeros(  len(array_i) , dtype = np.complex_ )
                c_array = array_i + 1j * array_q
                return np.absolute(c_array), np.rad2deg(np.arctan2(-array_i, array_q)) #np.log10(np.absolute(c_array)) * 20, np.angle(c_array, deg = True)

        elif self.test_flag == 'test':
            assert(data_type in self.meas_data_type), f"Incorrect data measurement type; data_type = {self.meas_data_type}"
            assert(s in self.data_source_list), f"Incorrect data source; s = {self.data_source_list}"
            assert(type in self.meas_type), f"Incorrect data type; data_type = {self.meas_type}"
            assert(channel >= 1 and channel <= self.channels), f"Incorrect channel. The available range is from {1} to {self.channels}"

            raw_array = self.test_data
            array_i = raw_array[0::2]
            array_q = raw_array[1::2]
            if type == 'IQ':
                return array_i, array_q
            elif type == 'AP':
                c_array = np.zeros(  len(array_i) , dtype = np.complex_ )
                c_array = array_i + 1j * array_q
                return np.absolute(c_array), np.rad2deg(np.arctan2(-array_i, array_q)) #np.log10(np.absolute(c_array)) * 20, np.angle(c_array, deg = True)

    def vector_analyzer_get_frequency_points(self, channel = 1):
        if self.test_flag != 'test':
            raw_array = np.array( self.device_query(f"SENSe{int(channel)}:FREQuency:DATA?").split(',') ).astype(np.float64) / 10**6
            return raw_array
        elif self.test_flag == 'test':
            assert(channel >= 1 and channel <= self.channels), f"Incorrect channel. The available range is from {1} to {self.channels}"
            return self.test_freq_data

    def vector_analyzer_measurement_time(self, channel = 1):
        if self.test_flag != 'test':
            raw_answer = float( self.device_query(f"SENSe{int(channel)}:SWEep:CW:TIME?") )
            answer = pg.siFormat( raw_answer, suffix = 's', precision = 5, allowUnicode = False)
            return answer
        elif self.test_flag == 'test':
            assert(channel >= 1 and channel <= self.channels), f"Incorrect channel. The available range is from {1} to {self.channels}"
            return self.test_meas_time

    def vector_analyzer_command(self, command):
        if self.test_flag != 'test':
            self.device_write(command)
        elif self.test_flag == 'test':
            pass

    def vector_analyzer_query(self, command):
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

