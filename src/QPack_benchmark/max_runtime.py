#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 27 13:14:57 2022

@author: koen
"""
import json

with open('logs/log_mcp_qblox_cluster.json','r') as f:
    base_data = json.load(f)
    
data = base_data['data']
max_calls = 100
max_runtime = 0
for entry in data:
    if entry['func_calls'] <= max_calls:
        max_calls = entry['func_calls']
        max_runtime = sum(entry['time_res']['quantum_runtime'])
print(max_calls, max_runtime)