import keysight_3034T as dsox3034t
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

fig, ax = plt.subplots ()


# INITIALIZATION

start_time = datetime.now()


dsox3034t.connection()

#dsox2012a.scope_timeresolution()
#dsox2012a.scope_acquisition_type(1)
#dsox2012a.scope_record_length(16000)
dsox3034t.scope_wave_freq(1000)
points = dsox3034t.scope_wave_width()
#print(dsox2012a.scope_read_preamble("CH1"))
#resolution = dsox2012a.scope_timeresolution()
#dsox2012a.scope_number_of_averages(5)
print(points)

# ACQUISITION
#dsox2012a.scope_start_acquisition()
#array_y=dsox2012a.scope_get_curve("CH1")

#print(array_y)

dsox3034t.close_connection()

# PLOTTING
#array_x= list(map(lambda x: resolution*(x+1), list(range(points))))
#final_data = list(zip(array_x,array_y))


#end_time=datetime.now()
#print("Full time: {}".format(end_time - start_time))

#ax.plot(np.array(final_data)[:,0],np.array(final_data)[:,1])
#ax.set_xlabel("Time (mcs)",weight = "bold")
#ax.set_ylabel("Intensity (a.u.)",weight = "bold")

#plt.show()
#plt.show()

#start_time = datetime.now()
#end_time=datetime.now()
#print("Duration: {}".format(end_time - start_time))
