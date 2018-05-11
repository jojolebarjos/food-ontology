# -*- coding: utf-8 -*-


import regex as re


# Use simple rules to tokenize text
_token = re.compile(r'\s*(\p{L}+|\d+|\S)', re.UNICODE)
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
