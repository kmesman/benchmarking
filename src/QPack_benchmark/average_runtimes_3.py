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

with open('logs/log_mcp_qblox_cluster_5.json','r') as f:
    base_data = json.load(f)

with open('logs/log_mcp_qblox_dummy_cluster.json','r') as f:
    dummy_data = json.load(f)
    
    
data = base_data['data']
print(data)
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

running = [r['total job time'] for r in runtime]
running = norm(running, iterations)
run_mean = np.mean(running)
run_std = np.std(running)


total = [sum(r['time_res']['quantum_runtime']) for r in data]
total = norm(total, iterations)
total_mean = np.mean(total)
total_std = np.std(total)

compile_time = [r['compile'] for r in runtime]
compile_time = norm(compile_time, iterations)
print(compile_time)
compile_mean = np.mean(compile_time)
compile_std = np.std(compile_time)


d_runtime = [d['time_res']['time_per_step'] for d in dummy_data['data']]
d_iterations = [d['time_res']['iterations'] for d in dummy_data['data']]

d_schedule = [r['schedule'] for r in d_runtime]
d_schedule = norm_sched(d_schedule, d_iterations)
d_schedule = [k-(200e-6)*2000 for k in d_schedule]
d_sched_mean = np.mean(d_schedule)
d_sched_std = np.std(d_schedule)

cpu_time = [r["opt_time"] for r in dummy_data['data']]
cpu_iter = [r["func_calls"] for r in dummy_data['data']]
cpu_time = norm(cpu_time, cpu_iter)
cpu_mean = np.mean(cpu_time)
cpu_std = np.std(cpu_time)


overhead = subtract(running, schedule)
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

print(overhead)
print(average(overhead))
acc_overhead = [t-((t-2.5e-3)*(4/5)) for t in overhead]
print(acc_overhead)
acc_overhead_mean = np.mean(acc_overhead)
print(acc_overhead_mean)
print(average(acc_overhead))
acc_overhead_std = np.std(acc_overhead)

"""
time_ax = ['schedule', 'compile', 'overhead', 'cpu']
x_pos = np.arange(len(time_ax))
means = [sched_mean, compile_mean, overhead_mean, cpu_mean]
error = [sched_std, compile_std, overhead_std, cpu_std]
"""
total= []

for i in range(len(reset)):
    t = reset[i]+compile_time[i]+overhead[i]+cpu_time[i]
    total.append(t)
total_mean = np.mean(total)
total_std = np.std(total)



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
"""
active_total = []
for i in range(len(reset)):
    t = no_reset[i]+compile_time[i]+overhead[i]+cpu_mean
    active_total.append(t)
total_mean = np.mean(active_total)
total_std = np.std(active_total)
"""


time_ax = ['circuit\nexecution', 'reset', 'communication', 'compile', 'optimizer', 'total']
x_pos = np.arange(len(time_ax))
means = [d_sched_mean, reset_mean, overhead_mean, compile_mean, cpu_mean, total_mean]
error = [d_sched_std, reset_e, overhead_std, compile_std, cpu_std, total_std]

active_means = [d_sched_mean, active_reset, overhead_mean, compile_mean, cpu_mean, active_total_mean]
active_error = [d_sched_std, reset_e, overhead_std, compile_std, cpu_std, active_total_std]


means_acc = [d_sched_mean, active_reset, acc_overhead_mean, compile_mean, cpu_mean, final_total_mean]
error_acc = [d_sched_std, reset_e, overhead_std, compile_std, cpu_std, active_total_std]

#means_acc = [d_sched_mean, active_reset, 0, compile_mean, cpu_mean, 0]
#error_acc = [d_sched_std, reset_e, 0, compile_std, cpu_std, 0]

#means_acc2 = [0, 0, acc_overhead_mean, 0, 0, final_total_mean]



#print(average(schedule) + average(overhead) + average(compile_time) + average(cpu_time))

print(means)

fig, ax = plt.subplots(figsize=(8,6))
ax.bar(x_pos-0.3, means, yerr=error, align='center', alpha=0.5, ecolor='black', capsize=10, width = 0.3, label='baseline')
ax.bar(x_pos, active_means, yerr=active_error, align='center', alpha=0.5, ecolor='black', capsize=10, color = 'g',
       width = 0.3, label='active reset')
ax.bar(x_pos+0.3, means_acc, yerr=error_acc, align='center', alpha=0.5, ecolor='black', capsize=10, color = 'r', width = 0.3,
       label='active reset + parallel module setup')
#ax.bar(x_pos+0.3, means_acc2, yerr=None, align='center', alpha=0.5, ecolor='black', capsize=10, color = 'r', width = 0.3
   #    )

ax.set_xticks(x_pos)
ax.set_xticklabels(time_ax)
#ax.set_yscale('log')
plt.legend()
plt.ylabel("runtime [s]")
plt.title("Average runtimes per iteration for 2000 shots")



note = "{}ms".format(round(d_sched_mean*1e3, 3))
plt.text( -0.3, active_means[0]+0.03, note)
   
   
#plt.savefig("average_runtimes_all.pdf")

   
   
   