---
title: Microwave Bridges
nav_order: 30
layout: page
permlink: /functions/microwave_bridge/
parent: Documentation
---

### Devices

Available devices:
- Micran X-band MW Bridge (TCP/IP Socket); Tested 06/2021
- Micran X-band MW Bridge v2 (TCP/IP Socket); Tested 12/2022
- Micran Q-band MW Bridge (TCP/IP Socket); Tested 12/2023

---

### Functions
- [mw_bridge_name()](#mw_bridge_name)<br/>
- [mw_bridge_open()](#mw_bridge_open)<br/>
- [mw_bridge_close()](#mw_bridge_close)<br/>
- [mw_bridge_synthesizer(\*freq)](#mw_bridge_synthesizerfreq)<br/>
- [mw_bridge_att1_prd(\*atten)](#mw_bridge_att1_prdatten)<br/>
- [mw_bridge_att2_prd(\*atten)](#mw_bridge_att2_prdatten)<br/>
- [mw_bridge_fv_ctrl(\*phase)](#mw_bridge_fv_ctrlphase)<br/>
- [mw_bridge_fv_prm(\*phase)](#mw_bridge_fv_prmphase)<br/>
- [mw_bridge_att_prm(\*atten)](#mw_bridge_att_prmatten)<br/>
- [mw_bridge_att2_prm(\*atten)](#mw_bridge_att2_prmatten)<br/>
- [mw_bridge_k_prm(\*amplif)](#mw_bridge_k_prmamplif)<br/>
- [mw_bridge_att_pin(\*atten)](#mw_bridge_att_pinatten)<br/>
- [mw_bridge_cut_off(\*cutoff)](#mw_bridge_cut_offcutoff)<br/>
- [mw_bridge_rotary_vane(\*atten, mode)](#mw_bridge_rotary_vaneatten-mode) <br/>
- [mw_bridge_telemetry()](#mw_bridge_telemetry)<br/>
- [mw_bridge_initialize()](#mw_bridge_initialize)<br/>
- [mw_bridge_reset()](#mw_bridge_reset)<br/>

---

### mw_bridge_name()
```python
mw_bridge_name() -> str
```
This function returns device name.<br>

---

### mw_bridge_open()
```python
mw_bridge_open() -> ['DEVICE OPENED','DEVICE NOT FOUND']
```
This function is only available for Micran Q-band MW Bridge. It opens the driver of the microwave bridge and should be called before any other functions.<br>

---

### mw_bridge_close()
```python
mw_bridge_close() -> ['DEVICE CLOSED']
```
This function is only available for Micran Q-band MW Bridge. It closes the driver of the microwave bridge and should be called after the last operation function in the script is executed.<br>

---

### mw_bridge_synthesizer(\*freq)
```python
mw_bridge_synthesizer(freq: int) -> none
mw_bridge_synthesizer() -> 'Frequency: {int} MHz'
```
```
Example: mw_bridge_synthesizer(9750)
sets the frequency of the synthesizer to 9750 MHz.
```
This function queries or sets the frequency of the synthesizer in MHz. If an argument is specified, the function sets a new frequency value. If there is no argument, the function returns the current frequency in the form of 'Frequency: 9750 MHz'. The valid range of frequency is from 9000 to 10000 MHz with 1 MHz step. The range can be modified in the configuration file.<br>

---

### mw_bridge_att1_prd(\*atten)
```python
mw_bridge_att1_prd(attenuation: float) -> none 
mw_bridge_att1_prd() -> 'Attenuator PRD1: {float} dB'
```
```
Example: mw_bridge_att1_prd(1.5) sets the attenuation to 1.5 dB for the first
attenuator in the PRD part of the bridge.
```
This function queries or sets the attenuation (in dB) of the first attenuator in the PRD part of the bridge. If an argument is specified, the function sets a new attenuation value. If there is no argument, the function returns the current attenuation. The output is in the form of 'Attenuator PRD1: 15.5 dB'. The valid range is from 0 to 31.5 dB with 0.5 dB step.<br>

---

### mw_bridge_att2_prd(\*atten)
```python
mw_bridge_att2_prd(attenuation: float) -> none 
mw_bridge_att2_prd() -> 'Attenuator PRD2: {float} dB'
```
```
Example: mw_bridge_att2_prd() returns the attenuation for the second attenuator
in the PRD part of the bridge.
```
This function queries or sets the attenuation (in dB) of the second attenuator in the PRD part of the bridge. If an argument is specified, the function sets a new attenuation value. If there is no argument, the function returns the current attenuation. The output is in the form: 'Attenuator PRD2: 15.5 dB'. The valid range is from 0 to 31.5 dB with 0.5 dB step.<br>
This function is not available for Micran Q-band MW bridge.<br>

---

### mw_bridge_fv_ctrl(\*phase)
```python
mw_bridge_fv_ctrl(phase: float) -> none
mw_bridge_fv_ctrl() -> 'Phase CTRL: {float} deg'
```
```
Example: mw_bridge_fv_ctrl('100') 
sets the phase shifter in the CTRL part of the bridge to 100 deg.
```
This function queries or sets the phase (in deg) of the phase shifter in the CTRL part of the bridge. If an argument is specified, the function sets a new phase value. If there is no argument, the function returns the current phase. The output is in the form: 'Phase CTRL: 5.625 deg'. The valid range is from 0 to 354.375° with 5.625° step. If there is no phase setting fitting the argument the nearest available value is used and warning is printed.<br>
This function is not available for Micran Q-band MW bridge.<br>

---

### mw_bridge_fv_prm(\*phase)
```python
mw_bridge_fv_prm(phase: float) -> none
mw_bridge_fv_prm() -> 'Phase PRM: {float} deg'
```
```
Example: mw_bridge_fv_prm() returns the phase in the PRM part of the bridge.
```
This function queries or sets the phase (in deg) of the phase shifter in the PRM part of the bridge. If an argument is specified, the function sets a new phase value. If there is no argument the function returns the current phase. The output is in the form: 'Phase PRM: 5.625 deg'. The valid range is from 0 to 354.375° with 5.625° step. If there is no phase setting fitting the argument the nearest available value is used and warning is printed.<br>
This function is not available for Micran Q-band MW bridge.<br>

---

### mw_bridge_att_prm(\*atten)
```python
mw_bridge_att_prm(attenuation: float) -> none
mw_bridge_att_prm() -> 'Video Attenuation: {int} dB'
```
```
Example: mw_bridge_att_prm('2 dB') sets the attenuation to 2 dB 
for the attenuator in the PRM part of the bridge.
```
This function queries or sets the attenuation (in dB) of the attenuator in the PRM part of the bridge. If an argument is specified, the function sets a new attenuation value. If there is no argument the function returns the current attenuation. The valid range is from 0 to 22 dB with 2 dB step. The output is in the form: 'Video Attenuation: 14 dB'.<br>

---

### mw_bridge_att2_prm(\*atten)
```python
mw_bridge_att2_prm(attenuation: float) -> none
mw_bridge_att2_prm() -> 'Video Attenuation 2: {int} dB'
```
```
Example: mw_bridge_att2_prm('2 dB') sets the attenuation to 2 dB 
for the attenuator 2 in the PRM part of the bridge.
```
This function queries or sets the attenuation (in dB) of the attenuator 2 in the PRM part of the bridge. If an argument is specified, the function sets a new attenuation value. If there is no argument, the function returns the current attenuation. The output is in the form: 'Video Attenuation 2: 14 dB'. The valid range is from 0 to 31.5 dB with 0.5 dB step.<br>
This function is only available for the Micran X-band MW Bridge v2 and Micran Q-band MW Bridge. The function [mw_bridge_k_prm()](#mw_bridge_k_prmamplif) should be used for Micran X-band MW Bridge.<br>

---

### mw_bridge_k_prm(\*amplif)
```python
mw_bridge_k_prm(amplification: float) -> none
mw_bridge_k_prm() -> 'Amplification PRM: {int} dB'
```
```
Example: mw_bridge_k_prm(0) sets the amplification coefficient to 0 dB.
```
This function queries or sets the amplification coefficient (in dB) in the PRM part of the bridge. If an argument is specified, the function sets a new amplification value. If there is no argument, the function returns the current amplification. The output is in the form: 'Amplification PRM: 22 dB'. The valid values are 0 and 22 dB.<br/>
This function is only available for the Micran X-band MW Bridge. The function [mw_bridge_att2_prm()](#mw_bridge_att2_prmatten) should be used for Micran X-band MW Bridge v2 and Micran Q-band MW Bridge.<br>

---

### mw_bridge_att_pin(\*atten)
```python
mw_bridge_att_pin(attenuation: float) -> none
mw_bridge_att_pin() -> 'PIN Attenuator: {int} dB'
```
```
Example: mw_bridge_att_pin(10) sets the attenuation to 10 dB
for the pin attenuator of the bridge. 
```
This function queries or sets the attenuation (in dB) of the pin attenuator of the bridge. If an argument is specified, the function sets a new attenuation. If there is no argument, the function returns the current attenuation. The output is in the form: 'PIN Attenuator: 10 dB'. The valid range is from 0 to 36 dB.<br/>
This function is only available for the Micran Q-band MW Bridge.<br>

---

### mw_bridge_cut_off(\*cutoff)
```python
mw_bridge_cut_off(cutoff: [30, 105, 300]) -> none
mw_bridge_cut_off() -> 'Cut-off Frequency: {int} MHz'
```
```
Example: mw_bridge_cut_off(300) sets the cut-off frequency to 300 MHz.
```
This function queries or sets the cut-off frequency (in MHz) of the bridge. If an argument is specified the function sets a new cut-off frequency. If there is no argument, the function returns the current cut-off frequency. The output is in the form: 'Cut-off Frequency: 105 MHz'. The valid values are 30, 105, and 300 MHz.<br>

---

### mw_bridge_rotary_vane(\*atten, mode)
```python
mw_bridge_rotary_vane(attenuation: float, mode = 'Arbitrary')
mw_bridge_rotary_vane() -> 'Rotary Vane Attenuation: {int} dB'
```
```
Example: mw_bridge_rotary_vane('10 dB', mode = 'Arbitrary')
sets the attenuation of the rotary vane to 10 dB.
```
This function queries or sets the attenuation (in dB) of the rotary vane attenuator of the bridge. If an argument is specified, the function sets a new attenuation value. If there is no argument, the function returns the current attenuation. The output is in the form: 'Rotary Vane Attenuation: 10 dB'. The valid range is from 0 to 60 dB with 0.1 dB step.<br/>
There are also two possible mode of the attenuator, that can be selected using the 'mode' key argument. The available modes are: ['Limit', 'Arbitrary']. In 'Limit' mode only two limit values of the attenuation can be used: 0 dB and 60 dB. This mode is usually used for initialization. In 'Arbitrary' mode any attenuation value from the range of 0 to 60 dB with 0.1 dB step can be used.<br/>
This function is not available on the Micran X-band MW Bridge.<br/>
For consistency, it is always best to end the experimental script at 60 dB attenuation:
```python
mw_bridge_rotary_vane(60, mode = 'Limit')
```

---

### mw_bridge_telemetry()
```python
mw_bridge_telemetry() -> str
```
```
Example: mw_bridge_telemetry() returns the telemetry.
```
This function returns the telemetry. The format for Micran X-band MW Bridge and Micran X-band MW Bridge v2 is DATE; TEMPERATURE; STATE (INIT/WORK).<br/>
The format for Micran Q-band MW Bridge is DATE; ANSWER RECEIVED; PARAMS UPDATED; TI TOO SHORT; HPA TOO LONG; HPA ON INCORRECT; HPA OFF INCORRECT; EXT CLOCK CORRECT; SHAPER TOO LONG; DUTY CYCLE TOO LOW. All parameters except DATE has 0 (Off) and 1 (On) format.<br>

---

### mw_bridge_initialize()
```python
mw_bridge_initialize() -> none
```
```
Example: mw_bridge_initialize() resets the bridge to initialization state.
```
This function returns the bridge to initialization state. The initialization state corresponds to ATT1_PRD = 0 dB; ATT2_PRD = 0 dB; FV_CTRL = 0°; FV_PRM = 0°; ATT_PRM = 0 dB; K_PRM = 22 dB for Micran X-band MW Bridge or ATT2_PRM = 0 dB for Micran X-band MW Bridge v2; CUT-OFF frequency = 300 MHz; Synthesizer frequency = 1000 MHz; Synthesizer power = OFF.<br>
For Micran Q-band MW Bridge a modified function should be used:<br>
```python
mw_bridge_initialize(state: ['On','Off']) -> none
```
This function initializes the bridge and turns on several options, namely "Internal Start ON", "External Clock ON", "Receiver LO Amp ON", "AWG LO Amp ON".<br>

---

### mw_bridge_reset()
```python
mw_bridge_initialize() -> none
```
This function is only available for Micran Q-band MW Bridge. It resets all the errors occured during the device operation. The status of these error flags can be checked using the [mw_bridge_telemetry()](#mw_bridge_telemetry) function.<br>
