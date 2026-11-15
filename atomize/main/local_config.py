#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil
import configparser
from platformdirs import *

try:
    import atomize.station as _station
    APP_NAME = _station.app_name
    ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(_station.__file__)))
    STATION = True
except ImportError:
    APP_NAME = "atomize-py"
    ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    STATION = False

def get_user_config_dir(app_name):
    return user_config_dir(app_name)

def get_user_documents_dir():
    return user_documents_dir()

def copy_config(src, src2):
    config_dir = get_user_config_dir(APP_NAME)
    config_dir2 = os.path.join(config_dir, "device_config")
    config_file_path = os.path.join(config_dir, "main_config.ini")

    # Ensure config directory exists
    if not os.path.exists(config_dir) or not os.listdir(config_dir):
        os.makedirs(config_dir, exist_ok = True)
        try:
            shutil.copyfile(src, config_file_path)
            shutil.copytree(src2, config_dir2, dirs_exist_ok = True)
            if STATION:
                station_config = os.path.join(ROOT_DIR, "atomize", "config.ini")
                station_device = os.path.join(ROOT_DIR, "atomize", "device_modules", "config")
                if os.path.isfile(station_config):
                    shutil.copyfile(station_config, config_file_path)
                if os.path.isdir(station_device):
                    shutil.copytree(station_device, config_dir2, dirs_exist_ok = True)
            for file_to_remove in ["__init__.py", "config_utils.py"]:
                path = os.path.join(config_dir2, file_to_remove)
                if os.path.exists(path):
                    os.remove(path)

        except PermissionError:
            print("During copying config files an error occures: Permission denied.")

    return config_file_path, config_dir2

def load_config():
    config_dir = get_user_config_dir(APP_NAME)
    config_dir2 = os.path.join(config_dir, "device_config")
    config_file_path = os.path.join(config_dir, "main_config.ini")

    return config_file_path, config_dir2

def load_config_device():
    config_dir2 = os.path.join(get_user_config_dir(APP_NAME), "device_config")

    return config_dir2

def load_scripts(src):
    config_dir = os.path.join( get_user_documents_dir(), APP_NAME, "default" )

    # the shipped example scripts live in script_examples/ here, tests/ in the forks
    if not os.path.isdir(src):
        src = os.path.join( os.path.dirname(src), 'script_examples' )

    # Ensure config directory exists
    if not os.path.exists(config_dir) or not os.listdir(config_dir):
        try:
            shutil.copytree(src, config_dir, dirs_exist_ok = True)
            station_scripts = os.path.join(ROOT_DIR, "atomize", "script_examples")
            if STATION and os.path.isdir(station_scripts):
                shutil.copytree(station_scripts, config_dir, dirs_exist_ok = True)
        except PermissionError:
            print("During copying configs file the error occures: Permission denied.")
        except FileNotFoundError:
            print(f"During copying configs file the error occures: {src} not found.")

    return os.path.normpath( os.path.join( config_dir, '..') )
