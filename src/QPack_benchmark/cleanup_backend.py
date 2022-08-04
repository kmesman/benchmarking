#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 4 2022

Configure hardware cluster
@author: koen
"""

# TODO: integrate device config
# TODO: reorder methods
# TODO: verify when cluster component needs to be initialized
# TODO: raise error if module config does not comply with found hardware
# Needs cleanup and restructure

import runner

from qcodes.instrument import Instrument
from quantify_core.data.handling import set_datadir
from quantify_scheduler.instrument_coordinator import InstrumentCoordinator
from qblox_instruments import Cluster, ClusterType
import generate_qblox_config as gen_config

from quantify_scheduler.instrument_coordinator.components.qblox import ClusterComponent, QCMComponent, QRMComponent, QRMRFComponent, QCMRFComponent

import re
from pathlib import Path
import json
import copy

from math import ceil

class Backend:
    def __init__(self,
        hardware_path=None,
        device_path=None,
        ip="",
        module_config = {},
        name = "",
        qubits = 0
        ):
        """
        Class containing the quantum computer setup. This includes the hardware
        and device configuration. This class contains the methods to run a
        quantify schedule. The backend instance should be closed with the
        close() method.
        
        Parameters
        ----------
        hardware_path : str, optional
            Path to the hardware config file. The default is None.
        device_path : str, optional
            Path to the device config file. The default is None.
        module_config : dict, optional
            Dict containing the configuration of the cluster modules. The
            default is {}.
        name : str, optional
            Name of the backend instance. The default is "".
        qubits: int, optional
            If no hardware configuration or cluster object is created, the
            number of required qubits should be given. The default is None.
        """
        
        #Define default storage location for schedules
        datadir = Path.home()/"quantify-data"
        set_datadir(datadir)
        self.qubits = qubits
        self.module_config = module_config
        if ip:
            cluster = Cluster("cluster0", ip)
        

        # configure modules with given information
        self.name = name
        cluster_exists = self._cluster_exists()
        if cluster_exists and module_config:
            #check if config complies with hardware
            self.get_qubits()

        if cluster_exists and not module_config:
            print("auto creating config")
            self._create_module_config_from_instrument()
            
        # if no cluster is connected, create dummy cluster
        elif module_config and not cluster_exists:
                #create from module config
                self.module_config = module_config
                self._create_dummy_cluster()
        elif qubits and not cluster_exists:
                #create from number of qubits
                self._create_module_config_from_qubits(qubits)
                self.qubits = 0
                self._create_dummy_cluster()
        #create dummy frequency configuration
        print(self.module_config)
        self.frequency_config = gen_config.freq_config(self.module_config)
        

        
        #add hardware to ic and set configuration
        self._set_hardware_config(hardware_path)
        print(Instrument._all_instruments)

        self._set_device_config(device_path)
        self._configure_ic()


    def _set_hardware_config(self, hardware_path):
        """
        This method loads the hardware configuration. If no path is defined by
        the user, a dummy config file will be generated.
        
        Parameters
        ----------
        hardware_path : str
            Path to the config file of the hardware.
            
        """
        
        if hardware_path:
            with open(hardware_path, 'r') as file:
                self.hardware_config = json.load(file)
        else:
            self.hardware_config = gen_config.generate_cluster_config(self.module_config, self.frequency_config)
            with open("config/generated_hardware_config.json", 'w') as f:
                json.dump(self.hardware_config, f, indent=4, separators=(',', ': '))
            
            

    def _cluster_exists(self):
        instruments = Instrument._all_instruments
        print(instruments)
        return any('cluster' in name for name in instruments)


    def get_qubits(self):
        self.rf_qubits = []
        qubits = []
        for rmrf in self.module_config["QRM_RF"].values():
            if rmrf['control']:
                [self.rf_qubits.append(q) for q in rmrf['qubits']]
        for cmrf in self.module_config["QCM_RF"].values():
            [self.rf_qubits.append(q) for q in cmrf['qubits']]  
        for cm in self.module_config["QCM"].values():
            [qubits.append(q) for q in cm['qubits']]
        qubits.append(self.rf_qubits)
        self.qubits = len(qubits)

    def _create_module_config_from_instrument(self):
        # TODO: test if enough qubits are allocated to the readout modules
        """
        Creates a module configuration from cluster instrument.
        Config example: {"QCM":{"8":{"qubits":[0, 1]}}, "QRM": {"5" : {"qubits":[0, 1]}}, "QCM_RF": {"3" : {"qubits":[2, 3]}},
                   "QRM_RF":{"16" : {"qubits":[4], "control":True}, "17":{"qubits":[2, 3, 4], 'control':False}}}#, "LO":[None]
        
        New: {"1" : {"qubits":[0, 1]}, "2" : {"qubits":[0, 1, 2],"type":"QRM_RF" },
              "16" : {"qubits" : [2], "type": QRM_RF, "control" : True} }
        
        """
        
        instr_dict = Instrument._all_instruments.copy()
        for name in instr_dict.keys():
            if re.search("cluster.*", name):
                cluster = Instrument.find_instrument(name)
                self.cluster_comp = ClusterComponent(cluster)
        
        modules = self.cluster_comp._cluster_modules
        self.module_config = {'QCM':{}, 'QCM_RF':{}, 'QRM':{}, 'QRM_RF':{}}
        
        control_qubits = 0
        control_qubits_array = []
        control_rf_qubits = []
        # TODO: test
        
        for mod in modules:
            slot_nr = mod.replace('cluster0_module','')
            if type(modules[mod]) == QCMComponent:
                control_qubits+=2
                control_qubits_array.append(control_qubits-2)
                control_qubits_array.append(control_qubits-1)
                self.module_config['QCM']['{}'.format(slot_nr)] = {'qubits': [control_qubits-2, control_qubits-1]}
            if type(modules[mod]) == QCMRFComponent:
                control_qubits+=2
                control_rf_qubits.append(control_qubits-2)
                control_rf_qubits.append(control_qubits-1)
                self.module_config['QCM_RF']['{}'.format(slot_nr)] = {'qubits': [control_qubits-2, control_qubits-1]}
        
        self.rf_qubits = control_rf_qubits
        
        # under review
        def get_readout_adr(control_qubits_array):
            if len(control_qubits_array) <6:
                readout_arr = control_qubits_array
                control_qubits_array = []
            else:                     
                readout_arr = control_qubits_array[0:5]
                del control_qubits_array[0:5]
            return control_qubits_array, readout_arr
        
        control_rf_arr = control_rf_qubits.copy()
        for mod in modules:
            if type(modules[mod]) == QRMComponent:
                control_qubits_array, readout_qubits_arr = get_readout_adr(control_qubits_array)
                self.module_config['QRM']['{}'.format(slot_nr)] = {'qubits': readout_qubits_arr, 'control': False}
                
            if type(modules[mod]) == QRMRFComponent:
                control_rf_arr, readout_rf_arr = get_readout_adr(control_rf_arr)
                self.module_config['QRM_RF']['{}'.format(slot_nr)] = {'qubits': readout_rf_arr, 'control': False}
        

        self.qubits = control_qubits
            
            
    def _create_dummy_cluster(self):
        """
        Creates dummy cluster and modules from the module configuration.

        Returns
        -------
        None.

        """
        instr_dict = Instrument._all_instruments.copy()
        dummy_cfg_dct = {}
        qubits = 0
        for qcm_module in self.module_config['QCM']:
            dummy_cfg_dct[qcm_module] = ClusterType.CLUSTER_QCM
            self.qubits += len(self.module_config['QCM'][qcm_module]['qubits'])
        for qrm_module in self.module_config['QRM']:
            dummy_cfg_dct[qrm_module] = ClusterType.CLUSTER_QRM
        for qcmrf_module in self.module_config['QCM_RF']:
            dummy_cfg_dct[qcmrf_module] = ClusterType.CLUSTER_QCM_RF
            self.qubits += len(self.module_config['QCM_RF'][qcmrf_module]['qubits'])
        for qrmrf_module in self.module_config['QRM_RF']:
            dummy_cfg_dct[qrmrf_module] = ClusterType.CLUSTER_QRM_RF
            if self.module_config['QRM_RF'][qrmrf_module]['control']:
                self.qubits += len(self.module_config['QRM_RF'][qrmrf_module]['qubits'])

        if 'cluster0' not in instr_dict.keys():
            cl  = Cluster("cluster0", dummy_cfg=dummy_cfg_dct)
        self.rf_qubits = []
        for slot in self.module_config['QRM_RF'].values():
            for qubits in slot.values():
                if type(qubits) == list:
                    [self.rf_qubits.append(q) for q in qubits]
                else:
                    self.rf_qubits.append(qubits)
        
    def _create_module_config_from_qubits(self, qubits):
        """
        Create a dummy configuration for the number cluster modules required
        given the number of required qubits.

        Returns
        -------
        module_config : dict
            module slot configuration, indicating the qubits controlled or read by
            each module.
        """
        if not qubits:
            raise Exception("""Provide either the number of qubits required, or
                            create a cluster instance""")
        module_config = {"QCM":{}, "QRM":{}, "QCM_RF": {}, "QRM_RF":{}}
        module_config["QCM"] = {}
        module_config["QRM"] = {}
        module_index = 1
        max_modules = int(ceil(qubits/2))
        for qubit in range(0, qubits, 2):
            module_config["QCM"][str(module_index)] = {'qubits':[qubit, qubit+1]}
            module_config["QRM"][str(module_index+max_modules)] = {'qubits':[qubit, qubit+1], 'control':False}
            module_index += 1
        self.qubits = qubits
        return module_config


    def _set_device_config(self, device_path):
        if device_path:
            with open(device_path, 'r') as file:
                self.device_config = json.load(file)
        else:
            self.device_config = gen_config.generate_dummy_device_map(self.qubits, self.rf_qubits, self.frequency_config)
            with open("config/generated_device_config.json", 'w') as f:
                json.dump(self.device_config, f, indent=4, separators=(',', ': '))

    # under review
    def _configure_ic(self):
        """
        Includes all available hardware in the Instrument Coordinator.
        """
        self.ic = InstrumentCoordinator("IC")
        instr_dict = Instrument._all_instruments.copy()
        for name in instr_dict.keys():
            if re.search("cluster.*", name):
                cluster = Instrument.find_instrument(name)
                cluster_comp = ClusterComponent(cluster)
                break
        
        self.ic.add_component(cluster_comp)


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

    
    