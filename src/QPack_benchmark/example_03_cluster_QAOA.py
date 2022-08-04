#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 28 18:10:08 2022

Example Qpack run
@author: koen
"""

import QPack
import qblox_hardware_cluster as qblox_hardware

from qcodes.instrument import Instrument
import matplotlib.pyplot as plt
from qblox_instruments import Cluster, ClusterType
import numpy as np
Instrument.close_all()


#shots = 1000
size = 5

# important to assign add_instruments to a (unused) variable, to ensure the
# reference stays alive!

dummy_modules = qblox_hardware.add_instruments(size)
#cluster = Cluster("cluster0", '192.168.1.0')

qblox_backend = qblox_hardware.Backend(dummy_qubits=size)

#MCP benchmark
mcp = QPack.Benchmark('mcp', size, backend=qblox_backend)

#res = mcp.run(shots=2000)
import numpy as np

lim = 3.5

log_range = [round(i) for i in np.arange(750, 2000, 50)]
print(log_range)
#log_range = range(10, 20000, 10)
results_p1 = []
results_p2 = []
error = []

def avg(fun, rep):
    res = []
    for i in range(rep):
        tmp = fun()
        res.append(tmp['fun'])
        #res.append(fun)
    out = sum(res)/rep
    error = np.std(res)
    return out, error


for shots in log_range:
    k = 0
    #res1 = avg(mcp.run(shots=shots), 10)
    res = []
    for i in range(10):
        tmp = mcp.run(shots=shots)
        res.append(tmp['fun'])
        #res.append(fun)
    res1 = sum(res)/10
    err = np.std(res)
    print(k)
    if k>= 2:
        if np.mean(err[-3, -1])<= 0.4:
            print(shots[-3])
            break
    k+=1
#   res2 = avg(mcp.run(shots=shots, qaoa_layers=2)["fun"], 10)
    error.append(err)
    
    results_p1.append(-res1)
#  results_p2.append(-res2)
print(error)
plt.errorbar(log_range, results_p1, yerr=error)
   #plt.plot(log_range, results_p2)
plt.title("mcp score for 5-node graph")
plt.xlabel("shots")
plt.ylabel("score")
plt.show()