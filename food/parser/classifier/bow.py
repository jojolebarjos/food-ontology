# -*- coding: utf-8 -*-


import collections
import io
import numpy
import os
import pickle
import sklearn.linear_model

from .core import Model
from .vocabulary import Vocabulary


# Basic token-based logistic regression
class NaiveBagOfWordModel(Model):
    def __init__(self, path=None, min_token_count=1):
        self._path = path
        self._vocabulary = Vocabulary(min_token_count)
        self._model = None
        self._labels = None
        
        # Load existing model, if available
        if self._path is not None and os.path.exists(self._path):
            with io.open(self._path, 'rb') as file:
                dump = pickle.load(file)
            self._vocabulary, self._model, self._labels = dump
    
    # Annotate text with current model
    def classify(self, text, verbose=False):
        if self._model is None:
            return None
        features = self._vocabulary.transform([text])
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
        
        # Create vocabulary
        features = self._vocabulary.fit_transform([text for text, _ in samples])
        
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
            dump = (self._vocabulary, model, labels)
            with io.open(self._path, 'wb') as file:
                pickle.dump(dump, file)
        
        # Ready to annotate
        self._model = model
        self._labels = labels  
        
# TODO hierarchy-aware model
