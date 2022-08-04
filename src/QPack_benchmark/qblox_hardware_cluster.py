#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 4 2022

Configure hardware cluster
@author: koen
"""
import runner
import sim_device as sd

from qcodes.instrument import Instrument
#from pulsar_qcm.pulsar_qcm import pulsar_qcm_dummy, pulsar_qcm
#from pulsar_qrm.pulsar_qrm import pulsar_qrm_dummy, pulsar_qrm
from quantify_core.data.handling import set_datadir
from quantify_core.utilities.examples_support import mk_iq_shots
from instrument_coordinator_threaded import InstrumentCoordinator
#from quantify_scheduler.instrument_coordinator.components.qblox import PulsarQCMComponent, PulsarQRMComponent, _QCMComponent, _QRMComponent
import quantify_scheduler.schemas.examples as es
from qblox_instruments import Cluster, ClusterType

from quantify_scheduler.instrument_coordinator.components.qblox import ClusterComponent, QCMComponent, QRMComponent, QRMRFComponent, QCMRFComponent

import time
import re
from pathlib import Path
import math
import inspect
import json
import copy
import generate_graph as gg


def add_instruments(num):
    # depricated
    instr_dict = Instrument._all_instruments.copy()
    tmp_c = []
    tmp_r = []
    instr_ref = []
    dummy_cfg_dct = {}
    for i in range(math.ceil(num / 2)):
        dummy_cfg_dct["{}".format(i+1)] = ClusterType.CLUSTER_QCM
        latest_index = i    
    for i in range(1, math.ceil(num / 6)+1):
        dummy_cfg_dct["{}".format(i+latest_index+1)] = ClusterType.CLUSTER_QRM
    if 'cluster0' not in instr_dict.keys():
        cl  = Cluster("cluster0", dummy_cfg=dummy_cfg_dct)
        instr_ref.append(cl)
    
    print("Current registered instruments are: {}"
          .format(list(Instrument._all_instruments.keys())))
    instr_ref.append([tmp_c, tmp_r])
    return instr_ref



class Backend:
    def __init__(self, dummy_qubits=0,
    datadir=Path.home() / "quantify-data",
    device_path='',
    qblox_path='',
    threshold=0, control_readout = None,
    rf_qubits={}, explicit_config = {}, name = ""
    ):
        self.rf_qubits = rf_qubits
        self.name = name
        self.explicit_config = explicit_config
        self.device_path = device_path
        self.qblox_path = qblox_path
        self.dummy_qubits = dummy_qubits
        instruments = Instrument._all_instruments
        
        # Add dummy devices if no modules
        self.config_cluster(dummy_qubits)
        self.qubits = dummy_qubits
        set_datadir(datadir)
        # set simulated threshold
        if threshold == 0:
            self.threshold = sd.auto_threshold(
                mk_iq_shots(num_shots=20), return_clusters=True)
        self.mod_threshold = {"qrm0": self.threshold}
        
        self.set_control_readout(control_readout)
        
        self._remove_ic()
        self._set_hardware()
        self._load_hw_mapping()

    def _remove_ic(self):
        # remove remaining IC dummy instruments
        instr_dict = Instrument._all_instruments
        num = len(instr_dict)
        if Instrument.exist("IC"):
            Instrument.remove_instance(Instrument.find_instrument("IC"))
        for i in range(math.ceil(num / 2)):
            name = 'ic_qcm{}'.format(i)
            if Instrument.exist(name):
                Instrument.remove_instance(Instrument.find_instrument(name))
            name = 'ic_qrm{}'.format(i)
            if Instrument.exist(name):
                Instrument.remove_instance(Instrument.find_instrument(name))


    def add_instruments(self, num):
        # check for existing (physical) devices!
        instr_dict = Instrument._all_instruments.copy()
        tmp_c = []
        tmp_r = []
        dummy_cfg_dct = {}
        for i in range(math.ceil(num / 2)):
            dummy_cfg_dct["{}".format(i+1)] = ClusterType.CLUSTER_QCM
            latest_index = i
        for i in range(1, math.ceil(num / 6)+1):
            dummy_cfg_dct["{}".format(i+latest_index+1)] = ClusterType.CLUSTER_QRM
        if 'cluster0' not in instr_dict.keys():
            cl  = Cluster("cluster0", dummy_cfg=dummy_cfg_dct)
        
        print("Current registered instruments are: {}"
              .format(list(Instrument._all_instruments.keys())))
        return [cl, tmp_c, tmp_r]

    def config_cluster(self, q):
        instruments = Instrument._all_instruments
        if not any('cluster' in name for name in instruments):
            self.add_instruments(q)


    def _set_module_index(self, cluster_comp):  ##needs fix for multiple clusters
        modules = cluster_comp._cluster_modules
        self.ip_config = {'cluster':{'qcm':{}, 'qrm':{}, 'qcmrf':{}, 'qrmrf':{}}}
        for mod in modules:
            slot_nr = mod.replace('cluster0_module','')
            if type(modules[mod]) == QCMComponent:
                self.ip_config['cluster']['qcm']['qcm{}'.format(slot_nr)] = slot_nr
            if type(modules[mod]) == QCMRFComponent:
                self.ip_config['cluster']['qcmrf']['qcmrf{}'.format(slot_nr)] = slot_nr
            if type(modules[mod]) == QRMComponent:
                self.ip_config['cluster']['qrm']['qrm{}'.format(slot_nr)] = slot_nr
            if type(modules[mod]) == QRMRFComponent:
                self.ip_config['cluster']['qrmrf']['qrmrf{}'.format(slot_nr)] = slot_nr
        self.simulated = True
    
    
        """
        for q in range(1, math.ceil(qubits/2)+1):
            self.ip_config['cluster']["qcm"]["qcm{}".format(q)] = 0
            latest_index = q    

        for q in range(1, math.ceil(qubits/6)+1):
            self.ip_config['cluster']["qrm"]["qrm{}".format(q+latest_index)] = 0
        self.simulated = True
        """

    def set_control_readout(self, slot):
        self.control_readout = []
        self.control_readout.append(slot)


    def _generate_dummy_qblox_config(self):
        """
        Generate a dummy config file for qblox hardware.
        """
        esp = inspect.getfile(es)
        # !!!
        #cfg_f = Path(esp).parent / 'qblox_test_mapping.json'
        
        # exception for custom config files
        if self.qblox_path != '':
            with open(self.qblox_path, 'r') as f:
                base = json.load(f)
                return base
        
        cfg_f = Path(esp).parent / self.qblox_path

        with open(cfg_f, 'r') as f:
            base = json.load(f)
        qcm_base = copy.deepcopy(base['qcm0'])
        base.pop('lo0')
        base.pop('lo1')
        base.pop('qcm_rf0')
        base.pop('qcm0')
        base.pop('qrm1')
        base.pop('qrm_rf1')
        qrm_base = copy.deepcopy(base['qrm0'])
        base['cluster0'].pop('cluster0_module2')
        base['cluster0'].pop('cluster0_module3')
        #cluster_qcm = copy.deepcopy(base['cluster0']['cluster0_qcm0'])
        
        ##cluster = Instrument.find_instrument('cluster0')
        ci = 0  #control index
        for qcm_mod in self.ip_config['cluster']['qcm']:
            mod_int = qcm_mod.replace('qcm','')
            base['cluster0']['cluster0_module{}'.format(mod_int)] = copy.deepcopy(qcm_base)
            mod_base = base['cluster0']['cluster0_module{}'.format(mod_int)]
            mod_base['instrument_type'] = 'QCM'

            mod_base["complex_output_0"].pop('lo_name')

            mod_base["complex_output_0"]["seq0"]["port"] = "q{}:mw".format(
                ci)
            mod_base["complex_output_0"]["seq0"]["clock"] = "q{}.01".format(
                ci)
            mod_base["complex_output_0"]["seq0"]["interm_freq"] = 50e6
            out_cpy = copy.deepcopy(mod_base['complex_output_0'])
            out_cpy.pop('seq0')
            mod_base['real_output_0'] = out_cpy

            mod_base['real_output_0']['seq2'] = copy.deepcopy(
                mod_base['complex_output_0']['seq0'])

            mod_base['real_output_0']['seq2']['port'] = 'q{}:fl'.format(ci)
            mod_base['real_output_0']['seq2']['clock'] = 'cl0.baseband'
            mod_base['real_output_0']['seq2']['interm_freq'] = 0
            ci += 1
            mod_base["complex_output_1"].pop('lo_name')

            mod_base["complex_output_1"]["seq1"]["port"] = "q{}:mw".format(
                ci)
            mod_base["complex_output_1"]["seq1"]["clock"] = "q{}.01".format(
                ci)
            mod_base["complex_output_1"]["seq1"]["interm_freq"] = 50e6

            tmp_cpy = copy.deepcopy(mod_base['real_output_0'])
            tmp_cpy.pop('seq2')
            mod_base['real_output_1'] = tmp_cpy
            mod_base['real_output_1']['seq3'] = copy.deepcopy(
                mod_base['complex_output_0']['seq0'])
            mod_base['real_output_1']['seq3']['port'] = 'q{}:fl'.format(ci)
            mod_base['real_output_1']['seq3']['clock'] = 'cl0.baseband'
            mod_base['real_output_1']['seq3']['interm_freq'] = 0
            ci+=1
    
    
    
        # format qrm properly for number of required sequencers
        index = 0
        for qrm_mod in self.ip_config['cluster']['qrm']:
            mod_int = qrm_mod.replace('qrm','')
            base['cluster0']['cluster0_module{}'.format(mod_int)] = copy.deepcopy(qrm_base)
            mod_base = base['cluster0']['cluster0_module{}'.format(mod_int)]
            mod_base['instrument_type'] = 'QRM'
            # create config for control QRM
            if mod_int in self.control_readout:
                mod_base["complex_output_0"]["seq0"] = copy.deepcopy(mod_base["complex_output_0"]["seq0"])
                mod_base["complex_output_0"]["seq0"]['port'] = 'q{}:mw'.format(ci)
                mod_base["complex_output_0"]["seq0"]['clock'] = 'q{}.01'.format(ci)
            
            else:
                for ri in range(index*6, (index+1)*6):
                    if ri != 0:
                        mod_base["complex_output_0"]["seq{}".format(ri)] = copy.deepcopy(mod_base["complex_output_0"]["seq0"])
                    mod_base["complex_output_0"]["seq{}".format(ri)]['port'] = 'q{}:res'.format(ri)
                    mod_base["complex_output_0"]["seq{}".format(ri)]['clock'] = 'q{}.ro'.format(ri)
                    self.rf_qubits['{}'.format(ri)] = False

                index+=1
        base.pop('qrm0')
        
        #index = 0
        qrmrf_base = copy.deepcopy(base['qrm_rf0'])
        for qrmrf_mod in self.ip_config['cluster']['qrmrf']:
            mod_int = qrmrf_mod.replace('qrmrf','')
            
            base['cluster0']['cluster0_module{}'.format(mod_int)] = copy.deepcopy(qrmrf_base)
            mod_base = base['cluster0']['cluster0_module{}'.format(mod_int)]
            mod_base['instrument_type'] = 'QRM_RF'
            mod_base["complex_output_0"]['lo_freq'] = 3e9

            for i in range(index*6, (index+1)+6):
                if i != 0:
                    mod_base["complex_output_0"]["seq{}".format(i)] = copy.deepcopy(mod_base["complex_output_0"]["seq0"])
                    

                mod_base["complex_output_0"]["seq{}".format(i)]['port'] = 'q{}:res'.format(ri)
                mod_base["complex_output_0"]["seq{}".format(i)]['clock'] = 'q{}.ro'.format(ri)
                mod_base["complex_output_0"]["seq{}".format(i)]['interm_freq'] = None
                self.rf_qubits['{}'.format(ri)] = True

            index+=1
            
        base.pop('qrm_rf0')
        with open("generated_qblox_config.json", 'w') as outfile:
            json.dump(base, outfile)

        return base

    def _generate_dummy_device_map(self):
        """
        Generate a dummy config file for a transmon device.
        """
        # exception for custom config files
        if self.device_path != '':
            with open(self.device_path, 'r') as f:
                base = json.load(f)
                return base
        
        esp = inspect.getfile(es)
        cfg_f = Path(esp).parent / 'transmon_test_config.json'
        with open(cfg_f, 'r') as f:
            mapping = json.load(f)
        base = mapping['qubits']
        base['q0']
        qubit = base['q0']
        for i in range(self.dummy_qubits):
            base['q{}'.format(i)] = copy.deepcopy(qubit)
            base['q{}'.format(i)]['params']['mw_freq'] = 50000000
            if self.rf_qubits["{}".format(i)]:
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
            [v, edges] = gg.fully_connected(self.dummy_qubits)
            for e in edges:
                mapping['edges']['q{}-q{}'.format(e[0], e[1])] = sample_con
                mapping['edges']['q{}-q{}'.format(
                    e[0], e[1])]['resource_map']['q{}'.format(e[0])] = 'q{}:fl'.format(e[0])
                mapping['edges']['q{}-q{}'.format(
                    e[0], e[1])]['resource_map']['q{}'.format(e[1])] = 'q{}:fl'.format(e[1])
                mapping['edges']['q{}-q{}'.format(
                    e[0], e[1])]['params']['flux_amp_control'] = 0.1
                
                mapping['edges']['q{}-q{}'.format(e[1], e[0])] = sample_con
                mapping['edges']['q{}-q{}'.format(
                    e[1], e[0])]['resource_map']['q{}'.format(e[1])] = 'q{}:fl'.format(e[1])
                mapping['edges']['q{}-q{}'.format(
                    e[1], e[0])]['resource_map']['q{}'.format(e[0])] = 'q{}:fl'.format(e[0])
                mapping['edges']['q{}-q{}'.format(
                    e[1], e[0])]['params']['flux_amp_control'] = 0.1
                
                
        return mapping


    def _set_hardware(self):
        """
        Includes all available hardware in the Instrument Coordinator.
        """
        self.ic = InstrumentCoordinator("IC")
        instr_dict = Instrument._all_instruments.copy()
        copy_cluster_modules = {}
        qcm_instr = []
        qrm_instr = []
        qcm_index = 0
        qrm_index = 0
        for name in instr_dict.keys():
            if re.search("cluster.*", name):
                cluster = Instrument.find_instrument(name)
                cluster_comp = ClusterComponent(cluster)
                # go through existing modules, copy instantiated cluster modules to new ref and name
                # does this copy the port?
                # save for later usage
                break
        
        self.ic.add_component(cluster_comp)
        self._set_module_index(cluster_comp)
        
        #Alternatives:
                # Multiple cluster instances, only ref 1 module
                # Manually assign different port?
        """
        #manual test
        modules = ["3", "5", "8", "16", "17"]
        #QCM_RF, slot 3
        clone_cluster = {}
        for slot in modules:
            clone_cluster[slot] = Cluster("cluster{}".format(slot), '192.168.0.2')

        
        slot = 3
        copy_ref = clone_cluster[str(slot)].modules[slot-1]
        copy_ref._name = 'clone_module{}'.format(slot)
        tst_module_ref = _QCMRFComponent(copy_ref)

        #QRM, slot 5
        slot = 5
        copy_ref = clone_cluster[str(slot)].modules[slot-1]
        copy_ref._name = 'clone_module{}'.format(slot)
        tst_module_ref = _QRMComponent(copy_ref)
        
        #QCM, slot 8
        slot = 8
        copy_ref = clone_cluster[str(slot)].modules[slot-1]
        copy_ref._name = 'clone_module{}'.format(slot)
        tst_module_ref = _QCMComponent(copy_ref)
        
        #QRMRF, slot 16&17
        slot = 16
        copy_ref = clone_cluster[str(slot)].modules[slot-1]
        copy_ref._name = 'clone_module{}'.format(slot)
        tst_module_ref = _QRMRFComponent(copy_ref)
        
        slot = 17
        copy_ref = clone_cluster[str(slot)].modules[slot-1]
        copy_ref._name = 'clone_module{}'.format(slot)
        tst_module_ref = _QRMRFComponent(copy_ref)
        """
        
        """
        for mod in self.ip_config:
            #this sorta works
            copy_ref = cluster.modules[int(self.ip_config[mod])]
            copy_ref._name = 'tst{}'.format(self.ip_config[mod])
            # modules need to be copied before changing the name,
            # or first allocate all, then change name and assign (?)
            
            #change component types
            # test with manual
            tst_module_ref = _QCMRFComponent(copy_ref)
            print(tst_module_ref)
            print(cluster.modules[2])
        """
        
        """
        for name in instr_dict.keys():
            if re.search("qcm.*", name):
                self.accessable_qubits += 2
                qcm_instr.append(Instrument.find_instrument(name))
                cluster_comp.add_modules(qcm_instr[qcm_index])
                qcm_index += 1
            if re.search("qrm.*", name):
                qrm_instr.append(Instrument.find_instrument(name))
                ic_cluster.add_modules(qrm_instr[qrm_index])
                qrm_index += 1
        """
    
    def generate_config_explicit(self):
        for module in self.explicit_config["control"]:
            print(module)
            
        
    def _load_config_file(self, file_path):
        esp = inspect.getfile(es)
        cfg_f = Path(esp).parent / file_path
        with open(cfg_f, 'r') as f:
            config_var = json.load(f)
        return config_var

    def _load_hw_mapping(self):
        """
        Load the configurations for device and hardware. The config files are
        automatically generated for simulated devices.
        
        #needs cleanup
        """
        if self.simulated:
            print('simulate quantum device')
            if any in self.explicit_config:
                dummy_mapping = self.generate_config_explicit(self.explicit_config)
            else:
                dummy_mapping = self._generate_dummy_qblox_config()
            
            self.hardware_config = dummy_mapping
            dummy_device_map = self._generate_dummy_device_map()
            self.device_config = dummy_device_map
        else:
            self.hardware_config = self._load_config_file(self.qblox_path)
            self.device_config = self._load_config_file(self.device_path)

    def _load_device_config(self, f):
        cfg_f = Path().parent / f
        with open(cfg_f, 'r') as f:
            config_var = json.load(f)
        return config_var
    
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
    
    
    def run(self, sched, shots=100):
        job = runner.algorithm_runner(shots=shots)
        return job.run(sched, self)
        
        
    
    def close(self):
        """
        Closes the Instrument coordinator and stops time measurement.
        """
        self.ic.close()
        self.total_time = time.time_ns() - self.init_time
        self.hardware_runtime["total"] = self.total_time

        hw_times = self.hardware_runtime.copy()
        hw_times.pop('total')
        total = 0
        self.hardware_runtime['other'] = 0
        for k in hw_times:
            total += hw_times[k]
        self.hardware_runtime['other'] = self.total_time - total
    
    