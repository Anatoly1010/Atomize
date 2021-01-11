import time
import numpy as np
from liveplot import LivePlotClient
import atomize.device_modules.config.messenger_socket_client as send
import atomize.device_modules.SR_860 as sr

#plotter = LivePlotClient()

sr.connection()
sr.lock_in_sensitivity('300 mV')
x=sr.lock_in_sensitivity()
#x = sr_810.lock_in_noise_y()
#y = sr_810.lock_in_signal()
print(x)
#print(y)

#sr_810.close_connection()