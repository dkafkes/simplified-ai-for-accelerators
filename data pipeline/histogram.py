# -*- coding: utf-8 -*-
"""
Created on Tue Jun 23 11:31:08 2020

@author: dkafkes
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_csv('master_stdev.csv', header = 0, skiprows = list(np.arange(1, 177)))
df.drop(columns = ['Filename'], inplace = True)
df = df.set_index('Unnamed: 0')
#%%

x = df['B:IMINER']
array, bins, patches = plt.hist(x, bins = 100)
plt.title("B:IMINER Standard Deviation Spread")
plt.xlabel("Average Standard Deviation")
plt.ylabel("Log(Files)")
plt.ylim(0.1, 1000)
plt.semilogy()
plt.show()