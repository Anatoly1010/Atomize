import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.Cryomech_CPA1110 as cpa

cpa1110 = cpa.Cryomech_CPA1110()

general.message(cpa1110.cryogenic_refrigerator_status_data())
#general.message(cpa1110.cryogenic_refrigerator_state())
#general.message(cpa1110.cryogenic_refrigerator_warning_data())
#general.message(cpa1110.cryogenic_refrigerator_pressure_scale())
#general.message(cpa1110.cryogenic_refrigerator_temperature_scale())
#general.message(cpa1110.cryogenic_refrigerator_state('On'))
#general.message(cpa1110.cryogenic_refrigerator_state())


