import learn
import collections
import random
import tensorflow as tf

# Save Parameter information
"""
    1 : DISCOUNT_RATE
    2 : REPLAY_MEMORY
    3 : BATCH_SIZE
    4 : Hidden layer size
    5 : Learning rate
    6 : Activation function
    7 : Episodes that needed to train
    8 : Success / Failed
"""
train_data = collections.deque()

# tf.math.tanh have #1, tf.nn. relu have #2
activation_func = ["tf.nn.relu", "tf.nn.tanh"]

for func in activation_func:
    for i in range(10):
        """
        Each vars are according to following descriptions...
            1 : DISCOUNT_RATE
            2 : REPLAY_MEMORY
            3 : BATCH_SIZE
            4 : Hidden layer size
            5 : Learning rate
            6 : Activation function // Function은 string 형태로 입력되는 변수가 아닌데 어떻게 자동으로??... 오늘은 졸려서 잠좀 잘게요..내일 열심히해야
            7 : Episodes that needed to train
            8 : Success / Failed
        """
        params = [random.uniform(0.70, 0.99), random.randint(40000, 50000), random.randint(32, 64), 5, random.randint(12, 20), random.uniform(0.01, 0.001), func]
        model = learn.model("CartPole-v0", params[0], params[1], params[2], params[3], params[4], params[5], params[6], 600)
        result = model.train()

        # Append ending epsode number
        #params.append(result[0])

        # Append training was successful or not
        params.append(True if result[1] == 200 else False)

        print("Discount rate: {}\nReplay Memory : {}\nBatch size: {}\nHidden layer size: {}\nLearning rate: {}\nActivation function: {}\nEpisodes that needed to train: {}\n".format(params[0], params[1], params[2], params[3], params[4], params[6], params[7]))

        train_data.append(params)

        # Clear graph for next training
        tf.reset_default_graph()