import tensorflow as tf
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.gridspec as gridspec

from tensorflow.examples.tutorials.mnist import input_data
# 최신 Windows Laptop에서만 사용할것.CPU Version이 높을때 사용.
# AVX를 지원하는 CPU는 Giuthub: How to compile tensorflow using SSE4.1, SSE4.2, and AVX. 
# Ubuntu와 MacOS는 지원하지만 Windows는 없었음. 2018-09-29
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

# Compuntational Graph Initialization
from tensorflow.python.framework import ops
ops.reset_default_graph()

DATA_DIR = "/tmp/ML/MNIST_data"
mnist = input_data.read_data_sets(DATA_DIR, one_hot=True)

SAVE_DIR = "/tmp/ML/13_Generative_Adversarial_Network/24_Mode_Regularized"

# Define Hyper Parameters
N_EPISODES = 10000
mb_size = 32

# Parameters for the Networks
INPUT_SIZE = 784
NOISE_SIZE = 128
H_SIZE_01 = 256
lam1 = 1e-2
lam2 = 1e-2

def plot(samples):
    fig = plt.figure(figsize=(4, 4))
    gs = gridspec.GridSpec(4, 4)
    gs.update(wspace=0.05, hspace=0.05)

    for i, sample in enumerate(samples):
        ax = plt.subplot(gs[i])
        plt.axis('off')
        ax.set_xticklabels([])
        ax.set_yticklabels([])
        ax.set_aspect('equal')
        plt.imshow(sample.reshape(28, 28), cmap='Greys_r')

    return fig

def log(x):
    return tf.log(x + 1e-8)

X = tf.placeholder(tf.float32, shape=[None, INPUT_SIZE])
z = tf.placeholder(tf.float32, shape=[None, NOISE_SIZE])

"""
def xavier_init(size):
    in_dim = size[0]
    xavier_stddev = 1. / tf.sqrt(in_dim / 2.)
    return tf.random_normal(shape=size, stddev=xavier_stddev)

# Generator Variables
W01_Gen = tf.Variable(xavier_init([NOISE_SIZE, H_SIZE_01]))
W02_Gen = tf.Variable(xavier_init([H_SIZE_01, INPUT_SIZE]))
B01_Gen = tf.Variable(tf.zeros(shape=[H_SIZE_01]))
B02_Gen = tf.Variable(tf.zeros(shape=[INPUT_SIZE]))

# Discriminator Variables
W01_Dis = tf.Variable(xavier_init([INPUT_SIZE, H_SIZE_01]))
W02_Dis = tf.Variable(xavier_init([H_SIZE_01, 1]))
B01_Dis = tf.Variable(tf.zeros(shape=[H_SIZE_01]))
B02_Dis = tf.Variable(tf.zeros(shape=[1]))

# Encoder Variables
W01_Enc = tf.Variable(xavier_init([INPUT_SIZE, H_SIZE_01]))
W02_Enc = tf.Variable(xavier_init([H_SIZE_01, NOISE_SIZE]))
B01_Enc = tf.Variable(tf.zeros(shape=[H_SIZE_01]))
B02_Enc = tf.Variable(tf.zeros(shape=[NOISE_SIZE]))
"""

W01_Gen = tf.get_variable("W01_Gen", shape=[NOISE_SIZE, H_SIZE_01],
                     initializer=tf.contrib.layers.xavier_initializer())
W02_Gen = tf.get_variable("W02_Gen", shape=[H_SIZE_01, INPUT_SIZE],
                     initializer=tf.contrib.layers.xavier_initializer())
B01_Gen = tf.Variable(tf.random_normal([H_SIZE_01]))
B02_Gen = tf.Variable(tf.random_normal([INPUT_SIZE]))

W01_Dis = tf.get_variable("W01_Dis", shape=[INPUT_SIZE, H_SIZE_01],
                     initializer=tf.contrib.layers.xavier_initializer())
W02_Dis = tf.get_variable("W02_Dis", shape=[H_SIZE_01, 1],
                     initializer=tf.contrib.layers.xavier_initializer())
B01_Dis = tf.Variable(tf.random_normal([H_SIZE_01]))
B02_Dis = tf.Variable(tf.random_normal([1]))

W01_Enc = tf.get_variable("W01_Enc", shape=[INPUT_SIZE, H_SIZE_01],
                     initializer=tf.contrib.layers.xavier_initializer())
W02_Enc = tf.get_variable("W02_Enc", shape=[H_SIZE_01, NOISE_SIZE],
                     initializer=tf.contrib.layers.xavier_initializer())
B01_Enc = tf.Variable(tf.random_normal([H_SIZE_01]))
B02_Enc = tf.Variable(tf.random_normal([NOISE_SIZE]))

# Build Generator Network.
def GENERATOR(z):
    _LAY01_Gen = tf.nn.relu(tf.matmul(z, W01_Gen) + B01_Gen)
    output_Gen = tf.nn.sigmoid(tf.matmul(_LAY01_Gen, W02_Gen) + B02_Gen)
    return output_Gen

def DISCRIMINATOR(x):
    _LAY01_Dis = tf.nn.relu(tf.matmul(x, W01_Dis) + B01_Dis)
    output_Dis = tf.nn.sigmoid(tf.matmul(_LAY01_Dis, W02_Dis) + B02_Dis)
    return output_Dis

def GET_NOISE(BATCH_SIZE, NOISE_SIZE):
#    return np.random.uniform(-1., 1., size=[BATCH_SIZE, NOISE_SIZE])
    return np.random.normal(-1., 1., size=[BATCH_SIZE, NOISE_SIZE])

def ENCODER(x):
    _LAY01_Enc = tf.nn.relu(tf.matmul(x, W01_Enc) + B01_Enc)
    output_Enc = tf.matmul(_LAY01_Enc, W02_Enc) + B02_Enc
    return output_Enc

G_var_list = [W01_Gen, W02_Gen, B01_Gen, B02_Gen]
D_var_list = [W01_Dis, W02_Dis, B01_Dis, B02_Dis]
E_var_list = [W01_Enc, W02_Enc, B01_Enc, B02_Enc]

G_sample = GENERATOR(z)
G_sample_reg = GENERATOR(ENCODER(X))

D_real = DISCRIMINATOR(X)
D_fake = DISCRIMINATOR(G_sample)
D_reg = DISCRIMINATOR(G_sample_reg)

mse = tf.reduce_sum((X - G_sample_reg)**2, 1)

D_loss = -tf.reduce_mean(log(D_real) + log(1 - D_fake))
E_loss = tf.reduce_mean(lam1 * mse + lam2 * log(D_reg))
G_loss = -tf.reduce_mean(log(D_fake)) + E_loss

E_solver = (tf.train.AdamOptimizer(learning_rate=1e-3)
            .minimize(E_loss, var_list=E_var_list))
D_solver = (tf.train.AdamOptimizer(learning_rate=1e-3)
            .minimize(D_loss, var_list=D_var_list))
G_solver = (tf.train.AdamOptimizer(learning_rate=1e-3)
            .minimize(G_loss, var_list=G_var_list))

sess = tf.Session()
sess.run(tf.global_variables_initializer())

if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

i = 0

for episode in range(N_EPISODES):
    X_mb, _ = mnist.train.next_batch(mb_size)

    _, D_loss_curr = sess.run(
        [D_solver, D_loss],
        feed_dict={X: X_mb, z: GET_NOISE(mb_size, NOISE_SIZE)}
    )

    _, G_loss_curr = sess.run(
        [G_solver, G_loss],
        feed_dict={X: X_mb, z: GET_NOISE(mb_size, NOISE_SIZE)}
    )

    _, E_loss_curr = sess.run(
        [E_solver, E_loss],
        feed_dict={X: X_mb, z: GET_NOISE(mb_size, NOISE_SIZE)}
    )

    if episode % 1000 == 0:
        print('[Episode : {:>5}] [D_loss: {:2.5f}] [G_loss: {:2.5f}] [E_loss: {:2.5f}]'
              .format(episode, D_loss_curr, G_loss_curr, E_loss_curr))

        samples = sess.run(G_sample, feed_dict={z: GET_NOISE(16, NOISE_SIZE)})

        fig = plot(samples)
        plt.savefig(SAVE_DIR + '/{}.png'
                    .format(str(i).zfill(3)), bbox_inches='tight')
        i += 1
        plt.close(fig)
