# -*- coding: utf-8 -*-
"""
Created on Tue Jul 21 11:24:51 2020

@author: dkafkes
"""

import pandas as pd
import os
import argparse

def debug(save_where, sliced):
    trial = pd.Series(['a', 'b', 'c', 'd'])
    test = pd.DataFrame()
    test['col 1'] = trial
    test.to_csv(os.path.join(str(save_where), "metadata"+str(sliced)+".csv"))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Saves all standard deviations to stdev.txt in working directory.')
    parser.add_argument('--save_where', type=str, default='/accelai/app/kafkes', help="directory you wish to save")
    parser.add_argument('--sliced', type=int, default= 1, help="which portion of the filenames would you like to run")

    args = parser.parse_args()

    save_where = str(args.save_where)
    sliced = int(args.sliced)
    
    debug(save_where, sliced)