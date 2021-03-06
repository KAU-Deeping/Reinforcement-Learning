"""
Double DQN (Nature 2015)
http://web.stanford.edu/class/psych209/Readings/MnihEtAlHassibis15NatureControlDeepRL.pdf
Notes:
    The difference is that now there are two DQNs (DQN & Target DQN)
    y_i = r_i + 𝛾 * max(Q(next_state, action; 𝜃_target))
    Loss: (y_i - Q(state, action; 𝜃))^2
    Every C step, 𝜃_target <- 𝜃
"""
import numpy as np
import tensorflow as tf
import random

from collections import deque
from breakout import dqn
import matplotlib.pyplot as plt

from skimage.transform import resize
from skimage.color import rgb2gray

import gym
from typing import List

class model:

    # Initialize model with params
    def __init__(self, game_name: str, DISCOUNT_RATE: int=0.99, REPLAY_MEMORY: int=50000, BATCH_SIZE: int=64, TARGET_UPDATE_FREQUENCY: int=5,
                 h_size: int=16, l_rate: int=0.001, activation: str="tf.nn.relu", MAX_EPISODES: int=50000):
        self.env = gym.make(game_name)
        self.env = gym.wrappers.Monitor(self.env, directory="gym-results/", force=True)

        # Constants defining our neural network
        # Shape[0]이 맞는지 확인 필요
        self.INPUT_SIZE = self.env.observation_space.shape
        self.OUTPUT_SIZE = self.env.action_space.n

        # Initialize model's params
        self.DISCOUNT_RATE = DISCOUNT_RATE
        self.REPLAY_MEMORY = REPLAY_MEMORY
        self.BATCH_SIZE = BATCH_SIZE
        self.TARGET_UPDATE_FREQUENCY = TARGET_UPDATE_FREQUENCY
        self.MAX_EPISODES = MAX_EPISODES
        # Initialize dqn's params
        self.h_size = h_size
        self.l_rate = l_rate
        self.activation = activation
    # Make input frame to gray scale and resize
    def pre_proc(self, x):
        x = np.uint8(resize(rgb2gray(x), (84, 84), mode='constant') * 255)
        return x

    # Train with main DQN and target DQN
    def replay_train(self, mainDQN: dqn.DQN, targetDQN: dqn.DQN, train_batch: list) -> float:
        """Trains `mainDQN` with target Q values given by `targetDQN`
        Args:
            mainDQN (dqn.DQN): Main DQN that will be trained
            targetDQN (dqn.DQN): Target DQN that will predict Q_target
            train_batch (list): Minibatch of replay memory
                Each element is (s, a, r, s', done)
                [(state, action, reward, next_state, done), ...]
        Returns:
            float: After updating `mainDQN`, it returns a `loss`
        """
        states = np.vstack([x[0] for x in train_batch])
        actions = np.array([x[1] for x in train_batch])
        rewards = np.array([x[2] for x in train_batch])
        next_states = np.stack([x[3] for x in train_batch])
        done = np.array([x[4] for x in train_batch])

        X = states

        Q_target = rewards + self.DISCOUNT_RATE * np.max(targetDQN.predict(next_states), axis=1) * ~done

        y = mainDQN.predict(states)
        y[np.arange(len(X)), actions] = Q_target

        # Train our network using target and predicted Q values on each episode
        return mainDQN.update(X, y)

    # Copy main DQN's args to target DQN
    def get_copy_var_ops(self, *, dest_scope_name: str, src_scope_name: str) -> List[tf.Operation]:
        """Creates TF operations that copy weights from `src_scope` to `dest_scope`
        Args:
            dest_scope_name (str): Destination weights (copy to)
            src_scope_name (str): Source weight (copy from)
        Returns:
            List[tf.Operation]: Update operations are created and returned
        """
        # Copy variables src_scope to dest_scope
        op_holder = []

        src_vars = tf.get_collection(
            tf.GraphKeys.TRAINABLE_VARIABLES, scope=src_scope_name)
        dest_vars = tf.get_collection(
            tf.GraphKeys.TRAINABLE_VARIABLES, scope=dest_scope_name)

        for src_var, dest_var in zip(src_vars, dest_vars):
            op_holder.append(dest_var.assign(src_var.value()))

        return op_holder


    def bot_play(self, mainDQN: dqn.DQN, env: gym.Env) -> None:
        """Test runs with rendering and prints the total score
        Args:
            mainDQN (dqn.DQN): DQN agent to run a test
            env (gym.Env): Gym Environment
        """
        state = env.reset()
        reward_sum = 0

        while True:
            env.render()
            action = np.argmax(mainDQN.predict(state))
            state, reward, done, _ = env.step(action)
            reward_sum += reward

            if done:
                print("Total score: {}".format(reward_sum))
                break

    # Train with E-greedy, discount rate and random batch. Save episode and step data into each episode_data_stored and step_data_stored using list
    def train(self, episode_data_stored, step_data_stored):
        # store the previous observations in replay memory
        replay_buffer = deque(maxlen=self.REPLAY_MEMORY)

        last_10_game_reward = deque(maxlen=10)

        with tf.Session() as sess:
            mainDQN = dqn.DQN(sess, self.INPUT_SIZE, self.OUTPUT_SIZE, self.h_size, self.l_rate, activation=self.activation, name="main")
            targetDQN = dqn.DQN(sess, self.INPUT_SIZE, self.OUTPUT_SIZE, name="target")
            sess.run(tf.global_variables_initializer())

            # initial copy q_net -> target_net
            copy_ops = self.get_copy_var_ops(dest_scope_name="target",
                                        src_scope_name="main")
            sess.run(copy_ops)

            for episode in range(self.MAX_EPISODES):
                e = 1. / ((episode / 10) + 1)
                done = False
                reward_sum = 0
                state = self.env.reset()

                if np.shape(state) == (1, 84, 84, 1):
                    continue
                else:
                    state = self.pre_proc(state)

                history = np.stack((state, state, state, state), axis=2)
                history = np.reshape([history], (1, 84, 84, 4))

                while not done:
                    if np.random.rand() < e:
                        action = self.env.action_space.sample()
                    else:
                        # Reshape state to (1, 84, 84, 1)
                        state = np.reshape(state, (1, 84, 84, 1))
                        # Choose an action by greedily from the Q-network
                        action = np.argmax(mainDQN.predict(history))
                        print(action)

                    # Get new state and reward from environment
                    next_state, reward, done, _ = self.env.step(action)

                    if done:  # Penalty
                        continue
                        #reward = -10

                    # Pre processing next_states
                    next_state = self.pre_proc(next_state)
                    next_state = np.reshape(next_state, (1, 84, 84, 1))
                    next_history = np.append(next_state, history[:, :, :, :3], axis=3)

                    # Save the experience to our buffer
                    replay_buffer.append((history, action, reward, next_history, done))

                    if len(replay_buffer) > self.BATCH_SIZE:
                        minibatch = random.sample(replay_buffer, self.BATCH_SIZE)
                        loss, _ = self.replay_train(mainDQN, targetDQN, minibatch)

                    if reward_sum % self.TARGET_UPDATE_FREQUENCY == 0:
                        sess.run(copy_ops)

                    state = next_state
                    reward_sum += reward

                print("Episode: {}  Rewards: {}".format(episode, reward_sum))

                episode_data_stored.append(episode)
                step_data_stored.append(reward_sum)

                """
                # CartPole-v0 Game Clear Checking Logic
                last_10_game_reward.append(reward_sum)

                if len(last_10_game_reward) == last_10_game_reward.maxlen:
                    avg_reward = np.mean(last_10_game_reward)


                    if avg_reward > 4000:
                        print("Game Cleared in {episode} episodes with avg reward {avg_reward}")
                        break
                """

            # Save model
            self.save_model(sess)

        # Return episode and average reward data
        return [episode]

    def plot(self, params, episode_data, step_data):
        plt.plot(episode_data, step_data)

        plt.xlabel("Episode")
        plt.ylabel("Step")

        plt.title("Discount rate: {:.3f} Replay Memory : {} Batch size: {} Target Update Frequency: {} Hidden layer size: {} "
                  "Learning rate: {}\nActivation function: {} Episodes that needed to train: {}".format(params[0], params[1], params[2], params[3],
                                                                                                        params[4], params[5], params[6], params[7]))

        # Save figure to pdf
        plt.savefig(
            fname="Discount rate: {:.3f} Replay Memory : {} Batch size: {} Target Update Frequency: {} Hidden layer size: {} Learning rate: {} "
                  "Activation function: {} Episodes that needed to train: {}.pdf".format(params[0], params[1], params[2], params[3],
                                                                                         params[4], params[5], params[6], params[7]), format="pdf")
        # Clear figure for next training
        plt.clf()

    # Save model to file "breakout_model.ckpt"
    def save_model(self, sess: tf.Session):
        saver = tf.train.Saver()
        save_path = saver.save(sess, "./breakout_model.ckpt")