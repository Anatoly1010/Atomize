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

# 10.1016/S0009-2614(00)01171-4   -> phase cycling
# 10.1039/C5CP03671B              -> timings

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
    file_handler.save_data(file_data, data, header = header, mode = 'w')
    sys.exit(0)

signal.signal(signal.SIGTERM, cleanup)

### Experimental parameters
POINTS = 160
STEP = 2                  # in NS
STEP8 = 8
CYCLE8 = 12
FIELD = 3446
AVERAGES = 64
SCANS = 1
process = 'None'
PHASE = 16

# PULSES
REP_RATE = '2000 Hz'
PULSE_1_LENGTH = '220 ns'
PULSE_2_LENGTH = '220 ns'
PULSE_3_LENGTH = '220 ns'
PULSE_4_LENGTH = '220 ns'
PULSE_1_START = '0 ns'
PULSE_2_START = '500 ns'
PULSE_3_START = '1000 ns'
PULSE_4_START = '1600 ns'
PULSE_SIGNAL_START = '2694 ns'

# NAMES
EXP_NAME = 'SIFTER AWG'
CURVE_NAME = 'exp1'

#
dig4450.digitizer_read_settings()
dig4450.digitizer_number_of_averages(AVERAGES)
time_res = int( 1000 / int(dig4450.digitizer_sample_rate().split(' ')[0]) )
# a full oscillogram will be transfered
wind = dig4450.digitizer_number_of_points()
cycle_data_x = np.zeros( (PHASE, int(wind)) )
cycle_data_y = np.zeros( (PHASE, int(wind)) )
data = np.zeros( (2, int(wind), POINTS) )

bh15.magnet_setup(FIELD, 1)
bh15.magnet_field(FIELD)

# probably 2D; but in the 10.1039/C5CP03671B the step of t1 is equal to the step of t2
# additionally 8 cycles with delta_P0_P1 = delta_P1_P2 = t1 and delta_P2_P3 = delta_P3_P4 = t2
# delta_t1 = delta_t2 = 16 ns; to get rid of D modulation
pb.pulser_pulse(name = 'P0', channel = 'TRIGGER_AWG', start = PULSE_1_START, length = '20 ns')

pb.pulser_pulse(name = 'P1', channel = 'AWG', start = str( int(PULSE_1_START.split(' ')[0]) + 494 ) + ' ns', length = PULSE_1_LENGTH)
awg.awg_pulse(name = 'P2', channel = 'CH0', func = 'WURST', frequency = ('80 MHz', '390 MHz'), phase = 0, \
                length = PULSE_1_LENGTH, sigma = PULSE_1_LENGTH, start = PULSE_1_START, \
                phase_list = ['+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x'], \
                d_coef = 3.12, n = 30)

pb.pulser_pulse(name = 'P3', channel = 'AWG', start = str( int(PULSE_2_START.split(' ')[0]) + 494 ) + ' ns', length = PULSE_2_LENGTH, \
                delta_start = str(STEP) + ' ns')
awg.awg_pulse(name = 'P4', channel = 'CH0', func = 'WURST', frequency = ('80 MHz', '390 MHz'), phase = 0, \
                length = PULSE_2_LENGTH, sigma = PULSE_2_LENGTH, start = PULSE_2_START, delta_start = str(STEP) + ' ns', \
                phase_list = ['+x', '+y', '-x', '-y', '+x', '+y', '-x', '-y', '+x', '+y', '-x', '-y', '+x', '+y', '-x', '-y'], \
                d_coef = 1.0, n = 30)

pb.pulser_pulse(name = 'P5', channel = 'AWG', start = str( int(PULSE_3_START.split(' ')[0]) + 494 ) + ' ns', length = PULSE_3_LENGTH, \
                delta_start = str(2 * STEP) + ' ns')
awg.awg_pulse(name = 'P6', channel = 'CH0', func = 'WURST', frequency = ('80 MHz', '390 MHz'), phase = 0, \
                length = PULSE_3_LENGTH, sigma = PULSE_3_LENGTH, start = PULSE_3_START, delta_start = str(2 * STEP) + ' ns', \
                phase_list = ['+y', '+y', '+y', '+y', '-y', '-y', '-y', '-y', '+y', '+y', '+y', '+y', '-y', '-y', '-y', '-y'], \
                d_coef = 3.12, n = 30)

pb.pulser_pulse(name = 'P7', channel = 'AWG', start = str( int(PULSE_4_START.split(' ')[0]) + 494 ) + ' ns', length = PULSE_4_LENGTH, \
                delta_start = str(STEP) + ' ns')
awg.awg_pulse(name = 'P8', channel = 'CH0', func = 'WURST', frequency = ('80 MHz', '390 MHz'), phase = 0, \
                length = PULSE_4_LENGTH, sigma = PULSE_4_LENGTH, start = PULSE_4_START, delta_start = str(STEP) + ' ns', \
                phase_list = ['+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '-x', '-x', '-x', '-x', '-x', '-x', '-x', '-x'], \
                d_coef = 1.0, n = 30)

pb.pulser_pulse(name = 'P9', channel = 'TRIGGER', start = PULSE_SIGNAL_START, length = '100 ns', delta_start = str(STEP8 * 4) + ' ns')

# 398 ns is delay from AWG trigger 1.25 GHz
# 494 ns is delay from AWG trigger 1.00 GHz
# AWG = 494 (awg_output delay) + (awg pulse position)

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
         'SIFTER; Full AWG\n' + 'Field: ' + str(FIELD) + ' G \n' + str(mw.mw_bridge_att1_prd()) + '\n' + \
           str(mw.mw_bridge_att2_prd()) + '\n' + str(mw.mw_bridge_att_prm()) + '\n' + str(mw.mw_bridge_synthesizer()) + '\n' + \
          'Repetition Rate: ' + str(pb.pulser_repetition_rate()) + '\n' + 'Number of Scans: ' + str(SCANS) + '\n' +\
          'Averages: ' + str(AVERAGES) + '\n' + 'Points: ' + str(POINTS) + '\n' + 'Window: ' + str(wind * time_res) + ' ns\n' \
          + 'Horizontal Resolution: ' + str(time_res) + ' ns\n' + 'Vertical Resolution: ' + str(2 * STEP) + ' ns\n' \
          + 'Temperature: ' + str(ptc10.tc_temperature('2A')) + ' K\n' +\
          'Pulse List: ' + '\n' + str(pb.pulser_pulse_list()) + 'AWG Pulse List: ' + '\n' +\
          str(awg.awg_pulse_list()) + '2D Data'

file_data, file_param = file_handler.create_file_parameters('.param')
file_handler.save_header(file_param, header = header, mode = 'w')

for j in general.scans(SCANS):

    cycle_8 = 1 
    while cycle_8 <= CYCLE8:

        m = 1
        while m < cycle_8:
            pb.pulser_redefine_delta_start(name = 'P3', delta_start = str( int(STEP8) ) + ' ns')
            awg.awg_redefine_delta_start(name = 'P4', delta_start = str( int(STEP8) ) + ' ns')
            pb.pulser_redefine_delta_start(name = 'P5', delta_start = str( int(STEP8 * 2) ) + ' ns')
            awg.awg_redefine_delta_start(name = 'P6', delta_start = str( int(STEP8 * 2) ) + ' ns')
            pb.pulser_redefine_delta_start(name = 'P7', delta_start = str( int(STEP8 * 3) ) + ' ns')
            awg.awg_redefine_delta_start(name = 'P8', delta_start = str( int(STEP8 * 3) ) + ' ns')
            pb.pulser_shift('P3', 'P5', 'P7', 'P9')
            awg.awg_shift('P4', 'P6', 'P8')

            pb.pulser_redefine_delta_start(name = 'P3', delta_start = str( int(STEP) ) + ' ns')
            awg.awg_redefine_delta_start(name = 'P4', delta_start = str( int(STEP) ) + ' ns')
            pb.pulser_redefine_delta_start(name = 'P5', delta_start = str( int(STEP * 2) ) + ' ns')
            awg.awg_redefine_delta_start(name = 'P6', delta_start = str( int(STEP * 2) ) + ' ns')
            pb.pulser_redefine_delta_start(name = 'P7', delta_start = str( int(STEP) ) + ' ns')
            awg.awg_redefine_delta_start(name = 'P8', delta_start = str( int(STEP) ) + ' ns')

            m += 1

        for i in range(POINTS):

            # phase cycle
            k = 0
            pb.pulser_update()
            while k < PHASE:

                awg.awg_next_phase()
                x_axis, cycle_data_x[k], cycle_data_y[k] = dig4450.digitizer_get_curve( )

                awg.awg_stop()
                k += 1
            
            x, y = pb.pulser_acquisition_cycle(cycle_data_x, cycle_data_y, \
                    acq_cycle = ['+', '-', '+', '-', '+', '-', '+', '-', '+', '-', '+', '-', '+', '-', '+', '-'])

            data[0, :, i] = ( data[0, :, i] * (cycle_8 - 1 + (j - 1) * CYCLE8 ) + x ) / ( cycle_8 + (j - 1) * CYCLE8 )
            data[1, :, i] = ( data[1, :, i] * (cycle_8 - 1 + (j - 1) * CYCLE8 ) + y ) / ( cycle_8 + (j - 1) * CYCLE8 )

            process = general.plot_2d(EXP_NAME, data, start_step = ( (0, time_res), (0, 2* STEP) ), xname = 'Time',\
                xscale = 'ns', yname = 'Delay', yscale = 'ns', zname = 'Intensity', zscale = 'V', pr = process, \
                text = str(j) + ' / ' + str(cycle_8) + ' / ' + str(i*STEP))

            #awg.awg_stop()
            awg.awg_shift('P4', 'P6', 'P8')
            pb.pulser_shift('P3', 'P5', 'P7')

        awg.awg_pulse_reset()
        pb.pulser_pulse_reset()
        cycle_8 += 1

    awg.awg_pulse_reset()
    pb.pulser_reset()

dig4450.digitizer_stop()
dig4450.digitizer_close()
awg.awg_stop()
awg.awg_close()
pb.pulser_stop()

file_handler.save_data(file_data, data, header = header, mode = 'w')
