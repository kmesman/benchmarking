#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 16 15:13:38 2022

@author: koen
"""


import qblox_instruments
from qblox_instruments import Cluster
from qblox_instruments import Pulsar
import quantify_scheduler
from quantify_scheduler import Schedule
from quantify_scheduler.gettables import ScheduleGettable
from quantify_scheduler.compilation import qcompile
from quantify_scheduler.device_under_test.quantum_device import QuantumDevice
from quantify_scheduler.device_under_test.transmon_element import BasicTransmonElement
from quantify_scheduler.instrument_coordinator import InstrumentCoordinator
from quantify_scheduler.instrument_coordinator.components.qblox import ClusterComponent, PulsarQRMComponent
from quantify_scheduler.schedules.timedomain_schedules import rabi_sched
from quantify_core.data.handling import set_datadir, snapshot, gen_tuid, get_datadir
from qcodes import Instrument

import pandas

from quantify_scheduler.gettables_profiled import ProfiledScheduleGettable
set_datadir("quantify-data")

Instrument.close_all()

#pnp...

IC = InstrumentCoordinator('IC')



#IC.add_component(PulsarQRMComponent(qrm0))
#conf_obj = HardwareConfig()
#hw_config = conf_obj.JSON
quantumdevice = QuantumDevice('TestDevice')
quantumdevice.instr_instrument_coordinator('IC')
quantumdevice.hardware_config(hw_config)

q1 = BasicTransmonElement('q1')
q1.clock_freqs.f01(6e9)
q1.clock_freqs.readout(5e9)
q1.rxy.amp180(0.03)
q1.measure.acq_delay(100e-9)
q1.measure.pulse_amp(0.05)
# repitions: 1024
quantumdevice.add_element(q1)
sched = rabi_sched
print(sched)
#sched.repetitions(5)

gettable = ProfiledScheduleGettable(quantumdevice, sched, {'pulse_amp': 0.05, 'pulse_duration': 1e-7, 'frequency': 6e9, 'qubit': 'q1'})

gettable.get()
gettable.close()
gettable.plot_profile()
log = gettable.log_profile()
print(log)
#assert len(log) == 6
#assert [len(x)>= 2 for x in log.values()]
