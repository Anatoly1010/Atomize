import sys
import signal
import datetime
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.PB_ESR_500_pro as pb_pro
import atomize.device_modules.Spectrum_M4I_6631_X8 as spectrum
import atomize.device_modules.Spectrum_M4I_4450_X8 as spectrum_dig
import atomize.device_modules.Mikran_X_band_MW_bridge as mwBridge
import atomize.device_modules.BH_15 as bh
import atomize.device_modules.SR_PTC_10 as sr
import atomize.general_modules.csv_opener_saver_tk_kinter as openfile

# initialization of the devices
file_handler = openfile.Saver_Opener()
ptc10 = sr.SR_PTC_10()
mw = mwBridge.Mikran_X_band_MW_bridge()
pb = pb_pro.PB_ESR_500_Pro()
bh15 = bh.BH_15()
dig4450 = spectrum_dig.Spectrum_M4I_4450_X8()
awg = spectrum.Spectrum_M4I_6631_X8()

def cleanup(*args):
    dig4450.digitizer_stop()
    dig4450.digitizer_close()
    awg.awg_stop()
    awg.awg_close()
    pb.pulser_stop()
    file_handler.save_data(file_data, np.c_[x_axis, data_x, data_y], header = header, mode = 'w')
    sys.exit(0)

signal.signal(signal.SIGTERM, cleanup)

### Experimental parameters
POINTS = 250
STEP = 4                  # in NS; delta_start for PUMP pulse; # delta_start = str(STEP) + ' ns' -> delta_start = '4 ns'
FIELD = 3447
AVERAGES = 2
SCANS = 1
process = 'None'

# PULSES
REP_RATE = '2000 Hz'
PULSE_1_LENGTH = '16 ns'
PULSE_2_LENGTH = '32 ns'
PULSE_3_LENGTH = '32 ns'
PULSE_PUMP_LENGTH = '14 ns'
# 398 ns is delay from AWG trigger 1.25 GHz
# 494 ns is delay from AWG trigger 1.00 GHz
PULSE_1_START = '2100 ns'
PULSE_2_START = '2400 ns'
# 2680 = 494 (awg_output delay) + 430 (awg trigger) + 1756 (awg position)
PULSE_PUMP_START = '2600 ns'
PULSE_3_START = '3700 ns'
PULSE_SIGNAL_START = '4700 ns'

PULSE_TRIGGER_AWG_START = '430 ns'
PULSE_AWG_PUMP_START = '1676 ns'

# NAMES
EXP_NAME = 'DEER 64'
CURVE_NAME = 'exp1'

#
cycle_data_x = np.zeros( 64 )
cycle_data_y = np.zeros( 64 )
data_x = np.zeros(POINTS)
data_y = np.zeros(POINTS)
x_axis = np.linspace(0, (POINTS - 1)*STEP, num = POINTS) 
###

#PROBE
pb.pulser_pulse(name = 'P0', channel = 'MW', start = PULSE_1_START, length = PULSE_1_LENGTH, \
    phase_list = ['+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x',\
                  '+y', '+y', '+y', '+y', '+y', '+y', '+y', '+y', '+y', '+y', '+y', '+y', '+y', '+y', '+y', '+y',\
                  '-x', '-x', '-x', '-x', '-x', '-x', '-x', '-x', '-x', '-x', '-x', '-x', '-x', '-x', '-x', '-x',\
                  '-y', '-y', '-y', '-y', '-y', '-y', '-y', '-y', '-y', '-y', '-y', '-y', '-y', '-y', '-y', '-y'])
pb.pulser_pulse(name = 'P1', channel = 'MW', start = PULSE_2_START, length = PULSE_2_LENGTH, \
    phase_list = ['+x', '+x', '+x', '+x', '+y', '+y', '+y', '+y', '-x', '-x', '-x', '-x', '-y', '-y', '-y', '-y',\
                  '+x', '+x', '+x', '+x', '+y', '+y', '+y', '+y', '-x', '-x', '-x', '-x', '-y', '-y', '-y', '-y',\
                  '+x', '+x', '+x', '+x', '+y', '+y', '+y', '+y', '-x', '-x', '-x', '-x', '-y', '-y', '-y', '-y',\
                  '+x', '+x', '+x', '+x', '+y', '+y', '+y', '+y', '-x', '-x', '-x', '-x', '-y', '-y', '-y', '-y'])
pb.pulser_pulse(name = 'P2', channel = 'MW', start = PULSE_3_START, length = PULSE_3_LENGTH, \
    phase_list = ['+x', '+y', '-x', '-y', '+x', '+y', '-x', '-y', '+x', '+y', '-x', '-y', '+x', '+y', '-x', '-y',\
                  '+x', '+y', '-x', '-y', '+x', '+y', '-x', '-y', '+x', '+y', '-x', '-y', '+x', '+y', '-x', '-y',\
                  '+x', '+y', '-x', '-y', '+x', '+y', '-x', '-y', '+x', '+y', '-x', '-y', '+x', '+y', '-x', '-y',\
                  '+x', '+y', '-x', '-y', '+x', '+y', '-x', '-y', '+x', '+y', '-x', '-y', '+x', '+y', '-x', '-y'])

#PUMP
pb.pulser_pulse(name = 'P3', channel = 'AWG', start = PULSE_PUMP_START, length = PULSE_PUMP_LENGTH, delta_start = str(STEP) + ' ns')
pb.pulser_pulse(name = 'P4', channel = 'TRIGGER_AWG', start = PULSE_TRIGGER_AWG_START, length = '20 ns', delta_start = str(STEP) + ' ns')
awg.awg_pulse(name = 'P5', channel = 'CH0', func = 'SINE', frequency = '70 MHz', phase = 0, \
            length = PULSE_PUMP_LENGTH, sigma = PULSE_PUMP_LENGTH, start = PULSE_AWG_PUMP_START)
# 398 ns is delay from AWG trigger 1.25 GHz
# 494 ns is delay from AWG trigger 1.00 GHz
# 2680 = 494 (awg_output delay) + 430 (awg trigger) + 1756 (awg position)

#DETECTION
pb.pulser_pulse(name = 'P6', channel = 'TRIGGER', start = PULSE_SIGNAL_START, length = '100 ns')


bh15.magnet_setup(FIELD, 1)
bh15.magnet_field(FIELD)

dig4450.digitizer_read_settings()
dig4450.digitizer_number_of_averages(AVERAGES)
tb = dig4450.digitizer_window()

pb.pulser_repetition_rate( REP_RATE )

awg.awg_sample_rate(1000)
awg.awg_clock_mode('External')
awg.awg_reference_clock(100)
awg.awg_channel('CH0', 'CH1')
awg.awg_card_mode('Single Joined')
###awg.trigger_delay('1792 ns')
awg.awg_setup()


# Data saving
header = 'Date: ' + str(datetime.datetime.now().strftime("%d-%m-%Y %H-%M-%S")) + '\n' + \
         'DEER Measurement; 64 Step Phase Cycling\n' + 'Field: ' + str(FIELD) + ' G \n' + str(mw.mw_bridge_att1_prd()) + '\n' + \
           str(mw.mw_bridge_att2_prd()) + '\n' + str(mw.mw_bridge_att_prm()) + '\n' + str(mw.mw_bridge_synthesizer()) + '\n' + \
          'Repetition Rate: ' + str(pb.pulser_repetition_rate()) + '\n' + 'Number of Scans: ' + str(SCANS) + '\n' +\
          'Averages: ' + str(AVERAGES) + '\n' + 'Points: ' + str(POINTS) + '\n' + 'Window: ' + str(tb) + ' ns\n' \
          + 'Temperature: ' + str(ptc10.tc_temperature('2A')) + ' K\n' +\
          'Pulse List: ' + '\n' + str(pb.pulser_pulse_list()) + 'AWG Pulse List: ' + '\n' +\
          str(awg.awg_pulse_list()) + 'Time (awg delta_start), X (V*s), Y (V*s) '

file_data, file_param = file_handler.create_file_parameters('.param')
file_handler.save_header(file_param, header = header, mode = 'w')


# Data acquisition
for j in general.scans(SCANS):

    for i in range(POINTS):

        # phase cycle
        k = 0
        while k < 64:

            pb.pulser_next_phase()
            if k == 0:
                awg.awg_update()

            cycle_data_x[k], cycle_data_y[k] = dig4450.digitizer_get_curve( integral = True )

            k += 1
        
        # acquisition cycle
        x, y = pb.pulser_acquisition_cycle(cycle_data_x, cycle_data_y, \
            acq_cycle = ['+', '-', '+', '-', '-', '+', '-', '+', '+', '-', '+', '-', '-', '+', '-', '+',
                         '+i', '-i', '+i', '-i', '-i', '+i', '-i', '+i', '+i', '-i', '+i', '-i', '-i', '+i', '-i', '+i',
                         '-', '+', '-', '+', '+', '-', '+', '-', '-', '+', '-', '+', '+', '-', '+', '-',
                         '-i', '+i', '-i', '+i', '+i', '-i', '+i', '-i', '-i', '+i', '-i', '+i', '+i', '-i', '+i', '-i' ])

# ['+', '-', '+', '-', '-', '+', '-', '+', '+', '-', '+', '-', '-', '+', '-', '+', 
# '-i', '+i', '-i', '+i', '+i', '-i', '+i', '-i', '-i', '+i', '-i', '+i', '+i', '-i', '+i', '-i', 
# '-', '+', '-', '+', '+', '-', '+', '-', '-', '+', '-', '+', '+', '-', '+', '-', 
# '+i', '-i', '+i', '-i', '-i', '+i', '-i', '+i', '+i', '-i', '+i', '-i', '-i', '+i', '-i', '+i']

        data_x[i] = ( data_x[i] * (j - 1) + x ) / j
        data_y[i] = ( data_y[i] * (j - 1) + y ) / j

        process = general.plot_1d(EXP_NAME, x_axis, ( data_x, data_y ), xname = 'Delay',\
            xscale = 'ns', yname = 'Area', yscale = 'V*s', label = CURVE_NAME, pr = process, \
            text = 'Scan / Time: ' + str(j) + ' / ' + str(i*STEP))

        pb.pulser_shift()

    ###awg.awg_pulse_reset()
    pb.pulser_pulse_reset()

dig4450.digitizer_stop()
dig4450.digitizer_close()
awg.awg_stop()
awg.awg_close()
pb.pulser_stop()

file_handler.save_data(file_data, np.c_[x_axis, data_x, data_y], header = header, mode = 'w')
