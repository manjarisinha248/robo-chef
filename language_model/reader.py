
# This code is recycled from the PTB Language Model tutorial for TensorFlow. The
# original copyright can be found below.

# ==============================================================================
# Copyright 2015 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

# pylint: disable=unused-import,g-bad-import-order

"""Utilities for parsing PTB-style text files."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import collections
import os
import sys
import time

import tensorflow.python.platform

import numpy as np
from six.moves import xrange  # pylint: disable=redefined-builtin
import tensorflow as tf

from tensorflow.python.platform import gfile

import data_preprocess as dpp


def _read_words(filename):
  with gfile.GFile(filename, "r") as f:
    return f.read().replace("\n", "<eos>").split()


def _build_vocab(filename):
  data = _read_words(filename)

  counter = collections.Counter(data)
  count_pairs = sorted(counter.items(), key=lambda x: -x[1])

  words, _ = list(zip(*count_pairs))
  word_to_id = dict(zip(words, range(1,len(words)+1)))

  return word_to_id


def _file_to_word_ids(filename, word_to_id):
  data = _read_words(filename)
  return [word_to_id.get(word, 0) for word in data]


def get_raw_training_data(data_path=None):
  """Load raw data from data directory "data_path".

  Reads PTB-style text files, converts strings to integer ids,
  and performs mini-batching of the inputs.

  Args:
    data_path: string path to the directory where the data files exist.

  Returns:
    tuple (train_data, valid_data, vocabulary_size, word_to_id).
  """

  train_path = os.path.join(data_path, "lm.train.txt")
  valid_path = os.path.join(data_path, "lm.valid.txt")
  # test_path = os.path.join(data_path, "lm.test.txt")

  word_to_id = _build_vocab(train_path)
  train_data = _file_to_word_ids(train_path, word_to_id)
  valid_data = _file_to_word_ids(valid_path, word_to_id)
  # test_data = _file_to_word_ids(test_path, word_to_id)
  vocabulary_size = len(word_to_id) + 1
  return train_data, valid_data, vocabulary_size, word_to_id

def process_review_segments(review_segments, word_to_id):
  processed_segments = dpp.numSymbolSubstitutions(dpp.processesPuntuation(review_segments))
  segments_data = []
  for segment in processed_segments:
    seg_data = [word_to_id.get(word, 0) for word in segment.replace("\n", "<eos>").split()]
    segments_data.append(seg_data)

  return segments_data

def data_iterator(raw_data, batch_size, num_steps):
  """Iterate on the raw PTB-style data.

  This generates batch_size pointers into the raw data, and allows
  minibatch iteration along these pointers.

  Args:
    raw_data: one of the raw data outputs from get_raw_training_data.
    batch_size: int, the batch size.
    num_steps: int, the number of unrolls.

  Yields:
    Pairs of the batched data, each a matrix of shape [batch_size, num_steps].
    The second element of the tuple is the same data time-shifted to the
    right by one.

  Raises:
    ValueError: if batch_size or num_steps are too high.
  """
  raw_data = np.array(raw_data, dtype=np.int32)

  data_len = len(raw_data)
  batch_len = data_len // batch_size
  data = np.zeros([batch_size, batch_len], dtype=np.int32)
  for i in range(batch_size):
    data[i] = raw_data[batch_len * i:batch_len * (i + 1)]

  epoch_size = (batch_len - 1) // num_steps

  if epoch_size == 0:
    raise ValueError("epoch_size == 0, decrease batch_size or num_steps")

  for i in range(epoch_size):
    x = data[:, i*num_steps:(i+1)*num_steps]
    y = data[:, i*num_steps+1:(i+1)*num_steps+1]
    yield (x, y)

