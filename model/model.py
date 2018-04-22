# -*- coding: utf-8 -*-


import os
import io
import regex as re
import pycrfsuite


# Get local directory
HERE = os.path.dirname(os.path.realpath(__file__))
POS_CRFSUITE = os.path.join(HERE, 'pos.crfsuite')


# Use simple rules to tokenize text
_token = re.compile(r'\s*((?:\p{L}|\d)+|\S)', re.UNICODE)
def tokenize(text):
  pos = 0
  while True:
    match = _token.match(text, pos)
    if not match:
      break
    token = match.group(1)
    start = match.start(1)
    end = match.end(1)
    yield token, start, end
    pos = end


# Simplify tokens
_digits = re.compile(r'\d+', re.UNICODE)
def simplify(token):
  token = token.lower()
  token = _digits.sub('0', token)
  return token


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


# Import tab separated dataset
def from_tab(file):
  samples = []
  tokens = []
  pos_tags = []
  food_tags = []
  
  # For each line
  for line in file:
    line = line.rstrip()
    
    # Empty line marks end-of-sample
    if len(line) == 0:
      if len(tokens) > 0:
        sample = (tokens, pos_tags, food_tags)
        samples.append(sample)
      tokens = []
      pos_tags = []
      food_tags = []
      continue
    
    # Ignore comments
    if line[0] == '#':
      continue
    
    # Accumulate tokens
    token, pos_tag, food_tag = line.split('\t')
    tokens.append(token)
    pos_tags.append(pos_tag)
    food_tags.append(food_tag)
  
  # Ready
  return samples


# Generate features for Part-of-Speech tagger
def pos_extract_features(tokens):
  
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
def pos_train():
  
  # Import CoNLL-U Part-of-Speech file
  path = os.path.join(HERE, 'UD_English', 'en-ud-train.conllu')
  with io.open(path, 'r', newline='\n', encoding='utf-8') as file:
    samples = from_conllu(file)
  
  # Import specialized Part-of-Speech file, if any
  path = os.path.join(HERE, 'entity.train.txt')
  if os.path.exists(path):
    with io.open(path, 'r', newline='\n', encoding='utf-8') as file:
      for tokens, pos_tags, food_tags in from_tab(path):
        sample = (tokens, pos_tags)
        samples.append(sample)
  
  # Create trainer
  trainer = pycrfsuite.Trainer(verbose=True)
  trainer.set_params({
    'c1': 1.0,
    'c2': 1e-3,
    'max_iterations': 50,
    'feature.possible_transitions': True
  })
  
  # Generate training samples
  for tokens, tags in samples:
    features = pos_extract_features(tokens)
    trainer.append(features, tags)
  
  # Train
  trainer.train(POS_CRFSUITE)
  
  # TODO print infos
  # TODO test model on each corpus (separately)


# Create Part-of-Speech tagger
def get_pos_tagger():
  tagger = pycrfsuite.Tagger()
  tagger.open(POS_CRFSUITE)
  def tag(tokens):
    features = pos_extract_features(tokens)
    return tagger.tag(features)
  return tag


# Generate features for food entity tagger
def food_extract_features(tokens):
  # TODO
  pass


# Train food entity tagger
def food_train():
  # TODO
  pass


# Create food entity tagger
def get_food_tagger():
  # TODO
  pass


# Generate features for ingredient classifier
def ingredient_extract_features(tokens):
  # TODO
  pass


# Train ingredient classifier
def ingredient_train():
  # TODO
  pass


# Create ingredient classifier
def get_ingredient_classifier():
  # TODO
  pass
