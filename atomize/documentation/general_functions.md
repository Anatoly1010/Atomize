# List of available general functions

## Contents
- [Available functions](#available-functions)<br/>
- [Print function](#print-a-line-in-the-main-window)<br/>
- [Wait function](#wait-for-the-specified-amount-of-time)<br/>
- [Infinite loop](#infinite-loop)<br/>
- [File handling functions](#file-handling)<br/>
- [Example 1](#open-file)<br/>
- [Example 2](#save-file-in-the-end-of-the-script)<br/>
- [Example 3](#save-file-during-the-script)<br/>

## Available functions
- [message('string')](#print-a-line-in-the-main-window)<br/>
- [bot_message('message')](#send-a-message-via-telegram-bot)<br/>
- [wait('10 ms')](#wait-for-the-specified-amount-of-time)<br/>
- [to_infinity()](#infinite-loop)<br/>
- [const_shift(x, shift)](#constant-shift)<br/>
- [open_1D(path, header = 0)](#open_1D)<br/>
- [open_1D_dialog(self, directory = '', header = 0)](#open_1D_dialog)<br/>
- [save_1D_dialog(data, directory = '', header = '')](#save_1D_dialog)<br/>
- [open_2D(path, header = 0)](#open_2D)<br/>
- [open_2D_dialog(directory = '', header = 0)](#open_2D_dialog)<br/>
- [open_2D_appended(path, header = 0, chunk_size = 1)](#open_2D_appended)<br/>
- [open_2D_appended_dialog(directory = '', header = 0, chunk_size = 1)](#open_2D_appended_dialog)<br/>
- [save_2D_dialog(data, directory = '', header = '')](#save_2D_dialog)<br/>
- [create_file_dialog(directory = '')](#create_file_dialog)<br/>
- [create_file_parameters(add_name, directory = '')](#create_file_parameters)<br/>
- [save_header(filename, header = '', mode = 'w')](#save_header)<br/>
- [save_data(filename, data, header = '', mode = 'w')](#save_data)<br/>

## Print a line in the main window
To call this function a corresponding general function module should be imported. After that
 the function should be used as follows:
```python3
import atomize.general_modules.general_functions as general
general.message('A message to print', 'One more message', ...)
```
## Send a message via Telegram bot
To call this function Telegram bot token and message chat ID should be specified in the configuration file (/atomize/config.ini). General function module should be imported. After that the function should be used as follows:
```python3
import atomize.general_modules.general_functions as general
general.bot_message('A message to send', 'One more message', ...)
```
## Wait for the specified amount of time
To call this function a corresponding general function module should be imported. Function has
one argument, which is a string of number and scaling factor (ks, s, ms, us):
```python3
import atomize.general_modules.general_functions as general
general.wait('10 ms')
```
## Infinite loop
Since all experimental scripts are tested before actually interacting with devices, a standard Python infinite loop like while True will stuck in the test mode. Instead, one can use a special function general.to_infinity(). This function imitates a standard infinite loop for which the first 50 loops will be checked in the test run.
```python3
import atomize.general_modules.general_functions as general

for i in general.to_infinity():
	# DO SOMETHING
    general.message(i)
```
It is also possible to interrupt an infinite loop under certain conditions:
```python3
for i in general.to_infinity():
    general.message(i)
    if i > 10:
        break
```
## Repeating scans in an experimental script
In addition to an infinite loop, a standard Python loop with repeating scans will also waste extra time in the test mode. To tackle it, one can use a special function general.scans( number_of_scans ). This function imitates a standard loop for which only the first loop will be checked in the test run. Please, note that in this case there is no need to declare and iterate a loop iterator, i.e. See the example below for more details.
```python3
import atomize.general_modules.general_functions as general

# Run 10 scans
for i in general.scans( 10 ):
	# DO MEASUREMENTS
    general.message(i)
    # the output will be from 1 to 10
```
## Constant shift
To match the timescales of the DAC and the pulse generator a function general.сonst_shift( str(initial_position) + ['ns', 'ms', 'us'], shift_in_ns ) can be used as follows:
```python3
import atomize.general_modules.general_functions as general
PULSE_AWG_2_START = '250 ns'
# SHIFT THE PULSE POSITION FROM 494 NS TO 744 NS
PULSE_2_START = general.const_shift(PULSE_AWG_2_START, 494)
```
## File handling
To open or save raw experimental data one can use a special module based on Tkinter / PyQt.
Alternatively, it is possible to use the CSV Exporter embedded into Pyqtgraph for saving 1D data and a special option in Liveplot (right click -> Save Data Action) for saving 2D data as comma separated two dimensional numpy array. To call functions from Tkinter module one should create a corresponding class instance:
```python3
import atomize.general_modules.csv_opener_saver_tk_kinter as openfile #Tkinter
import atomize.general_modules.csv_opener_saver as openfile #PyQt
file_handler = openfile.Saver_Opener()
```
After importing the functions should be used as follows:
### open_1D()
```python3
open_1D(path, header = 0)
```
Simple function to open a specified file with comma separated values;
path is a path to file;<br/>
header is an integer to specify the number of columns in the file header. This argument is optional, default value is 0.<br/>
Output: header as array of lists; data as numpy array.<br/>
### open_1D_dialog()
```python3
open_1D_dialog(self, directory = '', header = 0)
```
This function returns a dialog to open a file with comma separated values;<br/>
directory is a path to preopened directory in the dialog window;<br/>
header is an integer to specify the number of columns in the file header;<br/>
All these arguments are optional, default values are shown above;<br/>
Output: header as array of lists; data as numpy array.<br/>
### save_1D_dialog()
```python3
save_1D_dialog(data, directory = '', header = '')
```
This function returns a dialog to save data as comma separated values;<br/>
data is numpy array of data to save;<br/>
directory is a path to preopened directory in the dialog window;<br/>
header is a string to prepend to a file as a header;<br/>
All these arguments are optional, default values are shown above;<br/>
The values will be saved in '%.4e' format.<br/>
### open_2D()
```python3
open_2D(path, header = 0)
```
Simple function to open a specified file with 2D array of comma separated values;<br/>
path is a path to file;<br/>
header is an integer to specify the number of columns in the file header. This argument is optional, default value is 0.<br/>
Output: header as array of lists; data as 2D numpy array.<br/>
### open_2D_dialog()
```python3
open_2D_dialog(directory = '', header = 0)
```
This function returns a dialog to open a file with 2D array of comma separated values;<br/>
directory is a path to preopened directory in the dialog window;<br/>
header is an integer to specify the number of columns in the file header;<br/>
All these arguments are optional, default values are shown above;<br/>
Output: header as array of lists; data as 2D numpy array.<br/>
### open_2D_appended()
```python3
open_2D_appended(path, header = 0, chunk_size = 1)
```
This function returns a dialog to open a file with a single column array
of values from 2D array;<br/>
path is a path to file;<br/>
header is an integer to specify the number of columns in the file header;
chunk_size is Y axis size of the initial 2D array;<br/>
Output: header as array of lists; data as 2D numpy array.<br/>
### open_2D_appended_dialog()
```python3
open_2D_appended_dialog(directory = '', header = 0, chunk_size = 1)
```
This function returns a dialog to open a file with a single column array
of values from 2D array;<br/>
directory is a path to preopened directory in the dialog window;<br/>
header is an integer to specify the number of columns in the file header;<br/>
chunk_size is Y axis size of the initial 2D array;<br/>
All these arguments are optional, default values are shown above;<br/>
Output: header as array of lists; data as 2D numpy array.<br/>
### save_2D_dialog()
```python3
save_2D_dialog(data, directory = '', header = '')
```
This function returns a dialog to save a 2D array as comma separated
values;<br/>
data is numpy 2D array of data to save;<br/>
directory is a path to preopened directory in the dialog window;<br/>
header is a string to prepend to a file as a header;<br/>
All these arguments are optional, default values are shown above;<br/>
The values will be saved in '%.4e' format.<br/>
### create_file_dialog()
```python3
create_file_dialog(directory = '')
```
Function that returns a dialog to enter a name for a file;<br/>
It can be used to manually saved your data inside the experimental
script to specified file;<br/>
directory is a path to preopened directory in the dialog window. This argument is optional, default value is shown above.<br/>
### create_file_parameters()
```python3
create_file_parameters(add_name, directory = '')
```
This function has the full functionality of the [create_file_dialog()](#create_file_dialog) function, but also returns a second file for saving parameters / header;<br/>
add_name argument is a string that will be added to the second file instead of the first file '.csv' extension. For instance, create_file_parameters('.param') will create a second file with .param extension.<br/>
directory is a path to preopened directory in the dialog window. This argument is optional, default value is shown above.<br/>
### save_header()
```python3
save_header(filename, header = '', mode = 'w')
```
This function save the string given by argument header to the file with the path 'filename'. Argument mode allows choosing whether the file will be rewritten (mode = 'w') or the data will be appended to the end of the file (mode = 'a').
### save_data()
```python3
save_data(filename, data, header = '', mode = 'w')
```
This function save the numpy array given by the argument data and the string given by argument header to the file with the path 'filename'. Argument mode allows choosing whether the file will be rewritten (mode = 'w') or the data will be appended to the end of the file (mode = 'a'). This function works for 1D, 2D, and 3D data. In case of 3D (an array of 2D arrays) data, a separate file will be created for each 2D array with the additional '_i' string in the filename. The standard combination of function to save the experimental data together with a header is the following:
```python3
file_data, file_param = file_handler.create_file_parameters('.param')
header = 'Test Header'
file_handler.save_header(file_param, header = header, mode = 'w')
# Acquiring experimental data
file_handler.save_data(file_data, data, header = header, mode = 'w')
```
### Standard numpy savetxt() function
For saving inside the script by [create_file_dialog()](#create_file_dialog) a standard numpy function should be used:
```python3
np.savetxt(path_to_file, data_to_save, fmt = '%.4e', delimiter = ' ',
newline = 'n', header = 'field: %d' % i, footer = '', comments = '#',
encoding = None)
```

# Minimal examples of using these functions inside the experimental script
## Open file
```python3
import atomize.general_modules.general_functions as general
import atomize.general_modules.csv_opener_saver_tk_kinter as openfile

file_handler = openfile.Saver_Opener()

head, data = file_handler.open_2D_dialog(header = 0):

general.plot_2d('Plot Z Test', dat, start_step = ((0, 1), (0.3, 0.001)), xname = 'Time', 
	xscale = 's', yname = 'Magnetic Field', yscale = 'T', zname = 'Intensity', zscale = 'V')
```
## Save file in the end of the script
```python3
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.general_modules.csv_opener_saver as openfile

file_handler = openfile.Saver_Opener()

data = [];
step = 10;
i = 0;
general.message('Test of saving data')
path_to_file = file_handler.create_file_dialog(directory = '')

## 2D Experiment
while i <= 10:
	i = i + 1;
	axis_x = np.arange(4000)
	ch_time = np.random.randint(250, 500, 1)
	zs = 1 + 100*np.exp(-axis_x/ch_time) + 7*np.random.normal(size = (4000))
	data.append(zs)
	general.wait('100 ms')	

	general.plot_2d('Plot Z Test', data, start_step = ((0, 1), (0.3, 0.001)),
	xname = 'Time', xscale = 's', yname = 'Magnetic Field', yscale = 'T', zname = 'Intensity',
	zscale = 'V')

f = open(path_to_file, 'a')
np.savetxt(f, data, fmt = '%.4e', delimiter = ',', newline = 'n',
	header = 'field: %d' % i, footer = '', comments = '#', encoding = None)
f.close()
```

## Save file during the script
```python3
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.general_modules.csv_opener_saver as openfile

file_handler = openfile.Saver_Opener()

data = [];
step = 10;
i = 0;
general.message('Test of saving data')
path_to_file = file_handler.create_file_dialog(directory = '', fmt = '')

f = open(path_to_file, 'a')
## 2D Experiment
while i <= 10:
	i = i + 1;
	axis_x = np.arange(4000)
	ch_time = np.random.randint(250, 500, 1)
	zs = 1 + 100*np.exp(-axis_x/ch_time) + 7*np.random.normal(size=(4000))
	data.append(zs)
	general.wait('100 ms')
	np.savetxt(f, zs, fmt = '%.4e', delimiter = ' ', newline = 'n', 
	header = 'field: %d' % i, footer = '', comments = '#', encoding = None)

	general.plot_2d('Plot Z Test', data, start_step = ((0, 1), (0.3, 0.001)),
	xname = 'Time', xscale = 's', yname = 'Magnetic Field', yscale = 'T', zname = 'Intensity',
	zscale = 'V')

f.close()
```


