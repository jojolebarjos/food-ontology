# -*- coding: utf-8 -*-


import collections
import hunspell
import numpy
import regex
import scipy.sparse
import unidecode


# Get supported character set
LATIN_1_CHARACTERS = set(bytes((byte,)).decode('latin-1') for byte in range(256))

# Convert character to latin-1
def latinize_char(char):
    if char in LATIN_1_CHARACTERS:
        return char
    codepoint = ord(char)
    if codepoint > 0xeffff:
        return ''
    if 0xd800 <= codepoint and codepoint <= 0xdfff:
        return ''
    section = codepoint >> 8
    position = codepoint % 256
    try:
        table = unidecode.Cache[section]
    except KeyError:
        try:
            mod = __import__('unidecode.x%03x' % section, globals(), locals(), ['data'])
            unidecode.Cache[section] = table = mod.data
        except ImportError:
            unidecode.Cache[section] = table = None
        if table and len(table) > position:
            return table[position]
    return ''

# Convert string to latin-1
def latinize(text):
    return ''.join(latinize_char(char) for char in text)


# Instanciate Hunspell helper
english_hunspell = hunspell.Hunspell()


# Tokenization regex
token_regex = regex.compile(r'\s*(?:(\p{L}+)|.)', regex.UNICODE)

# Tokenize and simplify text
def tokenize(text):
    tokens = []
    index = 0
    while True:
        match = token_regex.match(text, index)
        if match is None:
            return tokens
        index = match.end(0)
        word = match.group(1)
        if word is not None:
            token = word.lower()
            token = latinize(token)
            lemmas = english_hunspell.stem(token)
            lemma = lemmas[0] if len(lemmas) > 0 else token
            tokens.append(lemma)


# Vocabulary container
class Vocabulary:
    def __init__(self, min_token_count=1):
        self._min_token_count = min_token_count
        self._vocabulary = []
        self._vocabulary_map = {}
    
    # Tokenize samples
    def _tokenize(self, texts):
        return [tokenize(text) for text in texts]
    
    # Fit tokens
    def _fit(self, tokenized_texts):
        vocabulary = collections.Counter(token for tokens in tokenized_texts for token in tokens)
        self._vocabulary = [token for token, count in vocabulary.items() if count >= self._min_token_count]
        self._vocabulary_map = {token : index for index, token in enumerate(self._vocabulary)}
    
    # Transform tokens
    def _transform(self, tokenized_texts):
        features = scipy.sparse.dok_matrix((len(tokenized_texts), len(self._vocabulary)), dtype=numpy.float32)
        for i, tokens in enumerate(tokenized_texts):
            for token in tokens:
                j = self._vocabulary_map.get(token)
                if j is not None:
                    # TODO maybe use frequency-based weighting
                    features[i, j] = 1.0
        return features
    
    # Create vocabulary from samples and return one-hot encoded data
    def fit_transform(self, texts):
        tokenized_texts = self._tokenize(texts)
        self._fit(tokenized_texts)
        return self._transform(tokenized_texts)
    
    # Fit-only version
    def fit(self, texts):
        tokenized_texts = self._tokenize(texts)
        self._fit(tokenized_texts)
    
    # Transform-only version
    def transform(self, texts):
        tokenized_texts = self._tokenize(texts)
        return self._transform(tokenized_texts)


# Tagset container
# TODO
