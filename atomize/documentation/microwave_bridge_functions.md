# List of available functions for microwave bridge controllers

Available devices:
- Mikran X-band MW Bridge (TCP/IP Socket); Tested 06/2021

Functions:
- [mw_bridge_name()](#mw_bridge_name)<br/>
- [mw_bridge_synthesizer(*freq)](#mw_bridge_synthesizerfreq)<br/>
- [mw_bridge_att1_prd(*atten)](#mw_bridge_att1_prdatten)<br/>
- [mw_bridge_att2_prd(*atten)](#mw_bridge_att2_prdatten)<br/>
- [mw_bridge_fv_ctrl(*phase)](#mw_bridge_fv_ctrlphase)<br/>
- [mw_bridge_fv_prm(*phase)](#mw_bridge_fv_prmphase)<br/>
- [mw_bridge_att_prm(*atten)](#mw_bridge_att_prmatten)<br/>
- [mw_bridge_k_prm(*amplif)](#mw_bridge_k_prmamplif)<br/>
- [mw_bridge_cut_off(*cutoff)](#mw_bridge_cut_offcutoff)<br/>
- [mw_bridge_telemetry()](#mw_bridge_telemetry)<br/>
- [mw_bridge_initialize()](#mw_bridge_initialize)<br/>

### mw_bridge_name()
```python3
mw_bridge_name()
Arguments: none; Output: string.
```
This function returns device name.
### mw_bridge_synthesizer(*freq)
```python3
mw_bridge_synthesizer(*freq)
Arguments: none or freq = frequency (MHz); Output: frequency (MHz).
Example: mw_bridge_synthesizer('9750') sets the frequency of the synthesizer to 9750 MHz.
```
This function queries or sets the frequency of the synthesizer in MHz. If an argument is specified the function sets a new frequency value. If there is no argument the function returns the current frequency. The valid range of frequency is from 9000 to 10000 MHz with 1 MHz step.
### mw_bridge_att1_prd(*atten)
```python3
mw_bridge_att1_prd(*atten)
Arguments: none or atten = attenuation (dB); Output: attenuation (dB).
Example: mw_bridge_att1_prd('1.5') sets the attenuation to 1.5 dB for the first
attenuator in the PRD part of the bridge.
```
This function queries or sets the attenuation (in dB) of the first attenuator in the PRD part of the bridge. If an argument is specified the function sets a new attenuation value. If there is no argument the function returns the current attenuation. The valid range is from 0 to 31.5 dB with 0.5 dB step.
### mw_bridge_att2_prd(*atten)
```python3
mw_bridge_att2_prd(*atten)
Arguments: none or atten = attenuation (dB); Output: attenuation (dB).
Example: mw_bridge_att2_prd() returns the attenuation for the second attenuator
in the PRD part of the bridge.
```
This function queries or sets the attenuation (in dB) of the second attenuator in the PRD part of the bridge. If an argument is specified the function sets a new attenuation value. If there is no argument the function returns the current attenuation. The valid range is from 0 to 31.5 dB with 0.5 dB step.
### mw_bridge_fv_ctrl(*phase)
```python3
mw_bridge_fv_ctrl(*phase)
Arguments: none or phase = phase (deg); Output: phase (deg).
Example: mw_bridge_fv_ctrl('100') sets the phase shifter in the CTRL part of the bridge to 100 deg.
```
This function queries or sets the phase (in deg) of the phase shifter in the CTRL part of the bridge. If an argument is specified the function sets a new phase value. If there is no argument the function returns the current phase. The valid range is from 0 to 354.375° with 5.625° step.
### mw_bridge_fv_prm(*phase)
```python3
mw_bridge_fv_prm(*phase)
Arguments: none or phase = phase (deg); Output: phase (deg).
Example: mw_bridge_fv_prm() returns the phase in the PRM part of the bridge.
```
This function queries or sets the phase (in deg) of the phase shifter in the PRM part of the bridge. If an argument is specified the function sets a new phase value. If there is no argument the function returns the current phase. The valid range is from 0 to 354.375° with 5.625° step.
### mw_bridge_att_prm(*atten)
```python3
mw_bridge_att_prm(*atten)
Arguments: none or atten = attenuation (dB); Output: attenuation (dB).
Example: mw_bridge_att_prm('2 dB') sets the attenuation to 2 dB for the
attenuator in the PRM part of the bridge.
```
This function queries or sets the attenuation (in dB) of the attenuator in the PRM part of the bridge. If an argument is specified the function sets a new attenuation value. If there is no argument the function returns the current attenuation. The valid range is from 0 to 22 dB with 2 dB step.
### mw_bridge_k_prm(*amplif)
```python3
mw_bridge_k_prm(*amplif)
Arguments: none or amplif = amplification (dB); Output: amplification (dB).
Example: mw_bridge_k_prm('0 dB') sets the amplification coefficient to 0 dB.
```
This function queries or sets the amplification coefficient (in dB) in the PRM part of the bridge. If an argument is specified the function sets a new amplification value. If there is no argument the function returns the current amplification. The valid values are 0 and 22 dB.
### mw_bridge_cut_off(*cutoff)
```python3
mw_bridge_cut_off(*cutoff)
Arguments: none or cutoff = cut-off frequency (MHz);
Output: cut-off frequency (MHz).
Example: mw_bridge_cut_off('300') sets the cut-off frequency to 300 MHz.
```
This function queries or sets the cut-off frequency (in MHz) of the bridge. If an argument is specified the function sets a new cut-off frequency. If there is no argument the function returns the current cut-off frequency. The valid values are 30, 105, and 300 MHz.
### mw_bridge_telemetry()
```python3
mw_bridge_telemetry()
Arguments: none; Output: telemtry string.
Example: mw_bridge_telemetry() returns the telemetry.
```
This function returns the telemetry. The format is DATE; TEMPERATURE; STATE (INIT/WORK).<br/>
### mw_bridge_initialize()
```python3
mw_bridge_initialize()
Arguments: none; Output: none.
Example: mw_bridge_initialize() resets the bridge to initialization state.
```
This function returns the bridge to initialization state. The initialization state corresponds to ATT1_PRD = 0 dB; ATT2_PRD = 0 dB; FV_CTRL = 0°; FV_PRM = 0°; ATT_PRM = 0 dB; K_PRM = 22 dB; CUT-OFF frequency = 300 MHz; Synthesizer frequency = 1000 MHz; Synthesizer power = OFF.


