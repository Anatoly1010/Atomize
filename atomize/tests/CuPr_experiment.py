import os
import sys
import time
from datetime import datetime
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.Lakeshore_335 as ls
import atomize.device_modules.Keysight_3000_Xseries as key
import atomize.device_modules.Agilent_53131a as ag
import atomize.device_modules.BH_15 as bh
import atomize.device_modules.SR_830 as sr

if len(sys.argv) > 1:
    test_flag = sys.argv[1]
else:
    test_flag = 'None'

ag53131a = ag.Agilent_53131a()
ls335 = ls.Lakeshore_335()
t3034 = key.Keysight_3000_Xseries()
bh15 = bh.BH_15()
sr830 = sr.SR_830()

# Step 0. Initialization
start_field = 2450
end_field = 3950
step_field = 2.5

lock_in_sensitivity_standby = '1 V'
lock_in_sensitivity_operate = '100 mV'
lock_in_time_constant = '10 ms'
lock_in_phase = 159.6
lock_in_freq = 100000
lock_in_amplitude = 3

averages = 1500
points = 4000
freq_gen = 1500

t3034.oscilloscope_record_length(points)
t3034.oscilloscope_number_of_averages(averages)

# Magnetic field for initiazilation
field = 2450
sr830.lock_in_sensitivity(lock_in_sensitivity_standby)
general.wait('20 ms')
#sr830.lock_in_phase(lock_in_phase)
#general.wait('20 ms')
#sr830.lock_in_ref_freq(lock_in_freq)
#general.wait('20 ms')
sr830.lock_in_ref_amplitude(lock_in_amplitude)
general.wait('20 ms')
sr830.lock_in_time_constant(lock_in_time_constant)
general.wait('20 ms')


bh15.magnet_setup(2450, 2.5)
field_step_initialization = 10
#general.wait('15 s')

step_1 = 1
step_2 = 2
step_3 = 1

data2D = []


##### jump in field
while field <= start_field:
    
    field = bh15.magnet_field(field + field_step_initialization)


# Step 1. No THz radation
i = 1
sr830.lock_in_sensitivity(lock_in_sensitivity_operate)
t3034.wave_gen_stop()

while i <= step_1:
    
    field = bh15.magnet_field(start_field)
    x_axis = []
    signal = []

    timenow = str(datetime.now().strftime("%d-%m-%Y_%H-%M-%S"))
    if test_flag != 'test':
        path_to_file_1D = os.path.join('/home/lmr-pc/Experimental_Data/Auto/', str(timenow) + '_Step_1' + '.csv')
        file_save_1D = open(path_to_file_1D, 'a')
    elif test_flag == 'test':
        pass

    temperature = ls335.tc_temperature('B')
    freq = ag53131a.freq_counter_frequency('CH3')/1000000

    while field <= end_field:
        #general.wait(sr830.lock_in_time_constant())
        x_axis = np.append(x_axis, field)
        signal = np.append(signal, sr830.lock_in_get_data())
        if (i % 2) == 0:
            if len(signal) % 5 == 0:
                general.plot_1d('CW_Spectrum', x_axis, signal, xname='Magnetic Field',\
                	xscale='G', yname='Signal Intensity', yscale='V', label='Even')
            else:
                pass
        elif (i % 2) == 1:
            if len(signal) % 5 == 0:
                general.plot_1d('CW_Spectrum', x_axis, signal, xname='Magnetic Field',\
                    xscale='G', yname='Signal Intensity', yscale='V', label='Odd')
            else:
                pass

        field = field + step_field
        bh15.magnet_field(field)

    head = 'Date: ' + str(timenow) + '\n' + 'Start field: ' + str(start_field) + '\n' + \
         'End field: ' + str(end_field) + '\n' + 'Field step: ' + str(step_field) + '\n' \
         'Modulation amplitude: ' + str(lock_in_amplitude) + ' V\n' + 'Time constant: ' + str(lock_in_time_constant) + '\n' + \
         'Frequency amplitude: ' + str(freq) + ' GHz\n' + 'Temperature: ' + str(temperature) + ' K' 


    if test_flag != 'test':
        np.savetxt(file_save_1D, np.c_[x_axis, signal], fmt='%.10f', delimiter=',', \
            newline='\n', header=head, footer='', comments='# ', encoding=None) #header='field: %d' % i
        file_save_1D.close()

        path_to_file_2D = os.path.join('/home/lmr-pc/Experimental_Data/Auto/', '2D_appended_data' + '.csv')
        file_save_2D = open(path_to_file_2D, 'ab')

        np.savetxt(file_save_2D, signal, fmt='%.10f', delimiter=',', \
            newline='\n', header=timenow, footer='', comments='# ', encoding=None)

        file_save_2D.close()

    elif test_flag == 'test':
        pass


    data2D.append(signal)

    general.plot_2d('2D_Dynamic', data2D, start_step = ((start_field, step_field), (0, 1)), xname='Magnetic Field',\
        xscale='G', yname='Number of Spectrum', yscale='Arb. U.', zname='Signal Intensity', zscale='V')    

    while field >= start_field:
        field = bh15.magnet_field(field - field_step_initialization)

    general.message(f"Scan {i} has been done. No THz radiation. Step 1.")
    i += 1


# Step 2. THz radation
i = 1
t3034.wave_gen_run()
integral_for_plotting = []
t3034.wave_gen_frequency(str(freq_gen) + ' Hz')
res = t3034.oscilloscope_time_resolution()

while i <= step_2:

    field = bh15.magnet_field(start_field)
    x_axis = []
    signal = []
    signal_osc = []
    signal_corrected = []
    zero_level = 0
    integral_value = 0
    x_axis_integral = []

    timenow = str(datetime.now().strftime("%d-%m-%Y_%H-%M-%S"))
    if test_flag != 'test':
        path_to_file_1D = os.path.join('/home/lmr-pc/Experimental_Data/Auto/', str(timenow) + '_Step_2' + '.csv')
        file_save_1D = open(path_to_file_1D, 'a')
    elif test_flag == 'test':
        pass

    temperature = ls335.tc_temperature('B')
    freq = ag53131a.freq_counter_frequency('CH3')/1000000

    # Power checking
    t3034.oscilloscope_start_acquisition()
    signal_osc = t3034.oscilloscope_get_curve('CH2')
    t3034.oscilloscope_run()

    # Baseline correction and Integral Calculation
    zero_level = np.sum(signal_osc[0:1000])/1000
    signal_corrected = -zero_level + signal_osc
    if i == 1:
        integral_value = np.trapz(signal_corrected[1200:2801], dx = 1.0)
        integral_value_start = integral_value
    elif i != 1:
        integral_value = np.trapz(signal_corrected[1200:2801], dx = 1.0)
        ratio = integral_value/integral_value_start
        general.message(f'Integral Start: {integral_value_start}')
        general.message(f'Integral: {integral_value}')
        general.message(f'ratio: {abs(ratio)}')
        if round(abs(freq_gen/ratio)) <= 7500 and round(abs(freq_gen/ratio)) >= 1:
            freq_corrected = str(round(abs(freq_gen/ratio))) + ' Hz'
            general.message(f'Freq: {freq_corrected}')
            t3034.wave_gen_frequency(freq_corrected)
        else:
            general.message('Frequency is too high. Probably FEL is off.')
            sys.exit()

    integral_for_plotting = np.append(integral_for_plotting, integral_value)
    x_axis_integral = np.arange(len(integral_for_plotting))
    general.plot_1d('Power_Integral', x_axis_integral, integral_for_plotting, xname='Number of Spectra',\
        xscale='Arb. u.', yname='THz Power', yscale='Arb. u.', label='THz power')

    # Integal Saving
    if test_flag != 'test':

        path_to_file_2D = os.path.join('/home/lmr-pc/Experimental_Data/Auto/', '2D_CW_pulses_and_power' + '.csv')
        file_save_2D = open(path_to_file_2D, 'ab')

        head = 'Integral: ' + str(integral_value) + ' arb.u.\n' + \
            'Resolution: ' + str(res) + ' us'


        np.savetxt(file_save_2D, signal_corrected, fmt='%.10f', delimiter=',', \
            newline='\n', header=head, footer='', comments='# ', encoding=None)

        file_save_2D.close()

    elif test_flag == 'test':
        pass



    while field <= end_field:
        #general.wait(sr830.lock_in_time_constant())
        x_axis = np.append(x_axis, field)
        signal = np.append(signal, sr830.lock_in_get_data())
        if (i % 2) == 0:
            if len(signal) % 5 == 0:            
                general.plot_1d('CW_Spectrum', x_axis, signal, xname='Magnetic Field',\
                    xscale='G', yname='Signal Intensity', yscale='V', label='Even')
            else:
                pass
        elif (i % 2) == 1:
            if len(signal) % 5 == 0:            
                general.plot_1d('CW_Spectrum', x_axis, signal, xname='Magnetic Field',\
                    xscale='G', yname='Signal Intensity', yscale='V', label='Odd')
            else:
                pass

        field = field + step_field
        bh15.magnet_field(field)

    head = 'Date: ' + str(timenow) + '\n' + 'Start field: ' + str(start_field) + '\n' + \
         'End field: ' + str(end_field) + '\n' + 'Field step: ' + str(step_field) + '\n' \
         'Modulation amplitude: ' + str(lock_in_amplitude) + ' V\n' + 'Time constant: ' + str(lock_in_time_constant) + '\n' + \
         'Frequency amplitude: ' + str(freq) + ' GHz\n' + 'Temperature: ' + str(temperature) + ' K' 

    if test_flag != 'test':
        np.savetxt(file_save_1D, np.c_[x_axis, signal], fmt='%.10f', delimiter=',', \
            newline='\n', header=head, footer='', comments='# ', encoding=None) #header='field: %d' % i
        file_save_1D.close()

        path_to_file_2D = os.path.join('/home/lmr-pc/Experimental_Data/Auto/', '2D_appended_data' + '.csv')
        file_save_2D = open(path_to_file_2D, 'ab')

        np.savetxt(file_save_2D, signal, fmt='%.10f', delimiter=',', \
            newline='\n', header=timenow, footer='', comments='# ', encoding=None)

        file_save_2D.close()

    elif test_flag == 'test':
        pass


    data2D.append(signal)

    general.plot_2d('2D_Dynamic', data2D, start_step = ((start_field, step_field), (0, 1)), xname='Magnetic Field',\
        xscale='G', yname='Number of Spectrum', yscale='Arb. U.', zname='Signal Intensity', zscale='V')    

    while field >= start_field:
        field = bh15.magnet_field(field - field_step_initialization)

    general.message(f"Scan {i} has been done. THz radiation is opened. Step 2.")
    i += 1


# Step 3. No THz radation
i = 1
t3034.wave_gen_stop()

while i <= step_3:

    field = bh15.magnet_field(start_field)
    x_axis = []
    signal = []

    timenow = str(datetime.now().strftime("%d-%m-%Y_%H-%M-%S"))
    if test_flag != 'test':
        path_to_file_1D = os.path.join('/home/lmr-pc/Experimental_Data/Auto/', str(timenow) + '_Step_3' + '.csv')
        file_save_1D = open(path_to_file_1D, 'a')
    elif test_flag == 'test':
        pass

    temperature = ls335.tc_temperature('B')
    freq = ag53131a.freq_counter_frequency('CH3')/1000000

    while field <= end_field:
        #general.wait(sr830.lock_in_time_constant())
        x_axis = np.append(x_axis, field)
        signal = np.append(signal, sr830.lock_in_get_data())
        if (i % 2) == 0:
            if len(signal) % 5 == 0:
                general.plot_1d('CW_Spectrum', x_axis, signal, xname='Magnetic Field',\
                    xscale='G', yname='Signal Intensity', yscale='V', label='Even')
            else:
                pass
        elif (i % 2) == 1:
            if len(signal) % 5 == 0:
                general.plot_1d('CW_Spectrum', x_axis, signal, xname='Magnetic Field',\
                    xscale='G', yname='Signal Intensity', yscale='V', label='Odd')
            else:
                pass

        field = field + step_field
        bh15.magnet_field(field)

    head = 'Date: ' + str(timenow) + '\n' + 'Start field: ' + str(start_field) + '\n' + \
         'End field: ' + str(end_field) + '\n' + 'Field step: ' + str(step_field) + '\n' \
         'Modulation amplitude: ' + str(lock_in_amplitude) + ' V\n' + 'Time constant: ' + str(lock_in_time_constant) + '\n' + \
         'Frequency amplitude: ' + str(freq) + ' GHz\n' + 'Temperature: ' + str(temperature) + ' K' 


    if test_flag != 'test':
        np.savetxt(file_save_1D, np.c_[x_axis, signal], fmt='%.10f', delimiter=',', \
            newline='\n', header=head, footer='', comments='# ', encoding=None) #header='field: %d' % i
        file_save_1D.close()

        path_to_file_2D = os.path.join('/home/lmr-pc/Experimental_Data/Auto/', '2D_appended_data' + '.csv')
        file_save_2D = open(path_to_file_2D, 'ab')

        np.savetxt(file_save_2D, signal, fmt='%.10f', delimiter=',', \
            newline='\n', header=timenow, footer='', comments='# ', encoding=None)

        file_save_2D.close()

    elif test_flag == 'test':
        pass


    data2D.append(signal)

    general.plot_2d('2D_Dynamic', data2D, start_step = ((start_field, step_field), (0, 1)), xname='Magnetic Field',\
        xscale='G', yname='Number of Spectrum', yscale='Arb. U.', zname='Signal Intensity', zscale='V')    

    while field >= start_field:
        field = bh15.magnet_field(field - field_step_initialization)

    general.message(f"Scan {i} has been done. No THz radiation. Step 3.")
    i += 1

sr830.lock_in_sensitivity(lock_in_sensitivity_standby)


# Final 2D Saving
if test_flag != 'test':

    timenow = str(datetime.now().strftime("%d-%m-%Y_%H-%M-%S"))

    path_to_file_2D = os.path.join('/home/lmr-pc/Experimental_Data/Auto/', '2D_data_' + str(timenow) + '.csv')
    file_save_2D = open(path_to_file_2D, 'a')

    head = 'Date: ' + str(timenow) + '\n' + 'Start field: ' + str(start_field) + '\n' + \
         'End field: ' + str(end_field) + '\n' + 'Field step: ' + str(step_field) + '\n' \
         'Modulation amplitude: ' + str(lock_in_amplitude) + ' V\n' + 'Time constant: ' + str(lock_in_time_constant) + '\n' + \
         'Frequency amplitude: ' + str(freq) + ' GHz\n' + 'Temperature: ' + str(temperature) + ' K\n' + \
         'Step 1. No THz: ' + str(step_1) + ' spectra\n' + 'Step 2. THz: ' + str(step_2) + ' spectra\n' + \
         'Step 3. No THz: ' + str(step_3) + ' spectra'

    np.savetxt(file_save_2D, data2D, fmt='%.10f', delimiter=',', \
        newline='\n', header=head, footer='', comments='# ', encoding=None)

    file_save_2D.close()

elif test_flag == 'test':
    pass

general.message('Complete scan had been done.')
