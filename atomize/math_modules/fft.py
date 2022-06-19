#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import numpy as np

class Fast_Fourier():

    def __init__(self):
        # Test run parameters
        # These values are returned by the modules in the test run 
        if len(sys.argv) > 1:
            self.test_flag = sys.argv[1]
        else:
            self.test_flag = 'None'

    def ph_correction(self, freq, data_i, data_q, cor1, cor2, cor3):
        if self.test_flag != 'test':
            data = data_i + 1j*data_q
            data = data*np.exp( 1j*cor1 + 1j*cor2*freq + 1j*cor3*freq*freq )
            if len( data_i.shape ) == 1:
                return np.array( (np.real(data), np.imag(data)) )
            else:
                return np.array( (np.transpose( np.real(data) ), np.transpose( np.imag(data) )) )

        elif self.test_flag == 'test':
            data = data_i + 1j*data_q
            data = data*np.exp( 1j*cor1 + 1j*cor2*freq + 1j*cor3*freq*freq )
            if len( data_i.shape ) == 1:
                return np.array( (np.real(data), np.imag(data)) )
            else:
                return np.array( (np.transpose( np.real(data) ), np.transpose( np.imag(data) )) )
    
    def fft(self, x_axis, data_i, data_q, sample_spacing, re = 'False'):
        if self.test_flag != 'test':
            if re == 'False':
                data = data_i + 1j*data_q
                sp = np.fft.fft( data )

                freq = np.fft.fftfreq(x_axis.shape[-1], sample_spacing*10**(-3))
                i = np.argsort(freq)

                return freq[i], np.abs( sp[i] )

            elif re == 'True':
                data = data_i + 1j*data_q

                if len( data_i.shape ) == 1:
                    sp = np.fft.fft( data )
                    freq = np.fft.fftfreq(x_axis.shape[-1], sample_spacing*10**(-3))
                    i = np.argsort(freq)

                    sp.real = sp.real[i]
                    sp.imag = sp.imag[i]

                    return freq[i], sp.real, sp.imag

                else:
                    sp = np.fft.fft( data, axis = 1 )
                    freq = np.fft.fftfreq(x_axis.shape[-1], sample_spacing*10**(-3))
                    i = np.argsort(freq)

                    sp.real = sp.real[:,i]
                    sp.imag = sp.imag[:,i]

                    return freq[i], sp.real, sp.imag

        elif self.test_flag == 'test':
            if re == 'False':
                data = data_i + 1j*data_q
                sp = np.fft.fft( data )

                freq = np.fft.fftfreq(x_axis.shape[-1], sample_spacing*10**(-3))
                i = np.argsort(freq)

                return freq[i], np.abs( sp[i] )

            elif re == 'True':
                data = data_i + 1j*data_q

                if len( data_i.shape ) == 1:
                    sp = np.fft.fft( data )
                    freq = np.fft.fftfreq(x_axis.shape[-1], sample_spacing*10**(-3))
                    i = np.argsort(freq)

                    sp.real = sp.real[i]
                    sp.imag = sp.imag[i]

                    return freq[i], sp.real, sp.imag

                else:
                    sp = np.fft.fft( data, axis = 1 )
                    freq = np.fft.fftfreq(x_axis.shape[-1], sample_spacing*10**(-3))
                    i = np.argsort(freq)

                    sp.real = sp.real[:,i]
                    sp.imag = sp.imag[:,i]

                    return freq[i], sp.real, sp.imag

if __name__ == "__main__":
    main()