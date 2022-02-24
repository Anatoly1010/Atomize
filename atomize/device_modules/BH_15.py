#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import gc
import sys
import math
import atomize.device_modules.config.config_utils as cutil
import atomize.general_modules.general_functions as general

"""
Programming this field controller became a bit of a mess because of the
number of conditions to be taken into consideration:

1. Field range is -50 G to 23000 G
2. CF must be set with a resolution of 50 mG
3. Sweep range limits 0 G to 16000 G
4. Sweep range resolution: 100 mG
5. CF plus or minus 0.5 time sweep range may never excced the field
   range limits
6. Sweep range is not truely symmetric (in contrast to what the manual
   claims), SWA settings can range from 0 to 4095, the generated field
   is equal to CF for SWA = 2048
7. Repeatability of CF setting: 5 mG
8. The current field can't be measured since when switching to measurement
   mode the currently set field isn't kept but is set back to zero.
"""

class BH_15:
    #### Device specific functions
    def __init__(self):

        #### Inizialization
        # setting path to *.ini file
        self.path_current_directory = os.path.dirname(__file__)
        self.path_config_file = os.path.join(self.path_current_directory, 'config','BH_15_config.ini')

        # configuration data
        self.config = cutil.read_conf_util(self.path_config_file)
        self.specific_parameters = cutil.read_specific_parameters(self.path_config_file)

        # Ramges and limits
        self.min_swa = 0
        self.center_swa = 2048
        self.max_swa = 4095
        """
        The maximum field resolution: this is, according to the manual the best
        result that can be achieved when repeatedly setting the center field and
        it doesn't seem to make too much sense to set a new field when the
        difference from the current field is below this resolution.
        """
        self.fc_resolution = 0.005
        # Maximum resolution that can be used for sweep ranges
        self.fc_sw_resolution = 0.1
        """
        As Mr. Antoine Wolff from Bruker pointed out to me the center field
        can only be set with a resolution of 50 mG (at least for the ER032M,
        but I guess that also holds for the BH15).
        """
        self.fc_cf_resolution = 0.05
        # Define the maximum number of retries before giving up if the
        # overload LED is on.
        self.max_retries = 300
        """
        To make sure the new setting for a center field or sweep width setting
        does arrive at the device we general it BH15_FC_MAX_SET_RETRIES times.
        Remember, this is a device by Bruker...
        """
        self.max_set_retries = 2

        self.max_sweep_width = 16000.0
        self.min_field = -50.0
        self.max_field = 23000.0
        self.min_field_step = 0.001
        self.max_recursion = 20
        self.max_add_steps = 100

        # Test run parameters
        # These values are returned by the modules in the test run 
        if len(sys.argv) > 1:
            self.test_flag = sys.argv[1]
        else:
            self.test_flag = 'None'

        if self.test_flag != 'test':
            if self.config['interface'] == 'gpib':
                try:
                    import Gpib
                    self.status_flag = 1
                    self.device = Gpib.Gpib(self.config['board_address'], self.config['gpib_address'])
                    try:
                        #test should be here
                        self.status_flag = 1
                        # Switch off service requests
                        self.device_write('SR0')
                        # Switch to mode 0, i.e. field-controller mode via internal sweep-address-generator
                        self.device_write('MO0')
                        # Set IM0 sweep mode (we don't use it, just to make sure we don't trigger a sweep start inadvertently)
                        self.device_write('IM0')
                        # The device seems to need a bit of time after being switched to remote mode
                        general.wait('1 s')
                    except BrokenPipeError:
                        general.message("No connection")
                        self.device.close()
                        self.status_flag = 0
                        sys.exit()              
                except BrokenPipeError:
                        general.message("No connection")
                        self.device.close()
                        self.status_flag = 0
                        sys.exit()

        elif self.test_flag == 'test':
            self.test_field = 3500

        self.act_field = None       # the real current field
        self.is_act_field = False   # set if current field is known
        self.sf = None              # the current center field (CF) setting
        self.sw = None              # the current sweep width (SW) setting
        self.swa = None             # the current sweep address (SWA) setting
        self.is_sw = False          # set if sweep width is known
        self.max_sw = None          # maximum sweep width
        self.swa_step = None        # field step between two sweep addresses (SWAs)
        self.step_incr = None       # how many SWAs to step for a sweep step
        self.start_field = None     # the start field given by the user
        self.field_step = None      # the field steps to be used
        self.is_init = False        # flag, set if magnet_setup() has been called
        self.max_field_dev = 0.     # maximum field deviation (in test run)

        self.max_sw = self.max_sweep_width
        if self.max_sw > self.max_field - self.min_field:
            self.max_sw = self.max_field - self.min_field

    def magnet_name(self):
        if self.test_flag != 'test':
            answer = self.config['name']
            return answer
        elif self.test_flag == 'test':
            answer = self.config['name']
            return answer

    def magnet_setup(self, start_field, field_step):
        """
        Function for registering the start field and the
        field step size during the PREPARATIONS section.    
        """
        # Check that both the variables, i.e. the start field and the field step 
        # size are reasonable.
        start_field = round(start_field/self.min_field_step)*self.min_field_step
        self.field_check(start_field)
        #  Get the field step size and round it to the next allowed value
        # (resulting in a sweep step resolution of about 25 uG with the
        # given setting for the sweep width resolution of 0.1 G)

        if field_step < self.min_field_step:
            general.message(f"Field sweep step size {field_step} G too small \
                , minimum is {self.min_field_step} G.")
            sys.exit()

        field_step = round(self.max_swa*field_step/self.fc_sw_resolution)*self.fc_sw_resolution/self.max_swa;
        """
        We would get into problems with setting the field exactly for start
        fields not being multiples of the center field resolution and field
        steps that are larger than the center field resolution when we have
        to shift the center field during a longer sweep. Thus we readjust
        the start field in these cases.
        """
        rem = round(start_field/self.min_field_step) %\
         round(self.fc_cf_resolution/self.min_field_step)

        if rem > 0 & (round(field_step/self.min_field_step) % round(self.fc_cf_resolution/self.min_field_step)) == 0:
            start_field = round(start_field/self.fc_cf_resolution)*self.fc_cf_resolution;
            general.message(f"Readjusting start field to {start_field} G.")

        self.start_field = start_field
        self.field_step = field_step
        self.is_init = True

        if self.is_init == True:
            # self.fc_start_field()
            # 16-08-2021; NIOCH First initialization problem
            try:
                self.fc_start_field()
            except BrokenPipeError:
                #pass
                self.fc_start_field()

        #?
        if (self.is_init and self.max_field_dev/self.field_step >= 0.01) or (self.is_init == False \
        and self.is_act_field and math.floor(self.max_field_dev/self.fc_resolution) >= 1):
            general.message(f"Maximum field error during experiment was {self.max_field_dev*1000} mG.")
            self.max_field_dev = 0.0
            self.is_act_field = False

    def magnet_sweep_up(self):
        if self.is_init != True:
            general.message("No sweep step size has been set - you must call the function magnet_setup() to be able to do sweeps.")
            sys.exit()
        # Check that the new field value is still within the allowed range
        self.field_check(self.act_field + self.field_step)
        """
        If the new field is still within the sweep range set the new field by
        changing the SWA, otherwise shift the center field up by a quarter of
        the total sweep width. If this would move the upper sweep limit above
        the maximum allowed field move the center field only as far as
        possible.
        """
        if (self.swa + self.step_incr <= self.max_swa):
            self.swa = self.swa + self.step_incr
            self.fc_set_swa(self.swa)
        else:
            if (self.cf + 0.75*self.sw < self.max_field):
                steps = self.max_swa/4
            else:
                steps = round(math.floor((self.max_field - self.cf)/self.swa_step)) - self.center_swa
            """
            We also need the center field to be a multiple of the center field
            resolution. If necessary shift the center field by as many swep
            steps until this condition is satisfied (with a deviation of not
            more than 2 mG). And while we're at it also try to eliminate
            differences between the actual field and the field the user is
            expecting.
            """
            new_swa = self.swa - steps + self.step_incr;
            diff = self.cf + (self.swa - self.center_swa)*self.swa_step - self.act_field
            new_cf = self.cf - diff + steps*self.swa_step

            """
            When we're extremely near to the maximum field it may happen that
            the field can't be set with a useful combination of CF and SWA.
            """
            if new_swa > self.max_swa or new_cf + 0.5*self.sw > self.max_field:
                general.message(f"Cannot set field of {self.act_field + self.field_step} G.")
            
            self.fc_best_fit_search(new_cf, new_swa, True, 2)

            assert(new_swa >= self.min_swa and new_swa <= self.max_swa and (new_cf - 0.5*self.sw) >= self.min_field\
                and (new_cf + 0.5*self.sw) <= self.max_field), "Incorrect parameters. Probably field is out of range."

            self.swa = new_swa
            self.fc_set_swa(self.swa)
            self.cf = fc_set_cf(new_cf)

 
        self.fc_test_leds()

        self.fc_deviation(self.act_field + self.field_step)
        self.act_field = self.cf + (self.swa - self.center_swa )*self.swa_step
        
        return self.act_field

    def magnet_sweep_down(self):
        if self.is_init != True:
            general.message("No sweep step size has been set - you must call the function magnet_setup() to be able to do sweeps.")
            sys.exit()

        self.field_check(self.act_field - self.field_step)

        """
        If the new field is still within the sweep range set the new field by
        changing the SWA, otherwise shift the center field down by a quarter of
        the total sweep width. If this would move the lower sweep limit below
        the minimum allowed field move the center field only as far as
        possible.
        """
        if (self.swa - self.step_incr >= self.min_swa):
            self.swa = self.swa - self.step_incr
            self.fc_set_swa(self.swa)
        else:
            if (self.cf - 0.75*self.sw > self.min_field):
                steps = self.max_swa/4
            else:
                steps = round(math.floor((self.cf - self.min_field)/self.swa_step)) - self.center_swa
            """
            We also need the center field to be a multiple of the center field
            resolution. If necessary shift the center field by as many swep
            steps until this condition is satisfied (with a deviation of not
            more than 2 mG)
            """
            new_swa = self.swa + steps - self.step_incr;
            diff = self.cf + (self.swa - self.center_swa)*self.swa_step - self.act_field
            new_cf = self.cf - diff - steps*self.swa_step

            # When we're extremely near to the minimum field it may happen that
            # the field can't be set with a useful combination of CF and SWA
            if new_swa < self.min_swa or new_cf - 0.5*self.sw < self.min_field:
                general.message(f"Can't set field of {self.act_field + self.field_step} G.")
            
            self.fc_best_fit_search(new_cf, new_swa, False, 2);

            assert(new_swa >= self.min_swa and new_swa <= self.max_swa and (new_cf - 0.5*self.sw) >= self.min_field\
                and (new_cf + 0.5*self.sw) <= self.max_field), "Incorrect parameters. Probably field is out of range."

            self.swa = new_swa
            self.fc_set_swa(self.swa)
            self.cf = self.fc_set_cf(new_cf)

        self.fc_test_leds()

        self.fc_deviation(self.act_field - self.field_step)
        self.act_field = self.cf + (self.swa - self.center_swa )*self.swa_step
        
        return self.act_field

    def magnet_reset_field(self):
        if self.is_init != True:
            general.message("Start field has not been defined  - you must call the function magnet_setup() before.")
            sys.exit()
        self.fc_start_field()

        return self.act_field   

    def magnet_field(self, *field):
        if self.test_flag != 'test':
            if len(field) == 1:
                self.set_field(field[0])
                return self.get_field()
            elif len(field) == 0:
                return self.get_field()
            else:
                general.message("Incorrect argument")
                sys.exit()

        elif self.test_flag == 'test':
            if len(field) == 1:
                self.set_field(field[0])
                return self.get_field()
            elif len(field) == 0:
                return self.get_field()
            else:
                assert(1 == 2), "Incorrect argument"

    def magnet_field_step_size(self, *step):
        """
        Function returns the minimum field step size if called without
        an argument and the possible field step size nearest to the
        argument.
        """
        if self.test_flag != 'test':
            if len(step) == 0:
                return self.fc_resolution
            elif len(step) == 1:
                field_step = float(step[0])
                if field_step < 0.:
                    general.message("Invalid negative field step size.")
                    sys.exit()
                steps = round(field_step/self.fc_resolution)
                if steps == 0:
                    steps += 1

                return steps*self.fc_resolution
            else:
                general.message("Invalid argument")
                sys.exit()

        elif self.test_flag == 'test':
            if len(step) == 0:
                return self.fc_resolution
            elif len(step) == 1:
                field_step = float(step[0])
                assert(field_step >= 0), "Invalid negative field step size."
                steps = round(field_step/self.fc_resolution)
                if steps == 0:
                    steps += 1
                return steps*self.fc_resolution

    # Auxiliary functions
    def get_field(self):
        if self.test_flag != 'test':
            if self.is_act_field != True:
                general.message("Field hasn't been set yet and is thus still unknown.")
                sys.exit()

            return self.act_field

        elif self.test_flag == 'test':
            #self.act_field = self.test_field
            return self.act_field

    def set_field(self, field):
        field = float(field)
        self.field_check(field)

        if self.is_act_field != True:
            return self.fc_initial_field_setup(field)

        return self.fc_set_field(field)
    
    def fc_initial_field_setup(self, field):
        """
        Function for initializing everything related to the field setting,
        called if there was no call of magnet_init() and the field gets
        set for the very first time.
        """
        self.act_field = float(field)
        self.is_act_field = True

        rem = (round(self.act_field/self.min_field_step) % round(self.fc_cf_resolution/self.min_field_step))\
         * self.min_field_step

        if rem <= 2*self.min_field_step:
            self.swa = self.fc_set_swa(self.center_swa)
            self.sw = self.fc_set_sw(0.)
            self.cf = self.fc_set_cf(self.act_field)
        else:
            self.fc_set_sw(0.)
            self.cf = self.fc_set_cf(self.act_field - rem)
            self.swa = self.center_swa + 1
            self.fc_set_swa(self.swa)
            self.sw = self.fc_set_sw(self.max_swa*rem)

        self.fc_test_leds()

        self.fc_deviation(self.act_field)

        self.act_field = self.cf + (self.swa - self.center_swa)*self.swa_step
        return self.act_field

    def fc_set_field(self, field):
        """
        This function is called when the user asks for setting a new field.
        One important point here is to change the center field only if
        absolutely necessary. We have to distinguish several cases:
        1. There is no sweep step size set and thus the sweep width is set
           to zero. In this case we try to guess a step size from the
           difference between the currrent field and the target field. This
           is used to set a sweep width, and if we're lucky (i.e. the user
           does not require random field changes in the future) we can use
           the SWAs also for later field changes.
        2. If there is a sweep width set but there was no magnet_setup()
           call we try to set the field using SWAs if one of them fits the
           the new field value. If not we have to shift the center field,
           but we first try to keep the change as small as possible.
           Because our guess about the typical field changes didn't work
           out we also have to adapt the sweep width.
        3. If magnet_setup() has been called changing the sweep width can't
           be done. If possible the field change is done via changing the
           SWA, otherwise a combination of changing the SWA and shifting
           the center field is used.
        """
        field = float(field)
        assert(field >= self.min_field and field <= self.max_field), "Incorrect parameters"

        # If no field has been set before (and thus the module doesn't even
        # know what's the current field) do the initialization now
        if self.is_act_field != True:
            return self.fc_initial_field_setup(field)

        # We don't try to set a new field when the change is extremely small,
        # i.e. lower than the accuracy for setting a center field.
        if self.is_sw != True:
            self.fc_change_field_and_set_sw(field)
        else:
            if self.is_init != True:
                self.fc_change_field_and_sw(field)
            else:
                self.fc_change_field_and_keep_sw(field)

        self.fc_test_leds()

        self.fc_deviation(field)
        
        self.act_field = self.cf + (self.swa - self.center_swa)*self.swa_step

        return self.act_field

    def fc_start_field(self):
        """
        Function sets up the magnet in case magnet_setup() had been called,
        assuming that field will be changed via sweep_up() or sweep_down()
        calls, in which case the sweep usually can be done via changes of
        the SWA and without changing the center field. The center field is
        set to the required start field trying to achieve that up and down
        sweeps can be done without changing the center field.   
        """
        self.cf = self.start_field
        self.sw = self.max_swa*self.field_step
        self.swa = self.center_swa
        self.swa_step = self.field_step
        self.step_incr = 1

        """
        Make sure that the sweep width isn't larger than the maximum sweep
        width, otherwise divide it by two as often as needed and remember
        that we now have to step not by one SWA but by a power of 2 SWAs.
        """
        if self.sw > self.max_sw:
            factor = round(math.ceil(self.sw/self.max_sw))
            self.sw = self.sw/factor
            self.swa_step = self.swa_step/factor
            self.step_incr = self.step_incr*factor

        """
        Sweep range must be a multiple of BH15_FC_SW_RESOLUTION and we adjust
        it silently to fit this requirement - hopefully, this isn't going to
        lead to any real field precision problems.
        """
        self.sw = self.fc_sw_resolution*round(self.sw/self.fc_sw_resolution)
        self.swa_step = self.sw / self.max_swa
        self.field_step = self.step_incr * self.swa_step

        """
        Make sure the sweep range is still within the allowed field range,
        otherwise shift the center field and calculate the SWA that's needed
        in this case. When the start field is extremely near to the limits
        it can happen that it's not possible to set the start field.
        """
        if (self.cf + 0.5*self.sw) > self.max_field:
            shift = round(math.ceil((self.cf + 0.5*self.sw - self.max_field)/self.swa_step))
            self.swa += shift
            self.cf -= shift*self.swa_step
        elif (self.cf - 0.5*self.sw) < self.min_field:
            shift = round(math.ceil((self.min_field-(self.cf - 0.5*self.sw))/self.swa_step))
            self.swa -= shift
            self.cf += shift*self.swa_step

        if (self.swa > self.max_swa) or (self.swa < self.min_swa) or ((self.cf + 0.5*self.sw)\
         > self.max_field) or ((self.cf - 0.5*self.sw) < self.min_field):
            print(f'Cannot set field of {self.start_field} G.')

        """
        Now readjust the SWA count a bit to make sure that the center field is
        a multiple of the maximum CF resolution (at least within accuracy of
        2 mG). This should always work out correctly because we made sure that
        either CF is already a multiple of the required resolution or the step
        size is below this resolution. So we can set the correct start field
        with a combination of a slightly shifted CF plus not too large a number
        of SWA steps (typically not more than 100).
        """
        self.fc_best_fit_search(self.cf, self.swa, self.cf >= 0.5*(self.max_field - self.min_field), 2)

        assert(self.swa >= self.min_swa and self.swa <= self.max_swa and (self.cf - 0.5*self.sw) >= self.min_field\
            and (self.cf + 0.5*self.sw) <= self.max_field), "Incorrect parameters"

        """
        Set the new field, sweep width and sweep address - in order to avoid
        accidentally going over the field limits in the process set the
        sweep width first to 0.
        """

        self.fc_set_sw(0.0)
        self.fc_set_cf(self.cf)
        self.fc_set_swa(self.swa)
        self.fc_set_sw(self.sw)

        self.fc_test_leds()

        self.is_sw = True
        self.fc_deviation(self.start_field)
        self.act_field = self.cf + (self.swa - self.center_swa )*self.swa_step
        self.is_act_field = True

    def fc_best_fit_search(self, cf, swa, dire, fac):

        add_steps = 0
        new_cf = cf
        new_swa = swa
        recursion_count = 0
        dir_change = False

        assert(new_swa >= self.min_swa and new_swa <= self.max_swa and (new_cf - 0.5*self.swa_step) >= self.min_field\
            and (new_cf + 0.5*self.swa_step) <= self.max_field), "Incorrect parameters. Probably field is out of range."

        if  dire == True:
            if new_swa == self.max_swa:
                return self.max_add_steps

            while new_swa < self.max_swa and (new_cf - 0.5*self.swa_step) > self.min_field:
                rem = round(abs(new_cf)/self.min_field_step) % round(self.fc_cf_resolution/self.min_field_step)
                if rem <= fac or (add_steps + 1) >= self.max_add_steps:
                    break
                new_swa += 1
                new_cf -= self.swa_step
        else:
            if new_swa == self.min_swa:
                return self.max_add_steps

            while new_swa > self.min_swa and (new_cf + 0.5*self.swa_step < self.max_field):
                rem = round(abs(new_cf)/self.min_field_step) % round(self.fc_cf_resolution/self.min_field_step)
                if rem <= fac or (add_steps + 1) >= self.max_add_steps:
                    break
                new_swa -= 1
                new_cf += self.swa_step

        if dir_change == False:
            if new_swa <= self.min_swa or new_swa >= self.max_swa or\
            new_cf - 0.5*self.sw < self.min_field or new_cf + 0.5*self.sw > self.max_field or\
            add_steps >= self.max_add_steps:
                new_cf = cf
                new_swa = swa

                dir_change = True
                add_steps = self.fc_best_fit_search(new_cf, new_swa, not dire, fac)
                dir_change = False

            if new_swa <= self.min_swa or new_swa >= self.max_swa or\
            new_cf - 0.5*self.sw < self.min_field or new_cf + 0.5*self.sw > self.max_field or\
            add_steps >= self.max_add_steps:
                if recursion_count >= self.max_recursion:
                    return self.max_add_steps
                new_cf = cf
                new_swa = swa

                recursion_count += 1
                self.fc_best_fit_search(new_cf, new_swa, dire, fac + 1)
                recursion_count -= 1

        cf = round(new_cf/self.fc_cf_resolution)*self.fc_cf_resolution
        swa = new_swa

        return add_steps

    def fc_set_sw(self, sweep_width):
        assert(sweep_width >= 0. and sweep_width <= self.max_sw), "Incorrect sweep width"

        sweep_width = self.fc_sw_resolution*round(sweep_width/self.fc_sw_resolution)
        if round(sweep_width/self.fc_sw_resolution) != 0:
            self.swa_step = sweep_width/self.max_swa
            self.is_sw = True
        else:
            self.swa_step = 0.
            self.is_sw = False

        if self.test_flag != 'test':
            i = self.max_set_retries
            while i > 0:
                i -= 1
                self.device_write(f'SW{sweep_width:.3f}')
        elif self.test_flag == 'test':
            pass

        return sweep_width

    def fc_set_cf(self, center_field):
        center_field = self.fc_cf_resolution*round(center_field/self.fc_cf_resolution)
        assert(center_field >= self.min_field and center_field <= self.max_field), "Incorrect center field"

        if self.test_flag != 'test':
            i = self.max_set_retries
            while i > 0:
                i -= 1
                self.device_write(f'CF{center_field:.3f}')
        elif self.test_flag == 'test':
            pass

        return center_field

    def fc_set_swa(self, sweep_address):
        """
        Function for setting sweep address.
        """
        assert(sweep_address >= self.min_swa and sweep_address <= self.max_swa), "Incorrect sweep address"

        if self.test_flag != 'test':
            i = self.max_set_retries
            while i > 0:
                i -= 1
                self.device_write(f'SS{sweep_address:.3f}')
        elif self.test_flag == 'test':
            pass

        return sweep_address

    def fc_change_field_and_set_sw(self, field):
        # Try to determine a sweep width so that we can set the field without
        # changing the center field, i.e. alone by setting a SWA.
        field = float(field)
        self.is_sw = self.fc_guess_sw(abs(field - self.cf))

        # If this fails we have to change the center field, otherwise we use the
        # newly calculated sweep width.
        if self.is_sw != True:
            rem = (round(field/self.min_field_step) % round( self.fc_cf_resolution/self.min_field_step))\
            *self.min_field_step
            if rem > self.min_field_step:
                self.cf = self.fc_set_cf(field - rem)
                self.swa = self.center_swa + 1
                self.fc_set_swa(self.swa)
                self.sw = self.fc_set_sw(self.max_swa*rem)
            else:
                self.sw = self.fc_set_sw(0.)
                self.cf = self.fc_set_cf(field)

        else:
            self.swa += round((field - self.cf)/self.swa_step)
            self.fc_best_fit_search(self.cf, self.swa, self.cf >= 0.5*(self.max_field - self.min_field), 2)

            if self.swa < self.min_swa or self.swa > self.max_swa or (self.cf - 0.5*self.sw) < self.min_field or \
            (self.cf + 0.5*self.sw) > self.max_field or (field - (self.cf + (self.swa - self.center_swa)*self.swa_step)) > \
            self.fc_resolution:
                rem = (round(field/self.min_field_step) % round(self.fc_cf_resolution/self.min_field_step))*self.min_field_step
                self.fc_set_sw(0.)
                self.cf = self.fc_set_cf(field - rem)
                self.swa = self.center_swa + 1 
                self.fc_set_swa(self.swa)
                self.sw = self.fc_set_sw(self.max_swa*rem)

            else:
                self.fc_set_sw(0.)
                self.cf = self.fc_set_cf(self.cf)
                self.fc_set_swa(self.swa)
                self.sw = self.fc_set_sw(self.sw)

    def fc_change_field_and_sw(self, field):
        # If the new field value can be reached (within an accuracy of 1% of the
        # SWA step size) by setting a SWA do just this.
        field = float(field)
        steps = round((field - self.act_field)/self.swa_step)

        if abs(abs(field - self.act_field) - self.swa_step*abs(steps)) < 0.01*self.swa_step and \
        (self.swa + steps) <= self.max_swa and (self.swa + steps) >= self.min_swa:
            self.swa = self.swa + steps
            self.fc_set_swa(self.swa)
            return

        self.fc_change_field_and_set_sw(field)

    def fc_change_field_and_keep_sw(self, field):
        """
        This function gets called for the set_field() EDL function when
        the magnet_setup() EDL function had also been called during the
        PREPARATION stage. In this case we can't change the sweep width
        and have to do our best trying to achieve the requested field
        with just changing the center field and the SWA count. Sometimes
        we will only be able to set the field with a certain deviation
        from the requested field.
        """

        # If the new field value can be reached (within an accuracy of 1% of the
        # SWA step size) by setting a SWA do just this.
        field = float(field)
        steps = round((field - self.act_field )/self.swa_step)

        if abs(abs(field - self.act_field) - self.swa_step*abs(steps)) < 0.01*self.swa_step and \
        (self.swa + steps) <= self.max_swa and (self.swa + steps) >= self.min_swa:
            self.swa += steps
            self.fc_set_swa(self.swa)
            return

        # Otherwise we start of with the center field set to the requested
        # field
        self.swa = self.center_swa
        self.cf = field

        # Make sure we don't get over the field limits (including halve the
        # sweep range)
        if (self.cf + 0.5*self.sw) > self.max_field:
            steps = round(math.ceil((self.cf + 0.5*self.sw - self.max_field)/self.swa_step))
            self.swa += steps
            self.cf  -= steps*self.swa_step
        elif (self.cf - 0.5*self.sw) < self.min_field:
            steps = round(math.ceil((self.min_field + 0.5*self.sw - self.cf)/self.swa_step))
            self.cf  += steps*self.swa_step   
            self.swa -= steps

        # When we're extremely near to the limits it's possible that there is
        # no combination of CF and SWA that can be used
        if self.swa > self.max_swa or self.swa < self.min_swa or (self.cf + 0.5*self.sw) > \
            self.max_field or (self.cf - 0.5*self.sw) < self.min_field:

            general.message(f"Can't set field of {field} G.")
            sys.exit()

        # Now we again got to deal with cases where the resulting center field
        # isn't a multiple of the CF resoultion...
        rem = round(self.cf/self.min_field_step) % round(self.fc_cf_resolution/self.min_field_step)

        if rem > 0:
            """
            If the new CF value isn't a multiple of the CF resolution but the
            step size is we can't adjust the field to the required value and
            must use the nearest possible field instead.
            """
            if round(self.swa_step/self.min_field_step) % round(self.fc_cf_resolution/self.min_field_step) == 0:
                self.cf = round(self.cf/self.fc_cf_resolution)*self.fc_cf_resolution
            else:
                # Otherwise try to adjust the field by a few additional SWA
                # steps in the right direction
                self.fc_best_fit_search(self.cf, self.swa, self.cf >= 0.5*(self.max_field - self.min_field), 2)

                assert(self.swa >= self.min_swa and self.swa <= self.max_swa and self.cf - 0.5*self.sw >= \
                self.min_field and self.cf + 0.5*self.sw <= self.max_field), "Incorrect parameters"

        self.cf = self.fc_set_cf(self.cf)
        self.fc_set_swa(self.swa)

    def fc_guess_sw(self, field_diff):
        """
        This function tries to guess a useful sweep range from the difference
        between the current center field and the target field so that the
        jump can be done by setting a SWA. If it isn't possible to find such
        a setting the function returns FAIL, otherwise both the entries sw,
        swa and swa_step in the magnet structure get set and OK is returned.
        """

        # For very small or huge changes we can't deduce a sweep range.
        if (field_diff*self.max_swa) < self.fc_sw_resolution or field_diff > self.max_sw/2:
            return False
        # This also doesn't work if the center field is nearer to one of the
        # limits than to the new field value.
        if (self.max_field - self.cf) < field_diff or (self.cf - self.min_field) < field_diff:
            return False

        # Now start with the step size set to the field difference
        swa_step = field_diff
        sw = self.max_swa*field_diff

        # The following reduces the sweep width to the maximum possible sweep
        # width and will always happen for field changes above 3.90625 G.
        if sw > self.max_sw:
            factor = round(math.ceil(sw/self.max_sw))
            sw = sw/factor
            swa_step = swa_step/factor

        # If with this corrected SWA step size the field change can't be achieved
        # give up.
        if swa_step*(self.center_swa-1) < field_diff:
            return False

        """
        We also can't use a sweep range that exceeds the maximum or minimum
        field (keeping the center field) thus we must reduce it further as
        far as necessary
        """
        i = 1
        while (self.cf + 0.5*sw/i) > self.max_field:
            sw = sw/i
            swa_step = swa_step/i
            i += 1

        i = 1
        while (self.cf - 0.5*sw/i) < self.min_field:
            sw = sw/i
            swa_step = swa_step/i
            i += 1

        sw = self.fc_sw_resolution*round(sw/self.fc_sw_resolution)
        swa_step = sw/self.max_swa

        if swa_step*(self.center_swa-1) < field_diff:
            return False

        self.sw = sw
        self.swa_step = swa_step
        self.swa = self.center_swa

        return True

    def fc_test_leds(self):
        """
        Function for testing LED indicators.
        """
        if self.test_flag != 'test':
            while True:
                is_overload = is_remote = False
                answer = self.device_query('LE')

                while answer and answer !='LE\r\n':
                    if answer=='LE1\r\n':
                        is_overload = True
                        break
                    elif answer == 'LE2\r\n':
                        general.message("Probehead thermostat not in equilibrilum.")
                        break
                    elif answer == 'LE4\r\n':
                        is_remote = True
                        break
                    else:
                        break

                    answer = int(answer) + 1;

                # If remote LED isn't on we're out of luck...
                if is_remote == False:
                    # 22-02-2022;
                    ###general.message("Device isn't in remote state.")
                    # 16-08-2021; NIOCH First initialization problem
                    pass
                    #raise BrokenPipeError
                    #sys.exit()
                
                # If there's no overload we're done, otherwise we retry several
                # times before giving up.
                if is_overload == False:
                    break

                if (self.max_retries - 1) > 0:
                    general.wait('1 s')
                else:
                    general.message("Field regulation loop not balanced.")
                    sys.exit()

        elif self.test_flag == 'test':
            pass

    def fc_deviation(self, field):
        """
        Function for calculating the new maximum value for the deviation
        between a requested and an achieved field.
        """
        d = abs(field - self.cf - (self.swa - self.center_swa)*self.swa_step)

        if d > self.max_field_dev:
            self.max_field_dev = d

    def field_check(self, field):
        field = float(field)
        if self.test_flag != 'test':
            if field > self.max_field:
                general.message(f"Field of {field} G is too high, maximum field is {self.max_field} G.")
                sys.exit()
            if field < self.min_field:
                general.message(f"Field of {field} G is too low, minimum field is {self.min_field} G.")
                sys.exit()
        if self.test_flag == 'test':
            assert(field <= self.max_field and field >= self.min_field), f"Field of {field} G is unavailable"

    def device_write(self, command):
        if self.status_flag == 1:
            try:
                command = str(str(command) + str(self.config['write_termination']))
                #print(command)
                self.device.write(command)
            except gpib.GpibError:
                general.message("No answer")
                sys.exit()
        else:
            general.message("No connection")
            sys.exit()

    def device_query(self, command):
        if self.config['interface'] == 'gpib':
            try:
                command = str(str(command) + str(self.config['read_termination']))
                #print(command)
                self.device.write(command)
                #general.wait('50 ms')
                answer = self.device.read().decode("utf-8")
                return answer
            except gpib.GpibError:
                general.message("No answer")
                sys.exit()
        else:
            general.message("No connection")
            sys.exit()

def main():
    pass

if __name__ == "__main__":
    main()

