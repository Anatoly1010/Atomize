import time
import atomize.general_modules.general_functions as general
import atomize.device_modules.Bruker_Xepr as xepr

xfc = xepr.Bruker_Xepr()

general.message(xfc.magnet_name())
general.message(f'Field now: {xfc.magnet_field()} G')

# small sweep around 4000 G and back
xfc.magnet_setup(4000, 10)
for i in range(3):
    general.message(f'Sweep up: {xfc.magnet_sweep_up()} G')
t = time.perf_counter()
general.message(f'Reset: {xfc.magnet_reset_field()} G')
general.message(f'One set call: {(time.perf_counter() - t) * 1e3:.1f} ms')
general.message(f'Readback: {xfc.magnet_field()} G')

xfc.close_connection()
