from dataset import reformat_data, load_reformated_hdf5
import os

file_list = ['MLData_1560460545.3972487_From_MLrn_2019-06-07+00:00:00_to_2019-06-08+00:00:00.h5', 'MLData_1560460915.7555828_From_MLrn_2019-06-08+00:00:00_to_2019-06-09+00:00:00.h5',
'MLData_1560461275.2004719_From_MLrn_2019-06-09+00:00:00_to_2019-06-10+00:00:00.h5']

os.chdir('/pnfs/ldrd/accelai/tape')

for file in file_list:
	reformat_data(file)
	load_reformated_hdf5(file)