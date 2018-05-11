# -*- coding: utf-8 -*-


import os
import io
#import pandas

from .text import tokenize


# Get local directory
HERE = os.path.dirname(os.path.realpath(__file__))
TRAIN_CONLLU = os.path.join(HERE, 'UD_English', 'en-ud-train.conllu')
TEST_CONLLU = os.path.join(HERE, 'UD_English', 'en-ud-test.conllu')
ENTITY_TRAIN_TXT = os.path.join(HERE, 'entity.train.txt')
ENTITY_TEST_TXT = os.path.join(HERE, 'entity.test.txt')


# Import tab separated dataset
def from_tab(file):
  samples = []
  text = None
  tokens = []
  pos_tags = []
  entity_tags = []
  
  # For each line
  for line in file:
    line = line.rstrip()
    
    # Empty line marks end-of-sample
    if len(line) == 0:
      if len(tokens) > 0:
        sample = (text, tokens, pos_tags, entity_tags)
        samples.append(sample)
      text = None
      tokens = []
      pos_tags = []
      entity_tags = []
      continue
    
    # Keep comments as text reference
    if line[0] == '#':
      text = line[2:]
      continue
    
    # Accumulate tokens
    token, pos_tag, entity_tag = line.split('\t')
    tokens.append(token)
    pos_tags.append(pos_tag)
    entity_tags.append(entity_tag)
  
  # Ready
  return samples


# Import CoNLL-U Part-of-Speech dataset, with retokenization
def from_conllu(file):
  samples = []
  text = ''
  text_tags = []
  
  # For each line
  for line in file:
    line = line.rstrip()
    
    # Empty line marks end-of-sample
    if len(line) == 0:
      tokens = []
      tags = []
      for token, start, end in tokenize(text):
        tag = text_tags[start]
        tokens.append(token)
        tags.append(tag)
      if len(tokens) > 0:
        sample = (tokens, tags)
        samples.append(sample)
      text = ''
      text_tags = []
      continue
    
    # Ignore comments
    if line[0] == '#':
      continue
    
    # Acquire token info
    parts = line.split('\t')
    token = parts[1]
    tag = parts[3]
    misc = parts[9].split('|')
    space_after = 'SpaceAfter=No' not in misc
    
    # Accumulate text
    if space_after:
      token += ' '
    text += token
    text_tags.extend([tag] * len(token))
  
  # Ready
  return samples


# Import sentence dataset
def get_custom_dataset(test=False):
  path = ENTITY_TEST_TXT if test else ENTITY_TRAIN_TXT
  if not os.path.exists(path):
    samples = []
  else:
    with io.open(path, 'r', newline='\n', encoding='utf-8') as file:
      samples = from_tab(file)
  return samples


# Import Part-of-Speech dataset, based on custom sentences and Universal Dependencies
def get_pos_dataset(test=False, oversampling=1):
  
  # Load Universal Dependencies
  path = TEST_CONLLU if test else TRAIN_CONLLU
  with io.open(path, 'r', newline='\n', encoding='utf-8') as file:
    samples_ud = from_conllu(file)
  
  # Load custom sentences
  samples_custom = [(tokens, pos_tags) for _, tokens, pos_tags, _ in get_custom_dataset(test)]
  
  # Combine
  return samples_ud + samples_custom * oversampling


# Import entity dataset, based on custom sentences only
def get_entity_dataset(test=False):
  samples = get_custom_dataset(test)
  return samples
