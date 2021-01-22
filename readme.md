# Atomize - Split your spectrometer apart!
![](https://github.com/Anatoly1010/Atomize/blob/master/screenshots/logoAtomize.png)<br/>
A modular open source software for working with scientific devices and combining them into spectrometer.<br/>
The general idea is close to [FSC2 software](http://users.physik.fu-berlin.de/~jtt/fsc2.phtml) developed by Jens Thomas Törring.<br/>
Remote control of spectrometers is usually carried out using home-written programs, which are often restricted to doing a certain experiment with a specific set of devices. In contrast, the programs like [FSC2](http://users.physik.fu-berlin.de/~jtt/fsc2.phtml) and [Atomize](https://github.com/Anatoly1010/Atomize) are much more flexible, since they are based on a modular approach for communication with device and scripting language (EDL in FSC2; Python in Atomize) for data measuring.

Atomize uses [liveplot library](https://github.com/PhilReinhold/liveplot) based on pyqtgraph as a main graphics library. [Liveplot](https://github.com/PhilReinhold/liveplot) was originally developed by Phil Reinhold. Since several minor improvements have been made to use it in Atomize, the latest version of liveplot is included to Atomize.

[Python Programming Language](https://www.python.org/) is used inside experimental scripts, which opens up almost unlimited possibilities for raw experimental data treatment. In addition, with PyQt, one can create experimental scripts with a simple graphical interface, allowing users not familiar with Python to use it. Several examples of scripts (with dummy data) are provided in /atomize/tests/ directory, including a GUI script with extended comments inside.<br/>
At the moment, the program has been tested on Ubuntu 18.04 LTS, 20.04 LTS, and Windows 10.

### Status: in development; device testing

## Requirements
- [Python (tested with 3.6+)](https://www.python.org/)
- [Numpy](https://numpy.org/)
- [PyQt5](http://www.riverbankcomputing.com/software/pyqt/download)
- [pyqtgraph](http://www.pyqtgraph.org)
- [PyVisa](https://pyvisa.readthedocs.io/en/latest/)
- [PyVisa-py](https://github.com/pyvisa/pyvisa-py)
- [PySerial;](https://pypi.org/project/pyserial/) for serial instruments
- [OpenGL;](https://pypi.org/project/PyOpenGL/) highly recommended for efficient plotting 
- [Scipy;](https://www.scipy.org/) optional, for math modules
- [GPIB driver;](https://linux-gpib.sourceforge.io/) optional

## Basic usage

1. Atomize

Install from the source directory:

	pip3 install .

run from the source directory:

	python3 atomize

or using bash option to open specified script:

	python3 atomize /path/to/experimental/script

The text editor used for editing  can be specified in atomize/config.ini

2. [Liveplot](https://github.com/PhilReinhold/liveplot) Author: Phil Reinhold

Install from the source directory (from atomize/liveplot):

	python3 setup.py install

Start the window (optional; atomize opens it)

	python3 -m liveplot

To communicate with Liveplot inside a script the general function module should be
imported and the Liveplot window should be open.
```python
import atomize.general_modules.general_functions as general
general.plot_1d(arguments)
```

3. Using device modules

To communicate with a device one should:
1) modify the config file (/atomize/device_modules/config/) of the desired device accordingly.
Usually you need to specify the interface type and interface settings.
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

5. Speeding up plotting functions

It is highly recommended to use OpenGL, if you want to plot data with more than 2000 points.
On Ubuntu 18.04 LTS, 20.04 LTS python openGL bindings can be installed as:

	apt-get install python3-pyqt5.qtopengl

On Windows 10 one should use:
	
	pip install PyOpenGL PyOpenGL_accelerate

## Available devices
#### Temperature Controllers
	- Lakeshore (GPIB, RS-232)
	325; 331; 332; 335; 336; 340; Tested 01/21
	- Oxford Instruments (RS-232)
	ITC 503; Tested 01/21

#### Lock-in Amplifiers
	- Stanford Research Lock-In Amplifier (GPIB, RS-232)
	SR-810; SR-830; SR-850 (untested).
	- Stanford Research Lock-In Amplifier (GPIB, RS-232, Ethernet)
	SR-860; SR-865a; Tested 01/2021

#### Oscilloscopes
	- Keysight InfiniiVision 2000 X-Series (Ethernet); untested
	- Keysight InfiniiVision 3000 X-Series (Ethernet); tested
	- Keysight InfiniiVision 4000 X-Series (Ethernet); untested
	- Tektronix 4000 Series (Ethernet); Tested 01/2021

#### Arbitrary Wave Generators
	- Wave Generator of Keysight InfiniiVision 2000 X-Series (Ethernet)
	Available via corresponding oscilloscope module.
	- Wave Generator of Keysight InfiniiVision 3000 X-Series (Ethernet)
	Available via corresponding oscilloscope module.
	- Wave Generator of Keysight InfiniiVision 4000 X-Series (Ethernet)
	Available via corresponding oscilloscope module.

#### Frequency Counters
	- Agilent Frequency Counter (GPIB)
	53181A (untested); 53131A/132A.
	- Keysight Frequency Counter (GPIB, RS-232, Ethernet)
	53230A/220A (untested).

#### Magnetic Field Controller
	- Bruker BH15 (GPIB); Tested 01/2021
	- Bruker ER032M (GPIB); available via BH15 module
	- Bruker ER031M (RS-232 using arduino emulated keyboard) tested

#### Balances
	- CPWplus 150 (RS-232); Tested 01/2021

#### Other
	- Solid-state Relay RODOS-10N (Ethernet); Tested 01/2021

## [Available general functions](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/general_functions.md)
```python3
message('A message to print')
wait('number + scaling')
open_1D(path, header = 0)
open_1D_dialog(self, directory = '', header = 0)
save_1D_dialog(data, directory = '', header = '')
open_2D(path, header = 0)
open_2D_dialog(directory = '', header = 0)
open_2D_appended(path, header = 0, chunk_size = 1)
open_2D_appended_dialog(directory = '', header = 0, chunk_size = 1)
save_2D_dialog(data, directory = '', header = '')
create_file_dialog(directory = '')
```

## [Available plotting functions](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/plotting_functions.md)
```python3
plot_1d('name', Xdata, Ydata, **args)
append_1d('name', value, start_step = (x[0], x[1]-x[0]), label = 'label', **args)
plot_2d('name', data, start_step = ((Xstart, Xstep), (Ystart, Ystep)), **args)
append_2d('name', data, start_step = ((Xstart, Xstep), (Ystart, Ystep)), **args)
text_label('label', 'text', DynamicValue)
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
### [Wave generators](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/wave_generator_functions.md)
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
freq_counter_ratio(channel1, channel2)
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
### [Balances](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/other_device_functions.md)
```python3
balance_weight()
```
### [Other](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/other_device_functions.md)
#### Solid-sate Relay RODOS-10N (Ethernet)
```python3
turn_on(number)
turn_off(number)
```

## Screenshots
![](https://github.com/Anatoly1010/Atomize/blob/master/screenshots/screenshot.png)
![](https://github.com/Anatoly1010/Atomize/blob/master/screenshots/screenshot2.png)