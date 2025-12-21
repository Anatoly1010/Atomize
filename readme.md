# Atomize - Split your spectrometer apart!
![](https://github.com/Anatoly1010/Atomize/blob/master/screenshots/logoAtomize.png)<br/>
Atomize is a modular software designed to control a wide range of scientific and industrial instruments, integrate them into a unified multifunctional setup, and automate routine experimental work.<br/>
The general idea is close to [FSC2 software](http://users.physik.fu-berlin.de/~jtt/fsc2.phtml) developed by Jens Thomas Törring.<br/>
Remote control of spectrometers is usually carried out using home-written programs, which are often restricted to doing a certain experiment with a specific set of devices. In contrast, the programs like [FSC2](http://users.physik.fu-berlin.de/~jtt/fsc2.phtml) and [Atomize](https://github.com/Anatoly1010/Atomize) are much more flexible, since they are based on a modular approach for communication with device and scripting language (EDL in FSC2; Python in Atomize) for data measuring.

Atomize[^1] uses [liveplot library](https://github.com/PhilReinhold/liveplot) based on pyqtgraph as a main graphics library. [Liveplot](https://github.com/PhilReinhold/liveplot) was originally developed by Phil Reinhold. Since then, several improvements have been made to use it in Atomize, and it has been directly embedded into Atomize.

[Python Programming Language](https://www.python.org/) is used inside experimental scripts, which opens up almost unlimited possibilities for raw experimental data treatment. In addition, with PyQt, one can create experimental scripts with a simple graphical interface, allowing users not familiar with Python to use it. Several examples of scripts (with dummy data) are provided in the /atomize/tests/ directory, including a GUI script with extended comments inside. Also a variant of the Atomize with GUI Control Window extension can be found [here.](https://github.com/Anatoly1010/Atomize_NIOCH)<br/>

Currently there are more than 200 device specific and general functions available for over 27 different devices, including 6 series of devices. If you would like to write a module for the device that is not currently available, please, read this short [instruction.](https://anatoly1010.github.io/atomize_docs/pages/writing_modules.html)

## Documentation and Available Instruments

[Detailed documentation](https://anatoly1010.github.io/atomize_docs/functions/)<br/>
[Available instruments](https://anatoly1010.github.io/atomize_docs/pages/instruments.html)

## Status

At the moment, Atomize has been tested and is currently used for controlling several EPR spectrometers using a broad range of different devices. The program has been tested on Ubuntu 18.04 LTS, 20.04 LTS, and 22.04 LTS.

## Requirements
- [Python >= 3.9](https://www.python.org/)
- [Numpy >= 1.25](https://numpy.org/)
- [PyQt6 >= 6.2](http://www.riverbankcomputing.com/software/pyqt/download)
- [pyqtgraph >= 0.12](http://www.pyqtgraph.org)
- [PyVisa >= 1.11](https://pyvisa.readthedocs.io/en/latest/)
- [PyVisa-py >= 0.5](https://github.com/pyvisa/pyvisa-py)
- [hatchling >= 1.9 ](https://pypi.org/project/hatchling/)<br/>
Optional:
- [PySerial;](https://pypi.org/project/pyserial/) for serial instruments
- [Minimalmodbus;](https://minimalmodbus.readthedocs.io/en/stable/index.html) for Modbus instruments
- [SciPy;](https://scipy.org/) for mathematical modules
- [GPIB driver;](https://linux-gpib.sourceforge.io/) for GPIB devices
- [Telegram bot API;](https://github.com/eternnoir/pyTelegramBotAPI) for Telegram bot messages
- [SpinAPI;](http://www.spincore.com/support/spinapi/) for Pulse Blaster ESR 500 Pro
- [Spcm driver;](https://spectrum-instrumentation.com/en/m4i4450-x8) for Spectrum M4I 6631 X8; M4I 4450 X8

## Usage

### 1. Installation

Install from PyPi:

	pip3 install atomize-py

Run GUI from terminal:

	atomize

### 2. General Configuration

In the terminal where you launched Atomize, the paths to the configuration files and some other details are displayed as follows:
```yml
SYSTEM: Linux
DATA DIRECTORY: /path/to/experimental/data/to/open/
SCRIPTS DIRECTORY: /path/to/atomize/scripts/
MAIN CONFIG DIRECTORY: ~/.config/atomize-py/
DEVICE CONFIG DIRECTORY: ~/.config/atomize-py/device_config/
EDITOR: text editor used for editing scripts
```
The "MAIN CONFIG DIRECTORY" contains a general configuration file with the name main_config.ini. It should be changed at will according to the description below:
```yml
[DEFAULT]
# configure the text editor that will opened when the Edit  button is pressed.
# "EDITOR":
editor = subl # Linux
editorW = /path/to/text_editor/on/Windows/  # Windows

# configure the directory that will opened when Open 1D Data or Open 2D Data
# feature is used in the Liveplot tab. 
# "DATA DIRECTORY":
open_dir = /path/to/experimental/data/to/open/

# configure the directory that will be opened when the Open Script button is pressed:
# "SCRIPTS DIRECTORY":
script_dir = /path/to/atomize/scripts/

# configure Telegram bot
telegram_bot_token = 
message_id = 
```

### 3. Using Instrument Modules

To communicate with a device one should:
1) Modify the config file located in "DEVICE CONFIG DIRECTORY" of the desired device accordingly. Choose the desired protocol (rs-232, gpib, ethernet, etc.) and correct the settings of the specified protocol in accordance with device settings. A little bit more detailed information about protocol settings can be found [here.](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/protocol_settings.md)
2) Import the module or modules in your script and initialize the appropriate class. A class always
has the same name as the module file. Initialization connect the desired device, if the settings are correct.
```python
# importing of the instruments
import atomize.device_modules.Keysight_3000_Xseries as keys
import atomize.device_modules.Lakeshore331 as tc

# initialization of the instruments
dsox3034t = keys.Keysight_3000_Xseries()
lakeshore331 = tc.Lakeshore331()

# using the instruments
name_oscilloscope = dsox3034t.oscilloscope_name()
temperature = lakeshore331.tc_temperature('CH A')
```
The same idea is valid for plotting and file handling modules.
```python
# importing of the general purpose modules
import atomize.general_modules.general_functions as general
import atomize.general_modules.csv_opener_saver_tk_kinter as openfile

# initialization
file_handler = openfile.Saver_Opener()
head, data = file_handler.open_1D_dialog(header = 0)

# using
general.plot_1d('1D Plot', data[0], data[1], label = 'test_data', yname = 'Y axis', yscale = 'V')
```

### 4. Experimental Scripts

Python is used to write an experimental script. Examples (with dummy data) can be found in the
"SCRIPTS DIRECTORY".

## Screenshots
![](https://github.com/Anatoly1010/Atomize/blob/master/screenshots/screenshot.png)
![](https://github.com/Anatoly1010/Atomize/blob/master/screenshots/screenshot2.png)
![](https://github.com/Anatoly1010/Atomize/blob/master/screenshots/screenshot3.png)

[^1]: Atomize = A + TOM + ize; A stands for Anatoly, main developer; TOMo stands for the International TOMography center, our organization