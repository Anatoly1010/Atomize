#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from threading import Thread
import atomize.general_modules.general_functions as general

class rThread(Thread):
    """doc"""
    def __init__(self, group=None, target=None, name=None, \
                 args=(), kwargs={}, Verbose=None):
        
        Thread.__init__(self, group, target, name, args, kwargs)
        self._return = None


    def run(self):
        #general.message(type(self._target))
        if self._target is not None:
            self._return = self._target(*self._args, **self._kwargs)
    
    def join(self, *args):
        Thread.join(self, *args)
        
        return self._return

def main():
    pass

if __name__ == "__main__":
    main()