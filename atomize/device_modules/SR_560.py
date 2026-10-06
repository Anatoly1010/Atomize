#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from numbers import Real
import atomize.device_modules.base_device as base


class SR_560(base.BaseDevice):
    """SR560 control with cached getters for its listen-only RS-232 interface.

    Getters return the last requested setting, or None if it is unknown.
    Front-panel changes and commands from other controllers cannot be read back.
    """

    config_file = 'SR_560_config.ini'

    def __init__(self):
        self.gain_dict = {value: index for index, value in enumerate(
            [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000])}
        self.gain_mode_dict = {'Low Noise': 0, 'High Dynamic Reserve': 1, 'Calibration': 2}
        self.source_dict = {'A': 0, 'A-B': 1, 'B': 2}
        self.coupling_dict = {'Ground': 0, 'DC': 1, 'AC': 2}
        self.on_off_dict = {'Off': 0, 'On': 1}
        self.filter_mode_dict = {'Bypass': 0, '6 dB Low Pass': 1, '12 dB Low Pass': 2,
                                '6 dB High Pass': 3, '12 dB High Pass': 4, 'Bandpass': 5}
        self.frequency_list = [0.03, 0.1, 0.3, 1, 3, 10, 30, 100, 300,
                               1000, 3000, 10000, 30000, 100000, 300000, 1000000]
        self.frequency_labels = ['0.03 Hz', '0.1 Hz', '0.3 Hz', '1 Hz', '3 Hz', '10 Hz',
                                 '30 Hz', '100 Hz', '300 Hz', '1 kHz', '3 kHz', '10 kHz',
                                 '30 kHz', '100 kHz', '300 kHz', '1 MHz']
        self._clear_cache()
        super().__init__()

    def _check(self, condition, message):
        if self.test_flag == 'test':
            assert condition, message
        elif not condition:
            raise ValueError(message)

    def _configure_address(self):
        self._check(self.config['interface'] == 'rs232', 'SR560 supports only RS-232')
        address = self.specific_parameters['address']
        self._check(address in ['0', '1', '2', '3'], 'Invalid SR560 address; expected 0, 1, 2, or 3')
        self.unit_address = int(address)

    def _connect(self):
        self._configure_address()
        super()._connect()

    def _init_test_values(self):
        self._configure_address()

    def _clear_cache(self):
        for name in ['gain', 'gain_mode', 'input_source', 'input_coupling', 'invert',
                     'filter_mode', 'high_pass_frequency', 'low_pass_frequency',
                     'vernier', 'vernier_gain', 'blanking']:
            setattr(self, '_' + name, None)

    def _send_command(self, command):
        if self.test_flag != 'test':
            self.device_write('UNLS')
            self.device_write(f'LISN {self.unit_address}')
            self.device_write(command)

    def _setting(self, name, command, choices, values):
        self._check(len(values) <= 1, f'{name} accepts zero or one argument')
        if len(values) == 0:
            return getattr(self, '_' + name)
        value = values[0]
        self._check(isinstance(value, (str, Real)) and not isinstance(value, bool)
                    and value in choices, f'Invalid {name}; expected one of {list(choices)}')
        self._send_command(f'{command} {choices[value]}')
        setattr(self, '_' + name, next(key for key in choices if key == value))

    def _frequency(self, name, command, count, values):
        self._check(len(values) <= 1, f'{name} accepts zero or one argument')
        if len(values) == 0:
            return getattr(self, '_' + name)
        value = values[0]
        units = {'Hz': 1, 'kHz': 1000, 'MHz': 1000000}
        self._check(isinstance(value, str), 'Frequency must be a string with Hz, kHz, or MHz')
        parts = value.split()
        self._check(len(parts) == 2 and parts[1] in units,
                    'Frequency must be a string with Hz, kHz, or MHz')
        try:
            frequency = float(parts[0]) * units[parts[1]]
        except ValueError:
            self._check(False, 'Invalid frequency value')
        self._check(frequency in self.frequency_list[:count],
                    f'Invalid {name}; expected one of {self.frequency_labels[:count]}')
        index = self.frequency_list.index(frequency)
        self._send_command(f'{command} {index}')
        setattr(self, '_' + name, self.frequency_labels[index])

    def preamplifier_name(self):
        return self.config['name']

    def preamplifier_gain(self, *gain):
        return self._setting('gain', 'GAIN', self.gain_dict, gain)

    def preamplifier_gain_mode(self, *mode):
        return self._setting('gain_mode', 'DYNR', self.gain_mode_dict, mode)

    def preamplifier_input_source(self, *source):
        return self._setting('input_source', 'SRCE', self.source_dict, source)

    def preamplifier_input_coupling(self, *coupling):
        return self._setting('input_coupling', 'CPLG', self.coupling_dict, coupling)

    def preamplifier_invert(self, *invert):
        return self._setting('invert', 'INVT', self.on_off_dict, invert)

    def preamplifier_filter_mode(self, *mode):
        return self._setting('filter_mode', 'FLTM', self.filter_mode_dict, mode)

    def preamplifier_high_pass_frequency(self, *frequency):
        return self._frequency('high_pass_frequency', 'HFRQ', 12, frequency)

    def preamplifier_low_pass_frequency(self, *frequency):
        return self._frequency('low_pass_frequency', 'LFRQ', 16, frequency)

    def preamplifier_vernier(self, *vernier):
        return self._setting('vernier', 'UCAL', self.on_off_dict, vernier)

    def preamplifier_vernier_gain(self, *gain):
        return self._setting('vernier_gain', 'UCGN', dict(enumerate(range(101))), gain)

    def preamplifier_blanking(self, *blanking):
        return self._setting('blanking', 'BLINK', self.on_off_dict, blanking)

    def preamplifier_overload_reset(self):
        self._send_command('ROLD')

    def preamplifier_reset(self):
        """Recall instrument defaults and cache the values documented by SRS."""
        self._send_command('*RST')
        self._clear_cache()
        self._gain = 20
        self._gain_mode = 'High Dynamic Reserve'
        self._input_source = 'A'
        self._input_coupling = 'DC'
        self._invert = 'Off'
        self._filter_mode = 'Bypass'
        self._high_pass_frequency = '0.03 Hz'
        self._low_pass_frequency = '1 MHz'
        self._vernier = 'Off'

    def preamplifier_command(self, command):
        """Send a raw command and discard cached settings it may have changed."""
        self._check(isinstance(command, str) and bool(command.strip()), 'Expected a nonempty command string')
        self._send_command(command)
        self._clear_cache()

    def device_query(self, command):
        raise NotImplementedError('SR560 is listen-only; use the cached preamplifier getters')


def main():
    pass


if __name__ == '__main__':
    main()
