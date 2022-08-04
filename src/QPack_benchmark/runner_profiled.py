#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 24 16:55:12 2022

Run quantum algorithm using profiler
@author: koen
"""
import cast_to_QASM as qasm
import simulator_template as sim
import sim_device as sd
from quantify_scheduler.compilation import qcompile
from quantify_scheduler.gettables_profiled import ProfiledScheduleGettable
from quantify_scheduler.device_under_test.quantum_device import QuantumDevice

from qcodes.instrument import Instrument

import time
import numpy as np
import collections
import copy
import threading



def timer(func, *args):
    start = time.time()
    res = func(*args)
    stop = time.time()
    runtime = stop-start
    return runtime, res

class algorithm_runner:
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
                 simulated=True,
                 simulate_res=True
):
        # general class variables
        self.shots = shots
        self.log = False #!!!
        self.simulate_res = simulate_res
        self.accessable_qubits = 0
        self.simulated = simulated
        self.hardware_runtime = {"initialization": 0, "compile": 0,
                                 "running": 0, "total": 0,
                                 "optimizer": 0, "post_processing": 0,
                                 "simulation": 0, "schedule": 0,
                                 "prepare": 0, "sched_run": 0}  # ns


    def run(self, sched, backend, args=None, qubits=5):
        """
        Runs the quantify schedule, optionally simulating the results if no
        quantum device is used.
        """
        # compile schedule
        quantumdevice = backend.device_obj
        quantumdevice.hardware_config(backend.hardware_config)

        if self.simulate_res:
            meas = self._simulated_run(sched(**args), backend)
            #thr_meas = self.threshold_meas(meas, backend.mod_threshold["qrm0"])
            thr_meas = meas
        else:
            thr_meas = 0

        start_job_time = time.time()
      
        gettable = ProfiledScheduleGettable(quantumdevice, sched, args)

        gettable.get()
        gettable.close()
        
        stop_job_time = time.time()
        job_time = stop_job_time - start_job_time
        time_dict = gettable.log_profile(path=False)

        
        
        
        time_dict["total job time"] = job_time
        #total job time does not include compile
        return {"counts": thr_meas, "time_per_step": time_dict}

    def threshold_meas(self, sim_meas, thr):
        """
        Software solution to threshold the measurement points. In the future,
        this is to be replaced with a hardware intgrated function.
        """
        measures = []
        qubit = []
        for mod in sim_meas:
            for seq in sim_meas[mod]:
                
                thr_meas = [sd.q_threshold(shot, thr) for shot in sim_meas[mod][seq]]
                str_meas = [str(shot) for shot in thr_meas]
                if str_meas:
                    qubit.append(str_meas)
        num_shots = len(qubit[0])
        shots=[]
        for i in range(num_shots):
            shot = []
            for q in qubit:
                shot.append(q[i])
            shots.append(shot)
        #measures = np.array(measures)
        #measures = np.transpose(measures)
        measures = ["".join(meas) for meas in shots]
        result = dict(collections.Counter(measures))
        return result


    def _simulated_run(self, sched, backend):
        """
        Simulates measurement points from a quantify schedule using a
        pre-defined quantum simulator.
        """
        # simulation of results
        print(sched)
        sim_start = time.time_ns()
        qasm_str = qasm.cast_to_QASM(sched, backend.qubits)
        sim_result = sim.simulate_results(qasm_str, shots=self.shots)
        sim_meas = sd.simulate_qi_res(sim_result)
        self.hardware_runtime['simulation'] += time.time_ns() - sim_start
        """
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
        """
        return sim_result    #!!!

    def _play_simulated_waveforms(self, simulated_results):
        """
        Function to play simualted results as waveforms on a qblox device,
        in order to emulate a quantum device signal.
        """
        return 0

    
