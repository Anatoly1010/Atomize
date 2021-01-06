# Atomize - Split your spectrometer apart!

A modular open source software for working with scientific devices and combining them into a spectrometer.<br/>
The general idea is close to FSC2 software developed by Jens Thomas Törring, http://users.physik.fu-berlin.de/~jtt/fsc2.phtml.<br/>
The liveplot library based on pyqtgraph is used as a main graphics library. The liveplot was developed by Phil Reinhold, https://github.com/PhilReinhold/liveplot

### Status: early in development


## Requirements
- Python (tested with 3.8+)
- Numpy
- Scipy
- [PyQt5](http://www.riverbankcomputing.com/software/pyqt/download)
- [pyqtgraph](http://www.pyqtgraph.org)
- [PyVisapy](https://github.com/pyvisa/pyvisa-py)

## Basic Usage

1. Atomize

Clone from github repository

Install from the source directory:

	pip3 install .

run from the source directory:

	python3 atomize

2. Liveplot

Clone from github repository

Install from the source directory:

	python3 setup.py install

Start the window

	python3 -m liveplot

