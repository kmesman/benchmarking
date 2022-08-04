#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 25 12:10:53 2022

Quantum algorithm coordinator
A QIL file to manage hardware and simulations
@author: koen
"""
import io
import pstats
import cProfile
from pstats import SortKey
from qblox_algorithm_benchmark import generate_graph as gg
from qblox_algorithm_benchmark import sim_device as sd
from qblox_algorithm_benchmark import simulator_template as sim
from qblox_algorithm_benchmark import cast_to_QASM as qasm
from qcodes.instrument import Instrument
from quantify_scheduler.instrument_coordinator.components.qblox import PulsarQCMComponent, PulsarQRMComponent
from quantify_scheduler.instrument_coordinator import InstrumentCoordinator
from quantify_scheduler.compilation import qcompile
#from qblox_transmon_demo.utilities.qblox_instruments import cluster, cluster_qcm, cluster_qrm
from quantify_core.utilities.examples_support import mk_iq_shots
from quantify_scheduler.backends.types.common import LocalOscillator
from quantify_scheduler.backends.qblox_backend import hardware_compile
from quantify_core.data.handling import set_datadir
from quantify_scheduler.compilation import add_pulse_information_transmon, determine_absolute_timing
import quantify_scheduler.schemas.examples as es
from pulsar_qcm.pulsar_qcm import pulsar_qcm_dummy, pulsar_qcm
from pulsar_qrm.pulsar_qrm import pulsar_qrm_dummy, pulsar_qrm
import re
import copy
import time
import math
import collections
import json
import inspect
from pathlib import Path
import numpy as np
import sys
# sys.path.append("/home/koen/qblox-transmon-demo")


def init_qubits(size):
    q = []
    for i in range(size):
        q.append('q' + str(i))
    return q


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


class algorithm_coordinator:
    """
    Operation flow of algorithm coordinator:
    init:
        initialize class variables
        set dummy ip --> add dummy ip to input ip
        determine if device is simulated
            --> configure simulated threshold
        start walltime timer
        add registered devices to IC
    run:
        compile schedule
        prepare IC
        run IC
        if simulated: run device simulation
        measure and post process
    """

    def __init__(self,
                 shots=100,
                 threshold=0,
                 quiet=False,
                 dummy_qubits=0,
                 datadir=Path.home() / "quantify-data",
                 device_path='transmon_dummy_config.json',
                 qblox_path='qblox_test_mapping.json',
                 simulated=True,
                 simulate_res=True,
                 plot=False):
        # general class variables
        self.init_time = time.time_ns()
        self.device_path = device_path
        self.qblox_path = qblox_path
        self.shots = shots
        self.simulate_res = simulate_res
        self.plot = plot
        if self.plot:
            import matplotlib.pyplot as plt
            plt.figure()

            #self.fig, self.ax = plt.subplots(1, 1, figsize=(15, 15/2/1.61))

        self.dummy_qubits = dummy_qubits
        self.ip_config = {'qcm': {}, 'qrm': {}}
        self._set_dummy_ip(dummy_qubits)
        self.log = not quiet
        self.accessable_qubits = 0
        self.simulated = simulated
        self.total_time = time.time_ns()
        set_datadir(datadir)
        self._runtime = 0
        self.runtime_total = 0
        self.hardware_runtime = {"initialization": 0, "compile": 0,
                                 "running": 0, "total": 0,
                                 "optimizer": 0, "post_processing": 0,
                                 "simulation": 0, "schedule": 0,
                                 "prepare": 0, "sched_run": 0}  # ns

        # set simulated threshold
        if threshold == 0:
            self.threshold = sd.auto_threshold(
                mk_iq_shots(num_shots=20), return_clusters=True)
        self.mod_threshold = {"qrm0": self.threshold}

        # add registered instruments
        # Instrument.close_all()
        self._remove_ic()
        #self.instruments = add_instruments(dummy_qubits)
        self._set_hardware()
        self._load_hw_mapping()
        self.hardware_runtime['initialization'] += time.time_ns() - \
            self.init_time

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

    def threshold_meas(self, sim_meas, thr):
        """
        Software solution to threshold the measurement points. In the future,
        this is to be replaced with a hardware intgrated function.
        """
        measures = []
        for mod in sim_meas:
            for seq in sim_meas[mod]:
                qubits = [sd.q_threshold(q, thr) for q in sim_meas[mod][seq]]
                qubits = [str(q) for q in qubits]
                measures.append(qubits)
        measures = np.array(measures)
        measures = np.transpose(measures)
        measures = ["".join(meas) for meas in measures]
        result = dict(collections.Counter(measures))
        return result

    def run(self, sched):
        """
        Runs the quantify schedule, optionally simulating the results if no
        quantum device is used.
        """
        # compile schedule
        comp_start = time.time_ns()
        compiled_sched = qcompile(
            sched, self.device_config, self.qblox_mapping)
        comp_stop = time.time_ns()
        sched_time = 0

        for item in compiled_sched["operation_dict"]:
            if self.log:
                print(item, compiled_sched["operation_dict"]
                      [item]["pulse_info"][0]["duration"])
            sched_time += compiled_sched["operation_dict"][item]["pulse_info"][0]["duration"]

        # for sched_item in compiled_sched.timing_constraints:
        #    print(sched_item)
        #    print(sched_item['abs_time'])
        #    sched_time += sched_item['abs_time']
        self.hardware_runtime['schedule'] += sched_time * 1e9 * self.shots
        self.hardware_runtime["compile"] += comp_stop - comp_start
        # simulation
        if self.simulate_res:
            tick = time.time_ns()
            meas = self._simulated_run(sched)
            tock = time.time_ns()
            sim_time = tock - tick

            tick = time.time_ns()
            thr_meas = self.threshold_meas(meas, self.mod_threshold["qrm0"])
            tock = time.time_ns()
            post = tock - tick
        else:
            post = 0
            thr_meas = 0

        iter_run_start = time.time_ns()

        # run schedule
        run_start = time.time_ns()

        self.ic.prepare(compiled_sched)

        prep_time = time.time_ns()
        self.hardware_runtime["prepare"] += prep_time - run_start

        self.hardware_runtime["sched_run"] += time.time_ns() - prep_time

        tick = time.time_ns()
        self.ic.start()
        self.ic.wait_done()
        tock = time.time_ns()
        run_time = tock - tick

        self.hardware_runtime['running'] += run_time

        self.hardware_runtime['post_processing'] += post
        iter_run_stop = time.time_ns()
        self._runtime += iter_run_stop - iter_run_start
        time_dict = {"compile": comp_stop - comp_start,
                     "running": run_time,
                     "post_processing": post,
                     "simulation": sim_time,
                     "schedule": sched_time}
        return {"counts": thr_meas, "time_per_step": time_dict}

    def _simulated_run(self, sched):
        """
        Simulates measurement points from a quantify schedule using a
        pre-defined quantum simulator.
        """
        # simulation of results
        sim_start = time.time_ns()
        qasm_str = qasm.cast_to_QASM(sched, self.accessable_qubits)
        sim_result = sim.simulate_results(qasm_str, shots=self.shots)
        sim_meas = sd.simulate_qi_res(sim_result)
        self.hardware_runtime['simulation'] += time.time_ns() - sim_start
        plot_index = "2{}".format(len(sim_meas))
        if self.plot:
            i = 0
            for mod in sim_meas:
                j = 0
                for seq in sim_meas[mod]:
                    j += 1
                    sub_index = int(plot_index + str(j + 2 * i))
                    plt.subplot(sub_index)
                    plt.plot(
                        np.real(
                            sim_meas[mod][seq]), np.imag(
                            sim_meas[mod][seq]), '.')
                i += 1
        # sim_meas = self._play_simulated_waveforms()
        return sim_meas

    def _play_simulated_waveforms(self, simulated_results):
        """
        Function to play simualted results as waveforms on a qblox device,
        in order to emulate a quantum device signal.
        """
        return 0

    def runtime(self):
        """
        Returns the time measurement dict.
        """
        print(self.hardware_runtime)
        return self.hardware_runtime

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

    def configuration(self):
        # define hardware name for Qpack
        class config:
            __init__():
                self.name = "qblox_module"
        config_obj = config()
        return config_obj

    def plot_results(self, old_dict={}):
        import matplotlib.pyplot as plt
        if not bool(old_dict):
            dct = self.hardware_runtime
        else:
            dct = old_dict
        dct.pop('total')
        dct["CPU"] = dct["optimizer"] + \
            dct["initialization"] + dct["post_processing"]
        dct.pop("optimizer")
        dct.pop("initialization")
        dct.pop("post_processing")
        print(dct)
        val = list(dct.values())
        key = list(dct.keys())
        x = range(len(val))
        fig = plt.figure(figsize=(8, 6))
        ax = fig.add_axes([0, 0, 1, 1])
        ax.bar(key, val)
        plt.xlabel('Computation step')
        plt.ylabel('Time [ns]')
        plt.title(
            "Benchmarking results L-VQE for {} qubits".format(self.accessable_qubits))
        plt.plot()
