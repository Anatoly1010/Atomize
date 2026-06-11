# Synthetizers

## Devices

| Device       | Tested  | Connection |
| ------------ | ------- | ---------- |
| **ECC 15K**  | 01/2023 | RS-232     |

## Functions

### synthetizer_name() { #synthetizer_name data-toc-label="synthetizer_name" }

```python
synthetizer_name()    # -> str; device name
```

The function returns device name.

---

### synthetizer_frequency(*freq) { #synthetizer_frequency data-toc-label="synthetizer_frequency" }

```python
synthetizer_frequency()           # -> str (query)
synthetizer_frequency('9 GHz')    # set frequency to 9 GHz
```

This function queries or sets the frequency of the synthetizer. If there is no argument, the function returns the current frequency. If there is an argument, the specified frequency will be set.

**Output format:** `'number'` + `'Hz'` | `'kHz'` | `'MHz'` | `'GHz'`
{: .enum }

**Range (ECC 15K):** `10 MHz` – `15 GHz`
{: .enum }

---

### synthetizer_state(*state) { #synthetizer_state data-toc-label="synthetizer_state" }

```python
synthetizer_state()        # -> str (query)
synthetizer_state('On')    # turn on the synthetizer
```

This function queries or sets the state of the power output. If there is no argument, the function returns the current state. If there is an argument, the specified state will be set.

**Allowed:** `'On'`, `'Off'`
{: .enum }

---

### synthetizer_power(*level) { #synthetizer_power data-toc-label="synthetizer_power" }

```python
synthetizer_power()     # -> int (query)
synthetizer_power(1)    # set power level to 1 arb. u.
```

This function queries or sets the power level. If there is no argument, the function returns the current power level as an integer. If there is an argument, the specified power level will be set. The value of 15 corresponds to the maximum power level.

**Range (ECC 15K):** `0` – `15` arb. u.
{: .enum }

---

### synthetizer_command(command) { #synthetizer_command data-toc-label="synthetizer_command" }

```python
synthetizer_command(command)    # str -> none
```

This function for sending an arbitrary command to the device in a string format. No output is expected.

---

### synthetizer_query(command) { #synthetizer_query data-toc-label="synthetizer_query" }

```python
synthetizer_query(command)    # str -> str
```

This function for sending an arbitrary command to the device in a string format. An output in a string format is expected.
