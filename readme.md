# Atomize - Split your spectrometer apart!

A modular open source software for working with scientific devices and combining them into a spectrometer.<br/>
The general idea is close to [FSC2 software](http://users.physik.fu-berlin.de/~jtt/fsc2.phtml) developed by Jens Thomas Törring.<br/>
The liveplot library based on pyqtgraph is used as a main graphics library.<br/>
The [liveplot](https://github.com/PhilReinhold/liveplot) was developed by Phil Reinhold.

![](https://github.com/Anatoly1010/Atomize/blob/master/screenshot.png)

### Status: early in development


## Requirements
- [Python (tested with 3.8+)](https://www.python.org/)
- [Numpy](https://numpy.org/)
- [Scipy](https://www.scipy.org/)
- [PyQt5](http://www.riverbankcomputing.com/software/pyqt/download)
- [pyqtgraph](http://www.pyqtgraph.org)
- [PyVisapy](https://github.com/pyvisa/pyvisa-py)

## Basic Usage

1. Atomize

Install from the source directory:

	pip3 install .

run from the source directory:

	python3 atomize

or
	python3 atomize /path/to/experimental/script

2. [Liveplot](https://github.com/PhilReinhold/liveplot)  Author: Phil Reinhold

Install from the source directory:

	python3 setup.py install

Start the window

	python3 -m liveplot

To communicate with Liveplot inside a script it should be imported and initialized:
```python
from liveplot import LivePlotClient
plotter = LivePlotClient()
plotter.plotter_functions()
```

## Available general functions
### [message()](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/general_functions.md)
### [open_1D()](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/general_functions.md)
### [open_1D_dialog()](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/general_functions.md)
### [save_1D_dialog()](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/general_functions.md)
### [open_2D()](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/general_functions.md)
### [open_2D_dialog()](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/general_functions.md)
### [open_2D_appended()](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/general_functions.md)
### [open_2D_appended_dialog()](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/general_functions.md)
### [save_2D_dialog()](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/general_functions.md)
### [create_file_dialog()](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/general_functions.md)

## Available plotting functions
### [plot_xy()](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/plotting_functions.md)
### [append_y()](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/plotting_functions.md)
### [plot_z()](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/plotting_functions.md)
### [append_z()](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/plotting_functions.md)
### [label()](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/plotting_functions.md)
### [clear()](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/plotting_functions.md)

## Available function for devices

