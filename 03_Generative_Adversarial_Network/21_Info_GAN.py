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

SAVE_DIR = "/tmp/ML/13_Generative_Adversarial_Network/21_Info_GAN"

# Define Hyper Parameters
N_EPISODES = 10000
mb_size = 32
Z_dim = 16

# Parameters for the Networks
H_SIZE_01 = 256
INPUT_SIZE = 784
# NOISE_SIZE = 128

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

X = tf.placeholder(tf.float32, shape=[None, INPUT_SIZE])
Z = tf.placeholder(tf.float32, shape=[None, 16])
c = tf.placeholder(tf.float32, shape=[None, 10])

"""
def xavier_init(size):
    in_dim = size[0]
    xavier_stddev = 1. / tf.sqrt(in_dim / 2.)
    return tf.random_normal(shape=size, stddev=xavier_stddev)

# Generator Variables
W01_Gen = tf.Variable(xavier_init([26, H_SIZE_01]))
W02_Gen = tf.Variable(xavier_init([H_SIZE_01, INPUT_SIZE]))
B01_Gen = tf.Variable(tf.zeros(shape=[H_SIZE_01]))
B02_Gen = tf.Variable(tf.zeros(shape=[INPUT_SIZE]))

# Discriminator Variables
W01_Dis = tf.Variable(xavier_init([INPUT_SIZE, H_SIZE_01]))
W02_Dis = tf.Variable(xavier_init([H_SIZE_01, 1]))
B01_Dis = tf.Variable(tf.zeros(shape=[H_SIZE_01]))
B02_Dis = tf.Variable(tf.zeros(shape=[1]))

W01_Q   = tf.Variable(xavier_init([INPUT_SIZE, H_SIZE_01]))
W02_Q   = tf.Variable(xavier_init([H_SIZE_01, 10]))
B01_Q   = tf.Variable(tf.zeros(shape=[H_SIZE_01]))
B02_Q   = tf.Variable(tf.zeros(shape=[10]))
"""

W01_Gen = tf.get_variable("W01_Gen", shape=[26, H_SIZE_01],
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

W01_Q   = tf.get_variable("W01_Q", shape=[INPUT_SIZE, H_SIZE_01],
                     initializer=tf.contrib.layers.xavier_initializer())
W02_Q   = tf.get_variable("W02_Q", shape=[H_SIZE_01, 10],
                     initializer=tf.contrib.layers.xavier_initializer())
B01_Q   = tf.Variable(tf.random_normal([H_SIZE_01]))
B02_Q   = tf.Variable(tf.random_normal([10]))

# Build Generator Network.
def GENERATOR(z, c):
    inputs = tf.concat(axis=1, values=[z, c])
    _LAY01_Gen = tf.nn.relu(tf.matmul(inputs, W01_Gen) + B01_Gen)
    output_Gen = tf.nn.sigmoid(tf.matmul(_LAY01_Gen, W02_Gen) + B02_Gen)
    return output_Gen

def DISCRIMINATOR(x):
    _LAY01_Dis = tf.nn.relu(tf.matmul(x, W01_Dis) + B01_Dis)
    output_Dis = tf.nn.sigmoid(tf.matmul(_LAY01_Dis, W02_Dis) + B02_Dis)
    return output_Dis

def Q(x):
    _LAY01_Q = tf.nn.relu(tf.matmul(x, W01_Q) + B01_Q)
    output_Q = tf.nn.softmax(tf.matmul(_LAY01_Q, W02_Q) + B02_Q)
    return output_Q

def GET_NOISE(BATCH_SIZE, NOISE_SIZE):
#    return np.random.uniform(-1., 1., size=[BATCH_SIZE, NOISE_SIZE])
    return np.random.normal(-1., 1., size=[BATCH_SIZE, NOISE_SIZE])

def sample_c(m):
    return np.random.multinomial(1, 10*[0.1], size=m)

G_var_list = [W01_Gen, W02_Gen, B01_Gen, B02_Gen]
D_var_list = [W01_Dis, W02_Dis, B01_Dis, B02_Dis]
Q_var_list = [W01_Q, W02_Q, B01_Q, B02_Q]

G_sample = GENERATOR(Z, c)
D_real = DISCRIMINATOR(X)
D_fake = DISCRIMINATOR(G_sample)
Q_c_given_x = Q(G_sample)

D_loss = -tf.reduce_mean(tf.log(D_real + 1e-8) + tf.log(1 - D_fake + 1e-8))
G_loss = -tf.reduce_mean(tf.log(D_fake + 1e-8))

cross_ent = tf.reduce_mean(-tf.reduce_sum(tf.log(Q_c_given_x + 1e-8) * c, 1))
Q_loss = cross_ent

D_solver = tf.train.AdamOptimizer().minimize(D_loss, var_list=D_var_list)
G_solver = tf.train.AdamOptimizer().minimize(G_loss, var_list=G_var_list)
Q_solver = tf.train.AdamOptimizer().minimize(Q_loss, var_list=G_var_list + Q_var_list)

sess = tf.Session()
sess.run(tf.global_variables_initializer())

if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

i = 0

for episode in range(N_EPISODES):
    if episode % 1000 == 0:
        Z_noise = GET_NOISE(16, Z_dim)

        idx = np.random.randint(0, 10)
        c_noise = np.zeros([16, 10])
        c_noise[range(16), idx] = 1

        samples = sess.run(G_sample,
                           feed_dict={Z: Z_noise, c: c_noise})

        fig = plot(samples)
        plt.savefig(SAVE_DIR + '/{}.png'
                    .format(str(i).zfill(3)), bbox_inches='tight')
        i += 1
        plt.close(fig)

    X_mb, _ = mnist.train.next_batch(mb_size)
    Z_noise = GET_NOISE(mb_size, Z_dim)
    c_noise = sample_c(mb_size)

    _, D_loss_curr = sess.run([D_solver, D_loss],
                              feed_dict={X: X_mb, Z: Z_noise, c: c_noise})

    _, G_loss_curr = sess.run([G_solver, G_loss],
                              feed_dict={Z: Z_noise, c: c_noise})

    sess.run([Q_solver], feed_dict={Z: Z_noise, c: c_noise})

    if episode % 1000 == 0:
        print("[Episode : {:>5d}]".format(episode),"[D loss: {:2.5f}]". format(D_loss_curr),"[G_loss: {:2.5f}]".format(G_loss_curr))
