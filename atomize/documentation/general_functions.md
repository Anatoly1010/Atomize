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
- [open_1D(path, header = 0)](#open_1D)<br/>
- [open_1D_dialog(self, directory = '', header = 0)](#open_1D_dialog)<br/>
- [save_1D_dialog(data, directory = '', header = '')](#save_1D_dialog)<br/>
- [open_2D(path, header = 0)](#open_2D)<br/>
- [open_2D_dialog(directory = '', header = 0)](#open_2D_dialog)<br/>
- [open_2D_appended(path, header = 0, chunk_size = 1)](#open_2D_appended)<br/>
- [open_2D_appended_dialog(directory = '', header = 0, chunk_size = 1)](#open_2D_appended_dialog)<br/>
- [save_2D_dialog(data, directory = '', header = '')](#save_2D_dialog)<br/>
- [create_file_dialog(directory = '')](#create_file_dialog)<br/>

## Print a line in the main window
To call this function a corresponding general function module should be imported. After that
 the function should be used as follows:
```python
import atomize.general_modules.general_functions as general
general.message('A message to print','One more message', ...)
```
## Send a message via Telegram bot
To call this function Telegram bot token and message chat ID should be specified in the configuration file (/atomize/config.ini). General function module should be imported. After that the function should be used as follows:
```python
import atomize.general_modules.general_functions as general
general.bot_message('A message to send','One more message', ...)
```
## Wait for the specified amount of time
To call this function a corresponding general function module should be imported. Function has
one argument, which is a string of number and scaling factor (ks, s, ms, us):
```python
import atomize.general_modules.general_functions as general
general.wait('10 ms')
```
## Infinite loop
Since all experimental scripts are tested before tactually interacting with devices, a standard Python infinite loop like while True will stuck in test mode. Instead, use the special function general.to_infinity(). This function imitates a standard infinite loop for which the first 50 loops will be checked in a test run.
```python
import atomize.general_modules.general_functions as general

for i in general.to_infinity():
	# DO SOMETHING
    general.message(i)
```
It is also possible to interrupt an infinite loop under certain conditions:
```python
for i in general.to_infinity():
    general.message(i)
    if i > 10:
        break
```
## File handling
To open or save raw experimental data one can use a special module based on Tkinter.
Alternatively, it is possible to use the CSV Exporter embedded into Pyqtgraph for saving 1D data
and a special option in Liveplot (right click -> Save Data Action) for saving 2D data as
comma separated two dimensional numpy array.
To call functions from Tkinter module one should create a corresponding class instance:
```python
import atomize.general_modules.csv_opener_saver_tk_kinter as openfile
file_handler = openfile.Saver_Opener()
```
After importing the functions should be used as follows:
### open_1D()
```python	
open_1D(path, header = 0)
```
	Simple function to open a specified file with comma separeted values;

	path is a path to file;
	header is an integer to specify the number of columns in the file header;
	This argument is optional, default value is 0.

	Output: header as array of lists; data as numpy array
### open_1D_dialog()
```python	
open_1D_dialog(self, directory = '', header = 0)
```
	Function that returns a dialog to open a file with comma separeted values;
	
	directory is a path to preopened directory in the dialog window;
	header is an integer to specify the number of columns in the file header;
	All these arguments are optional, default values are shown above;

	Output: header as array of lists; data as numpy array
### save_1D_dialog()
```python
save_1D_dialog(data, directory = '', header = '')
```
	Function that returns a dialog to save data as comma separeted values;
	
	data is numpy array of data to save;
	directory is a path to preopened directory in the dialog window;
	header is a string to prepend to a file as a header;
	All these arguments are optional, default values are shown above;
	The values will be saved in '%.10f' format.
### open_2D()
```python
open_2D(path, header = 0)
```
	Simple function to open a specified file with 2D array of comma separeted values;

	path is a path to file;
	header is an integer to specify the number of columns in the file header;
	This argument is optional, default value is 0.

	Output: header as array of lists; data as 2D numpy array
### open_2D_dialog()
```python
open_2D_dialog(directory = '', header = 0)
```
	Function that returns a dialog to open a file with 2D array of comma separeted values;
	
	directory is a path to preopened directory in the dialog window;
	header is an integer to specify the number of columns in the file header;
	All these arguments are optional, default values are shown above;

	Output: header as array of lists; data as 2D numpy array
### open_2D_appended()
```python
open_2D_appended(path, header = 0, chunk_size = 1)
```
	Function that returns a dialog to open a file with a single column array
	of values from 2D array;
	
	path is a path to file;
	header is an integer to specify the number of columns in the file header;
	chunk_size is Y axis size of the initial 2D array;

	Output: header as array of lists; data as 2D numpy array
### open_2D_appended_dialog()
```python
open_2D_appended_dialog(directory = '', header = 0, chunk_size = 1)
```
	Function that returns a dialog to open a file with a single column array
	of values from 2D array;
	
	directory is a path to preopened directory in the dialog window;
	header is an integer to specify the number of columns in the file header;
	chunk_size is Y axis size of the initial 2D array;
	All these arguments are optional, default values are shown above;

	Output: header as array of lists; data as 2D numpy array
### save_2D_dialog()
```python
save_2D_dialog(data, directory = '', header = '')
```
	Function that returns a dialog to save a 2D array as comma separeted
	values;
	
	data is numpy 2D array of data to save;
	directory is a path to preopened directory in the dialog window;
	header is a string to prepend to a file as a header;
	All these arguments are optional, default values are shown above;
	The values will be saved in '%.10f' format.
### create_file_dialog()
```python
create_file_dialog(directory = '')
```
	Function that returns a dialog to enter a name for a file;
	It can be used to manually saved your data inside the experimental
	script to specified file;

	directory is a path to preopened directory in the dialog window;
	The argument is optional, default value is shown above;

For saving inside the script by [create_file_dialog()](#create_file_dialog) a typical numpy
function should be used:
```python
np.savetxt(path_to_file, data_to_save, fmt = '%.10f', delimiter = ' ',
newline = 'n', header = 'field: %d' % i, footer = '', comments = '#',
encoding = None)
```

# Minimal examples of using these functions inside the experimental script
## Open file
```python
import atomize.general_modules.general_functions as general
import atomize.general_modules.csv_opener_saver_tk_kinter as openfile

file_handler = openfile.Saver_Opener()

head, data = file_handler.open_2D_dialog(header = 0):

general.plot_2d('Plot Z Test', dat, start_step = ((0, 1), (0.3, 0.001)), xname = 'Time', 
	xscale = 's', yname = 'Magnetic Field', yscale = 'T', zname = 'Intensity', zscale = 'V')
```
## Save file in the end of the script
```python
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.general_modules.csv_opener_saver_tk_kinter as openfile

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
np.savetxt(f, data, fmt = '%.10f', delimiter = ',', newline = 'n',
	header = 'field: %d' % i, footer = '', comments = '#', encoding = None)
f.close()
```

## Save file during the script
```python
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.general_modules.csv_opener_saver_tk_kinter as openfile

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
	np.savetxt(f, zs, fmt = '%.10f', delimiter = ' ', newline = 'n', 
	header = 'field: %d' % i, footer = '', comments = '#', encoding = None)

	general.plot_2d('Plot Z Test', data, start_step = ((0, 1), (0.3, 0.001)),
	xname = 'Time', xscale = 's', yname = 'Magnetic Field', yscale = 'T', zname = 'Intensity',
	zscale = 'V')

f.close()
```


