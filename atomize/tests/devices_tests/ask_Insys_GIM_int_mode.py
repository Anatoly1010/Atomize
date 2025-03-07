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

POINTS = 50
PHASES = 2
SCANS = 1
STEP = 6.4
DETECTION_WINDOW = 1635.2
NUM_AVE = 100
pb.digitizer_decimation(1)
DEC_COEF = pb.digitizer_decimation()

CURVE_NAME = 'INT'

pb.pulser_pulse(name = 'P1', channel = 'MW' , start = '320 ns', length = '32 ns', phase_list =  ['+x', '-x']) #, phase_list =  ['+x', '-x', '+x', '-x']
pb.pulser_pulse(name = 'P2', channel = 'MW' , start = '416 ns', length = '32 ns', delta_start='3.2 ns', phase_list = ['+x', '+x']) #, phase_list =  ['+x', '+x', '+x', '-x']
pb.pulser_pulse(name = 'P4', channel = 'TRIGGER' , start = '0 ns', length = str(DETECTION_WINDOW ) + ' ns', delta_start='6.4 ns')

x_axis = np.linspace(0, ( STEP*(POINTS - 1) ), num = POINTS) 
data = np.zeros( ( 2, POINTS ) )

a = time.time()
pb.pulser_repetition_rate('500 Hz')
pb.pulser_open()
pb.digitizer_number_of_averages(NUM_AVE)
pb.digitizer_read_settings()

for k in general.scans(SCANS):

    for j in range( int( POINTS ) ):

        for i in range(PHASES):

            pb.pulser_next_phase()
            data[0], data[1] = pb.digitizer_get_curve( POINTS, PHASES, acq_cycle = ['+x', '+x'], integral = True )

            general.plot_1d('1D', x_axis, ( data[0], data[1] ), xname = 'Time',\
                        xscale = 'ns', yname = 'Intensity', yscale = 'mV', label = CURVE_NAME, text = 'Scan: ' + str(j) )

        
        pb.pulser_shift()

    pb.pulser_pulse_reset()


general.message( round(time.time() - a, 1) )
general.message( f'CALCULATED: {POINTS * PHASES * SCANS * NUM_AVE / 1000}' )

pb.pulser_close()

