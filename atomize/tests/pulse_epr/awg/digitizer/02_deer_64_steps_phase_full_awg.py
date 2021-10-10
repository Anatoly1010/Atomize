import sys
import signal
import datetime
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.PB_ESR_500_pro as pb_pro
###import atomize.device_modules.Keysight_3000_Xseries as key
import atomize.device_modules.Spectrum_M4I_6631_X8 as spectrum
import atomize.device_modules.Spectrum_M4I_4450_X8 as spectrum_dig
import atomize.device_modules.Mikran_X_band_MW_bridge as mwBridge
import atomize.device_modules.BH_15 as bh
import atomize.device_modules.SR_PTC_10 as sr
import atomize.general_modules.csv_opener_saver as openfile

# initialization of the devices
file_handler = openfile.Saver_Opener()
ptc10 = sr.SR_PTC_10()
mw = mwBridge.Mikran_X_band_MW_bridge()
pb = pb_pro.PB_ESR_500_Pro()
bh15 = bh.BH_15()
###t3034 = key.Keysight_3000_Xseries()
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
POINTS = 250
STEP = 4                  # in NS; delta_start for PUMP pulse; # delta_start = str(STEP) + ' ns' -> delta_start = '4 ns'
FIELD = 3449
AVERAGES = 20
SCANS = 1

# PULSES
REP_RATE = '1000 Hz'

# NAMES
EXP_NAME = 'DEER 64'
CURVE_NAME = 'exp1'

#
dig4450.digitizer_read_settings()
dig4450.digitizer_number_of_averages(AVERAGES)
time_res = int( 1000 / int(dig4450.digitizer_sample_rate().split(' ')[0]) )
# a full oscillogram will be transfered
wind = dig4450.digitizer_number_of_points()
cycle_data_x = np.zeros( (64, int(wind)) )
cycle_data_y = np.zeros( (64, int(wind)) )
data = np.zeros( (2, int(wind), POINTS) )

###t3034.oscilloscope_record_length( 2500 )
###real_length = t3034.oscilloscope_record_length( )
###tb = t3034.oscilloscope_timebase() * 1000
#x_axis = np.linspace(0, (POINTS - 1)*STEP, num = POINTS) 
###

#PROBE
pb.pulser_pulse(name = 'P0', channel = 'TRIGGER_AWG', start = '0 ns', length = '20 ns')

pb.pulser_pulse(name = 'P1', channel = 'AWG', start = '494 ns', length = '16 ns')
awg.awg_pulse(name = 'P2', channel = 'CH0', func = 'SINE', frequency = '200 MHz', phase = 0, \
            length = '16 ns', sigma = '16 ns', start = '0 ns', \
            phase_list = ['+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x',\
                  '+y', '+y', '+y', '+y', '+y', '+y', '+y', '+y', '+y', '+y', '+y', '+y', '+y', '+y', '+y', '+y',\
                  '-x', '-x', '-x', '-x', '-x', '-x', '-x', '-x', '-x', '-x', '-x', '-x', '-x', '-x', '-x', '-x',\
                  '-y', '-y', '-y', '-y', '-y', '-y', '-y', '-y', '-y', '-y', '-y', '-y', '-y', '-y', '-y', '-y'])

pb.pulser_pulse(name = 'P3', channel = 'AWG', start = '834 ns', length = '32 ns')
awg.awg_pulse(name = 'P4', channel = 'CH0', func = 'SINE', frequency = '200 MHz', phase = 0, \
            length = '32 ns', sigma = '32 ns', start = '340 ns', \
            phase_list = ['+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x',\
                  '+y', '+y', '+y', '+y', '+y', '+y', '+y', '+y', '+y', '+y', '+y', '+y', '+y', '+y', '+y', '+y',\
                  '-x', '-x', '-x', '-x', '-x', '-x', '-x', '-x', '-x', '-x', '-x', '-x', '-x', '-x', '-x', '-x',\
                  '-y', '-y', '-y', '-y', '-y', '-y', '-y', '-y', '-y', '-y', '-y', '-y', '-y', '-y', '-y', '-y'])

#PUMP
pb.pulser_pulse(name = 'P7', channel = 'AWG', start = '1074 ns', length = '20 ns', delta_start = str(STEP) + ' ns')
awg.awg_pulse(name = 'P8', channel = 'CH0', func = 'SINE', frequency = '70 MHz', phase = 0, \
            length = '20 ns', sigma = '20 ns', start = '580 ns', delta_start = str(STEP) + ' ns', \
            phase_list = ['+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x',\
                  '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x',\
                  '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x',\
                  '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x'])

pb.pulser_pulse(name = 'P5', channel = 'AWG', start = '2174 ns', length = '32 ns')
awg.awg_pulse(name = 'P6', channel = 'CH0', func = 'SINE', frequency = '200 MHz', phase = 0, \
            length = '32 ns', sigma = '32 ns', start = '1680 ns', \
            phase_list = ['+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x',\
                  '+y', '+y', '+y', '+y', '+y', '+y', '+y', '+y', '+y', '+y', '+y', '+y', '+y', '+y', '+y', '+y',\
                  '-x', '-x', '-x', '-x', '-x', '-x', '-x', '-x', '-x', '-x', '-x', '-x', '-x', '-x', '-x', '-x',\
                  '-y', '-y', '-y', '-y', '-y', '-y', '-y', '-y', '-y', '-y', '-y', '-y', '-y', '-y', '-y', '-y'])

# 398 ns is delay from AWG trigger 1.25 GHz
# 494 ns is delay from AWG trigger 1.00 GHz
# AWG = 494 (awg_output delay) + (awg pulse position)

#DETECTION
pb.pulser_pulse(name = 'P9', channel = 'TRIGGER', start = '2680 ns', length = '100 ns')


bh15.magnet_setup(FIELD, 1)
bh15.magnet_field(FIELD)

###t3034.oscilloscope_trigger_channel('CH1')
###t3034.oscilloscope_record_length(250)
###t3034.oscilloscope_acquisition_type('Average')
###t3034.oscilloscope_number_of_averages(AVERAGES)
###t3034.oscilloscope_stop()


pb.pulser_repetition_rate( REP_RATE )

awg.awg_clock_mode('External')
awg.awg_reference_clock(100)
awg.awg_channel('CH0', 'CH1')
awg.awg_card_mode('Single Joined')
###awg.trigger_delay('1792 ns')
awg.awg_setup()


# Data saving
header = 'Date: ' + str(datetime.datetime.now().strftime("%d-%m-%Y %H-%M-%S")) + '\n' + \
         'DEER Measurement; 64 Step Phase Cycling; Full AWG\n' + 'Field: ' + str(FIELD) + ' G \n' + str(mw.mw_bridge_att1_prd()) + '\n' + \
           str(mw.mw_bridge_att2_prd()) + '\n' + str(mw.mw_bridge_att_prm()) + '\n' + str(mw.mw_bridge_synthesizer()) + '\n' + \
          'Repetition Rate: ' + str(pb.pulser_repetition_rate()) + '\n' + 'Number of Scans: ' + str(SCANS) + '\n' +\
          'Averages: ' + str(AVERAGES) + '\n' + 'Points: ' + str(POINTS) + '\n' + 'Window: ' + str(wind * time_res) + ' ns\n' \
          + 'Horizontal Resolution: ' + str(time_res) + ' ns\n' + 'Vertical Resolution: ' + str(STEP) + ' ns\n' \
          + 'Temperature: ' + str(ptc10.tc_temperature('2A')) + ' K\n' +\
          'Pulse List: ' + '\n' + str(pb.pulser_pulse_list()) + 'AWG Pulse List: ' + '\n' +\
          str(awg.awg_pulse_list()) + '2D Data'

file_data, file_param = file_handler.create_file_parameters('.param')
file_handler.save_header(file_param, header = header, mode = 'w')


# Data acquisition
#j = 1
for j in general.scans(SCANS):
#while j <= SCANS:

    for i in range(POINTS):

        # phase cycle
        k = 0
        pb.pulser_update()
        while k < 64:

            awg.awg_next_phase()

            x_axis, cycle_data_x[k], cycle_data_y[k] = dig4450.digitizer_get_curve()
            ###t3034.oscilloscope_start_acquisition()
            ###cycle_data_x[k] = t3034.oscilloscope_area('CH4')
            ###cycle_data_y[k] = t3034.oscilloscope_area('CH3')

            awg.awg_stop()
            k += 1
        
        # acquisition cycle
        x, y = pb.pulser_acquisition_cycle(cycle_data_x, cycle_data_y, \
            acq_cycle = ['+', '-', '+', '-', '-', '+', '-', '+', '+', '-', '+', '-', '-', '+', '-', '+',
                         '+i', '-i', '+i', '-i', '-i', '+i', '-i', '+i', '+i', '-i', '+i', '-i', '-i', '+i', '-i', '+i',
                         '-', '+', '-', '+', '+', '-', '+', '-', '-', '+', '-', '+', '+', '-', '+', '-',
                         '-i', '+i', '-i', '+i', '+i', '-i', '+i', '-i', '-i', '+i', '-i', '+i', '+i', '-i', '+i', '-i' ])

        data[0, :, i] = ( data[0, :, i] * (j - 1) + x ) / j
        data[1, :, i] = ( data[0, :, i] * (j - 1) + y ) / j

        general.plot_2d(EXP_NAME, data, start_step = ( (0, time_res), (0, STEP) ), xname = 'Time',\
            xscale = 'ns', yname = 'Delay', yscale = 'ns', zname = 'Intensity', zscale = 'V')
        general.text_label( EXP_NAME, "Scan / Time: ", str(j) + ' / '+ str(i*STEP) )

        #awg.awg_stop()
        awg.awg_shift()
        pb.pulser_shift()

    #j += 1
    awg.awg_pulse_reset()
    pb.pulser_pulse_reset()

dig4450.digitizer_stop()
dig4450.digitizer_close()
awg.awg_stop()
awg.awg_close()
pb.pulser_stop()

file_handler.save_data(file_data, data, header = header, mode = 'w')
