# Writing Modules

Please, read these rules carefully and try to follow them when writing a new module.<br/>

## Contents
- [Code Convention](#code-convention)<br/>
- [Function Naming](#function-naming)<br/>
- [Function Clustering](#function-clustering)<br/>
- [Device Class](#device-class)<br/>
- [Class __init__() function](#class-__init__-function)<br/>
- [Limits, Ranges, and Dictionaries](#limits-ranges-and-dictionaries)<br/>
- [Configuration Files](#configuration-files)<br/>
- [Device Specific Configuration Parameters](#device-specific-configuration-parameters)<br/>
- [Dimensions](#dimensions)<br/>
- [Script Testing](#script-testing)<br/>

## Code Convention
Atomize tries to adhere to PEP 8 [code convention.](https://www.python.org/dev/peps/pep-0008/)

## Function Naming
It is highly recommended to use pre-existing function names when writing a module for a device class that is already present in Atomize. Also do not forget to change the documentation accordingly, if there are any peculiarities in using of your function.

## Function Clustering
If it is possible, the same function should be able to query and set the 
target value:
```python3
lock_in_time_constant('30 ms')
lock_in_time_constant()
```
In this example the same function lock_in_time_constant() sets and queries the time constant of lock-in amplifier.

## Device Class
All functions should be combined into one class. The class must have the name of the module file:
```python3
# File SR-860.py
class SR_860:
    def function_1(self):
    def function_2(self):
```

## Class __init__() function
The class inizialization function should connect computer to the device. Examples can be found in in atomize/device_modules/ directory. 

## Limits, Ranges, and Dictionaries
Specify ranges and limits for the device inside an __init()__ function of the device class and use (if possible) dictionaries for matching device specific syntax and general high-level Atomize function arguments:
```python3
# auxilary dictionaries
self.current_dict = {'A': 1, 'mA': 1000,}
self.ac_type_dic = {'Norm': "NORMal", 'Ave': "AVER", 'Hres': "HRES",'Peak': "PEAK"}
self.channel_dict = {'CH1': 1, 'CH2': 2, 'CH3': 3,}
```
```python3
# Ranges and limits
self.ref_freq_min = 0.001
self.ref_freq_max = 500000
```

## Configuration Files
Each device should have a configuration file. In this file the communication [protocol settings](https://github.com/Anatoly1010/Atomize/blob/master/atomize/documentation/protocol_settings.md) and device specific parameters (module for a series of the devices) should be specified. Examples can be found in atomize/device_modules/config/ directory. Reading of a configuration file can be done inside an __init()__ function of the device class using a special function from the config_utils.py file:
```python3
import atomize.device_modules.config.config_utils as cutil
# setting path to *.ini file
self.path_current_directory = os.path.dirname(__file__)
self.path_config_file = os.path.join(self.path_current_directory, 'config','SR_860_config.ini')
# configuration data
self.config = cutil.read_conf_util(self.path_config_file)
self.specific_parameters = cutil.read_specific_parameters(self.path_config_file)
```

## Device Specific Configuration Parameters
When you write a module for a series of the devices, it is convenient to specify some parameters in the configuration file. For example, the number of analog channels of an oscilloscope or a temperature controller loop. In this case, the module should work universally at any given values of specific device parameters.
```python3
# config.ini file
[SPECIFIC]
analog_channels = 4
```

## Dimensions
Currently Atomize does not use the dimensions of physical units (current, frequency etc.), instead, special dictionaries are used:
```python3
self.current_dict = {'A': 1, 'mA': 1000,}
```
In order to take into account different scaling factors usually the value and scaling factor are treated independently:
```python3
if scaling in self.current_dict:
    coef = self.current_dict[scaling]
    if curr / coef >= self.current_min and curr / coef <= self.current_max:
        device_write(':SOURce' + str(flag) + ':CURRent' + str(curr / coef))
```
Searching of a key can be done using a special function from the config_utils.py file:
```python3
import atomize.device_modules.config.config_utils as cutil
answer = cutil.search_keys_dictionary(sensitivity_dict, raw_answer)
return answer
```

## Script Testing
There is a test section in Atomize. During the test software checks that an experimental script has appropriate syntax and does not contain logical errors. It means that all the parameters during script execution do not go beyond the device limits. For instance, the test can detect that the field of the magnet is requested to be set to a value that the magnet cannot produce. During the test run the devices are not accessed, calls of the wait() function do not make the program sleep for the requested time, graphics are not drawn etc.<br/>
In order to be able to run a test, one should specify inside a module appropriate values for all the device parameters (since the devices are not accessed) and describe what the function should do during the test run. Typically, it is just different assertions and checkings:
```python3
elif self.test_flag == 'test':
    if len(amplitude) == 1:
        ampl = float(amplitude[0]);
        assert(ampl <= self.ref_ampl_max and ampl >= self.ref_ampl_min), "Incorrect amplitude"
```
The test flag parameter is used to indicate the start of the test:
```python3
if len(sys.argv) > 1:
    self.test_flag = sys.argv[1]
else:
    self.test_flag = 'None'
```

## To Be Continued...


