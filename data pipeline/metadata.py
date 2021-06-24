# -*- coding: utf-8 -*-
"""
Created on Tue Jul 14 15:33:29 2020

@author: dkafkes
"""
import pandas as pd
import h5py
import os
import argparse
import subprocess
# import glob
import re

def metadata_finder(directory, save_where, sliced):
    
    data = pd.read_csv('tape_names.txt', sep=" ", header=None)
    data.columns = ['Filenames']
    relevant = data[data.Filenames.str.startswith("MLParamData")]
    relevant.reset_index(drop= True, inplace = True)
        
    if sliced == 1:
        files = relevant[0:30]
    elif sliced == 2:
        files = relevant[30:60]
    elif sliced == 3:
        files = relevant[60:90]
    elif sliced == 4:
        files = relevant[90:120]
    elif sliced == 5:
        files = relevant[120:150]
    elif sliced == 6:
        files = relevant[150:175]
    elif sliced == 7:
         files = ['MLParamData_1562043667.8512678_From_MLrn_2019-07-01+00:00:00_to_2019-07-02+00:00:00.h5','MLParamData_1586757608.2241669_From_MLrn_2020-04-12+00:00:00_to_2020-04-13+00:00:00.h5']
        
    os.chdir(str(directory))
    
    # relevant_files = glob.glob1(str(directory),"MLParamData*.h5")
    relevant_files = files.Filenames.tolist()
    
    current_file = 0
    print('Files to go: '+str(len(relevant_files)))
    
    master_df = pd.DataFrame()
    master_df['Filename'] = pd.Series(relevant_files)
    master_df = master_df.set_index('Filename')
    
    for filename in relevant_files:
        print(filename)
        #print(timeit(stmt = '''subprocess.run('cat ".(get)('+str(filename)+')(locality)"', shell=True, stdout=subprocess.PIPE)''', setup = "import subprocess", number = 10000))
        
        subprocess.run('cat ".(touch)('+str(filename)+')(stage)(120)"', shell = True)

        disk_mounted = subprocess.run('cat ".(get)('+str(filename)+')(locality)"', shell=True, stdout=subprocess.PIPE)
                        
        if disk_mounted.stdout == 'ONLINE_AND_NEARLINE' or 'ONLINE':
            f= h5py.File(filename, 'r')   
            h5_keys = list(f.keys())
            f.close()
            
            relevant_keys = []

            for i in h5_keys:
                if re.match('B_*', i) is not None:
                    relevant_keys.append(re.match('B_*', i).string)
                elif re.match('I_*', i) is not None:
                    relevant_keys.append(re.match('I_*', i).string)
        
            remainder = len(relevant_keys)
            
            for key in relevant_keys:
                                    
                df = pd.read_hdf(filename, key)
                
                if key in df.columns:
                    stdev = df[str(key)].std()
                    big = df[str(key)].max()
                    small = df[str(key)].min()
                    mean = df[str(key)].mean()
                    non = df[str(key)].isnull().sum()
                elif 'value' in df.columns:
                    stdev = df.value.std()
                    big = df.value.max()
                    small = df.value.min()
                    mean = df.value.mean()
                    non = df.value.isnull().sum()
                
                print(stdev, big, small, mean, non)
                
                if str(key)+' STD' not in master_df.columns:
                    master_df[str(key)+' STD'] = ''
                    master_df.loc[str(filename), str(key)+' STD'] = stdev
                    
                    master_df[str(key)+' MEAN'] = ''
                    master_df.loc[str(filename), str(key)+' MEAN'] = mean
                    
                    master_df[str(key)+' MAX'] = ''
                    master_df.loc[str(filename), str(key)+' MAX'] = big
                    
                    master_df[str(key)+' MIN'] = ''
                    master_df.loc[str(filename), str(key)+' MIN'] = small
                    
                    master_df[str(key)+' NULLS'] = ''
                    master_df.loc[str(filename), str(key)+' NULLS'] = non
                    
                else:
                    master_df.loc[str(filename), str(key)+' STD'] = stdev
                    master_df.loc[str(filename), str(key)+' MEAN'] = mean
                    master_df.loc[str(filename), str(key)+' MAX'] = big
                    master_df.loc[str(filename), str(key)+' MIN'] = small
                    master_df.loc[str(filename), str(key)+' NULLS'] = non
                
                remainder -= 1
                print(str(remainder)+' keys remaining')
                
            current_file += 1
            print('Completed: '+str(round(current_file/len(relevant_files)*100, 2))+'%')

        else:
            print(str(filename)+" not staged")
            
    master_df.to_csv(os.path.join(str(save_where), "metadata"+str(sliced)+".csv"))
        
    print('Process complete!')
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Saves all metadata to metadata.txt in working directory.')
    parser.add_argument('--directory', type=str, default='/pnfs/ldrd/accelai/tape', help="directory where your hdf5 files live")
    parser.add_argument('--save_where', type=str, default='/accelai/app/kafkes', help="directory you wish to save")
    parser.add_argument('--sliced', type=int, default= 1, help="which portion of the filenames would you like to run")

    args = parser.parse_args()

    directory = str(args.directory)
    save_where = str(args.save_where)
    sliced = int(args.sliced)
    
    metadata_finder(directory, save_where, sliced)
    

