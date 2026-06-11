# Microwave Bridges

## Devices

| Device                            | Tested  | Connection      |
| --------------------------------- | ------- | --------------- |
| **Micran X-band MW Bridge**       | 06/2021 | TCP/IP Socket   |
| **Micran X-band MW Bridge v2**    | 12/2022 | TCP/IP Socket   |
| **Micran Q-band MW Bridge**       | 12/2023 | TCP/IP Socket   |

## Functions

### mw_bridge_name() { #mw_bridge_name data-toc-label="mw_bridge_name" }

```python
mw_bridge_name()    # -> str; device name
```

This function returns device name.

---

### mw_bridge_open() { #mw_bridge_open data-toc-label="mw_bridge_open" }

```python
mw_bridge_open()    # -> 'DEVICE OPENED' | 'DEVICE NOT FOUND'
```

This function is only available for Micran Q-band MW Bridge. It opens the driver of the microwave bridge and should be called before any other functions.

---

### mw_bridge_close() { #mw_bridge_close data-toc-label="mw_bridge_close" }

```python
mw_bridge_close()    # -> 'DEVICE CLOSED'
```

This function is only available for Micran Q-band MW Bridge. It closes the driver of the microwave bridge and should be called after the last operation function in the script is executed.

---

### mw_bridge_synthesizer(*freq) { #mw_bridge_synthesizer data-toc-label="mw_bridge_synthesizer" }

```python
mw_bridge_synthesizer()        # -> 'Frequency: {int} MHz' (query)
mw_bridge_synthesizer(9750)    # set synthesizer frequency to 9750 MHz
```

This function queries or sets the frequency of the synthesizer in MHz. If an argument is specified, the function sets a new frequency value. If there is no argument, the function returns the current frequency in the form of `'Frequency: 9750 MHz'`. The range can be modified in the configuration file.

**Range:** `9000 MHz` – `10000 MHz` (1 MHz step)
{: .enum }

---

### mw_bridge_att1_prd(*atten) { #mw_bridge_att1_prd data-toc-label="mw_bridge_att1_prd" }

```python
mw_bridge_att1_prd()       # -> 'Attenuator PRD1: {float} dB' (query)
mw_bridge_att1_prd(1.5)    # set PRD1 attenuation to 1.5 dB
```

This function queries or sets the attenuation (in dB) of the first attenuator in the PRD part of the bridge. If an argument is specified, the function sets a new attenuation value. If there is no argument, the function returns the current attenuation. The output is in the form of `'Attenuator PRD1: 15.5 dB'`.

**Range:** `0 dB` – `31.5 dB` (0.5 dB step)
{: .enum }

---

### mw_bridge_att2_prd(*atten) { #mw_bridge_att2_prd data-toc-label="mw_bridge_att2_prd" }

```python
mw_bridge_att2_prd()       # -> 'Attenuator PRD2: {float} dB' (query)
mw_bridge_att2_prd(2.0)    # set PRD2 attenuation
```

This function queries or sets the attenuation (in dB) of the second attenuator in the PRD part of the bridge. If an argument is specified, the function sets a new attenuation value. If there is no argument, the function returns the current attenuation. The output is in the form: `'Attenuator PRD2: 15.5 dB'`.

**Range:** `0 dB` – `31.5 dB` (0.5 dB step)
{: .enum }

!!! note
    This function is not available for Micran Q-band MW bridge.

---

### mw_bridge_fv_ctrl(*phase) { #mw_bridge_fv_ctrl data-toc-label="mw_bridge_fv_ctrl" }

```python
mw_bridge_fv_ctrl()       # -> 'Phase CTRL: {float} deg' (query)
mw_bridge_fv_ctrl(100)    # set CTRL phase to 100 deg
```

This function queries or sets the phase (in deg) of the phase shifter in the CTRL part of the bridge. If an argument is specified, the function sets a new phase value. If there is no argument, the function returns the current phase. The output is in the form: `'Phase CTRL: 5.625 deg'`. If there is no phase setting fitting the argument the nearest available value is used and warning is printed.

**Range:** `0°` – `354.375°` (5.625° step)
{: .enum }

!!! note
    This function is not available for Micran Q-band MW bridge.

---

### mw_bridge_fv_prm(*phase) { #mw_bridge_fv_prm data-toc-label="mw_bridge_fv_prm" }

```python
mw_bridge_fv_prm()      # -> 'Phase PRM: {float} deg' (query)
mw_bridge_fv_prm(50)    # set PRM phase
```

This function queries or sets the phase (in deg) of the phase shifter in the PRM part of the bridge. If an argument is specified, the function sets a new phase value. If there is no argument the function returns the current phase. The output is in the form: `'Phase PRM: 5.625 deg'`. If there is no phase setting fitting the argument the nearest available value is used and warning is printed.

**Range:** `0°` – `354.375°` (5.625° step)
{: .enum }

!!! note
    This function is not available for Micran Q-band MW bridge.

---

### mw_bridge_att_prm(*atten) { #mw_bridge_att_prm data-toc-label="mw_bridge_att_prm" }

```python
mw_bridge_att_prm()     # -> 'Video Attenuation: {int} dB' (query)
mw_bridge_att_prm(2)    # set PRM video attenuation to 2 dB
```

This function queries or sets the attenuation (in dB) of the attenuator in the PRM part of the bridge. If an argument is specified, the function sets a new attenuation value. If there is no argument the function returns the current attenuation. The output is in the form: `'Video Attenuation: 14 dB'`.

**Range:** `0 dB` – `22 dB` (2 dB step)
{: .enum }

---

### mw_bridge_att2_prm(*atten) { #mw_bridge_att2_prm data-toc-label="mw_bridge_att2_prm" }

```python
mw_bridge_att2_prm()     # -> 'Video Attenuation 2: {int} dB' (query)
mw_bridge_att2_prm(2)    # set PRM video attenuation 2 to 2 dB
```

This function queries or sets the attenuation (in dB) of the attenuator 2 in the PRM part of the bridge. If an argument is specified, the function sets a new attenuation value. If there is no argument, the function returns the current attenuation. The output is in the form: `'Video Attenuation 2: 14 dB'`.

**Range:** `0 dB` – `31.5 dB` (0.5 dB step)
{: .enum }

!!! note
    This function is only available for the Micran X-band MW Bridge v2 and
    Micran Q-band MW Bridge. The function [`mw_bridge_k_prm()`](#mw_bridge_k_prm)
    should be used for Micran X-band MW Bridge.

---

### mw_bridge_k_prm(*amplif) { #mw_bridge_k_prm data-toc-label="mw_bridge_k_prm" }

```python
mw_bridge_k_prm()     # -> 'Amplification PRM: {int} dB' (query)
mw_bridge_k_prm(0)    # set amplification to 0 dB
```

This function queries or sets the amplification coefficient (in dB) in the PRM part of the bridge. If an argument is specified, the function sets a new amplification value. If there is no argument, the function returns the current amplification. The output is in the form: `'Amplification PRM: 22 dB'`.

**Allowed:** `0 dB`, `22 dB`
{: .enum }

!!! note
    This function is only available for the Micran X-band MW Bridge. The
    function [`mw_bridge_att2_prm()`](#mw_bridge_att2_prm) should be used
    for Micran X-band MW Bridge v2 and Micran Q-band MW Bridge.

---

### mw_bridge_att_pin(*atten) { #mw_bridge_att_pin data-toc-label="mw_bridge_att_pin" }

```python
mw_bridge_att_pin()      # -> 'PIN Attenuator: {int} dB' (query)
mw_bridge_att_pin(10)    # set PIN attenuation to 10 dB
```

This function queries or sets the attenuation (in dB) of the pin attenuator of the bridge. If an argument is specified, the function sets a new attenuation. If there is no argument, the function returns the current attenuation. The output is in the form: `'PIN Attenuator: 10 dB'`.

**Range:** `0 dB` – `36 dB`
{: .enum }

!!! note
    This function is only available for the Micran Q-band MW Bridge.

---

### mw_bridge_cut_off(*cutoff) { #mw_bridge_cut_off data-toc-label="mw_bridge_cut_off" }

```python
mw_bridge_cut_off()       # -> 'Cut-off Frequency: {int} MHz' (query)
mw_bridge_cut_off(300)    # set cut-off frequency to 300 MHz
```

This function queries or sets the cut-off frequency (in MHz) of the bridge. If an argument is specified the function sets a new cut-off frequency. If there is no argument, the function returns the current cut-off frequency. The output is in the form: `'Cut-off Frequency: 105 MHz'`.

**Allowed:** `30 MHz`, `105 MHz`, `300 MHz`
{: .enum }

---

### mw_bridge_rotary_vane(*atten, mode) { #mw_bridge_rotary_vane data-toc-label="mw_bridge_rotary_vane" }

```python
mw_bridge_rotary_vane()    # -> 'Rotary Vane Attenuation: {int} dB'
mw_bridge_rotary_vane('10 dB', mode='Arbitrary') # set rotary vane to 10 dB
```

This function queries or sets the attenuation (in dB) of the rotary vane attenuator of the bridge. If an argument is specified, the function sets a new attenuation value. If there is no argument, the function returns the current attenuation. The output is in the form: `'Rotary Vane Attenuation: 10 dB'`.

There are also two possible mode of the attenuator, that can be selected using the `'mode'` key argument. In `'Limit'` mode only two limit values of the attenuation can be used: 0 dB and 60 dB. This mode is usually used for initialization. In `'Arbitrary'` mode any attenuation value from the range can be used.

For consistency, it is always best to end the experimental script at 60 dB attenuation:

```python
mw_bridge_rotary_vane(60, mode='Limit')
```

**Allowed mode:** `'Limit'`, `'Arbitrary'`
{: .enum }

**Range (Arbitrary):** `0 dB` – `60 dB` (0.1 dB step)
{: .enum }

!!! note
    This function is not available on the Micran X-band MW Bridge.

---

### mw_bridge_telemetry() { #mw_bridge_telemetry data-toc-label="mw_bridge_telemetry" }

```python
mw_bridge_telemetry()    # -> str; telemetry
```

This function returns the telemetry. The format for Micran X-band MW Bridge and Micran X-band MW Bridge v2 is `DATE; TEMPERATURE; STATE (INIT/WORK)`.

The format for Micran Q-band MW Bridge is `DATE; ANSWER RECEIVED; PARAMS UPDATED; TI TOO SHORT; HPA TOO LONG; HPA ON INCORRECT; HPA OFF INCORRECT; EXT CLOCK CORRECT; SHAPER TOO LONG; DUTY CYCLE TOO LOW`. All parameters except DATE has 0 (Off) and 1 (On) format.

---

### mw_bridge_initialize() { #mw_bridge_initialize data-toc-label="mw_bridge_initialize" }

```python
mw_bridge_initialize()        # reset bridge to initialization state
mw_bridge_initialize('On')    # Q-band: turn on init + several options
```

This function returns the bridge to initialization state. The initialization state corresponds to `ATT1_PRD = 0 dB`; `ATT2_PRD = 0 dB`; `FV_CTRL = 0°`; `FV_PRM = 0°`; `ATT_PRM = 0 dB`; `K_PRM = 22 dB` for Micran X-band MW Bridge or `ATT2_PRM = 0 dB` for Micran X-band MW Bridge v2; CUT-OFF frequency = 300 MHz; Synthesizer frequency = 1000 MHz; Synthesizer power = OFF.

For Micran Q-band MW Bridge a modified version is used that accepts a `state` argument; it initializes the bridge and turns on several options, namely "Internal Start ON", "External Clock ON", "Receiver LO Amp ON", "AWG LO Amp ON".

**Allowed state (Q-band):** `'On'`, `'Off'`
{: .enum }

---

### mw_bridge_reset() { #mw_bridge_reset data-toc-label="mw_bridge_reset" }

```python
mw_bridge_reset()    # reset error flags
```

This function is only available for Micran Q-band MW Bridge. It resets all the errors occured during the device operation. The status of these error flags can be checked using the [`mw_bridge_telemetry()`](#mw_bridge_telemetry) function.
