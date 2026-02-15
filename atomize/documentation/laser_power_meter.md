---
title: Laser Power Meters
nav_order: 26
layout: page
permlink: /functions/laser_power_meter/
parent: Documentation
---

### Devices
- Gentec-EO (RS-232)
**Solo2**; Tested 12/2025

---

### Functions
- [laser_power_meter_name()](#laser_power_meter_name)<br/>
- [laser_power_meter_head_name()](#laser_power_meter_head_name)<br/>
- [laser_power_meter_get_data()](#laser_power_meter_get_data)<br/>
- [laser_power_meter_wavelength(\*wavelength)](#laser_power_meter_wavelengthwavelength)<br/>
- [laser_power_meter_zero_offset(\*zero_mode)](#laser_power_meter_zero_offsetzero_mode)<br/>
- [laser_power_meter_analog_output(\*analog_output)](#laser_power_meter_analog_outputanalog_output)<br/>
- [laser_power_meter_energy_mode(\*energy_mode)](#laser_power_meter_energy_modeenergy_modey)<br/>
- [laser_power_meter_scale(scale)](#laser_power_meter_scalescale)<br/>
- [laser_power_meter_command(command)](#laser_power_meter_commandcommand)<br/>
- [laser_power_meter_query(command)](#laser_power_meter_querycommand)<br/>

---

### laser_power_meter_name()
```python
laser_power_meter_name() -> str
```

The function returns device name.<br/>

---

### laser_power_meter_head_name()
```python
laser_power_meter_head_name() -> str
```

The function returns the model name of the current head.<br/>

---

### laser_power_meter_get_data()
```python
laser_power_meter_get_data() -> float
```
```
Example: laser_power_meter_get_data() queries the current measured value.
```
This function returns the measured value as soon as a new value appears on the device. If there is no new value, 10 consecutive attempts will be made, each of which will be repeated after the timeout specified in the configuration file has elapsed. After 10 unsuccessful attempts, a corresponding message will be displayed and the function will return 0.<br/>

---

### laser_power_meter_wavelength(\*wavelength)
```python
laser_power_meter_wavelength(wavelength: int) -> none
laser_power_meter_wavelength() -> str
```
```
Example: laser_power_meter_wavelength(532) sets the wavelength used to 532 nm.
```
This function queries or sets the wavelength being used on the detector. If there is no argument the function will return the current wavelength as a string: "Wavelength for correction: xxx nm". If there is an argument the specified wavelength will be set. The available range is 193-2100 nm.<br/>

---

### laser_power_meter_zero_offset(\*zero_mode)
```python
laser_power_meter_zero_offset(zero_mode: ['On','Off','Undo']) -> none
laser_power_meter_zero_offset() -> str
```
```
Example: laser_power_meter_zero_offset('On') resets the current measured value to zero.
```
This function queries or sets the zero mode being used on the detector. If there is no argument the function will return the current zero mode as a string: "Zero offset mode: ['On', 'Off']". The argument 'On' resets the current measured value to zero. The argument 'Off' disables the previousy performed reset.<br/>

---

### laser_power_meter_analog_output(\*analog_output)
```python
laser_power_meter_analog_output(zero_mode: ['On','Off']) -> none
laser_power_meter_analog_output() -> str
```
```
Example: laser_power_meter_analog_output() queries the current state of the analog output.
```
This function queries or sets the status of the analog output. If there is no argument, the function returns the current status of the analog output as a string: "Analog output: ['On', 'Off']". The argument 'On' turns on the analog output of the detector. The argument 'Off' turns off the analog output.<br/>

---

### laser_power_meter_energy_mode(\*energy_mode)
```python
laser_power_meter_energy_mode(energy_mode: ['On','Off']) -> none
laser_power_meter_energy_mode() -> str
```
```
Example: laser_power_meter_energy_mode('Off') turns off the energy mode.
```
This function queries or sets the current state of the energy mode. If there is no argument, the function returns the state of the energy mode as a string: "Energy mode: ['On', 'Off']". The argument 'On' can be used to toggle energy mode when using a wattmeter. The argument 'Off' turns off the energy mode.<br/>

---

### laser_power_meter_scale(scale)
```python
laser_power_meter_scale(scale: int + [' pW',' nW',' uW',' mW',' W',' kW']) -> none
laser_power_meter_scale(scale: 0) -> none
```
```
Example: laser_power_meter_scale('10 mW') sets the dispay range to 10 mW.
laser_power_meter_scale(0) sets automatic scaling.
```
This function forces the display of the current data within a specific range indicated as an argument. The argument is discrete and can take values from the following array: [1, 3, 10, 30, 100, 300] with pW, nW, uW, mW, W, and kW scaling. If there is no scale setting corresponding to the argument, the nearest available value is used and warning is printed. Note that not all scales are available for all heads.<br/>
An argument equals to 0 has a special meaning and corresponds to automatic scaling. The auto scale mode applies the best scale for the current values in real time.<br/>

---

### laser_power_meter_command(command)
```python
laser_power_meter_command(command: str) -> none
```
```
Example: laser_power_meter_command('str').
```
The function for sending an arbitrary command from a programming guide to the device in a string format. No output is expected. Please note that Gentec-EO Solo2 always responds to commands, so this function cannot be used for it.<br/>

---

### laser_power_meter_query(command)
```python
laser_power_meter_query(command: str) -> str
```
```
Example: laser_power_meter_query('*SHL'). This command adds significant digits 
to the on-screen reading.
```
The function for sending an arbitrary command from a programming guide to the device in a string format. An output in a string format is expected. Please note that Gentec-EO Solo2 will respond with “ACK” if the command is successfully executed.<br/>
