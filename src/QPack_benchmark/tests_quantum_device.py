#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun  2 13:05:42 2022

@author: koen
"""

from quantify_scheduler.device_under_test.quantum_device import QuantumDevice
from quantify_scheduler.device_under_test.transmon_element import TransmonElement


q0 = TransmonElement('q0')
qd = QuantumDevice('transmon')
#qd.add_element(q0)