#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 14 11:04:42 2022

cast quantify schedule to QASM
@author: koen
"""
import re
from math import radians

# Cast single Q1ASM instruction to QASM
def Cast_QASM_instr(schedinstr, formatted_instr):
    # dictionary for casting schedule operations to QASM operations
    cast_dict = {
        "X": """x q[{}];\n""",
        "X90": """rx(pi/2) q[{}];\n""",
        "Y": """y q[{}];\n""",
        "Y90": """ry(pi/2) q[{}];\n""",
        "Rxy": """rx({}) q[{}];\nry({}) q[{}];\n""",
        "CZ": """cz q[{}],q[{}];\n""",
        "Measure": """measure q[{}] -> c[{}];\n"""
        }
    #find all inputs
    print(schedinstr)
    params = [par[6:] for par in re.findall("theta=\-?\w*\.\w*|theta=\-?\w*", schedinstr)]
    params += [par[4:] for par in re.findall("phi=\-?\w*\.\w*|phi=\-?\w*", schedinstr)]

    targets = re.findall("q\d", schedinstr)
    targets = [target[1:] for target in targets]

    #format parameters and targets
    print(params)
    if params:
        #parameterized gates, parameters need to best casted to radians
        format_params = [radians(float(params[0])), targets[0], radians(float(params[1])), targets[0]]
    else:
        #regular gates
        format_params = targets
    #if formatted_instr == "Measure":
        #QASM_instr = cast_dict[formatted_instr].format(format_params[0], format_params[0])
    #    print()
    #else:
    QASM_instr = cast_dict[formatted_instr].format((*format_params)) # not allowed for python >=3.9
    return QASM_instr


def cast_to_QASM(sched_source, qubits):
    # Read operations from quantify schedule
    sched =  dict(sched_source.data["operation_dict"].items())
    # Construct base string for QASM
    base_str = """OPENQASM 2.0;
include "qelib1.inc";
"""
    # Add classical and quantum registers
    QASM_sched = base_str + """qreg q[{}];
creg c[{}];
""".format(qubits, qubits)
    
    # Supported Q1ASM operations
    instr_list = ["X90", "X", "Y", "Y90", "Rxy", "CNOT", "CZ"]

    # Format instructions to QASM
    for key in sched.keys():
        formatted_instr = re.search(".*[(]", key).group(0)[0:-1]
        if formatted_instr in instr_list:
            QASM_oper = Cast_QASM_instr(key, formatted_instr)
            QASM_sched += QASM_oper

    # Add measurement
    # Note that all qubits will be measured, selective measurement
    # is not yet implemented
    QASM_sched += """measure q -> c;"""
    # Return QASM schedule string
    return QASM_sched
