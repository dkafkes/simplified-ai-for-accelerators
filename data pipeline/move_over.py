# -*- coding: utf-8 -*-
"""
Created on Thu Aug  6 11:51:08 2020

@author: dkafkes
"""

import os
import argparse
import subprocess
# import glob

def move_over(directory, save_where):
    os.chdir(str(directory))
    # param_files = glob.glob1(str(directory),"MLParamData*.h5")
    # event_files = glob.glob1(str(directory),"MLEventData*.h5")
    
    # relevant_files = param_files + event_files
    # get missing files
    relevant_files = ['MLEventData_1579248003.5331511_From_EventC_2020-01-16+00:00:00_to_2020-01-17+00:00:00.h5', \
 'MLEventData_1582444802.8679726_From_EventC_2020-02-22+00:00:00_to_2020-02-23+00:00:00.h5', \
 'MLEventData_1561796994.5220554_From_EventC_2019-06-09+00:00:00_to_2019-06-10+00:00:00.h5', \
 'MLEventData_1561954075.7979_From_EventC_2019-05-07+00:00:00_to_2019-05-08+00:00:00.h5', \
 'MLEventData_1561746365.6698549_From_EventC_2019-06-23+00:00:00_to_2019-06-24+00:00:00.h5', \
 'MLEventData_1580544003.0838468_From_EventC_2020-01-31+00:00:00_to_2020-02-01+00:00:00.h5', \
 'MLEventData_1584255604.0225317_From_EventC_2020-03-14+00:00:00_to_2020-03-15+00:00:00.h5', \
 'MLEventData_1583222403.3547802_From_EventC_2020-03-02+00:00:00_to_2020-03-03+00:00:00.h5', \
 'MLEventData_1561960540.473038_From_EventC_2019-05-06+00:00:00_to_2019-05-07+00:00:00.h5', \
 'MLEventData_1579161603.617057_From_EventC_2020-01-15+00:00:00_to_2020-01-16+00:00:00.h5', \
 'MLEventData_1579075203.4427295_From_EventC_2020-01-14+00:00:00_to_2020-01-15+00:00:00.h5', \
 'MLEventData_1584428403.6679916_From_EventC_2020-03-16+00:00:00_to_2020-03-17+00:00:00.h5', \
 'MLEventData_1577692803.4391448_From_EventC_2019-12-29+00:00:00_to_2019-12-30+00:00:00.h5', \
 'MLEventData_1576224002.872758_From_EventC_2019-12-12+00:00:00_to_2019-12-13+00:00:00.h5', \
 'MLEventData_1563841043.3830473_From_EventC_2019-07-21+23:59:59_to_2019-07-22+00:00:00.h5', \
 'MLEventData_1578902403.5957174_From_EventC_2020-01-12+00:00:00_to_2020-01-13+00:00:00.h5', \
 'MLEventData_1577260803.7663343_From_EventC_2019-12-24+00:00:00_to_2019-12-25+00:00:00.h5']
    
    for filename in relevant_files:
        print(filename)
        
        subprocess.run('cat ".(touch)('+str(filename)+')(stage)(120)"', shell = True)

        disk_mounted = subprocess.run('cat ".(get)('+str(filename)+')(locality)"', shell=True, stdout=subprocess.PIPE)
                        
        if disk_mounted.stdout == 'ONLINE_AND_NEARLINE' or 'ONLINE':
            print("moving "+str(filename))
            command = 'cp '+str(directory)+'/'+str(filename)+' '+str(save_where)
            subprocess.run(str(command), shell = True)
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Move files to persistent storage.')
    parser.add_argument('--directory', type=str, default='/pnfs/ldrd/accelai/tape', help="directory where your hdf5 files live")
    parser.add_argument('--save_where', type=str, default='/pnfs/ldrd/accelai/persistent', help="directory you wish to save")

    args = parser.parse_args()
    directory = str(args.directory)
    save_where = str(args.save_where)
    
    move_over(directory, save_where)
