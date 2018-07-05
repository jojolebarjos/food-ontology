# -*- coding: utf-8 -*-


import collections
import io
import numpy
import os
import pickle
import regex
import scipy.sparse
import sklearn.linear_model
from .core import Model


# Simple token pattern
token_regex = regex.compile(r'\s*(?:(\p{L}+)|.)', regex.UNICODE)

# Tokenize and simplify in a language-agnostic manner
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
            # TODO apply basic stemming strategy?
            token = word.lower()
            tokens.append(token)


# Basic token-based logistic regression
class NaiveBagOfWordModel(Model):
    def __init__(self, path=None, min_token_count=1):
        self._path = path
        self._min_token_count = min_token_count
        self._vocabulary = None
        self._model = None
        self._labels = None
        
        # Load existing model, if available
        if self._path is not None and os.path.exists(self._path):
            with io.open(self._path, 'rb') as file:
                dump = pickle.load(file)
            self._vocabulary, self._model, self._labels = dump
            self._vocabulary_map = {token : index for index, token in enumerate(self._vocabulary)}
    
    # Annotate text with current model
    def classify(self, text, verbose=False):
        if self._model is None:
            return None
        tokens = tokenize(text)
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
        tokenized_samples = [tokenize(text) for text, _ in samples]
        
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
            n_jobs = 1
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
