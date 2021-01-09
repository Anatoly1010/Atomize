# List of available general functions

## Print a line in the main window
To call this function a corresponding module should be imported:
```python
import atomize.device_modules.config.messenger_socket_client as send
```
After that the function should be used as follows:
```python
send.message('A message to print')
```

## File handling
To call these functions one should create a corresponding class instance:
```python
import atomize.general_modules.csv_opener_saver as openfile
file_handler = openfile.csv()
```
After that the functions should be used as follows:
```python	
open_1D(path, header=0)
```
	Simple function to open a specified file with comma separeted values;

	path is a path to file;
	header is an integer to specify the number of columns in the file header;
	This argument is optional, default value is 0.

	Output: header as array of lists; data as numpy array
```python	
open_1D_dialog(self, directory='', fmt='', header=0)
```
	Function that returns a dialog to open a file with comma separeted values;
	
	directory is a path to preopened directory in the dialog window;
	header is an integer to specify the number of columns in the file header;
	fmt is the file extension to show; in string format ('csv');
	All these arguments are optional, default values are shown above;

	Output: header as array of lists; data as numpy array
```python
save_1D_dialog(data, directory='', fmt='', header='')
```
	Function that returns a dialog to save data as comma separeted values;
	
	data is numpy array of data to save;
	directory is a path to preopened directory in the dialog window;
	header is a string to prepend to a file as a header;
	fmt is the file extension to show; in string format ('csv');
	All these arguments are optional, default values are shown above;
	The values will be saved in '%.10f' format.
```python
open_2D(path, header=0)
```
	Simple function to open a specified file with 2D array of comma separeted values;

	path is a path to file;
	header is an integer to specify the number of columns in the file header;
	This argument is optional, default value is 0.

	Output: header as array of lists; data as 2D numpy array
```python
open_2D_dialog(directory='', fmt='', header=0)
```
	Function that returns a dialog to open a file with 2D array of comma separeted values;
	
	directory is a path to preopened directory in the dialog window;
	header is an integer to specify the number of columns in the file header;
	fmt is the file extension to show; in string format ('csv');
	All these arguments are optional, default values are shown above;

	Output: header as array of lists; data as 2D numpy array
```python
open_2D_appended(path, header=0, chunk_size=1)
```
	Function that returns a dialog to open a file with a single column array
	of values from 2D array;
	
	path is a path to file;
	header is an integer to specify the number of columns in the file header;
	chunk_size is Y axis size of the initial 2D array;

	Output: header as array of lists; data as 2D numpy array
```python
open_2D_appended_dialog(directory='', fmt='', header=0, chunk_size=1)
```
	Function that returns a dialog to open a file with a single column array
	of values from 2D array;
	
	directory is a path to preopened directory in the dialog window;
	header is an integer to specify the number of columns in the file header;
	fmt is the file extension to show; in string format ('csv');
	chunk_size is Y axis size of the initial 2D array;
	All these arguments are optional, default values are shown above;

	Output: header as array of lists; data as 2D numpy array
```python
save_2D_dialog(data, directory='', fmt='', header='')
```
	Function that returns a dialog to save a 2D array as comma separeted
	values;
	
	data is numpy 2D array of data to save;
	directory is a path to preopened directory in the dialog window;
	header is a string to prepend to a file as a header;
	fmt is the file extension to show; in string format ('csv');
	All these arguments are optional, default values are shown above;
	The values will be saved in '%.10f' format.
```python
create_file_dialog(directory='', fmt='')
```
	Function that returns a dialog to enter a name for a file;
	It can be used to manually saved your data inside the experimental
	script to specified file;

	directory is a path to preopened directory in the dialog window;
	fmt is the file extension to show; in string format ('csv');
	All these arguments are optional, default values are shown above;

For saving inside the script by create_file_dialog() a typical numpy
function should be used:
```python
np.savetxt(path_to_file, data_to_save, fmt='%.10f', delimiter=' ',
newline='n', header='field: %d' % i, footer='', comments='#', encoding=None)
```

# Minimal examples of using these functions inside the experimental script
## Open file
```python
from liveplot import LivePlotClient
import atomize.general_modules.csv_opener_saver as openfile

plotter = LivePlotClient()
file_handler =openfile.csv()

head, data = file_handler.open_2D_dialog(header=0):

plotter.plot_z('Plot Z Test', dat, start_step=((0,1),(0.3,0.001)), xname='Time', 
	xscale='s', yname='Magnetic Field', yscale='T', zname='Intensity', zscale='V')
```
## Save file in the end of the script
```python
import time
import numpy as np
from liveplot import LivePlotClient
import atomize.device_modules.config.messenger_socket_client as send
import atomize.general_modules.csv_opener_saver as openfile

plotter = LivePlotClient()
file_handler = openfile.csv()

data=[];
step=10;
i = 0;
send.message('Test of saving data')
path_to_file = file_handler.create_file_dialog(directory='', fmt='')

## 2D Experiment
while i <= 10:
	i=i+1;
	axis_x=np.arange(4000)
	ch_time=np.random.randint(250, 500, 1)
	zs = 1 + 100*np.exp(-axis_x/ch_time)+7*np.random.normal(size=(4000))
	data.append(zs)
	time.sleep(0.1)	

	plotter.plot_z('Plot Z Test', data, start_step=((0,1),(0.3,0.001)),
	xname='Time', xscale='s', yname='Magnetic Field', yscale='T', zname='Intensity',
	zscale='V')

f=open(path_to_file,'a')
np.savetxt(f, data, fmt='%.10f', delimiter=',', newline='n',
	header='field: %d' % i, footer='', comments='#', encoding=None)
f.close()
```

## Save file during the script
```python
import time
import numpy as np
from liveplot import LivePlotClient
import atomize.device_modules.config.messenger_socket_client as send
import atomize.general_modules.csv_opener_saver as openfile

plotter = LivePlotClient()
file_handler = openfile.csv()

data=[];
step=10;
i = 0;
send.message('Test of saving data')
path_to_file = file_handler.create_file_dialog(directory='', fmt='')

f = open(path_to_file,'a')
## 2D Experiment
while i <= 10:
	i=i+1;
	axis_x=np.arange(4000)
	ch_time=np.random.randint(250, 500, 1)
	zs = 1 + 100*np.exp(-axis_x/ch_time)+7*np.random.normal(size=(4000))
	data.append(zs)
	time.sleep(0.1)
	np.savetxt(f, zs, fmt='%.10f', delimiter=' ', newline='n', 
	header='field: %d' % i, footer='', comments='#', encoding=None)

	plotter.plot_z('Plot Z Test', data, start_step=((0,1),(0.3,0.001)),
	xname='Time', xscale='s', yname='Magnetic Field', yscale='T', zname='Intensity',
	zscale='V')

f.close()
```

