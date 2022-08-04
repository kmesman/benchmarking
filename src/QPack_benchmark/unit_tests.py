#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu May 19 11:20:09 2022

Unit tests
@author: koen
"""

import QPack
from qcodes.instrument import Instrument
from MockLo import MockLocalOscillator
from backend_classes import PulsarBackend, ClusterBackend
from qblox_instruments import Pulsar

import time


tick = time.time_ns()

Instrument.close_all()
lo0 = MockLocalOscillator("lo0")
# removing the mock lo shaves off 0.8 seconds

#module_config = {'3':{'qubits':[0,1], 'type':'QCM'}, '5':{'qubits':[2,3], 'type':'QCM_RF'},
#                 '8':{'qubits':[0,1], 'type':'QRM'}, '16':{'qubits':[2,3], 'type':'QRM_RF'}}
#module_config = {'3':{'qubits':[0,1]}, '5':{'qubits':[2,3]}, '8':{'qubits':[0,1]}, '16':{'qubits':[2,3]}}
#module_config = {'3':{'qubits':[0,1]},  '8':{'qubits':[0,1]}}
#module_config = {'5':{'qubits':[0,1]},  '16':{'qubits':[0,1]}}

#auto_backend = ClusterBackend(module_config=module_config, lo=False)



#auto_backend = ClusterBackend(module_config=module_config, ip='192.168.0.2', name='with_lo', lo=False)
auto_backend = ClusterBackend(ip='192.168.0.2')
#auto_backend = ClusterBackend(qubits=2)
tock = time.time_ns()


qtick = time.time_ns()
test = QPack.Benchmark('mcp', auto_backend.qubits, backend=auto_backend)
qtock = time.time_ns()

result = test.test_run(rep=3)

print(result)
print('setup time : {}'.format((tock-tick)*1e-9))
print('QPack time : {}'.format((qtock-qtick)*1e-9))

#result = test.run()
#print(result)
auto_backend.ic.log_profiles()
auto_backend.ic.plot_profile()

#print(auto_backend.get_profiles())

auto_backend.close()


"""
Instrument.close_all()

#lo0 = MockLocalOscillator("lo0")

tick = time.time()
qcm0 = Pulsar('qcm0', '192.168.0.3')
qrm1 = Pulsar('qrm0', '192.168.0.4')
tock = time.time()
print("pulsar setup", tock-tick)

tick = time.time()

pulsars_backend = PulsarBackend()
tock = time.time()

qtick = time.time()

test = QPack.Benchmark('mcp', pulsars_backend.qubits, backend=pulsars_backend)
qtock = time.time()



result = test.test_run()
print(result)
pulsars_backend.close()
print('setup time : {}'.format((tock-tick)))
print('QPack time : {}'.format((qtock-qtick)))
"""
