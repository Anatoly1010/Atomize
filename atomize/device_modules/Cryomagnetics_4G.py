#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import gc
import sys
import pyvisa
import numpy as np
from pyvisa.constants import StopBits, Parity
import atomize.device_modules.config.config_utils as cutil
import atomize.general_modules.general_functions as general

class Cryomagnetics_4G:
    #### Basic interaction functions
    def __init__(self):

        #### Inizialization
        # setting path to *.ini file
        self.path_current_directory = os.path.dirname(__file__)
        self.path_config_file = os.path.join(self.path_current_directory, 'config','Cryomagnetics_4G_config.ini')

        # configuration data
        self.config = cutil.read_conf_util(self.path_config_file)
        self.specific_parameters = cutil.read_specific_parameters(self.path_config_file)

        # auxilary dictionaries
        self.persistent_switch_heater_dict = {'On': 'ON', 'Off': 'OFF', }
        self.sweep_dict = {'Up': 'UP', 'Down': 'DOWN', 'Pause': 'PAUSE', 'Zero': 'ZERO', 'Limit': 'LIMIT', }
        self.control_mode_dict = {'Remote': 'REMOTE', 'Local': 'LOCAL', }
        self.sweep_mode_dict = {'Fast': 'FAST', 'Slow': 'SLOW', }
        self.units_dict = {'A': 'A', 'G': 'G', }

        # Ranges and limits

        self.max_current = int(self.specific_parameters['max_current'])
        self.min_current = int(self.specific_parameters['min_current'])

        self.range = str(self.specific_parameters['range']).split(" ")
        self.range = [float(i) for i in self.range]
        self.range_0 = self.range[0]
        self.range_1 = self.range[1]
        self.range_2 = self.range[2]
        self.range_3 = self.range[3]
        self.range_4 = self.max_current

        self.rate = str(self.specific_parameters['rate']).split(" ")
        self.rate = [float(i) for i in self.rate]
        self.rate_0 = self.rate[0]
        self.rate_1 = self.rate[1]
        self.rate_2 = self.rate[2]
        self.rate_3 = self.rate[3]
        self.rate_4 = self.rate[4]

        self.rate_fast = float(self.specific_parameters['rate_fast'])
        
        #### kG ?
        self.conversion = float(self.specific_parameters['field/current'])
        self.max_field = self.max_current * self.conversion / 1000 # kG
        self.min_field = self.min_current * self.conversion / 1000 # kG

        self.units = str(self.specific_parameters['units'])

        self.voltage_limit = float(self.specific_parameters['voltage_limit'])
        self.max_voltage_limit = 10.0
        self.min_voltage_limit = 0.0

        self.max_channels = int(self.specific_parameters['max_channels'])
        self.channel = str(self.specific_parameters['channel'])

        self.low_sweep_limit = 0.0
        self.upper_sweep_limit = 0.5

        self.current = 0.0
        #self.sweep_mode = 0 # 0 slow; 1 fast
        self.shim_mode = 0 # 0 off; 1 on

        # Test run parameters
        # These values are returned by the modules in the test run 
        if len(sys.argv) > 1:
            self.test_flag = sys.argv[1]
        else:
            self.test_flag = 'None'

        if self.test_flag != 'test':
            if self.config['interface'] == 'ethernet':
                try:
                    self.status_flag = 1
                    rm = pyvisa.ResourceManager()
                    self.device = rm.open_resource(self.config['ethernet_address'], read_termination=self.config['read_termination'],
                    write_termination=self.config['write_termination'])
                    self.device.timeout = self.config['timeout'] # in ms
                    try:
                        # test should be here
                        answer = int(self.device_query('*TST?'))
                        if answer == 1:
                            self.status_flag = 1
                            # to write data the device should be in REMOTE
                            self.device_query('*OPC?')
                        else:
                            general.message('During internal device test errors are found')
                            self.status_flag = 0
                            sys.exit()
                    except pyvisa.VisaIOError:
                        general.message("No connection Cryomagnetics 4G")
                        self.status_flag = 0
                        sys.exit()
                    except BrokenPipeError:
                        general.message("No connection Cryomagnetics 4G")
                        self.status_flag = 0
                        sys.exit()
                except pyvisa.VisaIOError:
                    general.message("No connection Cryomagnetics 4G")
                    self.status_flag = 0
                    sys.exit()
                except BrokenPipeError:
                    general.message("No connection Cryomagnetics 4G")
                    self.status_flag = 0
                    sys.exit()
            else:
                general.message("Incorrect interface setting Cryomagnetics 4G")
                self.status_flag = 0
                sys.exit()

        elif self.test_flag == 'test':
            self.test_channel = 'CH1'
            self.test_units = 'G'
            self.persistent_switch_heater_state = 'Off'
            self.test_voltage = '4.75 V'
            self.test_magnet_voltage = '4.75 V'
            self.test_sweep = 'sweep up fast'
            self.test_mode = 'Manual'
            self.test_persistent_current = 10

        # Initial setup of the limits
        #self.magnet_power_supply_control_mode('Remote')
        #self.magnet_power_supply_range( self.range_0, self.range_1, self.range_2, self.range_3 )
        #self.magnet_power_supply_sweep_rate( self.rate_0, self.rate_1, self.rate_2, self.rate_3, self.rate_4, self.rate_fast )
        #self.magnet_power_supply_voltage_limit( self.voltage_limit )
        #self.magnet_power_supply_units( self.units )
        #self.magnet_power_supply_select_channel( self.channel )
        #self.magnet_power_supply_low_sweep_limit( self.low_sweep_limit )
        #self.magnet_power_supply_upper_sweep_limit( self.upper_sweep_limit )
        #self.magnet_power_supply_sweep('Zero', 'Slow')

    def close_connection(self):
        if self.test_flag != 'test':
            self.status_flag = 0
            gc.collect()
        elif self.test_flag == 'test':
            pass

    def device_write(self, command):
        if self.status_flag == 1:
            command = str(command)
            self.device.write(command)
        else:
            general.message("No Connection")
            self.status_flag = 0
            sys.exit()

    def device_query(self, command):
        if self.status_flag == 1:
            answer = self.device.query(command)
            return answer
        else:
            general.message("No Connection")
            self.status_flag = 0
            sys.exit()

    #### device specific functions
    def magnet_power_supply_name(self):
        if self.test_flag != 'test':
            answer = self.device_query('*IDN?')
            return answer
        elif self.test_flag == 'test':
            answer = self.config['name']
            return answer

    def magnet_power_supply_select_channel(self, *ch):
        if self.test_flag != 'test':
            if len( ch ) == 1:
                if self.max_channels == 2:
                    if ch[0] == 'CH1':
                        self.device_write('CHAN ' + '1')
                    elif ch[0] == 'CH2':
                        self.device_write('CHAN ' + '2')
                elif self.max_channels == 1:
                    general.message("Only one channel is available")
                else:
                    general.message("Invalid channel")
                    sys.exit()

            elif len( ch ) == 0:
                if self.max_channels == 2:
                    raw_answer = int( self.device_query('CHAN?') )
                    if raw_answer == 1:
                        return 'CH1'
                    elif raw_answer == 2:
                        return 'CH2'
                elif self.max_channels == 1:
                    return 'CH1'
            else:
                general.message("Invalid Channel Argument")
                sys.exit()

        elif self.test_flag == 'test':
            if len( ch ) == 1:
                if self.max_channels == 2:
                    assert( ch[0] == 'CH1' or ch[0] == 'CH2'), "Invalid channel"
                if self.max_channels == 1:
                    assert( ch[0] == 'CH1' ), "Invalid channel. Only one channel is available"
            elif len( ch ) == 0:
                return self.test_channel
            else:
                assert( 1 == 2 ), "Invalid Argument"

    def magnet_power_supply_low_sweep_limit(self, *lmt):
        # in the range of -Max_Current to +Max_Current
        # lower than High sweep limit
        if self.test_flag != 'test':
            if len( lmt ) == 1:
                self.low_sweep_limit = float( lmt[0] )
                self.device_write( 'LLIM ' + str(self.low_sweep_limit) )

            elif len( lmt ) == 0:
                raw_answer = str( self.device_query('LLIM?') )
                return raw_answer

            else:
                general.message("Invalid low limit is given")
                sys.exit()

        elif self.test_flag == 'test':
            if len( lmt ) == 1:
                self.low_sweep_limit = float( lmt[0] )
                assert( self.low_sweep_limit <= self.max_current and \
                        self.low_sweep_limit >= self.min_current ), "Low sweep limit is out of range of " + str(self.min_current) + " A to " + str(self.max_current) + " A"
                assert( self.low_sweep_limit <= self.upper_sweep_limit ), "Low sweep limit should be lower than Upper sweep limit that is " + str(self.upper_sweep_limit)
            elif len( lmt ) == 0:
                return self.low_sweep_limit
            else:
                assert( 1 == 2 ), "Invalid low limit is given"

    def magnet_power_supply_upper_sweep_limit(self, *lmt):
        # in the range of -Max_Current to +Max_Current
        # greater than Low sweep limit
        if self.test_flag != 'test':
            if len( lmt ) == 1:
                self.upper_sweep_limit = float( lmt[0] )
                self.device_write( 'ULIM ' + str(self.upper_sweep_limit) )

            elif len( lmt ) == 0:
                raw_answer = str( self.device_query('ULIM?') )
                return raw_answer

            else:
                general.message("Invalid upper limit is given")
                sys.exit()

        elif self.test_flag == 'test':
            if len( lmt ) == 1:
                self.upper_sweep_limit = float( lmt[0] )
                assert( self.upper_sweep_limit <= self.max_current and \
                        self.upper_sweep_limit >= self.min_current ), "Upper sweep limit is out of range of " + str(self.min_current) + " A to " + str(self.max_current) + " A"
                assert( self.upper_sweep_limit >= self.low_sweep_limit ), "Upper sweep limit should be greater than Low sweep limit that is " + str(self.low_sweep_limit)
            elif len( lmt ) == 0:
                return self.upper_sweep_limit
            else:
                assert( 1 == 2 ), "Invalid upper limit is given"

    def magnet_power_supply_voltage_limit(self, *lmt):
        # in the range of 0.0 to 10.0 V
        if self.test_flag != 'test':
            if len( lmt ) == 1:
                self.voltage_limit = float( lmt[0] )
                self.device_write( 'VLIM ' + str(self.voltage_limit) )

            elif len( lmt ) == 0:
                raw_answer = str( self.device_query('VLIM?') )
                return raw_answer

            else:
                general.message("Invalid voltage limit is given")
                sys.exit()

        elif self.test_flag == 'test':
            if len( lmt ) == 1:
                self.voltage_limit = float( lmt[0] )
                assert( self.voltage_limit <= self.max_voltage_limit and \
                        self.voltage_limit >= self.min_voltage_limit ), "Voltage limit is out of range of " + str(self.min_voltage_limit) + " V to " + str(self.max_voltage_limit) + " V"
            elif len( lmt ) == 0:
                return self.voltage_limit
            else:
                assert( 1 == 2 ), "Invalid voltage limit is given"

    def magnet_power_supply_sweep_rate(self, *rt):
        # A/s
        if self.test_flag != 'test':
            if len( rt ) == 6:
                self.rate_0 = float( rt[0] )
                self.rate_1 = float( rt[1] )
                self.rate_2 = float( rt[2] )
                self.rate_3 = float( rt[3] )
                self.rate_4 = float( rt[4] )
                self.rate_fast = float( rt[5] )
                self.device_write('RATE 0 ' + str(self.rate_0))
                self.device_write('RATE 1 ' + str(self.rate_1))
                self.device_write('RATE 2 ' + str(self.rate_2))
                self.device_write('RATE 3 ' + str(self.rate_3))
                self.device_write('RATE 4 ' + str(self.rate_4))
                self.device_write('RATE 5 ' + str(self.rate_fast))

            elif len( rt ) == 0:
                answer = np.zeros(6)
                for i in range(6):
                    raw_answer = float( self.device_query( 'RATE? ' + str(i) ) )
                    answer[i] = raw_answer
                return answer
            else:
                general.message("Invalid rate arguments are given")
                sys.exit()

        elif self.test_flag == 'test':
            if len( rt ) == 6:
                self.rate_0 = float( rt[0] )
                self.rate_1 = float( rt[1] )
                self.rate_2 = float( rt[2] )
                self.rate_3 = float( rt[3] )
                self.rate_4 = float( rt[4] )
                self.rate_fast = float( rt[5] )
                assert( self.rate_0 > 0), ("Invalid rate argument is given. Rate_1 should be greater than 0")
                assert( self.rate_1 > 0), ("Invalid rate argument is given. Rate_2 should be greater than 0")
                assert( self.rate_2 > 0), ("Invalid rate argument is given. Rate_3 should be greater than 0")
                assert( self.rate_3 > 0), ("Invalid rate argument is given. Rate_4 should be greater than 0")
                assert( self.rate_4 > 0), ("Invalid rate argument is given. Rate_5 should be greater than 0")
                assert( self.rate_fast > 0), ("Invalid rate argument is given. Rate_fast should be greater than 0")

            elif len( rt ) == 0:
                return np.array([self.rate_0, self.rate_1, self.rate_2, self.rate_3, self.rate_4, self.rate_fast])
            else:
                assert( 1 == 2 ), "Invalid range arguments are given. Six numbers are expected"

    def magnet_power_supply_range(self, *rng):
        if self.test_flag != 'test':
            if len( rng ) == 4:
                self.range_0 = float( rng[0] )
                self.range_1 = float( rng[1] )
                self.range_2 = float( rng[2] )
                self.range_3 = float( rng[3] )
                self.device_write('RANGE 0 ' + str(self.range_0))
                self.device_write('RANGE 1 ' + str(self.range_1))
                self.device_write('RANGE 2 ' + str(self.range_2))
                self.device_write('RANGE 3 ' + str(self.range_3))

            elif len( rng ) == 0:
                answer = np.zeros(5)
                for i in range(5):
                    raw_answer = float( self.device_query( 'RANGE? ' + str(i) ) )
                    answer[i] = raw_answer
                return answer
            else:
                general.message("Invalid range arguments are given")
                sys.exit()

        elif self.test_flag == 'test':
            if len( rng ) == 4:
                self.range_0 = float( rng[0] )
                self.range_1 = float( rng[1] )
                self.range_2 = float( rng[2] )
                self.range_3 = float( rng[3] )
                assert( self.range_0 > 0), ("Invalid range argument is given. Range_0 should be greater than 0")
                assert( self.range_0 < self.range_1), ("Invalid range argument is given. Range_0 should be lower than Range_1")
                assert( self.range_1 < self.range_2), ("Invalid range argument is given. Range_1 should be lower than Range_2")
                assert( self.range_2 < self.range_3), ("Invalid range argument is given. Range_2 should be lower than Range_3")
                assert( self.range_3 < self.max_current), ("Invalid range argument is given. Range_3 should be lower than Max_current")
            elif len( rng ) == 0:
                return np.array([self.range_0, self.range_1, self.range_2, self.range_3, self.range_4])
            else:
                assert( 1 == 2 ), "Invalid range arguments are given. Four numbers are expected"

    def magnet_power_supply_sweep(self, *sw):
        """
        If the FAST parameter is given, the fast mode rate will be used instead of a rate
        selected from the output current range. SLOW is required to change from fast sweep.
        If in Shim Mode, SWEEP LIMIT sweeps to the shim target current.
        """
        if self.test_flag != 'test':
            if len( sw ) == 1:
                sweep = str( sw[0] )
                if sweep in self.sweep_dict:
                    flag = self.sweep_dict[sweep]
                    self.device_write('SWEEP ' + str(flag))
                else:
                    general.message("Invalid sweep type is given")
                    sys.exit()

            elif len( sw ) == 2:
                sweep = str( sw[0] )
                sw_mode = str( sw[1] )
                if sweep in self.sweep_dict and sw_mode in self.sweep_mode_dict:
                    flag_1 = self.sweep_dict[sweep]
                    flag_2 = self.sweep_mode_dict[sw_mode]
                    self.device_write('SWEEP ' + str(flag_1) + str(flag_2) )
                else:
                    general.message("Invalid sweep type or sweep mode is given")
                    sys.exit()

            elif len( sw ) == 0:
                raw_answer = str( self.device_query('SWEEP?') )
                return raw_answer
            else:
                general.message("Invalid Sweep Argument")
                sys.exit()

        elif self.test_flag == 'test':
            if len( sw ) == 1:
                sweep = str(sw[0])
                if self.shim_mode == 0:
                    assert( sweep in self.sweep_dict), "Invalid sweep type is given"
                    assert( sweep != 'Limit' ), "Limit sweep type available only in Shim mode"
                elif self.shim_mode == 1:
                    assert( sweep == 'Limit' ), "Only Limit sweep type available in Shim mode"

            elif len( sw ) == 2:
                sweep = str( sw[0] )
                sw_mode = str( sw[1] )
                if self.shim_mode == 0:
                    assert( sweep in self.sweep_dict ), "Invalid sweep type is given"
                    assert( sw_mode in self.sweep_mode_dict ), "Invalid sweep mode is given"
                    assert( sweep != 'Limit' ), "Limit sweep type available only in Shim mode"
                elif self.shim_mode == 1:
                    assert( sweep == 'Limit' ), "Only Limit sweep type available in Shim mode"
                    assert( sw_mode in self.sweep_mode_dict ), "Invalid sweep mode is given"
            elif len( sw ) == 0:
                return self.test_sweep
            else:
                assert( 1 == 2 ), "Invalid Sweep Argument"

    def magnet_power_supply_units(self, *un):
        if self.test_flag != 'test':
            if len( un ) == 1:
                unit = str( un[0] )
                if unit in self.units_dict:
                    flag = self.units_dict[unit]
                    self.units = unit
                    self.device_write('UNITS ' + str(flag))
                else:
                    general.message("Invalid units is given")
                    sys.exit()

            elif len( un ) == 0:
                raw_answer = str( self.device_query('UNITS?') )
                return raw_answer
            else:
                general.message("Invalid Units Argument")
                sys.exit()

        elif self.test_flag == 'test':
            if len( un ) == 1:
                unit = str(un[0])
                assert( unit in self.units_dict), "Invalid units is given"
                flag = self.units_dict[unit]
                self.units = unit
            elif len( un ) == 0:
                return self.units
            else:
                assert( 1 == 2 ), "Invalid Argument"

    def magnet_power_supply_persistent_current(self, *vl):
        # returns the magnet current (or magnetic field strength) in the
        # present units. If the persistent switch heater is ON the magnet current returned will be the same as
        # the power supply output current. If the persistent switch heater is off, the magnet current will be the
        # value of the power supply output current when the persistent switch heater was last turned off.
        # The value must be supplied in the selected units - amperes or field (kG).
        if self.test_flag != 'test':
            if len( vl ) == 1:
                value = float( vl[0] )
                self.device_write( 'IMAG ' + str( value ) )

            elif len( vl ) == 0:
                raw_answer = str( self.device_query('IMAG?') )
                return raw_answer

            else:
                general.message("Invalid persistent current is given")
                sys.exit()

        elif self.test_flag == 'test':
            if len( vl ) == 1:
                value = float( vl[0] )
                if self.units == 'A':
                    assert( value <= self.max_current and \
                        value >= self.min_current ), "Persistent current is out of range of " + str(self.min_current) + " A to " + str(self.max_current) + " A"
                elif self.units == 'G':
                    assert( value <= self.max_field and \
                        value >= self.min_field ), "Persistent field is out of range of " + str(self.min_field) + " kG to " + str(self.max_field) + " kG"

            elif len( vl ) == 0:
                return self.test_persistent_current
            else:
                assert( 1 == 2 ), "Invalid persistent current is given"

    def magnet_power_supply_mode(self):
        # only query; power supply mode
        if self.test_flag != 'test':
            raw_answer = str( self.device_query('MODE?') )
            return raw_answer
        elif self.test_flag == 'test':
            return self.test_mode  

    def magnet_power_supply_control_mode(self, mode):
        # remote or local; only set
        if self.test_flag != 'test':
            if mode in self.control_mode_dict:
                flag = self.control_mode_dict[mode]
                self.device_write(str(flag))
            else:
                general.message("Invalid control mode is given. Only 'Remote' and 'Local' are available.")
                sys.exit()

        elif self.test_flag == 'test':
            assert( mode in self.control_mode_dict), "Invalid units is given"

    def magnet_power_supply_current(self):
        # only query; power supply current
        if self.test_flag != 'test':
            raw_answer = str( self.device_query('IOUT?') )
            if raw_answer[-1] == 'G':
                self.current = float( raw_answer.split("k")[0] )
            elif raw_answer[-1] == 'A':
                self.current = float( raw_answer.split("A")[0] )

            return raw_answer
        elif self.test_flag == 'test':
            return self.current        

    def magnet_power_supply_voltage(self):
        # only query; power supply voltage
        if self.test_flag != 'test':
            raw_answer = str( self.device_query('VOUT?') )
            #self.voltage = float( raw_answer.split(" ")[0] )
            return raw_answer
        elif self.test_flag == 'test':
            return self.test_voltage

    def magnet_power_supply_magnet_voltage(self):
        # only query; magnet voltage
        if self.test_flag != 'test':
            raw_answer = str( self.device_query('VMAG?') )
            #self.voltage = float( raw_answer.split(" ")[0] )
            return raw_answer
        elif self.test_flag == 'test':
            return self.test_magnet_voltage

    def magnet_power_supply_persistent_heater(self, *st):
        if self.test_flag != 'test':
            if len( st ) == 1:
                state = str( st[0] )
                if state in self.persistent_switch_heater_dict:
                    flag = self.persistent_switch_heater_dict[state]
                    self.device_write('PSHTR ' + str(flag))
                else:
                    general.message("Invalid persistent switch heater is given")
                    sys.exit()

            elif len( st ) == 0:
                raw_answer = int( self.device_query('PSHTR?') )
                if raw_answer == 0:
                    return 'Off'
                elif raw_answer == 1:
                    return 'On'
            else:
                general.message("Invalid Persistent Switch Argument")
                sys.exit()

        elif self.test_flag == 'test':
            if len( st ) == 1:
                state = str(st[0])
                assert( state in self.persistent_switch_heater_dict), "Invalid persistent switch heater is given"
            elif len( st ) == 0:
                return self.persistent_switch_heater_state
            else:
                assert( 1 == 2 ), "Invalid Argument"

    def magnet_power_supply_command(self, command):
        if self.test_flag != 'test':
            self.device_write(command)
        elif self.test_flag == 'test':
            pass

    def magnet_power_supply_query(self, command):
        if self.test_flag != 'test':
            answer = self.device_query(command)
            return answer
        elif self.test_flag == 'test':
            answer = None
            return answer

def main():
    pass

if __name__ == "__main__":
    main()

