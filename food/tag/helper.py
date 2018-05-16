# -*- coding: utf-8 -*-


import os
import io
import collections
import random
import pandas

from .text import tokenize
from .pos import get_tagger as get_pos_tagger
from .entity import get_tagger as get_entity_tagger


# Get local directory
HERE = os.path.dirname(os.path.realpath(__file__))


# Dummy pipeline used mostly for debug
def get_debug_tagger():
  pos_tagger = get_pos_tagger()
  entity_tagger = get_entity_tagger(pos_tagger)
  def tag(text):
    tokens = [token for token, _, _ in tokenize(text)]
    pos_tags = pos_tagger(tokens)
    entity_tags = entity_tagger(tokens, pos_tags)
    return ' '.join('%s/%s/%s' % x for x in zip(tokens, pos_tags, entity_tags))
  return tag


# Generate additional samples for Part-of-Speech and food entities
def generate_entities(input_path, output_path, count=50, by_frequency=True):
  
  # Acquire existing lines
  with io.open(os.path.join(HERE, 'entity.train.txt'), 'r', newline='\n', encoding='utf-8') as file:
    existing_lines = {line[1:].strip() for line in file if line.startswith('#')}
  
  # Acquire raw lines
  lines = collections.Counter()
  with io.open(input_path, 'r', newline='\n', encoding='utf-8') as file:
    for line in file:
      line = line.strip()
      if line not in existing_lines:
        lines[line] += 1
  
  # Select random samples
  # TODO add option to output most common lines
  lines = [line for line, _ in lines.most_common()]
  if not by_frequency:
    random.shuffle(lines)
  lines = lines[:count]
  
  # Automatically annotate
  pos_tagger = get_pos_tagger()
  entity_tagger = get_entity_tagger(pos_tagger)
  with io.open(output_path, 'w', newline='\n', encoding='utf-8') as file:
    file.write('\n')
    for line in lines:
      file.write('# text = ' + line + '\n')
      tokens = [token for token, _, _ in tokenize(line)]
      pos_tags = pos_tagger(tokens)
      entity_tags = entity_tagger(tokens, pos_tags)
      for index, (token, pos_tag, entity_tag) in enumerate(zip(tokens, pos_tags, entity_tags)):
        file.write('%d\t%s\t%s\t%s\n' % (index + 1, token, pos_tag, entity_tag))
      file.write('\n')


# Convert tab-separated file to Excel file
def to_excel(input_path, output_path):
  data = pandas.read_csv(input_path, encoding='utf-8', delimiter='\t', quoting=3, skip_blank_lines=False, keep_default_na=False, header=None, names=['index', 'token', 'pos', 'entity'], dtype=object)
  data.to_excel(output_path, index=False, header=False)


# Convert Excel file to tab-separated file
def to_tab(input_path, output_path):
  data = pandas.read_excel(input_path, keep_default_na=False, header=None, names=['index', 'token', 'pos', 'entity'], dtype=object)
  text = io.StringIO()
  data.to_csv(text, index=False, header=False, sep='\t', doublequote=False)
  text.seek(0)
  text = text.read()
  with io.open(output_path, 'w', newline='\n', encoding='utf-8') as file:
    for line in text.split('\n'):
      file.write(line.rstrip())
      file.write('\n')
