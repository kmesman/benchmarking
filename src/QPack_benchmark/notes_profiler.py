#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun  8 11:42:43 2022

@author: koen
"""

import time



class newclass():
    def __init__(self):
        self.time = []
        
    def profiler(func):
        '''Decorator that reports the execution time.'''
      
        def wrap(self, *args, **kwargs):
            start = time.time()
            result = func(self, *args, **kwargs)
            end = time.time()
            
            self.time.append(end-start)
            return result
        return wrap   
    
    
    @profiler
    def waitfunc(self):
        time.sleep(2)


cl = newclass()
cl.waitfunc()
print(cl.time)

"""
def profiler(func):
    '''Decorator that reports the execution time.'''
  
    def wrap(self, *args, **kwargs):
        start = time.time()
        result = func(self, *args, **kwargs)
        end = time.time()
        
        self.profile[func.__name__].append(end-start)
        return result
    return wrap
"""
"""
        #self.profile = {"start":[], "prepare":[],
        #               "wait_done":[], "retrieve_acquisition":[]}
        """