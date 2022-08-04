#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 31 11:28:57 2022

@author: koen
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 28 18:10:08 2022

Example Qpack run
@author: koen
"""

from QPack_benchmark import QPack
from QPack_benchmark import qblox_hardware

from qcodes.instrument import Instrument
from pulsar_qrm.pulsar_qrm import pulsar_qrm
from pulsar_qcm.pulsar_qcm import pulsar_qcm


def mcp_benchmark(modules, size, shots):
    Instrument.close_all()

    if modules != 0:
        qrm_ip = '192.168.0.4'
        pulsar_r = pulsar_qrm("qrm0", qrm_ip)
        print(pulsar_r)

        qcm_ip = '192.168.0.3'
        pulsar_c = pulsar_qcm("qcm0", qcm_ip)
        print(pulsar_c)
        
        
    # important to assign add_instruments to a (unused) variable, to ensure the
    # reference stays alive!
    dummy_pulsars = qblox_hardware.add_instruments(size)
    qblox_backend = qblox_hardware.Backend(dummy_qubits=size)
    
    #MCP benchmark
    mcp = QPack.Benchmark('mcp', size, backend=qblox_backend)
    result = mcp.run(shots=shots)
    print(result)
        
"""
Instrument.close_all()
"""
"""
qrm_ip = '192.168.0.4'
pulsar_r = pulsar_qrm("qrm0", qrm_ip)
print(pulsar_r)

qcm_ip = '192.168.0.3'
pulsar_c = pulsar_qcm("qcm0", qcm_ip)
print(pulsar_c)
"""
"""
shots = 10000
size = 5

# important to assign add_instruments to a (unused) variable, to ensure the
# reference stays alive!
dummy_pulsars = qblox_hardware.add_instruments(size)
qblox_backend = qblox_hardware.Backend(dummy_qubits=size)

#MCP benchmark
mcp = QPack.Benchmark('mcp', size, backend=qblox_backend)
mcp.run(shots=shots)
"""
mcp_benchmark(0, 5, 10000)