#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun  3 11:01:26 2022

@author: koen
"""

import runner_profiled as runner
import generate_qblox_config as gen_config

from qcodes.instrument import Instrument
from quantify_core.data.handling import set_datadir
from quantify_scheduler.instrument_coordinator import InstrumentCoordinator

from qblox_instruments import Cluster, ClusterType, Pulsar
from quantify_scheduler.instrument_coordinator.components.qblox import ClusterComponent, QCMComponent, QRMComponent, QRMRFComponent, QCMRFComponent, PulsarQCMComponent, PulsarQRMComponent

import re
from pathlib import Path
import json
from math import ceil
import time

def timeis(func):
    '''Decorator that reports the execution time.'''
  
    def wrap(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
          
        print(func.__name__, end-start)
        return result
    return wrap
  


class QbloxBackend:
    def __init__(self,
        hardware_path=None,
        device_path=None,
        module_config = {},
        name = "",
        qubits = 0
        ):
        self.name = name
        self.module_config = module_config

    @timeis
    def _get_num_qubits(self):
        rf_qubits = []
        qubits = []
        for module in self.module_config.values():
            if module['type'] == 'QRM_RF' and module.get('control'):
                [rf_qubits.append(q) for q in module['qubits']]
            elif module['type'] == 'QCM':
                [qubits.append(q) for q in module['qubits']]
            elif module["type"] == 'QRM' and module.get('control'):
                [qubits.append(q) for q in module['qubits']]
            elif module['type'] == 'QCM_RF':
                [rf_qubits.append(q) for q in module['qubits']]
        self.qubits = len(qubits) + len(rf_qubits)
        
    @timeis
    def _set_device_config(self, device_path):
        if device_path:
            with open(device_path, 'r') as file:
                self.device_config = json.load(file)
        else:
            self.device_config = gen_config.generate_dummy_device_map(self.frequency_config)
            with open("config/generated_device_config.json", 'w') as f:
                json.dump(self.device_config, f, indent=4, separators=(',', ': '))
        self.device_obj, self.qubit_obj = gen_config.generate_dummy_device_obj(self.device_config)
        
        
    @timeis
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
            
    @timeis        
    def set_schedule_path(self, path):
        """
        Method to replace the storage path for schedules.

        Parameters
        ----------
        path : str
            Path to new directory.

        """
        set_datadir(Path.home()/path)
    
    @timeis
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
    
    @timeis
    def run(self, sched, args, shots=100):
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
        print("running!")
        job = runner.algorithm_runner(shots=shots)
        return job.run(sched, self, args=args)
        
    
    def close(self):
        """
        Closes the Instrument coordinator and stops time measurement.
        """
        self.ic.close()
        

@timeis
class ClusterBackend(QbloxBackend):
    def __init__(self,
        hardware_path=None,
        device_path=None,
        ip="",
        module_config = {},
        name = "",
        qubits = 0,
        lo=False
        ):
        super().__init__(hardware_path, device_path,
                         module_config, name, qubits)
        
        #Define default storage location for schedules
        set_datadir(Path.home()/"quantify-data")
        
        
        cluster_exists = self._find_cluster(ip)
    
        # Create module configuration if none is given
        if not module_config:
            if cluster_exists:
                print("cluster found!")
                self._module_config_cluster()
            elif qubits:
                print("configuring backend from nr of qubits")
                self.qubits = qubits
                self._module_config_qubits()
            else:
                raise Exception("No hardware is connected and no dummy can be created.")
        elif cluster_exists:
            self._verify_config()
    
        if not any(mod.get('type') for mod in self.module_config.values()):
            raise Exception("No module types provided in configuration.")
            
        if not cluster_exists:
            self._create_dummy_cluster()
        
        self._get_num_qubits()
        
        self.frequency_config = gen_config.freq_config(self.module_config)
        self._set_hardware_config(hardware_path, lo)
        self._set_device_config(device_path)
        self._configure_ic()
    
    @timeis
    def _find_cluster(self, ip):
        """
        Method to check if cluster is in known instruments. Adds cluster
        as component if found. If an ip adress gives, create cluster object.

        Returns
        -------
        flag : Boolean

        """
        flag = False
        if ip:
            tick = time.time()
            self.cluster = Cluster("cluster0", ip)
            tock = time.time()
            print("create cluster instance", tock-tick)
            flag = True
        else:
            # Test if cluster in known instruments        
            instr_dict = Instrument._all_instruments.copy()
            for name in instr_dict.keys():
                if re.search("cluster.*", name):
                    self.cluster = Instrument.find_instrument(name)
                    flag = True
        if flag:            
            self.cluster_comp = ClusterComponent(self.cluster)
        
        return flag
        
    @timeis
    def _module_config_cluster(self):
        modules = self.cluster_comp._cluster_modules
        bb_qubits = []
        rf_qubits = []
        qubit_index = 0
        
        # get control mudules and assign qubits
        for mod in modules:
            slot_nr = mod.replace('cluster0_module','')
            
            if type(modules[mod]) == QCMComponent:
                self.module_config[slot_nr] = {'qubits': [qubit_index, qubit_index+1, qubit_index+2, qubit_index+3], 'type': "QCM"}
                bb_qubits.extend([qubit_index, qubit_index+1, qubit_index+2, qubit_index+3])
                qubit_index+= 4
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
                rf_qubits = rf_qubits[6:]
        print("module config:", self.module_config)

    @timeis
    def _verify_config(self):
        instr_dict = self.cluster_comp._cluster_modules
        module_slots = [mod_name.replace('cluster0_module','') for mod_name in instr_dict]
        types = dict(zip(module_slots, instr_dict.values()))
        #for slot, module_type in zip(self.module_config, instr_dict.values()):
        for slot in self.module_config:

            if slot not in module_slots:
                raise Exception('Configuration refers to slot {}, which is not present in the hardware.'.format(slot))
            self.module_config[slot]['type'] = {
                QCMComponent : "QCM",
                QRMComponent : "QRM",
                QCMRFComponent : "QCM_RF",
                QRMRFComponent : "QRM_RF"
                }.get(type(types[slot]))

    @timeis
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

    @timeis    
    def _set_hardware_config(self, hardware_path, lo):
        if hardware_path:
            with open(hardware_path, 'r') as file:
                self.hardware_config = json.load(file)
        else:
            self.hardware_config = gen_config.generate_cluster_config(self.module_config, self.frequency_config, lo)
            with open("config/generated_hardware_config.json", 'w') as f:
                json.dump(self.hardware_config, f, indent=4, separators=(',', ': '))
                     
    @timeis    
    def _configure_ic(self):
        """
        Includes all available hardware in the Instrument Coordinator.
        """

        self.ic = InstrumentCoordinator("IC")
        self.ic.add_component(self.cluster_comp)
        
 
@timeis
class PulsarBackend(QbloxBackend):
    def __init__(self,
        hardware_path=None,
        device_path=None,
        module_config = {},
        name = "",
        qubits = 0
        ):
        
        __slots__ = ('qubits', 'module_config', 'components', 'pulsars', 'frequency_config',
                     'hardware_config', 'ic', 'device_config', 'name')
        
        super().__init__(hardware_path, device_path,
                         module_config, name, qubits)
        self.qubits = qubits
        self.module_config = module_config
        self.components = []
        
        if self._find_pulsars():        
            self._pulsar_config()
            self._get_num_qubits()
        else:
            self.pulsars = self._create_dummy_pulsars()
            self._module_config_qubits()


        self.frequency_config = gen_config.freq_config(self.module_config)
        self._set_hardware_config(hardware_path)
        self._set_device_config(device_path)
        self._configure_ic()
        
    
    @timeis
    def _find_pulsars(self):
        instruments = Instrument._all_instruments
        return any(('qrm' in name or 'qcm' in name)for name in instruments)
    
    @timeis
    def _pulsar_config(self):
        config = {}
        instruments = Instrument._all_instruments.copy()
        cqubits = 0
        rqubits = 0
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
        
    @timeis      
    def _create_dummy_pulsars(self):
        if not self.qubits:
            raise Exception("No number of qubits provided or hardware connected.")
        pulsars_qcm = []
        pulsars_qrm = []

        for i in range(ceil(self.qubits / 2)):
            name = 'qcm{}'.format(i)
            pulsars_qcm.append(Pulsar(name, dummy_type=('Pulsar_QCM')))
            self.components.append(PulsarQCMComponent(pulsars_qcm[i]))
            name = 'qrm{}'.format(i)
            pulsars_qrm.append(Pulsar(name, dummy_type=('Pulsar_QRM')))
            self.components.append(PulsarQRMComponent(pulsars_qrm[i]))
        return [pulsars_qcm, pulsars_qrm]
    
    
    @timeis    
    def _set_hardware_config(self, hardware_path):
        if hardware_path:
            with open(hardware_path, 'r') as file:
                self.hardware_config = json.load(file)
        else:
            self.hardware_config = gen_config.generate_pulsar_config(self.module_config, self.frequency_config)
            with open("config/generated_hardware_config.json", 'w') as f:
                json.dump(self.hardware_config, f, indent=4, separators=(',', ': '))
                
    @timeis   
    def _configure_ic(self):
        """
        Includes all available hardware in the Instrument Coordinator.
        """

        self.ic = InstrumentCoordinator("IC")
        for component in self.components:
            self.ic.add_component(component)
        print(self.components)