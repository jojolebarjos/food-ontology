# -*- coding: utf-8 -*-


import os
import io
import regex as re
import pycrfsuite
import random


# Get local directory
HERE = os.path.dirname(os.path.realpath(__file__))
POS_CRFSUITE = os.path.join(HERE, 'pos.crfsuite')
FOOD_CRFSUITE = os.path.join(HERE, 'food.crfsuite')
INGREDIENT_CRFSUITE = os.path.join(HERE, 'ingredient.crfsuite')


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
  text = None
  tokens = []
  pos_tags = []
  food_tags = []
  
  # For each line
  for line in file:
    line = line.rstrip()
    
    # Empty line marks end-of-sample
    if len(line) == 0:
      if len(tokens) > 0:
        sample = (text, tokens, pos_tags, food_tags)
        samples.append(sample)
      text = None
      tokens = []
      pos_tags = []
      food_tags = []
      continue
    
    # Keep comments as text reference
    if line[0] == '#':
      text = line[2:]
      continue
    
    # Accumulate tokens
    token, pos_tag, food_tag = line.split('\t')
    tokens.append(token)
    pos_tags.append(pos_tag)
    food_tags.append(food_tag)
  
  # Ready
  return samples


# Import row dataset (sentence fragments and label)
def from_row(file):
  samples = []
  for line in file:
    line = line.rstrip()
    if len(line) == 0 or line[0] == '#':
      continue
    parts = line.split('\t')
    text = parts[0]
    label = parts[1]
    tokens = [token for token, _, _ in tokenize(text)]
    sample = (tokens, label)
    samples.append(sample)
  return samples


# Generate features for Part-of-Speech tagger
def pos_extract_features(tokens):
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
def pos_train():
  
  # Import CoNLL-U Part-of-Speech file
  path = os.path.join(HERE, 'UD_English', 'en-ud-train.conllu')
  with io.open(path, 'r', newline='\n', encoding='utf-8') as file:
    samples = from_conllu(file)
  
  # Import specialized Part-of-Speech file, if any
  path = os.path.join(HERE, 'entity.train.txt')
  if os.path.exists(path):
    with io.open(path, 'r', newline='\n', encoding='utf-8') as file:
      for _, tokens, pos_tags, food_tags in from_tab(file):
        sample = (tokens, pos_tags)
        for _ in range(5):
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
  try:
    tagger = pycrfsuite.Tagger()
    tagger.open(POS_CRFSUITE)
    def tag(tokens):
      features = pos_extract_features(tokens)
      return tagger.tag(features)
  except:
    def tag(tokens):
      return ['X'] * len(tokens)
  return tag


# Generate features for food entity tagger
def food_extract_features(tokens, pos_tags):
  result = pos_extract_features(tokens)
  for i in range(len(tokens)):
    features = result[i]
    if i > 0:
      features['-p' + pos_tags[i - 1]] = 1.0
    features['p' + pos_tags[i]] = 1.0
    if i < len(tokens) - 1:
      features['+p' + pos_tags[i + 1]] = 1.0
  return result


# Train food entity tagger
def food_train():
  
  # Import specialized food entity file
  path = os.path.join(HERE, 'entity.train.txt')
  with io.open(path, 'r', newline='\n', encoding='utf-8') as file:
    samples = from_tab(file)
  
  # Create trainer
  trainer = pycrfsuite.Trainer(verbose=True)
  trainer.set_params({
    'c1': 1.0,
    'c2': 1e-3,
    'max_iterations': 50,
    'feature.possible_transitions': True
  })
  
  # Generate training samples
  for _, tokens, pos_tags, food_tags in samples:
    features = food_extract_features(tokens, pos_tags)
    trainer.append(features, food_tags)
  
  # Train
  trainer.train(FOOD_CRFSUITE)
  
  # TODO print infos
  # TODO test model


# Create food entity tagger
def get_food_tagger(pos_tagger=None):
  if pos_tagger is None:
    pos_tagger = get_pos_tagger()
  try:
    tagger = pycrfsuite.Tagger()
    tagger.open(FOOD_CRFSUITE)
    def tag(tokens, pos_tags=None):
      if pos_tags is None:
        pos_tags = pos_tagger(tokens)
      features = food_extract_features(tokens, pos_tags)
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


# Generate features for ingredient classifier
def ingredient_extract_features(tokens):
  # TODO improve features, especially regarding lemmatization
  # TODO maybe also use embeddings and clusters
  # TODO maybe use PoS tags?
  # TODO also consider bigrams and trigrams
  features = [simplify(token) for token in tokens]
  return features


# Train ingredient classifier
def ingredient_train():
  
  # Import specialized ingredient file
  path = os.path.join(HERE, 'ingredient.train.txt')
  with io.open(path, 'r', newline='\n', encoding='utf-8') as file:
    samples = from_row(file)
  
  # Create trainer
  trainer = pycrfsuite.Trainer(verbose=True)
  trainer.set_params({
    'c1': 1.0,
    'c2': 1e-3,
    'max_iterations': 50,
    'feature.possible_transitions': True
  })
  
  # Generate training samples
  for tokens, label in samples:
    features = ingredient_extract_features(tokens)
    trainer.append([features], [label])
  
  # Train
  trainer.train(INGREDIENT_CRFSUITE)
  
  # TODO print infos
  # TODO test model


# Create ingredient classifier
def get_ingredient_classifier():
  # TODO ingredient classification should use ontology to improve accuracy
  try:
    tagger = pycrfsuite.Tagger()
    tagger.open(INGREDIENT_CRFSUITE)
    def tag(tokens):
      features = ingredient_extract_features(tokens)
      return tagger.tag([features])[0]
  except:
    def tag(tokens, pos_tags=None):
      return 'misc'
  return tag


# Generate additional samples for Part-of-Speech and food entities
def food_generate(input_path, output_path, count=50):
  
  # Acquire raw lines
  with io.open(input_path, 'r', newline='\n', encoding='utf-8') as file:
    lines = {line.strip() for line in file}
  
  # Acquire existing lines
  with io.open(os.path.join(HERE, 'entity.train.txt'), 'r', newline='\n', encoding='utf-8') as file:
    existing_lines = {line[1:].strip() for line in file if line.startswith('#')}
  
  # Select random samples
  lines.difference_update(existing_lines)
  lines = list(lines)
  random.shuffle(lines)
  lines = lines[:count]
  
  # Automatically annotate
  pos_tagger = get_pos_tagger()
  food_tagger = get_food_tagger(pos_tagger)
  with io.open(output_path, 'w', newline='\n', encoding='utf-8') as file:
    file.write('\n')
    for line in lines:
      file.write('# ' + line + '\n')
      tokens = [token for token, _, _ in tokenize(line)]
      pos_tags = pos_tagger(tokens)
      food_tags = food_tagger(tokens, pos_tags)
      for token, pos_tag, food_tag in zip(tokens, pos_tags, food_tags):
        file.write(token + '\t' + pos_tag + '\t' + food_tag + '\n')
      file.write('\n')


# Generate additional samples for ingredient classification
def ingredient_generate(input_path, output_path):
  
  # Use specified tab dataset (ground truth or predicted)
  with io.open(input_path, 'r', newline='\n', encoding='utf-8') as file:
    samples = from_tab(file)
  
  # Extract items
  ingredient_classifier = get_ingredient_classifier()
  with io.open(output_path, 'w', newline='\n', encoding='utf-8') as file:
    file.write('\n')
    for text, tokens, _, food_tags in samples:
      entities = [(start, end) for tag, start, end in entity_ranges(food_tags) if tag == 'ITEM']
      if len(entities) > 0:
        file.write('# ' + text + '\n')
        for start, end in entities:
          tag = ingredient_classifier(tokens[start : end])
          file.write(' '.join(tokens[start : end]) + '\t' + tag + '\n')
        file.write('\n')
