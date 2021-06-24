# -*- coding: utf-8 -*-
import gym
import time
import logging
import csv
import os
import random
import numpy as np
import tensorflow as tf

from tqdm import tqdm
from datetime import datetime

# Try plaidml
#os.environ["KERAS_BACKEND"] = "tensorflow.keras.backend"

# Framework class
import os
import sys
cwd = os.getcwd()
new = 'C:/Users/dkafkes/Desktop/fermi/accelerator-reinforcement-learning/control-for-accelerators-in-hep/agents'

sys.path.append(new)
os.chdir(sys.path[-1])
print(os.getcwd())
from dqn import DQN
os.chdir(cwd)

# Seed value
# Apparently you may use different seed values at each stage
seed_value = 0

# 1. Set the PYTHONHASHSEED environment variable at a fixed value
os.environ['PYTHONHASHSEED'] = str(seed_value)

# 2. Set the `python` built-in pseudo-random generator at a fixed value
random.seed(seed_value)

# 3. Set the `numpy` pseudo-random generator at a fixed value
np.random.seed(seed_value)

# 4. Set the `tensorflow` pseudo-random generator at a fixed value
tf.random.set_seed(seed_value)

#
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('RL-Logger')
logger.setLevel(logging.INFO)

if __name__ == "__main__":

    now = datetime.now()
    timestamp = now.strftime("D%m%d%Y-T%H%M%S")
    print("date and time:", timestamp)

    doPlay = True #change to True for test

    # Train
    EPISODES = 2000
    NSTEPS: int = 50
    best_reward = -100000
    
    if doPlay:
        EPISODES = 1000 #seems fine to test?

    # Setup environment
    estart = time.time()
    env_version = 1
    env = gym.make('gym_accelerator:Surrogate_Accelerator-v{}'.format(env_version))
    env._max_episode_steps = NSTEPS
    env.seed(1)
    end = time.time()
    logger.info('Time init environment: %s' % str((end - estart) / 60.0))
    logger.info('Using environment: %s' % env)
    logger.info('Observation_space: %s' % env.observation_space.shape)
    logger.info('Action_size: %s' % env.action_space)

    # Setup agent
    arch_type = 'MLP'
    nmodels = 1
    logger.info('Using DQN {}'.format(arch_type))
    agent = DQN(env, cfg='../cfg/dqn_setup.json', arch_type=arch_type, nmodels=nmodels)

    if doPlay: 
        agent.load('../results/sansUQ_results_dqn_MLP_1_n128_gamma85_250warmup_train5_surrogate1_in6_out2_D05282021-T113137_v1/final_policy_model.weights.h5')

        # new: results_dqn_MLP_1_n128_gamma85_250warmup_train5_surrogate1_in6_out2_UQ_D05262021-T104923_v1
        
            # IPAC: results_dqn_MLP_1_n128_gamma85_250warmup_train5_surrogate1_in6_out2_UQ_D05132021-T201402_v1
        #stopped at 89% due to filling up my whole disk RIP

        ### PAPER V2: results_dqn_MLP_1_n128_gamma85_250warmup_train5_surrogate1_in5_out3_D04142021-T114217_v1

            # '../policy_models/results_dqn_09132020_v2/best_episodes'
            # '/policy_model_e143_fnal_surrogate_dqn_mlp_episodes250_steps100_09132020.weights.h5')

    # Save information
    save_directory = '../results/results_dqn_{}_{}_n128_gamma85_250warmup_train5_surrogate{}_in5_out3_{}_v1/'.format(arch_type, nmodels, env_version, timestamp)
    
    if doPlay:
        save_directory = '../test/sansUQ_play_results_dqn_surrogate{}_{}_v1/'.format(env_version, timestamp)
    
    # Make directory for information
    if not os.path.exists(save_directory):
        #print("making directory")
        os.makedirs(save_directory)

    logger.info('Save directory:{}'.format(save_directory))
    env.save_dir = save_directory
    #safe_file_prefix = 'fnal_surrogate_dqn_mlp_episodes{}_steps{}_{}'.format(EPISODES, NSTEPS, timestamp)

    os.chdir(save_directory)
    desired_cwd = os.getcwd()
    
    train_file_s = open('batched_memories.log'.format(EPISODES, NSTEPS, timestamp), 'w')
    train_writer_s = csv.writer(train_file_s, delimiter=" ")

    train_file_e = open('reduced_batched_memories.log'.format(EPISODES, timestamp), 'w') #weirdest thing ever... will not save with NSTEPS in it... seems to be coming up against the windows 260 char limit for paths
    train_writer_e = csv.writer(train_file_e, delimiter=" ")

    # train_file_s = open(safe_file_prefix+'_batched_memories.log', 'w+')
    # train_writer_s = csv.writer(train_file_s, delimiter=" ")
    # train_file_e = open(safe_file_prefix+ '_reduced_batched_memories.log', 'w+')
    # train_writer_e = csv.writer(train_file_e, delimiter=" ")

    counter = 0
    for e in tqdm(range(EPISODES), desc='RL Episodes', leave=True):
        os.chdir(desired_cwd)
        print(os.getcwd())

        logger.info('Starting new episode: %s' % str(e))
        current_state = env.reset()
        total_reward = 0
        done = False
        step_counter = 0
        episode_loss = []

        while not done:
            os.chdir(desired_cwd)
            action, policy_type = agent.action(current_state)
            
            if doPlay:
                action, policy_type = agent.play(current_state)
            
            next_state, reward, PID_reward, data_reward, done, _ = env.step(action)
            
            if not doPlay:
                agent.remember(current_state, action, reward, next_state, done)
                if counter >= 250 and counter % 5 == 0:
                    agent.train()

            # Print information
            logger.info('Current state: %s' % str(current_state))
            logger.info('Action: %s' % str(action))
            logger.info('Next state: %s' % str(next_state))
            logger.info('Next state shape: %s' % str(next_state.shape))
            logger.info('Reward: %s' % str(reward))
            logger.info('Done: %s' % str(done))

            # Update  current state
            current_state = next_state

            # Increment total reward
            total_reward += reward
            step_counter += 1
            counter += 1

            # Check if maximum episode steps is reached
            if step_counter >= NSTEPS:
                done = True

            # Save memory
            train_writer_s.writerow([current_state, action, reward, PID_reward, data_reward, next_state, total_reward, done, policy_type, e]) #would i just write more of the rewards?
            train_file_s.flush()

        logger.info('Total reward: %s' % str(total_reward))
        train_writer_e.writerow([e, total_reward])
        train_file_e.flush()
        if total_reward > best_reward:
            os.chdir(desired_cwd)
            agent.save('policy_model_e{}_'.format(e))
            best_reward = total_reward
    
    os.chdir(desired_cwd)
    agent.save('final_policy_model')
    train_file_s.close()
