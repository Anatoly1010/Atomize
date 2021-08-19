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


    def fft(self, x_axis, data, baseline_point):
        if self.test_flag != 'test':
            baseline = ( np.sum(data[0:baseline_point]) + np.sum(data[len(data)-baseline_point:len(data)] ) ) / (2 * baseline_point ) 
            
            sp = np.fft.fft( data - baseline)
            freq = np.fft.fftfreq(x_axis.shape[-1])
            i = np.argsort(freq)

            sp.real = sp.real[i]
            sp.imag = sp.imag[i]

            return np.sort( freq ), sp.real, sp.imag

        elif self.test_flag == 'test':
            baseline = ( np.sum(data[0:baseline_point]) + np.sum(data[len(data)-baseline_point:len(data)] ) ) / (2 * baseline_point )

            sp = np.fft.fft( data - baseline )
            freq = np.fft.fftfreq(x_axis.shape[-1])
            i = np.argsort(freq)

            sp.real = sp.real[i]
            sp.imag = sp.imag[i]

            return np.sort( freq ), sp.real, sp.imag

            #return x_axis, data, data



if __name__ == "__main__":
    main()