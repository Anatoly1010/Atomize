# Atomize - Split your spectrometer apart!
![](https://github.com/Anatoly1010/Atomize/blob/master/screenshots/logoAtomize.png)<br/>
A modular open source software for working with scientific devices and combining them into spectrometer.<br/>
The general idea is close to [FSC2 software](http://users.physik.fu-berlin.de/~jtt/fsc2.phtml) developed by Jens Thomas Törring.<br/>
Remote control of spectrometers is usually carried out using home-written programs, which are often restricted to doing a certain experiment with a specific set of devices. In contrast, the programs like [FSC2](http://users.physik.fu-berlin.de/~jtt/fsc2.phtml) and [Atomize](https://github.com/Anatoly1010/Atomize) are much more flexible, since they are based on a modular approach for communication with device and scripting language (EDL in FSC2; Python in Atomize) for data measuring.

Atomize uses [liveplot library](https://github.com/PhilReinhold/liveplot) based on pyqtgraph as a main graphics library. [Liveplot](https://github.com/PhilReinhold/liveplot) was originally developed by Phil Reinhold. Since several minor improvements have been made to use it in Atomize.

[Python Programming Language](https://www.python.org/) is used inside experimental scripts, which opens up almost unlimited possibilities for raw experimental data treatment. In addition, with PyQt, one can create experimental scripts with a simple graphical interface, allowing users not familiar with Python to use it. Several examples of scripts (with dummy data) are provided in /atomize/tests/ directory, including a GUI script with extended comments inside. Also a variant of the Atomize with GUI Control Window extension can be found [here.](https://github.com/Anatoly1010/Atomize_NIOCH)<br/>

Currently there are more than 200 device specific and general functions available for over 27 different devices, including 6 series of devices. If you would like to write a module for the device that is not currently available, please, read this short [instruction.](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/writing_modules.md)

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
    - [Magnet Power Supplies](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/magnet_power_supply_functions.md)<br/>
    - [Delay Generators](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/delay_generator_functions.md)<br/>
    - [Moisture Meters](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/moisture_meter_functions.md)<br/>
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
	- Tektronix 5 Series MSO (Ethernet); Tested 12/2023

#### [Digitizers](#digitizers-1)
	- Spectrum M4I 4450 X8; Tested 08/2021
	- Spectrum M4I 2211 X8; Tested 01/2021
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

	- Pulse  Programmer Micran based on [Insys FMC126P](https://www.insys.ru/fmc/fmc126p); Tested 12/2023

#### [Frequency Counters](#frequency-counters-1)
	- Agilent Frequency Counter (GPIB, RS-232)
	53181A; 53131A/132A; Tested 02/2021
	5343A; GPIB, Tested 02/2023
	- Keysight Frequency Counter (GPIB, RS-232, Ethernet)
	53230A/220A; Untested

#### [Magnetic Field Controllers](#magnetic-field-controllers-1)
	- Bruker BH15 (GPIB); Tested 01/2021
	- Bruker ER032M (GPIB); Available via BH15 module
	- Bruker ER031M (RS-232 using arduino emulated keyboard); Tested 01/2021
	- [Homemade](https://patents.google.com/patent/RU2799103C1/en?oq=RU2799103C1) magnetic field controller (RS-232); Tested 04/2023

#### [Microwave Bridge Controllers](#microwave-bridge-controllers-1)
	- Micran X-band MW Bridge (TCP/IP Socket); Tested 06/2021
	- Micran X-band MW Bridge v2 (TCP/IP Socket); Tested 12/2022
	- Micran Q-band MW Bridge; Tested 12/2023

#### [Gaussmeters](#gaussmeters-1)
	- Lakeshore 455 DSP (RS-232); Tested 01/2021

#### [Power Supplies](#power-supplies-1)
	- Rigol DP800 Series (RS-232, Ethernet); Tested 01/2021
	- Stanford Research DC205 (RS-232); Untested
    - Stanford Research PS300 High Voltage Series (RS-232, GPIB); Untested

#### [Magnet Power Supplies](#magnet-power-supplies-1)
	- Cryomagnetics 4G (Ethernet); Tested 11/2023

#### [Delay Generators](#delay-generators-1)
    - Stanford Research DG535 (GPIB); Untested

#### [Moisture Meters](#moisture-meters-1)
	- IVG-1/1 (RS-485); Tested 02/2023

#### [Balance](#balances-1)
	- CPWplus 150 (RS-232); Tested 01/2021

#### [Other](#other-1)
	- RODOS-10N Solid-State Relay (Ethernet); Tested 01/2021
    - Owen-MK110-220.4DN.4R Discrete IO Module (RS-485); Tested 04/2021
    - Cryomagnetics LM-510 Liquid Cryogen Monitor (TCP/IP Socket); Tested 07/2022
    - Cryomech CPA2896, CPA1110 Digital Panels (RS-485); Tested 07/2022

## [Available general functions](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/general_functions.md)

## [Available plotting functions](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/plotting_functions.md)

## Available functions for devices
### [Temperature controllers](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/temperature_controller_functions.md)
### [Oscilloscopes](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/oscilloscope_functions.md)
### [Digitizers](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/digitizer_functions.md)
### [Oscilloscope wave generators](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/oscilloscope_wave_generator_functions.md)
### [Arbitrary wave generators](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/awg_functions.md)
### [Pulse programmers](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/pulse_programmers_functions.md)
### [Lock-in amplifiers](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/lock_in_amplifier_functions.md)
### [Frequency counters](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/frequency_counter_functions.md)
### [Magnetic field controllers](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/magnet_functions.md)
### [Microwave bridge controllers](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/microwave_bridge_functions.md)
### [Gaussmeters](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/gaussmeter_functions.md)
### [Power supplies](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/power_supply_functions.md)
### [Magnet power supplies](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/magnet_power_supply_functions.md)
### [Delay generators](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/delay_generator_functions.md)
### [Moisture meters](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/moisture_meter_functions.md)
### [Balance](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/other_device_functions.md)
### [Other](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/other_device_functions.md)

## Screenshots
![](https://github.com/Anatoly1010/Atomize/blob/master/screenshots/screenshot.png)
![](https://github.com/Anatoly1010/Atomize/blob/master/screenshots/screenshot2.png)
![](https://github.com/Anatoly1010/Atomize/blob/master/screenshots/screenshot3.png)