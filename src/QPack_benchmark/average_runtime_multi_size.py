#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 13 13:48:16 2022

@author: koen
"""


import json
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

def norm(data, iterations):
    res = []
    for i in range(len(iterations)):
        k = data[i]/iterations[i]
        res.append(k)
    return res

def norm_sched(data, iterations):
    res = []
    for i in range(len(iterations)):
        k = data[i]/(iterations[i])
        res.append(k)
    return res

def subtract(a, b):
    res = []
    for i in range(len(a)):
        k = a[i] - b[i]
        res.append(k)
    return res

def average(lst):
    return sum(lst) / len(lst)


def parse(qubits):
    with open('logs/log_mcp_qblox_cluster_{}.json'.format(qubits),'r') as f:
        base_data = json.load(f)
    
    with open('logs/log_mcp_qblox_dummy_cluster_{}.json'.format(qubits),'r') as f:
        dummy_data = json.load(f)
    
    
    data = base_data['data']
    iterations = [d['time_res']['iterations'] for d in data]
    runtime = [d['time_res']['time_per_step'] for d in data]
    
    job_times = [r['total job time'] for r in runtime]
    job_times = norm(job_times, iterations)
    job_mean = np.mean(job_times)
    job_std = np.std(job_times)
    
    schedule = [r['schedule'] for r in runtime]
    schedule = norm_sched(schedule, iterations)
    sched_mean = np.mean(schedule)
    sched_std = np.std(schedule)
    
    running = [r['running'] for r in runtime]
    running = norm(running, iterations)
    run_mean = np.mean(running)
    run_std = np.std(running)
    
    
    total = [sum(r['time_res']['quantum_runtime']) for r in data]
    total = norm(total, iterations)
    total_mean = np.mean(total)
    total_std = np.std(total)
    
    compile_time = [r['compile'] for r in runtime]
    compile_time = norm(compile_time, iterations)
    compile_mean = np.mean(compile_time)
    compile_std = np.std(compile_time)
    
    
    d_runtime = [d['time_res']['time_per_step'] for d in dummy_data['data']]
    d_iterations = [d['time_res']['iterations'] for d in dummy_data['data']]
    
    #d_runtime = [d['time_res']['time_per_step'] for d in data]
    #d_iterations = [d['time_res']['iterations'] for d in data]
    
    d_schedule = [r['schedule'] for r in d_runtime]
    d_schedule = norm_sched(d_schedule, d_iterations)
    d_schedule = [k-(200e-6)*2000 for k in d_schedule]
    d_sched_mean = np.mean(d_schedule)
    d_sched_std = np.std(d_schedule)
    
    cpu_time = [r["opt_time"] for r in dummy_data['data']]
    #cpu_time = [r["opt_time"] for r in data]
    cpu_iter = [r["func_calls"] for r in dummy_data['data']]
    #cpu_iter = [r["func_calls"] for r in data]

    cpu_time = norm(cpu_time, cpu_iter)
    cpu_mean = np.mean(cpu_time)
    cpu_std = np.std(cpu_time)
    
    
    overhead = subtract(job_times, schedule)
    overhead_mean = np.mean(overhead)
    overhead_std = np.std(overhead)
    
    #sched_active = [r-((200e-6)+(3e-6)+(30e-9))*2000 for r in schedule]
    sched_active = [r-((200e-6)+(1e-6))*2000 for r in d_schedule]
    
    sched_active_mean = np.mean(sched_active)
    sched_active_std = np.std(sched_active)
    
    reset = [200e-6*2000]*len(total)
    active_reset = [1e-6*2000]*len(total)
    reset_mean = np.mean(reset)
    reset_e = np.std(reset)
    active_reset = np.mean(active_reset)
    

    acc_overhead = [t-((t-2.5e-3)*(4/5)) for t in overhead]
    acc_overhead_mean = np.mean(acc_overhead)
    acc_overhead_std = np.std(acc_overhead)

    """
    time_ax = ['schedule', 'compile', 'overhead', 'cpu']
    x_pos = np.arange(len(time_ax))
    means = [sched_mean, compile_mean, overhead_mean, cpu_mean]
    error = [sched_std, compile_std, overhead_std, cpu_std]
    """
    total= []
    for i in range(len(reset)):
        t = reset[i]+compile_time[i]+overhead[i]+cpu_mean+d_sched_mean
        total.append(t)
        
    total_mean = np.mean(total)
    total_std = np.std(total)
    
    overhead_diff = subtract(overhead, acc_overhead)
    total_acc = subtract(total, overhead_diff)
    total_acc_mean = np.mean(total_acc)
    total_acc_std = np.std(total_acc)
    
    no_reset = [(1e-6)*2000]*len(total)
    no_reset_mean = np.mean(no_reset)
    
    active_total = subtract(total, reset)
    active_total_mean = np.mean(active_total)
    active_total_std = np.std(active_total)
    
    
    final_total = subtract(active_total, overhead_diff)
    final_total_mean = np.mean(final_total)
    final_total_std = np.std(final_total)
    
    raw_data = [d_schedule, reset, overhead, compile_time, cpu_time, total]
    
    time_ax = ['circuit\nexecution', 'reset', 'communication', 'compile', 'optimizer', 'total']
    x_pos = np.arange(len(time_ax))
    means = [d_sched_mean, reset_mean, overhead_mean, compile_mean, cpu_mean, total_mean]
    error = [d_sched_std, reset_e, overhead_std, compile_std, cpu_std, total_std]
    
    x = [qubits]*len(reset)
    
    raw_data = {"circuit\nexecution":[[qubits]*len(d_schedule), d_schedule],
                "reset":[x, reset],
                "communication":[x, overhead],
                "compile":[x, compile_time],
                "optimizer":[[qubits]*len(cpu_time), cpu_time],
                "total":[x, total]}
    
    means = {"circuit\nexecution":[qubits, d_sched_mean],
                "reset":[qubits, reset_mean],
                "communication":[qubits, overhead_mean],
                "compile":[qubits, compile_mean],
                "optimizer":[qubits, cpu_mean],
                "total":[qubits, total_mean]}
    
    error = {"circuit\nexecution":[qubits, d_sched_std],
                "reset":[qubits, reset_e],
                "communication":[qubits, overhead_std],
                "compile":[qubits, compile_std],
                "optimizer":[qubits, cpu_std],
                "total":[qubits, total_std]}
    
    return {"raw":raw_data, "means":means, "error": error}





fig, ax = plt.subplots(figsize=(8,6))

colors = [
     "xkcd:bright blue",
     "xkcd:sky blue",
     "xkcd:sea blue",
     "xkcd:turquoise blue",
     "xkcd:aqua",
     "xkcd:cyan",
 ]

data = []


raw_data = {"reset":[[],[]],
            "circuit\nexecution":[[],[]],
            "communication":[[],[]],
            "compile":[[],[]],
            "optimizer":[[],[]],
            "total":[[],[]]}

mean_data = {"reset":[[],[]],
            "circuit\nexecution":[[],[]],
            "communication":[[],[]],
            "compile":[[],[]],
            "optimizer":[[],[]],
            "total":[[],[]]}
    

def log_func(x, a, b):
    return a*np.log(x)+b

def lin_func(x, a, b):
    return a*x+b

def sat_func(x, a, b, c):
    return a/(1+np.exp(-1*b*(x-c)))


qubits=20
for i in range(5, qubits+1):
    data = parse(i)
    for key in raw_data.keys():
        raw_data[key][0]+=data["raw"][key][0]
        raw_data[key][1]+=data["raw"][key][1]

        mean_data[key][0].append(data["means"][key][0])
        mean_data[key][1].append(data["means"][key][1])

for key in zip(raw_data.keys(), colors):
    rd = raw_data[key]
    plt.plot(rd[0],rd[1],'.', alpha=0.3)
    md = mean_data[key]
    plt.plot(md[0], md[1],'.')
    if key == "communication":#or key == "total"
        plt.plot(md[0], md[1],'.')
        popt, param_cov = curve_fit(lin_func, md[0], md[1])
        a, b = popt
        print(a,b)
        print(param_cov)
        # use optimal parameters to calculate new values
        y_new = [lin_func(d, a, b) for d in md[0]]
        plt.plot(md[0], y_new,'-', label=key)
        
    elif key=="optimizer":
        plt.plot(md[0], md[1],'.', color=color)
        popt, param_cov = curve_fit(sat_func, md[0], md[1])
        a, b, c = popt
        # use optimal parameters to calculate new values
        y_new = sat_func(md[0], a, b, c)
        plt.plot(md[0], y_new,'-', label=key)
    else:
        plt.plot(md[0], md[1],'-',  label=key)

plt.ylabel("time [s]")
plt.xlabel("(virtual) qubits")
plt.title("Average runtime per iteration (2000 shots)")
plt.legend()
plt.savefig("result_images/Results_{}_qubits.pdf".format(qubits))
plt.show()
 
   