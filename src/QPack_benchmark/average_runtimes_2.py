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

def norm_sched(data, iterations):
    res = []
    for i in range(len(iterations)):
        k = data[i]/(iterations[i]-1)
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

with open('logs/log_mcp_qblox_cluster_threaded.json','r') as f:
    base_data = json.load(f)
    
with open('logs/log_mcp_qblox_dummy_cluster.json','r') as f:
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
compile_std = np.mean(compile_time)




cpu_time = [r["opt_time"] for r in dummy_data['data']]
cpu_iter = [r["func_calls"] for r in dummy_data['data']]
cpu_time = norm(cpu_time, cpu_iter)
cpu_mean = np.mean(cpu_time)
cpu_std = np.mean(cpu_time)


overhead = subtract(running, schedule)
overhead_mean = np.mean(overhead)
overhead_std = np.std(overhead)

sched_active = [r-((200e-6)+(3e-6)+(30e-9))*2000 for r in schedule]
sched_active_mean = np.mean(sched_active)
sched_active_std = np.std(sched_active)

reset = [200e-6*2000] * len(sched_active)

acc_overhead = [t-((t-25e-3)/5)*4 for t in overhead]
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
    t = reset[i]+compile_time[i]+overhead[i]+cpu_mean
    total.append(t)
total_mean = np.mean(total)
total_std = np.std(total)+cpu_std

"""
import operator

single_overhead = average(running) - average(schedule)
print(single_overhead)
single_sched = (average(schedule)/2000)*100
print(single_sched)
single_run = single_overhead + single_sched
print(single_run)
clops = (1/ single_run)*100
print(clops)
"""

"""
fig, ax = plt.subplots()
ax.bar(x_pos, means, yerr=error, align='center', alpha=0.5, ecolor='black', capsize=10)
ax.set_xticks(x_pos)
ax.set_xticklabels(time_ax)
plt.ylabel("runtime [s]")
plt.title("Average runtimes per iteration for 2000 shots")
plt.savefig("average_runtimes.pdf")
"""

time_ax = ['total', 'passive\nreset', 'schedule', 'compile', 'overhead', 'accelerated\noverhead', 'optimizer']
x_pos = np.arange(len(time_ax))
means = [total_mean, sched_mean, sched_active_mean, compile_mean, overhead_mean, acc_overhead_mean, cpu_mean]
error = [total_std, sched_std, sched_active_std, compile_std, overhead_std, acc_overhead_std, cpu_std]

#print(average(schedule) + average(overhead) + average(compile_time) + average(cpu_time))
print(average(compile_time))
print(average(cpu_time))


fig, ax = plt.subplots(figsize=(7.5,6))
ax.bar(x_pos, means, yerr=error, align='center', alpha=0.5, ecolor='black', capsize=10)
ax.set_xticks(x_pos)
ax.set_xticklabels(time_ax)
plt.ylabel("runtime [s]")
plt.title("Average runtimes per iteration for 2000 shots")
plt.savefig("average_runtimes_all.pdf")