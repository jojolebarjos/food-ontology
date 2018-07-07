# -*- coding: utf-8 -*-


import collections
import hunspell
import io
import numpy
import os
import pickle
import regex
import scipy.sparse
import sklearn.linear_model
import unidecode
from .core import Model


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


# Basic token-based logistic regression
class NaiveBagOfWordModel(Model):
    def __init__(self, path=None, min_token_count=1):
        self._path = path
        self._min_token_count = min_token_count
        self._vocabulary = None
        self._model = None
        self._labels = None
        self._token_regex = regex.compile(r'\s*(?:(\p{L}+)|.)', regex.UNICODE)
        self._hunspell = hunspell.Hunspell()
        
        # Load existing model, if available
        if self._path is not None and os.path.exists(self._path):
            with io.open(self._path, 'rb') as file:
                dump = pickle.load(file)
            self._vocabulary, self._model, self._labels = dump
            self._vocabulary_map = {token : index for index, token in enumerate(self._vocabulary)}
    
    # Tokenize and simplify in a language-agnostic manner
    def _tokenize(self, text):
        tokens = []
        index = 0
        while True:
            match = self._token_regex.match(text, index)
            if match is None:
                return tokens
            index = match.end(0)
            word = match.group(1)
            if word is not None:
                token = word.lower()
                token = latinize(token)
                lemmas = self._hunspell.stem(token)
                lemma = lemmas[0] if len(lemmas) > 0 else token
                tokens.append(lemma)
    
    # Annotate text with current model
    def classify(self, text, verbose=False):
        if self._model is None:
            return None
        tokens = self._tokenize(text)
        features = scipy.sparse.dok_matrix((1, len(self._vocabulary)), dtype=numpy.float32)
        for token in tokens:
            j = self._vocabulary_map.get(token)
            if j is not None:
                features[0, j] = 1.0
        if verbose:
            probabilities = self._model.predict_proba(features)[0]
            probabilities = dict(zip(self._labels, probabilities))
            return probabilities
        output = self._model.predict(features)[0]
        return self._labels[output]
    
    # Train whole model from given samples
    def train(self, samples):
        
        # Handle multi labels as separate samples
        samples = [(text, label) for text, labels in samples for label in labels]
        
        # Tokenize samples
        tokenized_samples = [self._tokenize(text) for text, _ in samples]
        
        # Create vocabulary
        vocabulary = collections.Counter(token for tokens in tokenized_samples for token in tokens)
        vocabulary = [token for token, count in vocabulary.items() if count >= self._min_token_count]
        vocabulary_map = {token : index for index, token in enumerate(vocabulary)}
        # TODO maybe consider bigrams?
        
        # Build feature matrix
        features = scipy.sparse.dok_matrix((len(samples), len(vocabulary)), dtype=numpy.float32)
        for i, tokens in enumerate(tokenized_samples):
            for token in tokens:
                j = vocabulary_map.get(token)
                if j is not None:
                    # TODO maybe use frequency-based weighting
                    features[i, j] = 1.0
        
        # Create tag set
        # TODO handle multi-labels at some point (e.g. need to split comma)
        labels = list({label for _, label in samples})
        label_map = {label : index for index, label in enumerate(labels)}
        
        # Build output vector
        outputs = numpy.empty(len(samples), numpy.int32)
        for i, (_, label) in enumerate(samples):
            outputs[i] = label_map[label]
        
        # Create and train model
        model = sklearn.linear_model.LogisticRegression(
            solver = 'lbfgs',
            multi_class = 'multinomial',
            n_jobs = 1,
            max_iter = 100
        )
        model.fit(features, outputs)
        
        # Export model
        if self._path is not None:
            dump = (vocabulary, model, labels)
            with io.open(self._path, 'wb') as file:
                pickle.dump(dump, file)
        
        # Ready to annotate
        self._vocabulary = vocabulary
        self._vocabulary_map = vocabulary_map
        self._model = model
        self._labels = labels  
        
# TODO hierarchy-aware model
