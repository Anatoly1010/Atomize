#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import struct
import datetime
import socket
from math import exp, sqrt
from threading import Thread
import numpy as np
import atomize.device_modules.config.config_utils as cutil
import atomize.general_modules.general_functions as general

class Micran_X_band_MW_bridge_v2:
    #### Basic interaction functions
    def __init__(self):

        #### Inizialization
        # setting path to *.ini file
        self.path_current_directory = os.path.dirname(__file__)
        self.path_config_file = os.path.join(self.path_current_directory, 'config','Micran_x_band_mw_bridge_v2_config.ini')

        # configuration data
        #config = cutil.read_conf_util(self.path_config_file)
        self.specific_parameters = cutil.read_specific_parameters(self.path_config_file)

        # auxilary dictionaries
        self.curr_dB = 60
        self.prev_dB = 60
        # first initialization
        self.flag = 0
        self.mode_list = ['Limit', 'Arbitrary']
        self.p1 = 'None'

        # Ranges and limits
        self.UDP_IP = str(self.specific_parameters['udp_ip'])
        self.UDP_PORT = int(self.specific_parameters['udp_port'])
        self.TCP_IP = str(self.specific_parameters['tcp_ip'])
        self.TCP_PORT = int(self.specific_parameters['tcp_port'])
        self.synthesizer_min = int(self.specific_parameters['synthesizer_min'])
        self.synthesizer_max = int(self.specific_parameters['synthesizer_max'])

        # Test run parameters
        # These values are returned by the modules in the test run 
        if len(sys.argv) > 1:
            self.test_flag = sys.argv[1]
        else:
            self.test_flag = 'None'

        if self.test_flag != 'test':
            pass
        elif self.test_flag == 'test':
            self.test_freq_str = 'Frequency: 9750 MHz'
            self.test_telemetry = 'Temperature: 28; State: INIT'
            self.test_attenuation = '0 dB'
            self.test_phase = '0 deg'
            self.test_cut_off = '300 MHz'

        #self.mw_bridge_rotary_vane(60, mode = 'Limit')

    def device_query(self, command, bytes_to_recieve):
        # MW bridge answers every command
        try:
            self.sock = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
            # timeout in sec
            self.sock.settimeout(10) 
            self.sock.connect( (self.TCP_IP, self.TCP_PORT) )

            self.sock.sendto( command, (self.TCP_IP, self.TCP_PORT) )
            data_raw, addr = self.sock.recvfrom( int(bytes_to_recieve) )

            self.sock.shutdown(socket.SHUT_RDWR)
            self.sock.close()

            return data_raw
        except socket.error:
            general.message("No Connection")
            sys.exit()

    #### device specific functions
    def mw_bridge_name(self):
        if self.test_flag != 'test':
            answer = 'Mikran X-band MW bridge'
            return answer
        elif self.test_flag == 'test':
            answer = 'Mikran X-band MW bridge'
            return answer

    def mw_bridge_synthesizer(self, *freq):
        if self.test_flag != 'test':
            if len(freq) == 1:

                temp = str(freq[0])
                if len( temp ) == 4:
                    temp = '0' + temp
                elif len( temp ) == 5:
                    temp = temp

                MESSAGE = b'\x04' + b'\x08' + b'\x00' + b'\x00' + b'\x00' + temp.encode()
                # 10 bytes to recieve
                garb = self.device_query( MESSAGE, 10)

            elif len(freq) == 0:

                # get frequency
                MESSAGE = b'\x1e' + b'\x08' + (0).to_bytes(8, byteorder = 'big')
                # 10 bytes to recieve
                data_raw = self.device_query( MESSAGE, 10)

                if chr(data_raw[4]) == '1':
                    state = 'ON'
                elif chr(data_raw[4]) == '0':
                    state = 'OFF'

                if chr(data_raw[5]) == '0':
                    freq = chr(data_raw[6]) + chr(data_raw[7])\
                        + chr(data_raw[8]) + chr(data_raw[9])
                else:
                    freq = chr(data_raw[5]) + chr(data_raw[6]) + chr(data_raw[7])\
                        + chr(data_raw[8]) + chr(data_raw[9])

                answer = 'Frequency: ' + freq + ' MHz'

                return answer

        elif self.test_flag == 'test':
            if len(freq) == 1:

                temp = int(freq[0])
                assert(temp >= self.synthesizer_min and temp < self.synthesizer_max), 'Incorrect frequency; Too low / high'

            elif len(freq) == 0:

                return self.test_freq_str

    def mw_bridge_att1_prd(self, *atten):
        if self.test_flag != 'test':
            if len(atten) == 1:

                temp = 2*float(atten[0])

                if int(temp) != temp:
                    general.message('Attenuation value is rounded to the nearest available ' + str(int(temp)/2) + 'dB')

                MESSAGE = b'\x15' + b'\x01' + struct.pack(">B", int(temp))
                # 3 bytes to recieve
                garb = self.device_query( MESSAGE, 3)

            elif len(atten) == 0:

                MESSAGE = b'\x1f' + b'\x01' + b'\x00'
                # 3 bytes to recieve
                data_raw = self.device_query( MESSAGE, 3)

                answer = 'Attenuator RECT: ' + str(data_raw[2]/2) + ' dB'

                return answer

        elif self.test_flag == 'test':
            if len(atten) == 1:

                temp = float(atten[0])
                assert(temp >= 0 and temp <= 31.5), 'Incorrect attenuation'

            elif len(atten) == 0:

                return self.test_attenuation

    def mw_bridge_att2_prd(self, *atten):
        if self.test_flag != 'test':
            if len(atten) == 1:

                temp = 2*float(atten[0])
                if int(temp) != temp:
                    general.message('Attenuation value is rounded to the nearest available ' + str(int(temp)/2) + 'dB')

                MESSAGE = b'\x16' + b'\x01' + struct.pack(">B", int(temp))
                # 3 bytes to recieve
                garb = self.device_query( MESSAGE, 3)

            elif len(atten) == 0:

                MESSAGE = b'\x20' + b'\x01' + b'\x00'
                # 3 bytes to recieve
                data_raw = self.device_query( MESSAGE, 3)

                answer = 'Attenuator AWG: ' + str(data_raw[2]/2) + ' dB'

                return answer

        elif self.test_flag == 'test':
            if len(atten) == 1:

                temp = float(atten[0])
                assert(temp >= 0 and temp <= 31.5), 'Incorrect attenuation'

            elif len(atten) == 0:

                return self.test_attenuation

    def mw_bridge_fv_ctrl(self, *phase):
        if self.test_flag != 'test':
            if len(phase) == 1:

                temp = float(phase[0])/5.625
                if int(temp) != temp:
                    general.message('Phase value is rounded to the nearest available ' + str(int(temp)*5.625) + 'deg')

                MESSAGE = b'\x17' + b'\x01' + struct.pack(">B", int(temp))
                # 3 bytes to recieve
                garb = self.device_query( MESSAGE, 3)

            elif len(phase) == 0:

                MESSAGE = b'\x21' + b'\x01' + b'\x00'
                # 3 bytes to recieve
                data_raw = self.device_query( MESSAGE, 3)

                answer = 'Phase CTRL: ' + str(data_raw[2]*5.625) + ' deg'

                return answer

        elif self.test_flag == 'test':
            if len(phase) == 1:

                temp = float(phase[0])
                assert(temp >= 0 and temp <= 354.375), 'Incorrect phase'

            elif len(phase) == 0:

                return self.test_phase

    def mw_bridge_fv_prm(self, *phase):
        if self.test_flag != 'test':
            if len(phase) == 1:

                temp = float(phase[0])/5.625
                if int(temp) != temp:
                    general.message('Phase value is rounded to the nearest available ' + str(int(temp)*5.625) + 'deg')

                MESSAGE = b'\x19' + b'\x01' + struct.pack(">B", int(temp))
                # 3 bytes to recieve
                garb = self.device_query( MESSAGE, 3)

            elif len(phase) == 0:

                MESSAGE = b'\x23' + b'\x01' + b'\x00'
                # 3 bytes to recieve
                data_raw = self.device_query( MESSAGE, 3)

                answer = 'Phase PRM: ' + str(data_raw[2]*5.625) + ' deg'

                return answer

        elif self.test_flag == 'test':
            if len(phase) == 1:

                temp = float(phase[0])
                assert(temp >= 0 and temp <= 354.375), 'Incorrect phase'

            elif len(phase) == 0:

                return self.test_phase

    def mw_bridge_att_prm(self, *atten):
        if self.test_flag != 'test':
            if len(atten) == 1:

                temp = float(atten[0])/2
                if int(temp) != temp:
                    general.message('Attenuation value is rounded to the nearest available ' + str(int(temp)*2) + 'dB')

                MESSAGE = b'\x1c' + b'\x01' + struct.pack(">B", int(temp))
                # 3 bytes to recieve
                garb = self.device_query( MESSAGE, 3)

            elif len(atten) == 0:

                MESSAGE = b'\x26' + b'\x01' + b'\x00'
                # 3 bytes to recieve
                data_raw = self.device_query( MESSAGE, 3)

                answer = 'Video Attenuation 1: ' + str(data_raw[2]*2) + ' dB'

                return answer

        elif self.test_flag == 'test':
            if len(atten) == 1:

                temp = float(atten[0])
                assert(temp >= 0 and temp <= 30), 'Incorrect attenuation'

            elif len(atten) == 0:

                return self.test_attenuation

    def mw_bridge_att2_prm(self, *atten):
        if self.test_flag != 'test':
            if len(atten) == 1:

                temp = 2*float(atten[0])
                if int(temp) != temp:
                    general.message('Attenuation value is rounded to the nearest available ' + str(int(temp)/2) + 'dB')

                MESSAGE = b'\x1a' + b'\x01' + struct.pack(">B", int(temp))
                # 3 bytes to recieve
                garb = self.device_query( MESSAGE, 3)

            elif len(atten) == 0:

                MESSAGE = b'\x24' + b'\x01' + b'\x00'
                # 3 bytes to recieve
                data_raw = self.device_query( MESSAGE, 3)

                answer = 'Video Attenuation 2: ' + str(data_raw[2]/2) + ' dB'

                return answer

        elif self.test_flag == 'test':
            if len(atten) == 1:

                temp = float(atten[0])
                assert(temp >= 0 and temp <= 31.5), 'Incorrect attenuation'

            elif len(atten) == 0:

                return self.test_attenuation

    def mw_bridge_cut_off(self, *cutoff):
        if self.test_flag != 'test':
            if len(cutoff) == 1:
                temp = str(cutoff[0])

                if temp == '30':
                    MESSAGE = b'\x1b' + b'\x01' + b'\x00'
                elif temp == '105':
                    MESSAGE = b'\x1b' + b'\x01' + b'\x01'
                elif temp == '300':
                    MESSAGE = b'\x1b' + b'\x01' + b'\x02'
                else:
                    general.message('Incorrect cut-off frequency')
                    sys.exit()

                # 3 bytes to recieve
                garb = self.device_query( MESSAGE, 3)

            elif len(cutoff) == 0:
                MESSAGE = b'\x25' + b'\x01' + b'\x00'
                # 3 bytes to recieve
                data_raw = self.device_query( MESSAGE, 3)

                if data_raw[2] == 0:
                    freq = '30'
                elif data_raw[2] == 1:
                    freq = '105'
                elif data_raw[2] == 2:
                    freq = '300'

                answer = 'Cut-off Frequency: ' + freq + ' MHz'

                return answer

        elif self.test_flag == 'test':
            if len(cutoff) == 1:
                temp = str(cutoff[0])
                assert(temp == '30' or temp == '105' or temp == '300'), 'Incorrect cut-off frequency should be 30, 105 or 300'

            elif len(cutoff) == 0:

                return self.test_cut_off

    def mw_bridge_rotary_vane(self, *atten, mode = 'Arbitrary'):
        if self.test_flag != 'test':
            if len(atten) == 1:
                #self.mode_list = ['Limit', 'Arbitrary']
                if mode == 'Arbitrary':
                    self.curr_dB = round( float( atten[0] ), 1 )
                    step = int( self.calibration( self.curr_dB ) ) - int( self.calibration( self.prev_dB ) )

                    try:
                        self.p1.join()
                    except ( AttributeError, NameError, TypeError ):
                        pass

                    MESSAGE = b'\x0e' + b'\x04' + b'\x01' + b'\x02' + ( step ).to_bytes( 2, byteorder = 'big', signed = True )
                    # 6 bytes to recieve
                    garb = self.device_query( MESSAGE, 6)
                    
                    # 36 is a manual calibration
                    time_to_wait = abs( 36 * step )

                    self.p1 = Thread(target = general.wait, args = (str(time_to_wait) + ' ms', ) )
                    self.p1.start()

                    self.prev_dB = self.curr_dB

                elif mode == 'Limit':
                    temp = round( float( atten[0] ), 1 )
                    self.curr_dB = int( general.numpy_round( temp, 60 ) )

                    if int(temp) != self.curr_dB:
                        general.message('Attenuation value is rounded to the nearest available ' + str( self.curr_dB ) + 'dB')

                    if self.curr_dB == 60: 
                        try:
                            self.p1.join()
                        except ( AttributeError, NameError, TypeError ):
                            pass

                        MESSAGE = b'\x0e' + b'\x04' + b'\x01' + b'\x01' + (3).to_bytes( 2, byteorder = 'big', signed = False )
                        garb = self.device_query( MESSAGE, 6)

                        step = int( self.calibration( self.curr_dB ) ) - int( self.calibration( self.prev_dB ) )
                        
                        # 36 is a manual calibration
                        if self.flag == 0:
                            time_to_wait = 7000
                        else:
                            time_to_wait = abs( 36 * step )

                        self.p1 = Thread(target = general.wait, args = (str(time_to_wait) + ' ms', ) )
                        self.p1.start()

                        self.prev_dB = self.curr_dB
                        self.flag = 1

                    elif self.curr_dB == 0:
                        try:
                            self.p1.join()
                        except ( AttributeError, NameError, TypeError ):
                            pass

                        MESSAGE = b'\x0e' + b'\x04' + b'\x01' + b'\x01' + (2).to_bytes( 2, byteorder = 'big', signed = False )
                        garb = self.device_query( MESSAGE, 6)
                        
                        step = int( self.calibration( self.curr_dB ) ) - int( self.calibration( self.prev_dB ) )
                        
                        # 36 is a manual calibration
                        if self.flag == 0:
                            time_to_wait = 7000
                        else:
                            time_to_wait = abs( 36 * step )

                        self.p1 = Thread(target = general.wait, args = (str(time_to_wait) + ' ms', ) )
                        self.p1.start()

                        self.prev_dB = self.curr_dB
                        self.flag = 1

                else:
                    general.message('Incorrect rotary vane attenuator mode')
                    sys.exit()

            elif len(atten) == 0:

                #MESSAGE = b'\x24' + b'\x01' + b'\x00'
                # 6 bytes to recieve
                # check
                #data_raw = self.device_query( MESSAGE, 6)

                answer = 'Rotary Vane Attenuation: ' + str( self.curr_dB ) + ' dB'

                return answer

        elif self.test_flag == 'test':
            if len( atten ) == 1:

                assert( mode in self.mode_list ), 'Incorrect rotary vane attenuator mode'
                if mode == 'Arbitrary':
                    temp = round( float( atten[0] ), 1 )
                    assert( temp >= 0 and temp <= 60 ), 'Incorrect attenuation'
                elif mode == 'Limit':
                    temp = round( float( atten[0] ), 1 )
                    temp = int( general.numpy_round( temp, 60 ) )

                    assert( temp >= 0 and temp <= 60 ), 'Incorrect attenuation'

            elif len(atten) == 0:

                return self.test_attenuation

    def mw_bridge_telemetry(self):
        if self.test_flag != 'test':

            MESSAGE = b'\x0d' + b'\x08' + (0).to_bytes(8, byteorder = 'big')
            # 10 bytes to recieve
            data_raw = self.device_query( MESSAGE, 10)

            if int(data_raw[4]) == 1:
                state = 'INIT'
            elif int(data_raw[4]) == 2:
                state = 'WORK'
            elif int(data_raw[4]) == 3:
                state = 'FAIL'

            answer = str(datetime.datetime.now().strftime("%d %b %Y %H:%M")) + '; ' + 'Temperature: ' + str(data_raw[8]) + '; ' \
                 + 'State: ' + state

            return answer

        elif self.test_flag == 'test':

            return self.test_telemetry

    def mw_bridge_initialize(self):
        if self.test_flag != 'test':

            MESSAGE = b'\x27' + b'\x01' + b'\x00'
            # 3 bytes to recieve
            data_raw = self.device_query( MESSAGE, 3 )

            general.message('Initialization done')

        elif self.test_flag == 'test':
            pass

    # device specific function
    def calibration(self, x):
        # approximation curve
        # step to dB
        return -4409.48 + 676.179 * exp( -0.0508708 * x ) + 2847.41 * exp( 0.00768761 * x ) - 0.345934 * x ** 2 + 2847.41 * exp( 0.00768761 * x ) - 440.034 * sqrt( x )
    
    def numpy_round(x, base):
        """
        A function to round x to be divisible by y
        """
        return base * np.round(x / base)

def main():
    pass

if __name__ == "__main__":
    main()

