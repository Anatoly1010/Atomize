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

    @staticmethod
    def auto_phase_zero(spectrum, threshold=0.1):
        """Zero-order phase (degrees) that rotates a complex spectrum onto the
        real axis.

        Uses the principal-axis ("square-the-signal") estimator φ₀ =
        -½·angle( Σ S_k² ). Each bin S_k = |S_k|·e^{iθ_k}, so S_k² has phase
        2θ_k weighted by |S_k|²; halving its angle recovers the common axis the
        significant bins lie on. This is sign-blind, so it handles **bipolar**
        data — an inversion-recovery T1 (echo negative at short delay, positive
        after recovery) or any trace that crosses zero — where the older
        magnitude-weighted vector sum Σ|S_k|·S_k fails: opposite-sign bins
        cancel in that sum and bias φ₀. For unipolar data (an FFT peak, a plain
        FID) the two agree. The ±180° ambiguity of the axis is resolved by
        flipping to the orientation that makes the magnitude-weighted real part
        positive. A magnitude threshold (default 10 % of the peak) keeps noise
        and baseline bins out. Returns a value in [0, 360); feed it to
        ph_correction as cor1 = φ₀·π/180.
        """
        s = np.asarray(spectrum, dtype=complex).ravel()
        mag = np.abs(s)
        peak = mag.max() if mag.size else 0.0
        if peak <= 0:
            return 0.0
        keep = mag >= threshold*peak
        sk = s[keep]
        acc2 = np.sum(sk*sk)                 # Σ S_k² : phase 2θ, |S_k|²-weighted
        if acc2 == 0:
            # degenerate (e.g. a single real point); fall back to the vector sum
            acc = np.sum(mag[keep]*sk)
            if acc == 0:
                return 0.0
            return float(np.degrees(-np.angle(acc)) % 360.0)
        phi = -0.5*np.angle(acc2)            # principal axis, ±180° ambiguous
        if np.sum(mag[keep]*np.real(sk*np.exp(1j*phi))) < 0:
            phi += np.pi                     # flip so the real part is positive
        return float(np.degrees(phi) % 360.0)

    def ph_correction(self, freq, data_i, data_q, cor1, cor2, cor3):
        if self.test_flag != 'test':
            if np.isnan(data_i).any() or np.isnan(data_q).any():
                if len(data_i.shape) > 1:
                    out_shape = (2, *data_i.shape[::-1])
                else:
                    out_shape = (2, *data_i.shape)

            data = data_i + 1j*data_q
            data = data*np.exp( 1j*cor1 + 1j*cor2*freq + 1j*cor3*freq*freq )
            if len( data_i.shape ) == 1:
                return np.array( (np.real(data), np.imag(data)) )
            else:
                return np.array( (np.transpose( np.real(data) ), np.transpose( np.imag(data) )) )

        elif self.test_flag == 'test':
            if np.isnan(data_i).any() or np.isnan(data_q).any():
                if len(data_i.shape) > 1:
                    out_shape = (2, *data_i.shape[::-1])
                else:
                    out_shape = (2, *data_i.shape)

            data = data_i + 1j*data_q
            data = data*np.exp( 1j*cor1 + 1j*cor2*freq + 1j*cor3*freq*freq )
            if len( data_i.shape ) == 1:
                return np.array( (np.real(data), np.imag(data)) )
            else:
                return np.array( (np.transpose( np.real(data) ), np.transpose( np.imag(data) )) )
    
    def fft(self, x_axis, data_i, data_q, sample_spacing, re = 'False'):
        if self.test_flag != 'test':
            if re == 'False':

                if np.isnan(data_i).any() or np.isnan(data_q).any():
                    nan_array = np.full_like(data_i, np.nan, dtype=float)
                    return nan_array, nan_array

                data = data_i + 1j*data_q
                sp = np.fft.fft( data )

                freq = np.fft.fftfreq(x_axis.shape[-1], sample_spacing*10**(-3))
                i = np.argsort(freq)

                return freq[i], np.abs( sp[i] )

            elif re == 'True':

                if np.isnan(data_i).any() or np.isnan(data_q).any():
                    nan_array = np.full_like(data_i, np.nan, dtype=float)
                    return nan_array, nan_array, nan_array

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
                
                if np.isnan(data_i).any() or np.isnan(data_q).any():
                    nan_array = np.full_like(data_i, np.nan, dtype=float)
                    return nan_array, nan_array

                data = data_i + 1j*data_q
                sp = np.fft.fft( data )

                freq = np.fft.fftfreq(x_axis.shape[-1], sample_spacing*10**(-3))
                i = np.argsort(freq)

                return freq[i], np.abs( sp[i] )

            elif re == 'True':
                
                if np.isnan(data_i).any() or np.isnan(data_q).any():
                    nan_array = np.full_like(data_i, np.nan, dtype=float)
                    return nan_array, nan_array, nan_array

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