#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import math
from numbers import Real
import numpy as np
import atomize.device_modules.base_device as base
import atomize.general_modules.general_functions as general


class Agilent_34410A(base.BaseDevice):
    """Agilent 34410A multimeter with GPIB/LAN control and hardware-free test mode."""

    config_file = 'Agilent_34410A_config.ini'

    def __init__(self):
        self.mode_dict = {'DC Voltage': 'VOLT:DC', 'AC Voltage': 'VOLT:AC',
                          'DC Current': 'CURR:DC', 'AC Current': 'CURR:AC',
                          'Resistance 2W': 'RES', 'Resistance 4W': 'FRES',
                          'Capacitance': 'CAP', 'Frequency': 'FREQ', 'Period': 'PER',
                          'Temperature': 'TEMP', 'Continuity': 'CONT', 'Diode': 'DIOD'}
        self.range_dict = {
            'DC Voltage': [0.1, 1, 10, 100, 1000],
            'AC Voltage': [0.1, 1, 10, 100, 750],
            'DC Current': [0.0001, 0.001, 0.01, 0.1, 1, 3],
            'AC Current': [0.0001, 0.001, 0.01, 0.1, 1, 3],
            'Resistance 2W': [100, 1000, 10000, 100000, 1e6, 1e7, 1e8, 1e9],
            'Resistance 4W': [100, 1000, 10000, 100000, 1e6, 1e7, 1e8, 1e9],
            'Capacitance': [1e-9, 1e-8, 1e-7, 1e-6, 1e-5],
            'Frequency': [0.1, 1, 10, 100, 750],
            'Period': [0.1, 1, 10, 100, 750]}
        self.range_units = {
            'V': {'mV': 1e-3, 'V': 1},
            'A': {'uA': 1e-6, 'mA': 1e-3, 'A': 1},
            'Ohm': {'Ohm': 1, 'kOhm': 1e3, 'MOhm': 1e6, 'GOhm': 1e9},
            'F': {'nF': 1e-9, 'uF': 1e-6, 'F': 1}}
        self.dc_modes = ['DC Voltage', 'DC Current', 'Resistance 2W', 'Resistance 4W', 'Temperature']
        self.ac_modes = ['AC Voltage', 'AC Current', 'Frequency', 'Period']
        self.time_units = {'s': 1, 'ms': 1e-3, 'us': 1e-6}
        self.trigger_dict = {'Immediate': 'IMM', 'External': 'EXT', 'Bus': 'BUS'}
        super().__init__()

    def _check(self, condition, message):
        if self.test_flag == 'test':
            assert condition, message
        elif not condition:
            raise ValueError(message)

    def _check_interface(self):
        self._check(self.config['interface'] in ['gpib', 'ethernet'],
                    'Agilent_34410A supports GPIB or Ethernet')

    def _connect(self):
        self._check_interface()
        super()._connect()

    def _self_test(self):
        if self.config['interface'] == 'ethernet':
            self.device.read_termination = self.config['read_termination']
            self.device.write_termination = self.config['write_termination']
        identity = self._query('*IDN?').split(',')
        if len(identity) < 2 or identity[1].strip() != '34410A':
            self.status_flag = 0
            raise ValueError('Expected an Agilent/Keysight 34410A')

    def _init_test_values(self):
        self._check_interface()
        self.test_mode = 'DC Voltage'
        self.test_settings = {}
        for mode in self.mode_dict:
            self.test_settings.update({(mode, 'nplc'): 1., (mode, 'integration_time'): 1.,
                                       (mode, 'auto_zero'): 'On', (mode, 'autorange'): 'On',
                                       (mode, 'ac_filter'): 20., (mode, 'gate_time'): 0.1})
        for mode, ranges in self.range_dict.items():
            self.test_settings[(mode, 'range')] = float(ranges[0])
        self.test_settings[('DC Voltage', 'range')] = 10.
        self.test_settings[(None, 'sample_count')] = 1
        self.test_settings[(None, 'trigger_delay')] = 'Auto'
        self.test_trigger_source = 'Immediate'
        self.test_armed = False
        self.test_readings = None

    def _query(self, command):
        answer = self.device_query(command)
        if isinstance(answer, bytes):
            answer = answer.decode('ascii')
        return answer.strip()

    def _function(self, allowed):
        mode = self.multimeter_mode()
        self._check(mode in allowed, f'Setting is unavailable in {mode} mode; expected one of {list(allowed)}')
        return mode, self.mode_dict[mode]

    def _number(self, value, units=None):
        if isinstance(value, str) and units is not None:
            parts = value.split()
            self._check(len(parts) == 2 and parts[1] in units, f'Expected a value with units from {list(units)}')
            try:
                value = float(parts[0]) * units[parts[1]]
            except ValueError:
                self._check(False, 'Invalid numeric value')
        self._check(isinstance(value, Real) and not isinstance(value, bool)
                    and math.isfinite(value), 'Expected a finite numeric value')
        return float(value)

    def _numeric_setting(self, name, command, values, mode=None, units=None,
                         choices=None, limits=None, integer=False):
        self._check(len(values) <= 1, f'{name} accepts zero or one argument')
        key = (mode, name)
        if not values:
            answer = self.test_settings[key] if self.test_flag == 'test' else float(self._query(command + '?'))
            return int(answer) if integer else float(answer)
        value = self._number(values[0], units)
        if choices is not None:
            match = next((item for item in choices if math.isclose(value, item, rel_tol=1e-12, abs_tol=0)), None)
            self._check(match is not None, f'Invalid {name}; expected one of {choices}')
            value = match
        if limits is not None:
            for limit in limits:
                if math.isclose(value, limit, rel_tol=1e-12, abs_tol=0):
                    value = limit
            self._check(limits[0] <= value <= limits[1], f'Invalid {name}; expected {limits[0]} to {limits[1]}')
        if integer:
            self._check(value == int(value), f'{name} must be an integer')
            value = int(value)
        if self.test_flag != 'test':
            self.device_write(f'{command} {value:g}')
        else:
            self.test_settings[key] = value

    def _switch_setting(self, name, command, values, mode):
        self._check(len(values) <= 1, f'{name} accepts zero or one argument')
        key = (mode, name)
        if not values:
            if self.test_flag == 'test':
                return self.test_settings[key]
            return 'On' if int(self._query(command + '?')) else 'Off'
        value = values[0]
        self._check(value in ['On', 'Off', 'Once'], f'Invalid {name}; expected On, Off, or Once')
        if self.test_flag != 'test':
            self.device_write(f'{command} {value.upper()}')
        else:
            self.test_settings[key] = 'Off' if value == 'Once' else value

    def _range_function(self):
        mode, function = self._function(self.range_dict)
        if mode in ['Frequency', 'Period']:
            function += ':VOLT'
        return mode, function

    def multimeter_name(self):
        if self.test_flag == 'test':
            return self.config['name']
        return self._query('*IDN?')

    def multimeter_mode(self, *mode):
        self._check(len(mode) <= 1, 'mode accepts zero or one argument')
        if mode:
            value = mode[0]
            self._check(isinstance(value, str) and value in self.mode_dict,
                        f'Invalid mode; expected one of {list(self.mode_dict)}')
            if self.test_flag != 'test':
                self.device_write(f'SENS:FUNC "{self.mode_dict[value]}"')
            else:
                self.test_mode = value
        elif self.test_flag == 'test':
            return self.test_mode
        else:
            answer = self._query('SENS:FUNC?').strip('"').upper()
            aliases = {'VOLTAGE': 'VOLT', 'CURRENT': 'CURR', 'RESISTANCE': 'RES',
                       'FRESISTANCE': 'FRES', 'CAPACITANCE': 'CAP', 'FREQUENCY': 'FREQ',
                       'PERIOD': 'PER', 'TEMPERATURE': 'TEMP', 'CONTINUITY': 'CONT', 'DIODE': 'DIOD'}
            answer = ':'.join(aliases.get(part, part) for part in answer.split(':'))
            if answer in ['VOLT', 'CURR']:
                answer += ':DC'
            for name, function in self.mode_dict.items():
                if function == answer:
                    return name
            raise ValueError(f'Unexpected measurement function: {answer}')

    def multimeter_range(self, *range_value):
        mode, function = self._range_function()
        unit = 'A' if 'Current' in mode else 'Ohm' if 'Resistance' in mode else 'F' if mode == 'Capacitance' else 'V'
        answer = self._numeric_setting('range', f'SENS:{function}:RANG', range_value, mode,
                                       units=self.range_units[unit], choices=self.range_dict[mode])
        if range_value and self.test_flag == 'test':
            self.test_settings[(mode, 'autorange')] = 'Off'
        return answer

    def multimeter_autorange(self, *autorange):
        mode, function = self._range_function()
        return self._switch_setting('autorange', f'SENS:{function}:RANG:AUTO', autorange, mode)

    def multimeter_nplc(self, *nplc):
        mode, function = self._function(self.dc_modes)
        return self._numeric_setting('nplc', f'SENS:{function}:NPLC', nplc, mode,
                                     choices=[0.006, 0.02, 0.06, 0.2, 1, 2, 10, 100])

    def multimeter_integration_time(self, *integration_time):
        mode, function = self._function(self.dc_modes)
        return self._numeric_setting('integration_time', f'SENS:{function}:APER', integration_time,
                                     mode, units=self.time_units, limits=(0.0001, 1))

    def multimeter_ac_filter(self, *ac_filter):
        mode, function = self._function(self.ac_modes)
        suffix = 'RANG:LOW' if mode in ['Frequency', 'Period'] else 'BAND'
        return self._numeric_setting('ac_filter', f'SENS:{function}:{suffix}', ac_filter, mode,
                                     units={'Hz': 1, 'kHz': 1000}, choices=[3, 20, 200])

    def multimeter_gate_time(self, *gate_time):
        mode, function = self._function(['Frequency', 'Period'])
        return self._numeric_setting('gate_time', f'SENS:{function}:APER', gate_time, mode,
                                     units=self.time_units, choices=[0.001, 0.01, 0.1, 1])

    def multimeter_auto_zero(self, *auto_zero):
        mode, function = self._function(['DC Voltage', 'DC Current', 'Resistance 2W', 'Resistance 4W'])
        if mode == 'Resistance 4W':
            self._check(len(auto_zero) == 0, 'Auto zero is always On for Resistance 4W')
            return 'On'
        return self._switch_setting('auto_zero', f'SENS:{function}:ZERO:AUTO', auto_zero, mode)

    def multimeter_sample_count(self, *count):
        return self._numeric_setting('sample_count', 'SAMP:COUN', count, limits=(1, 50000), integer=True)

    def multimeter_trigger_source(self, *source):
        self._check(len(source) <= 1, 'trigger_source accepts zero or one argument')
        if source:
            value = source[0]
            self._check(isinstance(value, str) and value in self.trigger_dict,
                        f'Invalid trigger source; expected one of {list(self.trigger_dict)}')
            if self.test_flag != 'test':
                self.device_write(f'TRIG:SOUR {self.trigger_dict[value]}')
            else:
                self.test_trigger_source = value
        elif self.test_flag == 'test':
            return self.test_trigger_source
        else:
            answer = self._query('TRIG:SOUR?').upper()
            for name, code in self.trigger_dict.items():
                if answer.startswith(code):
                    return name
            raise ValueError(f'Unexpected trigger source: {answer}')

    def multimeter_trigger_delay(self, *delay):
        self._check(len(delay) <= 1, 'trigger_delay accepts zero or one argument')
        if not delay:
            if self.test_flag == 'test':
                return self.test_settings[(None, 'trigger_delay')]
            if int(self._query('TRIG:DEL:AUTO?')):
                return 'Auto'
            return float(self._query('TRIG:DEL?'))
        if delay[0] == 'Auto':
            if self.test_flag != 'test':
                self.device_write('TRIG:DEL:AUTO ON')
            else:
                self.test_settings[(None, 'trigger_delay')] = 'Auto'
        else:
            return self._numeric_setting('trigger_delay', 'TRIG:DEL', delay,
                                         units=self.time_units, limits=(0, 3600))

    @staticmethod
    def _result(readings):
        return float(readings[0]) if len(readings) == 1 else readings.copy()

    def _read_data(self, command):
        self.device_write('FORM:DATA ASC')
        if self.config['interface'] == 'gpib':
            self.device_write(command)
            general.wait(self.gpib_query_wait)
            answer = self.device.read(2 ** 21)
            if isinstance(answer, bytes):
                answer = answer.decode('ascii')
        else:
            answer = self._query(command)
        readings = np.array([float(value) for value in answer.strip().split(',')])
        return self._result(readings)

    def multimeter_get_data(self):
        """Start and read a measurement using the current settings."""
        self._check(self.multimeter_trigger_source() != 'Bus',
                    'Bus triggering requires multimeter_start(), multimeter_trigger(), multimeter_fetch()')
        if self.test_flag != 'test':
            return self._read_data('READ?')
        self.multimeter_start()
        return self.multimeter_fetch()

    def multimeter_start(self):
        if self.test_flag != 'test':
            self.device_write('INIT')
        else:
            self.test_readings = None
            self.test_armed = True
            if self.test_trigger_source != 'Bus':
                self.test_readings = np.zeros(self.multimeter_sample_count())
                self.test_armed = False

    def multimeter_trigger(self):
        self._check(self.multimeter_trigger_source() == 'Bus', 'Software triggering requires the Bus trigger source')
        if self.test_flag != 'test':
            self.device_write('*TRG')
        else:
            self._check(self.test_armed, 'Call multimeter_start() before multimeter_trigger()')
            self.test_readings = np.zeros(self.multimeter_sample_count())
            self.test_armed = False

    def multimeter_fetch(self):
        """Read completed acquisition data without starting another acquisition."""
        if self.test_flag != 'test':
            return self._read_data('FETC?')
        self._check(self.test_readings is not None, 'No readings; start and trigger a measurement before fetching')
        return self._result(self.test_readings)

    def multimeter_stop(self):
        if self.test_flag != 'test':
            self.device_write('ABOR')
        else:
            self.test_armed = False

    def multimeter_reset(self):
        if self.test_flag != 'test':
            self.device_write('*RST')
        else:
            self._init_test_values()

    def multimeter_command(self, command):
        self._check(isinstance(command, str) and bool(command.strip()), 'Expected a nonempty command string')
        if self.test_flag != 'test':
            self.device_write(command)

    def multimeter_query(self, command):
        self._check(isinstance(command, str) and bool(command.strip()), 'Expected a nonempty query string')
        if self.test_flag != 'test':
            return self._query(command)
        return None


def main():
    pass


if __name__ == '__main__':
    main()
