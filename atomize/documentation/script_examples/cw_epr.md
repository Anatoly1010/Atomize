# CW EPR

Assume that we have built a continuous wave (CW) EPR spectrometer and now would like to realize the ability to record CW EPR spectra under different experimental conditions. Without going into detail, recording the EPR spectrum is quite simple: using a lock-in amplifier, it is necessary to measure the amplitude of the signal from the detector located in the microwave bridge at different values of the external magnetic field. The signal is caused by microwave power absorption by the spin system, observed under resonant conditions. To increase the signal to noise ratio, external magnetic field modulation is typically used, requiring the use of the lock-in detection scheme. To make the setup slightly more advanced, we will also add the possibility to measure the exact frequency of the microwave source using a frequency counter. A schematic representation of the main principles of CW EPR spectroscopy, a scheme of a possible experimental setup, and the experimental flow are shown in the figure:

![Figure_3](../images/Figure_3.png)

---

The first part is the import and initialization of the necessary devices and other auxiliary modules:

```python
# Lock-in amplifier (Stanford Research Systems SR-860),
# magnetic field controller (Bruker BH-15),
# frequency counter (Agilent 53131a)
import atomize.device_modules.SR_860 as sr
import atomize.device_modules.BH_15 as bh
import atomize.device_modules.Agilent_53131a as ag

# General-purpose methods + file-handling module
import atomize.general_modules.general_functions as general
import atomize.general_modules.csv_opener_saver_tk_kinter as openfile

# Other libraries
import numpy as np

# Initialize device modules
file_handler = openfile.Saver_Opener()
ag53131a     = ag.Agilent_53131a()
sr860        = sr.SR_860()
bh15         = bh.BH_15()
```

---

After that, all the devices should be properly configured and the remaining experimental parameters defined, such as a range of external magnetic field, arrays for storing the obtained data, etc. Devices are configured using the appropriate methods from the device classes. For the rest, standard Python code can be used:

```python
# Spectrum acquisition parameters
START_FIELD = 3000
END_FIELD   = 4000
FIELD_STEP  = 1
SCANS       = 1

# Arrays for storing data
points = int((END_FIELD - START_FIELD) / FIELD_STEP) + 1
data   = np.zeros(points)
x_axis = np.linspace(START_FIELD, END_FIELD, num=points)

# Configure the devices
bh15.magnet_setup(100, FIELD_STEP)
field = bh15.magnet_field(START_FIELD)

sr860.lock_in_time_constant('30 ms')
sr860.lock_in_sensitivity('10 mV')
sr860.lock_in_ref_amplitude('0.5')
sr860.lock_in_phase(159.6)
sr860.lock_in_ref_frequency(100000)

ag53131a.freq_counter_digits(8)
ag53131a.freq_counter_stop_mode('Digits')
```

---

Finally, we are ready to measure the spectrum and plot the results. This can be done in one or two Python loops, depending on whether multiple identical scans are required, as shown below. Due to the user-friendly names of the methods of the device modules, the described sequence of actions is understandable to users, even if they do not have significant programming experience. The script usually ends with saving the data.

```python
# Main measurement
for j in general.scans(SCANS):

    i = 0
    # Set the initial magnetic field for this scan
    field = bh15.magnet_field(START_FIELD)

    # Main acquisition loop
    while field <= END_FIELD:

        # Read lock-in data at the current field
        data[i] = (data[i] * (j - 1) + sr860.lock_in_get_data()) / j

        # Update the plot
        general.plot_1d(
            'CW EPR', x_axis, data,
            xname='Field', xscale='G',
            yname='Intensity', yscale='V',
            label='Experiment_1',
            text=f'Scan / Field: {j} / {field}',
        )

        # Step the field
        field = round(FIELD_STEP + field, 3)
        bh15.magnet_field(field)

        i += 1

# Query the microwave frequency
mw_freq = ag53131a.freq_counter_frequency('CH3')

# Reset the magnet to the start field after the experiment
general.message('Script finished')
field = bh15.magnet_field(START_FIELD)

# Save the data
header = 'header for the acquired data'
file_data, file_param = file_handler.create_file_parameters('.param')
file_handler.save_data(
    file_data, np.c_[x_axis, data],
    header=header, mode='w',
)
```
