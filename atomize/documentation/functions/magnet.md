# Magnetic Field Controllers

Bruker BH15 module was rewritten from the [FSC2 module](http://users.physik.fu-berlin.de/~jtt/fsc2/fsc2.html) originally created by Jens Thomas Törring in C. Communication with Bruker ER032M field controller can be achieved using the same module.

## Devices

| Device                                                                                          | Tested  | Connection                                  |
| ----------------------------------------------------------------------------------------------- | ------- | ------------------------------------------- |
| **Bruker BH15**                                                                                 | 01/2021 | GPIB (linux-gpib)                           |
| **Bruker ER032M**                                                                               | —       | GPIB (linux-gpib); available via BH15 module |
| **Bruker ER031M**                                                                               | 01/2021 | RS-232 (Arduino-emulated keyboard)          |
| **[Homemade ITC1](https://patents.google.com/patent/RU2799103C1/en?oq=RU2799103C1)**            | 04/2023 | RS-232                                      |

## Functions

### magnet_name() { #magnet_name data-toc-label="magnet_name" }

```python
magnet_name()    # -> str; device name
```

This function returns device name.

---

### magnet_setup(start_field, step_field) { #magnet_setup data-toc-label="magnet_setup" }

```python
magnet_setup(3500, 10)    # start field 3500 G, step 10 G (for sweeps)
```

This function is used to set the start field and the field step used in sweeps. The function expects two floating point arguments both in Gauss.

As it is indicated [here:](http://users.physik.fu-berlin.de/~jtt/fsc2/Magnet-Functions.html#magnet_005fsweep_005fup_0028_0029) for Bruker BH15 field controller for some combinations of the start field and field step size deviations between the requested field and the real field may result of up to 25 mG. If the maximum field deviation was larger than 5 mG at the end of the test run as well as the experiment the maximum field deviation is printed out. To minimize these deviations use a start field that is a multiple of 50 mG and avoid sweeps with more than about 2000 steps away from the start field.

!!! note
    The function is available for ITC1 field controller but has no meaning.

---

### magnet_field(*field) { #magnet_field data-toc-label="magnet_field" }

```python
magnet_field()        # -> float (query)
magnet_field(1000)    # set magnetic field to 1000 G
```

This function queries or sets the magnetic field in Gauss. If an argument is specified the function sets a new magnetic field value. If there is no argument the function returns the current magnetic field. For the Bruker BH15 and Bruker ER031M field controllers this function returns the current field setting in Gauss.

For Bruker BH15 field controller setting a field with this function while also having initialized the magnet using [`magnet_setup()`](#magnet_setup) may result in deviations between the requested field and the real field of up to 25 mG.

Requesting the current value of the field is only possible, if the function [`magnet_setup()`](#magnet_setup) has been called or a field already has been set.

---

### magnet_sweep_up() { #magnet_sweep_up data-toc-label="magnet_sweep_up" }

```python
magnet_sweep_up()    # -> float; sweep up by the step from magnet_setup()
```

This function does not take an argument and starts sweeping of magentic field up using the field step value specified in [`magnet_setup()`](#magnet_setup) function. It can be used only if the function [`magnet_setup()`](#magnet_setup) has been called before. The function returns the new field value.

!!! note
    The function is not available for Bruker ER031M and ITC1 field controllers.

---

### magnet_sweep_down() { #magnet_sweep_down data-toc-label="magnet_sweep_down" }

```python
magnet_sweep_down()    # -> float; sweep down by the step from magnet_setup()
```

This function does not take an argument and starts sweeping of magentic field down using the field step value specified in [`magnet_setup()`](#magnet_setup) function. It can be used only if the function [`magnet_setup()`](#magnet_setup) has been called before. The function returns the new field value.

!!! note
    The function is not available for Bruker ER031M and ITC1 field controllers.

---

### magnet_reset_field() { #magnet_reset_field data-toc-label="magnet_reset_field" }

```python
magnet_reset_field()    # -> float; reset to start field from magnet_setup()
```

This function resets the magnetic field to the start field value specified in a previous call of [`magnet_setup()`](#magnet_setup). The function returns the new field value.

!!! note
    The function is not available for Bruker ER031M and ITC1 field controllers.

---

### magnet_field_step_size(*step) { #magnet_field_step_size data-toc-label="magnet_field_step_size" }

```python
magnet_field_step_size()      # -> float; minimum field step size in G
magnet_field_step_size(10)    # -> float; nearest possible step to 10 G
```

This function returns the minimum field step size (in Gauss) if called without an argument and the possible field step size (in Gauss) nearest to the argument.

!!! note
    The function is not available for Bruker ER031M and ITC1 field controllers.

---

### magnet_command(command) { #magnet_command data-toc-label="magnet_command" }

```python
magnet_command(command)    # str -> none
```

This function for sending an arbitrary command to the device in a string format. No output is expected.

!!! note
    The function is not available for Bruker ER031M and ITC1 field controllers.
