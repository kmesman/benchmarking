#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr 26 09:28:09 2022

parse results
@author: koen
"""

import json
import numpy as np
import matplotlib.pyplot as plt

def norm(data, iterations):
    res = []
    for i in range(len(iterations)):
        k = data[i]/iterations[i]
        res.append(k)
    return res

with open('logs/log_mcp_qblox_cluster.json','r') as f:
    base_data = json.load(f)
    data = base_data['data']
    iterations = [d['time_res']['iterations'] for d in data]
    runtime = [d['time_res']['time_per_step'] for d in data]
    
    total_times = [r['total job time'] for r in runtime]
    total_times = norm(total_times, iterations)
    total_mean = np.mean(total_times)
    total_std = np.std(total_times)
    
    schedule = [r['schedule'] for r in runtime]
    schedule = norm(schedule, iterations)

    sched_mean = np.mean(schedule)
    sched_std = np.std(schedule)
    
    running = [r['running'] for r in runtime]
    running = norm(running, iterations)

    run_mean = np.mean(running)
    run_std = np.std(running)
    
    compile_time = [r['compile'] for r in runtime]
    compile_time = norm(compile_time, iterations)

    compile_mean = np.mean(compile_time)
    compile_std = np.mean(compile_time)
    
    time_ax = ['total', 'schedule', 'running', 'compile']
    x_pos = np.arange(len(time_ax))
    means = [total_mean, sched_mean, run_mean, compile_mean]
    error = [total_std, sched_std, run_std, compile_std]
    
    fig, ax = plt.subplots()
    ax.bar(x_pos, means, yerr=error, align='center', alpha=0.5, ecolor='black', capsize=10)
    ax.set_xticks(x_pos)
    ax.set_xticklabels(time_ax)
    plt.ylabel("runtime [s]")
    plt.title("Average runtimes per iteration")
    plt.savefig("average_runtimes.pdf")


    