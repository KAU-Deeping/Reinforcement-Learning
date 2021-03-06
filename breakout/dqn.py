import numpy as np
import tensorflow as tf

class DQN:

# Initialize DQN
    def __init__(self, session: tf.Session, input_size: int, output_size: int, h_size: int=16, l_rate: int=0.001, activation: str="tf.nn.relu", name: str="main") -> None:

        # Initialize args
        self.session = session
        self.input_size = input_size
        self.output_size = output_size
        self.net_name = name

        # Initialize params
        """
        h_size : dimension of hidden layer
        l_rate : learning rate
        activation : activation function
        """
        self.h_size = h_size
        self.l_rate = l_rate
        self.activation = activation

        self._build_network()

    # Create Deep Q Network
    def _build_network(self, h_size=128, l_rate=0.001) -> None:

        with tf.variable_scope(self.net_name, reuse=False):

            # Initialize X with input_size(from envs)
            self._X = tf.placeholder(tf.float32, shape=(None, 84, 84, 4), name="input_x")
            input_data = self._X


            conv1 = tf.layers.conv2d(inputs=input_data, filters=64, kernel_size=[8, 8], strides=[8, 8], activation=tf.nn.relu)
            conv2 = tf.layers.conv2d(inputs=conv1, filters=32, kernel_size=[4, 4], strides=[4, 4], activation=tf.nn.relu)
            conv3 = tf.layers.conv2d(inputs=conv2, filters=32, kernel_size=[3, 3], padding='SAME', activation=tf.nn.relu)

            flat = tf.layers.flatten(conv3)

            net1 = tf.layers.dense(flat, h_size, tf.nn.relu)
            net2 = tf.layers.dense(net1, h_size, tf.nn.relu)

            output = tf.layers.dense(net2, self.output_size)
            self._Qpred = output

            # Get Y
            self._Y = tf.placeholder(tf.float32, shape=[None, self.output_size])
            print(self._Y)

            # Define loss function
            self._loss = tf.losses.mean_squared_error(self._Y, self._Qpred)

            optimizer = tf.train.AdamOptimizer(learning_rate=l_rate)
            self._train = optimizer.minimize(self._loss)


    def predict(self, state: np.ndarray) -> np.ndarray:
        x = np.reshape(state, newshape=[-1, 84, 84, 4])
        return self.session.run(self._Qpred, feed_dict={self._X: x})

    def update(self, x_stack: np.ndarray, y_stack: np.ndarray) -> list:

        feed = {
            self._X: x_stack,
            self._Y: y_stack
        }
        return self.session.run([self._loss, self._train], feed)