#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 28 11:23:30 2022

adjusted schedule runtime
@author: koen
"""
import json

measurement = 500e-9
sgate = 40e-9
tgate = 100e-9

with open('logs/log_mcp_qblox_dummy_cluster.json','r') as f:
    base_data = json.load(f)
    
data = base_data['data']

for entry in data:
    runtime = (entry['time_res']['time_per_step']['schedule']/(entry['func_calls']-1))/2000
