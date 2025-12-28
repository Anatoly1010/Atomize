import os
import atomize.general_modules.general_functions as general
import atomize.tests.consecutive_script_to_run as script

path_to_main = os.path.abspath( os.getcwd() )
path_to_folder = os.path.join( path_to_main, '..', '..' )

filename = 'FtS.csv'
path = os.path.join( path_to_folder, filename )

script.experiment( points = 100, path_to_file = path )

