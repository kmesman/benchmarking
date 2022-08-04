#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 24 15:26:50 2022

QAOA for quantify
@author: koen
"""
import time
from math import pi
from quantify_scheduler import Schedule
from quantify_scheduler.operations.gate_library import *
from quantify_scheduler.resources import BasebandClockResource
def init_qubits(size):
    q = []
    for i in range(size):
        q.append('q' + str(i))
    return q

def timeis(func):
    '''Decorator that reports the execution time.'''

    def wrap(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        
        return [result, end-start]
    return wrap


def qaoa_mcp_function(params, graph, p, backend, repetitions=0):
    beta = params[0:p]
    gamma = params[p:2*p]
    
    v, edge_list = graph
    vertice_list = list(range(0, v, 1))
    for pb in range(len(beta)):
        if beta[pb] < 0 or beta[pb] > (2 * pi) or gamma[pb] < 0 or gamma[pb] > (2 * pi):
            return 0
    else:
        qc = Schedule(name="QAOA-MCP", repetitions=repetitions)
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

@timeis
def qaoa_mcp(params, graph, p, backend, shots):
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
        
        #job = backend.run(qc, shots=shots)
        job = backend.run(qaoa_mcp_function,args=
                          {"params":params,
                           "graph":graph,
                           'p':p,
                           "backend":backend,
                           #"repetitions":shots
                           }, shots=shots)
        result = job["counts"]
        time_dict = job["time_per_step"]
    return job