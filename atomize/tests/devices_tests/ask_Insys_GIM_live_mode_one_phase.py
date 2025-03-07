import sys
import time
import signal
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.Insys_FPGA as pb_pro

def cleanup(*args):
    pb.pulser_close()
    #file_handler.save_data(file_data, np.c_[x_axis, data_x, data_y], header = header, mode = 'w')
    sys.exit(0)

signal.signal(signal.SIGTERM, cleanup)

pb = pb_pro.Insys_FPGA()

POINTS = 1
PHASES = 1
DETECTION_WINDOW = 1635.2 * 1

TR_ADC = round(3.2 / 8, 1)

WIN_ADC = int( (DETECTION_WINDOW / TR_ADC) )
CURVE_NAME = 'LIVE'

pb.pulser_pulse(name = 'P1', channel = 'MW' , start = '320 ns'  , length = '32 ns', phase_list =  ['+x']) #, phase_list =  ['+x', '-x']
pb.pulser_pulse(name = 'P2', channel = 'MW' , start = '448 ns', length = '32 ns', phase_list =  ['+x']) # , delta_start='3.2 ns', phase_list =  ['+x', '+x']
pb.pulser_pulse(name = 'P4', channel = 'TRIGGER' , start = '0 ns', length = str( DETECTION_WINDOW ) + ' ns') #, delta_start='6.4 ns'

data = np.zeros( ( 2, WIN_ADC, POINTS ) )
x_axis = np.linspace(0, ( DETECTION_WINDOW - TR_ADC), num = WIN_ADC) 

pb.pulser_repetition_rate('500 Hz')
pb.pulser_open()

pb.digitizer_number_of_averages(10)

for j in general.to_infinity():

    for i in range(PHASES):

        pb.pulser_next_phase()
        data[0], data[1] = pb.digitizer_get_curve( POINTS, PHASES, acq_cycle = ['-y'], live_mode = 1 )

        general.plot_1d('1D', x_axis, ( data[0].ravel(), data[1].ravel() ), xname = 'Time',\
                    xscale = 'ns', yname = 'Intensity', yscale = 'mV', label = CURVE_NAME )

    #pb.pulser_pulse_reset()


pb.pulser_close()


