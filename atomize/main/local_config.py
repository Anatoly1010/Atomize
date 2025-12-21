#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil
import configparser
from platformdirs import *

def get_user_config_dir(app_name):
    return user_config_dir(app_name)

def get_user_documents_dir():
    return user_documents_dir()

def copy_config(src, src2):
    app_name = "atomize-py"
    config_dir = get_user_config_dir(app_name)
    config_dir2 = os.path.join(config_dir, "device_config")
    config_file_path = os.path.join(config_dir, "main_config.ini")

    # Ensure config directory exists
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
        try:
            shutil.copyfile(src, config_file_path)
            shutil.copytree(src2, config_dir2)
            os.remove( os.path.join(config_dir2, "__init__.py") )
            os.remove( os.path.join(config_dir2, "config_utils.py") )
        except PermissionError:
            print("During copying config files an error occures: Permission denied.")

    return config_file_path, config_dir2

def load_config():
    app_name = "atomize-py"
    config_dir = get_user_config_dir(app_name)
    config_dir2 = os.path.join(config_dir, "device_config")
    config_file_path = os.path.join(config_dir, "main_config.ini")

    return config_file_path, config_dir2

def load_config_device():
    app_name = "atomize-py"
    config_dir2 = os.path.join(get_user_config_dir(app_name), "device_config")

    return config_dir2

def load_scripts(src):
    app_name = "atomize-py"
    config_dir = os.path.join( get_user_documents_dir(), app_name, "default" )

    # Ensure config directory exists
    if not os.path.exists(config_dir):
        try:
            shutil.copytree(src, config_dir)
        except PermissionError:
            print("During copying configs file the error occures: Permission denied.")

    return  os.path.join( config_dir, '..')
