# -*- coding: utf-8 -*-
"""
Created on Tue Jul 14 15:44:42 2020

@author: dkafkes
"""

import pandas as pd

one = pd.read_csv('metadata1.csv')
two = pd.read_csv('metadata2.csv')
three = pd.read_csv('metadata3.csv')
four = pd.read_csv('metadata4.csv')
five = pd.read_csv('metadata5.csv')
six = pd.read_csv('metadata6.csv')
# seven = pd.read_csv('metadata7.csv')
#%%

mega = pd.concat([one,two], axis=0, ignore_index=True)
mega = pd.concat([mega,three], axis=0, ignore_index=True)
mega = pd.concat([mega,four], axis=0, ignore_index=True)
mega = pd.concat([mega,five], axis=0, ignore_index=True)
mega = pd.concat([mega,six], axis=0, ignore_index=True)
mega = pd.concat([mega,seven], axis=0, ignore_index=True)

#%%
data = pd.read_csv('tape_names.txt', sep=" ", header=None)
data.columns = ['Filenames']
relevant = data[data.Filenames.str.startswith("MLParamData")]
relevant.reset_index(drop= True, inplace = True)

set(relevant.Filenames - mega.Filename)

#%%
#mega.to_csv("Parameter_Metadata_All.csv")

#%%%
import pandas as pd

mega = pd.read_csv("Parameter_Metadata_All.csv")
mega.to_json("parameter_metadata_all")