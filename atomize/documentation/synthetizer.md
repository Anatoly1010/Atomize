---
title: Synthetizers
nav_order: 35
layout: page
permlink: /functions/synthetizer/
parent: Documentation
---

### Devices

Available devices:
- **ECC 15K** (RS-232); Tested 01/2023

---

### Functions
- [synthetizer_name()](#synthetizer_name)<br/>
- [synthetizer_frequency(\*freq)](#synthetizer_frequencyfreq)<br/>
- [synthetizer_state(\*state)](#synthetizer_statestate)<br>
- [synthetizer_power(\*level)](#synthetizer_powerlevel)<br>
- [synthetizer_command(command)](#synthetizer_commandcommand)<br/>
- [synthetizer_query(command)](#synthetizer_querycommand)<br/>

---

### synthetizer_name()
```python
synthetizer_name()
Arguments: none; Output: string.
```
The function returns device name.<br/>

---

### synthetizer_frequency(\*freq)
```python
synthetizer_frequency(freq: int + [' Hz',' kHz',' MHz',' GHz']) -> none
synthetizer_frequency() -> str
```
```
Example: synthetizer_frequency('9 GHz') sets the frequency to 9 GHz.
```
This function queries or sets the frequency of the synthetizer. If there is no argument, the function returns the current frequency. The output of the function is a string in the format 'number + ['Hz', 'kHz', 'MHz', 'GHz']. If there is an argument, the specified frequency will be set. The center frequency argument is a string in the format 'number [Hz, kHz, MHz, GHz]'. The available range for ECC 15K is from 10 MHz to 15 GHz.<br/>

---

### synthetizer_state(\*state)
```python
synthetizer_state(state: ['On','Off']) -> none
synthetizer_state() -> str
```
```
Example: synthetizer_frequency('On') turns on the synthetizer.
```
This function queries or sets the state of the power output. If there is no argument, the function returns the current state. If there is an argument, the specified state will be set. The available states are ['On', 'Off'].<br/>

---

### synthetizer_power(\*level)
```python
synthetizer_power(level: int) -> none
synthetizer_power() -> int
```
```
Example: synthetizer_power(1) sets the power level to 1 arb. u.
```
This function queries or sets the power level. If there is no argument, the function returns the current power level as an integer. If there is an argument, the specified power level will be set. The available range for ECC 15K is from 0 arb. u. to 15 arb. u. The value of 15 corresponds to the maximum power level.<br/>

---

### synthetizer_command(command)
```python
synthetizer_command(command: str) -> none
```
This function for sending an arbitrary command to the device in a string format. No output is expected.<br/>

---

### synthetizer_query(command)
```python
synthetizer_query(command: str) -> none
```
This function for sending an arbitrary command to the device in a string format. An output in a string format is expected.<br>
