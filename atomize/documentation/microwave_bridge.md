---
title: Microwave Bridges
nav_order: 29
layout: page
permlink: /functions/microwave_bridge/
parent: Documentation
---

### Devices

Available devices:
- Mikran X-band MW Bridge (TCP/IP Socket); Tested 06/2021
- Mikran X-band MW Bridge v2 (TCP/IP Socket); Tested 12/2022

---

### Functions
- [mw_bridge_name()](#mw_bridge_name)<br/>
- [mw_bridge_synthesizer(*freq)](#mw_bridge_synthesizerfreq)<br/>
- [mw_bridge_att1_prd(*atten)](#mw_bridge_att1_prdatten)<br/>
- [mw_bridge_att2_prd(*atten)](#mw_bridge_att2_prdatten)<br/>
- [mw_bridge_fv_ctrl(*phase)](#mw_bridge_fv_ctrlphase)<br/>
- [mw_bridge_fv_prm(*phase)](#mw_bridge_fv_prmphase)<br/>
- [mw_bridge_att_prm(*atten)](#mw_bridge_att_prmatten)<br/>
- [mw_bridge_att2_prm(*atten)](#mw_bridge_att2_prmatten)<br/>
- [mw_bridge_k_prm(*amplif)](#mw_bridge_k_prmamplif)<br/>
- [mw_bridge_cut_off(*cutoff)](#mw_bridge_cut_offcutoff)<br/>
- [mw_bridge_rotary_vane(*atten, mode)](#mw_bridge_rotary_vaneatten-mode) <br/>
- [mw_bridge_telemetry()](#mw_bridge_telemetry)<br/>
- [mw_bridge_initialize()](#mw_bridge_initialize)<br/>

---

### mw_bridge_name()
```python
mw_bridge_name() -> str
```
This function returns device name.

---

### mw_bridge_synthesizer(*freq)
```python
mw_bridge_synthesizer(freq: int) -> none
mw_bridge_synthesizer() -> str
```
```
Example: mw_bridge_synthesizer(9750)
sets the frequency of the synthesizer to 9750 MHz.
```
This function queries or sets the frequency of the synthesizer in MHz. If an argument is specified, the function sets a new frequency value. If there is no argument, the function returns the current frequency.<br/>
The valid range of frequency is from 9000 to 10000 MHz with 1 MHz step. The range can be modified in the config file. The output is in the form: 'Frequency: 9750 MHz'.

---

### mw_bridge_att1_prd(*atten)
```python
mw_bridge_att1_prd(attenuation: float) -> none 
mw_bridge_att1_prd() -> str
```
```
Example: mw_bridge_att1_prd('1.5') sets the attenuation to 1.5 dB for the first
attenuator in the PRD part of the bridge.
```
This function queries or sets the attenuation (in dB) of the first attenuator in the PRD part of the bridge. If an argument is specified, the function sets a new attenuation value. If there is no argument, the function returns the current attenuation.<br/>
The valid range is from 0 to 31.5 dB with 0.5 dB step. The output is in the form: 'Attenuator PRD1: 15.5 dB'.

---

### mw_bridge_att2_prd(*atten)
```python
mw_bridge_att2_prd(attenuation: float) -> none 
mw_bridge_att2_prd() -> str
```
```
Example: mw_bridge_att2_prd() returns the attenuation for the second attenuator
in the PRD part of the bridge.
```
This function queries or sets the attenuation (in dB) of the second attenuator in the PRD part of the bridge. If an argument is specified, the function sets a new attenuation value. If there is no argument, the function returns the current attenuation.<br/>
The valid range is from 0 to 31.5 dB with 0.5 dB step. The output is in the form: 'Attenuator PRD2: 15.5 dB'.

---

### mw_bridge_fv_ctrl(*phase)
```python
mw_bridge_fv_ctrl(phase: float) -> none
mw_bridge_fv_ctrl() -> str
```
```
Example: mw_bridge_fv_ctrl('100') 
sets the phase shifter in the CTRL part of the bridge to 100 deg.
```
This function queries or sets the phase (in deg) of the phase shifter in the CTRL part of the bridge. If an argument is specified, the function sets a new phase value. If there is no argument, the function returns the current phase.<br/>
The valid range is from 0 to 354.375° with 5.625° step. If there is no phase setting fitting the argument the nearest available value is used and warning is printed. The output is in the form: 'Phase CTRL: 5.625 deg'.

---

### mw_bridge_fv_prm(*phase)
```python
mw_bridge_fv_prm(phase: float) -> none
mw_bridge_fv_prm() -> str
```
```
Example: mw_bridge_fv_prm() returns the phase in the PRM part of the bridge.
```
This function queries or sets the phase (in deg) of the phase shifter in the PRM part of the bridge. If an argument is specified, the function sets a new phase value. If there is no argument the function returns the current phase.<br/>
The valid range is from 0 to 354.375° with 5.625° step. If there is no phase setting fitting the argument the nearest available value is used and warning is printed. The output is in the form: 'Phase PRM: 5.625 deg'.

---

### mw_bridge_att_prm(*atten)
```python
mw_bridge_att_prm(attenuation: float) -> none
mw_bridge_att_prm() -> str
```
```
Example: mw_bridge_att_prm('2 dB') sets the attenuation to 2 dB 
for the attenuator in the PRM part of the bridge.
```
This function queries or sets the attenuation (in dB) of the attenuator in the PRM part of the bridge. If an argument is specified, the function sets a new attenuation value. If there is no argument the function returns the current attenuation.<br/>
The valid range is from 0 to 22 dB with 2 dB step. The output is in the form: 'Video Attenuation: 14 dB'.

---

### mw_bridge_att2_prm(*atten)
```python
mw_bridge_att2_prm(attenuation: float) -> none
mw_bridge_att2_prm() -> str
```
```
Example: mw_bridge_att2_prm('2 dB') sets the attenuation to 2 dB 
for the attenuator 2 in the PRM part of the bridge.
```
This function queries or sets the attenuation (in dB) of the attenuator 2 in the PRM part of the bridge. If an argument is specified, the function sets a new attenuation value. If there is no argument, the function returns the current attenuation.<br/>
The valid range is from 0 to 31.5 dB with 0.5 dB step. This function is only available on the Mikran X-band MW Bridge v2. The function [mw_bridge_k_prm()](#mw_bridge_k_prmamplif) should be used for Mikran X-band MW Bridge. The output is in the form: 'Video Attenuation 2: 14 dB'.

---

### mw_bridge_k_prm(*amplif)
```python
mw_bridge_k_prm(amplification: float) -> none
mw_bridge_k_prm() -> str
```
```
Example: mw_bridge_k_prm(0) sets the amplification coefficient to 0 dB.
```
This function queries or sets the amplification coefficient (in dB) in the PRM part of the bridge. If an argument is specified, the function sets a new amplification value. If there is no argument, the function returns the current amplification.<br/>
The valid values are 0 and 22 dB. This function is only available on the Mikran X-band MW Bridge. The function [mw_bridge_att2_prm()](#mw_bridge_att2_prmatten) should be used for Mikran X-band MW Bridge v2. The output is in the form: 'Amplification PRM: 22 dB'.

---

### mw_bridge_cut_off(*cutoff)
```python
mw_bridge_cut_off(cutoff: int) -> none
mw_bridge_cut_off() -> str
```
```
Example: mw_bridge_cut_off(300) sets the cut-off frequency to 300 MHz.
```
This function queries or sets the cut-off frequency (in MHz) of the bridge. If an argument is specified the function sets a new cut-off frequency. If there is no argument, the function returns the current cut-off frequency.<br/>
The valid values are 30, 105, and 300 MHz. The output is in the form: 'Cut-off Frequency: 105 MHz'.

---

### mw_bridge_rotary_vane(*atten, mode)
```python
mw_bridge_rotary_vane(attenuation: float, mode = 'Arbitrary')
mw_bridge_rotary_vane() -> str
```
```
Example: mw_bridge_rotary_vane('10 dB', mode = 'Arbitrary')
sets the attenuation of the rotary vane to 10 dB.
```
This function queries or sets the attenuation (in dB) of the rotary vane attenuator of the bridge. If an argument is specified, the function sets a new attenuation value. If there is no argument, the function returns the current attenuation. The valid range is from 0 to 60 dB with 0.1 dB step.<br/>
There are also two possible mode of the attenuator, that can be selected using the 'mode' key argument. The available modes are: ['Limit', 'Arbitrary']. In 'Limit' mode only two limit values of the attenuation can be used: 0 dB and 60 dB. This mode is usually used for initialization. In 'Arbitrary' mode any attenuation value from the range of 0 to 60 dB with 0.1 dB step can be used. The output is in the form: 'Rotary Vane Attenuation: 10 dB'.<br/>
This function is not available on the Mikran X-band MW Bridge.
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
This function returns the telemetry. The format is DATE; TEMPERATURE; STATE (INIT/WORK).<br/>

---

### mw_bridge_initialize()
```python
mw_bridge_initialize() -> none
```
```
Example: mw_bridge_initialize() resets the bridge to initialization state.
```
This function returns the bridge to initialization state. The initialization state corresponds to ATT1_PRD = 0 dB; ATT2_PRD = 0 dB; FV_CTRL = 0°; FV_PRM = 0°; ATT_PRM = 0 dB; K_PRM = 22 dB for Mikran X-band MW Bridge or ATT2_PRM = 0 dB for Mikran X-band MW Bridge v2; CUT-OFF frequency = 300 MHz; Synthesizer frequency = 1000 MHz; Synthesizer power = OFF.