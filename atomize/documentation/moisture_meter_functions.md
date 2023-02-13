# List of available functions for moisture meters

Available devices:
- IVG-1/1 (RS-485); Tested 02/2023

Functions:
- [moisture_meter_name()](#moisture_meter_name)<br/>
- [moisture_meter_meter()](#moisture_meter_meter)<br/>

### moisture_meter_name()
```python3
moisture_meter_name()
Arguments: none; Output: string.
```
The function returns device name.
### moisture_meter_meter()
```python3
moisture_meter_meter()
Arguments: none; Output: list [ -49.9, 40.12, 29.1, 25.1 ].
Example: moisture_meter_meter() returns the measured data.
```
This function returns a list with the measured data and is only called without arguments. The format of the measured data is the following: ['dew point in deg. C', 'water content in ppm', 'water content in mg/m^3', 'temperature in deg. C'].<br/>