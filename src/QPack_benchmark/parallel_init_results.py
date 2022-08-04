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

def d_norm(data, iterations):
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

def add(a, b):
    t=[]
    for i in range(len(a)):
        t.append(a[i] + b[i])
    return t


def average(lst):
    return sum(lst) / len(lst)

def add_data(data, mean, error):
    mean.append(np.mean(data))
    error.append(np.std(data))
    return mean, error

with open('logs/log_mcp_qblox_cluster.json','r') as f:
    old_base_data = json.load(f)
old_data = old_base_data['data']
old_iterations = [d['time_res']['iterations'] for d in old_data]
old_runtime = [d['time_res']['time_per_step'] for d in old_data]

with open('logs/log_mcp_qblox_cluster_serial_prepare.json','r') as f:
    base_data = json.load(f)
data = base_data['data']
iterations = [d['time_res']['iterations'] for d in data]
runtime = [d['time_res']['time_per_step'] for d in data]  

with open('logs/log_mcp_qblox_dummy_cluster.json','r') as f:
    dummy_data = json.load(f)
d_runtime = [d['time_res']['time_per_step'] for d in dummy_data['data']]
d_iterations = [d['time_res']['iterations'] for d in dummy_data['data']]
  
with open('logs/log_mcp_qblox_cluster_threaded_prepare.json','r') as f:
    new_base_data = json.load(f)  
new_data = new_base_data['data']
new_iterations = [d['time_res']['iterations'] for d in new_data]
new_runtime = [d['time_res']['time_per_step'] for d in new_data]
  
# data
#   opt_time
#   func_calls
#   time_res
#       quantum_runtime
#       time_per_step
#           total_job_time
#           schedule
#           running
#           compile


# schedule    -    dummy schedule
# reset    -    200us
# prepare    -    job-running
# other overhead: running - schedule
# compile
# optimizer

# simulation = quantum_runtime - total_job_time - compile
baseline = []
active = []
threaded = []


# schedule###################################################
d_schedule = [r['schedule'] for r in d_runtime]
d_schedule = d_norm(d_schedule, d_iterations)
d_schedule = [k-(200e-6)*2000 for k in d_schedule]

reset = [200e-6*2000]*len(d_schedule)
d_schedule = add(d_schedule, reset)

sched_active = [r-((200e-6)+(1e-6))*2000 for r in d_schedule]

schedule = [r['schedule'] for r in runtime]
schedule = norm(schedule, iterations)

new_schedule = [r['schedule'] for r in new_runtime]
new_schedule = norm(new_schedule, new_iterations)

baseline.append(sched_active)
active.append(sched_active)
threaded.append(sched_active)
##############################################################

#reset#####################################
active_reset = [1e-6*2000]*len(d_schedule)

baseline.append(reset)
active.append(active_reset)
threaded.append(active_reset)
###########################################

#prepare###########################################
old_job_times = [r['total job time'] for r in old_runtime]
old_job_times = norm(old_job_times, old_iterations)
old_running = [r['running'] for r in old_runtime]
old_running = norm(old_running, old_iterations)
old_prepare = subtract(old_job_times, old_running)

job_times = [r['total job time'] for r in runtime]
job_times = norm(job_times, iterations)
running = [r['running'] for r in runtime]
running = norm(running, iterations)
prepare = subtract(job_times, running)

new_job_times = [r['total job time'] for r in new_runtime]
new_job_times = norm(new_job_times, new_iterations)
new_running = [r['running'] for r in new_runtime]
new_running = norm(new_running, new_iterations)
new_prepare = subtract(new_job_times, new_running)

baseline.append(prepare)
active.append(prepare)
threaded.append(new_prepare)
####################################################

#communication (excluding prepare)#################
print(schedule)
print(running)
communication = subtract(running, schedule)
print(communication)
communication = norm(communication, iterations)

new_communication = subtract(new_running, new_schedule)
new_communication = norm(new_communication, new_iterations)

baseline.append(communication)
active.append(communication)
threaded.append(new_communication)

##########################################################

#compile##################################################
compile_time = [r['compile'] for r in runtime]
compile_time = norm(compile_time, iterations)

new_compile_time = [r['compile'] for r in new_runtime]
new_compile_time = norm(new_compile_time, new_iterations)

baseline.append(compile_time)
active.append(compile_time)
threaded.append(new_compile_time)
##########################################################


#replace with new measurements
#optimizer################################################
cpu_time = [r["opt_time"] for r in dummy_data['data']]
cpu_iter = [r["func_calls"] for r in dummy_data['data']]
cpu_time = norm(cpu_time, cpu_iter)

baseline.append(cpu_time)
active.append(cpu_time)
threaded.append(cpu_time)
##########################################################

#total######################################
total = add(job_times, compile_time)
total = add(total, cpu_time)
total = subtract(total, reset)


active_total = subtract(total, reset)
active_total = add(active_total, active_reset)



new_total = add(new_job_times, new_compile_time)
new_total = subtract(new_total, reset)
new_total = subtract(new_total, reset)

new_total = add(new_total, active_reset)
new_total = add(new_total, cpu_time)

baseline.append(total)
active.append(active_total)
threaded.append(new_total)
#################################################


baseline_mean = [np.mean(t) for t in baseline]
active_mean = [np.mean(t) for t in active]
threaded_mean = [np.mean(t) for t in threaded]

baseline_error = [np.std(t) for t in baseline]
active_error = [np.std(t) for t in active]
threaded_error = [np.std(t) for t in threaded]


"""
time_ax = ['circuit\nexecution', 'reset', 'initialization', 'communication', 'compile', 'optimizer', 'total']
x_pos = np.arange(len(time_ax))


fig, ax = plt.subplots(figsize=(8,6))
ax.bar(x_pos-0.3, baseline_mean, yerr=baseline_error, align='center', alpha=0.5, ecolor='black', capsize=10, width = 0.3, label='baseline')

ax.bar(x_pos, active_mean, yerr=active_error, align='center', alpha=0.5, ecolor='black', capsize=10, color = 'g',
       width = 0.3, label='active reset')
ax.bar(x_pos+0.3, threaded_mean, yerr=threaded_error, align='center', alpha=0.5, ecolor='black', capsize=10, color = 'r', width = 0.3,
      label='active reset + parallel module setup')


ax.set_xticks(x_pos)
ax.set_xticklabels(time_ax)
#ax.set_yscale('log')
plt.legend()
plt.ylabel("runtime [s]")
plt.title("Average runtimes per iteration for 2000 shots")

note = "{}ms".format(round(np.mean(d_schedule)*1e3, 3))
plt.text( -0.3, active_mean[0]+0.03, note)
"""

x_pos = 1
fig, ax = plt.subplots()
old_prep = np.mean(old_prepare)
old_prep_e = np.std(old_prepare)

serial_prep = np.mean(prepare)
serial_prep_e = np.std(prepare)

threaded_prep = np.mean(new_prepare)
threaded_prep_e = np.std(new_prepare)

estimate1 = np.mean(old_prep) - (np.mean(prepare) - np.mean(new_prepare))

estimate2 = np.mean(old_prep) * (np.mean(new_prepare)/np.mean(prepare))

estimate3 = (np.mean(prepare)-2.5e-3)/5 + 2.5e-3
"""
ax.bar(x_pos-0.3, old_prep, yerr=old_prep_e, align='center', alpha=0.5, ecolor='black', capsize=10, width = 0.3, label='baseline')
ax.bar(x_pos, serial_prep, yerr=serial_prep_e, align='center', alpha=0.5, ecolor='black', capsize=10, color = 'g',
       width = 0.3, label='serial new')
ax.bar(x_pos+0.3, threaded_prep, yerr=threaded_prep_e, align='center', alpha=0.5, ecolor='black', capsize=10, color = 'r', width = 0.3,
      label='parallel module setup')
"""
ax.bar(x_pos-0.3, old_prep, yerr=old_prep_e, align='center', alpha=0.5, ecolor='black', capsize=10, width = 0.3, label='baseline')
ax.bar(x_pos, estimate1, align='center', alpha=0.5, ecolor='black', capsize=10, color = 'g',
       width = 0.3, label='estimate 1')
ax.bar(x_pos+0.3, estimate2, align='center', alpha=0.5, ecolor='black', capsize=10, color = 'r', width = 0.3,
      label='estimate 2')
ax.bar(x_pos+0.6, estimate3, align='center', alpha=0.5, ecolor='black', capsize=10, color = 'c', width = 0.3,
      label='estimate paper')


plt.legend()
plt.ylabel("runtime [s]")
