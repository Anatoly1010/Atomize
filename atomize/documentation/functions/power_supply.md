# Power Supplies

## Devices

| Device                                                 | Tested   | Connection                          |
| ------------------------------------------------------ | -------- | ----------------------------------- |
| **Rigol DP800 Series**                                 | 01/2021  | RS-232, Ethernet                    |
| **Stanford Research DC205**                            | Untested | RS-232                              |
| **Stanford Research PS300 High Voltage Series**        | Untested | RS-232, GPIB (linux-gpib)           |

Please note, that since SR PS310 and PS325 have only GPIB interface, while SR PS350, PS355, PS365, PS370, PS375 have both RS-232 and GPIB, this setting should be specified in the configuration file:

```ini
[SPECIFIC]
rs232 = yes
```

## Functions

### power_supply_name() { #power_supply_name data-toc-label="power_supply_name" }

```python
power_supply_name()    # -> str; device name
```

This function returns device name.

---

### power_supply_voltage(*voltage) { #power_supply_voltage data-toc-label="power_supply_voltage" }

```python
power_supply_voltage('CH1')            # -> str (query)
power_supply_voltage('CH1', '10 V')    # set channel 1 voltage to 10 V
```

This function queries (if called with one argument) or sets (if called with two arguments) the voltage of one of the channels of the power supply. If there is a second argument it will be set as a new voltage. If there is no second argument the current voltage for specified the channel is returned.

Note that this function returns the voltage setting of the instrument, not actual measured voltage. The latter can be achieved with [`power_supply_measure()`](#power_supply_measure) function.

Rigol DP800 power supply series has `['V', 'mV']` as the scaling dictionary.

Stanford Research DC205 has only one channel, however, it should be listed as the first argument for consistency. Also, the available range of SR DC205 depends on the range setting. Check function [`power_supply_range()`](#power_supply_range). Scaling dictionary is `['V', 'mV']`.

Stanford Research PC300 high voltage supply series has only one channel, however, it should be listed as the first argument for consistency. Scaling dictionary is `['kV', 'V']`. The value of voltage to set must match the polarity of the power supply.

**Allowed channels:** `'CH1'`, `'CH2'`, `'CH3'`
{: .enum }

**Output format:** `'number'` + `'kV'` | `'V'` | `'mV'`
{: .enum }

---

### power_supply_current(*current) { #power_supply_current data-toc-label="power_supply_current" }

```python
power_supply_current('CH2')              # -> str (query)
power_supply_current('CH2', '100 mA')    # set channel 2 current to 100 mA
```

This function queries (if called with one argument) or sets (if called with two arguments) the current of one of the channels of the power supply. If there is a second argument it will be set as a new current. If there is no second argument the current for specified the channel is returned.

**Allowed channels:** `'CH1'`, `'CH2'`, `'CH3'`
{: .enum }

**Output format:** `'number'` + `'A'` | `'mA'`
{: .enum }

!!! note
    This function is only supported by Rigol DP800 Series.

---

### power_supply_overvoltage(*voltage) { #power_supply_overvoltage data-toc-label="power_supply_overvoltage" }

```python
power_supply_overvoltage('CH1')            # -> str (query)
power_supply_overvoltage('CH1', '30 V')    # set channel 1 OVP to 30 V
```

This function queries (if called with one argument) or sets (if called with two arguments) the overvoltage protection of one of the channels of the power supply. If there is a second argument it will be set as a new overvoltage protection setting. If there is no second argument the current overvoltage protection setting for specified the channel is returned.

Stanford Research PC300 high voltage supply series has only one channel, however, it should be listed as the first argument for consistency. The value of overvoltage (the voltage limit) to set must match the polarity of the power supply. The overvoltage value must be greater than or equal to the value indicated in [`power_supply_voltage()`](#power_supply_voltage) function.

**Allowed channels:** `'CH1'`, `'CH2'`, `'CH3'`
{: .enum }

**Output format:** `'number'` + `'kV'` | `'V'` | `'mV'`
{: .enum }

!!! note
    This function is not supported by Stanford Research DC205.

---

### power_supply_overcurrent(*current) { #power_supply_overcurrent data-toc-label="power_supply_overcurrent" }

```python
power_supply_overcurrent('CH1')           # -> str (query)
power_supply_overcurrent('CH1', '3 A')    # set channel 1 OCP to 3 A
```

This function queries (if called with one argument) or sets (if called with two arguments) the overcurrent protection of one of the channels of the power supply. If there is a second argument it will be set as a new overcurrent protection setting. If there is no second argument the current overcurrent protection setting for specified the channel is returned.

Stanford Research PC300 high voltage supply series has only one channel, however, it should be listed as the first argument for consistency. The overcurrent (the current limit) value may be set from 0 to 105 % of full scale.

**Allowed channels:** `'CH1'`, `'CH2'`, `'CH3'`
{: .enum }

**Output format:** `'number'` + `'A'` | `'mA'` | `'uA'`
{: .enum }

!!! note
    This function is not supported by Stanford Research DC205.

---

### power_supply_channel_state(*state) { #power_supply_channel_state data-toc-label="power_supply_channel_state" }

```python
power_supply_channel_state('CH1')          # -> str (query)
power_supply_channel_state('CH1', 'On')    # enable output of channel 1
```

This function queries (if called with one argument) or sets (if called with two arguments) the state of the output of one of the channels of the power supply. If there is a second argument it will be set as a new state setting. If there is no second argument the current state setting for the specified channel is returned. The state argument means that the output is enabled (`'On'`) or disabled (`'Off'`).

Stanford Research DC205 has only one channel, however, it should be listed as the first argument for consistency. For SR DC205 in case of using `'100 V'` range, the channel can be turned on only while the safety interlock is closed. See [`power_supply_interlock()`](#power_supply_interlock) function. If the safety interlock is open a warning will be shown and the state remains unchanged.

Stanford Research PC300 high voltage supply series has only one channel, however, it should be listed as the first argument for consistency. The setting `'On'` turns the high voltage ON, provided the front-panel high voltage switch is not in the OFF position. Also this function cannot query the state of the high voltage supply.

**Allowed channels:** `'CH1'`, `'CH2'`, `'CH3'`
{: .enum }

**Allowed state:** `'On'`, `'Off'`
{: .enum }

---

### power_supply_measure(channel) { #power_supply_measure data-toc-label="power_supply_measure" }

```python
# Query voltage, current, and power (optional) measured on the
# output terminal of channel 1.
power_supply_measure('CH1')
```

This function can be called only with one argument and queries the voltage, current and power measured on the output terminal of the specified channel. The function returns measured values in Volts, Amperes, Watts as a python list.

Stanford Research PC300 high voltage supply series has only one channel, however, it should be listed as the first argument for consistency. For these devices the function returns measured values in Volts and Amperes as a python list.

**Allowed channels:** `'CH1'`, `'CH2'`, `'CH3'`
{: .enum }

!!! note
    This function is not supported by Stanford Research DC205.

---

### power_supply_preset(preset) { #power_supply_preset data-toc-label="power_supply_preset" }

```python
power_supply_preset('User1')    # recall preset 'User1'
```

This function can be called only with one argument and allows restoring the instrument to the default setting (`'Default'` argument) or recall the user-defined setting (`'UserN'` arguments).

**Allowed:** `'Default'`, `'User1'`, `'User2'`, `'User3'`
{: .enum }

!!! note
    This function is only supported by Rigol DP800 Series.

---

### power_supply_range(*range) { #power_supply_range data-toc-label="power_supply_range" }

```python
power_supply_range()          # -> str (query)
power_supply_range('10 V')    # set voltage range to 10 V
```

This function is only supported by Stanford Research DC205 and allows to set or query the voltage range setting. If there is an argument it will be set as a new voltage range setting. If there is no argument the current voltage range setting is returned as a string. The values correspond to one of the three range settings: ±1 V, ±10 V, or ±100 V.

**Allowed:** `'1 V'`, `'10 V'`, `'100 V'`
{: .enum }

---

### power_supply_interlock() { #power_supply_interlock data-toc-label="power_supply_interlock" }

```python
power_supply_interlock()    # -> 'On' | 'Off'
```

This function is only supported by Stanford Research DC205 and allows to query the interlock condition. The DC205 is designed with a safety interlock circuit that must be activated for the ±100 V output range to be enabled. To close the interlock, a low impedance circuit must be established between pins 1 and 2 of the rear-panel INTERLOCK header.

---

### power_supply_rear_mode(*mode) { #power_supply_rear_mode data-toc-label="power_supply_rear_mode" }

```python
power_supply_rear_mode()           # -> str (query)
power_supply_rear_mode('Front')    # voltage controlled by front-panel
```

This function is only supported by Stanford Research PS300 high voltage power supply series and allows to set or query the voltage setting mode.

The argument `'Front'` means that the voltage value is controlled by the front-panel setting, while `'Rear'` indicates that the output is controlled by the rear-panel VSET voltage control input. Note that changing the rear_mode value while the high voltage is ON causes the high voltage to be switched OFF.

**Allowed:** `'Front'`, `'Rear'`
{: .enum }

---

### power_supply_command(command) { #power_supply_command data-toc-label="power_supply_command" }

```python
# Sets the voltage and current of CH1 to 5 V and 1 A, respectively.
power_supply_command(':APPL CH1,5,1')
```

This function sends an arbitrary command from a programming guide to the device in a string format. No output is expected.

---

### power_supply_query(command) { #power_supply_query data-toc-label="power_supply_query" }

```python
# Queries the voltage and current setting values of CH1
# (returns e.g. CH1:30V/5A,5.000,1.0000).
power_supply_query(':APPL? CH1')
```

This function sends an arbitrary command from a programming guide to the device in a string format. An output in a string format is expected.
