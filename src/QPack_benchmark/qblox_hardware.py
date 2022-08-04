#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 24 16:40:44 2022

Configure hardware
@author: koen
"""
from QPack_benchmark import runner
from QPack_benchmark import sim_device as sd
from QPack_benchmark import generate_graph as gg

from qcodes.instrument import Instrument
from pulsar_qcm.pulsar_qcm import pulsar_qcm_dummy, pulsar_qcm
from pulsar_qrm.pulsar_qrm import pulsar_qrm_dummy, pulsar_qrm
from quantify_core.data.handling import set_datadir
from quantify_core.utilities.examples_support import mk_iq_shots
from quantify_scheduler.instrument_coordinator import InstrumentCoordinator
from quantify_scheduler.instrument_coordinator.components.qblox import PulsarQCMComponent, PulsarQRMComponent
import quantify_scheduler.schemas.examples as es

import re
from pathlib import Path
import math
import inspect
import json
import copy


# TODO: inherit IC class

def add_instruments(num):
    # check for existing (physical) devices!
    instr_dict = Instrument._all_instruments.copy()
    tmp_c = []
    tmp_r = []
    for i in range(math.ceil(num / 2)):
        name = 'qcm{}'.format(i)
        if name not in instr_dict.keys():
            tmp_c.append(pulsar_qcm_dummy(name))

        name = 'qrm{}'.format(i)
        if name not in instr_dict.keys():
            tmp_r.append(pulsar_qrm_dummy(name))

    print("Current registered instruments are: {}"
          .format(list(Instrument._all_instruments.keys())))
    return [tmp_c, tmp_r]

class Backend:
    def __init__(self, dummy_qubits=0,
    datadir=Path.home() / "quantify-data",
    device_path='transmon_dummy_config.json',
    qblox_path='qblox_test_mapping.json',
    threshold=0):
        
        self.device_path = device_path
        self.qblox_path = qblox_path
        self.dummy_qubits = dummy_qubits
        self.ip_config = {'qcm': {}, 'qrm': {}}
        self._set_dummy_ip(dummy_qubits)
        self.accessable_qubits = 0
        set_datadir(datadir)
        # set simulated threshold
        if threshold == 0:
            self.threshold = sd.auto_threshold(
                mk_iq_shots(num_shots=20), return_clusters=True)
        self.mod_threshold = {"qrm0": self.threshold}

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

    def _set_dummy_ip(self, qubits):
        for q in range(0, math.ceil(qubits / 2)):
            self.ip_config["qcm"]["qcm{}".format(q)] = 0
            self.ip_config["qrm"]["qrm{}".format(q)] = 0
        self.simulated = True

    def _generate_dummy_qblox_config(self):
        """
        Generate a dummy config file for qblox hardware.
        """
        esp = inspect.getfile(es)
        cfg_f = Path(esp).parent / 'qblox_test_mapping.json'

        with open(cfg_f, 'r') as f:
            base = json.load(f)
        # remove unused modules
        base.pop('lo0')
        base.pop('lo1')
        base.pop('cluster0')
        base.pop('qcm_rf0')
        base.pop('qrm_rf0')
        base.pop('qrm1')
        base.pop('qrm_rf1')
        qcm_base = base['qcm0']
        qrm_base = base['qrm0']
        qrm_base['ref'] = 'internal'
        # add sequencer
        seq0 = copy.deepcopy(qcm_base["complex_output_0"])
        qcm_base["complex_output_1"] = seq0
        qcm_base["complex_output_1"]['seq1'] = qcm_base["complex_output_1"].pop(
            'seq0')

        seq0 = copy.deepcopy(qrm_base["complex_output_0"]['seq0'])
        qrm_base["complex_output_0"]['seq1'] = seq0

        i = 0
        for module in self.ip_config['qcm']:
            base[module] = copy.deepcopy(qcm_base)
            base[module]["complex_output_0"]["seq0"]["port"] = "q{}:mw".format(
                i)
            base[module]["complex_output_0"]["seq0"]["clock"] = "q{}.01".format(
                i)
            base[module]["complex_output_0"]["seq0"]["interm_freq"] = 50e6
            out_cpy = copy.deepcopy(base[module]['complex_output_0'])
            out_cpy.pop('seq0')
            base[module]['real_output_0'] = out_cpy

            base[module]['real_output_0']['seq2'] = copy.deepcopy(
                base[module]['complex_output_0']['seq0'])

            base[module]['real_output_0']['seq2']['port'] = 'q{}:fl'.format(i)
            base[module]['real_output_0']['seq2']['clock'] = 'cl0.baseband'
            base[module]['real_output_0']['seq2']['interm_freq'] = 0
            i += 1
            base[module]["complex_output_1"]["seq1"]["port"] = "q{}:mw".format(
                i)
            base[module]["complex_output_1"]["seq1"]["clock"] = "q{}.01".format(
                i)
            base[module]["complex_output_1"]["seq1"]["interm_freq"] = 50e6

            tmp_cpy = copy.deepcopy(base[module]['real_output_0'])
            tmp_cpy.pop('seq2')
            base[module]['real_output_1'] = tmp_cpy
            base[module]['real_output_1']['seq3'] = copy.deepcopy(
                base[module]['complex_output_0']['seq0'])
            base[module]['real_output_1']['seq3']['port'] = 'q{}:fl'.format(i)
            base[module]['real_output_1']['seq3']['clock'] = 'cl0.baseband'
            base[module]['real_output_1']['seq3']['interm_freq'] = 0

            i += 1
        i = 0
        for module in self.ip_config['qrm']:
            base[module] = copy.deepcopy(qrm_base)
            base[module]["complex_output_0"]["seq0"]["port"] = "q{}:res".format(
                i)
            base[module]["complex_output_0"]["seq0"]["clock"] = "q{}.ro".format(
                i)
            base[module]["complex_output_0"]["seq0"]["interm_freq"] = 50e6
            i += 1
            base[module]["complex_output_0"]["seq1"]["port"] = "q{}:res".format(
                i)
            base[module]["complex_output_0"]["seq1"]["clock"] = "q{}.ro".format(
                i)
            base[module]["complex_output_0"]["seq1"]["interm_freq"] = 50e6

            i += 1
        return base

    def _generate_dummy_device_map(self):
        """
        Generate a dummy config file for a transmon device.
        """
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

                mapping['edges']['q{}-q{}'.format(e[1], e[0])] = sample_con
                mapping['edges']['q{}-q{}'.format(
                    e[1], e[0])]['resource_map']['q{}'.format(e[1])] = 'q{}:fl'.format(e[1])
                mapping['edges']['q{}-q{}'.format(
                    e[1], e[0])]['resource_map']['q{}'.format(e[0])] = 'q{}:fl'.format(e[0])
        return mapping

    def _set_hardware(self):
        """
        Includes all available hardware in the Instrument Coordinator.
        """
        self.ic = InstrumentCoordinator("IC")
        instr_dict = Instrument._all_instruments.copy()
        qcm_instr = []
        qrm_instr = []
        qcm_pulsar_comp = []
        qrm_pulsar_comp = []
        i = 0
        for name in instr_dict.keys():
            if re.search("qcm.*", name):
                self.accessable_qubits += 2
                qcm_instr.append(Instrument.find_instrument(name))
                qcm_pulsar_comp.append(PulsarQCMComponent(qcm_instr[i]))
                self.ic.add_component(qcm_pulsar_comp[i])
                i += 1
            if re.search("qrm.*", name):
                self.ic.add_component(
                    PulsarQRMComponent(
                        Instrument.find_instrument(name)))

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
        """
        if self.simulated:
            dummy_mapping = self._generate_dummy_qblox_config()
            self.qblox_mapping = dummy_mapping
            dummy_device_map = self._generate_dummy_device_map()
            self.device_config = dummy_device_map
        else:
            self.qblox_mapping = self._load_config_file(self.qblox_path)
            self.device_config = self._load_config_file(self.device_path)

    def _load_device_config(self, f):
        cfg_f = Path().parent / f
        with open(cfg_f, 'r') as f:
            config_var = json.load(f)
        return config_var
    
    def configuration(self):
        # define hardware name for Qpack
        class config:
            def __init__(self):
                self.backend_name = "qblox_module"
        config_obj = config()
        return config_obj
    
    
    def run(self, sched, backend, shots=100):
        job = runner.algorithm_runner(shots=shots)
        return job.run(sched, backend)
        
        
    
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
    
    
