# Atomize - Split your spectrometer apart!
![](https://github.com/Anatoly1010/Atomize/blob/master/logoAtomize.png)<br/>
A modular open source software for working with scientific devices and combining them into a spectrometer.<br/>
The general idea is close to [FSC2 software](http://users.physik.fu-berlin.de/~jtt/fsc2.phtml) developed by Jens Thomas Törring.<br/>
Remote control of spectrometers is usually carried out using home-written programs, which are often restricted to doing a certain experiment with a specific set of devices. In contrast, the programs like [FSC2](http://users.physik.fu-berlin.de/~jtt/fsc2.phtml) and [Atomize](https://github.com/Anatoly1010/Atomize) are much more flexible, since they are based on a modular approach for communication with device and scripting language (EDL in FSC2; Python in Atomize) for data measuring.

Atomize uses [liveplot library](https://github.com/PhilReinhold/liveplot) based on pyqtgraph as a main graphics library. [Liveplot](https://github.com/PhilReinhold/liveplot) was originally developed by Phil Reinhold. Since several minor improvements have been made to use it in Atomize, the latest version of liveplot is included to Atomize.

[Python Programming Language](https://www.python.org/) is used inside experimental scripts, which opens up almost unlimited possibilities for raw experimetnal data treatment. In addition, with PyQt, one can create experimental scripts with a simple graphical interface, allowing users not familiar with Python to use it.
Several examples of scripts (with dummy data) are provided in /atomize/tests/ directory, including a GUI script with extended comments inside.

### Status: early in development; waiting for device tests

## Requirements
- [Python (tested with 3.8+)](https://www.python.org/)
- [Numpy](https://numpy.org/)
- [Scipy](https://www.scipy.org/)
- [PyQt5](http://www.riverbankcomputing.com/software/pyqt/download)
- [pyqtgraph](http://www.pyqtgraph.org)
- [PyVisa-py](https://github.com/pyvisa/pyvisa-py)

## Basic usage

1. Atomize

Install from the source directory:

	pip3 install .

run from the source directory:

	python3 atomize

or using bash option to open specified script:

	python3 atomize /path/to/experimental/script


2. [Liveplot](https://github.com/PhilReinhold/liveplot)  Author: Phil Reinhold

Install from the source directory (from atomize/liveplot):

	python3 setup.py install

Start the window (optional; atomize opens it)

	python3 -m liveplot

To communicate with Liveplot inside a script it should be imported and initialized:
```python
from liveplot import LivePlotClient
plotter = LivePlotClient()
plotter.plotter_functions()
```

3. Using device modules<br/>
To communicate with a device one should:
1) modify the config file (/atomize/device_modules/config/) of the desired device accordingly.
Usually you need to specify the interface type and interface settings.
2) import the module or modules in your script:
```python
import atomize.device_modules.keysight_3000_Xseries as keys
import atomize.device_modules.Lakeshore331 as tc

name_oscilloscope = keys.oscilloscope_name()
temperature = tc.tc_temperature('CH A')
```

4. Experimental script<br/>
Python is used to write an experimental script. Examples (with dummy data) can be found in
/atomize/tests/ directory.

## Available devices
#### Temperature Controllers
	- LakeShore (Gpib, RS-232)
	325 (untested); 331 (untested); 332 (untested); 335; 336 (untested); 340.

#### Lock-in Amplifiers
	- Stanford Research Lock-In Amplifier (Gpib, RS-232)
	SR-810; SR-830; SR-850 (untested).
	- Stanford Research Lock-In Amplifier (Gpib, RS-232, ethernet)
	SR-860 (untested); SR-865a (untested).

#### Oscilloscopes
	- Keysight InfiniiVision 2000 X-Series (Ethernet)
	MSO-X 2004A; MSO-X 2002A; DSO-X 2004A; DSO-X 2002A; MSO-X 2014A; MSO-X 2012A;
	DSO-X 2014A; DSO-X 2012A; MSO-X 2024A; MSO-X 2022A; DSO-X 2024A; DSO-X 2022A.
	- Keysight InfiniiVision 3000 X-Series (Ethernet)
	MSO-X 3014A; MSO-X 3012A; DSO-X 3014A; DSO-X 3012A; MSO-X 3024A; DSO-X 3024A;
	MSO-X 3034A; MSO-X 3032A; DSO-X 3034A; DSO-X 3032A; MSO-X 3054A; MSO-X 3052A;
	DSO-X 3054A; DSO-X 3052A; MSO-X 3104A; MSO-X 3102A; DSO-X 3104A; DSO-X 3102A.

#### Arbitrary Wave Generators
	- Wave Generator of Keysight InfiniiVision 3000 X-Series (Ethernet)
	Available via corresponding oscilloscope module.

#### Frequency Counters
	- Agilent Frequency Counter (Gpib)
	53181A (untested); 53131A/132A.
	- Keysight Frequency Counter (Gpib)
	53230A/220A (untested).

#### Magnetic Field Controller
	- Bruker ER031M (RS-232 using arduino emulated keyboard) tested

#### Balances
	- CW 150 (RS-232) tested

#### Other
	- Solid-state Relay RODOS-10N (ethernet) tested

## [Available general functions](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/general_functions.md)
```python3
message('A message to print')
open_1D(path, header=0)
open_1D_dialog(self, directory='', fmt='', header=0)
save_1D_dialog(data, directory='', fmt='', header='')
open_2D(path, header=0)
open_2D_dialog(directory='', fmt='', header=0)
open_2D_appended(path, header=0, chunk_size=1)
open_2D_appended_dialog(directory='', fmt='', header=0, chunk_size=1)
save_2D_dialog(data, directory='', fmt='', header='')
create_file_dialog(directory='', fmt='')
```

## [Available plotting functions](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/plotting_functions.md)
```python3
plot_xy('name', Xdata, Ydata, **args)
append_y('name', value, start_step=(x[0], x[1]-x[0]), label='label', **args)
plot_z('name', data, start_step=((Xstart, Xstep), (Ystart, Ystep)), **args)
append_z('name', data, start_step=((Xstart, Xstep), (Ystart, Ystep)), **args)
label('label', 'text: %d' % DynamicValue)
clear()
```
## Available function for devices
### [Temperature controllers](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/temperature_controller_functions.md)
```python3
tc_name()
tc_temperature(channel)
tc_setpoint(*temp)
tc_heater_range(*heater)
tc_heater_state()
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
oscilloscope_time_resolution()
oscilloscope_start_acquisition()
oscilloscope_preamble(channel)
oscilloscope_stop()
oscilloscope_run()
oscilloscope_get_curve(channel)
oscilloscope_sensitivity(*channel)
oscilloscope_offset(*channel)
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
### [Magnetic field controllers](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/other_device_functions.md)
```python3
magnet_name()
magnet_field(*field)
magnet_command(command)
```
### [Balances](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/other_device_functions.md)
```python3
balance_weight()
```
### [Other](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/other_device_functions.md)
#### Solid-sate Relay RODOS-10N (ethernet)
```python3
turn_on(number)
turn_off(number)
```

## Screenshots
![](https://github.com/Anatoly1010/Atomize/blob/master/screenshot.png)
![](https://github.com/Anatoly1010/Atomize/blob/master/screenshot2.png)