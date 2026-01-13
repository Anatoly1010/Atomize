import time
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.Rigol_MSO8000_Series as key

r8104 = key.Rigol_MSO8000_Series()

#general.message( r8104.oscilloscope_name() )

r8104.oscilloscope_record_length(10000)
#general.message(r8104.oscilloscope_record_length())

r8104.oscilloscope_acquisition_type('Average')
#general.message(r8104.oscilloscope_acquisition_type())

#r8104.oscilloscope_number_of_averages(10)
#general.message(r8104.oscilloscope_number_of_averages())

#r8104.oscilloscope_timebase('990 us')
#general.message(r8104.oscilloscope_timebase())

#general.message(r8104.oscilloscope_time_resolution())

#r8104.oscilloscope_stop()
#r8104.oscilloscope_run()

#general.message(r8104.oscilloscope_preamble('CH1'))

r8104.oscilloscope_start_acquisition()
x, y, i = r8104.oscilloscope_get_curve('CH1', mode='Normal', integral = 'Both')

general.plot_1d('1D', x, y, label = 'raw2', xname = 'Delay', xscale = 's', yname = 'Area', yscale = 'V')

#r8104.oscilloscope_sensitivity('CH1', '20 mV')
#general.message(r8104.oscilloscope_sensitivity('CH1'))

#r8104.oscilloscope_offset('CH1', '-10 mV')
#general.message(r8104.oscilloscope_offset('CH1'))

#r8104.oscilloscope_horizontal_offset('1 ms')
#general.message(r8104.oscilloscope_horizontal_offset())

#r8104.oscilloscope_coupling('CH1', 'AC')
#general.message(r8104.oscilloscope_coupling('CH1'))

#r8104.oscilloscope_impedance('CH1', 'AC')
#general.message(r8104.oscilloscope_impedance('CH1'))

#r8104.oscilloscope_trigger_mode('Normal')
#general.message(r8104.oscilloscope_trigger_mode())

#r8104.oscilloscope_trigger_channel('CH1')
#general.message(r8104.oscilloscope_trigger_channel())

#r8104.oscilloscope_trigger_low_level('CH1', '20 mV')
#general.message(r8104.oscilloscope_trigger_low_level('CH1'))

#r8104.wave_gen_frequency('202 Hz', channel = '2')
#general.message(r8104.wave_gen_frequency(channel = '2'))

#r8104.wave_gen_pulse_width(10, channel = '2')
#general.message(r8104.wave_gen_pulse_width(channel = '2'))

#r8104.wave_gen_function('Pulse', channel = '2')
#general.message(r8104.wave_gen_function(channel = '2'))

#r8104.wave_gen_amplitude('0.02 V', channel = '2')
#general.message(r8104.wave_gen_amplitude(channel = '2'))

#r8104.wave_gen_offset('20 mV', channel = '2')
#general.message(r8104.wave_gen_offset(channel = '2'))

#r8104.wave_gen_offset('20 mV', channel = '2')
#general.message(r8104.wave_gen_impedance(channel = '2'))

#r8104.wave_gen_start()
#r8104.wave_gen_stop()

#r8104.wave_gen_phase(20, channel = '2')
#general.message(r8104.wave_gen_phase(channel = '2'))