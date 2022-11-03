import os
import runpy
import atomize.general_modules.general_functions as general
import atomize.tests.nutations as nut

path_to_main = os.path.abspath( os.getcwd() )
path_to_folder = os.path.join( path_to_main, '..', '..', 'Experimental_Data/Kuznetsov/auto_test' )

filename = str( 9594 ) + ' MHz.csv'
path = os.path.join( path_to_folder, filename )

#round(  , 3 )
#int( )

nut.experiment( MW_freq = int(9594), MF = 3463, Averages = 120, path_to_file = path )

