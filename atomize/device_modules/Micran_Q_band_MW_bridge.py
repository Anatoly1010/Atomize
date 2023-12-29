#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import fcntl
import array
import struct
import termios
import datetime
from math import exp, sqrt
from threading import Thread
import numpy as np
import atomize.device_modules.config.config_utils as cutil
import atomize.general_modules.general_functions as general

class Micran_Q_band_MW_bridge:
    #### Basic interaction functions
    def __init__(self):

        #### Inizialization
        # setting path to *.ini file
        self.path_current_directory = os.path.dirname(__file__)
        self.path_config_file = os.path.join(self.path_current_directory, 'config','Micran_q_band_mw_bridge_config.ini')

        # configuration data
        #config = cutil.read_conf_util(self.path_config_file)
        self.specific_parameters = cutil.read_specific_parameters(self.path_config_file)

        # auxilary dictionaries
        self.curr_dB = 60
        self.prev_dB = 60
        self.curr_dB_pin = 40
        # first initialization
        self.flag = 0
        self.state = 0
        self.mode_list = ['Limit', 'Arbitrary']
        self.p1 = 'None'
        self.internal_pause = '30 us'
        self.init_state = 0
        self.init_flags = 56

        # Read/Write data buffer
        # dataio[0] - addr
        # dataio[1] - count byte read
        # dataio[2] - data read/write
        self.dataio = array.array('L', [0, 0, 0])
        
        self.READ_BAR = 21
        self.WRITE_BAR = 22

        # Ranges and limits
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
            self.test_freq_str = 'Frequency: 6750 MHz'
            self.test_telemetry = 'Temperature: 28; State: INIT'
            self.test_attenuation = '0 dB'
            self.test_phase = '0 deg'
            self.test_cut_off = '300 MHz'
            self.test_attenuation_pin = '0 dB'

        #self.mw_bridge_rotary_vane(60, mode = 'Limit')

    # NEW
    def mw_bridge_open(self):
        if self.state == 0: 
            dev = '/dev/devfmc' 
            mode = 0o666 
            flags = os.O_RDWR #| os.O_CREAT
            self.m_device_fd = os.open(dev, flags, mode)

            if self.m_device_fd < 0:
               return 'ERROR open device - DEVICE NOT FOUND'
               self.state = 0
               #sys.exit()
            else:
                self.state = 1
                return 'DEVICE OPENED'
                #pass

    # NEW
    def mw_bridge_close(self):
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
            self.dataio[0] = int( address, 16)
            general.wait( self.internal_pause )
            fcntl.ioctl(self.m_device_fd, self.READ_BAR, self.dataio, 1)
            
            #return self.dataio[2]

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

            if address == '0x0010' and self.init_state == 1:
                self.dataio[2] = self.dataio[2] + self.init_flags

            self.dataio[1] = int( byte_to_write )
            self.dataio[0] = int( address, 16)

            general.wait( self.internal_pause )
            fcntl.ioctl(self.m_device_fd, self.WRITE_BAR, self.dataio, 1)
        
        elif self.test_flag == 'test':
            pass
    
    #### device specific functions
    def mw_bridge_name(self):
        if self.test_flag != 'test':
            answer = 'Mikran Q-band MW bridge'
            return answer
        elif self.test_flag == 'test':
            answer = 'Mikran Q-band MW bridge'
            return answer

    def mw_bridge_synthesizer(self, *freq):
        if self.test_flag != 'test':
            if len(freq) == 1:

                temp = str( freq[0] )
                n1 = ord(temp[-1]) << 0
                n2 = ord(temp[-2]) << 8
                n3 = ord(temp[-3]) << 16
                n4 = ord(temp[-4]) << 24
                # No more then 10000 MHz because of x5
                # address 0x0205 + 0x0206 for higher 10k+
                self.device_write( '0x0814', byte_to_write = 4, data_to_write = (n1 + n2 + n3 + n4), type_of_systems = 10 )
                self.device_write( '0x0818', byte_to_write = 4, data_to_write = 0, type_of_systems = 10 )
                self.device_write( '0x0008', byte_to_write = 4, data_to_write = 1, type_of_systems = 2, shift = 13 )

            elif len(freq) == 0:

                # get frequency read address 0x0002; 2**21
                self.device_write( '0x0008', byte_to_write = 4, data_to_write = 1, type_of_systems = 2, shift = 21 )
                self.device_read( '0x0840', byte_to_read = 4 )

                c1 = self.dataio[2] >> 24
                c2 = ( self.dataio[2] - (( self.dataio[2] >> 24 ) << 24) ) >> 16
                c3 = ( self.dataio[2] - (( self.dataio[2] >> 16 ) << 16) ) >> 8
                c4 = ( self.dataio[2] - (( self.dataio[2] >> 8 ) << 8) ) >> 0
                freq = int( chr( c1 ) + chr( c2 ) + chr( c3 ) + chr( c4 ) ) * 1

                answer = 'Frequency: ' + str( freq ) + ' MHz'

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
                    general.message('Attenuation value is rounded to the nearest available ' + str(int(temp)/2) + ' dB')

                # address 0x0200
                self.device_write( '0x0800', byte_to_write = 4, data_to_write = temp, type_of_systems = 10 )
                # c = 1 << 8
                self.device_write( '0x0008', byte_to_write = 4, data_to_write = 1, type_of_systems = 2, shift = 8 )
                # strob reg [8]
                # write address 0x0002; 2**8
                # read address 0x0002; 2**16

            elif len(atten) == 0:

                # read address 0x0002; 2**16
                self.device_write( '0x0008', byte_to_write = 4, data_to_write = 1, type_of_systems = 2, shift = 16 )
                self.device_read( '0x0840', byte_to_read = 4 )
                answer = 'Attenuator PRD: ' + str( self.dataio[2] / 2 ) + ' dB'
                
                return answer

        elif self.test_flag == 'test':
            if len(atten) == 1:

                temp = float(atten[0])
                assert(temp >= 0 and temp <= 31.5), 'Incorrect attenuation'

            elif len(atten) == 0:

                return self.test_attenuation

    # NEW
    def mw_bridge_att_pin(self, *atten):
        if self.test_flag != 'test':
            if len(atten) == 1:

                self.curr_dB_pin = round( float( atten[0] ), 1 )
                dac_code = self.pin_calibration( self.curr_dB_pin )
        
                # address 0x0201
                self.device_write( '0x0804', byte_to_write = 4, data_to_write = dac_code, type_of_systems = 10 )
                self.device_write( '0x0008', byte_to_write = 4, data_to_write = 1, type_of_systems = 2, shift = 9 )

            elif len(atten) == 0:


                self.device_write( '0x0008', byte_to_write = 4, data_to_write = 1, type_of_systems = 2, shift = 17 )
                self.device_read( '0x0840', byte_to_read = 4 )

                answer = self.pin_reverse_calibration( self.dataio[2] )
                if answer < -1:

                    for i in range(20):
                        
                        self.device_write( '0x0008', byte_to_write = 4, data_to_write = 1, type_of_systems = 2, shift = 17 )

                        self.device_read( '0x0840', byte_to_read = 4 )
                        answer = self.pin_reverse_calibration( self.dataio[2] )

                        if answer > -1:
                            break

                return 'PIN Attenuator: ' + str( answer ) + ' dB' 

        elif self.test_flag == 'test':
            if len(atten) == 1:

                self.curr_dB_pin = round( float( atten[0] ), 1 )
                dac_code = self.pin_calibration( self.curr_dB_pin )

                assert(dac_code >= 0 and dac_code <= 4095), 'Incorrect PIN attenuation'

            elif len(atten) == 0:

                return self.test_attenuation_pin

    def mw_bridge_att_prm(self, *atten):
        if self.test_flag != 'test':
            if len(atten) == 1:

                temp = float(atten[0])/2
                if int(temp) != temp:
                    general.message('Attenuation value is rounded to the nearest available ' + str(int(temp)*2) + ' dB')

                # address 0x0202
                self.device_write( '0x080c', byte_to_write = 4, data_to_write = temp, type_of_systems = 10 )
                self.device_write( '0x0008', byte_to_write = 4, data_to_write = 1, type_of_systems = 2, shift = 11 )

            elif len(atten) == 0:

                # read address 0x0002; 2**18
                self.device_write( '0x0008', byte_to_write = 4, data_to_write = 1, type_of_systems = 2, shift = 19 )
                self.device_read( '0x0840', byte_to_read = 4 )
                answer = 'Video Attenuation 1: ' + str( self.dataio[2]*2 ) + ' dB'

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
                    general.message('Attenuation value is rounded to the nearest available ' + str(int(temp)/2) + ' dB')

                # address 0x0203
                self.device_write( '0x0808', byte_to_write = 4, data_to_write = temp, type_of_systems = 10 )
                self.device_write( '0x0008', byte_to_write = 4, data_to_write = 1, type_of_systems = 2, shift = 10 )

            elif len(atten) == 0:

                # read address 0x0002; 2**19
                self.device_write( '0x0008', byte_to_write = 4, data_to_write = 1, type_of_systems = 2, shift = 18 )
                self.device_read( '0x0840', byte_to_read = 4 )
                answer = 'Video Attenuation 2: ' + str( self.dataio[2]/2 ) + ' dB'

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
                    # address 0x0204
                    self.device_write( '0x0810', byte_to_write = 4, data_to_write = 0, type_of_systems = 10 )
                    self.device_write( '0x0008', byte_to_write = 4, data_to_write = 1, type_of_systems = 2, shift = 12 )
                elif temp == '105':
                    self.device_write( '0x0810', byte_to_write = 4, data_to_write = 1, type_of_systems = 10 )
                    self.device_write( '0x0008', byte_to_write = 4, data_to_write = 1, type_of_systems = 2, shift = 12 )
                elif temp == '300':
                    self.device_write( '0x0810', byte_to_write = 4, data_to_write = 2, type_of_systems = 10 )
                    self.device_write( '0x0008', byte_to_write = 4, data_to_write = 1, type_of_systems = 2, shift = 12 )
                else:
                    general.message('Incorrect cut-off frequency')
                    sys.exit()

            elif len(cutoff) == 0:
                self.device_write( '0x0008', byte_to_write = 4, data_to_write = 1, type_of_systems = 2, shift = 20 )
                self.device_read( '0x0840', byte_to_read = 4 )

                if self.dataio[2] == 0:
                    freq = '30'
                elif self.dataio[2] == 1:
                    freq = '105'
                elif self.dataio[2] == 2:
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

                    if step >= 0:
                        # address 0x0207
                        MESSAGE = (int( '0x01', 16 ) << 24 ) +  (int( '0x02', 16 ) << 16 ) + step
                    elif step < 0:
                        MESSAGE = (int( '0x01', 16 ) << 24 ) +  (int( '0x02', 16 ) << 16 ) + 65535 + step

                    general.wait('500 ms')
                    self.device_write( '0x081c', byte_to_write = 4, data_to_write = MESSAGE, type_of_systems = 10 )
                    general.wait('500 ms')
                    self.device_write( '0x0008', byte_to_write = 4, data_to_write = 1, type_of_systems = 2, shift = 14 )

                    # 60 is a manual calibration
                    time_to_wait = abs( 60 * step )

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

                        MESSAGE = (int( '0x01', 16 ) << 24 ) +  (int( '0x01', 16 ) << 16 ) + 3

                        general.wait('500 ms')
                        self.device_write( '0x081c', byte_to_write = 4, data_to_write = MESSAGE, type_of_systems = 10 )
                        general.wait('500 ms')
                        self.device_write( '0x0008', byte_to_write = 4, data_to_write = 1, type_of_systems = 2, shift = 14 )

                        step = int( self.calibration( self.curr_dB ) ) - int( self.calibration( self.prev_dB ) )
                        
                        # 60 is a manual calibration
                        if self.flag == 0:
                            time_to_wait = 7000
                        else:
                            time_to_wait = abs( 60 * step )

                        self.p1 = Thread(target = general.wait, args = (str(time_to_wait) + ' ms', ) )
                        self.p1.start()

                        self.prev_dB = self.curr_dB
                        self.flag = 1

                    elif self.curr_dB == 0:
                        try:
                            self.p1.join()
                        except ( AttributeError, NameError, TypeError ):
                            pass

                        MESSAGE = (int( '0x01', 16 ) << 24 ) +  (int( '0x01', 16 ) << 16 ) + 2

                        general.wait('500 ms')
                        self.device_write( '0x081c', byte_to_write = 4, data_to_write = MESSAGE, type_of_systems = 10 )
                        general.wait('500 ms')
                        self.device_write( '0x0008', byte_to_write = 4, data_to_write = 1, type_of_systems = 2, shift = 14 )

                        step = int( self.calibration( self.curr_dB ) ) - int( self.calibration( self.prev_dB ) )
                        
                        # 60 is a manual calibration
                        if self.flag == 0:
                            time_to_wait = 7000
                        else:
                            time_to_wait = abs( 60 * step )

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

            self.device_read( '0x084c', byte_to_read = 4 )
            # split on registers
            ans_reg = [self.dataio[2] >> i & 1 for i in range(9)]

            answer = 'DATE: ' + str(datetime.datetime.now().strftime("%d %b %Y %H:%M")) + '\n' \
                             + 'ANSWER RECEIVED: ' + str( ans_reg[0] ) + '\n' + 'PARAMS UPDATED: ' + str( ans_reg[1] ) + '\n' + 'TI TOO SHORT: ' + str( ans_reg[2] ) + '\n' \
                             + 'HPA TOO LONG: ' + str( ans_reg[3] ) + '\n' + 'HPA ON INCORRECT: ' + str( ans_reg[4] ) + '\n' + 'HPA OFF INCORRECT: ' + str( ans_reg[5] ) + '\n' \
                             + 'EXT CLOCK CORRECT: ' + str( ans_reg[6] ) + '\n' + 'SHAPER TOO LONG: ' + str( ans_reg[7] ) + '\n' + 'DUTY CYCLE TOO LOW: ' + str( ans_reg[8] ) + '\n'

            
            return answer

        elif self.test_flag == 'test':

            return self.test_telemetry

    # CHANGED
    def mw_bridge_initialize(self, state = 'On'):
        if self.test_flag != 'test':

            if state == 'On':
                self.init_state = 1
                # 0x0004
                # External Start - 1; Internal Start - 0;
                self.device_write( '0x0010', byte_to_write = 4, data_to_write = 0, type_of_systems = 2, shift = 2 )
                # External Clock - 1; Internal Clock - 0;
                self.device_write( '0x0010', byte_to_write = 4, data_to_write = 1, type_of_systems = 2, shift = 3 )
                # Receiver LO Amp ON - 1; Receiver LO Amp OFF - 0;
                self.device_write( '0x0010', byte_to_write = 4, data_to_write = 1, type_of_systems = 2, shift = 4 )
                # AWG LO Amp ON - 1; AWG LO Amp OFF - 0;
                self.device_write( '0x0010', byte_to_write = 4, data_to_write = 1, type_of_systems = 2, shift = 5 )

                self.init_flags = 56

            elif state == 'Off':
                self.init_state = 0
                self.device_write( '0x0010', byte_to_write = 4, data_to_write = 0, type_of_systems = 2, shift = 0 )
                self.init_flags = 0

        elif self.test_flag == 'test':
            assert( state == 'On' or state == 'Off' ), 'Incorrect Initialization State argument. Only "On" and "Off" are allowed'

    # NEW
    def mw_bridge_reset(self):
        if self.test_flag != 'test':

            # 0x0002
            # Reset Flags
            self.device_write( '0x0008', byte_to_write = 4, data_to_write = 1, type_of_systems = 2, shift = 1 )
            general.wait('400 ms')

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

    def pin_calibration(self, x):
        # approximation curve
        # dB to DAC code
        return int( 3.5351895 * exp(-x * 0.043690547888) * (1156.64105732 + 39.2489705679 * x +  0.9778005577776837 * x**2) )

    def pin_reverse_calibration(self, x):
        # approximation curve
        # dB to DAC code
        return round( float( -0.00456187 * (-0.00912374004 - exp(-x * 0.5) ) * (1.724999386 * 10**6 - 36.3308391 * x - 0.09509760115 * x**2) ), 1)

def main():
    pass

if __name__ == "__main__":
    main()

