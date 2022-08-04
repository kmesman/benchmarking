 #!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 28 18:10:08 2022

cluster test run using a QRM as control module
@author: koen
"""

import QPack
import backend_classes as qblox_hardware

from qcodes.instrument import Instrument
from qblox_instruments import Cluster, ClusterType

from MockLo import MockLocalOscillator
"""
Instrument.close_all()


shots = 1000
size = 2
rep = 1
# important to assign add_instruments to a (unused) variable, to ensure the
# reference stays alive!
#cluster = Cluster("cluster0", dummy_cfg={"1": ClusterType.CLUSTER_QCM, "5": ClusterType.CLUSTER_QRM_RF})
cluster = Cluster("cluster0", dummy_cfg={"3": ClusterType.CLUSTER_QCM_RF, "5": ClusterType.CLUSTER_QRM, "8":ClusterType.CLUSTER_QCM,
                                         "16":ClusterType.CLUSTER_QRM_RF, "17":ClusterType.CLUSTER_QRM_RF})

#cluster = Cluster("cluster0", '192.168.1.0')



print(Instrument._all_instruments)
#dummy_pulsars = qblox_hardware.add_instruments(size)
#qblox_backend = qblox_hardware.Backend(dummy_qubits=size, rf_qubits={"0":False, "1":False, "2":True, "3":True, "4":True},
#                                       explicit_config = {"control": {"3":[0,1], "8":[2,3], "16":[4]}, "readout": {"5":[2,3], "17":[0,1,4]}}
#                                       )
qblox_backend = qblox_hardware.Backend(dummy_qubits=size, rf_qubits={"0":False, "1":False, "2":True, "3":True, "4":True},
                                       qblox_path="cluster_test_config.json", name = "dummy_cluster"

                                       )
#MCP benchmark
test = QPack.Benchmark('mcp', size, backend=qblox_backend)
print(Instrument._all_instruments)
print(test.test_run(shots=shots, rep=rep))

# Notes:
# configure network for ip: 192.168.1.200
"""
Instrument.close_all()


#shots = 1000
size = 5    #!!!

# important to assign add_instruments to a (unused) variable, to ensure the
# reference stays alive!

#dummy_modules = qblox_hardware.add_instruments(size)
#cluster = Cluster("cluster0", '192.168.1.0')

lo0 = MockLocalOscillator("lo0")

#cluster = Cluster("cluster0", dummy_cfg={"2": ClusterType.CLUSTER_QCM, "6": ClusterType.CLUSTER_QRM, "3":ClusterType.CLUSTER_QCM,
#                                        "7":ClusterType.CLUSTER_QRM}
#                  )

#qblox_backend = qblox_hardware.ClusterBackend(qubits=size, name = "qblox_dummy_cluster")

cluster = Cluster("cluster0", '192.168.0.2')
qblox_backend = qblox_hardware.ClusterBackend(qubits=size,
                                              module_config={"2":{"type":"QCM", "qubits":[0,1,2,3]},
                                                             "3":{"type":"QCM", "qubits":[4, 5, 6, 7]},
                                                             #"4":{"type":"QCM", "qubits":[8,9,10,11]},
                                                             #"5":{"type":"QCM", "qubits":[12, 13, 14, 15]},
                                                             "6":{"type":"QRM", "qubits":[0,1,2,3, 4, 5]},
                                                             "7":{"type":"QRM", "qubits":[6, 7, 8, 9, 10, 11]},
                                                             #"8":{"type":"QRM", "qubits":[12, 13, 14, 15]}
                                                             },
                                              name = "qblox_cluster_dummy")


#qblox_backend = qblox_hardware.Backend(dummy_qubits=size, rf_qubits={"0":False, "1":False},
#                                       qblox_path="cluster_test_config.json", name = "dummy_cluster")


test = QPack.Benchmark('mcp', size, backend=qblox_backend)
#print(Instrument._all_instruments)
print(test.test_run(shots=2000, rep=10))
#MCP benchmark
#mcp = QPack.Benchmark('mcp', size, backend=qblox_backend)
#for i in range(2):
#    print(mcp.run(shots=20))

