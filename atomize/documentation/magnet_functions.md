# List of available functions for magnetic field controllers

Bruker BH15 module was rewritten from the [FSC2 module](http://users.physik.fu-berlin.de/~jtt/fsc2/fsc2.html) originally created by Jens Thomas Törring in C. Communication with Bruker ER032M field controller can be achieved using the same module.

```python3
magnet_name()
Arguments: none; Output: string.
```
This function returns device name.
```python3
magnet_setup(start_field, step_field)
Arguments: start_field, step_field = floats; Output: none.
Example: magnet_setup(3500, 10) sets the magnetic field to 3500 G and 
the field step to 10 G for using in sweeps.
```
This function is used to set the start field and the field step used in sweeps. The function expects two floating point arguments both in Gauss.
As it is indicated [here:](http://users.physik.fu-berlin.de/~jtt/fsc2/Magnet-Functions.html#magnet_005fsweep_005fup_0028_0029) for Bruker BH15 field controller for some combinations of the start field and field step size deviations between the requested field and the real field may result of up to 25 mG. If the maximum field deviation was larger than 5 mG at the end of the test run as well as the experiment the maximum field deviation is printed out. To minimize these deviations use a start field that is a multiple of 50 mG and avoid sweeps with more than about 2000 steps away from the start field.
```python3
magnet_field(*field)
Arguments: field = float; Output: float.
Example: magnet_field(1000) sets the magnetic field to 1000 G.
```
This function queries or sets the magnetic field in Gauss. If an argument is specified the function sets a new magnetic field value. If there is no argument the function returns the current magnetic field. For the Bruker BH15 and Bruker ER031M field controllers this function returns the current field setting in Gauss.<br/>
For Bruker BH15 field controller setting a field with this function while also having initialized the magnet using magnet_setup() may result in deviations between the requested field and the real field of up to 25 mG.<br/>
Requesting the current value of the field is only possible, if the function magnet_setup() has been called or a field already has been set.<br/>
```python3
magnet_sweep_up()
Arguments: none; Output: float.
Example: magnet_sweep_up() sweeps up the magnet by the field step value set
in the magnet_setup() function.
```
This function doesn't take an argument and starts sweeping of magentic field up using the field step value specified in magnet_setup() function. It can be used only if the function magnet_setup() has been called before. The function returns the new field value.<br/>
The function is not available for Bruker ER031M field controller.
```python3
magnet_sweep_down()
Arguments: none; Output: float.
Example: magnet_sweep_down() sweeps down the magnet by the field step value set
in the magnet_setup() function.
```
This function doesn't take an argument and starts sweeping of magentic field down using the field step value specified in magnet_setup() function. It can be used only if the function magnet_setup() has been called before. The function returns the new field value.<br/>
The function is not available for Bruker ER031M field controller.
```python3
magnet_reset_field()
Arguments: none; Output: float.
Example: magnet_reset_field() resets the magnetic field to the start field
value.
```
This function resets the magnetic field to the start field value specified in a previous call of magnet_setup(). The function returns the new field value.<br/>
The function is not available for Bruker ER031M field controller.
```python3
magnet_field_step_size(*step)
Arguments: step = float; Output: float.
Example: magnet_field_step_size(10) returns the possible field step size nearest to 10 Gauss
```
This function returns the minimum field step size (in Gauss) if called without an argument and the possible field step size (in Gauss) nearest to the argument.<br/>
The function is not available for Bruker ER031M field controller.
```python3
magnet_command(command)
Arguments: command = string; Output: none.
```
This function for sending an arbitrary command to the device in a string format. No output is expected.<br/>

