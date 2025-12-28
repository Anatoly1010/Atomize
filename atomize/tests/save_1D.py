import numpy as np
import atomize.general_modules.csv_opener_saver_tk_kinter as openfile
#import atomize.general_modules.csv_opener_saver as openfile

file_handler = openfile.Saver_Opener()

header = 'save 1D'
POINTS = 100

### OPTION 1
file_data, file_param = file_handler.create_file_parameters('.param')
file_handler.save_header(file_param, header = header, mode = 'w')

x_axis = np.arange(POINTS)
data_x = np.random.normal(size = POINTS)
data_y = np.random.normal(size = POINTS)

###

file_handler.save_data(file_data, np.c_[x_axis, data_x, data_y], header = header, mode = 'w')

### OPTION 2
#x_axis_2 = np.arange(POINTS)
#data_x_2 = np.random.normal(size = POINTS)
#data_y_2 = np.random.normal(size = POINTS)

#file_handler.save_1D_dialog( (x_axis_2, data_x_2, data_y_2), header = header )

###