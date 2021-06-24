# -*- coding: utf-8 -*-
"""
Created on Thu Aug  6 15:23:42 2020

@author: dkafkes
"""

import pandas as pd

want = pd.read_csv('db_want.txt', header=None)
have = pd.read_csv('db_have.txt', header=None)

missing = list(set(want[0].tolist()) - set(have[0].tolist()))

#%%
a = pd.DataFrame(missing)



have.columns[0]