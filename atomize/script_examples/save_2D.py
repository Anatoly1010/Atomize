import numpy as np
import atomize.general_modules.csv_opener_saver as openfile

file_handler = openfile.Saver_Opener()

header = 'save 2D'
POINTS = 100

### SAVE
file_data = file_handler.create_file_dialog()

data = np.random.normal(size = (POINTS, POINTS))

file_handler.save_data(file_data, data, header = header, mode = 'w')

### OPEN
#file_path = file_handler.open_file_dialog()
#header, data = file_handler.open_2d(file_path)

