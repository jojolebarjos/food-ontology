# -*- coding: utf-8 -*-


import os
import numpy
import sklearn.metrics
import pycrfsuite

from .dataset import get_pos_dataset
from .text import tokenize, simplify


# Get local directory
HERE = os.path.dirname(os.path.realpath(__file__))
POS_CRFSUITE = os.path.join(HERE, 'pos.crfsuite')


# Generate features for Part-of-Speech tagger
def extract_features(tokens):
  # TODO improve features, especially regarding lemmatization
  # TODO maybe also use embeddings and clusters
  
  # Prepare tokens
  words = [simplify(token) for token in tokens]
  # TODO improve features
  
  # Collect features
  result = []
  for i in range(len(tokens)):
    features = {}
    features['b'] = 1.0
    
    # Previous token
    if i > 0:
      features['-w' + words[i - 1]] = 1.0
    else:
      features['s'] = 1.0
    
    # Current token
    features['w' + words[i]] = 1.0
    
    # Next token
    if i < len(tokens) - 1:
      features['+w' + words[i + 1]] = 1.0
    else:
      features['e'] = 1.0
    
    # Ready
    result.append(features)
  return result


# Train Part-of-Speech tagger
def train():
  
  # Create trainer
  trainer = pycrfsuite.Trainer(verbose=True)
  trainer.set_params({
    'c1': 1.0,
    'c2': 1e-3,
    'max_iterations': 50,
    'feature.possible_transitions': True
  })
  
  # Generate training samples
  for tokens, tags in get_pos_dataset(test=False, oversampling=5):
    features = extract_features(tokens)
    trainer.append(features, tags)
  
  # Train
  trainer.train(POS_CRFSUITE)
  
  # Get trained tagger
  tagger = get_tagger()
  
  # Acquire test samples
  samples = get_pos_dataset(test=True)
  tags = sorted({tag for _, tags in samples for tag in tags})
  tags_to_index = {tag : index for index, tag in enumerate(tags)}
  
  # Evaluate model
  truth = []
  prediction = []
  confusion = numpy.zeros([len(tags), len(tags)], dtype=numpy.int32)
  for tokens, true_tags in samples:
    predicted_tags = tagger(tokens)
    truth.extend(true_tags)
    prediction.extend(predicted_tags)
  
  # Report accuracy
  f1 = sklearn.metrics.f1_score(truth, prediction, average='macro')
  print('F-1: %6.6f' % f1)
  
  # TODO print infos
  # TODO test model on each corpus (separately)


# Create Part-of-Speech tagger
def get_tagger():
  try:
    tagger = pycrfsuite.Tagger()
    tagger.open(POS_CRFSUITE)
    def tag(tokens):
      features = extract_features(tokens)
      return tagger.tag(features)
  except:
    def tag(tokens):
      return ['X'] * len(tokens)
  return tag
