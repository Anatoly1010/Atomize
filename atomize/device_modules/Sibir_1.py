#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import struct 
from ctypes import * 
from socket import *
import numpy as np 
import scipy as sp
from scipy.fft  import rfft, rfftfreq
import atomize.main.local_config as lconf
import atomize.device_modules.config.config_utils as cutil
import atomize.general_modules.general_functions as general

def bytes_to_c_uint(a):
    return c_uint(int(a.hex(), 16))
def bytes_to_int(a):
    return int(a.hex(), 16)

class Sibir_1():

    # Number of accumulations N_A corresponding to the nav codes 0 - 5
    # (manual, Table 6)
    NAV_TO_NA = (1, 8, 16, 32, 64, 128)

    # Divisor of the accumulated ADC sum, see convert_arr_data_to_np_array().
    # Manual, Sec. 3.2 gives U_A = u/(N_A + 1) - 2048, which cannot be right: u
    # is an unsigned short, so the block cannot hold the raw sum of more than 16
    # samples of the 12-bit ADC and shifts it right instead, and the divisor
    # saturates. Measured with the excitation off, where the mean of the raw
    # array u_f is the ADC baseline times the divisor: the ratios come out
    # 1.000, 8.000, 16.000, 16.000, 16.000, 16.000, and the noise follows the
    # matching divisor/sqrt(N_A) to within 2%
    NAV_TO_DIV = (1, 8, 16, 16, 16, 16)

    def __init__(self):
        
        # setting path to *.ini file
        self.path_current_directory = lconf.load_config_device()
        self.path_config_file = os.path.join(self.path_current_directory, 'Sibir_1_config.ini')
       
        # configuration data
        #config = cutil.read_conf_util(self.path_config_file)
        self.specific_parameters = cutil.read_specific_parameters(self.path_config_file)

        # auxilary dictionaries

        # Ranges and limits
        self.ip_UDP = str(self.specific_parameters['udp_ip'])
        self.port_UDP = int(self.specific_parameters['udp_port'])
        self.sensor_number = int(self.specific_parameters['sensor'])

        #self.gaussmeter_pulse_length =  self.gaussmeter_length_90_deg_pulse
        #self.gaussmeter_sensor = self.NMR_sensor_number
        #self.Gaussmeter_Gain = self.NMR_gain

        if len(sys.argv) > 1:
            self.test_flag = sys.argv[1]
        else:
            self.test_flag = 'None'

        if self.test_flag != 'test':
            #---------SOCKET-----------#        
            self.sock = socket( AF_INET, SOCK_DGRAM )
            self.sock.settimeout(10)

            self.sock.connect( (self.ip_UDP, self.port_UDP ) )

            #----------INSIDE---REGISTER-------
            self.set_reg = [self.set_0_reg , self.set_1_reg , self.set_2_reg , self.set_3_reg , self.set_4_reg , 
                            self.set_5_reg , self.set_6_reg , self.set_7_reg , self.set_8_reg , self.set_9_reg , 
                            self.set_10_reg, self.set_11_reg, self.set_12_reg, self.set_13_reg, self.set_14_reg,
                            self.set_15_reg, self.set_16_reg, self.set_17_reg, self.set_18_reg, self.set_19_reg, 
                            self.set_20_reg, self.set_21_reg, self.set_22_reg, self.set_23_reg, self.set_24_reg, 
                            self.set_25_reg, self.set_26_reg, self.set_27_reg, self.set_28_reg, self.set_29_reg,
                            self.set_30_reg, self.set_31_reg]
            
            self.reg = (c_uint * 32)()

            self.gain_value = 0          # reg 0: dB           
            self.mode_point = 0
            self.num_point  = 8192       # reg 1: 3 - 53248   2 - 32768  1 - 16384  0 - 8192  :  i*2**14 + 8192   
            self.time_90_deg_pulse = 0   # reg 2: micro second  
            self.mode_nav = 1            # reg 5: number of savings Na = 1,8,16,32,64,128 
                                         #                    mode_nav = 0,1, 2, 3, 4,  5
            
            for i in range(6): self.write_reg_i(i)
            
            #------------SYNTHESIZER-----------
            # self.command_synt_bytes =[  A    ,    D0   ,   D1    ,    D2   ,    D3    , num-bit  ] 
            self.command_synt_bytes = [b'\x10', b'\xb8' , b'\x00' , b'\x00' , b'\x00'  ,  b'\x10' ]
            self.init_synthesizer()
            
            for f in self.set_reg:f() # update
            #-----------SETTING----------------
            self.Fref = 32767.846
            self.N    = 8192
            self.T    = 1/2048 # ms; ADC sampling frequency is Fref/16 = 2.048 MHz
                               # (manual, Sec. 3.2), so the frequency axis is in kHz
            self.Fr   = 42.57637
            self.num_exp = 1
            #----------NMR---LINE---WINDOW-----
            self.IF         = 480.0  # kHz; F2 = F1 + 480 kHz (manual, Sec. 5)
            self.band_width =  50.0  # kHz; half-width of the search window around IF
            self.sn_min     =   5.0  # S/N_MIN, usually 5 - 20 (manual, Sec. 6, Stage 2)
            self.N_fft      = 524288 # zero padding used for the field determination
                                     # (manual, Sec. 6, Stage 3); 3.9 Hz per bin
            self.N_disp     =  53248 # zero padding of the spectrum returned to the
                                     # user; kept small enough to be plotted live
            self.verify_synt = False # read the synthesizer frequencies back after
                                     # every setting (manual, Sec. 5)
            #----------FIND---NOIZE-----------
            self.NOIZE = 1
            self.noize_state = None  # acquisition settings NOIZE was measured at
            self.noize_each_time = False # re-measure the noise before every single
                                     # field measurement instead of only after a
                                     # change of the acquisition settings

            # problem with connection?!
            # 2025-04-17
            self.NOIZE = self.NMR_find_noize(3000)
            #self.find_noize()
            #----------set pi/2 impulse--------
            #self.time_90_deg_pulse = 7.5  # reg 2:
            #self.write_reg_i(2)
            self.B = 100.0

        else:
            self.set_reg = [self.set_0_reg , self.set_1_reg , self.set_2_reg , self.set_3_reg , self.set_4_reg , 
                            self.set_5_reg , self.set_6_reg , self.set_7_reg , self.set_8_reg , self.set_9_reg , 
                            self.set_10_reg, self.set_11_reg, self.set_12_reg, self.set_13_reg, self.set_14_reg,
                            self.set_15_reg, self.set_16_reg, self.set_17_reg, self.set_18_reg, self.set_19_reg, 
                            self.set_20_reg, self.set_21_reg, self.set_22_reg, self.set_23_reg, self.set_24_reg, 
                            self.set_25_reg, self.set_26_reg, self.set_27_reg, self.set_28_reg, self.set_29_reg,
                            self.set_30_reg, self.set_31_reg]
            self.reg = (c_uint * 32)()
            self.sensor_number = 3   
            self.gain_value = 31          # reg 0: dB           
            self.mode_point = 0 
            self.num_point  = 1000        # reg 1: 3 - 53248   2 - 32768  1 - 16384  0 - 8192  :  i*2**14 + 8192   
            self.time_90_deg_pulse = 20   # reg 2: micro second  
            self.mode_nav = 3  
            self.command_synt_bytes = [b'\x10', b'\xb8' , b'\x00' , b'\x00' , b'\x00'  ,  b'\x10' ]
            for f in self.set_reg: f() # update
            self.Fref = 32767.846
            self.Fr   = 42.57637
            self.N    = 53248
            self.T    = 1/2048
            self.num_exp = 1
            self.IF         = 480.0
            self.band_width =  50.0
            self.sn_min     =   5.0
            self.N_fft      = 524288
            self.N_disp     =  53248
            self.verify_synt = False
            self.NOIZE = 0
            self.noize_state = None
            self.noize_each_time = False
            self.NOIZE = self.NMR_find_noize(3000)
            self.B = 100.0

    #def gaussmeter_name():
    def gaussmeter_name(self):
        if self.test_flag != 'test':
            answer = 'Sibir 1 NMR Gaussmeter'
            return answer
        elif self.test_flag == 'test':
            answer = 'Sibir 1 NMR Gaussmeter'
            return answer

    def gaussmeter_points(self, *points):
        if self.test_flag != 'test':
            if len(points) == 1:
                if int(points[0])>=0 and int(points[0]) <= 53248:
                    if int(points[0])>=0 and int(points[0]) <= 8192:
                        self.num_point = int(points[0])
                        self.NMR_number_point(0)
                        if int(points[0]) != 8192:
                            general.message(f"Np is set to {8192} points on the device; the first {int(points[0])} points of the FID will be used.")
                    elif int(points[0])>=8193 and int(points[0]) <= 16384:
                        self.num_point = int(points[0])
                        self.NMR_number_point(1)
                        if int(points[0]) != 16384:
                            general.message(f"Np is set to {16384} points on the device; the first {int(points[0])} points of the FID will be used.")                        
                    elif int(points[0])>=16385 and int(points[0]) <= 32768:
                        self.num_point = int(points[0])
                        self.NMR_number_point(2)
                        if int(points[0]) != 32768:
                            general.message(f"Np is set to {32768} points on the device; the first {int(points[0])} points of the FID will be used.")                        
                    elif int(points[0])>=32769 and int(points[0]) <= 53248:
                        self.num_point = int(points[0])
                        self.NMR_number_point(3)
                        if int(points[0]) != 53248:
                            general.message(f"Np is set to {53248} points on the device; the first {int(points[0])} points of the FID will be used.")                        

            elif len(points) == 0:       
                return self.num_point

        elif self.test_flag == 'test':
            if len(points) == 1:
                if int(points[0])>=0 and int(points[0]) <= 53248:
                    pass
                else:
                    assert(1 == 2), 'Invalid number of points; points: [8192, 16384, 32768, 53248]'
            elif len(points) == 0:       
                return self.num_point 
            else:
                assert(1 == 2), 'Invalid number of points; points: [8192, 16384, 32768, 53248]'

    def gaussmeter_number_of_averages(self, *nav):
        if self.test_flag != 'test':
            if len(nav) == 1:
                _nav = int(nav[0])
                if _nav >=0 and _nav <= 2048:
                    if _nav >=0 and _nav <= 1:
                        self.NMR_nav(0)
                        self.num_exp = 1
                        if _nav != 1:
                            general.message(f"The specified number of averages cannot be set. The following number was set instead: {1}")
                    elif _nav>=2 and _nav <= 8:
                        self.NMR_nav(1)
                        self.num_exp = 1
                        if _nav != 8:
                            general.message(f"The specified number of averages cannot be set. The following number was set instead: {8}")
                    elif _nav>=9 and _nav <= 16:
                        self.NMR_nav(2)
                        self.num_exp = 1
                        if _nav != 16:
                            general.message(f"The specified number of averages cannot be set. The following number was set instead: {16}")
                    elif _nav>=17 and _nav <= 32:
                        self.NMR_nav(3)
                        self.num_exp = 1
                        if _nav != 32:
                            general.message(f"The specified number of averages cannot be set. The following number was set instead: {32}")
                    elif _nav>=33 and _nav <= 64:
                        self.NMR_nav(4)
                        self.num_exp = 1
                        if _nav != 64:
                            general.message(f"The specified number of averages cannot be set. The following number was set instead: {64}")
                    elif _nav>=65 and _nav <= 128:
                        self.NMR_nav(5)
                        self.num_exp = 1
                        if _nav != 128:
                            general.message(f"The specified number of averages cannot be set. The following number was set instead: {128}")
                    elif _nav>=129 and _nav <= 256:
                        self.NMR_nav(5)
                        self.num_exp = 2
                        if _nav != 256:
                            general.message(f"The specified number of averages cannot be set. The following number was set instead: {256}")
                    elif _nav>=257 and _nav <= 512:
                        self.NMR_nav(5)
                        self.num_exp = 4
                        if _nav != 512:
                            general.message(f"The specified number of averages cannot be set. The following number was set instead: {512}")                        
                    elif _nav>=513 and _nav <= 1024:
                        self.NMR_nav(5)
                        self.num_exp = 8
                        if _nav != 1024:
                            general.message(f"The specified number of averages cannot be set. The following number was set instead: {1024}")                        
                    elif _nav>=1025 and _nav <= 2048:
                        self.NMR_nav(5)
                        self.num_exp = 16
                        if _nav != 2048:
                            general.message(f"The specified number of averages cannot be set. The following number was set instead: {2048}")                        
                    
            elif len(nav) == 0:
                # NMR_nav() returns the code nav (0 - 5), not the number of
                # accumulations N_A itself (manual, Table 6)
                #return self.NMR_nav() * self.num_exp
                return self.NAV_TO_NA[self.NMR_nav()] * self.num_exp

        elif self.test_flag == 'test':
            if len(nav) == 1:
                _nav = int(nav[0])
                if  _nav>=0 and _nav <= 2048:
                    pass 
                else:
                    assert(1 == 2), 'Invalid number of averages, number: [1, 8, 16, 32, 64, 128, 256, 512, 1024, 2048]'
            elif len(nav) == 0:
                #return self.mode_nav * self.num_exp
                return self.NAV_TO_NA[self.mode_nav] * self.num_exp
            else:
                assert(1 == 2), 'Invalid number of averages, number: [1, 8, 16, 32, 64, 128, 256, 512, 1024, 2048]'

    def gaussmeter_search(self, B_lower, B_upper, step):
        B1   = int(B_lower)
        B2   = int(B_upper)
        st   = int(step)
        N    = int((B2-B1)/st)
        # Manual, Sec. 6, Stage 4: the excitation pulse only covers B_STEP =
        # 10/T90 mT = 100/T90 G, a wider step can step over the NMR signal
        if self.time_90_deg_pulse > 0:
            st_max = 100 / self.time_90_deg_pulse
            if st > st_max:
                general.message('The scan step of ' + str(st) + ' G is wider than 100/T90 = ' \
                                 + str(round(st_max, 2)) + ' G, the NMR signal can be missed')
        Bref = self.NMR_search(B1,B2,N)
        #self.B = Bref
        return Bref

    def gaussmeter_set_field(self, *B):
        if len(B) == 1:
            F = int(self.Fr *  float(B[0])/10)
            #general.message(F)
            #self.NMR_freq_synthesizer(F)
            self.B = float(B[0])
        elif len(B) == 0:
            return self.NMR_freq_synthesizer()/self.Fr*10
        if self.test_flag == 'test':
            assert( (len(B) == 1)  or (len(B) == 0) ), 'Invalid argument, B: float'

    def gaussmeter_field(self):
        if self.test_flag != 'test':
            Fref = int(self.Fr *  self.B/10)
            self.NMR_freq_synthesizer(Fref)
            # Manual, Sec. 6, Stage 2: NOISE_MAX has to be measured with the
            # excitation pulse switched off under the same conditions as the
            # signal. Doing it once at start up, at gain 0 and with a different
            # number of points, makes the S/N ratio meaningless
            if self.noize_each_time or self.noize_state != self.acquisition_state():
                self.NMR_find_noize()
            #all_arr = np.zeros(self.num_point)
            #for i in range(self.num_exp):
            #    self.NMR_start_experiment()
            #    arr = self.NMR_FID_array().T
            #    all_arr=all_arr + arr[:self.num_point]
            #all_arr= all_arr / self.num_exp
            all_arr = self.acquire_FID()
            #arr = all_arr - np.mean(all_arr)
            #arr=np.append(arr,np.zeros(53248 - arr.shape[0]))
            #W,I = self.get_rfft_FID(arr)
            W,I = self.process_FID(all_arr, self.N_fft)
            # The NMR line can only show up inside a narrow window around the
            # intermediate frequency F2 - F1 = 480 kHz, since the excitation
            # frequency has to be within a few tens of kHz of the NMR frequency
            # for the signal to be seen at all (manual, Sec. 6, Stage 2).
            # Searching the whole 0 - 1024 kHz band instead locks onto
            # out-of-band interference (e.g. the ever-present 12.5 kHz line,
            # which accumulates coherently just like the signal); picking that
            # peak up shifts the reported field by about 110 G.
            band = self.nmr_band(W)
            #S_n = np.max(I[2:])/self.NOIZE
            S_n = np.max(I[band])/self.NOIZE
            # the returned spectrum is computed with a much coarser zero padding:
            # it covers the whole 0 - 1024 kHz band, so the interference stays
            # visible, but it is small enough to be plotted after every point
            I_out = self.process_FID(all_arr, self.N_disp)[1]
            #if S_n > 0:
            if S_n > self.sn_min:
                #F_cl = self.z(W[2:], I[2:],Fref)
                F_cl = self.z_integral(W[band], I[band])
                B_cl = (-F_cl+Fref+self.IF)/self.Fr*10
                #return arr[2:] , I[2:] , round(B_cl, 4) , S_n
                return all_arr , I_out[2:] , round(B_cl, 4) , S_n
            else:
                #return arr[2:] , I[2:] , 0 , S_n
                return all_arr , I_out[2:] , 0 , S_n

        elif self.test_flag == 'test':
            return np.zeros(500) , np.zeros(500) , self.B , 6

    def gaussmeter_gain(self, *gain):
        if self.test_flag != 'test':
            if len(gain) == 1:
                if int(gain[0])>=0 and int(gain[0]) <= 31:
                    self.gain_value = int(gain[0])
                    #self.reg[0] = c_uint(gain[0])   # raises for a float argument
                    self.reg[0] = c_uint(int(gain[0]))
                    self.write_reg_i(0)
            elif len(gain) == 0:
                return self.read_reg_i(0)

        elif self.test_flag == 'test':
            if len(gain) == 1:  
                if gain[0]>=0 and gain[0] <= 31:
                    self.gain_value = int(gain[0])
                    #self.reg[0] = c_uint(gain[0])
                    self.reg[0] = c_uint(int(gain[0]))
                else:
                    assert(1 == 2), 'Invalid value of the preamplifier gain; gain: int [0 - 31]'
            elif len(gain) == 0:
                return self.reg[0]
            else:
                assert(1 == 2), 'Invalid value of the preamplifier gain; gain: int [0 - 31]'

    def gaussmeter_pulse_length(self, *time_pulse):
        if self.test_flag != 'test':
            if len(time_pulse) == 1:
                if time_pulse[0]>=0 and time_pulse[0] <= 40:
                    self.time_90_deg_pulse = time_pulse[0]
                    self.set_2_reg()
                    self.write_reg_i(2)    
            elif len(time_pulse) == 0:
                # register 2 holds the code T90*32.768, the documented unit of
                # this function is us (manual, Table 3)
                #return self.read_reg_i(2)
                return round(self.read_reg_i(2) / 32.768, 2)

        elif self.test_flag == 'test':
            if len(time_pulse) == 1:  
                if time_pulse[0]>=0 and time_pulse[0] <= 40:
                    self.time_90_deg_pulse = time_pulse[0]
                    self.set_2_reg()
                else:
                    assert(1 == 2), 'Invalid length of the pi/2 pulse, length: int [0 - 40]'
            elif len(time_pulse) == 0:
                #return  self.reg[2]
                return  round(self.reg[2] / 32.768, 2)
            else:
                assert(1 == 2), 'Invalid length of the pi/2 pulse, length: int [0 - 40]'

    def gaussmeter_sensor_number(self, *sensor_number):
        if self.test_flag != 'test':
            if len(sensor_number) == 1:
                if sensor_number[0]>=1 and sensor_number[0] <= 4:
                    self.sensor_number = sensor_number[0]
                    self.update_reg()
                    for i in range(6):
                        self.write_reg_i(i)
            elif len(sensor_number) == 0:
                return self.sensor_number

        elif self.test_flag == 'test':
            if len(sensor_number) == 1:  
                if sensor_number[0]>=1 and sensor_number[0] <= 4:
                    self.sensor_number = sensor_number[0]
                else:
                    assert(1 == 2), 'Invalid sensor number; number: [1, 2, 3, 4]'
            elif len(sensor_number) == 0:
                return  self.sensor_number
            else:
                assert(1 == 2), 'Invalid sensor number; number: [1, 2, 3, 4]'

### Auxiliary functions
    def nmr_band(self, W):
        # Boolean mask selecting the part of the spectrum where the NMR line
        # can appear: IF +/- band_width. Everything outside is interference.
        return np.abs(W - self.IF) <= self.band_width

    def acquisition_state(self):
        # Everything that changes the amplitude scale of the spectrum and
        # therefore invalidates the stored noise level
        return (self.gain_value, self.mode_nav, self.mode_point, self.num_point,
                self.num_exp, self.sensor_number, self.N_fft)

    def acquire_FID(self):
        # num_exp repetitions of the measurement cycle, averaged. num_exp is
        # larger than one only above 128 accumulations, which is the maximum
        # the block itself can do (manual, Table 6)
        all_arr = np.zeros(self.num_point)
        for i in range(self.num_exp):
            self.NMR_start_experiment()
            arr = self.NMR_FID_array().T
            all_arr = all_arr + arr[:self.num_point]
        return all_arr / self.num_exp

    def process_FID(self, arr, N):
        # Identical processing of the noise and of the signal, so that their
        # maxima can be divided by each other (manual, Sec. 6, Stages 2 and 3):
        # remove the DC offset and pad with zeros up to N points
        arr = arr - np.mean(arr)
        arr = np.append(arr, np.zeros(N - arr.shape[0]))
        return self.get_rfft_FID(arr)

    def z_integral(self, X, Y):
        # Manual, Sec. 6, Stage 3: subtract a pedestal of 0.2*S_MAX from the
        # spectrum and take the frequency that cuts the area of the remaining
        # "bell" in half, the triangular pieces at both edges included.
        # This replaces z(), which returned the midpoint between the two
        # crossings of the 0.2*S_MAX level and fell back to the position of the
        # maximum - i.e. to the bin grid - as soon as the level was crossed
        # anywhere else in the spectrum.
        k     = int(np.argmax(Y))
        level = 0.2 * Y[k]
        if not Y[k] > 0:
            return X[k]

        left = k
        while left > 0 and Y[left - 1] > level:
            left -= 1
        right = k
        while right < len(Y) - 1 and Y[right + 1] > level:
            right += 1

        x = list(X[left:right + 1])
        y = list(Y[left:right + 1] - level)
        # the bell is cut where it crosses the pedestal, somewhere between the
        # samples left-1/left and right/right+1: add these two crossing points
        # so that the edge triangles are included in the integral
        if left > 0 and Y[left] > Y[left - 1]:
            x.insert(0, X[left] - (X[left] - X[left - 1]) * y[0] / (Y[left] - Y[left - 1]))
            y.insert(0, 0.0)
        if right < len(Y) - 1 and Y[right] > Y[right + 1]:
            x.append(X[right] + (X[right + 1] - X[right]) * y[-1] / (Y[right] - Y[right + 1]))
            y.append(0.0)
        x = np.array(x, dtype = float)
        y = np.array(y, dtype = float)

        h     = np.diff(x)
        area  = 0.5 * (y[:-1] + y[1:]) * h
        total = np.sum(area)
        if not total > 0:
            return X[k]

        cum  = np.cumsum(area)
        j    = min(int(np.searchsorted(cum, 0.5 * total)), len(area) - 1)
        rest = 0.5 * total - (cum[j - 1] if j > 0 else 0.0)
        # area of the j-th piece up to t:  y[j]*t + (y[j+1] - y[j])/h[j] * t^2/2
        a = 0.5 * (y[j + 1] - y[j]) / h[j]
        b = y[j]
        t = rest / b if b > 0 else 0.0
        if abs(a) > 1e-12:
            d = b * b + 4.0 * a * rest
            if d >= 0:
                _t = (-b + np.sqrt(d)) / (2.0 * a)
                if 0.0 <= _t <= h[j]:
                    t = _t
        return x[j] + t

    def z(self, X, Y, F):
        m = 0.2 * np.max(Y)
        Y1 = Y[:-1]
        Y2 = Y[1: ]
        X1 = X[:-1]
        X2 = X[1: ]

        a1 = (Y2 - Y1) / (X2 - X1)
        b1 = (Y1 * X2 - Y2 * X1) / (X2 - X1)
        _x = (m - b1) / a1
        i = (X1 < _x) & (_x < X2)
        if _x[i].shape[0] == 2:
            q = _x[i]
            return np.sum(q) / (2)
        else:
            return X[np.where(Y==np.max(Y))[0][0]]

    def NMR_nav(self, *nav):
        if self.test_flag != 'test':
            if len(nav) == 1:
                if nav[0]>=0 and nav[0] <= 5:
                    self.mode_nav = nav[0]
                    self.reg[5] = nav[0]
                    self.write_reg_i(5)    
            elif len(nav) == 0:
                return self.read_reg_i(5)

            else:
                general.message("Invalid code of the number of averages")
                sys.exit()   

        elif self.test_flag == 'test':
            if len(nav) == 1:  
                if nav[0]>=0 and nav[0] <= 5:
                    self.mode_nav = nav[0]
                    self.reg[5] = nav[0]
                else:
                    assert (1 == 2), 'Invalid code of the number of averages, correct = [0..5]'
            elif len(nav) == 0:
                return  self.reg[5]
            else:
                assert (1 == 2), 'Invalid code of the number of averages'

    def NMR_number_point(self, *point):
        if self.test_flag != 'test':
            if len(point) == 1:
                if point[0]>=0 and point[0] <= 3:
                    self.mode_point = point[0]
                    self.reg[1] = point[0]
                    self.write_reg_i(1)    
            elif len(point) == 0:
                return self.read_reg_i(1)

            else:
                general.message("Invalid code of the number of points")
                sys.exit()   

        elif self.test_flag == 'test':
            if len(point) == 1:  
                if point[0]>=0 and point[0] <= 3:
                    self.mode_point = point[0]
                    self.reg[1] = point[0]
                else:
                    assert (1 == 2), 'Invalid code of the number of points, correct = [0..3]'
            elif len(point) == 0:
                return  self.reg[1]
            else:
                assert (1 == 2), 'Invalid code of the number of points'

    def NMR_start_experiment(self):
        if self.test_flag != 'test':
            self.start_experiment()   
        elif self.test_flag == 'test':
            pass

    def NMR_freq_synthesizer(self, *freq):
        if self.test_flag != 'test':
            if len(freq) == 1:
                if freq[0]>=1000 and freq[0] <= 100000:
                    self.write_freq_to_synthesizer(freq[0])    
            elif len(freq) == 0:
                # read_freq_to_synthesizer() returns both channels, (F1, F2);
                # F1 = G*B_SET is the one the field is derived from
                #return self.read_freq_to_synthesizer()
                return self.read_freq_to_synthesizer()[0]

            else:
                general.message("Invalid frequency")
                sys.exit()   

        elif self.test_flag == 'test':
            if len(freq) == 1:  
                if freq[0]>=1000 and freq[0] <= 100000:
                    self.reg[31] = c_uint(int(freq[0]))
                else:
                    assert (1 == 2), 'Invalid frequency, correct = [1000..10000]'
            elif len(freq) == 0:
                return  int(self.reg[31])
            else:
                assert (1 == 2), 'Invalid frequency'

    def NMR_FID_array(self):
        if self.test_flag != 'test':
            return self.read_arr_all_signal()  
        elif self.test_flag == 'test':
            return np.zeros(53248) + 1

    def NMR_search(self, B1, B2, N):
        if self.test_flag != 'test':
            F1 = int(self.Fr *  B1 / 10)
            F2 = int(self.Fr *  B2 / 10)
            #all_F = np.linspace(F1, F2, N)
            all_F = np.linspace(F1, F2, N + 1)  # N intervals are N + 1 points
            # Manual, Sec. 6, Stage 4: the noise level is measured once, for the
            # centre of the scanned range
            self.NMR_find_noize( (B1 + B2) / 2 )
            S_N = []
            for F in all_F:
                F = int(F)
                self.NMR_freq_synthesizer(F)
                #self.NMR_start_experiment()
                #arr = self.NMR_FID_array().T
                #W, I = self.get_rfft_FID(arr)
                W, I = self.process_FID(self.acquire_FID(), self.N_fft)
                #S_N.append(max(I[2:]) / self.NOIZE)
                S_N.append(np.max(I[self.nmr_band(W)]) / self.NOIZE)
                general.message('S/N: ' + str(round(S_N[-1], 2)) + '; Field: ' + str(round(F / self.Fr * 10, 4)) + ' G')

            L = S_N.index(max(S_N))
            Bref = all_F[L] / self.Fr * 10
            if max(S_N) < self.sn_min:
                general.message('No NMR signal found in the specified range; the best S/N is ' \
                                 + str(round(max(S_N), 2)) + ', S/N_MIN is ' + str(self.sn_min))
            return Bref
        elif self.test_flag == 'test':
            return 2000

    # Superseded by gaussmeter_field(). Never called, and it does not run: FF and
    # Fr are undefined, and the sign of the offset disagrees with Stage 3 of
    # Sec. 6 of the manual
    #def NMR_clarification(self, Bref):
    #    Fref = int(self.Fr * Bref / 10)
    #    self.NMR_freq_synthesizer(Fref)
    #    self.NMR_start_experiment()
    #    arr = self.NMR_FID_array().T
    #    W,I = self.get_rfft_FID(arr)
    #    F_cl = W[ list(I).index(max(I[2:])) ]
    #    return (FF + Fref - 480) / Fr * 10

    def NMR_find_noize(self, *B):
        # Manual, Sec. 6, Stage 2: measure the spectrum with the excitation
        # pulse switched off and take its maximum as NOISE_MAX. Called without
        # an argument the current synthesizer setting is kept, so that the noise
        # is measured at the field the signal is then looked for at.
        if self.test_flag != 'test':
            if len(B) == 1:
                self.NMR_freq_synthesizer(int(self.Fr * B[0] / 10))
            # read_reg_i(2) returns the register code (T90*32.768), not us, and
            # restoring it through gaussmeter_pulse_length() would silently fail
            # the 0 - 40 us check and leave the excitation pulse switched off
            #T0 = self.gaussmeter_pulse_length()
            T0 = self.time_90_deg_pulse
            self.gaussmeter_pulse_length(0)
            #self.NMR_start_experiment()
            #W,I = self.get_rfft_FID(self.NMR_FID_array().T)
            # exactly the same number of points, averaging and zero padding as
            # in gaussmeter_field(), otherwise the two maxima are not comparable
            W,I = self.process_FID(self.acquire_FID(), self.N_fft)
            self.gaussmeter_pulse_length(T0)
            # The same window as in gaussmeter_field(): with T90 = 0 the whole
            # spectrum is interference, and the 12.5 kHz line would otherwise
            # be taken as the noise level
            #self.NOIZE = max(I[2:])
            self.NOIZE = np.max(I[self.nmr_band(W)])
            self.noize_state = self.acquisition_state()
            return self.NOIZE
        elif self.test_flag == 'test':
            return 1
    
    def set_0_reg(self): 
        self.reg[0] = c_uint(self.gain_value) 
    def set_1_reg(self):
        self.reg[1] = c_uint(self.mode_point)
    def set_2_reg(self):
        code_t90=round(self.time_90_deg_pulse*32.768)
        self.reg[2] = c_uint(code_t90) 
    def set_3_reg(self):
        self.reg[3] = c_uint(80)
    def set_4_reg(self):
        if self.mode_nav > 0 and (self.sensor_number == 2 or self.sensor_number == 4): 
            self.reg[4] =  c_uint(40*16)
        else:
            self.reg[4] =  c_uint(0)
    def set_5_reg(self):
        if self.mode_nav >=0 and self.mode_nav <=5:
            self.reg[5] = c_uint(self.mode_nav )
    def set_6_reg(self):
        pass
    def set_7_reg(self):
        pass
    def set_8_reg(self):
        pass
    def set_9_reg(self):
        pass
    def set_10_reg(self):
        pass
    def set_11_reg(self):
        pass
    def set_12_reg(self):
        pass
    def set_13_reg(self):
        # NB: registers 13 and 15 are swapped on page 6 of the manual. Confirmed
        # by the manufacturer: register 15 takes the address and D0, register 13
        # takes D3 and the total number of transferred bits. The code below is
        # correct, the manual is not
        a = self.command_synt_bytes
        self.reg[13] = bytes_to_c_uint(a[4]+a[5])
    def set_14_reg(self):
        a = self.command_synt_bytes
        self.reg[14] = bytes_to_c_uint(a[2]+a[3])   
    def set_15_reg(self):
        a = self.command_synt_bytes
        self.reg[15] = bytes_to_c_uint(a[0]+a[1]) 
    def set_16_reg(self):
        pass
    def set_17_reg(self):
        pass
    def set_18_reg(self):
        pass
    def set_19_reg(self):
        pass
    def set_20_reg(self):
        pass
    def set_21_reg(self):
        pass
    def set_22_reg(self):
        pass
    def set_23_reg(self):
        pass
    def set_24_reg(self):
        pass
    def set_25_reg(self):
        pass
    def set_26_reg(self):
        pass
    def set_27_reg(self):
        pass
    def set_28_reg(self):
        pass
    def set_29_reg(self):
        pass
    def set_30_reg(self):
        pass
    def set_31_reg(self):
        self.reg[31] = c_uint(0)

    def update_reg(self):
        for f in self.set_reg:
            f()

    def __del__(self):
        if self.test_flag != 'test':
            self.sock.close() 
        elif self.test_flag == 'test':
            pass
        
    def show_reg(self):
        for i in range(32):
            print("[",i,"] ",hex(self.reg[i]))

#------------------0x00--------------------------------------------------------
    def get_command_write_reg_i(self, i):
        command = b'\x00' + (i).to_bytes(1, byteorder = "big") + (self.reg[i]).to_bytes(2, byteorder = "big") 
        return  command

    def check_out_write_reg_i(self, out, i):
        if out[0] == bytes_to_int(b'\x10') and out[1] == bytes_to_int(b'\x00') and out[2] == i and out[3] == bytes_to_int(b'\x0F'):
            pass
        else:
            general.message("An error occurs when writing to the register" , out)     

    def write_reg_i(self, i): # test ok
        self.set_reg[i]()
        command = self.get_command_write_reg_i(i)
        self.sock.sendto( command , (self.ip_UDP, self.port_UDP) )
        data_raw_answer, addr = self.sock.recvfrom( int(4) )
        self.check_out_write_reg_i(data_raw_answer,i)
        
#---------------------0x04-----------------------------------------------------
    def get_command_read_reg_i(self, i):
        command = b'\x04' + (i).to_bytes(1,byteorder = "big") + b'\x00\x00'
        return command 

    def check_out_read_reg_i(self, out_f, out_s, i):
        if out_f[0] == bytes_to_int(b'\x10') and out_f[1] == bytes_to_int(b'\x04') and out_f[2] == i and out_s[1] == i and out_f[3] == bytes_to_int(b'\x0F'):
            pass
        else:
            general.message("An error occurs when reading from the register")     

    def read_reg_i(self, i):
        command = self.get_command_read_reg_i(i)
        self.sock.sendto( command , (self.ip_UDP, self.port_UDP) )
        data_raw_answer, addr = self.sock.recvfrom( int(4) )
        # The manual (Fig. 7, Table 5) makes the 0xF4 packet 6 bytes long, with
        # the register content in bytes 2-5. The block sends 4: measured
        # "f4 05 00 01" for register 5, so the content is bytes 2-3. The buffer
        # is oversized because recvfrom() drops whatever does not fit in it
        data_raw_data, addr = self.sock.recvfrom( int(64) )
        self.check_out_read_reg_i(data_raw_answer,data_raw_data,i)
        return  bytes_to_int(data_raw_data[2:4])

#------------------------0x01--------------------------------------------------
    def get_command_read_arr_all_signal(self, i, first = 0):
        # bytes 2-3 are the first requested page, bytes 4-5 the last one
        # (manual, Fig. 1)
        #command = b'\x01\x09\x00' + (0).to_bytes(1, byteorder = "big") +b'\x00'+ (i).to_bytes(1, byteorder = "big")
        command = b'\x01\x09' + (first).to_bytes(2, byteorder = "big") + (i).to_bytes(2, byteorder = "big")
        return command

    def convert_arr_data_to_np_array(self, data):
        u_f_1 = np.array([ data[2*i] << 8 for i in range(len(data) // 2)])
        u_f_2 = np.array([ data[2*i + 1] for i in range(len(data) // 2)])
        u_f = u_f_1 + u_f_2
        #if self.mode_nav == 0:
        #    Na = 0
        #elif self.mode_nav == 1:
        #    Na = 7
        #else:
        #    Na = 15
        #Na = 8 #-------------------------FIX-----------
        #U  = u_f / (Na+1) - 2047
        # The measured divisor is in NAV_TO_DIV; the hardcoded 9 above was
        # correct only for nav code 1 (N_A = 8) and rescaled the amplitude by
        # roughly N_A/8 otherwise. This affects the amplitude scale and the DC
        # pedestal only: gaussmeter_field() subtracts the mean before the FFT,
        # so the measured field does not depend on it
        U  = u_f / self.NAV_TO_DIV[self.mode_nav] - 2048
        return  U

    def check_out_read_arr_all_signal(self, out):
        out, data_frame = out[:10] , out[10:]
        if out[0] == bytes_to_int(b'\xF1') and out[1] == bytes_to_int(b'\x01'):
            pass
        else:
            general.message("problems are possible to read_arr_all_signal")      
        return  self.convert_arr_data_to_np_array(data_frame)

    def read_pages(self, pages, first, last):
        # Each page comes in its own datagram and carries its own number in
        # bytes 3-4 of the header (manual, Fig. 5), so the pages are stored by
        # that number instead of by the order they arrive in. Byte 9 is the
        # number of the measurement they belong to.
        command = self.get_command_read_arr_all_signal(last, first)
        self.sock.sendto( command , (self.ip_UDP, self.port_UDP) )
        meas = set()
        # the measurement cycle is already over at this point, the pages arrive
        # at once; a short timeout keeps a lost page from blocking for 10 s
        self.sock.settimeout(2)
        try:
            data_raw_answer, addr = self.sock.recvfrom( int(4) )
            for i in range(last - first + 1):
                data_raw_data,addr = self.sock.recvfrom( int(512 * 2 + 10) )
                page               = bytes_to_int(data_raw_data[3:5])
                data_arr           = self.check_out_read_arr_all_signal(data_raw_data)
                meas.add(data_raw_data[9])
                if page >= 0 and page < len(pages):
                    pages[page] = data_arr
                else:
                    general.message("Page number " + str(page) + " is out of range")
        except timeout:
            pass
        finally:
            self.sock.settimeout(10)
        return meas

    def read_arr_all_signal(self):
        #FID = np.array([])
        if self.mode_point == 0:
            LIST = 15 #round(8192/512)
        elif self.mode_point == 1:
            LIST = 31 #round(16384/512)
        elif self.mode_point == 2:
            LIST = 63 #round(32768/512)
        elif self.mode_point == 3:
            LIST = 103 #round(32768/512)

        #command = self.get_command_read_arr_all_signal(LIST)
        #self.sock.sendto( command , (self.ip_UDP, self.port_UDP) )
        #data_raw_answer, addr = self.sock.recvfrom( int(4) )
        #for i in range(LIST + 1):
        #        data_raw_data,addr = self.sock.recvfrom( int(512 * 2 + 10) )
        #        data_arr           = self.check_out_read_arr_all_signal(data_raw_data)
        #        FID = np.append(FID, data_arr)
        #return FID
        pages = [None] * (LIST + 1)
        meas  = self.read_pages(pages, 0, LIST)
        # a lost page can simply be requested again (manual, Sec. 3.2); without
        # this a single dropped datagram used to shift the whole rest of the FID
        # by 512 points, or to raise a socket timeout
        for attempt in range(3):
            missing = [p for p, v in enumerate(pages) if v is None]
            if len(missing) == 0:
                break
            general.message("Lost pages " + str(missing) + ", requesting them again")
            for p in missing:
                meas |= self.read_pages(pages, p, p)

        missing = [p for p, v in enumerate(pages) if v is None]
        if len(missing) > 0:
            general.message("Pages " + str(missing) + " are still missing, filled with zeros")
            for p in missing:
                pages[p] = np.zeros(512)
        if len(meas) > 1:
            general.message("The pages come from different measurements: " + str(sorted(meas)))
        return np.concatenate(pages)

#------------------------0x03--------------------------------------------------

    def get_command_start_experiment(self):
        command = b'\x03\x00\x00\x00'
        return command

    def check_out_start_experiment(self, out_1, out_2):
        if out_1[0] == bytes_to_int(b'\x10') and out_1[1] == bytes_to_int(b'\x03') and out_1[3] == bytes_to_int(b'\x10'):
            pass 
        else:
            general.message("An error occurs when starting an experiment")
        if out_2[0] == bytes_to_int(b'\x11') and out_2[1] == bytes_to_int(b'\x03'):
            pass
        else:
            general.message("An error occurs when starting an experiment" )
        
    def measurement_time(self):
        # Duration of one measurement cycle in seconds: N_A elementary cycles,
        # each of them Np samples at Fref/16, plus the dead time of register 3
        # and the additional delay Del of register 4 (manual, Tables 4 and 5)
        Np  = (8192, 16384, 32768, 53248)[self.mode_point]
        NA  = self.NAV_TO_NA[self.mode_nav]
        Del = 40.0 if (self.mode_nav > 0 and (self.sensor_number == 2 or self.sensor_number == 4)) else 0.0
        return NA * (Np * self.T + 0.08 + Del) / 1000.0

    def start_experiment(self):
        command = self.get_command_start_experiment()
        self.sock.sendto( command , (self.ip_UDP, self.port_UDP) )
        data_raw_answer_1, addr = self.sock.recvfrom( int(4) )
        # The second packet only comes when the measurement cycle is over. With
        # 128 accumulations, 53248 points and the 40 ms delay of the slow
        # sensors 2 and 4 that is 8.5 s, which the fixed timeout of 10 s barely
        # covers
        self.sock.settimeout( 2 * self.measurement_time() + 10 )
        try:
            data_raw_answer_2, addr = self.sock.recvfrom( int(2) )
        finally:
            self.sock.settimeout(10)

        self.check_out_start_experiment(data_raw_answer_1,data_raw_answer_2)
        

#-----------------------0x05---------------------------------------------------

    def get_command_stop_experiment(self):
        command = b'\x05\x00\x00\x00'
        return command

    def stop_experiment(self): 
        command =  self.get_command_stop_experiment()
        self.sock.sendto( command , (self.ip_UDP, self.port_UDP) )
        data_raw_answer, addr = self.sock.recvfrom( int(4) )
        return data_raw_answer 

#-----------------------0x06------------------------------------------------

    def get_command_set_pack_to_synthesizer(self):
        command = b'\x06\x00\x00\x00'
        return command

    def check_out_set_pack_to_synthesizer(self, out):
        if out[0] == bytes_to_int(b'\x10') and out[1] == bytes_to_int(b'\x06')and out[3] == bytes_to_int(b'\x10'):
            pass 
        else:
            general.message("An error occurs when transferring data to the synthetizer")

    def set_pack_to_synthesizer(self):
        command = self.get_command_set_pack_to_synthesizer()
        self.sock.sendto( command , (self.ip_UDP, self.port_UDP) )
        data_raw_answer, addr = self.sock.recvfrom( int(4) )
        self.check_out_set_pack_to_synthesizer(data_raw_answer)
        
#---------------synthesizer------------------------------------------------

    def print_pack_to_synt(self):
        # see the note in set_13_reg(): reg 13 is D3 + number of bits,
        # reg 15 is the address + D0
        D3N  = (self.read_reg_i(13)).to_bytes(2, byteorder = "big")
        D1D2 = (self.read_reg_i(14)).to_bytes(2, byteorder = "big")
        AD0  = (self.read_reg_i(15)).to_bytes(2, byteorder = "big")
        R31  = (self.read_reg_i(31)).to_bytes(2, byteorder = "big")
        R30  = (self.read_reg_i(30)).to_bytes(2, byteorder = "big")
        print("13-15 ", AD0 + D1D2 + D3N," 30, 31 ", R31, R30)

    def init_synthesizer(self):
        print("Initialization of the synthetizer")
        self.write_reg_i(31)
        self.command_synt_bytes = [b'\x01', b'\xb8' , b'\x00' , b'\x00' , b'\x00'  ,  b'\x20' ]
        self.write_reg_i(13)
        self.write_reg_i(14)
        self.write_reg_i(15)
        self.set_pack_to_synthesizer()
        self.write_reg_i(18)
        time.sleep(1)

    def write_pack_to_synthesizer(self, command_synt_bytes):
        self.command_synt_bytes = command_synt_bytes
        self.write_reg_i(13)
        self.write_reg_i(14)
        self.write_reg_i(15)
        self.set_pack_to_synthesizer()
        time.sleep(0.01)

    def conv_code1_to_command_synt_bytes(self, code, addr):
        _temp =  (code).to_bytes(4,byteorder="big")
        D0 = (_temp[0]).to_bytes(1,byteorder="big")
        D1 = (_temp[1]).to_bytes(1,byteorder="big")
        D2 = (_temp[2]).to_bytes(1,byteorder="big")
        D3 = (_temp[3]).to_bytes(1,byteorder="big")
        return [addr,D0,D1,D2,D3,b'\x28']

    def write_freq_to_synthesizer(self, F1):
        #==1==#
        command = [b'\x00', b'\xb0' , b'\x00' , b'\x00' , b'\x00'  ,  b'\x10' ]
        self.write_pack_to_synthesizer(command)

        #==2==#
        code1 = int(F1 * 32.768 / 32.767846 * 2**16 / 7)
        
        #print("F = ",F1," code1 = ",code1, (code1).to_bytes(4,byteorder="big"))

        #==3==#
        addr  = b'\x04'
        command = self.conv_code1_to_command_synt_bytes(code1,addr)
        self.write_pack_to_synthesizer(command)

        #==4==#
        command = [b'\x00', b'\x70' , b'\x00' , b'\x00' , b'\x00'  ,  b'\x10' ]
        self.write_pack_to_synthesizer(command)

        #==5==#
        F2 = F1 + 480    # kHz; must stay equal to self.IF, which is where the
                         # NMR line is then looked for in gaussmeter_field()
        code2 = int(F2 * 32.768 / 32.767846 * 2**16 / 7)
        
        #==6==#
        addr  = b'\x04'
        command = self.conv_code1_to_command_synt_bytes(code2,addr)
        self.write_pack_to_synthesizer(command)

        #==7==#
        command = [b'\x00', b'\xf0' , b'\x00' , b'\x00' , b'\x00'  ,  b'\x10' ]
        self.write_pack_to_synthesizer(command)

        #==8==#
        self.write_reg_i(18)

        #==9==#
        time.sleep(0.01)

        #==10==#
        # Manual, Sec. 5: the frequencies that were actually set have to be read
        # back to be sure the transfer succeeded. Switched off by default, turn
        # it on once read_reg_i() has been confirmed on the hardware
        if self.verify_synt:
            self.check_synthesizer(F1, F2)

    def check_synthesizer(self, F1, F2):
        # the accuracy of the frequency measurement is 4 kHz (manual, Sec. 5)
        M1, M2 = self.read_freq_to_synthesizer()
        if abs(M1 - F1) > 4 or abs(M2 - F2) > 4:
            general.message("The synthetizer frequencies are not the requested ones: " \
                             + str((F1, F2)) + " kHz requested, " + str((M1, M2)) + " kHz measured")

    def read_freq_to_synthesizer(self):
        # register 31 holds the measured F1, register 30 the measured F2, and
        # F = (Fref/8192)*C_F (manual, Sec. 5)
        C1 = self.read_reg_i(31)
        C2 = self.read_reg_i(30)
        #F1 = C1 * 4
        #F2 = C2 * 4
        F1 = C1 * self.Fref / 8192
        F2 = C2 * self.Fref / 8192
        return F1, F2

#-------------------FID---------------------------------------------
# The helpers below are superseded by gaussmeter_field() and gaussmeter_search(),
# which follow Stages 2 - 4 of Sec. 6 of the manual. They were never called and
# do not run as they stand: get_NMR_spectrum() unpacks the (W, I) of
# get_rfft_FID() the wrong way round, get_clarification_field_B() uses an
# undefined G and returns nothing, search_field() and get_B() have no self,
# search_field() reads an undefined self.B_end and never changes B, so its loop
# does not terminate.
#    def find_noize(self, F):
#        FID  = self.get_FID(F)
#        W , I_NOIZE   = self.get_rfft_FID(FID)
#        self.NOIZE = np.max(I_NOIZE)
#
#    def get_FID(self, F):
#        self.NMR_freq_synthesizer(F)
#        self.NMR_start_experiment()
#        FID = self.NMR_FID_array().T
#
#        return FID

    def get_rfft_FID(self, FID):
        #FID = FID - np.sum(FID[len(FID) - 100:])/101
        #N , T = self.N , self.T 
        N, T = len(FID) , self.T 
        I = np.abs(rfft(FID))[:N // 2]
        W = rfftfreq(N, T)[:N // 2]
        return W, I

#    def get_NMR_spectrum(self, B_ref):
#        G = 42.57637513 # MG/Tl = KG/mTl
#        F_ref = G * B_ref
#        FID   = self.get_FID(F_ref)
#        I, W   = self.get_rfft_FID(FID)
#        return I, W
#
#    def get_clarification_field_B(self, B_ref):
#        I,W = get_NMR_spectrum(B_ref)
#        F_cl  = W[np.where(I == np.max(I))[0][0]]
#        F_NMR = G * B_ref + F_cl + 480
#        B_return = F_NMR / G
#
#    def search_field():
#        Bstep = 10 / self.time_90_deg_pulse
#        B = 0
#        S_N   = []
#        B_S_N = []
#        while B < self.B_end:
#            b += Bstep
#            B_S_N.append(b)
#            I, W = self.get_NMR_spectrum(B)
#            S = np.max(I)
#            s_n = S / self.NOIZE
#            S_N.append(s_n)
#        S_N   = np.array(  S_N)
#        B_S_N = np.array(B_S_N)
#        B_res  = B_S_N[np.where(S_N==np.max(S_N))[0][0]]
#        return B_res
#
#    def get_B():
#        S,_ = self.get_NMR_spectrum(self.B)
#        S = np.max(S)
#        s_n = S/self.NOIZE
#        if s_n < 5:
#            B = self.search_field()
#            B = self.get_clarification_field_B(B)
#            self.B = B
#        else:
#            B = self.get_clarification_field_B(self.B)
#        return B


    #def ind_loc_max(self, v):
    #    return np.where(np.append(np.nan,np.diff(np.sign(np.append(np.nan , np.diff(v))))) == -2)[0]-1