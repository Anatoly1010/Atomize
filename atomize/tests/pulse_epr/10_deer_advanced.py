import time
import datetime
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.PB_ESR_500_pro as pb_pro
import atomize.device_modules.Keysight_3000_Xseries as key
import atomize.device_modules.Mikran_X_band_MW_bridge as mwBridge
import atomize.device_modules.BH_15 as bh
import atomize.device_modules.SR_PTC_10 as sr
import atomize.general_modules.csv_opener_saver_tk_kinter as openfile

### Experimental parameters
POINTS = 200
STEP = 4                  # in NS; delta_start for PUMP pulse; 
                          # delta_start = str(STEP) + ' ns' -> delta_start = '4 ns'
FIELD = 3473
AVERAGES = 1000

cycle_data_x = np.zeros(POINTS)
cycle_data_y = np.zeros(POINTS)
data_x = np.zeros(POINTS)
data_y = np.zeros(POINTS)
x_axis = np.arange(0, POINTS*STEP, STEP)
###

# initialization of the devices
file_handler = openfile.Saver_Opener()
ptc10 = sr.SR_PTC_10()
mw = mwBridge.Mikran_X_band_MW_bridge()
pb = pb_pro.PB_ESR_500_Pro()
t3034 = key.Keysight_3000_Xseries()
bh15 = bh.BH_15()

bh15.magnet_setup(FIELD, 1)
bh15.magnet_field(FIELD)

t3034.oscilloscope_trigger_channel('CH1')
t3034.oscilloscope_record_length(250)
t3034.oscilloscope_acquisition_type('Average')
t3034.oscilloscope_number_of_averages(AVERAGES)
t3034.oscilloscope_stop()

#PROBE
pb.pulser_pulse(name = 'P0', channel = 'MW', start = '2100 ns', length = '16 ns', phase_list = ['+x', '-x'])
pb.pulser_pulse(name = 'P1', channel = 'MW', start = '2440 ns', length = '32 ns', delta_start = str(int(STEP*2)) + ' ns', phase_list = ['+x', '+x'])
pb.pulser_pulse(name = 'P2', channel = 'MW', start = '3780 ns', length = '32 ns', delta_start = str(int(STEP*4)) + ' ns', phase_list = ['+x', '+x'])
#PUMP
pb.pulser_pulse(name = 'P3', channel = 'AWG', start = '2680 ns', length = '20 ns', delta_start = str(STEP) + ' ns')
pb.pulser_pulse(name = 'P4', channel = 'TRIGGER_AWG', start = '526 ns', length = '20 ns', delta_start = str(STEP) + ' ns')
#DETECTION
pb.pulser_pulse(name = 'P5', channel = 'TRIGGER', start = '4780 ns', length = '100 ns', delta_start = str(int(STEP*4)) + ' ns')

pb.pulser_repetition_rate('1000 Hz')

k = 1 
while k < 9:
    
    j = 0
    while j < k:
        pb.pulser_shift('P1', 'P2', 'P3', 'P4', 'P5')
        pb.pulser_shift('P3', 'P4')
        pb.pulser_shift('P3', 'P4')
        pb.pulser_shift('P3', 'P4')

        j += 1

    if k % 2 == 1:
        pb.pulser_next_phase()
    elif k % 2 == 0:
        pb.pulser_next_phase()
        pb.pulser_next_phase()

    i = 0
    while i < POINTS:

        pb.pulser_update()

        t3034.oscilloscope_start_acquisition()
        area_x = t3034.oscilloscope_area('CH4')
        area_y = t3034.oscilloscope_area('CH3')

        cycle_data_x[i] = area_x
        cycle_data_y[i] = area_y

        pb.pulser_shift('P3','P4')

        general.plot_1d('DEER_Cycle', x_axis, cycle_data_x, xname = 'Delay',\
            xscale = 'ns', yname = 'Area', yscale = 'V*s', label = 'X')
        general.plot_1d('DEER_Cycle', x_axis, cycle_data_y, xname = 'Delay',\
            xscale = 'ns', yname = 'Area', yscale = 'V*s', label = 'Y')

        i += 1

    data_x = (data_x*(k-1) + cycle_data_x)/k
    data_y = (data_y*(k-1) + cycle_data_y)/k

    general.plot_1d('DEER_All', x_axis, data_x, xname = 'Delay',\
        xscale = 'ns', yname = 'Area', yscale = 'V*s', label = 'X')
    general.plot_1d('DEER_All', x_axis, data_y, xname = 'Delay',\
        xscale = 'ns', yname = 'Area', yscale = 'V*s', label = 'Y')

    pb.pulser_reset()

    k += 1

pb.pulser_stop()

# Data saving
header = 'Date: ' + str(datetime.datetime.now().strftime("%d-%m-%Y %H-%M-%S")) + '\n' + 'DEER Measurement\n' + \
            'Field: ' + str(FIELD) + ' G \n' + str(mw.mw_bridge_att_prm()) + '\n' + \
            str(mw.mw_bridge_synthesizer()) + '\n' + \
           'Repetition Rate: ' + str(pb.pulser_repetition_rate()) + '\n' +\
           'Averages: ' + str(AVERAGES) + '\n' + 'Window: ' + str(t3034.oscilloscope_timebase()*1000) + ' ns\n' + \
           'Temperature: ' + str(ptc10.tc_temperature('2A')) + ' K\n' +\
           'Pulse List: ' + '\n' + str(pb.pulser_pulse_list()) + 'Time (trig_awg delta_start), X (V*s), Y (V*s) '

file_handler.save_1D_dialog( (x_axis, data_x, data_y), header = header )

