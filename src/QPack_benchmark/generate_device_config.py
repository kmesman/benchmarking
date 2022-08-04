#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May 13 11:00:34 2022

@author: koen
"""

import json
from pathlib import Path
import inspect
import copy

import quantify_scheduler.schemas.examples as es


qubits = 5
"""
Current issues:
        no support for 2-qubit gates
        unclear where q{}:mw is specified
        
from qcodes.instrument import Instrument
from quantify_scheduler.device_under_test import transmon_element, quantum_device
Instrument.close_all()

transmon_obj = quantum_device.QuantumDevice("transmon")
qubit_elements = []
for q in range(qubits):
    qubit_elements.append(transmon_element.TransmonElement("q{}".format(q)))
    transmon_obj.add_component(qubit_elements[q])
    #qubit_elements[q].print_readable_snapshot()

device_config = transmon_obj.generate_device_config()
print(device_config)
"""

def map_all_edges(qubits):
    edges = []
    for i in range(qubits):
        for j in range(i+1, qubits):
            edges.append([i,j])
            edges.append([j,i])
    return edges


# !Cleanup
def generate_dummy_device_map(qubits, rf_qubits=[], freq_config={}):
    """
    Generate a dummy config file for a transmon device.
    inputs:
            qubits: number of total qubits
            rf_qubits: dict of qubits indicating which of the qubits are RF
    """
    
    """
    # exception for custom config files
    if self.device_path != 'transmon_dummy_config.json':
        with open(self.device_path, 'r') as f:
            base = json.load(f)
            return base
    """
    
    esp = inspect.getfile(es)
    cfg_f = Path(esp).parent / 'transmon_test_config.json'
    with open(cfg_f, 'r') as f:
        mapping = json.load(f)
    base = mapping['qubits']
    base['q0']
    qubit = base['q0']
    for i in range(qubits):
        base['q{}'.format(i)] = copy.deepcopy(qubit)
        base['q{}'.format(i)]['params']['mw_freq'] = 50000000
        if i in rf_qubits:
            base['q{}'.format(i)]['params']['ro_freq'] = 3000000000
            base['q{}'.format(i)]['params']['mw_amp180'] = 0.1
        else:
            base['q{}'.format(i)]['params']['ro_freq'] = 50000000
        base['q{}'.format(i)]['resources']["port_mw"] = "q{}:mw".format(i)
        base['q{}'.format(i)]['resources']["port_ro"] = "q{}:res".format(i)
        base['q{}'.format(
            i)]['resources']["port_flux"] = "q{}:fl".format(i)
        base['q{}'.format(i)]['resources']["clock_01"] = "q{}.01".format(i)
        base['q{}'.format(i)]['resources']["clock_12"] = "q{}.12".format(i)
        base['q{}'.format(i)]['resources']["clock_ro"] = "q{}.ro".format(i)

        sample_con = copy.deepcopy(mapping['edges']['q0-q1'])
        edges = map_all_edges(qubits)
        for e in edges:
            mapping['edges']['q{}-q{}'.format(e[0], e[1])] = sample_con
            mapping['edges']['q{}-q{}'.format(
                e[0], e[1])]['resource_map']['q{}'.format(e[0])] = 'q{}:fl'.format(e[0])
            mapping['edges']['q{}-q{}'.format(
                e[0], e[1])]['resource_map']['q{}'.format(e[1])] = 'q{}:fl'.format(e[1])
            mapping['edges']['q{}-q{}'.format(
                e[0], e[1])]['params']['flux_amp_control'] = 0.1
            """
            mapping['edges']['q{}-q{}'.format(e[1], e[0])] = sample_con
            mapping['edges']['q{}-q{}'.format(
                e[1], e[0])]['resource_map']['q{}'.format(e[1])] = 'q{}:fl'.format(e[1])
            mapping['edges']['q{}-q{}'.format(
                e[1], e[0])]['resource_map']['q{}'.format(e[0])] = 'q{}:fl'.format(e[0])
            mapping['edges']['q{}-q{}'.format(
                e[1], e[0])]['params']['flux_amp_control'] = 0.1
            """
    return mapping
