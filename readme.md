# Atomize - Split your spectrometer apart!
![](https://github.com/Anatoly1010/Atomize/blob/master/screenshots/logoAtomize.png)<br/>
A modular open source software for working with scientific devices and combining them into spectrometer.<br/>
The general idea is close to [FSC2 software](http://users.physik.fu-berlin.de/~jtt/fsc2.phtml) developed by Jens Thomas Törring.<br/>
Remote control of spectrometers is usually carried out using home-written programs, which are often restricted to doing a certain experiment with a specific set of devices. In contrast, the programs like [FSC2](http://users.physik.fu-berlin.de/~jtt/fsc2.phtml) and [Atomize](https://github.com/Anatoly1010/Atomize) are much more flexible, since they are based on a modular approach for communication with device and scripting language (EDL in FSC2; Python in Atomize) for data measuring.

Atomize uses [liveplot library](https://github.com/PhilReinhold/liveplot) based on pyqtgraph as a main graphics library. [Liveplot](https://github.com/PhilReinhold/liveplot) was originally developed by Phil Reinhold. Since several minor improvements have been made to use it in Atomize.

[Python Programming Language](https://www.python.org/) is used inside experimental scripts, which opens up almost unlimited possibilities for raw experimental data treatment. In addition, with PyQt, one can create experimental scripts with a simple graphical interface, allowing users not familiar with Python to use it. Several examples of scripts (with dummy data) are provided in /atomize/tests/ directory, including a GUI script with extended comments inside. Also a variant of the Atomize with GUI Control Window extension can be found [here.](https://github.com/Anatoly1010/Atomize_NIOCH)<br/>

Currently there are more than 200 device specific and general functions available for over 25 different devices, including 4 series of devices. If you would like to write a module for the device that is not currently available, please, read this short [instruction.](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/writing_modules.md)

Detailed documentation can be found [here.](https://github.com/Anatoly1010/Atomize/tree/master/atomize/documentation)

## Status

At the moment, Atomize has been tested and is currently used for controlling several EPR spectrometers using a broad range of different devices. Examples of experimental scripts for standard pulsed EPR methods can be found in /atomize/tests/pulse_epr directory. The program has been tested on Ubuntu 18.04 LTS, 20.04 LTS, and 22.04 LTS.

## Contents
- [Requirements](#requirements)<br/>
- [Basic usage](#basic-usage)<br/>
- [Available devices](#available-devices)<br/>
    - [Temperature Controllers](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/temperature_controller_functions.md)<br/>
    - [Lock-in Amplifiers](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/lock_in_amplifier_functions.md)<br/>
    - [Oscilloscopes](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/oscilloscope_functions.md)<br/>
    - [Digitizers](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/digitizer_functions.md)<br/>
    - [Oscilloscope Wave Generators](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/oscilloscope_wave_generator_functions.md)<br/>
    - [Arbitrary Wave Generators](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/awg_functions.md)<br/>
    - [Pulse Programmers](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/pulse_programmers_functions.md)<br/>
    - [Frequency Counters](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/frequency_counter_functions.md)<br/>
    - [Magnetic Field Controllers](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/magnet_functions.md)<br/>
    - [Microwave Bridge Controllers](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/microwave_bridge_functions.md)<br/>
    - [Gaussmeters](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/gaussmeter_functions.md)<br/>
    - [Power Supplies](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/power_supply_functions.md)<br/>
    - [Delay Generators](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/delay_generator_functions.md)<br/>
    - [Balances](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/other_device_functions.md)<br/>
    - [Other](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/other_device_functions.md)<br/>
- [Function for devices](#available-function-for-devices)<br/>
- [General functions](#available-general-functions)<br/>
- [Plotting functions](#available-plotting-functions)<br/>
- [Experimental script examples](https://github.com/Anatoly1010/Atomize/tree/master/atomize/tests)<br/>
- [Screenshots](#screenshots)<br/>
- [Writing modules](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/writing_modules.md)<br/>
- [Protocol settings](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/protocol_settings.md)<br/>

## Requirements
- [Python (3.8+)](https://www.python.org/)
- [Numpy](https://numpy.org/)
- [PyQt6; 6.1.0+](http://www.riverbankcomputing.com/software/pyqt/download)
- [pyqtgraph 0.12.2](http://www.pyqtgraph.org)
- [PyVisa](https://pyvisa.readthedocs.io/en/latest/)
- [PyVisa-py](https://github.com/pyvisa/pyvisa-py)<br/>
Optional:
- [PySerial;](https://pypi.org/project/pyserial/) for serial instruments
- [Minimalmodbus;](https://minimalmodbus.readthedocs.io/en/stable/index.html) for Modbus instruments
- [GPIB driver;](https://linux-gpib.sourceforge.io/) for GPIB devices
- [Telegram bot API;](https://github.com/eternnoir/pyTelegramBotAPI) for Telegram bot messages
- [SpinAPI;](http://www.spincore.com/support/spinapi/) for Pulse Blaster ESR 500 Pro
- [Spcm driver;](https://spectrum-instrumentation.com/en/m4i4450-x8) for Spectrum M4I 6631 X8; M4I 4450 X8

## Basic usage

1. Atomize

Install from the source directory:

	pip3 install -e .

run from the source directory:

	python3 atomize

or using bash option to open specified script:

	python3 atomize /path/to/experimental/script

To communicate with Liveplot inside a script the general function module should be imported.
```python
import atomize.general_modules.general_functions as general
general.plot_1d(arguments)
```
The text editor used for editing can be specified in atomize/config.ini. The Telegram bot token and message chat ID can be specified in the same file.

2. Setting up general configuration data

The /atomize directory contains a general configuration file with the name config.ini. It should be changed at will according to the description below:
```python
[DEFAULT]
# configure the text editor that will opened when Edit is pressed:
editor = subl	# Linux
editorW = /path/to/text_editor/on/Windows/	# Windows
# configure the directory that will opened when Open 1D Data or Open 2D Data
# feature is used in Liveplot:
open_dir = /path/to/experimental/data/to/open/
# configure the directory that will be opened when Open Script is pressed:
script_dir = /Atomize/atomize/tests
# configure Telegram bot
telegram_bot_token = 
message_id = 
```

3. Using device modules

To communicate with a device one should:
1) modify the config file (/atomize/device_modules/config/) of the desired device accordingly. Choose the desired protocol (rs-232, gpib, ethernet, etc.) and correct the settings of the specified protocol in accordance with device settings. A little bit more detailed information about protocol settings can be found [here.](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/protocol_settings.md)
2) import the module or modules in your script and initialize the appropriate class. A class always
has the same name as the module file. Initialization connect the desired device, if the settings are correct.
```python
import atomize.device_modules.Keysight_3000_Xseries as keys
import atomize.device_modules.Lakeshore331 as tc
dsox3034t = keys.Keysight_3000_Xseries()
lakeshore331 = tc.Lakeshore331()
name_oscilloscope = dsox3034t.oscilloscope_name()
temperature = lakeshore331.tc_temperature('CH A')
```
The same idea is valid for plotting and file handling modules. The description of available
functions is given below.
```python
import atomize.general_modules.general_functions as general
import atomize.general_modules.csv_opener_saver_tk_kinter as openfile
file_handler = openfile.Saver_Opener()
head, data = file_handler.open_1D_dialog(header = 0)
general.plot_1d('1D Plot', data[0], data[1], label = 'test_data', yname = 'Y axis', yscale = 'V')
```
4. Experimental scripts

Python is used to write an experimental script. Examples (with dummy data) can be found in
/atomize/tests/ directory.

## Available devices
#### [Temperature Controllers](#temperature-controllers-1)
	- Lakeshore (GPIB, RS-232)
	325; 331; 332; 335; 336; 340; Tested 01/2021
	- Oxford Instruments (RS-232)
	ITC 503; Tested 01/2021
    - Termodat (RS-485)
    11M6; 13KX3; Tested 04/2021
    - Stanford Research (TCP/IP Socket)
	PTC10; Tested 07/2021
	- Scientific Instruments (TCP/IP Socket, RS-232)
	SCM10 Temperature Monitor; 07/2022

#### [Lock-in Amplifiers](#lock-in-amplifiers-1)
	- Stanford Research Lock-In Amplifier (GPIB, RS-232)
	SR-810; SR-830; SR-850; Tested 02/2021
	- Stanford Research Lock-In Amplifier (GPIB, RS-232, Ethernet)
	SR-860; SR-865a; Tested 01/2021

#### [Oscilloscopes](#oscilloscopes-1)
	- Keysight InfiniiVision 2000 X-Series (Ethernet); Untested
	- Keysight InfiniiVision 3000 X-Series (Ethernet); Tested 06/2021
	- Keysight InfiniiVision 4000 X-Series (Ethernet); Untested
	- Tektronix 3000 Series (Ethernet); Tested 09/2022
	- Tektronix 4000 Series (Ethernet); Tested 01/2021

#### [Digitizers](#digitizers-1)
	- Spectrum M4I 4450 X8; Tested 08/2021
The original [library](https://spectrum-instrumentation.com/en/m4i4450-x8) was written by Spectrum.

#### [Oscilloscope Wave Generators](#oscilloscope-wave-generators-1)
	- Wave Generator of Keysight InfiniiVision 2000 X-Series (Ethernet)
	Available via corresponding oscilloscope module.
	- Wave Generator of Keysight InfiniiVision 3000 X-Series (Ethernet)
	Available via corresponding oscilloscope module.
	- Wave Generator of Keysight InfiniiVision 4000 X-Series (Ethernet)
	Available via corresponding oscilloscope module.

#### [Arbitrary Wave Generators](#arbitrary-wave-generators-1)
	- Spectrum M4I 6631 X8; Tested 07/2021
The original [library](https://spectrum-instrumentation.com/en/m4i6631-x8) was written by Spectrum.

#### [Pulse Programmers](#pulse-programmers-1)
    - Pulse Blaster ESR 500 Pro; Tested 06/2021
    The device is available via ctypes. 
The original [C library](http://www.spincore.com/support/spinapi/using_spin_api_pb.shtml) was written by SpinCore Technologies.

#### [Frequency Counters](#frequency-counters-1)
	- Agilent Frequency Counter (GPIB, RS-232)
	53181A; 53131A/132A; Tested 02/2021
	- Keysight Frequency Counter (GPIB, RS-232, Ethernet)
	53230A/220A; Untested

#### [Magnetic Field Controllers](#magnetic-field-controllers-1)
	- Bruker BH15 (GPIB); Tested 01/2021
	- Bruker ER032M (GPIB); Available via BH15 module
	- Bruker ER031M (RS-232 using arduino emulated keyboard); Tested 01/2021

#### [Microwave Bridge Controllers](#microwave-bridge-controllers-1)
	- Mikran X-band MW Bridge (TCP/IP Socket); Tested 06/2021

#### [Gaussmeters](#gaussmeters-1)
	- Lakeshore 455 DSP (RS-232); Tested 01/2021

#### [Power Supplies](#power-supplies-1)
	- Rigol DP800 Series (RS-232, Ethernet); Tested 01/2021
	- Stanford Research DC205 (RS-232); Untested
    - Stanford Research PS300 High Voltage Series (RS-232, GPIB); Untested

#### [Delay Generators](#delay-generators-1)
    - Stanford Research DG535 (GPIB); Untested

#### [Balance](#balances-1)
	- CPWplus 150 (RS-232); Tested 01/2021

#### [Other](#other-1)
	- RODOS-10N Solid-State Relay (Ethernet); Tested 01/2021
    - Owen-MK110-220.4DN.4R Discrete IO Module (RS-485); Tested 04/2021
    - Cryomagnetics LM-510 Liquid Cryogen Monitor (TCP/IP Socket); Tested 07/2022
    - Cryomech CPA2896, CPA1110 Digital Panels (RS-485); Tested 07/2022

## [Available general functions](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/general_functions.md)
```python3
message('A message to print')
wait('number + scaling')
to_infinity()
open_1D(path, header = 0)
open_1D_dialog(self, directory = '', header = 0)
save_1D_dialog(data, directory = '', header = '')
open_2D(path, header = 0)
open_2D_dialog(directory = '', header = 0)
open_2D_appended(path, header = 0, chunk_size = 1)
open_2D_appended_dialog(directory = '', header = 0, chunk_size = 1)
save_2D_dialog(data, directory = '', header = '')
create_file_parameters(add_name, directory = '')
save_header(filename, header = '', mode = 'w')
save_data(filename, data, header = '', mode = 'w')
create_file_dialog(directory = '')
create_file_parameters(add_name, directory = '')
save_header(filename, header = '', mode = 'w')
save_data(filename, data, header = '', mode = 'w')
```

## [Available plotting functions](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/plotting_functions.md)
```python3
plot_1d('name', Xdata, Ydata, **args)
plot_2d('name', data, start_step = ((Xstart, Xstep), (Ystart, Ystep)), **args)
text_label('label', DynamicValue)
plot_remove('name')
```
## Available function for devices
### [Temperature controllers](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/temperature_controller_functions.md)
```python3
tc_name()
tc_temperature(channel)
tc_setpoint(*temp)
tc_heater_range(*heater)
tc_heater_power()
tc_heater_power_limit(power)
tc_state(*mode)
tc_sensor(*sensor)
tc_gas_flow(*flow)
tc_lock_keyboard(*lock)
tc_proportional(*prop)]
tc_derivative(*der)
tc_integral(*integ)
tc_command(command)
tc_query(command)
```
### [Oscilloscopes](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/oscilloscope_functions.md)
```python3
oscilloscope_name()
oscilloscope_record_length(*points)
oscilloscope_acquisition_type(*ac_type)
oscilloscope_number_of_averages(*number_of_averages)
oscilloscope_timebase(*timebase)
oscilloscope_define_window(**kargs)
oscilloscope_time_resolution()
oscilloscope_start_acquisition()
oscilloscope_preamble(channel)
oscilloscope_area(channel)
oscilloscope_stop()
oscilloscope_run()
oscilloscope_get_curve(channel)
oscilloscope_sensitivity(*channel)
oscilloscope_offset(*channel)
oscilloscope_horizontal_offset(*h_offset)
oscilloscope_coupling(*coupling)
oscilloscope_impedance(*impedance)
oscilloscope_trigger_mode(*mode)
oscilloscope_trigger_channel(*channel)
oscilloscope_trigger_low_level(*level)
oscilloscope_command(command)
oscilloscope_query(command)
```
### [Digitizers](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/digitizer_functions.md)
```python3
digitizer_name()
digitizer_setup()
digitizer_get_curve()
digitizer_close()
digitizer_stop()
digitizer_number_of_points(*points)
digitizer_posttrigger(*post_points)
digitizer_channel(*channel)
digitizer_sample_rate(*s_rate)
digitizer_clock_mode(*mode)
digitizer_reference_clock(*ref_clock)
digitizer_card_mode(*mode)
digitizer_trigger_channel(*ch)
digitizer_trigger_mode(*mode)
digitizer_number_of_averages(*averages)
digitizer_trigger_delay(*delay)
digitizer_input_mode(*mode)
digitizer_amplitude(*ampl)
digitizer_offset(*offset)
digitizer_coupling(*coupling)
digitizer_impedance(*impedance)
```
### [Oscilloscope wave generators](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/oscilloscope_wave_generator_functions.md)
```python3
wave_gen_name()
wave_gen_frequency(*frequency)
wave_gen_pulse_width(*width)
wave_gen_function(*function)
wave_gen_amplitude(*amplitude)
wave_gen_offset(*offset)
wave_gen_impedance(*impedance)
wave_gen_run()
wave_gen_stop()
wave_gen_arbitrary_function(list)
wave_gen_arbitrary_clear()
wave_gen_arbitrary_interpolation(*mode)
wave_gen_arbitrary_points()
wave_gen_command(command)
wave_gen_query(command)
```
### [Arbitrary wave generators](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/awg_functions.md)
```python3
awg_name()
awg_setup()
awg_update()
awg_stop()
awg_close()
awg_pulse(*kargs)
awg_pulse_sequence(kargs)
awg_shift(*pulses)
awg_increment(*pulses)
awg_next_phase()
awg_redefine_delta_phase(*, name, delta_phase)
awg_redefine_phase(self, *, name, phase)
awg_redefine_frequency(self, *, name, freq)
awg_redefine_delta_start(self, *, name, delta_start)
awg_redefine_increment(*, name, increment)
awg_add_phase(*, name, add_phase)
awg_reset()
awg_pulse_reset(*pulses)
awg_number_of_segments(*segments)
awg_channel(*channel)
awg_sample_rate(*s_rate)
awg_clock_mode(*mode)
awg_reference_clock(*ref_clock)
awg_card_mode(*mode)
awg_trigger_channel(*channel)
awg_trigger_mode(*mode)
awg_loop(*loop)
awg_trigger_delay(*delay)
awg_amplitude(*amplitude)
awg_visualize()
awg_pulse_list()
```
### [Pulse programmers](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/pulse_programmers_functions.md)
```python3
pulser_name()
pulser_pulse(*kargs)
pulser_update()
pulser_next_phase()
pulser_acquisition_cycle(data1, data2, acq_cycle = [])
pulser_repetition_rate(*r_rate)
pulser_shift(*pulses)
pulser_increment(*pulses)
pulser_redefine_start(*, name, start)
pulser_redefine_delta_start(*, name, delta_start)
pulser_redefine_length_increment(*, name, length_increment)
pulser_reset()
pulser_pulse_reset(*pulses)
pulser_stop()
pulser_state()
pulser_visualize()
pulser_pulse_list()
```
### [Lock-in amplifiers](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/lock_in_amplifier_functions.md)
```python3
lock_in_name()
lock_in_ref_frequency(*frequency)
lock_in_phase(*degree)
lock_in_time_constant(*timeconstant)
lock_in_ref_amplitude(*amplitude)
lock_in_get_data(*channel)
lock_in_sensitivity(*sensitivity)
lock_in_ref_mode(*mode)
lock_in_ref_slope(*mode)
lock_in_sync_filter(*mode)
lock_in_lp_filter(*mode)
lock_in_harmonic(*harmonic)
lock_in_command(command)
lock_in_query(command)
```
### [Frequency counters](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/frequency_counter_functions.md)
```python3
freq_counter_name()
freq_counter_frequency(channel)
freq_counter_impedance(*impedance)
freq_counter_coupling(*coupling)
freq_counter_stop_mode(*mode)
freq_counter_start_mode(*mode)
freq_counter_gate_mode(*mode)
freq_counter_digits(*digits)
freq_counter_gate_time(*time)
freq_counter_expected_freq(*frequency)
freq_counter_period(channel)
freq_counter_command(command)
freq_counter_query(command)
```
### [Magnetic field controllers](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/magnet_functions.md)
```python3
magnet_name()
magnet_setup(start_field, step_field)
magnet_field(*field)
magnet_sweep_up()
magnet_sweep_down()
magnet_reset_field()
magnet_field_step_size(*step)
magnet_command(command)
```
### [Microwave bridge controllers](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/microwave_bridge_functions.md)
```python3
mw_bridge_name()
mw_bridge_synthesizer(*freq)
mw_bridge_att1_prd(*atten)
mw_bridge_att2_prd(*atten)
mw_bridge_fv_ctrl(*phase)
mw_bridge_fv_prm(*phase)
mw_bridge_att_prm(*atten)
mw_bridge_k_prm(*amplif)
mw_bridge_cut_off(*cutoff)
mw_bridge_telemetry()
mw_bridge_initialize()
```
### [Gaussmeters](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/gaussmeter_functions.md)
```python3
gaussmeter_name()
gaussmeter_field()
gaussmeter_units(*units)
gaussmeter_command(command)
gaussmeter_query(command)
```
### [Power supplies](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/power_supply_functions.md)
```python3
power_supply_name()
power_supply_voltage(*voltage)
power_supply_current(*current)
power_supply_overvoltage(*voltage)
power_supply_overcurrent(*current)
power_supply_channel_state(*state)
power_supply_measure(channel)
power_supply_preset(preset)
power_supply_range(*range)
power_supply_interlock()
power_supply_rear_mode(*mode)
power_supply_command(command)
power_supply_query(command)
```
### [Delay generators](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/delay_generator_functions.md)
```python3
delay_gen_name()
delay_gen_delay(*delay)
delay_gen_impedance(*impedance)
delay_gen_output_mode(*mode)
delay_gen_amplitude_offset(*amplitude_offset)
delay_gen_output_polarity(*polarity)
delay_gen_command(command)
delay_gen_query(command)
```
### [Balance](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/other_device_functions.md)
```python3
balance_weight()
```
### [Other](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/other_device_functions.md)
#### RODOS-10N Solid-sate Relay (Ethernet)
```python3
relay_turn_on(number)
relay_turn_off(number)
```
#### Owen-MK110-220.4DN.4R Discrete IO Module (RS-485)
```python3
discrete_io_input_counter(channel)
discrete_io_input_counter_reset(channel)
discrete_io_input_state()
discrete_io_output_state(*state)
```
#### Cryomech CPA2896, CPA1110 Digital Panels (RS-485)
```python3
cryogenic_refrigerator_name()
cryogenic_refrigerator_state(*state)
cryogenic_refrigerator_status_data()
cryogenic_refrigerator_warning_data()
cryogenic_refrigerator_pressure_scale()
cryogenic_refrigerator_temperature_scale()
```
#### Cryomagnetics LM-510 Liquid Cryogen Monitor (TCP/IP Socket)
```python3
level_monitor_name()
level_monitor_select_channel(*channel)
level_monitor_boost_mode(*mode)
level_monitor_high_level_alarm(*level)
level_monitor_low_level_alarm(*level)
level_monitor_sensor_length()
level_monitor_sample_mode(*mode)
level_monitor_units(*units)
level_monitor_measure(channel)
level_monitor_sample_interval(*interval)
level_monitor_hrc_target_pressure(*pressure)
level_monitor_hrc_heater_power_limit(*limit)
level_monitor_hrc_heater_enable(*state)
level_monitor_command(command)
level_monitor_query(command)
```

## Screenshots
![](https://github.com/Anatoly1010/Atomize/blob/master/screenshots/screenshot.png)
![](https://github.com/Anatoly1010/Atomize/blob/master/screenshots/screenshot2.png)
![](https://github.com/Anatoly1010/Atomize/blob/master/screenshots/screenshot3.png)