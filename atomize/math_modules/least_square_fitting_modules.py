#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import scipy
import numpy as np
from scipy import optimize

class math():

	def __init__(self):
		pass

	def exponential(self, x, a, k, b):
		return a*np.exp(-x/k) + b

	def one_exp_fit(self, curve, guess_array):

		popt_exp, pcov_exp = scipy.optimize.curve_fit(self.exponential, curve[0], curve[1], p0=guess_array)
		    
		axis_y_exp = self.exponential(curve[0], popt_exp[0], popt_exp[1], popt_exp[2])
		model_data = np.transpose(np.column_stack((curve[0], axis_y_exp)))

		residuals = np.transpose(np.column_stack((curve[0], curve[1] - axis_y_exp)))
		ss_res = np.sum(residuals[1]**2)
		ss_tot = np.sum((curve[1]-np.mean(curve[1]))**2)
		r_squared = 1 - (ss_res / ss_tot)

		return model_data, residuals, r_squared

if __name__ == "__main__":
    main()