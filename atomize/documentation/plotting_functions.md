---
title: Usage
nav_order: 10
layout: page
permlink: /functions/plotting_functions/usage/
parent: Plotting Funtions
grand_parent: Documentation
---
<br/>
To call plotting functions one should import general function module inside a script:

```python
import atomize.general_modules.general_functions as general
```

---

## 1D plotting
```python	
plot_1d('name', Xdata, Ydata, label = 'label', xname = 'NameXaxis', 
		xscale = 'XaxisDimension', yname = 'NameYaxis', yscale = 'YaxisDimension', 
		scatter = 'False', timeaxis = 'False', vline = 'False', 
		pr = 'None', text = '')
```

```
Xdata, Ydata are numpy arrays or python lists of data;
name is a string of the plot name;
label is a string of the curve name;
text is a label of the plot (for multithreading only);
scatter is ['False', 'True']. Enables scatter plot;
timeaxis is ['False', 'True']. Enables time axis;
vline is 'False' or a tuple (vline1, vline2). Shows up to two vertical lines;
pr is a name of process for plotting in another thread;
```

Other arguments are optional and used for automatic scaling (i.e. V to mV, etc.). Please, note
that it is impossible to redraw a line with scatters if they have the same name.
There is a possibility to draw data in parallel with the main script. To do this, a keyargumnet 'pr'
should be used. In this mode, the function returns the thread that starts the drawing, and check on
the next call whether the process has completed or not. A minimal working example for parallel
drawing with dynamic label is the following:

```python
import atomize.general_modules.general_functions as general
process = 'None'
for i in range(10):
	
	# draw one curve (x_axis, data_x) with a vertical line and a dynamic label "text"
	process = general.plot_1d('NAME_1', x_axis, data_1, xname = 'Delay', 
		xscale = 'ns', yname = 'Area', yscale = 'V*s', label = 'curve', 
		vline = (i, ), pr = process, text = str(i))

	# draw two curves (x_axis, data_x) and (x_axis, data_y) simultaneously
	process = general.plot_1d('NAME_2', x_axis, (data_1, data_2), label = 'curve', 
		xname = 'Delay', xscale = 'ns', yname = 'Area', yscale = 'V*s', 
		vline = (i, ), text = str(i))
```

A tuple (data_1, data_2) can be used as Ydata. In this case two curves will be plot simultaneously (see example above).
A dynamic label based on the text keyword argument works only for parallel drawing. For a standard drawing mode a function [general.text_label()](#dynamic-labeling) should be used.

---

## 2D plotting

```python		
plot_2d('name', data, start_step = ((Xstart, Xstep), (Ystart, Ystep)), 
		xname = 'NameXaxis', xscale = 'XaxisDimension', 
		yname = 'NameYaxis Field', yscale = 'YaxisDimension', 
		zname = 'NameZaxis', zscale = 'ZaxisDimension', 
		pr = 'None', text = '')
```

```
data is a multidimensional numpy array; example = [[1,1,1,..],[2,2,2,..],[3,3,3,..],..];
name is a string of the plot name;
label is a string of the curve name;
text is a label of the plot (for multithreading only);
pr is a name of process for plotting in another thread;
start_step is a list of starting points and steps for the X and Y axis;
```

Other arguments are optional and used for automatic scaling (i.e. V to mV, etc.).
There is a possibility to draw data in parallel with the main script. To do this, a key argumnet 'pr'
should be used. In this mode, the function returns the thread that starts the drawing, and check on
the next call whether the process has completed or not. A minimal working example for parallel
drawing with dynamic label is the following:

```python
import atomize.general_modules.general_functions as general
process = 'None'
for i in range(10):

    process = general.plot_2d('NAME', data, start_step = ((0, 1), (0, 1)), 
    	xname = 'Time', xscale = 'ns', yname = 'Delay', yscale = 'ns', 
    	zname = 'Intensity', zscale = 'V', pr = process, text = str(i))
```

---

## Dynamic labeling
```python
text_label('label', DynamicValue)
```

```
label is a string;
DynamicValue is a number that will change dynamically;
```

---

## Clearing
```python
plot_remove('name_of_plot')
```