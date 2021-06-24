import pandas as pd
import h5py
import os
import argparse
import subprocess
import glob
import re
# from timeit import timeit

def stdev_finder(directory, save_where):
    
    os.chdir(str(directory))
    
    # subprocess.run('ls -ltra MLParam*h5  | awk ''{print " touch \".(fset)("$9")(stage)(120)\""}' '', shell=True)
    
    relevant_files = glob.glob1(str(directory),"MLParamData*.h5")
    
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
                elif 'value' in df.columns:
                    stdev = df.value.std()
                    big = df.value.max()
                    small = df.value.min()
                                        
                if str(key) not in master_df.columns:
                    master_df[str(key)+' STD'] = ''
                    master_df.loc[str(filename)+' STD', str(key)] = stdev
                    
                    master_df[str(key)+' MAX'] = ''
                    master_df.loc[str(filename)+' MAX', str(key)] = big
                    
                    master_df[str(key)+' MIN'] = ''
                    master_df.loc[str(filename)+' MIN', str(key)] = small
                else:
                    master_df.loc[str(filename), str(key)+' STD'] = stdev
                    master_df.loc[str(filename), str(key)+' MAX'] = big
                    master_df.loc[str(filename), str(key)+' MIN'] = small
            
                remainder -= 1
                print(str(remainder)+' keys remaining')
                
            current_file += 1
            print('Completed: '+str(round(current_file/len(relevant_files)*100, 2))+'%')
                
        else:
            print(str(filename)+" not staged")
            
    master_df.to_csv(os.path.join(str(save_where), "metadata.csv"))
        
    print('Process complete!')
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Saves all standard deviations to stdev.txt in working directory.')
    parser.add_argument('--directory', type=str, default='/pnfs/ldrd/accelai/tape', help="directory where your hdf5 files live")
    parser.add_argument('--save_where', type=str, default='/accelai/app/kafkes', help="variable name")

    args = parser.parse_args()

    directory = str(args.directory)
    save_where = str(args.save_where)
    
    stdev_finder(directory, save_where)
    