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

    @staticmethod
    def _echo_window(z, frac):
        """Echo samples of a complex trace (or stack of traces): the |z|
        envelope, averaged over the traces, at or above `frac` of its peak.
        Returns (peak index, boolean mask over the time axis)."""
        env = np.abs(z).mean(axis=0)
        if env.size == 0 or env.max() <= 0:
            return 0, np.zeros(env.shape, dtype=bool)
        k = int(np.argmax(env))
        return k, env >= frac*env[k]

    @staticmethod
    def auto_phase_zero_echo(signal, frac=0.25):
        """Zero-order phase (degrees) measured on the **time-domain echo**, for
        a correction that is applied in the time domain.

        Works on the samples around the |z| envelope peak instead of on a
        spectrum, in two levels: each trace is first summed coherently over that
        echo window — which is exactly the integration the phased data is headed
        for, so it is the quantity whose real part should be maximal — and the
        per-trace sums are then combined with the sign-blind principal axis of
        `auto_phase_zero`, φ₀ = -½·angle(Σ s²). The two levels matter for
        different reasons: summing first keeps a decayed, phase-scrambled trace
        from dragging the estimate (|s|² weighting all but drops it), while the
        squared combination survives a set whose traces change sign, such as an
        inversion recovery. The ±180° the axis leaves open follows the same
        convention as `auto_phase_zero` (whichever makes the magnitude-weighted
        real part positive); for a balanced bipolar set that choice is arbitrary
        either way. For a single trace the whole thing collapses to
        φ₀ = -angle(Σ z) over the echo.

        Prefer this to `auto_phase_zero` whenever the phase is applied to the
        trace rather than to its transform, for two reasons:

        * **The time origin is unambiguous.** A spectrum computed from a trace
          truncated to start at the echo reports φ₀ in that *shifted* frame. For
          a line at offset f the two frames differ by 360·f·dt per skipped
          sample — 72°/sample for a 100 MHz carrier at dt = 2 ns — so such a
          value is wrong by a large, skip-dependent amount when it is applied
          from the start of the window.
        * **No dead-time ramp to flatten.** Restricting to the echo does the job
          that the leading-point skip does for the frequency-domain estimator,
          without moving the origin.

        `signal` is complex I+iQ, 1D or 2D (rows = traces, columns = the time
        axis; the envelope is averaged over the rows). **Any first/second-order
        phase must already be applied** — an un-demodulated carrier rotates z²
        right around the circle and makes the sum cancel; use `carrier_offset`
        to check. `frac` is the envelope level, relative to the peak, that
        delimits the echo. Returns a value in [0, 360); feed it to
        `ph_correction` as cor1 = φ₀·π/180.
        """
        z = np.asarray(signal, dtype=complex)
        if z.ndim == 1:
            z = z[None, :]
        _, keep = Fast_Fourier._echo_window(z, frac)
        if not keep.any():
            return 0.0
        s = z[:, keep].sum(axis=1)           # coherent echo integral, per trace
        acc2 = np.sum(s*s)                   # Σ s² : phase 2θ, |s|²-weighted
        if acc2 == 0:
            return 0.0
        phi = -0.5*np.angle(acc2)            # principal axis, ±180° ambiguous
        if np.real(np.sum(np.abs(s)*s)*np.exp(1j*phi)) < 0:
            phi += np.pi                     # flip so the real part is positive
        return float(np.degrees(phi) % 360.0)

    @staticmethod
    def carrier_offset(signal, dt, frac=0.25):
        """Dominant line offset of a time-domain echo, in cycles per unit of
        `dt` (so ×1000 gives MHz when dt is in ns).

        Undemodulated records — anything digitised at an intermediate frequency
        rather than at the video output — carry the whole signal at that offset,
        and no zero-order phase can make such a trace real: its real part just
        oscillates. This reports the offset so it can be removed with the
        first-order term (set it to −`carrier_offset`) before phasing.

        Estimated by the phase increment per sample over the echo window,
        angle(Σ z[t+1]·z*[t]) / (2π·dt), which needs no frequency resolution and
        no zero fill. Unambiguous up to the Nyquist offset ±1/(2·dt).
        """
        z = np.asarray(signal, dtype=complex)
        if z.ndim == 1:
            z = z[None, :]
        if z.shape[1] < 2 or dt == 0:
            return 0.0
        _, keep = Fast_Fourier._echo_window(z, frac)
        pair = keep[:-1] & keep[1:]
        if not pair.any():
            return 0.0
        acc = np.sum(z[:, 1:][:, pair]*np.conj(z[:, :-1][:, pair]))
        if acc == 0:
            return 0.0
        return float(np.angle(acc)/(2.0*np.pi*dt))

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