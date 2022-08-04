#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 28 18:10:08 2022

Example Qpack run
@author: koen
"""

import QPack
import qblox_hardware

from qcodes.instrument import Instrument
from pulsar_qrm.pulsar_qrm import pulsar_qrm
from pulsar_qcm.pulsar_qcm import pulsar_qcm


Instrument.close_all()

qrm_ip = '192.168.0.4'
pulsar_r = pulsar_qrm("qrm0", qrm_ip)
print(pulsar_r)

qcm_ip = '192.168.0.3'
pulsar_c = pulsar_qcm("qcm0", qcm_ip)
print(pulsar_c)


shots = 10000
size = 5

# important to assign add_instruments to a (unused) variable, to ensure the
# reference stays alive!
dummy_pulsars = qblox_hardware.add_instruments(size)
qblox_backend = qblox_hardware.Backend(dummy_qubits=size)

#MCP benchmark
mcp = QPack.Benchmark('mcp', size, backend=qblox_backend)
mcp.run(shots=shots)
