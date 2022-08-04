#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 24 14:44:27 2022

Qblox shot simulation
@author: koen
"""

from quantify_core.utilities.examples_support import *
from numpy import real, imag
import numpy as np
import collections
import math

def qi_threshold(data, thr):
    '''
    determine if the smallest distance is to cluster center of |0> or |1>
    '''
    data = [real(data), imag(data)]
    if abs(data[0] - thr[0][0]) + abs(data[1] - thr[0][1]
                                      ) < abs(data[0] - thr[1][0]) + abs(data[1] - thr[1][1]):
        return 1
    else:
        return 0

def q_threshold(data, thr):
    data = [real(data), imag(data)]
    if data[0] > thr[0][0]:
        return 1
    else:
        return 0
        
def auto_threshold(data, return_clusters=False):
    '''
    Using the K-means clustering algorithm,
    determine the threshold by averging the cluster centers
    returns: [imag threshold, real threshold]
    if return_cluster is set tot True, returns complex coordinates of cluster centers
    as [|1>, |0>]
    '''

    from sklearn.cluster import KMeans
    scaled_features = [[real(x), imag(x)] for x in data]
    kmeans = KMeans(
        init="k-means++",
        n_clusters=2
    )
    kmeans.fit(scaled_features)
    if return_clusters:
        return kmeans.cluster_centers_
    else:
        threshold = [
            (kmeans.cluster_centers_[0][1] + kmeans.cluster_centers_[1][1]) / 2,
            (kmeans.cluster_centers_[0][0] + kmeans.cluster_centers_[1][0]) / 2]
        return threshold

def simulate_shots(shots, val):
    qi_shots = mk_iq_shots(num_shots=shots, probabilities=[1-val, val])
    return qi_shots


def gen_emp_dct(res):
    size = len(list(res.keys())[0])
    modules = math.ceil(size / 2)
    dct = {}
    for i in range(modules):
        dct["qrm{}".format(i)] = {"seq0": [], "seq1": []}
    return dct


def add_to_mod_dict(res_dict, i, data):
    """
    Assign results to their respective module and sequencer.

    """
    
    mod = math.floor(i / 2)
    seq = i - mod * 2
    res_dict["qrm{}".format(mod)]["seq{}".format(seq)] += data
    return res_dict


def simulate_qi_res(sim_res):

    total_res = []
    emp_dict = gen_emp_dct(sim_res)

    for res in sim_res:
        meas = sim_res[res]
        inter_res = []
        i = 0
        for qubit in res:
            single_sim = list(simulate_shots(meas, int(qubit)))
            emp_dict = add_to_mod_dict(emp_dict, i, single_sim)
            i += 1

    return emp_dict


def to_str(arr):
    res = ""
    for b in arr:
        res += str(b)
    return res
