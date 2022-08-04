#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 28 18:10:08 2022

cluster test run
@author: koen
"""

#import QPack
from QPack import Benchmark
import backend_classes as qblox_hardware
#qblox_hardware_cluster
from qcodes.instrument import Instrument
from qblox_instruments import Cluster, ClusterType
from MockLo import MockLocalOscillator



Instrument.close_all()


shots = 2000

# important to assign add_instruments to a (unused) variable, to ensure the
# reference stays alive!
#cluster = Cluster("cluster0", dummy_cfg={"1": ClusterType.CLUSTER_QCM, "5": ClusterType.CLUSTER_QRM_RF})
#cluster = Cluster("cluster0", '192.168.1.0')
#lo0 = MockLocalOscillator("lo0")
lo0 = MockLocalOscillator("lo0")

"""
cluster = Cluster("cluster0", dummy_cfg={"3": ClusterType.CLUSTER_QCM_RF, "5": ClusterType.CLUSTER_QRM, "8":ClusterType.CLUSTER_QCM,
                                        "16":ClusterType.CLUSTER_QRM_RF, "17":ClusterType.CLUSTER_QRM_RF})
        

qblox_backend = qblox_hardware.ClusterBackend(dummy_qubits=size, rf_qubits={"0":True, "1":True, "2":True, "3":True, "4":True},
                                       qblox_path="config/generated_hardware_config.json", device_path = "config/generated_device_config.json", name = "qblox_dummy_cluster")
#config/generated_cluster_config qblox_path="config/generated_cluster_config.json", device_path = "config/generated_device_config.json",
#config/generated_device_config
"""

#cluster = Cluster("cluster0", dummy_cfg={"3": ClusterType.CLUSTER_QCM_RF, "5": ClusterType.CLUSTER_QRM, "8":ClusterType.CLUSTER_QCM,
#                                        "16":ClusterType.CLUSTER_QRM_RF, "17":ClusterType.CLUSTER_QRM_RF})

cluster = Cluster("cluster0", dummy_cfg={
                    "2": ClusterType.CLUSTER_QCM,
                    "3":ClusterType.CLUSTER_QCM,
                    "4": ClusterType.CLUSTER_QCM,
                    "5":ClusterType.CLUSTER_QCM,
                    "6": ClusterType.CLUSTER_QRM,
                    "7":ClusterType.CLUSTER_QRM,
                    "8":ClusterType.CLUSTER_QRM,
                    "11":ClusterType.CLUSTER_QCM_RF,
                    "12":ClusterType.CLUSTER_QCM_RF,
                    "13":ClusterType.CLUSTER_QRM_RF,
                    "14":ClusterType.CLUSTER_QRM_RF,
                    "15":ClusterType.CLUSTER_QRM_RF
                    }
                  )
"""
cluster = Cluster("cluster0", '192.168.0.2')
"""
qblox_backend = qblox_hardware.ClusterBackend(module_config={"2":{"type":"QCM", "qubits":[0,1,2,3]},
                                                             "3":{"type":"QCM", "qubits":[4, 5, 6, 7]},
                                                             "4":{"type":"QCM", "qubits":[8,9,10,11]},
                                                             "5":{"type":"QCM", "qubits":[12, 13, 14, 15]},
                                                             "6":{"type":"QRM", "qubits":[0,1,2,3, 4, 5]},
                                                             "7":{"type":"QRM", "qubits":[6, 7, 8, 9, 10, 11]},
                                                             "8":{"type":"QRM", "qubits":[12, 13, 14, 15]},
                                                             #"9":{"type":"QRM", "qubits":[4, 5], "control":True},
                                                             #"10":{"type":"QRM", "qubits":[22, 23]},
                                                             "11":{"type":"QCM_RF", "qubits":[16, 17]},
                                                             "12":{"type":"QCM_RF", "qubits":[18, 19]},
                                                             "13":{"type":"QRM_RF", "qubits":[16, 17]},
                                                             "14":{"type":"QRM_RF", "qubits":[18, 19, 20, 21]},
                                                             "15":{"type":"QRM_RF", "qubits":[20, 21], "control":True}

                                                             },
                                              name = "qblox_dummy_cluster_tests")

"""
qblox_backend = qblox_hardware.Backend(dummy_qubits=size, rf_qubits={"0":True, "1":True, "2":True, "3":True, "4":True},
                                       qblox_path="cluster_test_config.json", device_path = "transmon_cluster_test.json", name = "qblox_cluster_test")

"""
"""

cluster = Cluster("cluster0", dummy_cfg={"3": ClusterType.CLUSTER_QCM, "5": ClusterType.CLUSTER_QRM, "8":ClusterType.CLUSTER_QCM,
                                        "16":ClusterType.CLUSTER_QRM}
                  )

qblox_backend = qblox_hardware.ClusterBackend(qubits=size, name = "qblox_dummy_cluster")
"""
#print(Instrument._all_instruments)
#dummy_pulsars = qblox_hardware.add_instruments(size)
#qblox_backend = qblox_hardware.Backend(dummy_qubits=size)
#mcp = QPack.Benchmark('mcp', size, backend=qblox_backend)

#MCP benchmark
size = 5
size_lim = 5
rep = 1
test = Benchmark('mcp', size_lim, backend=qblox_backend)
print(test.run(shots=shots))
"""
for i in range(size, size_lim+1):
    test = QPack.Benchmark('mcp', i, backend=qblox_backend)
    for x in range(rep):
        print(test.run(shots=shots))
"""

# Notes:
# configure network for ip: 192.168.1.200