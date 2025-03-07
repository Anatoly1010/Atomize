import time
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.Insys_FPGA_AM as pb_pro

pb = pb_pro.Insys_FPGA()

POINTS = 400
PHASES = 1
SCANS = 1
DETECTION_WINDOW = 819.2
NUM_AVE = 50
pb.digitizer_decimation(4)
DEC_COEF = pb.digitizer_decimation()

pb.pulser_pulse(name = 'P1', channel = 'MW' , start = '320 ns', length = '32 ns') #, phase_list =  ['+x', '-x', '+x', '-x']
pb.pulser_pulse(name = 'P2', channel = 'MW' , start = '448 ns', length = '32 ns', delta_start='3.2 ns') #, phase_list =  ['+x', '+x', '+x', '-x']
pb.pulser_pulse(name = 'P4', channel = 'TRIGGER' , start = '0 ns', length = str(DETECTION_WINDOW ) + ' ns', delta_start='6.4 ns')

data = np.zeros( ( 2, int( (DETECTION_WINDOW / 3.2) * 8 / DEC_COEF), int( POINTS ) ) )

a = time.time()
pb.pulser_repetition_rate('1000 Hz')
pb.pulser_open()
pb.digitizer_number_of_averages(NUM_AVE)

for k in general.scans(SCANS):

    for j in range( int(POINTS * PHASES) ):

        pb.pulser_update()
        data[0], data[1] = pb.digitizer_get_curve( POINTS, PHASES) #, acq_cycle = ['+x', '+x', '+x', '+x'] 
            
        general.plot_2d('2D', data, start_step = ( (0, 0.4 * DEC_COEF), (0, 102.4) ), xname = 'Time',\
                        xscale = 'ns', yname = 'Delay', yscale = 'ns', zname = 'Intensity', zscale = 'mV')
        
        pb.pulser_shift()

    pb.pulser_pulse_reset()


general.message( round(time.time() - a, 1) )
general.message( f'CALCULATED: {POINTS * PHASES * SCANS * NUM_AVE / 1000}' )

pb.pulser_close()

