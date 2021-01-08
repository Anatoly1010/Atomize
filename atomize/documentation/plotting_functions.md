# List of available plotting functions

Plotting of raw experimental data is available via [Liveplot](https://github.com/PhilReinhold/liveplot) library modified according to the aims of the project.
The general idea of the Liveplot is a possibitily to see your data as it comes in to your script, with minimal effort using an appropriate shell to cover verbose syntax. 

The [Liveplot](https://github.com/PhilReinhold/liveplot) provides several possibilities for plotting 1D and 2D data. For raw experimental data plotting mainly four of them are applicable. An additional customizability has been added to these functions in comparison with the original Liveplot library.<br/>
To call these functions one should create a Liveplot instance:
```python
from liveplot import LivePlotClient
plotter = LivePlotClient()
```
After that the functiins should be used as follows:

## 1D plotting
```python	
plot_xy('name', Xdata, Ydata, label='label', xname='NameXaxis', 
xscale='XaxisDimension', yname='NameYaxis', yscale='YaxisDimension', scatter='False')
```
	Xdata, Ydata are numpy arrays;
	name, label are strings;
	scatter is 'False' (default) or 'True'. Enables scatter plot;
	other arguments are optional and used for automatic scaling (i.e. V to mV, etc.)
	Please, note that it is impossible to redraw a line with scatters if they have the same name.

	Currently, up to five curves can be plotted under the same name and different label.
```python	
append_y('name', value, start_step=(x[0], x[1]-x[0]), label='label', xname='NameXaxis',
xscale='XaxisDimension', yname='NameYaxis', yscale='YaxisDimension')
```
	value is a number to append;
	name, label are strings; 
	start_step is a list of starting point and step of the X axis;
	other arguments are optional

## 2D plotting
```python		
plot_z('name', data, start_step=((Xstart, Xstep), (Ystart, Ystep)), xname='NameXaxis',
xscale='XaxisDimension', yname='NameYaxis Field', yscale='YaxisDimension', zname='NameZaxis',
zscale='ZaxisDimension')
```
	data is a multidimensional numpy array; example = [[1,1,1,..],[2,2,2,..],[3,3,3,..],..];
	name, label are strings; 
	start_step is a list of starting points and steps. Since the plotting procedure looks like an append of data
	horizontally the first list is typically (0, 1), the second is (Ystart, Ystep);
	other arguments are optional
```python
append_z('name', data, start_step=((Xstart, Xstep), (Ystart, Ystep)), xname='NameXaxis',
xscale='XaxisDimension', yname='NameYaxis Field', yscale='YaxisDimension', zname='NameZaxis',
zscale='ZaxisDimension')
```
	data is a numpy 1D array to append; example = [1,1,1,..];
	name, label are strings; 
	start_step is a list in the format ((Xstart, Xstep), (Ystart, Ystep)). Since the plotting procedure looks
	like an append of data horizontally the first list is typically (0, 1), the second is (Ystart, Ystep);
	other arguments are optional

## Dynamic labling
```python
label('label', 'text: %d' % DynamicValue)
```
	label is a string;
	text is a string that will be shown on the label;
	DynamicValue is a number that will change dynamically

## Clearing
```python
clear()
```
# Minimal examples of using these functions inside the experimental script

## 1D plotting
```python
from liveplot import LivePlotClient
import numpy as np
import time

plotter = LivePlotClient()

xs=np.array([]);
ys=np.array([])

for i in range(40):
	xs = np.append(xs, i);
	ys = np.append(ys, np.random.random_integers(0,10));
	plotter.plot_xy('1D test plot', xs, ys, label='random data')
	time.sleep(0.2)
```
## 2D plotting
```python
from liveplot import LivePlotClient
import numpy as np
import time

plotter = LivePlotClient()

data=[];
step=10;
i = 0;

while i <= 20:
	i=i+1;

	axis_x=np.arange(4000)
	ch_time=np.random.randint(250, 500, 1)
	zs = 1 + 100*np.exp(-axis_x/ch_time)+7*np.random.normal(size=(4000))

	data.append(zs)

	time.sleep(0.1)

	plotter.append_z('2D test plot', data[i-1], start_step=((0,1),(0.3, 0.001)),
	xname='Time', xscale='s', yname='Magnetic Field', yscale='T', zname='Intensity',
	zscale='V')
	plotter.label('2D test plot', 'step: %d' % i)
```