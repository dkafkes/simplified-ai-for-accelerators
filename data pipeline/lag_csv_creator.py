# -*- coding: utf-8 -*-
"""
Created on Tue Sep  1 12:29:01 2020

@author: dkafkes
"""
import pandas as pd

#this is only the booster readings
devices = pd.read_csv('device_lag_data.txt', sep=" ")

new_frame = devices[['param', 'max']]
new_frame.to_csv('booster_readings.csv')