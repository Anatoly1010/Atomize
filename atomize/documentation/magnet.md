---
title: Magnetic Field Controllers
nav_order: 28
layout: page
permlink: /functions/magnet/
parent: Documentation
---
<br/>
Bruker BH15 module was rewritten from the [FSC2 module](http://users.physik.fu-berlin.de/~jtt/fsc2/fsc2.html) originally created by Jens Thomas Törring in C. Communication with Bruker ER032M field controller can be achieved using the same module.

### Devices
- Bruker **BH15** (GPIB: linux-gpib); Tested 01/2021
- Bruker **ER032M** (GPIB: linux-gpib); Available via BH15 module
- Bruker **ER031M** (RS-232 using arduino emulated keyboard); Tested 01/2021
- [Homemade](https://patents.google.com/patent/RU2799103C1/en?oq=RU2799103C1) magnetic field controller **ITC1** (RS-232); Tested 04/2023

---

### Functions
- [magnet_name()](#magnet_name)<br/>
- [magnet_setup(start_field, step_field)](#magnet_setupstart_field-step_field)<br/>
- [magnet_field(\*field)](#magnet_fieldfield)<br/>
- [magnet_sweep_up()](#magnet_sweep_up)<br/>
- [magnet_sweep_down()](#magnet_sweep_down)<br/>
- [magnet_reset_field()](#magnet_reset_field)<br/>
- [magnet_field_step_size(\*step)](#magnet_field_step_sizestep)<br/>
- [magnet_command(command)](#magnet_commandcommand)<br/>

---

### magnet_name()
```python
magnet_name() -> str
```
This function returns device name.<br/>

---

### magnet_setup(start_field, step_field)
```python
magnet_setup(start_field: float  step_field: float) -> none
```
```
Example: magnet_setup(3500, 10) sets the magnetic field to 3500 G and 
the field step to 10 G for using in sweeps.
```
This function is used to set the start field and the field step used in sweeps. The function expects two floating point arguments both in Gauss.
As it is indicated [here:](http://users.physik.fu-berlin.de/~jtt/fsc2/Magnet-Functions.html#magnet_005fsweep_005fup_0028_0029) for Bruker BH15 field controller for some combinations of the start field and field step size deviations between the requested field and the real field may result of up to 25 mG. If the maximum field deviation was larger than 5 mG at the end of the test run as well as the experiment the maximum field deviation is printed out. To minimize these deviations use a start field that is a multiple of 50 mG and avoid sweeps with more than about 2000 steps away from the start field.<br/>
The function is available for ITC1 field controller but has no meaning.<br/>

---

### magnet_field(\*field)
```python
magnet_field(field: float) -> none
magnet_field() -> float
```
```
Example: magnet_field(1000) sets the magnetic field to 1000 G.
```
This function queries or sets the magnetic field in Gauss. If an argument is specified the function sets a new magnetic field value. If there is no argument the function returns the current magnetic field. For the Bruker BH15 and Bruker ER031M field controllers this function returns the current field setting in Gauss.<br/>
For Bruker BH15 field controller setting a field with this function while also having initialized the magnet using [magnet_setup()](#magnet_setupstart_field-step_field) may result in deviations between the requested field and the real field of up to 25 mG.<br/>
Requesting the current value of the field is only possible, if the function [magnet_setup()](#magnet_setupstart_field-step_field) has been called or a field already has been set.<br/>

---

### magnet_sweep_up()
```python
magnet_sweep_up() -> float
```
```
Example: magnet_sweep_up() 
sweeps up the magnet by the field step value set in the magnet_setup() function.
```
This function does not take an argument and starts sweeping of magentic field up using the field step value specified in [magnet_setup()](#magnet_setupstart_field-step_field) function. It can be used only if the function [magnet_setup()](#magnet_setupstart_field-step_field) has been called before. The function returns the new field value.<br/>
The function is not available for Bruker ER031M and ITC1 field controllers.<br/>

---

### magnet_sweep_down()
```python
magnet_sweep_down() -> float
```
```
Example: magnet_sweep_down() 
sweeps down the magnet by the field step value set in the magnet_setup() function.
```
This function does not take an argument and starts sweeping of magentic field down using the field step value specified in [magnet_setup()](#magnet_setupstart_field-step_field) function. It can be used only if the function [magnet_setup()](#magnet_setupstart_field-step_field) has been called before. The function returns the new field value.<br/>
The function is not available for Bruker ER031M and ITC1 field controllers.<br/>

---

### magnet_reset_field()
```python
magnet_reset_field() -> float
```
```
Example: magnet_reset_field() 
resets the magnetic field to the start field value.
```
This function resets the magnetic field to the start field value specified in a previous call of [magnet_setup()](#magnet_setupstart_field-step_field). The function returns the new field value.<br/>
The function is not available for Bruker ER031M and ITC1 field controllers.<br/>

---

### magnet_field_step_size(\*step)
```python
magnet_field_step_size(step: float) -> none
magnet_field_step_size() -> float
```
```
Example: magnet_field_step_size(10) returns the possible field step size nearest to 10 Gauss
```
This function returns the minimum field step size (in Gauss) if called without an argument and the possible field step size (in Gauss) nearest to the argument.<br/>
The function is not available for Bruker ER031M and ITC1 field controllers.<br/>

---

### magnet_command(command)
```python
magnet_command(command: str) -> none
```
This function for sending an arbitrary command to the device in a string format. No output is expected.<br/>
The function is not available for Bruker ER031M and ITC1 field controllers.<br/>
