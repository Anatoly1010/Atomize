import sys
import time
import socket
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.Tektronix_4000_Series as t4032
import atomize.general_modules.csv_opener_saver_tk_kinter as openfile

open1d = openfile.Saver_Opener()
t4032 = t4032.Tektronix_4000_Series()
data = []
i = 9632

path_to_file = open1d.create_file_dialog(directory='')

#f = open(path_to_file,'a')

if len(sys.argv) > 1:
    test_flag = sys.argv[1]
else:
    test_flag = 'None'

t4032.oscilloscope_record_length(1000)
t4032.oscilloscope_number_of_averages(2)

## 2D Plot tests
while i <= 9732:
    i = i + 1

    temp = str(i)
    if len( temp ) == 4:
        temp = '0' + temp
    elif len( temp ) == 5:
        temp = temp

    general.message(str(i))
    MESSAGE = b'\x04' + b'\x08' + b'\x00' + b'\x00' + b'\x00' + temp.encode()

    if test_flag != 'test':
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect( ('172.16.16.20', 8890) )

        sock.sendto( MESSAGE, ('172.16.16.20', 8890) )

        data_raw, addr = sock.recvfrom(10)

        sock.shutdown(socket.SHUT_RDWR)
        sock.close()

    elif test_flag == 'test':
        pass

    general.wait('40 ms')

    t4032.oscilloscope_start_acquisition()

    y = t4032.oscilloscope_get_curve('CH2')
    data.append(y)

    general.plot_2d('Plot Z Test2', data, start_step=( (0, 0.2), (9.632, 0.001) ), xname='Time',\
        xscale='ns', yname='Frequency', yscale='GHz', zname='Intensity', zscale='V')

    f = open(path_to_file,'a')

    np.savetxt(f, y, fmt='%.10f', delimiter=' ', newline='\n', header='frequency: %d' % i, footer='', comments='#', encoding=None)

    f.close()
