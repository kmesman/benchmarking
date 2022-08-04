#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu May  5 09:45:30 2022

Generate custom config

TODO: needs cleanup
@author: koen
"""

import json
from pathlib import Path
import copy
import inspect

import quantify_scheduler.schemas.examples as es
from quantify_scheduler.device_under_test.quantum_device import QuantumDevice
from quantify_scheduler.device_under_test.transmon_element import BasicTransmonElement


def QCM_config(qubit_index, addtype = ""):
    instrument_dct = {"instrument_type": "{}QCM".format(addtype), 
    "ref": "internal",
    "complex_output_0":{"portclock_configs":[]},
    "complex_output_1":{"portclock_configs":[]}
    }
    print(qubit_index)
    instrument_dct["complex_output_0"]["portclock_configs"].append({"port" : "q{}:mw".format(qubit_index[0]),
                                                 'clock' : "q{}.01".format(qubit_index[0]),
                                                 "interm_freq": None})
    """
    instrument_dct["real_output_0"] = {"portclock_configs":
                                               [{"port" : "q{}:fl".format(qubit_index[0]),
                                                 'clock' : "q0.baseband"}
                                                ]
                                               }
    """
    if len(qubit_index)>1:
        instrument_dct["complex_output_1"]["portclock_configs"].append({"port" : "q{}:mw".format(qubit_index[1]),
                                                     'clock' : "q{}.01".format(qubit_index[1]),
                                                     "interm_freq": None})
    if len(qubit_index)>2:
        instrument_dct["complex_output_0"]["portclock_configs"].append({"port" : "q{}:mw".format(qubit_index[2]),
                                                     'clock' : "q{}.01".format(qubit_index[2]),
                                                     "interm_freq": None} )
    if len(qubit_index)>3:
        instrument_dct["complex_output_1"]["portclock_configs"].append({"port" : "q{}:mw".format(qubit_index[3]),
                                                     'clock' : "q{}.01".format(qubit_index[3]),
                                                     "interm_freq": None})
                        
            
    """
        instrument_dct["real_output_1"] = {"portclock_configs":
                                                   [{"port" : "q{}:fl".format(qubit_index[1]),
                                                     'clock' : "q0.baseband"}
                                                    ]
                                                   }
    """
    return instrument_dct


def QCM_RF_config(qubit_index, freq_config, lo=False):
    #instrument_dct = {"instrument_type": "QCM_RF", 
    #"ref": "internal"}

    dct = {"instrument_type": "QCM_RF",
           "complex_output_0" : {
               "portclock_configs" : []}
           }
    for q in qubit_index:
        portclock = {"port" : "q{}:mw".format(q),
          'clock' : "q{}.01".format(q),
          "interm_freq": freq_config["interm_freq"][str(q)]}
        dct["complex_output_0"]["portclock_configs"].append(portclock)

    """
    instrument_dct["complex_output_0"] = {"portclock_configs":
                                               [{"port" : "q{}:mw".format(qubit_index[0]),
                                                 'clock' : "q{}.01".format(qubit_index[0]),
                                                 "interm_freq": freq_config["interm_freq"][str(qubit_index[0])]}
                                                ]
                                               }
    if len(qubit_index)>1:
        instrument_dct["complex_output_1"] = {"portclock_configs":
                                                   [{"port" : "q{}:mw".format(qubit_index[1]),
                                                     'clock' : "q{}.01".format(qubit_index[1]),
                                                     "interm_freq": freq_config["interm_freq"][str(qubit_index[1])]}
                                                    ]
                                                   }

    """
 
    return dct

    
def QRM_config(module, addtype="", lo=False):
    qubits = module["qubits"]
    if not module.get('control'):
        dct = {"instrument_type": "{}QRM".format(addtype),
               "ref": "internal",
               "complex_output_0" : {
                   "lo_name" : "lo0",
                   "portclock_configs" : []},
               "real_output_0" : {
                   "lo_name" : "lo0",
                   "portclock_configs" : []}
               }
        for q in qubits:
            portclock = {"port": "q{}:res".format(q),
             "clock": "q{}.ro".format(q)}
            if q%2 == 0:
                dct["complex_output_0"]["portclock_configs"].append(
                        {"port": "q{}:res".format(q),
                         "clock": "q{}.ro".format(q)}
                    )
            else:
                dct["real_output_0"]["portclock_configs"].append(
                        portclock)
    else:
        dct = {"instrument_type": "{}QCM".format(addtype), 
        "ref": "internal",
        "complex_output_0":{"portclock_configs":[]},
        "complex_output_1":{"portclock_configs":[]}
        }
        dct["complex_output_0"]["portclock_configs"].append({"port" : "q{}:mw".format(qubits[0]),
                                                     'clock' : "q{}.01".format(qubits[0]),
                                                     "interm_freq": None})

        if len(qubits)>1:
            dct["complex_output_1"]["portclock_configs"].append({"port" : "q{}:mw".format(qubits[1]),
                                                         'clock' : "q{}.01".format(qubits[1]),
                                                         "interm_freq": None})
    
    return dct


def QRM_RF_config(module, freq_config=[], lo=False):
    qubits = module['qubits']
    control = module.get('control')
 

    if not control:
        dct = {"instrument_type": "QRM_RF",
               "complex_output_0" : {
                   "lo_freq" : 3e9,
                   "portclock_configs" : []}
               }
        for q in qubits:
            if q%2 == 0:
                dct["complex_output_0"]["portclock_configs"].append(
                        {"port": "q{}:res".format(q),
                         "clock": "q{}.ro".format(q)#,
                         #"interm_freq":-300000000
                         }
                    )
            else:
                dct["complex_output_0"]["portclock_configs"].append(
                        {"port": "q{}:res".format(q),
                         "clock": "q{}.ro".format(q)})
    else:
        dct = {"instrument_type": "QRM_RF",
               "complex_output_0" : {
                   "portclock_configs" : []}
               }
        for q in qubits:
            portclock = {"port" : "q{}:mw".format(q),
              'clock' : "q{}.01".format(q),
              "interm_freq": freq_config["interm_freq"][str(q)]}
            dct["complex_output_0"]["portclock_configs"].append(portclock)
    return dct
    


def generate_cluster_config(modules, freq_config, lo):
    json_obj = {"backend":"quantify_scheduler.backends.qblox_backend.hardware_compile"}
    json_obj["cluster0"] = {"ref": "internal", "instrument_type":"Cluster"}
    
    for slot, info in modules.items():
            qubits = info['qubits']
            instrument_type = info['type']
            if instrument_type == "QCM":
                instrument_json = QCM_config(qubits)
            elif instrument_type == "QCM_RF":
                instrument_json = QCM_RF_config(qubits, freq_config)
            elif instrument_type == "QRM":
                instrument_json = QRM_config(info, lo=lo)
            elif instrument_type == "QRM_RF":
                instrument_json = QRM_RF_config(info, freq_config, lo=lo)


            json_obj["cluster0"]["cluster0_module{}".format(slot)] = instrument_json
    if lo:
        print("lo True")
        lo_config = {"instrument_type": "LocalOscillator", "frequency": 2e7, "power": 15}
        json_obj["lo0"] = lo_config
    
    return json_obj

def generate_pulsar_config(modules, freq_config):
    json_obj = {"backend":"quantify_scheduler.backends.qblox_backend.hardware_compile"}
    index = 0
    for module in modules.values():
        qubits = module['qubits']
        instrument_type = module['type']
        if instrument_type == "QCM":
            instrument_json = QCM_config(qubits, addtype = "Pulsar_")
            json_obj["qcm{}".format(index)] = instrument_json
            

        elif instrument_type == "QRM":
            instrument_json = QRM_config(qubits, addtype = "Pulsar_")
            json_obj["qrm{}".format(index)] = instrument_json
            
    return json_obj
    
###############################################################################

def map_all_edges(qubits):
    edges = []
    for i in range(len(qubits)):
        for j in range(i+1, len(qubits)):
            if i!=j:
                edges.append([qubits[i],qubits[j]])
                edges.append([qubits[j],qubits[i]])
    return edges


# !Cleanup
def generate_dummy_device_map(freq_config={}):
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
    rf_qubits = freq_config.get('IF')
    qubits = list(freq_config['mw_freq'].keys())
    freq_config = freq_config['mw_freq']
    
    esp = inspect.getfile(es)
    cfg_f = Path(esp).parent / 'transmon_test_config.json'
    with open(cfg_f, 'r') as f:
        mapping = json.load(f)
    base = mapping['qubits']
    base['q0']
    qubit = base['q0']
    for i in qubits:
        base['q{}'.format(i)] = copy.deepcopy(qubit)
        base['q{}'.format(i)]['params']['mw_freq'] = freq_config['{}'.format(i)]
        if i in rf_qubits:
            base['q{}'.format(i)]['params']['mw_freq'] = 5000000000
            base['q{}'.format(i)]['params']['ro_freq'] = 2.8e9
            base['q{}'.format(i)]['params']['mw_amp180'] = 0.1
            base['q{}'.format(i)]['params']['1mw_motzoi'] = 0.1
            base['q{}'.format(i)]['params']['mw_ef_amp180'] = 0.1
        else:
            base['q{}'.format(i)]['params']['ro_freq'] = 3e8
        base['q{}'.format(i)]['resources']["port_mw"] = "q{}:mw".format(i)
        base['q{}'.format(i)]['resources']["port_ro"] = "q{}:res".format(i)
        base['q{}'.format(
            i)]['resources']["port_flux"] = "q{}:fl".format(i)
        base['q{}'.format(i)]['resources']["clock_01"] = "q{}.01".format(i)
        base['q{}'.format(i)]['resources']["clock_12"] = "q{}.12".format(i)
        base['q{}'.format(i)]['resources']["clock_ro"] = "q{}.ro".format(i)
        base['q{}'.format(i)]['params']['mw_amp180'] = 0.1
        base['q{}'.format(i)]['params']['1mw_motzoi'] = 0.1
        base['q{}'.format(i)]['params']['mw_ef_amp180'] = 0.1

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
    return mapping

def generate_dummy_device_obj(device_config):
    print("setting up quantum device")
    quantumdevice = QuantumDevice('TestDevice')
    quantumdevice.instr_instrument_coordinator('IC')
    qubits = []
    for qubit, values in device_config["qubits"].items():
        params = values["params"]
        qubits.append(BasicTransmonElement(qubit))
        qubits[-1].clock_freqs.f01(params["mw_freq"])
        qubits[-1].clock_freqs.readout(params['ro_freq'])
        qubits[-1].rxy.amp180(params["mw_amp180"])
        qubits[-1].measure.acq_delay(params["ro_acq_delay"])
        qubits[-1].measure.pulse_amp(params["ro_pulse_amp"])
        quantumdevice.add_element(qubits[-1])
    print(quantumdevice)
    return quantumdevice, qubits



""" TODO
def generate_dummy_device_obj(hw_config, freq_config={}):
    quantumdevice = QuantumDevice('TestDevice')
    quantumdevice.instr_instrument_coordinator('IC')
    quantumdevice.hardware_config(hw_config)
    qubits = range(5)
    q_reg = []
    for q in qubits:
        q_reg.append(BasicTransmonElement('q{}'.format(q)))
        q_reg[q].clock_freqs.f01(6e9)
        q_reg[q].clock_freqs.readout(5e9)
        q_reg[q].rxy.amp180(0.03)
        q_reg[q].measure.acq_delay(100e-9)
        q_reg[q].measure.pulse_amp(0.05)
        # repitions: 1024
        quantumdevice.add_element(q_reg[q])
"""
"""
## in  runner:
    if type device config == quantum_device:
        run_gettable
    else:
        run()
"""
###############################################################################

def freq_config(modules):

    IF = {}
    mw_freq = {}
    lo_freq = 5e9
    base_mw = 5.5e9
    freq_step = 5e7
    q = 0
    rf_qubits = []
    for module_info in modules.values():
        module = module_info['type']
        if module == "QCM" or module == "QCM_RF":
                for qubit in module_info["qubits"]:
                    if module == "QCM_RF":
                        mw_freq[str(qubit)] = base_mw#+q*freq_step
                        IF[str(qubit)] = -1*freq_step#*q
                        rf_qubits.append(str(qubit))
                    else:
                        mw_freq[str(qubit)] = 1e8 + q*1e7
                    q+=1
        #if module == "QRM" or module == "QRM_RF":
        if module == "QRM_RF" and module_info.get('control'):
            for qubit in module_info["qubits"]:
                mw_freq[str(qubit)] = base_mw#+q*freq_step
                IF[str(qubit)] =  -1*freq_step#*q
                rf_qubits.append(str(qubit))
                q+=1
        if module == "QRM" and module_info.get('control'):
            for qubit in module_info["qubits"]:
                mw_freq[str(qubit)] = 1e8 + q*1e7
                q+=1
                
    out = {'interm_freq':IF, 'mw_freq': mw_freq, 'lo_freq' : lo_freq, "IF":rf_qubits}
    print(out)
    return out 
