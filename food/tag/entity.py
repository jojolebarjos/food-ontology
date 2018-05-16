# -*- coding: utf-8 -*-


import os
import pycrfsuite

from .dataset import get_entity_dataset
from .pos import extract_features as extract_pos_features
from .pos import get_tagger as get_pos_tagger


# Get local directory
HERE = os.path.dirname(os.path.realpath(__file__))
ENTITY_CRFSUITE = os.path.join(HERE, 'entity.crfsuite')


# Generate features for food entity tagger
def extract_features(tokens, pos_tags):
  result = extract_pos_features(tokens)
  for i in range(len(tokens)):
    features = result[i]
    if i > 0:
      features['-p' + pos_tags[i - 1]] = 1.0
    features['p' + pos_tags[i]] = 1.0
    if i < len(tokens) - 1:
      features['+p' + pos_tags[i + 1]] = 1.0
  return result


# Train food entity tagger
def train(max_iterations=50):
  
  # Import specialized food entity file
  samples = get_entity_dataset(test=False)
  
  # Create trainer
  trainer = pycrfsuite.Trainer(verbose=True)
  trainer.set_params({
    'c1': 1.0,
    'c2': 1e-3,
    'max_iterations': max_iterations,
    'feature.possible_transitions': True
  })
  
  # Generate training samples
  for _, tokens, pos_tags, entity_tags in samples:
    features = extract_features(tokens, pos_tags)
    trainer.append(features, entity_tags)
  
  # Train
  trainer.train(ENTITY_CRFSUITE)
  
  # TODO print infos
  # TODO test model


# Create food entity tagger
def get_tagger(pos_tagger=None):
  if pos_tagger is None:
    pos_tagger = get_pos_tagger()
  try:
    tagger = pycrfsuite.Tagger()
    tagger.open(ENTITY_CRFSUITE)
    def tag(tokens, pos_tags=None):
      if pos_tags is None:
        pos_tags = pos_tagger(tokens)
      features = extract_features(tokens, pos_tags)
      return tagger.tag(features)
  except:
    def tag(tokens, pos_tags=None):
      return ['O'] * len(tokens)
  return tag


# Extract BIO entities as spans
def entity_ranges(tags):
  entities = []
  index = 0
  while index < len(tags):
    if '-' in tags[index]:
      tag = tags[index][2:]
      start = index
      index += 1
      while index < len(tags) and tags[index] == 'I-' + tag:
        index += 1
      entity = (tag, start, index)
      entities.append(entity)
    else:
      index += 1
  return entities
