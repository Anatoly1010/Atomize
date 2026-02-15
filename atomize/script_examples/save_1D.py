import numpy as np
import atomize.general_modules.csv_opener_saver as openfile

file_handler = openfile.Saver_Opener()

header = 'save 1D'
POINTS = 100

### SAVE
file_data = file_handler.create_file_dialog()

x_axis = np.arange(POINTS)
data_x = np.random.normal(size = POINTS)
data_y = np.random.normal(size = POINTS)

file_handler.save_data(file_data, np.c_[x_axis, data_x, data_y], header = header, mode = 'w')

### OPEN
#file_path = file_handler.open_file_dialog()
#header, data = file_handler.open_1d(file_path)
