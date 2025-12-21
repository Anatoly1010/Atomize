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
            self.T    = 1/2048 # хз 
            self.Fr   = 42.57637
            self.num_exp = 1
            #----------FIND---NOIZE-----------
            self.NOIZE = 1
            
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
            self.NOIZE = 0
            self.NOIZE = self.NMR_find_noize(3000)
            self.B = 100.0

    def gaussmeter_name():
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
                            general.message(f"The specified number of averages cannot be set. The following number was set instead: {8192}")
                    elif int(points[0])>=8193 and int(points[0]) <= 16384:
                        self.num_point = int(points[0])
                        self.NMR_number_point(1)
                        if int(points[0]) != 16384:
                            general.message(f"The specified number of averages cannot be set. The following number was set instead: {16384}")                        
                    elif int(points[0])>=16385 and int(points[0]) <= 32768:
                        self.num_point = int(points[0])
                        self.NMR_number_point(2)
                        if int(points[0]) != 32768:
                            general.message(f"The specified number of averages cannot be set. The following number was set instead: {32768}")                        
                    elif int(points[0])>=32769 and int(points[0]) <= 53248:
                        self.num_point = int(points[0])
                        self.NMR_number_point(3)
                        if int(points[0]) != 53248:
                            general.message(f"The specified number of averages cannot be set. The following number was set instead: {53248}")                        

            elif len(points) == 0:       
                return self.num_point 
        elif self.test_flag == 'test':
            if len(points) == 1:
                if int(points[0])>=0 and int(points[0]) <= 53248:
                    pass
                else:
                    assert (1 == 2), 'Invalid values points, correct = [0..53248]'
            elif len(points) == 0:       
                return self.num_point 
            else:
                general.message("Invalid argument")
                sys.exit()   

    def gaussmeter_number_of_averges(self, *nav):
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
                else:
                    assert (1 == 2), 'Invalid number of averages, correct = [0..2048]'
                    
            elif len(nav) == 0:   
                return self.NMR_nav() * self.num_exp
            else:
                general.message("Invalid argument")
                sys.exit()   
        elif self.test_flag == 'test':
            if len(nav) == 1:
                _nav = int(nav[0])
                if  _nav>=0 and _nav <= 2048:
                    pass 
                else:
                    assert (1 == 2), 'Invalid number of averages, correct = [0..2048]'
            elif len(nav) == 0:   
                return self.mode_nav * self.num_exp
            else:
                general.message("Invalid argument")
                sys.exit()

    def gaussmeter_search(self, B_lower, B_upper, step):
        B1   = int(B_lower)
        B2   = int(B_upper)  
        st   = int(step)
        N    = int((B2-B1)/st)
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
        else:
            general.message("Invalid argument")
            sys.exit()   

    def gaussmeter_field(self):
        if self.test_flag != 'test':
            Fref = int(self.Fr *  self.B/10)
            self.NMR_freq_synthesizer(Fref)
            all_arr = np.zeros(self.num_point)
            for i in range(self.num_exp):
                self.NMR_start_experiment()
                arr = self.NMR_FID_array().T
                all_arr=all_arr + arr[:self.num_point]
            all_arr= all_arr / self.num_exp
            arr = all_arr - np.mean(all_arr)
            arr=np.append(arr,np.zeros(53248 - arr.shape[0]))
            W,I = self.get_rfft_FID(arr)
            S_n = np.max(I[2:])/self.NOIZE
            if S_n > 0:
                F_cl = self.z(W[2:], I[2:],Fref)
                B_cl = (-F_cl+Fref+480)/self.Fr*10
                return arr[2:] , I[2:] , round(B_cl, 4) , S_n
            else:
                return arr[2:] , I[2:] , 0 , S_n
        elif self.test_flag == 'test':
            return np.zeros(500) , np.zeros(500) , self.B , 6

    def gaussmeter_gain(self, *gain):
        if self.test_flag != 'test':
            if len(gain) == 1:
                if int(gain[0])>=0 and int(gain[0]) <= 31:
                    self.gain_value = int(gain[0])
                    self.reg[0] = c_uint(gain[0])
                    self.write_reg_i(0)    
            elif len(gain) == 0:
                return self.read_reg_i(0)

            else:
                general.message("Invalid argument")
                sys.exit()   

        elif self.test_flag == 'test':
            if len(gain) == 1:  
                if gain[0]>=0 and gain[0] <= 31:
                    self.gain_value = gain[0]
                    self.reg[0] = c_uint(gain[0])
                else:
                    assert (1 == 2), 'Invalid value of the preamplifier gain, correct = [0..31]'
            elif len(gain) == 0:
                return self.reg[0]
            else:
                assert (1 == 2), 'Invalid value of the preamplifier gain'

    def gaussmeter_pulse_length(self, *time_pulse):
        if self.test_flag != 'test':
            if len(time_pulse) == 1:
                if time_pulse[0]>=0 and time_pulse[0] <= 40:
                    self.time_90_deg_pulse = time_pulse[0]
                    self.set_2_reg()
                    self.write_reg_i(2)    
            elif len(time_pulse) == 0:
                return self.read_reg_i(2)

            else:
                general.message("Invalid length of the pi/2 pulse")
                sys.exit()   

        elif self.test_flag == 'test':
            if len(time_pulse) == 1:  
                if time_pulse[0]>=0 and time_pulse[0] <= 40:
                    self.time_90_deg_pulse = time_pulse[0]
                    self.set_2_reg()
                else:
                    assert (1 == 2), 'Invalid length of the pi/2 pulse, correct = [0..40]'
            elif len(time_pulse) == 0:
                return  self.reg[2]
            else:
                assert (1 == 2), 'Invalid length of the pi/2 pulse'

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

            else:
                general.message("Invalid argument")
                sys.exit()   

        elif self.test_flag == 'test':
            if len(sensor_number) == 1:  
                if sensor_number[0]>=1 and sensor_number[0] <= 4:
                    self.sensor_number = sensor_number[0]
                else:
                    assert (1 == 2), 'Invalid sensor number, correct = [1..4]'
            elif len(sensor_number) == 0:
                return  self.sensor_number
            else:
                assert (1 == 2), 'Invalid sensor number argument'

### Auxiliary functions
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
                return self.read_freq_to_synthesizer()

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
            all_F = np.linspace(F1, F2, N)
            S_N = []
            for F in all_F:
                F = int(F)
                self.NMR_freq_synthesizer(F)
                self.NMR_start_experiment()
                arr = self.NMR_FID_array().T
                W, I = self.get_rfft_FID(arr)
                S_N.append(max(I[2:]) / self.NOIZE)
                general.message('S/N: ' + str(round(S_N[-1], 2)) + '; Field: ' + str(round(F / self.Fr * 10, 4)) + ' G')

            L = S_N.index(max(S_N))
            Bref = all_F[L] / self.Fr * 10
            return Bref
        elif self.test_flag == 'test':
            return 2000

    def NMR_clarification(self, Bref):
        Fref = int(self.Fr * Bref / 10)
        self.NMR_freq_synthesizer(Fref)
        self.NMR_start_experiment()
        arr = self.NMR_FID_array().T
        W,I = self.get_rfft_FID(arr)
        F_cl = W[ list(I).index(max(I[2:])) ]
        return (FF + Fref - 480) / Fr * 10

    def NMR_find_noize(self, B):
        F = int(self.Fr *  B / 10)

        if self.test_flag != 'test':
            T0 = self.gaussmeter_pulse_length()
            self.gaussmeter_pulse_length(0)
            self.NMR_freq_synthesizer(F)
            self.NMR_start_experiment()
            W,I = self.get_rfft_FID(self.NMR_FID_array().T)
            self.gaussmeter_pulse_length(T0)
            self.NOIZE = max(I[2:])
            return max(I[2:])
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
        data_raw_data, addr = self.sock.recvfrom( int(4) )
        self.check_out_read_reg_i(data_raw_answer,data_raw_data,i)
        return  bytes_to_int(data_raw_data[2:])

#------------------------0x01--------------------------------------------------
    def get_command_read_arr_all_signal(self, i):
        command = b'\x01\x09\x00' + (0).to_bytes(1, byteorder = "big") +b'\x00'+ (i).to_bytes(1, byteorder = "big")
        return command

    def convert_arr_data_to_np_array(self, data):
        u_f_1 = np.array([ data[2*i] << 8 for i in range(len(data) // 2)])
        u_f_2 = np.array([ data[2*i + 1] for i in range(len(data) // 2)])
        u_f = u_f_1 + u_f_2
        if self.mode_nav == 0:
            Na = 0
        elif self.mode_nav == 1:
            Na = 7
        else:
            Na = 15 
        Na = 8 #-------------------------FIX-----------
        U  = u_f / (Na+1) - 2047
        return  U 

    def check_out_read_arr_all_signal(self, out):
        out, data_frame = out[:10] , out[10:]
        if out[0] == bytes_to_int(b'\xF1') and out[1] == bytes_to_int(b'\x01'):
            pass
        else:
            general.message("problems are possible to read_arr_all_signal")      
        return  self.convert_arr_data_to_np_array(data_frame)

    def read_arr_all_signal(self):
        FID = np.array([])
        if self.mode_point == 0:
            LIST = 15 #round(8192/512)
        elif self.mode_point == 1:
            LIST = 31 #round(16384/512)
        elif self.mode_point == 2:
            LIST = 63 #round(32768/512)
        elif self.mode_point == 3:
            LIST = 103 #round(32768/512)

        command = self.get_command_read_arr_all_signal(LIST)
        self.sock.sendto( command , (self.ip_UDP, self.port_UDP) )
        data_raw_answer, addr = self.sock.recvfrom( int(4) )
        for i in range(LIST + 1):
                data_raw_data,addr = self.sock.recvfrom( int(512 * 2 + 10) )
                data_arr           = self.check_out_read_arr_all_signal(data_raw_data)
                FID = np.append(FID, data_arr)
        return FID 

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
        
    def start_experiment(self):
        command = self.get_command_start_experiment()
        self.sock.sendto( command , (self.ip_UDP, self.port_UDP) )
        data_raw_answer_1, addr = self.sock.recvfrom( int(4) )
        data_raw_answer_2, addr = self.sock.recvfrom( int(2) )
        
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
        AD0  = (self.read_reg_i(13)).to_bytes(2, byteorder = "big")
        D1D2 = (self.read_reg_i(14)).to_bytes(2, byteorder = "big")
        D3N  = (self.read_reg_i(15)).to_bytes(2, byteorder = "big")
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
        F2 = F1 + 480
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
        
    def read_freq_to_synthesizer(self):
        C1 = self.read_reg_i(31)
        C2 = self.read_reg_i(30)
        F1 = C1 * 4
        F2 = C2 * 4
        return F1, F2

#-------------------FID---------------------------------------------
    def find_noize(self, F):
        FID  = self.get_FID(F)
        W , I_NOIZE   = self.get_rfft_FID(FID)
        self.NOIZE = np.max(I_NOIZE)
       
    def get_FID(self, F):
        self.NMR_freq_synthesizer(F)
        self.NMR_start_experiment()
        FID = self.NMR_FID_array().T
        
        return FID 

    def get_rfft_FID(self, FID):
        #FID = FID - np.sum(FID[len(FID) - 100:])/101
        #N , T = self.N , self.T 
        N, T = len(FID) , self.T 
        I = np.abs(rfft(FID))[:N // 2]
        W = rfftfreq(N, T)[:N // 2]
        return W, I

    def get_NMR_spectrum(self, B_ref):
        G = 42.57637513 # MG/Tl = KG/mTl
        F_ref = G * B_ref
        FID   = self.get_FID(F_ref)
        I, W   = self.get_rfft_FID(FID)
        return I, W

    def get_clarification_field_B(self, B_ref):
        I,W = get_NMR_spectrum(B_ref)
        F_cl  = W[np.where(I == np.max(I))[0][0]] 
        F_NMR = G * B_ref + F_cl + 480
        B_return = F_NMR / G

    def search_field():
        Bstep = 10 / self.time_90_deg_pulse
        B = 0
        S_N   = []
        B_S_N = []
        while B < self.B_end:
            b += Bstep
            B_S_N.append(b)
            I, W = self.get_NMR_spectrum(B)
            S = np.max(I)
            s_n = S / self.NOIZE
            S_N.append(s_n)
        S_N   = np.array(  S_N)
        B_S_N = np.array(B_S_N)
        B_res  = B_S_N[np.where(S_N==np.max(S_N))[0][0]] 
        return B_res

    def get_B():
        S,_ = self.get_NMR_spectrum(self.B)
        S = np.max(S)
        s_n = S/self.NOIZE
        if s_n < 5:
            B = self.search_field()
            B = self.get_clarification_field_B(B)
            self.B = B
        else:
            B = self.get_clarification_field_B(self.B)
        return B


    #def ind_loc_max(self, v):
    #    return np.where(np.append(np.nan,np.diff(np.sign(np.append(np.nan , np.diff(v))))) == -2)[0]-1