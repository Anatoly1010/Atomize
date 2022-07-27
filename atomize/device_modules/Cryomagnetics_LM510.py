#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import gc
import sys
import pyvisa
from pyvisa.constants import StopBits, Parity
import atomize.device_modules.config.config_utils as cutil
import atomize.general_modules.general_functions as general

class Cryomagnetics_LM510:
    #### Basic interaction functions
    def __init__(self):

        #### Inizialization
        # setting path to *.ini file
        self.path_current_directory = os.path.dirname(__file__)
        self.path_config_file = os.path.join(self.path_current_directory, 'config','Cryomagnetics_LM510_config.ini')

        # configuration data
        self.config = cutil.read_conf_util(self.path_config_file)
        self.specific_parameters = cutil.read_specific_parameters(self.path_config_file)

        # auxilary dictionaries
        self.boost_dict = {'Off': 'OFF', 'On': 'ON', 'Smart': 'SMART', }
        self.sample_mode_dict = {'Sample/Hold': 'S', 'Continuous': 'C', 'Off': 'O', }
        self.units_dict = {'cm': 'CM', 'in': 'IN', '%': 'PERCENT', }
        self.heater_dict = {'Off': 'OFF', 'On': 'ON', }

        # Ranges and limits
        self.hrc_option = str(self.specific_parameters['hrc_second_channel'])
        self.hrc_second_channel = 0
        self.h_level_min = 0.0
        self.h_level_max = 500.0
        self.l_level_min = 0.0
        self.l_level_max = 500.0
        self.hours_min = 0
        self.hours_max = 99
        self.minutes_min = 0
        self.minutes_max = 59
        self.seconds_min = 0
        self.seconds_max = 59
        self.targ_pressure_min = 0.15
        self.targ_pressure_max = 14.25
        self.heater_limit_min = 0.1
        self.heater_limit_max = 10.0

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
                            self.device_query('REMOTE;*OPC?')
                        else:
                            general.message('During internal device test errors are found')
                            self.status_flag = 0
                            sys.exit()
                    except pyvisa.VisaIOError:
                        general.message("No connection")
                        self.status_flag = 0
                        sys.exit()
                    except BrokenPipeError:
                        general.message("No connection")
                        self.status_flag = 0
                        sys.exit()
                except pyvisa.VisaIOError:
                    general.message("No connection")
                    self.status_flag = 0
                    sys.exit()
                except BrokenPipeError:
                    general.message("No connection")
                    self.status_flag = 0
                    sys.exit()
            else:
                general.message("Incorrect interface setting")
                self.status_flag = 0
                sys.exit()

        elif self.test_flag == 'test':
            self.test_channel = 1
            self.test_boost_mode = 'On'
            self.test_h_alarm = '65 cm'
            self.test_l_alarm = '1 cm'
            self.test_sensor_length = '120 cm'
            self.test_sample_mode = 'Sample/Hold'
            self.test_units = 'cm'
            self.test_interval = '00:10:00'
            self.test_pressure = '0.5 PSI'
            self.test_heater_limit = '6.0 Watts'
            self.test_heater_state = 'On'

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
    def level_monitor_name(self):
        if self.test_flag != 'test':
            answer = self.device_query('*IDN?')
            return answer
        elif self.test_flag == 'test':
            answer = self.config['name']
            return answer

    def level_monitor_select_channel(self, *ch):
        if self.test_flag != 'test':
            if len( ch ) == 1:
                if ch[0] == '1':
                    self.device_write('CHAN ' + '1')
                elif ch[0] == '2':
                    self.device_write('CHAN ' + '2')
                else:
                    general.message("Invalid channel")
                    sys.exit()

            elif len( ch ) == 0:
                answer = str( self.device_query('CHAN?') )
                return answer
            else:
                general.message("Invalid Argument")
                sys.exit()

        elif self.test_flag == 'test':
            if len( ch ) == 1:
                assert( ch[0] == '1' or ch[0] == '2'), "Invalid channel"
                if ch[0] == '2' and self.hrc_option == 'True':
                    self.hrc_second_channel = 1
                if ch[0] == '1':
                    self.hrc_second_channel = 0
            elif len( ch ) == 0:
                return self.test_channel
            else:
                assert( 1 == 2 ), "Invalid Argument"

    def level_monitor_boost_mode(self, *md):
        if self.test_flag != 'test':
            if len( md ) == 1:
                mode = str( md[0] )
                if mode in self.boost_dict:
                    flag = self.boost_dict[mode]
                    self.device_write('BOOST ' + str(flag))
                else:
                    general.message("Invalid boost mode is given")
                    sys.exit()

            elif len( md ) == 0:
                raw_answer = str( self.device_query('BOOST?') )
                return raw_answer
            else:
                general.message("Invalid Argument")
                sys.exit()

        elif self.test_flag == 'test':
            if len( md ) == 1:
                mode = str(md[0])
                assert( mode in self.boost_dict), "Invalid boost mode is given"
                assert( self.hrc_second_channel != 1 ), "Second channel is used as HRC"
            elif len( md ) == 0:
                assert( self.hrc_second_channel != 1 ), "Second channel is used as HRC"
                return self.test_boost_mode
            else:
                assert( 1 == 2 ), "Invalid Argument"

    def level_monitor_high_level_alarm(self, *lvl):
        if self.test_flag != 'test':
            if len( lvl ) == 1:
                level = round( float( lvl[0] ), 1)
                if level <= float( self.level_monitor_sensor_length().split(' ')[0] ):
                    if level > float( self.level_monitor_low_level_alarm().split(' ')[0] ):
                        self.device_write('H-ALM ' + str(level))
                    else:
                        general.message("Specified high level alarm is lower than low level alarm")
                        sys.exit()
                else:
                    general.message("Specified high level alarm is higher than sensor length")
                    sys.exit()

            elif len( lvl ) == 0:
                answer = str( self.device_query('H-ALM?') )
                return answer
            else:
                general.message("Invalid Argument")
                sys.exit()

        elif self.test_flag == 'test':
            if len( lvl ) == 1:
                level = round( float( lvl[0] ), 1)
                assert( level >= self.h_level_min and level <= self.h_level_max), "Invalid high alarm limit"
                assert( self.hrc_second_channel != 1 ), "Second channel is used as HRC"
            elif len( lvl ) == 0:
                assert( self.hrc_second_channel != 1 ), "Second channel is used as HRC"
                return self.test_h_alarm
            else:
                assert( 1 == 2 ), "Invalid Argument"

    def level_monitor_low_level_alarm(self, *lvl):
        if self.test_flag != 'test':
            if len( lvl ) == 1:
                level = round( float( lvl[0] ), 1)
                if level < float( self.level_monitor_sensor_length().split(' ')[0] ):
                    if level < float( self.level_monitor_high_level_alarm().split(' ')[0] ):
                        self.device_write('L-ALM ' + str(level))
                    else:
                        general.message("Specified low level alarm is higher than high level alarm")
                        sys.exit()
                else:
                    general.message("Specified low level alarm is higher than sensor length")
                    sys.exit()

            elif len( lvl ) == 0:
                answer = str( self.device_query('L-ALM?') )
                return answer
            else:
                general.message("Invalid Argument")
                sys.exit()

        elif self.test_flag == 'test':
            if len( lvl ) == 1:
                level = round( float( lvl[0] ), 1)
                assert( level >= self.l_level_min and level <= self.l_level_max), "Invalid low alarm limit"
                assert( self.hrc_second_channel != 1 ), "Second channel is used as HRC"
            elif len( lvl ) == 0:
                assert( self.hrc_second_channel != 1 ), "Second channel is used as HRC"
                return self.test_l_alarm
            else:
                assert( 1 == 2 ), "Invalid Argument"

    def level_monitor_sensor_length(self):
        if self.test_flag != 'test':
                answer = str( self.device_query('LNGTH?') )
                return answer

        elif self.test_flag == 'test':
            assert( self.hrc_second_channel != 1 ), "Second channel is used as HRC"
            return self.test_sensor_length
  
    def level_monitor_sample_mode(self, *md):
        if self.test_flag != 'test':
            if len( md ) == 1:
                mode = str( md[0] )
                if mode in self.sample_mode_dict:
                    flag = self.sample_mode_dict[mode]
                    self.device_write('MODE ' + str(flag))
                else:
                    general.message("Invalid sample mode is given")
                    sys.exit()

            elif len( md ) == 0:
                raw_answer = str( self.device_query('MODE?') )
                return raw_answer
            else:
                general.message("Invalid Argument")
                sys.exit()

        elif self.test_flag == 'test':
            if len( md ) == 1:
                mode = str(md[0])
                assert( mode in self.sample_mode_dict), "Invalid sample mode is given"
                assert( self.hrc_second_channel != 1 ), "Second channel is used as HRC"
            elif len( md ) == 0:
                assert( self.hrc_second_channel != 1 ), "Second channel is used as HRC"
                return self.test_sample_mode
            else:
                assert( 1 == 2 ), "Invalid Argument"

    def level_monitor_units(self, *un):
        if self.test_flag != 'test':
            if len( un ) == 1:
                unit = str( un[0] )
                if unit in self.units_dict:
                    flag = self.units_dict[unit]
                    self.device_write('UNITS ' + str(flag))
                else:
                    general.message("Invalid units are given")
                    sys.exit()

            elif len( un ) == 0:
                raw_answer = str( self.device_query('UNITS?') )
                return raw_answer
            else:
                general.message("Invalid Argument")
                sys.exit()

        elif self.test_flag == 'test':
            if len( un ) == 1:
                unit = str(un[0])
                assert( unit in self.units_dict), "Invalid units are given"
                assert( self.hrc_second_channel != 1 ), "Second channel is used as HRC"
            elif len( un ) == 0:
                assert( self.hrc_second_channel != 1 ), "Second channel is used as HRC"
                return self.test_units
            else:
                assert( 1 == 2 ), "Invalid Argument"

    def level_monitor_measure(self, ch):
        if self.test_flag != 'test':
                if ch == '1':
                    self.device_write('MEAS ' + '1')
                    # wait for the measurement to finish
                    while str( bin( int(self.device_query('*STB?')) )[-1]  ) != '1':
                        general.wait('1000 ms')
                    # Clear STB Byte
                    self.device_write('*CLS')
                    
                    return self.device_query('MEAS? ' + '1')
                    
                elif ch == '2':
                    self.device_write('MEAS ' + '2')
                    # wait for the measurement to finish
                    while str( bin( int(self.device_query('*STB?')) )[-3]  ) != '1':
                        general.wait('1000 ms')
                    # Clear STB Byte
                    self.device_write('*CLS')

                    return self.device_query('MEAS? ' + '2')
                else:
                    general.message("Invalid channel")
                    sys.exit()

        elif self.test_flag == 'test':
            assert( ch == '1' or ch == '2'), "Invalid channel"

    def level_monitor_sample_interval(self, *interv):
        if self.test_flag != 'test':
            if len( interv ) == 3:
                h = int(interv[0])
                m = int(interv[1])
                s = int(interv[2])
                self.device_write('INTVL ' + str(h) + ':' + str(m) + ':' + str(s))
            elif len( interv ) == 0:
                answer = str(self.device_query('INTVL?'))
                return answer
            else:
                general.message("Invalid Argument. It should be ('hours', 'minutes', 'seconds')")
                sys.exit()

        elif self.test_flag == 'test':
            if len( interv ) == 3:
                h = int(interv[0])
                m = int(interv[1])
                s = int(interv[2])
                assert( h >= self.hours_min and h <= self.hours_max ), "The interval hours parameter should be in the range of 0 to 99"
                assert( m >= self.minutes_min and m <= self.minutes_max ), "The interval minutes parameter should be in the range of 0 to 59"
                assert( s >= self.seconds_min and s <= self.seconds_max ), "The interval seconds parameter should be in the range of 0 to 59"
                assert( self.hrc_second_channel != 1 ), "Second channel is used as HRC"
            elif len( interv ) == 0:
                assert( self.hrc_second_channel != 1 ), "Second channel is used as HRC"
                return self.test_interval
            else:
                assert( 1 == 2 ), "Invalid Argument. It should be ('hours', 'minutes', 'seconds')"

    def level_monitor_hrc_target_pressure(self, *pr):
        if self.test_flag != 'test':
            if len( pr ) == 1:
                pressure = round( float(pr[0]) , 3)
                self.device_write('PSET ' + str( pressure ))

            elif len( pr ) == 0:
                answer = str( self.device_query('PSET?') )
                return answer
            else:
                general.message("Invalid Argument")
                sys.exit()

        elif self.test_flag == 'test':
            if len( pr ) == 1:
                pressure = round( float(pr[0]) , 3)
                assert( pressure >= self.targ_pressure_min and pressure <= self.targ_pressure_max ), "Target pressure should be in the range of 0.15 to 14.25 psi"
                assert( self.hrc_second_channel == 1 ), "Second channel is not used as HRC"
            elif len( pr ) == 0:
                assert( self.hrc_second_channel == 1 ), "Second channel is not used as HRC"
                return self.test_pressure
            else:
                assert( 1 == 2 ), "Invalid Argument"

    def level_monitor_hrc_heater_power_limit(self, *lim):
        if self.test_flag != 'test':
            if len( lim ) == 1:
                limit = round( float(lim[0]) , 2)
                self.device_write('HLIM ' + str( limit ))

            elif len( lim ) == 0:
                answer = str( self.device_query('HLIM?') )
                return answer
            else:
                general.message("Invalid Argument")
                sys.exit()

        elif self.test_flag == 'test':
            if len( lim ) == 1:
                limit = round( float(lim[0]) , 2)
                assert( limit >= self.heater_limit_min and limit <= self.heater_limit_max ), "Heater power limit should be in the range of 0.1 to 10 watts"
                assert( self.hrc_second_channel == 1 ), "Second channel is not used as HRC"
            elif len( lim ) == 0:
                assert( self.hrc_second_channel == 1 ), "Second channel is not used as HRC"
                return self.test_heater_limit
            else:
                assert( 1 == 2 ), "Invalid Argument"

    def level_monitor_hrc_heater_enable(self, *st):
        if self.test_flag != 'test':
            if len( st ) == 1:
                state = str( st[0] )
                if state in self.heater_dict:
                    flag = self.heater_dict[state]
                    self.device_write('HEAT ' + str(flag))
                else:
                    general.message("Invalid heater state is given")
                    sys.exit()

            elif len( st ) == 0:
                raw_answer = str( self.device_query('HEAT?') )
                if raw_answer == 'ON':
                    return 'On'
                elif raw_answer == 'OFF':
                    return 'Off'
            else:
                general.message("Invalid Argument")
                sys.exit()

        elif self.test_flag == 'test':
            if len( st ) == 1:
                state = str( st[0] )
                assert( state in self.heater_dict), "Invalid heater state is given"
                assert( self.hrc_second_channel == 1 ), "Second channel is not used as HRC"
            elif len( st ) == 0:
                assert( self.hrc_second_channel == 1 ), "Second channel is not used as HRC"
                return self.test_heater_state
            else:
                assert( 1 == 2 ), "Invalid Argument"

    def level_monitor_command(self, command):
        if self.test_flag != 'test':
            self.device_write(command)
        elif self.test_flag == 'test':
            pass

    def level_monitor_query(self, command):
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

