# -*- coding: utf-8 -*-


import collections
import io
import numpy
import os
import pickle
import sklearn.linear_model

from .core import Model
from .vocabulary import Vocabulary


# Simple classifier
class LogisticNode:
    def __init__(self):
        self._labels = None
        self._mask = None
        self._model = None
    
    # Train model from given samples
    def fit(self, features, labels):
        
        # Wipe old model
        self._labels = None
        self._mask = None
        self._model = None
        
        # Create tag set
        self._labels = sorted(set(labels))
        label_map = {label : index for index, label in enumerate(self._labels)}
        
        # Handle naive tagset
        if len(self._labels) == 0:
            return
        if len(self._labels) == 1:
            self._labels = self._labels[0]
            return
        
        # Build output vector
        outputs = numpy.empty(len(labels), numpy.int32)
        for i, label in enumerate(labels):
            outputs[i] = label_map[label]
        
        # Build input mask (to avoid fitting unobserved words)
        _, self._mask = (features.sum(axis=0) > 0).nonzero()
        features = features[:, self._mask]
        
        # Fit model
        # TODO remove warning related to n_jobs
        model = sklearn.linear_model.LogisticRegression(
            solver = 'lbfgs',
            multi_class = 'multinomial',
            n_jobs = 1,
            max_iter = 100
        )
        model.fit(features, outputs)
        self._model = model
    
    # Predict class probabilities of a single sample
    def predict(self, features):
        if self._labels is None:
            return None
        if type(self._labels) is not list:
            return self._labels
        features = features[:, self._mask]
        probabilities = self._model.predict_proba(features)
        return [dict(zip(self._labels, result)) for result in probabilities]


# Flat classifier
class FlatArchitecture:
    def __init__(self, min_token_count=1):
        self._node = LogisticNode()
        self._vocabulary = Vocabulary(min_token_count)
    
    def fit(self, texts, labels):
        features = self._vocabulary.fit_transform(texts)
        self._node.fit(features, labels)
    
    # Predict class probabilities of a single sample
    def predict(self, text):
        features = self._vocabulary.transform([text])
        return self._node.predict(features)[0]


# TODO hierarchy-aware model


# Basic token-based logistic regression
class NaiveBagOfWordModel(Model):
    def __init__(self, path=None, min_token_count=1):
        self._path = path
        self._architecture = FlatArchitecture(min_token_count)
        if self._path is not None and os.path.exists(self._path):
            with io.open(self._path, 'rb') as file:
                self._architecture = pickle.load(file)
    
    # Annotate text with current model
    def classify(self, text):
        return self._architecture.predict(text)
    
    # Train whole model from given samples
    def train(self, samples):
        
        # Handle multi labels as separate samples
        # TODO handle multi-labels at some point (e.g. need to split comma)
        samples = [(text, label) for text, labels in samples for label in labels]
        
        # Create and train model
        self._architecture.fit(*zip(*samples))
        
        # Export model
        if self._path is not None:
            with io.open(self._path, 'wb') as file:
                pickle.dump(self._architecture, file)
