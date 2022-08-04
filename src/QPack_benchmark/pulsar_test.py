#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun  2 15:07:30 2022

@author: koen
"""

from qblox_instruments import Pulsar
from qcodes.instrument import Instrument

Instrument.close_all()
#p0 = Pulsar('qcm0', '')
p1 = Pulsar('qrm0', '192.168.0.4')
print(Instrument._all_instruments)
for instr in Instrument._all_instruments:
    print(instr)