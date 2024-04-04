# List of available functions for gaussmeters

Available devices:
- Lakeshore 455 DSP (RS-232); Tested 01/2021
- NMR Gaussmeter Sibir 1 (UDP/IP Socket); Tested 04/2024

Functions:
- [gaussmeter_name()](#gaussmeter_name)<br/>
- [gaussmeter_field()](#gaussmeter_field)<br/>
- [gaussmeter_units(*units)](#gaussmeter_unitsunits)<br/>
- [gaussmeter_points(*points)](#gaussmeter_pointspoints)<br/>
- [gaussmeter_number_of_averges(*number)](#gaussmeter_number_of_avergesnumber)<br/>
- [gaussmeter_search(low, high)](#gaussmeter_searchlow-high)<br/>
- [gaussmeter_set_field(*B)](#gaussmeter_set_fieldb)<br/>
- [gaussmeter_gain(*gain)](#gaussmeter_gaingain)<br/>
- [gaussmeter_pulse_length(*length)](#gaussmeter_pulse_lengthlength)<br/>
- [gaussmeter_sensor_number(*number)](#gaussmeter_sensor_numbernumber)<br/>
- [gaussmeter_command(command)](#gaussmeter_commandcommand)<br/>
- [gaussmeter_query(command)](#gaussmeter_querycommand)<br/>

### gaussmeter_name()
```python3
gaussmeter_name()
Arguments: none; Output: string.
```
This function returns device name.
### gaussmeter_field()
```python3
gaussmeter_field()
Arguments: none; Output: float.
Example: gaussmeter_field() returns the field reading in Gauss.
```
This function is for reading field and should be called with no argument. The default unit is Gauss. By using [gaussmeter_units()](#gaussmeter_unitsunits) function unit setting can be changed.<br/>
### gaussmeter_units(*units)
```python3
gaussmeter_units(*units)
Arguments: units = string (['Gauss','Tesla','Oersted','Amp/m']); Output: string.
Example: gaussmeter_units('Tesla') changes the unit of gaussmeter_field() function to Tesla.
```
This function queries or changes the unit in which [gaussmeter_field()](#gaussmeter_field) function returns the result. If called with no argument the current unit is returned. If called with an argument the specified unit is set. Argument should be from the array: ['Gauss', 'Tesla', 'Oersted', 'Amp/m'].<br/>
### gaussmeter_points(*points)
```python3
gaussmeter_points(*points)
```
### gaussmeter_number_of_averges(*number)
```python3
gaussmeter_number_of_averges(*number)
```
### gaussmeter_search(low, high)
```python3
gaussmeter_search(low, high)
```
### gaussmeter_set_field(*B)
```python3
gaussmeter_set_field(*B)
```
### gaussmeter_gain(*gain)
```python3
gaussmeter_gain(*gain)
```
### gaussmeter_pulse_length(*length)
```python3
gaussmeter_pulse_length(*length)
```
### gaussmeter_sensor_number(*number)
```python3
gaussmeter_sensor_number(*number)
```
### gaussmeter_command(command)
```python3
gaussmeter_command(command)
Arguments: command = string; Output: none.
Example: gaussmeter_command('RDGMODE 1,3,1,1,1') configures Lakeshore 455 gaussmeter for DC field
measurement, DC resolution of 5 digits, wide band rms filter mode, peak measurement mode
is periodic, and positive peak readings will be displayed if the measurement mode is changed to peak.
```
The function for sending an arbitrary command from a programming guide to the device in a string format. No output is expected.<br/>
### gaussmeter_query(command)
```python3
gaussmeter_query(command)
Arguments: command = string; Output: string.
Example: gaussmeter_query('TYPE? ') returns the type of the probe used.
```
The function for sending an arbitrary command from a programming guide to the device in a string format. An output in a string format is expected.<br/>