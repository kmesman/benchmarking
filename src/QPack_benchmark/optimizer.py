#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 24 14:33:26 2022

Classical optimizer for QPack benchmark
@author: koen
"""

from math import pi
import scipy.optimize as opt
import cost_library as cl
import time
import nlopt
import numpy as np

class optimize():
    def __init__(self):
        self.time_res = {"quantum_runtime" : [], "time_per_step":{}, "iterations":0}
        

    def __function_select(self, params, q_func, graph, p, backend, shots, opt_mode):
        """
        Select problem function. Runs the QAOA algorithm and cost function
        post-processing for selected problem.
        """
        # select quantum language for QAOA
        backend_name = backend.configuration().backend_name
        
        if "ibm" in backend_name or "simulator" in backend_name:
            import QAOA_qiskit as QAOA
        else:
            import QAOA_quantify as QAOA

        inverted=False
        
        # Run and post-process max cut problem
        if q_func == 'mcp':
            job, times = QAOA.qaoa_mcp(params, graph, p, backend, shots)
            cost_func = cl.mcp
            if opt_mode == "minimize":
                # mcp needs to be maximized, cost is inverted for minimizer
                inverted = True
                
        # Run and post-process dominating set problem
        elif q_func == 'dsp':
            job, times = QAOA.qaoa_dsp(params, graph, p, backend, shots)
            cost_func = cl.dsp
            
        # Run and post-process traveling salesman problem
        elif q_func == 'tsp':
            job, times = QAOA.qaoa_tsp(params, graph, p, backend, shots)
            cost_func = cl.tsp
        
        self.time_res["quantum_runtime"].append(times)
        
        # Add collected runtimes to output dictionary
        for key in job["time_per_step"]:
            if key in self.time_res["time_per_step"]:
                self.time_res["time_per_step"][key] += job["time_per_step"][key]
            else:
                self.time_res["time_per_step"][key] = job["time_per_step"][key]
        self.time_res["iterations"] += 1
            
        #self.time_res["time_per_step"].append(job["time_per_step"])
        return cost_func(job, graph, inverted)


    def shgo(self, init_param, graph, p, q_func, backend, shots):
        """
        Simplicial homology global optimization (SHGO) is a bounded minimization
        optimizer.
        """
        
        bounds = [(0, pi), (0, 2 * pi)]*p #!!!
        start_timer = time.time()
        res = opt.shgo(self.__function_select, bounds, args=(q_func, graph, p, backend, shots, "minimize"),
                       options={'ftol': 1e-10})
        stop_timer = time.time()
        total_opt_time = stop_timer-start_timer
        return {"fun" : res.fun, "result" : res.x,
                "function evaluations" : res.nfev, "optimizer iterations" : res.nit,
                "optimizer total time" : total_opt_time,
                #"opt_time" : total_opt_time - self.time_res["time_per_step"]["total job time"] -self.time_res["time_per_step"]["compile"],
                "opt_time" : total_opt_time - sum(self.time_res["quantum_runtime"]),
                "qpu time" : self.time_res
                }

    def bobyqa(self, init_param, graph, p, q_func, backend, shots):
        v, e = graph

        opt = nlopt.opt(nlopt.LN_BOBYQA, 3*v*p)
        opt.set_max_objective(lambda a, b: self.__function_select(a, q_func, graph, p, backend, shots, 'minimize'))
        opt.set_lower_bounds([0]*(3*v*p))
        opt.set_upper_bounds([2 * pi]*(3*v*p))
        opt.set_initial_step(0.005)
        opt.set_xtol_abs(np.array([1e-5]*(3*v*p)))
        opt.set_ftol_rel(1e-5)
        arr_param = np.array(init_param)
        res = opt.optimize(arr_param)
        opt_val = opt.last_optimum_value()  # returns number of expected cuts

        """
        return {"fun" : res.fun, "result" : res.x,
                "function evaluations" : res.nfev, "optimizer iterations" : res.nit,
                "optimizer total time" : total_opt_time,
                "opt_time" : total_opt_time - self.time_res["time_per_step"]["total job time"] -self.time_res["time_per_step"]["compile"],
                "qpu time" : self.time_res
                }
        """
