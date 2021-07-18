#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import struct
import datetime
import socket
import atomize.device_modules.config.config_utils as cutil
import atomize.general_modules.general_functions as general

#### Inizialization
# setting path to *.ini file
path_current_directory = os.path.dirname(__file__)
path_config_file = os.path.join(path_current_directory, 'config','Mikran_x_band_mw_bridge_config.ini')

# configuration data
#config = cutil.read_conf_util(path_config_file)
specific_parameters = cutil.read_specific_parameters(path_config_file)

# auxilary dictionaries

# Ranges and limits
UDP_IP = str(specific_parameters['udp_ip'])
UDP_PORT = int(specific_parameters['udp_port'])
TCP_IP = str(specific_parameters['tcp_ip'])
TCP_PORT = int(specific_parameters['tcp_port'])
synthesizer_min = int(specific_parameters['synthesizer_min'])
synthesizer_max = int(specific_parameters['synthesizer_max'])

# Test run parameters
# These values are returned by the modules in the test run 
if len(sys.argv) > 1:
    test_flag = sys.argv[1]
else:
    test_flag = 'None'

test_freq_str = 'Power: ON; Frequency: 9750'
test_telemetry = 'Temperature: 28; State: INIT'
test_attenuation = '0 dB'
test_phase = '0 deg'
test_cut_off = '300 MHz'

class Mikran_X_band_MW_bridge:
    #### Basic interaction functions
    def __init__(self):
        if test_flag != 'test':
            pass
        elif test_flag == 'test':
            pass

    def device_query(self, command, bytes_to_recieve):
        # MW bridge answers every command
        try:
            self.sock = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
            # timeout
            self.sock.settimeout(10) 
            self.sock.connect( (TCP_IP, TCP_PORT) )

            self.sock.sendto( command, (TCP_IP, TCP_PORT) )
            data_raw, addr = self.sock.recvfrom( int(bytes_to_recieve) )

            self.sock.shutdown(socket.SHUT_RDWR)
            self.sock.close()

            return data_raw
        except socket.error:
            general.message("No Connection")
            sys.exit()

    #### device specific functions
    def mw_bridge_name(self):
        if test_flag != 'test':
            answer = 'Mikran X-band MW bridge'
            return answer
        elif test_flag == 'test':
            answer = 'Mikran X-band MW bridge'
            return answer

    def mw_bridge_synthesizer(self, *freq):
        if test_flag != 'test':
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

        elif test_flag == 'test':
            if len(freq) == 1:

                temp = int(freq[0])
                assert(temp >= synthesizer_min and temp < synthesizer_max), 'Incorrect frequency; Too low / high'

            elif len(freq) == 0:

                return test_freq_str

    def mw_bridge_att1_prd(self, *atten):
        if test_flag != 'test':
            if len(atten) == 1:

                temp = 2*float(atten[0])

                if int(temp) != temp:
                    general.message('Attenuation value is rounded to the nearest availabe ' + str(int(temp)/2) + 'dB')

                MESSAGE = b'\x15' + b'\x01' + struct.pack(">B", int(temp))
                # 3 bytes to recieve
                garb = self.device_query( MESSAGE, 3)

            elif len(atten) == 0:

                MESSAGE = b'\x1f' + b'\x01' + b'\x00'
                # 3 bytes to recieve
                data_raw = self.device_query( MESSAGE, 3)

                answer = 'Attenuator 1 PRD: ' + str(data_raw[2]/2) + ' dB'

                return answer

        elif test_flag == 'test':
            if len(atten) == 1:

                temp = float(atten[0])
                assert(temp >= 0 and temp <= 31.5), 'Incorrect attenuation'

            elif len(atten) == 0:

                return test_attenuation

    def mw_bridge_att2_prd(self, *atten):
        if test_flag != 'test':
            if len(atten) == 1:

                temp = 2*float(atten[0])
                if int(temp) != temp:
                    general.message('Attenuation value is rounded to the nearest availabe ' + str(int(temp)/2) + 'dB')

                MESSAGE = b'\x16' + b'\x01' + struct.pack(">B", int(temp))
                # 3 bytes to recieve
                garb = self.device_query( MESSAGE, 3)

            elif len(atten) == 0:

                MESSAGE = b'\x20' + b'\x01' + b'\x00'
                # 3 bytes to recieve
                data_raw = self.device_query( MESSAGE, 3)

                answer = 'Attenuator 2 PRD: ' + str(data_raw[2]/2) + ' dB'

                return answer

        elif test_flag == 'test':
            if len(atten) == 1:

                temp = float(atten[0])
                assert(temp >= 0 and temp <= 31.5), 'Incorrect attenuation'

            elif len(atten) == 0:

                return test_attenuation

    def mw_bridge_fv_ctrl(self, *phase):
        if test_flag != 'test':
            if len(phase) == 1:

                temp = float(phase[0])/5.625
                if int(temp) != temp:
                    general.message('Phase value is rounded to the nearest availabe ' + str(int(temp)*5.625) + 'deg')

                MESSAGE = b'\x17' + b'\x01' + struct.pack(">B", int(temp))
                # 3 bytes to recieve
                garb = self.device_query( MESSAGE, 3)

            elif len(phase) == 0:

                MESSAGE = b'\x21' + b'\x01' + b'\x00'
                # 3 bytes to recieve
                data_raw = self.device_query( MESSAGE, 3)

                answer = 'Phase CTRL: ' + str(data_raw[2]*5.625) + ' deg'

                return answer

        elif test_flag == 'test':
            if len(phase) == 1:

                temp = float(phase[0])
                assert(temp >= 0 and temp <= 354.375), 'Incorrect phase'

            elif len(phase) == 0:

                return test_phase

    def mw_bridge_fv_prm(self, *phase):
        if test_flag != 'test':
            if len(phase) == 1:

                temp = float(phase[0])/5.625
                if int(temp) != temp:
                    general.message('Phase value is rounded to the nearest availabe ' + str(int(temp)*5.625) + 'deg')

                MESSAGE = b'\x19' + b'\x01' + struct.pack(">B", int(temp))
                # 3 bytes to recieve
                garb = self.device_query( MESSAGE, 3)

            elif len(phase) == 0:

                MESSAGE = b'\x23' + b'\x01' + b'\x00'
                # 3 bytes to recieve
                data_raw = self.device_query( MESSAGE, 3)

                answer = 'Phase PRM: ' + str(data_raw[2]*5.625) + ' deg'

                return answer

        elif test_flag == 'test':
            if len(phase) == 1:

                temp = float(phase[0])
                assert(temp >= 0 and temp <= 354.375), 'Incorrect phase'

            elif len(phase) == 0:

                return test_phase

    def mw_bridge_att_prm(self, *atten):
        if test_flag != 'test':
            if len(atten) == 1:

                temp = float(atten[0])/2
                if int(temp) != temp:
                    general.message('Attenuation value is rounded to the nearest availabe ' + str(int(temp)*2) + 'dB')

                MESSAGE = b'\x1c' + b'\x01' + struct.pack(">B", int(temp))
                # 3 bytes to recieve
                garb = self.device_query( MESSAGE, 3)

            elif len(atten) == 0:

                MESSAGE = b'\x26' + b'\x01' + b'\x00'
                # 3 bytes to recieve
                data_raw = self.device_query( MESSAGE, 3)

                answer = 'Video Gain: ' + str(data_raw[2]*2) + ' dB'

                return answer

        elif test_flag == 'test':
            if len(atten) == 1:

                temp = float(atten[0])
                assert(temp >= 0 and temp <= 30), 'Incorrect attenuation'

            elif len(atten) == 0:

                return test_attenuation

    def mw_bridge_k_prm(self, *amplif):
        if test_flag != 'test':
            if len(amplif) == 1:

                temp = float(amplif[0])/22
                if int(temp) != temp:
                    general.message('Amplification value is rounded to the nearest availabe ' + str(int(temp)*22) + 'dB')

                MESSAGE = b'\x1a' + b'\x01' + struct.pack(">B", int(temp))
                # 3 bytes to recieve
                garb = self.device_query( MESSAGE, 3)

            elif len(amplif) == 0:

                MESSAGE = b'\x24' + b'\x01' + b'\x00'
                # 3 bytes to recieve
                data_raw = self.device_query( MESSAGE, 3)

                answer = 'Amplification PRM: ' + str(data_raw[2]*22) + ' dB'

                return answer

        elif test_flag == 'test':
            if len(amplif) == 1:

                temp = float(amplif[0])
                assert(temp >= 0 and temp <= 22), 'Incorrect amplification'

            elif len(amplif) == 0:

                return test_attenuation

    def mw_bridge_cut_off(self, *cutoff):
        if test_flag != 'test':
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

        elif test_flag == 'test':
            if len(cutoff) == 1:
                temp = str(cutoff[0])
                assert(temp == '30' or temp == '105' or temp == '300'), 'Incorrect cut-off frequency should be 30, 105 or 300'

            elif len(cutoff) == 0:

                return test_cut_off

    def mw_bridge_telemetry(self):
        if test_flag != 'test':

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

        elif test_flag == 'test':

            return test_telemetry

    def mw_bridge_initialize(self):
        if test_flag != 'test':

            MESSAGE = b'\x27' + b'\x01' + b'\x00'
            # 3 bytes to recieve
            data_raw = self.device_query( MESSAGE, 3 )

            general.message('Initialization done')

        elif test_flag == 'test':
            pass


def main():
    pass

if __name__ == "__main__":
    main()
