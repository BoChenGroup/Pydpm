"""
===========================================
Convolutional Poisson Factor Analysis
Chaojie Wang  Sucheng Xiao  Bo Chen  and  Mingyuan Zhou
Published in International Conference on Machine Learning 2019

===========================================

"""

# Author: Chaojie Wang <xd_silly@163.com>; Jiawen Wu <wjw19960807@163.com>; Wei Zhao <13279389260@163.com>
# License: BSD-3-Clause

import numpy as np
import argparse
import scipy.io as sio
import _pickle as cPickle

from torch.utils.data import Dataset, DataLoader
from torchtext.data.utils import get_tokenizer
from torchtext.datasets import AG_NEWS

from pydpm.model import CPFA
from pydpm.metric import ACC
from pydpm.dataloader.text_data import Text_Processer, build_vocab_from_iterator

# =========================================== ArgumentParser ===================================================================== #
parser = argparse.ArgumentParser()

# device
parser.add_argument("--device", type=str, default='gpu')

# dataset
parser.add_argument("--data_path", type=str, default='../../../dataset/', help="the path of loading data")

# model
parser.add_argument("--save_path", type=str, default='../../save_models', help="the path of saving model")
parser.add_argument("--load_path", type=str, default='../../save_models/CPFA.npy', help="the path of loading model")

parser.add_argument("--z_dim", type=int, default=200, help="dimensionality of the z latent space")

# optim
parser.add_argument("--num_epochs", type=int, default=100, help="number of epochs of training")

args = parser.parse_args()

# =========================================== Dataset ===================================================================== #
# define transform for dataset and load orginal dataset
# load dataset (AG_NEWS from torchtext)
train_iter, test_iter = AG_NEWS(args.data_path, split=('train', 'test'))
tokenizer = get_tokenizer("basic_english")

# build vocabulary
vocab = build_vocab_from_iterator(map(lambda x: tokenizer(x[1]), train_iter), specials=['<unk>', '<pad>', '<bos>', '<eos>'], special_first=True, max_tokens=5000)
vocab.set_default_index(vocab['<unk>'])
text_processer = Text_Processer(tokenizer=tokenizer, vocab=vocab)

# Get train/test label and data_file(tokens) from data_iter and convert them into clean file
train_files, train_labels = text_processer.file_from_iter(train_iter, tokenizer=tokenizer)
test_files, test_labels = text_processer.file_from_iter(test_iter, tokenizer=tokenizer)

# Take part of dataset for convenience
train_idxs = np.arange(3000)
np.random.shuffle(train_idxs)
train_files = [train_files[i] for i in train_idxs]
train_labels = [train_labels[i] for i in train_idxs]

test_idxs = np.arange(1000)
np.random.shuffle(test_idxs)
test_files = [test_files[i] for i in test_idxs]
test_labels = [test_labels[i] for i in test_idxs]

# ===================================== mode 1, sparse input ====================================== #
# Build batch of word2index
train_sparse_batch, train_labels = text_processer.word_index_from_file(train_files, train_labels, to_sparse=True)
test_sparse_batch, test_labels = text_processer.word_index_from_file(test_files, test_labels, to_sparse=True)
print('Data has been processed!')

# create the model and deploy it on gpu or cpu
model = CPFA(K=args.z_dim, device=args.device)
model.initial(train_sparse_batch, is_sparse=True)  # use the shape of train_data to initialize the params of model

# train and evaluation
train_local_params = model.train(data=train_sparse_batch, is_sparse=True, num_epochs=args.num_epochs)
train_local_params = model.test(data=train_sparse_batch, is_sparse=True, num_epochs=args.num_epochs)
test_local_params = model.test(data=test_sparse_batch, is_sparse=True, num_epochs=args.num_epochs)

# save the model after training
model.save(args.save_path)
# load the model
model.load(args.load_path)

# evaluate the model with classification accuracy
# the demo accuracy can achieve 0.628
train_theta = np.sum(np.sum(train_local_params.W_nk, axis=3), axis=2).T
test_theta = np.sum(np.sum(test_local_params.W_nk, axis=3), axis=2).T
results = ACC(train_theta, test_theta, train_labels, test_labels, 'SVM')


# # Use custom dataset
# DATA = cPickle.load(open("../../dataset/TREC.pkl", "rb"), encoding='iso-8859-1')
#
# data_vab_list = DATA['Vocabulary']
# data_vab_count_list = DATA['Vab_count']
# data_vab_length = DATA['Vab_Size']
# data_label = DATA['Label']
# data_train_list = DATA['Train_Origin']
# data_train_label = np.array(DATA['Train_Label'])
# data_train_split = DATA['Train_Word_Split']
# data_train_list_index = DATA['Train_Word2Index']
# data_test_list = DATA['Test_Origin']
# data_test_label = np.array(DATA['Test_Label'])
# data_test_split = DATA['Test_Word_Split']
# data_test_list_index = DATA['Test_Word2Index']

# train_sparse_batch, train_labels = text_processer.word_index_from_file(data_train_list_index, data_train_label, to_sparse=True)
# test_sparse_batch, test_labels = text_processer.word_index_from_file(data_test_list_index, data_test_label, to_sparse=True)
