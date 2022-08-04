#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun  2 14:56:01 2022

Pulsar backend, to be merged as subclass to backend.py
@author: koen
"""

import runner

from qcodes.instrument import Instrument
from quantify_core.data.handling import set_datadir
from quantify_scheduler.instrument_coordinator import InstrumentCoordinator
from qblox_instruments import Cluster, ClusterType
import generate_qblox_config as gen_config
from quantify_scheduler.instrument_coordinator.components.qblox import ClusterComponent, QCMComponent, QRMComponent, QRMRFComponent, QCMRFComponent, PulsarQCMComponent, PulsarQRMComponent

import re
from pathlib import Path
import json
import copy
from math import ceil

class PulsarBackend:
    def __init__(self,
        hardware_path=None,
        device_path=None,
        ip="",
        module_config = {},
        name = "",
        qubits = 0
        ):
        
        self.name = name
        
        #Define default storage location for schedules
        set_datadir(Path.home()/"quantify-data")
        
        
        self._pulsar_config()
        
        self._get_num_qubits()

        self.frequency_config = gen_config.freq_config(self.module_config)
            
        self._set_hardware_config(hardware_path)

        self._set_device_config(device_path)
        
        self._configure_ic()
        
        
    def _pulsar_config(self):
        config = {}
        instruments = Instrument._all_instruments.copy()
        cqubits = 0
        rqubits = 0
        self.components = []
        for name in instruments:
            if 'qcm' in name:
                config[name] = {'qubits': [cqubits, cqubits+1], 'type':'QCM'}
                self.components.append(PulsarQCMComponent(Instrument.find_instrument(name)))
                cqubits+=2
            if 'qrm' in name:
                config[name] = {'qubits': [rqubits, rqubits+1], 'type':'QRM'}
                self.components.append(PulsarQRMComponent(Instrument.find_instrument(name)))
                rqubits+=2
        self.module_config = config
                
                
    def _module_config_cluster(self):
        modules = self.cluster_comp._cluster_modules
        bb_qubits = []
        rf_qubits = []
        qubit_index = 0
        
        # get control mudules and assign qubits
        for mod in modules:
            slot_nr = mod.replace('cluster0_module','')
            
            if type(modules[mod]) == QCMComponent:
                self.module_config[slot_nr] = {'qubits': [qubit_index, qubit_index+1], 'type': "QCM"}
                bb_qubits.extend([qubit_index, qubit_index+1])
                qubit_index+= 2
            if type(modules[mod]) == QCMRFComponent:
                self.module_config[slot_nr] = {'qubits': [qubit_index, qubit_index+1], 'type': 'QCM_RF'}
                rf_qubits.extend([qubit_index, qubit_index+1])
                qubit_index+= 2
                
        # return number of available qubits
        self.qubits = len(bb_qubits) + len(rf_qubits)


        # get readout modules and assign qubits
        for mod in modules:
            slot_nr = mod.replace('cluster0_module','')

            if type(modules[mod]) == QRMComponent:
                self.module_config[slot_nr] = {'qubits': bb_qubits[:6], 'type':'QRM'}
                bb_qubits = bb_qubits[6:]
            if type(modules[mod]) == QRMRFComponent:
                self.module_config[slot_nr] = {'qubits': rf_qubits[:6], 'type':'QRM_RF'}
                bb_qubits = bb_qubits[6:]

            
            
    def _module_config_qubits(self):
        """
        Create a dummy configuration for the number cluster modules required
        given the number of required qubits.

        Returns
        -------
        module_config : dict
            module slot configuration, indicating the qubits controlled or read by
            each module.
        """

        module_index = 1
        max_modules = int(ceil(self.qubits/2)*2)
        for qubit in range(0, max_modules, 2):
            self.module_config[str(module_index)] = {'qubits':[qubit, qubit+1], 'type':'QCM'}
            module_index+=1
            
        for qubit_index in range(0, self.qubits, 6):
            self.module_config[str(module_index)] = {'qubits':list(range(qubit_index, qubit_index+6)), 'type':'QRM'}
            module_index += 1
            
            
    def _verify_config(self):
        instr_dict = self.cluster_comp._cluster_modules
        module_slots = [mod_name.replace('cluster0_module','') for mod_name in instr_dict]
        for slot, module_type in zip(self.module_config, instr_dict.values()):
            if slot not in module_slots:
                raise Exception('Configuration refers to slot {}, which is not present in the hardware.'.format(slot))
            self.module_config[slot]['type'] = {
                QCMComponent : "QCM",
                QRMComponent : "QRM",
                QCMRFComponent : "QCM_RF",
                QRMRFComponent : "QRM_RF"
                }.get(type(module_type))
    
    def _get_num_qubits(self):
        rf_qubits = []
        qubits = []
        for module in self.module_config.values():
            if module['type'] == 'QRM_RF' and module.get('control'):
                [rf_qubits.append(q) for q in module['qubits']]
            elif module['type'] == 'QCM':
                [qubits.append(q) for q in module['qubits']]
            elif module['type'] == 'QCM_RF':
                [rf_qubits.append(q) for q in module['qubits']]
        self.qubits = len(qubits) + len(rf_qubits)

        
    def _create_dummy_cluster(self):
        """
        Creates dummy cluster and modules from the module configuration.

        Returns
        -------
        None.

        """
        dummy_cfg = {}
        
        for slot, module_info in self.module_config.items():
            module_type = {
                "QCM" : ClusterType.CLUSTER_QCM,
                "QRM" : ClusterType.CLUSTER_QRM,
                "QCM_RF" : ClusterType.CLUSTER_QCM_RF,
                "QRM_RF" : ClusterType.CLUSTER_QRM_RF
                }.get(module_info['type'])
            dummy_cfg[slot] = module_type
        
        self.cluster  = Cluster("cluster0", dummy_cfg=dummy_cfg)
        self.cluster_comp = ClusterComponent(self.cluster)

        

        
    def _set_hardware_config(self, hardware_path):
        if hardware_path:
            with open(hardware_path, 'r') as file:
                self.hardware_config = json.load(file)
        else:
            self.hardware_config = gen_config.generate_pulsar_config(self.module_config, self.frequency_config)
            with open("config/generated_hardware_config.json", 'w') as f:
                json.dump(self.hardware_config, f, indent=4, separators=(',', ': '))
                
        
    
    def _set_device_config(self, device_path):
        if device_path:
            with open(device_path, 'r') as file:
                self.device_config = json.load(file)
        else:
            self.device_config = gen_config.generate_dummy_device_map(self.frequency_config)
            with open("config/generated_device_config.json", 'w') as f:
                json.dump(self.device_config, f, indent=4, separators=(',', ': '))
        
        
    def _configure_ic(self):
        """
        Includes all available hardware in the Instrument Coordinator.
        """

        self.ic = InstrumentCoordinator("IC")
        for component in self.components:
            self.ic.add_component(component)
        #self.ic.add_component(self.cluster_comp)
        
        
    def configuration(self):
        # define hardware name for Qpack
        if self.name != "":
            backend_name = self.name
        else:
            backend_name = "qblox_module"
        class config:
            def __init__(self, backend_name):
                self.backend_name = backend_name
        config_obj = config(backend_name)
        return config_obj
    
    
    def set_schedule_path(self, path):
        """
        Method to replace the storage path for schedules.

        Parameters
        ----------
        path : str
            Path to new directory.

        """
        set_datadir(Path.home()/path)
    
    
    def run(self, sched, shots=100):
        """
        Run the schedule in the backend.

        Parameters
        ----------
        sched : quantify_schedule
            quantify schedule.
        shots : int, optional
            Number of circuit shots per call. The default is 100.

        Returns
        -------
        job object
            object containing the timing results and solution result.

        """
        job = runner.algorithm_runner(shots=shots)
        return job.run(sched, self)
        
    
    def close(self):
        """
        Closes the Instrument coordinator and stops time measurement.
        """
        self.ic.close()
        
        
        
        
# subclass ClusterBackend

# subclass PulsarBackend
        
        
        
        