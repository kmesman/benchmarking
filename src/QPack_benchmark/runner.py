#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 24 16:55:12 2022

Run quantum algorithm using instrument coordinator
@author: koen
"""
import cast_to_QASM as qasm
import simulator_template as sim
import sim_device as sd
from quantify_scheduler.compilation import qcompile

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


    def run(self, sched, backend, qubits=5):
        """
        Runs the quantify schedule, optionally simulating the results if no
        quantum device is used.
        """
        # compile schedule
        
        comp_start = time.time()
        compiled_sched = qcompile(
            sched, backend.device_config, backend.hardware_config)
        comp_stop = time.time()
        sched_time = 0
        count = 0
        #print("new get time:",compiled_sched.get_schedule_duration())

        for item in compiled_sched["operation_dict"]:
            if self.log:
                print(item, compiled_sched["operation_dict"]
                      [item]["pulse_info"][0]["duration"])
            count+=1
            sched_time += compiled_sched["operation_dict"][item]["pulse_info"][0]["duration"]
        
        print("gates:", count)
        #artificial schedule times for paper
        #measure
        gates = count-qubits
        new_time = 500e-9
        #hadamard init
        gates -= 2*qubits
        new_time += 2*qubits*40e-9
        #beta param
        gates-= qubits
        new_time += qubits*40e-9
        # two qubit gates
        tq = round(gates/13)
        new_time += tq*(2*100e-9+11*40e-9)
        sched_time = new_time+200e-6
        #end
    
        shots = compiled_sched['repetitions']
        total_schedule = shots*sched_time
        print("schedule time : {}s".format(sched_time))
        print("total schedule time : {}s".format(total_schedule))


        if self.simulate_res:
            meas = self._simulated_run(sched, backend)
            #thr_meas = self.threshold_meas(meas, backend.mod_threshold["qrm0"])
            thr_meas = meas
        else:
            post = 0
            thr_meas = 0



        start_job_time = time.time()

            
        """
        module_sched = copy.deepcopy(compiled_sched["compiled_instructions"]['cluster0'])
        module_sched.pop("settings")
        """
        
        #def threaded_prepare(name, args):
        #    module = Instrument.find_instrument("ic_clone_module{}".format(module_name[15:]))
        #    module.prepare(args)
        
        """
        for module_name, args in module_sched.items():
           print(module_name[15:])
           module = Instrument.find_instrument("ic_clone_module{}".format(module_name[15:]))
           module.prepare(args)
        """
        """
        threads = list()
        for module_name, args in module_sched.items():
            x = threading.Thread(target=threaded_prepare, args=(module_name, args))
            threads.append(x)
            x.start()
        
        print("running threads")
        for index, thread in enumerate(threads):
            #print("Main    : before joining -prepare- thread {}.".format(index))
            thread.join()
            #print("Main    :  -prepare- thread {} done".format(index))
          """  
            
        
        
        backend.ic.prepare(compiled_sched) #!!!
        
        stop_prepare_time = time.time()
        print("prepare_time : {}s".format(stop_prepare_time-start_job_time))
        
        

        start_time, res = timer(backend.ic.start)
        print("started")
        wait_time, res = timer(backend.ic.wait_done)
        #print("start : {}s \nwaiting : {}s".format(start_time, wait_time))

        """
        time_dict = {"compile": comp_stop - comp_start,
                     "running": run_time,
                     "post_processing": post,
                     "simulation": sim_time,
                     "schedule": sched_time}
        """
        stop_job_time = time.time()
        job_time = stop_job_time - start_job_time
        #print("total job time : {}".format(job_time))
        time_dict = {"total job time":job_time, "schedule":total_schedule,
                     "running": start_time+wait_time, "compile": comp_stop-comp_start}
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

    
