#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 24 14:47:38 2022

Library with supported cost functions
Includes:
    Max cut problem (mcp)
    Dominating set problem (dsp)
    Traveling salesman problem (tsp)
@author: koen
"""

def mcp(job, graph, inverted=False):
    """
    Cost evaluation for the max cut problem, with correction for minimization.
    """
    measurement = job["counts"]
    def eval_cost(meas, graph):
        # evaluate Max-Cut
        edges = graph[1]
        cost = 0
        bin_val = [int(i) for i in list(meas)]
        bin_val = [-1 if x == 0 else 1 for x in bin_val]
        for e in edges:
            cost += 0.5 * (1 - int(bin_val[e[0]]) * int(bin_val[e[1]]))
        return cost
    
    # average cost results
    prob = list(measurement.values())
    shots = sum(prob)
    states = list(measurement.keys())
    exp = 0
    for k in range(len(states)):
        exp += eval_cost(states[k], graph)*prob[k]
    exp = exp/shots

    #return result with correction
    if inverted:
        correction = -1
    else:
        correction = 1
    return exp*correction
    

# needs cleanup
def dsp_cost(measurement, graph, inverted=False):
    """
    Cost evaluation for the dominating set problem.
    """
    v, e = graph
    beta = params[0:p]
    gamma = params[p:2*p]


    edge_list = e
    vertice_list = list(range(0, v, 1))
    connections = []
    for i in range(v):
        connections.append([i])
    for t in edge_list:
        connections[t[0]].append(t[1])
        connections[t[1]].append(t[0])
    total_count = 0
    total_cost = 0
    for p_it in measurement:
        for t in measurement:
            count = int(measurement.get(t))
            total_count += count
            bin_len = "{0:0" + str(v) + "b}"  # string required for binary formatting
            bin_val = t.format(bin_len)
            bin_val = [int(i) for i in bin_val]
            T = 0
            for con in connections:
                tmp = 0
                for k in con:
                    tmp = tmp or bin_val[k]
                    if tmp:
                        T += 1
                        break
            D = 0
            for i in range(v):
                D += 1 - bin_val[i]
            total_cost += (T+D)*count
    total_cost = total_cost/total_count
    return total_cost


#needs cleanup
def cost_tsp(measurement, graph, inverted=False):
    """
    Cost evaluation for the traveling salesman problem.
    """
    v, A, D = graph
    total_cost = 0
    for t in measurement:
        count = int(measurement.get(t))
        bin_len = "{0:0" + str(v) + "b}"  # string required for binary formatting
        bin_val = t.format(bin_len)
        bin_val = [int(i) for i in bin_val]
        cost = 0
        coupling = []
        for i in range(v):
            for j in range(i):
                if i != j:
                    coupling.append([i+j*v, j+i*v])

        for i in range(0, v):
            for j in range(i, v):
                cost += D[i + v*j]*bin_val[i + v*j]
        for j in coupling:
            cost += -5*(1 - 2*bin_val[j[0]])*(1 - 2*bin_val[j[1]])
        total_cost += cost*count/rep

    return total_cost