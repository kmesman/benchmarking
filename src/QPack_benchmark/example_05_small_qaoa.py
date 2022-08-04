#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 12 14:22:06 2022
small qaoa test
@author: koen
"""

from math import pi
from quantify_scheduler import Schedule
from quantify_scheduler.operations.gate_library import *
from quantify_scheduler.resources import BasebandClockResource
import generate_graph as gg

def qaoa_mcp(params, graph, p, shots):
    beta = params[0:p]
    gamma = params[p:2*p]

    v, edge_list = graph
    vertice_list = list(range(0, v, 1))
    for pb in range(len(beta)):
        if beta[pb] < 0 or beta[pb] > (2 * pi) or gamma[pb] < 0 or gamma[pb] > (2 * pi):
            return 0
    else:
        qc = Schedule(name="QAOA-MCP", repetitions=shots)
        qubits = init_qubits(v)
        qc.add(Reset(qubits[0]))
        for q in range(v):
            # Hadamard: Y90, X180
            qc.add(Rxy(0, 90, qubits[q]))
            qc.add(Rxy(180, 0, qubits[q]))
        
        for iteration in range(p):
            for e in edge_list:                     # TODO: fix CZ -> CNOT
                #qc.cnot(e[0], e[1])
                qc.add(Rxy(0, 90, qubits[e[1]]))
                qc.add(Rxy(180, 0, qubits[e[1]]))
                
                #qc.add(CZ(qubits[e[0]], qubits[e[1]]))
                qc.add(Rxy(180, 0, qubits[e[1]]))
                
                qc.add(Rxy(0, 90, qubits[e[1]]))
                qc.add(Rxy(180, 0, qubits[e[1]]))
                
                
                #qc.rz(-gamma[p-1], e[1])
                qc.add(Rxy(-90, 0, qubits[e[1]]))
                qc.add(Rxy(0, -1*gamma[p-1], qubits[e[1]]))
                qc.add(Rxy(90, 0, qubits[e[1]]))
                
                
                #qc.cnot(e[0], e[1])
                qc.add(Rxy(0, 90, qubits[e[1]]))
                qc.add(Rxy(180, 0, qubits[e[1]]))
        
                #qc.add(CZ(qubits[e[0]], qubits[e[1]]))
                qc.add(Rxy(180, 0, qubits[e[1]]))

                qc.add(Rxy(0, 90, qubits[e[1]]))
                qc.add(Rxy(180, 0, qubits[e[1]]))
                
            for qb in vertice_list:
                #qc.rx(2*beta[p-1], qb)
                qc.add(Rxy(2*beta[p-1], 0, qubits[qb]))
                
        for q in qubits:
            qc.add(Measure(q))
            
        return qc

qubits = 5
graph = gg.regular_graph(qubits)
params = [0.3*pi]*(qubits*2)
sched = qaoa_mcp(params, graph, 1, 10)

lo0 = MockLocalOscillator("lo0")
cluster = Cluster("cluster0", '192.168.0.2')
qblox_backend = qblox_hardware.ClusterBackend(qubits=size,
                                              module_config={"2":{"type":"QCM", "qubits":[0,1,2,3]},
                                                             "3":{"type":"QCM", "qubits":[4, 5, 6, 7]},
                                                             "4":{"type":"QCM", "qubits":[8,9,10,11]},
                                                             "5":{"type":"QCM", "qubits":[12, 13, 14, 15]},
                                                             "6":{"type":"QRM", "qubits":[0,1,2,3, 4, 5]},
                                                             "7":{"type":"QRM", "qubits":[6, 7, 8, 9, 10, 11]},
                                                             "8":{"type":"QRM", "qubits":[12, 13, 14, 15]},
                                                             #"9":{"type":"QCM_RF", "qubits":[16, 17]},
                                                             #"10":{"type":"QCM_RF", "qubits":[18, 19]},
                                                             "11":{"type":"QCM_RF", "qubits":[16, 17]},
                                                             "12":{"type":"QCM_RF", "qubits":[18, 19]},
                                                             "13":{"type":"QRM_RF", "qubits":[16, 17]},
                                                             "14":{"type":"QRM_RF", "qubits":[18, 19]}
                                                             },
                                              name = "qblox_cluster")



