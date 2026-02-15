---
title: Gaussmeters
nav_order: 25
layout: page
permlink: /functions/gaussmeter/
parent: Documentation
---

### Devices
- Lakeshore **455 DSP** (RS-232); Tested 01/2021
- NMR Gaussmeter **Sibir 1** (UDP/IP Socket); Tested 04/2024

---

### Functions
- [gaussmeter_name()](#gaussmeter_name)<br/>
- [gaussmeter_field()](#gaussmeter_field)<br/>
- [gaussmeter_units(\*units)](#gaussmeter_unitsunits)<br/>
- [gaussmeter_points(\*points)](#gaussmeter_pointspoints)<br/>
- [gaussmeter_number_of_averages(\*number)](#gaussmeter_number_of_averagesnumber)<br/>
- [gaussmeter_search(start, end, step)](#gaussmeter_searchstart-end-step)<br/>
- [gaussmeter_set_field(\*B)](#gaussmeter_set_fieldb)<br/>
- [gaussmeter_gain(\*gain)](#gaussmeter_gaingain)<br/>
- [gaussmeter_pulse_length(\*length)](#gaussmeter_pulse_lengthlength)<br/>
- [gaussmeter_sensor_number(\*number)](#gaussmeter_sensor_numbernumber)<br/>
- [gaussmeter_command(command)](#gaussmeter_commandcommand)<br/>
- [gaussmeter_query(command)](#gaussmeter_querycommand)<br/>

---

### gaussmeter_name()
```python
gaussmeter_name() -> none
```
This function returns device name.<br>

---

### gaussmeter_field()
```python
gaussmeter_field() -> float
gaussmeter_field() -> numpy.array, numpy.array, float, float
```
```
Example: gaussmeter_field() returns the field reading in Gauss.
```
This function is for reading field and should be called with no argument. The default unit is Gauss. By using [gaussmeter_units()](#gaussmeter_unitsunits) function unit setting can be changed.<br/>
In the case of Sibir 1 Gaussmeter, this function returns (i) numpy.array of the measured FID, (ii) numpy.array of the measured NMR spectrum, (iii) float of the measured magnetic field in Gauss, (iv) float of the measured signal-to-noise ratio.<br/>

---

### gaussmeter_units(\*units)
```python
gaussmeter_units(units: ['Gauss','Tesla','Oersted','Amp/m']) -> none
gaussmeter_units() -> str
```
```
Example: gaussmeter_units('Tesla') changes the unit of gaussmeter_field() function to Tesla.
```
This function queries or changes the unit in which [gaussmeter_field()](#gaussmeter_field) function returns the result. If called with no argument the current unit is returned. If called with an argument the specified unit is set.<br/>
Argument should be from the array: ['Gauss', 'Tesla', 'Oersted', 'Amp/m'].<br/>
This function is not available for Sibir 1 Gaussmeter.<br/>

---

### gaussmeter_points(\*points)
```python
gaussmeter_points(points: int) -> none
gaussmeter_points() -> int
```
```
Example: gaussmeter_units(8192) sets the number of points in FID to 8192.
```
This function queries or sets the number of FID points that will be measured after applying pi/2 pulse. If called with no argument the current number of points is returned. If called with an argument the specified number of points is set.<br/>
Possible number of points are the following: [8192, 16384, 32768, 53248]. If there is no number of points setting fitting the argument the nearest available value is used and warning is printed.<br/>
This function is only available for Sibir 1 Gaussmeter.<br/>

---

### gaussmeter_number_of_averages(\*number)
```python
gaussmeter_number_of_averages(number: int) -> none
gaussmeter_number_of_averages() -> int
```
```
Example: gaussmeter_number_of_averages(64) sets the number of averages to 64.
```
This function queries or sets the number of averages for FID of NMR signal from the probe. If called with no argument the current number of averages is returned. If called with an argument the specified  number of averages is set.<br/>
Possible number of averages are the following: [1, 8, 16, 32, 64, 128, 256, 512, 1024, 2048]. If there is no number of averages setting fitting the argument the nearest available value is used and warning is printed.<br/>
This function is only available for Sibir 1 Gaussmeter.<br/>

---

### gaussmeter_search(start, end, step)
```python
gaussmeter_search(start: int, end: int, step: int) -> float
```
```
Example: gaussmeter_search(1000, 1500, 10) runs the search of the best SNR.
```
This function performs repeated measurements of the FID decay from the probe with a synthetizer frequency corresponding to the current field. The latter is varied during the function exectuion, starting from 'start' value with a step of 'step'. The function returns the value of magnetic field with the best measured signal-to-noise ratio.<br/>
This function is only available for Sibir 1 Gaussmeter.<br/>

---

### gaussmeter_set_field(\*B)
```python
gaussmeter_set_field(B: float) -> none
gaussmeter_set_field() -> float
```
```
Example: gaussmeter_set_field(1234) sets the synthetizer frequency, matching B of 1234 Gauss.
```
This function queries or sets the synthetizer frequency. Instead of the frequency a corresponding magnetic field is used as an argument. To increase the signal-to-noise ratio the value of magnetic field, indicated as an argument of this function, should be as closer as possible to the real value to be measured. If called with no argument the current value of magnetic field is returned. If called with an argument the specified value of magnetic field is set.<br/>
This function is only available for Sibir 1 Gaussmeter.<br/>

---

### gaussmeter_gain(\*gain)
```python
gaussmeter_gain(gain: int) -> none
gaussmeter_gain() -> int
```
```
Example: gaussmeter_gain(10) sets the preamplifier gain to 10 arb. u.
```
This function queries or sets the preamplifier gain for the detection of NMR signal from the probe. If called with no argument the current gain is returned. If called with an argument the specified gain is set.<br/>
The minimum gain is 0, the maximum gain is 31.<br/>
This function is only available for Sibir 1 Gaussmeter.<br/>

---

### gaussmeter_pulse_length(\*length)
```python
gaussmeter_pulse_length(length: int) -> none
gaussmeter_pulse_length() -> int
```
```
Example: gaussmeter_pulse_length(10) sets the pi/2 pulse length to 10 us.
```
This function queries or sets the pi/2 pulse length in us. If called with no argument the current pulse length is returned. If called with an argument the specified pulse length is set.<br/>
The minimum pulse length is 0 us, the maximum pulse length is 40 us.<br/>
This function is only available for Sibir 1 Gaussmeter.<br/>

---

### gaussmeter_sensor_number(\*number)
```python
gaussmeter_sensor_number(number: int) -> none
gaussmeter_sensor_number() -> int
```
```
Example: gaussmeter_sensor_number(1) indicates that the first sensor will be used.
```
This function queries or sets the number of sensor that will be used for magnetic field measurement. If called with no argument the current sensor number is returned. If called with an argument the specified sensor number is set. Each sensor is optimized for different magnetic field range. Sensors 1 and 2 are optimized for the range of 25 mT - 200 mT.  Sensors 3 and 4 are optimized for the range of 90 mT - 2000 mT.<br/>
Possible sensors are the following: [1, 2, 3, 4].<br/>
This function is only available for Sibir 1 Gaussmeter.<br/>

---

### gaussmeter_command(command)
```python
gaussmeter_command(command: str) -> none
```
```
Example: gaussmeter_command('RDGMODE 1,3,1,1,1') configures Lakeshore 455 for DC field
measurement, DC resolution of 5 digits, wide band rms filter mode, peak measurement mode
is periodic, and positive peak readings will be shown if the measurement mode is changed to peak.
```
This function sends an arbitrary command from a programming guide to the device in a string format. No output is expected.<br/>
This function is not available for Sibir 1 Gaussmeter.<br/>

---

### gaussmeter_query(command)
```python
gaussmeter_query(command: str) -> str
```
```
Example: gaussmeter_query('TYPE? ') returns the type of the probe used.
```
This function sends an arbitrary command from a programming guide to the device in a string format. An output in a string format is expected.<br/>
This function is not available for Sibir 1 Gaussmeter.<br/>