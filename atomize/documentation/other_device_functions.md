# List of available functions for other devices

## Magnetic Field Controllers
```python3
magnet_name()
#### Arguments: none; Output: string(name).
```
This function returns device name.
```python3
magnet_field(*field)
Arguments: float; Output: float.
```
This function queries or sets the magnetic field in Gauss. If an argument is specified the function sets a new magnetic field value. If there is no argument the function returns the current magnetic field.<br/>
For ER031M the function can be used only without arguments.<br/>
```python3
Example: magnet_field('1000') sets the magnetic field to 1000 G.
```
```python3
magnet_command(command)
Arguments: string(command); Output: none.
```
This function for sending an arbitrary command from a programming guide to the device in a string format. No output is expected.<br/>

## Balances
```python3
balance_weight()
```

## Other
## Solid-sate Relay RODOS-10N (ethernet)
```python3
turn_on(number)
```
```python3
turn_off(number)
```
