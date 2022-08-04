#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 24 14:06:57 2022

@author: koen
"""
import generate_graph as gg

import json
import numpy as np
import testquantify as test
import optimizer as opt
import os
from datetime import datetime

class result_object:
    def __init__(self, shots):
        self.shots = shots
        self.json_data = {"shots":shots}
        
    def add_acc(self, acc):
        self.accuracy = acc
        self.json_data['acc'] = acc
    
    def add_calls(self, calls):
        self.func_calls = calls
        self.json_data['func_calls'] = calls

    def add_times(self, times):
        self.time_results = times
        self.json_data["time_res"] = times
        
    def add_opt_time(self, opt_time):
        self.opt_time = opt_time
        self.json_data["opt_time"] = opt_time


class Benchmark:
    
    def __init__(self, func, size, backend=""):
        self.q_func = func
        self.backend = backend
        backend_config = backend.configuration()
        self.backend_tag = backend_config.backend_name
        self._problem_size = size
        self.qubits = self.__qubit_select(size)
        self.res_obj = result_object(self.q_func)
    
    def __qubit_select(self, size):
        self._qbits = {
            'mcp': size,
            'dsp': size + 10,
            'tsp': size**2
        }
        return self._qbits.get(self.q_func)

    def test_run(self, rep=1, shots=1):
        print("Starting test run")
        res = []
        for i in range(rep):
            res.append(test.circuit_run(shots, self._problem_size, self.backend))
        return res

    def set_size(self, size):
        self.problem_size = size

    def run(self, shots=1, max_iter=1, qaoa_layers=1):
        graph = gg.regular_graph(self._problem_size)
        init_val = np.random.rand(self._problem_size*3*qaoa_layers) * (2 * np.pi)   #!!!

        print('Start benchmark: {} {}'.format(self.q_func, self._problem_size))
        
        #self._results = opt.nm(self.init_param, self.graph, self.p, self.q_func)
        opt_inst = opt.optimize()
        res = opt_inst.shgo(init_val, graph, qaoa_layers, self.q_func, self.backend, shots)
        #res = opt_inst.bobyqa(init_val, graph, qaoa_layers, self.q_func, self.backend, shots)

        self.res_obj.add_opt_time(res['opt_time'])
        self.res_obj.add_calls(res['function evaluations'])
        self.res_obj.add_acc(res['fun'])
        self.res_obj.add_times(opt_inst.time_res)
        now = datetime.now()
        datestr = now.strftime("%m%d%Y%H%M")
        self.log_results('{}'.format(datestr), self.res_obj.json_data)
        print('finished!')
        return res
    
    # needs cleaning, post_processing for result object
    def log_results(self, date, res_data):
            work_dir = os.path.dirname(os.path.realpath(__file__))
            #path = work_dir + '/logs/log_'+ self.q_func + "_" + self.backend_tag + "_" date + '.json'
            path = "{}/logs/log_{}_{}_{}.json".format(work_dir, self.q_func, self.backend_tag, self._problem_size)
            try:
                with open(path,'r+') as file:
                    file_data = json.load(file)
                    
                    old_data = file_data["data"] 
                    data = old_data.copy()
                    data.append(res_data)
                    file_data = {"qfunc" :"mcp", "backend_tag":self.backend_tag, "data":data}
                    file.seek(0)
                    json.dump(file_data, file, indent = 4)
            except:
                with open(path, 'w') as file:
                    file_data = {"qfunc" :self.q_func, "backend_tag":self.backend_tag, "data":[res_data]}
                    file.seek(0)
                    json.dump(file_data, file, indent = 4)
            finally:
                print("data saved")
