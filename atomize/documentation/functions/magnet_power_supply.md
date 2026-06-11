# Magnet Power Supplies

## Devices

| Device                   | Tested   | Connection |
| ------------------------ | -------- | ---------- |
| **Cryomagnetics 4G**     | Untested | Ethernet   |

Please note, that there are several default settings for working with the Cryomagnetics 4G power supply. All of them must be specified in the configuration file. The parameters [range](#magnet_power_supply_range), [rate](#magnet_power_supply_sweep_rate), [rate_fast](#magnet_power_supply_sweep_rate), [voltage_limit](#magnet_power_supply_voltage_limit), [units](#magnet_power_supply_units), [channel](#magnet_power_supply_select_channel) are discussed in details in the corresponding functions. Field/current conversion parameter `field/current` is given in Gauss/Amps. The default configuration file is as follows:

```ini
[SPECIFIC]
max_current   = 100
min_current   = -100
range         = 40 60 85 93
rate          = 0.01 0.01 0.007 0.005 0.005
rate_fast     = 5.0
voltage_limit = 1
units         = G
max_channels  = 2
channel       = CH1
field/current = 1258
```

The following functions are used in the device initialization process:

```python
magnet_power_supply_control_mode('Remote')
magnet_power_supply_range(range)
magnet_power_supply_sweep_rate(rate, rate_fast)
magnet_power_supply_voltage_limit(voltage_limit)
magnet_power_supply_units(units)
magnet_power_supply_select_channel(channel)
magnet_power_supply_low_sweep_limit(low_sweep_limit)
magnet_power_supply_upper_sweep_limit(upper_sweep_limit)
magnet_power_supply_sweep('Zero', 'Slow')
```

## Functions

### magnet_power_supply_name() { #magnet_power_supply_name data-toc-label="magnet_power_supply_name" }

```python
magnet_power_supply_name()    # -> str; device name
```

This function returns device name.

---

### magnet_power_supply_select_channel(*channel) { #magnet_power_supply_select_channel data-toc-label="magnet_power_supply_select_channel" }

```python
magnet_power_supply_select_channel()         # -> str (query)
magnet_power_supply_select_channel('CH1')    # select channel 1 for subsequent commands
```

This function queries (if called without argument) or selects (if called with one argument) the module (channel) for subsequent remote commands. When a second channel is selected on a device with only one module installed, an error is returned. The output is returned as a string `'CH1'` or `'CH2'`.

**Allowed:** `'CH1'`, `'CH2'`
{: .enum }

---

### magnet_power_supply_low_sweep_limit(*limit) { #magnet_power_supply_low_sweep_limit data-toc-label="magnet_power_supply_low_sweep_limit" }

```python
magnet_power_supply_low_sweep_limit()      # -> str (query)
magnet_power_supply_low_sweep_limit(10)    # set lower limit for next sweep down
```

This function queries (if called without argument) or sets (if called with one argument) the current limit used for the next sweep down by the [`magnet_power_supply_sweep()`](#magnet_power_supply_sweep) function. The value must be supplied in the selected [units](#magnet_power_supply_units) – Amperes or Field (kG). An error will be returned if this value is greater than the [upper sweep limit](#magnet_power_supply_upper_sweep_limit). The output as a string is also returned in the selected units – Amperes or Field (kG), e.g. `'0.000kG'`.

---

### magnet_power_supply_upper_sweep_limit(*limit) { #magnet_power_supply_upper_sweep_limit data-toc-label="magnet_power_supply_upper_sweep_limit" }

```python
magnet_power_supply_upper_sweep_limit()      # -> str (query)
magnet_power_supply_upper_sweep_limit(10)    # set upper limit for next sweep up
```

This function queries (if called without argument) or sets (if called with one argument) the current limit used for the next sweep up by the [`magnet_power_supply_sweep()`](#magnet_power_supply_sweep) function. The value must be supplied in the selected [units](#magnet_power_supply_units) – Amps or Field (kG). An error will be returned if this value is lower than the [low sweep limit](#magnet_power_supply_low_sweep_limit). The output as a string is also returned in the selected [units](#magnet_power_supply_units) – Amperes or Field (kG), e.g. `'0.500kG'`.

---

### magnet_power_supply_voltage_limit(*limit) { #magnet_power_supply_voltage_limit data-toc-label="magnet_power_supply_voltage_limit" }

```python
magnet_power_supply_voltage_limit()     # -> str (query)
magnet_power_supply_voltage_limit(1)    # set output voltage limit to 1 V
```

This function queries (if called without argument) or sets (if called with one argument) the power supply output voltage limit. The output is returned as a string, e.g. `'4.750V'`.

**Range (Cryomagnetics 4G):** `0 V` – `10 V`
{: .enum }

---

### magnet_power_supply_sweep_rate(*rate) { #magnet_power_supply_sweep_rate data-toc-label="magnet_power_supply_sweep_rate" }

```python
magnet_power_supply_sweep_rate()    # -> numpy.array(6) (query)
magnet_power_supply_sweep_rate(0.01, 0.01, 0.007, 0.005, 0.005, 5.0)
# charge rates in Amps/second for the different ranges of the power supply
```

This function queries (if called without argument) or sets (if called with six arguments) the charge rates in Amps/second for the [different ranges](#magnet_power_supply_range) of the power supply. The first argument corresponds to the first range, the second argument to the second range, etc. The last argument sets the Fast mode sweep rate. The output is returned as a numpy array of six elements corresponding to the different ranges.

---

### magnet_power_supply_range(*range) { #magnet_power_supply_range data-toc-label="magnet_power_supply_range" }

```python
magnet_power_supply_range()                  # -> numpy.array(4) (query)
magnet_power_supply_range(40, 60, 85, 93)    # set upper limits for charge rate ranges (A)
```

This function queries (if called without argument) or sets (if called with four arguments) the upper limits for a [charge rate](#magnet_power_supply_sweep_rate) ranges in Amperes. The first argument corresponds to the Range 0 that starts at zero and ends at the limit provided. Range 1 starts at the Range 0 limit and ends at the Range 1 limit provided. The same for Range 2 and 3. Range 4 starts at the Range 3 limit and ends at the maximum output power of the power supply. The output is returned as a numpy array of five elements corresponding to the different ranges, including the maximum output power of the power supply as the last element.

---

### magnet_power_supply_sweep(*sweep) { #magnet_power_supply_sweep data-toc-label="magnet_power_supply_sweep" }

```python
magnet_power_supply_sweep()                # -> str; present sweep mode
magnet_power_supply_sweep('Up', 'Fast')    # sweep up at fast rate
```

This function causes (if called with one argument) the power supply to sweep the output current from the present current to the specified limit at the applicable charge rate set by the [range](#magnet_power_supply_range) and [rate](#magnet_power_supply_sweep_rate) commands. If the second argument `'Fast'` is given, the fast mode [rate](#magnet_power_supply_sweep_rate) will be used instead of a rate selected from the output current range. The second argument `'Slow'` is required to change from fast sweep. The first argument `'Up'` sweeps to the Upper limit; `'Down'` sweeps to the Lower limit; `'Zero'` discharges the supply. If the function is called without arguments, it returns the present sweep mode as a string. If sweep is not active then `'Standby'` is returned.

**Allowed sweep:** `'Up'`, `'Down'`, `'Pause'`, `'Zero'`
{: .enum }

**Allowed speed:** `'Fast'`, `'Slow'`
{: .enum }

---

### magnet_power_supply_units(*units) { #magnet_power_supply_units data-toc-label="magnet_power_supply_units" }

```python
magnet_power_supply_units()       # -> str (query)
magnet_power_supply_units('A')    # set units to Amps
```

This function queries (if called without argument) or sets (if called with one argument) the units to be used for all input and display operations. Units can be set to Amps (`'A'`) or Gauss (`'G'`). The unit will autorange to display Gauss, Kilogauss or Tesla. The output is returned as a string, e.g. `'A'`.

**Allowed:** `'A'`, `'G'`
{: .enum }

---

### magnet_power_supply_persistent_current(*current) { #magnet_power_supply_persistent_current data-toc-label="magnet_power_supply_persistent_current" }

```python
magnet_power_supply_persistent_current()         # -> str (query)
magnet_power_supply_persistent_current(17.93)    # set magnet current shown on display
```

This function queries (if called without argument) or sets (if called with one argument) the magnet current shown on the display. The supply must be in standby or a command error will be returned. The value must be supplied in the selected [units](#magnet_power_supply_units) – Amperes or Field (kG). The output is returned as a string, e.g. `'17.13A'`. If the [persistent switch heater](#magnet_power_supply_persistent_heater) is `'On'` the magnet current returned will be the same as the power supply output current. If the [persistent switch heater](#magnet_power_supply_persistent_heater) is `'Off'`, the magnet current will be the value of the power supply output current when the [persistent switch heater](#magnet_power_supply_persistent_heater) was last turned off.

---

### magnet_power_supply_mode() { #magnet_power_supply_mode data-toc-label="magnet_power_supply_mode" }

```python
magnet_power_supply_mode()    # -> 'Shim' | 'Manual'
```

This function returns the present operating mode of the power supply as a string, e.g. `'Manual'`.

**Allowed:** `'Shim'`, `'Manual'`
{: .enum }

---

### magnet_power_supply_control_mode(mode) { #magnet_power_supply_control_mode data-toc-label="magnet_power_supply_control_mode" }

```python
magnet_power_supply_control_mode('Remote')    # take control via remote interface
```

This function sets the control mode of the power supply. Please note that the Cryomagnetics 4G must be switched to `'Remote'` mode to change the default settings.

**Allowed:** `'Remote'`, `'Local'`
{: .enum }

---

### magnet_power_supply_current() { #magnet_power_supply_current data-toc-label="magnet_power_supply_current" }

```python
magnet_power_supply_current()    # -> str; output current in present units, e.g. '5A'
```

This function returns the power supply output current (or magnetic field strength) in the present [units](#magnet_power_supply_units) as a string, e.g. `'5A'`.

---

### magnet_power_supply_voltage() { #magnet_power_supply_voltage data-toc-label="magnet_power_supply_voltage" }

```python
magnet_power_supply_voltage()    # -> str; present output voltage, e.g. '10.000V'
```

This function returns the present power supply output voltage as a string, e.g. `'10.0V'`.

**Range:** `-12.80 V` – `+12.80 V`
{: .enum }

---

### magnet_power_supply_magnet_voltage() { #magnet_power_supply_magnet_voltage data-toc-label="magnet_power_supply_magnet_voltage" }

```python
magnet_power_supply_magnet_voltage()    # -> str; present magnet voltage, e.g. '3.0 V'
```

This function returns the present magnet voltage as a string, e.g. `'3.0V'`.

**Range:** `-10 V` – `+10 V`
{: .enum }

---

### magnet_power_supply_persistent_heater(*state) { #magnet_power_supply_persistent_heater data-toc-label="magnet_power_supply_persistent_heater" }

```python
magnet_power_supply_persistent_heater()         # -> str (query)
magnet_power_supply_persistent_heater('Off')    # turn off the persistent heater
```

This function queries (if called without argument) or sets (if called with one argument) the state of the persistent switch heater. Note that the switch heater current can only be set in the Magnet Menu using the keypad. This command should normally be used only when the supply output is stable and matched to the magnet current. The output is either `'On'` or `'Off'`.

**Allowed:** `'On'`, `'Off'`
{: .enum }

---

### magnet_power_supply_command(command) { #magnet_power_supply_command data-toc-label="magnet_power_supply_command" }

```python
magnet_power_supply_command(command)    # str -> none
```

This function sends an arbitrary command from a programming guide to the device in a string format. No output is expected.

---

### magnet_power_supply_query(command) { #magnet_power_supply_query data-toc-label="magnet_power_supply_query" }

```python
magnet_power_supply_query(command)    # str -> str
```

This function sends an arbitrary command from a programming guide to the device in a string format. An output in a string format is expected.
