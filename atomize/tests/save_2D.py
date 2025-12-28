import numpy as np
import atomize.general_modules.csv_opener_saver_tk_kinter as openfile
#import atomize.general_modules.csv_opener_saver as openfile

file_handler = openfile.Saver_Opener()

header = 'save 2D'
POINTS = 100

### OPTION 1
file_data, file_param = file_handler.create_file_parameters('.param')
file_handler.save_header(file_param, header = header, mode = 'w')

data = np.random.normal(size = (POINTS, POINTS))

###

file_handler.save_data(file_data, data, header = header, mode = 'w')

### OPTION 2
#data = np.random.normal(size = (POINTS, POINTS))

#file_handler.save_2D_dialog( data, header = header )

###