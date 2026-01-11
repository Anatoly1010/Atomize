---
title: Moisture Meters
nav_order: 31
layout: page
permlink: /functions/moisture_meter/
parent: Documentation
---

### Devices
- IVG **1/1** (RS-485); Tested 02/2023

---

### Functions
- [moisture_meter_name()](#moisture_meter_name)<br/>
- [moisture_meter_meter()](#moisture_meter_meter)<br/>

---

### moisture_meter_name()
```python
moisture_meter_name() -> str
```
The function returns device name.<br>

---

### moisture_meter_meter()
```python
moisture_meter_meter() -> list(4)
```
```
Example: moisture_meter_meter() returns the measured data.
```
This function returns a list with the measured data and is only called without arguments. The format of the measured data is the following: ['dew point in deg. C', 'water content in ppm', 'water content in mg/m<sub>3</sub>', 'temperature in deg. C'].<br>