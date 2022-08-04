#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr  5 12:54:33 2022

Test circuit
@author: koen
"""

from quantify_scheduler import Schedule
from quantify_scheduler.operations.gate_library import Rxy, Measure, Reset

def init_qubits(size):
    q = []
    for i in range(size):
        q.append('q' + str(i))
    return q

def circuit_run(shots, size, backend):
    qc = Schedule(name="test-circuit", repetitions=shots)
    qubits = init_qubits(size)
    qc.add(Reset(qubits[0]))
    
    
    for q in range(size):
        # Hadamard: Y90, X180
        qc.add(Rxy(0, 90, qubits[q]))
        qc.add(Rxy(180, 0, qubits[q]))

            
    for q in qubits:
        qc.add(Measure(q))
    
    job = backend.run(qc, shots=shots)
    result = job["counts"]
    time_dict = job["time_per_step"]
    return [result, time_dict]