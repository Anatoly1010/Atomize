import sys
import signal
import datetime
import numpy as np
import atomize.math_modules.fft as fft_module
import atomize.general_modules.general_functions as general
import atomize.general_modules.return_thread as returnThread
import atomize.device_modules.PB_ESR_500_pro as pb_pro
import atomize.device_modules.Spectrum_M4I_6631_X8 as spectrum
import atomize.device_modules.Spectrum_M4I_4450_X8 as spectrum_dig
import atomize.general_modules.csv_opener_saver as openfile

# initialization of the devices
file_handler = openfile.Saver_Opener()
pb = pb_pro.PB_ESR_500_Pro()
dig4450 = spectrum_dig.Spectrum_M4I_4450_X8()
awg = spectrum.Spectrum_M4I_6631_X8()
fft = fft_module.Fast_Fourier()

def cleanup(*args):
    dig4450.digitizer_stop()
    dig4450.digitizer_close()
    awg.awg_stop()
    awg.awg_close()
    file_handler.save_data(file_data, data, header = header, mode = 'w')
    sys.exit(0)

signal.signal(signal.SIGTERM, cleanup)

### Experimental parameters
POINTS = 75
FIELD = 3449
AVERAGES = 32
SCANS = 1
process = 'None'
STEP = 4   # in NS;
PHASE_STEPS = 16

# PULSES
PULSE_1_LENGTH = '260 ns'
PULSE_2_LENGTH = '130 ns'
PULSE_3_LENGTH = '260 ns'
PULSE_4_LENGTH = '130 ns'

PULSE_AWG_1_START = '0 ns'
PULSE_AWG_2_START = '500 ns'
PULSE_AWG_3_START = '1000 ns'
PULSE_AWG_4_START = '1600 ns'

FREQ = ('0 MHz', '368 MHz')
FUNC = 'WURST'


# NAMES
EXP_NAME = 'SIFTER_AWG'

# Setting pulses
awg.awg_pulse(name = 'P0', channel = 'CH0', func = FUNC, frequency = FREQ, phase = 0, \
            length = PULSE_1_LENGTH, sigma = PULSE_1_LENGTH, start = PULSE_AWG_1_START, \
            phase_list = ['+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x'], n = 30, d_coef = 3.85)
awg.awg_pulse(name = 'P1', channel = 'CH0', func = FUNC, frequency = FREQ, phase = 0, \
            length = PULSE_2_LENGTH, sigma = PULSE_2_LENGTH, start = PULSE_AWG_2_START, delta_start = str(int(STEP)) + ' ns', \
            phase_list = ['+x', '+y', '-x', '-y', '+x', '+y', '-x', '-y', '+x', '+y', '-x', '-y', '+x', '+y', '-x', '-y'], n = 30)
awg.awg_pulse(name = 'P2', channel = 'CH0', func = FUNC, frequency = FREQ, phase = 0, \
            length = PULSE_3_LENGTH, sigma = PULSE_3_LENGTH, start = PULSE_AWG_3_START, delta_start = str(int(STEP*2)) + ' ns', \
            phase_list = ['+y', '+y', '+y', '+y', '-y', '-y', '-y', '-y', '+y', '+y', '+y', '+y', '-y', '-y', '-y', '-y'], n = 30, d_coef = 3.85)
awg.awg_pulse(name = 'P3', channel = 'CH0', func = FUNC, frequency = FREQ, phase = 0, \
            length = PULSE_4_LENGTH, sigma = PULSE_4_LENGTH, start = PULSE_AWG_4_START, delta_start = str(int(STEP)) + ' ns', \
            phase_list = ['+x', '+x', '+x', '+x', '+x', '+x', '+x', '+x', '-x', '-x', '-x', '-x', '-x', '-x', '-x', '-x'], n = 30)

awg.awg_sample_rate(1000)
awg.awg_channel('CH0', 'CH1')
awg.awg_card_mode('Single Joined')
awg.awg_setup()

dig4450.digitizer_read_settings()
dig4450.digitizer_number_of_averages(AVERAGES)
time_res = int( 1000 / int(dig4450.digitizer_sample_rate().split(' ')[0]) )
# a full oscillogram will be transfered
wind = dig4450.digitizer_number_of_points()
cycle_data_x = np.zeros( (PHASE_STEPS, int(wind)) )
cycle_data_y = np.zeros( (PHASE_STEPS, int(wind)) )
data = np.zeros( (2, int(wind), POINTS) )

# Plot initialization
process = general.plot_2d(EXP_NAME, data, start_step = ( (0, time_res), (0, 2*STEP) ), xname = 'Time',\
    xscale = 'ns', yname = 'Delay', yscale = 'ns', zname = 'Intensity', zscale = 'V', pr = process, \
    text = 'Scan / Time: ' + str(1) + ' / ' + str(0*2*STEP))

# Data saving
header = 'Date: ' + str(datetime.datetime.now().strftime("%d-%m-%Y %H-%M-%S")) + '\n' + \
         'T2 Measurement; AWG Baseline\n' + 'Field: ' + str(FIELD) + ' G \n' + \
          'Number of Scans: ' + str(SCANS) + '\n' +\
          'Averages: ' + str(AVERAGES) + '\n' + 'Points: ' + str(POINTS) + '\n' + 'Window: ' + str(wind * time_res) + ' ns\n' \
          + 'Horizontal Resolution: ' + str(time_res) + ' ns\n' + 'Vertical Resolution: ' + str(2*STEP) + ' ns\n' + \
          'AWG Pulse List: ' + '\n' +\
          str(awg.awg_pulse_list()) + '2D Data'

file_data, file_param = file_handler.create_file_parameters('.param')
file_handler.save_header(file_param, header = header, mode = 'w')

# Data acquisition
for j in general.scans(SCANS):

    for i in range(POINTS):

        # phase cycle
        k = 0
        while k < PHASE_STEPS:

            prDig = returnThread.rThread(target = dig4450.digitizer_get_curve, args=())
            prDig.start()
            
            awg.awg_next_phase()
            x_axis, cycle_data_x[k], cycle_data_y[k]  = prDig.join()

            awg.awg_stop()
            k += 1
        
        # acquisition cycle
        x, y = pb.pulser_acquisition_cycle(cycle_data_x, cycle_data_y, \
                acq_cycle = ['+', '-', '+', '-', '+', '-', '+', '-', '+', '-', '+', '-', '+', '-', '+', '-'])
        
        data[0, :, i] = ( data[0, :, i] * (j - 1) + x ) / j
        data[1, :, i] = ( data[1, :, i] * (j - 1) + y ) / j

        process = general.plot_2d(EXP_NAME, data, start_step = ( (0, time_res), (0, 2*STEP) ), xname = 'Time',\
            xscale = 'ns', yname = 'Delay', yscale = 'ns', zname = 'Intensity', zscale = 'V', pr = process, \
            text = 'Scan / Time: ' + str(j) + ' / ' + str(i*2*STEP))

        awg.awg_shift()

    awg.awg_pulse_reset()

dig4450.digitizer_stop()
dig4450.digitizer_close()
awg.awg_stop()
awg.awg_close()

file_handler.save_data(file_data, data, header = header, mode = 'w')
