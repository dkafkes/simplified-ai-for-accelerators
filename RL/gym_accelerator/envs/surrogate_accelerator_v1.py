import gym
#import os
from gym import spaces
from gym.utils import seeding
import pandas as pd

# Framework class
import os
import sys
cwd = os.getcwd()
new = 'C:/Users/dkafkes/Desktop/fermi/accelerator-reinforcement-learning/control-for-accelerators-in-hep/dataprep'

sys.path.append(new)
os.chdir(sys.path[-1])
# print(os.getcwd())
import dataset as dp
os.chdir(cwd)

from tensorflow import keras
#from sklearn.preprocessing import MinMaxScaler
import matplotlib.pyplot as plt
import numpy as np
from tensorflow.keras.models import load_model

import logging

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('RL-Logger')
logger.setLevel(logging.INFO)

np.seterr(divide='ignore', invalid='ignore')


def create_dataset(dataset, look_back=10 * 15, look_forward=1):
    X, Y = [], []
    offset = look_back + look_forward
    for i in range(len(dataset) - (offset + 1)):
        xx = dataset[i:(i + look_back), 0]
        yy = dataset[(i + look_back):(i + offset), 0]
        X.append(xx)
        Y.append(yy)
    return np.array(X), np.array(Y)


def get_dataset(df, variable='B:VIMIN'):
    dataset = df[variable].values
    dataset = dataset.astype('float32')
    dataset = np.reshape(dataset, (-1, 1))
    #scaler = MinMaxScaler(feature_range=(0, 1)) ### bringing this back for reviewer
    #dataset = scaler.fit_transform(dataset)

    train_size = int(len(dataset) * 0.70)
    train, test = dataset[0:train_size, :], dataset[train_size:len(dataset), :]

    X_train, Y_train = create_dataset(train, look_back= 15) #3/25 needed to change to replicate results of the paper #15)
    X_train = np.reshape(X_train, (X_train.shape[0], 1, X_train.shape[1]))
    Y_train = np.reshape(Y_train, (Y_train.shape[0], Y_train.shape[1]))

    # X_test, Y_test = create_dataset(test, look_back=15)
    # X_test = np.reshape(X_test, (X_test.shape[0], 1, X_test.shape[1]))
    # Y_test = np.reshape(Y_test, (Y_test.shape[0],  Y_test.shape[1]))

    return X_train, Y_train #scaler, X_test, Y_test
    #return X_train, Y_train, scaler #need to return scaler to replicate

def all_inplace_scale(df):
    scale_dict = {}

    for var in ['B:VIMIN', 'B:IMINER', 'B_VIMIN', 'B:LINFRQ', 'I:IB', 'I:MDAT40']: #TODO: make dynamic
      our_data2 = df
      trace = our_data2[var].astype('float32')
      data = np.array(trace)
      # print(data)
      median = np.median(data)
      upper_quartile = np.percentile(data, 75)
      lower_quartile = np.percentile(data, 25)
      #print(median, upper_quartile, lower_quartile)
      iqr = upper_quartile - lower_quartile
      lower_whisker = data[data>=lower_quartile-1.5*iqr].min()
      upper_whisker = data[data<=upper_quartile+1.5*iqr].max()
      
      #print(f'Variable {var} with upper {upper_whisker} and lower {lower_whisker}')
      
      ranged = upper_whisker - lower_whisker
      #(value − median) / (upper - lower)
      our_data2[var] = 1/ranged*(data - median)
      
      scale_dict[str(var)] = {"median": median, "range": ranged}
    
    return scale_dict

def unscale(var_name, tseries, scale_dict):
    #equivalent to inverse transform
    from_model = np.asarray(tseries)
    update = from_model*scale_dict[str(var_name)]["range"] + scale_dict[str(var_name)]["median"]

    return(update)

def rescale(var_name, tseries, scale_dict):
    #equivalent to transform
    data = np.asarray(tseries)
    update = 1/scale_dict[str(var_name)]["range"]*(data - scale_dict[str(var_name)]["median"])

    return(update)

# def data_distribution_plot(model, BoX_test, BoY_test, episode, step):
#   fig, axs = plt.subplots(1, figsize=(12,12))
#   x_test=BoX_test
#   y_test=BoY_test
#   start=0
#   end=BoX_test.shape[0]
#   Y_predict = model.predict(x_test[start:end,:,:])
#   Y_test_var0 = data_list[0][0].inverse_transform(y_test[start:end,0].reshape(-1,1)).reshape(-1,1)
#   Y_test_var1 = data_list[1][0].inverse_transform(y_test[start:end,1].reshape(-1,1)).reshape(-1,1)
#   Y_predict_var0 = data_list[0][0].inverse_transform(Y_predict[:,0].reshape(-1,1)).reshape(-1,1)
#   Y_predict_var1 = data_list[1][0].inverse_transform(Y_predict[:,1].reshape(-1,1)).reshape(-1,1)
#   np_predict = np.concatenate((Y_test_var0,Y_test_var1,Y_predict_var0,Y_predict_var1),axis=concate_axis) 
#   df_cool = pd.DataFrame(np_predict,columns=['data_va0','data_va1','pred_va0','pred_va1'])

#   sns.scatterplot(data=df_cool, x="data_va0", y="data_va1", label='Data')#, hue="time")
#   sns.scatterplot(data=df_cool, x="pred_va0", y="pred_va1", label='Digital Twin')#, hue="time")
#   #sns.scatterplot(data=df_cool, x="data_va1", y="pred_va1", label='Data')#, hue="time")
#   plt.savefig(os.path.join(directory), 'episode{}_step{}_corr_final.png'.format(episode, step))

def create_dropout_predict_model(model, dropout):
    
    # Load the config of the original model
    conf = model.get_config()

    # Add the specified dropout to all layers
    for layer in conf['layers']:
        #print(layer)
#         if layer["class_name"]=="LSTM":
#             #print(layer)
#             print(layer["config"]["recurrent_dropout"])
#             layer["config"]["recurrent_dropout"] = dropout
#             print(layer["config"]["recurrent_dropout"])

        # Dropout layers
        if layer["class_name"]=="Dropout":
            # print(layer)
            layer["config"]["rate"] = dropout
        # Recurrent layers with dropout
#         elif "dropout" in layer["config"].keys():
#             layer["config"]["dropout"] = dropout
        
#         elif "recurrent_dropout" in layer["config"].keys():
#             print(layer["config"]["recurrent_dropout"])
#             layer["config"]["recurrent_dropout"] = dropout

    # Create a new model with specified dropout
    # print(type(model))
    model_dropout = keras.Model.from_config(conf)

    model_dropout.set_weights(model.get_weights()) 
    return model_dropout

def regulation(alpha, gamma, error, min_set, beta):
  ## calculate the prediction with current regulation rules
  ## from Rachael's report, eq (1)
  #beta=[0]
  ER = error #error
  _MIN = min_set #setting
  for i in range(len(_MIN)):
      if i>0:
            beta_t = beta[-1] + gamma*ER[i]
            beta.append(beta_t) #hopefully this will update self.rachael_beta in place
  # print()
  # print("Rachael's Eq")
  # print(_MIN.shape)
  # print(alpha)
  # print(ER.shape)
  # print(np.asarray(beta).reshape(15,1).shape)
  # print()

  MIN_pred = _MIN - alpha * ER - np.asarray(beta[-15:]).reshape(15,1) #predict the next, shiftting happens in the plotting #check here
  #used to be 15, now 150
  return MIN_pred

class Surrogate_Accelerator_v1(gym.Env):
    def __init__(self):

        self.save_dir = os.getcwd() #'./'
        self.episodes = 0
        self.steps = 0
        self.max_steps = 100
        self.total_reward = 0
        self.data_total_reward = 0
        self.diff = 0

        self.rachael_reward = 0
        self.rachael_beta = [0] #unclear if needed... depends on whether the regulation should be allowed to build continuously

        # Define boundary

        #4/12: removing this arbitrary boundary
        # self.min_BIMIN = 103.1
        # self.max_BIMIN = 103.6

#maybe we don't need boundary here... external to algorithm

        # self.max_IMINER = 1
        # self.variables = ['B:VIMIN', 'B:IMINER', 'B:LINFRQ', 'I:IB', 'I:MDAT40']
        # self.nbatches = 0
        # self.nsamples = 0

        # Load surrogate models
        #https://github.com/keras-team/keras/issues/14040 needs it to be false
        #print(os.getcwd())

        ### WAY I DO IT NOW
        model = keras.models.load_model('C:/Users/dkafkes/Desktop/fermi/accelerator-reinforcement-learning/control-for-accelerators-in-hep/surrogate_models/databricks models/6to2_UQ_prelim/fullbooster_noshift_e25_bs32_k_invar6_outvar2_axis1_mmscaler_t0_D03012021-T173721_kfold4__final.h5') #, compile = False)
        self.booster_model = create_dropout_predict_model(model, 0) #calibrated on 3/02/2021: .2
        #try with 7 actions and without dropout too! to validate previous results

        ### REVERSION
        # self.booster_model = keras.models.load_model('C:/Users/dkafkes/Desktop/fermi/accelerator-reinforcement-learning/control-for-accelerators-in-hep/surrogate_models/fullbooster_noshift_e250_bs99_nsteps250k_invar5_outvar3_axis1_mmscaler_t0_D10122020-T175237_kfold2__e16_vl0.00038.h5')

            #'../surrogate_models/databricks models/2to2_1sec_decomposed/fullbooster_noshift_e250_bs99_k_invar6_outvar2_axis1_mmscaler_t0_D12042020-T181345_kfold4__final.h5', compile = False)

            #fullbooster_noshift_e250_bs99_nsteps250k_invar5_outvar3_axis1_mmscaler_t0_D10122020'
            #'-T175237_kfold2__e16_vl0.00038.h5')
        # ("good") fullbooster_noshift_e250_bs99_nsteps250k_nvar5_axis1_mmscaler_t0_D10122020-T133515_kfold4__final.h5')
        # fullbooster_noshift_e250_bs99_nsteps250k_nvar7_axis1_mmscaler_t0_D10112020-T174516_kfold4__final.h5')
        # self.injector_model = keras.models.load_model(
        #     '../surrogate_models/model_injector_adam256_e350_bs99_nsteps250k.h5')

        # Load scalers

        # Load data to initialize the env
        filename = 'data_release.csv' #'decomposed_all.csv' #no longer want decomposed data
        data = dp.load_reformated_cvs('../data/' + filename, nrows=250000)
        #WHAT I WANT: 
        scale_dict = all_inplace_scale(data)

        data['B:VIMIN'] = data['B:VIMIN'].shift(-1)
        #B:VIMIN shifted back one... should B_VIMIN be shifted? should B:VIMIN_1 and B:VIMIN_2 be shifted?
        # data['B:VIMIN_1'] = data['B:VIMIN_1'].shift(-1) #yes
        # data['B:VIMIN_2'] = data['B:VIMIN_2'].shift(-1) #yes

        data = data.set_index(pd.to_datetime(data.time))
        data = data.dropna()
        data = data.drop_duplicates()
        self.variables = ['B:VIMIN', 'B:IMINER', 'B_VIMIN', 'B:LINFRQ', 'I:IB', 'I:MDAT40']

        #WHAT I WANT> 6 to 2: ['B:VIMIN', 'B:IMINER', 'B_VIMIN', 'B:LINFRQ', 'I:IB', 'I:MDAT40']
        #['B:VIMIN', 'B:IMINER', 'B_VIMIN', 'B:VIMIN_1', 'B:VIMIN_2', 'B:IMINER_1', 'B:IMINER_2', 'B:LINFRQ_1', 'B:LINFRQ_2', 'I:IB_1', 'I:IB_2', 'I:MDAT40_1', 'I:MDAT40_2']
        #['B:VIMIN', 'B:IMINER', 'B_VIMIN', 'B:VIMIN_1', 'B:VIMIN_2', 'B:IMINER_1', 'B:IMINER_2'] #'B:VIMIN_1', 'B:VIMIN_2', 'B:IMINER_1', 'B:VIMIN_2'] #['B:VIMIN', 'B:IMINER'] #TODO: change variables here 'B:LINFRQ', 'I:IB', 'I:MDAT40']
        # self.variables = ['B: #VIMIN', 'B:IMINER', 'B:VIPHAS', 'B:LINFRQ', 'I:IB', 'I:MDAT40', 'I:MXIB']
        self.nvariables = len(self.variables)
        logger.info('Number of variables:{}'.format(self.nvariables))

        self.scale_dict = scale_dict
        #self.scalers = []
        data_list = []
        x_train = []

        # get_dataset also normalizes the data
        for v in range(len(self.variables)):
            data_list.append(get_dataset(data, variable=self.variables[v]))
            # self.scalers.append(data_list[v][2]) #comment out for new scaling
            x_train.append(data_list[v][0])

        #work around to contain in plot
        # just_B_VIMIN = get_dataset(data, variable ='B_VIMIN')
        # self.B_VIMIN_record = just_B_VIMIN[0]
        # self.B_VIMIN_scaler = just_B_VIMIN[2]

        # Axis
        self.concate_axis = 1
        self.X_train = np.concatenate(x_train, axis=self.concate_axis)

        self.nbatches = self.X_train.shape[0]
        self.nsamples = self.X_train.shape[2]
        self.batch_id = self.episodes + 4200
        #to test: +5000
        #np.arange(0, 4000, 1)  #np.random.randint(low = 500, high = 1100) #to test
        #to train: np.random.randint(low = 500, high = 1100)
        #to test: np.random.randint(low = 1200, high = 2000)
        #10  # np.random.randint(0, high=self.nbatches)
        self.data_state = None

        print('Data shape:{}'.format(self.X_train.shape))
        self.observation_space = spaces.Box(
            low=0,
            high=+1,
            shape=(self.nvariables,),
            dtype=np.float64
        )

        #self.actionMap_VIMIN = [0, 0.0001, 0.005, 0.001, -0.0001, -0.005, -0.001]
        #self.action_space = spaces.Discrete(7)

        # DYNAMIC ACTION SPACE SIZING
        data['B:VIMIN_DIFF'] = data['B:VIMIN'] - data['B:VIMIN'].shift(-1)
        self.nactions = 15 #set here
        self.action_space = spaces.Discrete(self.nactions)
        self.actionMap_VIMIN = []
        for i in range(1, self.nactions + 1):
            self.actionMap_VIMIN.append(data['B:VIMIN_DIFF'].quantile(i / (self.nactions + 1)))

        self.VIMIN = 0
        self.state = np.zeros(shape=(1, self.nvariables, self.nsamples))
        # self.B_VIMIN_state = np.zeros(shape= (1, 1, self.nsamples)) ### shouldn't normally need this
        self.predicted_state = np.zeros(shape=(1, self.nvariables, 1))

        self.rachael_state = np.zeros(shape=(1, self.nvariables, self.nsamples))
        self.rachael_predicted_state = np.zeros(shape=(1, self.nvariables, 1))

        logger.debug('Init pred shape:{}'.format(self.predicted_state.shape))

    def seed(self, seed=None):
        self.np_random, seed = seeding.np_random(seed)
        return [seed]

    def step(self, action):
        self.steps += 1
        logger.info('Episode/State: {}/{}'.format(self.episodes, self.steps))
        done = False

        # Steps:
        # 1) Update VIMIN based on action
        # 2) Predict booster variables
        # 3) Predict next step for injector
        # 4) Shift state with new values

        # Step 1: Calculate the new B:VIMIN based on policy action
        logger.info('Step() before action VIMIN:{}'.format(self.VIMIN))
        delta_VIMIN = self.actionMap_VIMIN[int(action)]
        DENORN_BVIMIN = unscale(self.variables[0], np.array([self.VIMIN]).reshape(1, -1), self.scale_dict)
        #self.scalers[0].inverse_transform(np.array([self.VIMIN]).reshape(1, -1))
        ### unscale(self.variables[0], np.array([self.VIMIN]).reshape(1, -1), self.scale_dict) #self.scalers[0].inverse_transform(np.array([self.VIMIN]).reshape(1, -1))
        
        DENORN_BVIMIN += delta_VIMIN
        logger.debug('Step() descaled VIMIN:{}'.format(DENORN_BVIMIN))
        logger.debug('Action:{}'.format(delta_VIMIN))

        #Rachael's Eq as an action
        alpha = 10e-2
        gamma = 7.535e-5

        B_VIMIN_trace = unscale(self.variables[2], self.state[0, 2, :].reshape(-1, 1), self.scale_dict) 
        #self.B_VIMIN_scaler.inverse_transform(self.B_VIMIN_state.reshape(-1, 1))
        ### self.scalers[2].inverse_trans.form(self.state[0, 2, :].reshape(-1, 1))
        ### unscale(self.variables[2], self.state[0, 2, :].reshape(-1, 1), self.scale_dict) #self.scalers[2].inverse_transform(self.state[0, 2, :].reshape(-1, 1))
        BIMINER_trace = unscale(self.variables[1], self.state[0, 1, :].reshape(-1, 1), self.scale_dict)
        #self.scalers[1].inverse_transform(self.state[0, 1, :].reshape(-1, 1))
        ### unscale(self.variables[1], self.state[0, 1, :].reshape(-1, 1), self.scale_dict) #self.scalers[1].inverse_transform(self.state[0, 1, :].reshape(-1, 1))
        
        #need data to be plugged in to get predicted state from rachael's equation
        #a = regulation(alpha, gamma, error = BIMINER_trace, min_set = B_VIMIN_trace, beta = self.rachael_beta)
        #(a)
        #sys.exit()

        # print(regulation(alpha, gamma, error = BIMINER_trace, min_set = B_VIMIN_trace, beta = self.rachael_beta)[-1].shape)

        self.rachael_state[0][0][self.nsamples - 1] = rescale(self.variables[0], regulation(alpha, gamma, error = BIMINER_trace, min_set = B_VIMIN_trace, beta = self.rachael_beta)[-1].reshape(-1, 1), self.scale_dict)
        #self.scalers[0].transform(regulation(alpha, gamma, error = BIMINER_trace, min_set = B_VIMIN_trace, beta = self.rachael_beta)[-1].reshape(-1, 1))
        ### rescale(self.variables[0], regulation(alpha, gamma, error = BIMINER_trace, min_set = B_VIMIN_trace, beta = self.rachael_beta)[-1].reshape(-1, 1), self.scale_dict) #grab last value
        #print(self.rachael_beta) # i just verified it updates in place

        #add guardrails
        # if DENORN_BVIMIN < self.min_BIMIN or DENORN_BVIMIN > self.max_BIMIN:
        #     logger.info('Step() descaled VIMIN:{} is out of bounds.'.format(DENORN_BVIMIN))
        #     done = True

        #TODO: change to Rachael's equation prediction...
        # if np.abs(DENORN_BIVIMIN - self.rachael_state[0][0][self.nsamples - 1]) >= some constant:
        #     logger.info('Step() descaled VIMIN:{} is out of bounds.'.format(DENORN_BVIMIN))
        #     done = True

        self.VIMIN = rescale(self.variables[0], DENORN_BVIMIN, self.scale_dict)
        #self.scalers[0].transform(DENORN_BVIMIN)
        ### rescale(self.variables[0], DENORN_BVIMIN, self.scale_dict) #self.scalers[0].transform(DENORN_BVIMIN)

        logger.debug('Step() updated VIMIN:{}'.format(self.VIMIN))
        self.state[0][0][self.nsamples - 1] = self.VIMIN

        # Step 2: Predict using booster model
        self.predicted_state = self.booster_model.predict(self.state)
        #print(self.predicted_state)
        self.predicted_state = self.predicted_state.reshape(1, 2, 1) 
        ### used to be 3 in the center #TODO: make dynamic, changing back. now should be 2

        #Rachael's equation
        self.rachael_predicted_state = self.booster_model.predict(self.rachael_state)
        self.rachael_predicted_state = self.rachael_predicted_state.reshape(1, 2, 1)

        # Step 3: Update IMINER and LINFQN
        # print(self.state.shape)
        # logger.debug('Step() state with pre-state model\n{}'.format(self.state[0,:,-2:]))
        # self.state[0, 1:3, -1:] = self.predicted_state[0,1:3]
        # logger.debug('Step() state with updated state model\n{}'.format(self.state[0,:,-2:]))
        # print(self.state.shape)

        # Predict the injector variables
        # injector_input = self.state[0,3:5,:].reshape(1,2,150)
        # injector_prediction = self.injector_model.predict(injector_input).reshape(1,2,1)
        #
        # logger.debug('Step() state with pre-injector state model\n{}'.format(self.state[0,:,-2:]))
        # logger.debug('Step() state with injector state model shape\n{}'.format(injector_prediction.shape))
        # #self.state[0, 3:5, -1:] = injector_prediction[0,:]
        # logger.debug('Step() state with updated injector state model\n{}'.format(self.state[0,:,-2:]))
        #
        # Step 4: Shift state by one step
        self.state[0, :, 0:-1] = self.state[0, :, 1:] #shift forward
        self.rachael_state[0, :, 0:-1] = self.rachael_state[0, :, 1:]

        # Update IMINER
        self.state[0][1][self.nsamples - 1] = self.predicted_state[0, 1:2]
        self.rachael_state[0][1][self.nsamples - 1] = self.rachael_predicted_state[0, 1:2]
        # ## Update injector variables
        # self.state[0, 3:5, -1:] = injector_prediction[0,:]

        # Update data state for rendering
        #self.data_state = None
        self.data_state = np.copy(self.X_train[self.batch_id + self.steps].reshape(1, self.nvariables, self.nsamples))
        data_iminer = unscale(self.variables[1], self.data_state[0][1][self.nsamples - 1].reshape(1, -1), self.scale_dict)

        #print(data_iminer)

        #self.scalers[1].inverse_transform(self.data_state[0][1][self.nsamples - 1].reshape(1, -1))
        ### unscale(self.variables[1], self.data_state[0][1][self.nsamples - 1].reshape(1, -1), self.scale_dict) #self.scalers[1].inverse_transform(self.data_state[0][1][self.nsamples - 1].reshape(1, -1))

        #where's data_vimin
        data_reward = -abs(data_iminer)
        #data_reward = np.exp(-2*np.abs(data_iminer))

        # Use data for everything but the B:IMINER prediction
        self.state[0, 2:self.nvariables, :] = self.data_state[0, 2:self.nvariables, :]
        self.rachael_state[0, 2:self.nvariables, :] = self.data_state[0, 2:self.nvariables, :]

        iminer = self.predicted_state[0, 1]
        logger.debug('norm iminer:{}'.format(iminer))
        iminer = unscale(self.variables[1], np.array([iminer]), self.scale_dict).reshape(1, -1)
        #self.scalers[1].inverse_transform(np.array([iminer]).reshape(1, -1))
        ### unscale(self.variables[1], np.array([iminer]), self.scale_dict).reshape(1, -1) #self.scalers[1].inverse_transform(np.array([iminer]).reshape(1, -1))

        logger.debug('iminer:{}'.format(iminer))

        # Reward
        reward = -abs(iminer)
        #reward2 = np.exp(-2*np.abs(iminer))

        #update rachael state for rendering
        rach_reward = -abs(unscale(self.variables[1], np.array([self.rachael_predicted_state[0, 1]]).reshape(1, -1), self.scale_dict))
        #-abs(self.scalers[1].inverse_transform(np.array([self.rachael_predicted_state[0, 1]]).reshape(1, -1)))
        ### -abs(unscale(self.variables[1], np.array([self.rachael_predicted_state[0, 1]]).reshape(1, -1), self.scale_dict))
        #-abs(self.scalers[1].inverse_transform(np.array([self.rachael_predicted_state[0, 1]]).reshape(1, -1)))
        #print(self.rachael_reward)

        # if abs(iminer) >= 2:
        #     logger.info('iminer:{} is out of bounds'.format(iminer))
        #     done = True

        # if done:
        #     penalty = 5 * (self.max_steps - self.steps)
        #     logger.info('penalty:{} is out of bounds'.format(penalty))
        #     reward -= penalty

        if self.steps >= int(self.max_steps):
            done = True

        self.diff += np.asscalar(abs(data_iminer - iminer))
        self.data_total_reward += np.asscalar(data_reward)
        self.total_reward += np.asscalar(reward)
        self.rachael_reward += np.asscalar(rach_reward)

        # print(self.total_reward)
        # print(self.data_total_reward)
        # print(self.rachael_reward)

        if self.episodes % 100 == 0: # so over this rendering...
            self.render()

        return self.state[0, :, -1:].flatten(), np.asscalar(reward), np.asscalar(rach_reward), np.asscalar(data_reward), done, {}

    def reset(self):
        self.episodes += 1
        self.steps = 0
        self.data_total_reward = 0
        self.total_reward = 0
        self.diff = 0
        self.rachael_reward = 0
        self.rachael_beta = [0]

        # Prepare the random sample ##
        #self.batch_id = 10
        self.batch_id = self.episodes + 4200
        #to test:+ 5000
        #np.arange(0, 4000, 1) #np.random.randint(low = 500, high = 1100)
        #to test: np.random.randint(low = 1200, high = 2000) #to test
        #to train: np.random.randint(low = 500, high = 1100) #high=self.nbatches) #try some range: 0, 100... find one that captures spike
        logger.info('Resetting env')
        # self.state = np.zeros(shape=(1,5,150))
        logger.debug('self.state:{}'.format(self.state))
        self.state = None
        self.state = np.copy(self.X_train[self.batch_id].reshape(1, self.nvariables, self.nsamples))

        # self.B_VIMIN_state = None
        # self.B_VIMIN_state = np.copy(self.B_VIMIN_record[self.batch_id].reshape(1, 1, self.nsamples))

        self.data_state = None
        self.state = np.copy(self.X_train[self.batch_id].reshape(1, self.nvariables, self.nsamples))
        
        self.rachael_state = None
        self.rachael_state = np.copy(self.X_train[self.batch_id].reshape(1, self.nvariables, self.nsamples))

        logger.debug('self.state:{}'.format(self.state))
        logger.debug('reset_data.shape:{}'.format(self.state.shape))
        self.VIMIN = self.state[0, 0, -1:]
        logger.debug('Normed VIMIN:{}'.format(self.VIMIN))
        logger.debug('B:VIMIN:{}'.format(unscale(self.variables[0], np.array([self.VIMIN]), self.scale_dict).reshape(1, -1)))

            #self.scalers[0].inverse_transform(np.array([self.VIMIN]).reshape(1, -1))))

        ### unscale(self.variables[0], np.array([self.VIMIN]), self.scale_dict).reshape(1, -1))) 
        #self.scalers[0].inverse_transform(np.array([self.VIMIN]).reshape(1, -1))
        return self.state[0, :, -1:].flatten()

    def render(self):

        plt.rcParams['axes.titlesize'] = 18
        plt.rcParams['axes.titleweight'] = 'bold'
        plt.rcParams['axes.labelsize'] = 18
        plt.rcParams['axes.labelweight'] = 'regular'
        plt.rcParams['xtick.labelsize'] = 14
        plt.rcParams['ytick.labelsize'] = 14
        plt.rcParams['font.family'] = [u'serif']
        plt.rcParams['font.size'] = 14
        plt.rcParams['font.family'] = [u'serif']
        plt.rcParams['font.size'] = 16

        logger.debug('render()')
        #logger.debug('Save path:{}'.format(self.save_dir))

        #coming up against windows character limit
        #render_dir = os.path.join(self.save_dir, 'render')
        # render_dir = 'render'
        # print(render_dir)
        # logger.debug('Render path:{}'.format(render_dir))

        # print("Current working directory: ", os.getcwd())
        # cwd = os.getcwd()

        # if not os.path.exists(render_dir):
        #     os.mkdir(render_dir)
        
        #os.chdir(os.path.join(self.save_dir, render_dir))

        import seaborn as sns
        sns.set_style("ticks")
        nvars = 2  # len(self.variables)> we just want B:VIMIN and B:IMINER
        fig, axs = plt.subplots(nvars, figsize=(12, 8))
        logger.debug('self.state:{}'.format(self.state))

        #Rachael's Eq
        alpha = 10e-2
        gamma = 7.535e-5
        #try dstate
        BVIMIN_trace = unscale(self.variables[0], self.state[0, 0, 1:-1].reshape(-1, 1), self.scale_dict)
        #self.scalers[0].inverse_transform(self.state[0, 0, 1:-1].reshape(-1, 1))
        ### unscale(self.variables[0], self.state[0, 0, 1:-1].reshape(-1, 1), self.scale_dict) #self.scalers[0].inverse_transform(self.state[0, 0, 1:-1].reshape(-1, 1))

        # print(type(BVIMIN_trace))
        # print(BVIMIN_trace.shape)

        BIMINER_trace = unscale(self.variables[1], self.state[0, 1, :].reshape(-1, 1), self.scale_dict)
        #self.scalers[1].inverse_transform(self.state[0, 1, :].reshape(-1, 1))
        ### unscale(self.variables[1], self.state[0, 1, :].reshape(-1, 1), self.scale_dict) #self.scalers[1].inverse_transform(self.state[0, 1, :].reshape(-1, 1))

        # print(type(BIMINER_trace))
        # print(BIMINER_trace.shape)

        B_VIMIN_trace = unscale(self.variables[2], self.state[0, 2, :].reshape(-1, 1), self.scale_dict)
        #self.B_VIMIN_scaler.inverse_transform(self.B_VIMIN_state.reshape(-1, 1))
        ### self.scalers[2].inverse_transform(self.state[0, 2, :].reshape(-1, 1))
        ### unscale(self.variables[2], self.state[0, 2, :].reshape(-1, 1), self.scale_dict) #self.scalers[2].inverse_transform(self.state[0, 2, :].reshape(-1, 1)) #will this work or does it have to stay as something we grab from data

        # print(type(B_VIMIN_trace))
        # print(B_VIMIN_trace.shape)

        #something is weird with this change... it definitely is predicting 180 value which isn't right
        BVIMIN_pred = unscale(self.variables[0], self.rachael_state[0, 0, :].reshape(-1, 1), self.scale_dict)
        #self.scalers[0].inverse_transform(self.rachael_state[0, 0, :].reshape(-1, 1))
        ### unscale(self.variables[0], self.rachael_state[0, 0, :].reshape(-1, 1), self.scale_dict)
        #self.scalers[0].inverse_transform(self.rachael_state[0, 0, :].reshape(-1, 1)) #regulation(alpha, gamma, error = BIMINER_trace, min_set = B_VIMIN_trace, beta = [0]) #check here
        # print(self.rachael_state[0, 0, :].reshape(-1, 1))

        # print(type(BVIMIN_pred))
        # print(BVIMIN_pred.shape)

        #BVIMIN_pred = regulation(alpha, gamma, error = BIMINER_trace*0, min_set = B_VIMIN_trace)
        # _IMINER = 10*np.add(B_VIMIN_trace, -1*BVIMIN_pred)  #don't need to shift since BVIMIN started shifted

        rachael_IMINER = unscale(self.variables[1], self.rachael_state[0, 1, :].reshape(-1, 1), self.scale_dict)
        #self.scalers[1].inverse_transform(self.rachael_state[0, 1, :].reshape(-1, 1))
        ### unscale(self.variables[1], self.rachael_state[0, 1, :].reshape(-1, 1), self.scale_dict) #self.scalers[1].inverse_transform(self.rachael_state[0, 1, :].reshape(-1, 1))
        #print(rachael_IMINER)
        #sys.exit()
        #print(_IMINER)
        #print(BIMINER_trace)

        #sys.exit()
        # print(type(_IMINER))
        # print(_IMINER.shape)

        #self.rachael_reward += -1*np.asscalar(_IMINER[-1][0])
        
        for v in range(0, nvars):
            utrace = self.state[0, v, :]
            trace = unscale(self.variables[v], utrace.reshape(-1, 1), self.scale_dict)
            #self.scalers[v].inverse_transform(utrace.reshape(-1, 1))
            ### unscale(self.variables[v], utrace.reshape(-1, 1), self.scale_dict) # self.scalers[v].inverse_transform(utrace.reshape(-1, 1))

            if v == 0:
                axs[v].set_title('Raw data reward: {:.2f} - RL agent reward: {:.2f} - PID Eq reward {:.2f}'.format(self.data_total_reward, self.total_reward, self.rachael_reward)) #soemthing seems weird... might need to actually track it above
            
            axs[v].plot(trace, label='RL Policy', color='black')

            # if v==1:
            data_utrace = self.data_state[0, v, :]
            data_trace = unscale(self.variables[v], data_utrace.reshape(-1, 1), self.scale_dict)
            #self.scalers[v].inverse_transform(data_utrace.reshape(-1, 1))
            ### unscale(self.variables[v], data_utrace.reshape(-1, 1), self.scale_dict) #self.scalers[v].inverse_transform(data_utrace.reshape(-1, 1))

            #you'll need to transform two

            if v == 1:
                x = np.linspace(0, 14, 15) #np.linspace(0, 14, 15) #np.linspace(0, 149, 150) #TODO: change this so that it is dynamic for lookback
                axs[v].fill_between(x, -data_trace.flatten(), +data_trace.flatten(), alpha=0.2, color='red')

            axs[v].plot(data_trace, 'r--', label='Data')
            #axs[v].plot()
            axs[v].set_xlabel('time')
            axs[v].set_ylabel('{}'.format(self.variables[v]))
            #axs[v].legend(loc='upper left')

        ### replaced np.linspace(0,14,15)
        axs[0].plot(np.linspace(0, 14, 15), BVIMIN_pred, label="PID Eq", color = 'blue', linestyle = 'dotted')
        axs[0].legend(loc='upper left')
        axs[1].plot(np.linspace(0, 14, 15), rachael_IMINER, label="PID Eq", color = 'blue', linestyle = 'dotted')
        axs[1].legend(loc='upper left')

        plt.savefig('episode{}_step{}_v1.png'.format(self.episodes, self.steps))
        plt.clf()

        fig, axs = plt.subplots(1, figsize=(12,12))

        # print(self.scalers[0])
        # print(self.scalers[1])
        # print(self.state[0][0])
        # print(self.state[1][0])

        Y_agent_bvimin = unscale(self.variables[0], self.state[0][0].reshape(-1,1), self.scale_dict).reshape(-1,1)
        #self.scalers[0].inverse_transform(self.state[0][0].reshape(-1,1)).reshape(-1,1)
        ### unscale(self.variables[0], self.state[0][0].reshape(-1,1), self.scale_dict).reshape(-1,1) #self.scalers[0].inverse_transform(self.state[0][0].reshape(-1,1)).reshape(-1,1) #[start:end,0]
        Y_agent_biminer = unscale(self.variables[1], self.state[0][1].reshape(-1,1), self.scale_dict).reshape(-1,1)
        #self.scalers[1].inverse_transform(self.state[0][1].reshape(-1,1)).reshape(-1,1)
        ### unscale(self.variables[1], self.state[0][1].reshape(-1,1), self.scale_dict).reshape(-1,1) #self.scalers[1].inverse_transform(self.state[0][1].reshape(-1,1)).reshape(-1,1) #[start:end,1]

        Y_data_bvimin = unscale(self.variables[0], self.data_state[0][0].reshape(-1,1), self.scale_dict).reshape(-1,1)
        #self.scalers[0].inverse_transform(self.data_state[0][0].reshape(-1,1)).reshape(-1,1)
        ### unscale(self.variables[0], self.data_state[0][0].reshape(-1,1), self.scale_dict).reshape(-1,1) #self.scalers[0].inverse_transform(self.data_state[0][0].reshape(-1,1)).reshape(-1,1) #[start:end,0]
        
        Y_data_biminer = unscale(self.variables[1], self.data_state[0][1].reshape(-1,1), self.scale_dict).reshape(-1,1)
        #self.scalers[1].inverse_transform(self.data_state[0][1].reshape(-1,1)).reshape(-1,1)
        ### unscale(self.variables[1], self.data_state[0][1].reshape(-1,1), self.scale_dict).reshape(-1,1) #self.scalers[1].inverse_transform(self.data_state[0][1].reshape(-1,1)).reshape(-1,1) #[start:end,1]

        Y_rachael_bvimin = unscale(self.variables[0], self.rachael_state[0][0].reshape(-1,1), self.scale_dict).reshape(-1,1)
        #self.scalers[0].inverse_transform(self.rachael_state[0][0].reshape(-1,1)).reshape(-1,1)
        ### unscale(self.variables[0], self.rachael_state[0][0].reshape(-1,1), self.scale_dict).reshape(-1,1) #self.scalers[0].inverse_transform(self.rachael_state[0][0].reshape(-1,1)).reshape(-1,1)
        
        Y_rachael_iminer = unscale(self.variables[1], self.rachael_state[0][1].reshape(-1,1), self.scale_dict).reshape(-1,1)
        #self.scalers[1].inverse_transform(self.rachael_state[0][1].reshape(-1,1)).reshape(-1,1)
        ### unscale(self.variables[1], self.rachael_state[0][1].reshape(-1,1), self.scale_dict).reshape(-1,1) #self.scalers[1].inverse_transform(self.rachael_state[0][1].reshape(-1,1)).reshape(-1,1)

        # print(np.unique(Y_rachael_bvimin))
        # print(np.unique(Y_rachael_iminer))
        # print()
        # print(np.unique(Y_agent_bvimin))
        # print(np.unique(Y_agent_biminer))

        # sys.exit()

        np_predict = np.concatenate((Y_data_bvimin, Y_data_biminer, Y_agent_bvimin, Y_agent_biminer, Y_rachael_bvimin, Y_rachael_iminer), axis=self.concate_axis) 
        df_cool = pd.DataFrame(np_predict, columns=['bvimin_data','biminer_data', 'bvimin_agent', 'biminer_agent', 'bvimin_rachael', 'biminer_rachael'])

        # print(df_cool['bvimin_data'])
        # print(df_cool['biminer_data'])

        #can't get this to show up super well but i assure you they are overlapping
        # sns.scatterplot(data=df_cool, x="bvimin_data", y="biminer_data", label='Data', alpha = .5)#, hue="time")
        # sns.scatterplot(data=df_cool, x="bvimin_rachael", y="biminer_rachael", label="PID Eq", alpha = .3)#, hue="time")
        # sns.scatterplot(data=df_cool, x="bvimin_agent", y="biminer_agent", label='RL Policy', alpha = .5)#, hue="time")

        plt.scatter(Y_data_bvimin, Y_data_biminer, color = 'red', alpha=0.5, label = 'Data')
        plt.scatter(Y_agent_bvimin, Y_agent_biminer, color = 'black', alpha=0.5, label = 'RL Policy')
        plt.scatter(Y_rachael_bvimin, Y_rachael_iminer, color = 'blue', alpha=0.5, label = 'PID Eq')
        plt.xlabel('B:VIMIN')
        plt.ylabel('B:IMINER')
        plt.legend()

        plt.savefig('corr_episode{}_step{}.png'.format(self.episodes, self.steps))

        plt.close('all')
        os.chdir(cwd)
