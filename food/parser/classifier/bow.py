# -*- coding: utf-8 -*-


import asyncio
import collections
import io
import numpy
import os
import pickle
import sklearn.feature_extraction.text
import sklearn.linear_model
import sklearn.pipeline
import sklearn.preprocessing
import sklearn_hierarchical.classifier
from tqdm import tqdm

from .core import Classifier
from ..text import tokenize


# Convert a dictionary of list (i.e. parent to children mapping)
class HierarchyEncoder:
    def __init__(self, adjacency, root='<root>'):
        
        # Extract labels
        labels = set(adjacency.keys())
        for children in adjacency.values():
            labels.update(children)
        if root in labels:
            labels.remove(root)
        label_list = [root] + sorted(labels)
        label_map = {label : index for index, label in enumerate(label_list)}
        
        # Find parents
        ascendants = collections.defaultdict(set)
        descendants = collections.defaultdict(set)
        for parent, children in adjacency.items():
            parent = label_map[parent]
            for child in children:
                child = label_map[child]
                ascendants[child].add(parent)
                descendants[parent].add(child)
        
        # Make sure there is only one root
        for child, parents in ascendants.items():
            if child != 0 and 0 not in ascendants:
                parents.add(0)
                descendants[0].add(child)
        
        # Keep relevant information
        self.label_list = label_list
        self.label_map = label_map
        self.ascendants = ascendants
        self.descendants = descendants


# Scikit-Learn container
class Model:
    def __init__(self, hierarchical=False):
        self._hierarchy = None
        self._pipeline = None
        self._hierarchical = hierarchical
    
    # Apply classification on a single sample
    def classify(self, text):
        if self._pipeline is None:
            return {}
        probabilities = self._pipeline.predict_proba([text])[0]
        classes = self._pipeline.steps[-1][1].classes_
        result = {self._hierarchy.label_list[classes[i]] : probability for i, probability in enumerate(probabilities)}
        return result
    
    # Use samples to train a model from scratch
    def train(self, samples, hierarchy):
        
        # Split multilabels into separate samples
        samples = [(text, label) for text, labels in samples for label in labels]
        X, y = zip(*samples)
        
        # Encode labels
        y = [hierarchy.label_map[i] for i in y]
        
        # Convert words to boolean arrays
        vectorizer = sklearn.feature_extraction.text.CountVectorizer(
            tokenizer = tokenize,
            # TODO ngram_range = (1, 1),
            # TODO stop_words = [...],
            binary = True,
            dtype = numpy.int32
        )
        
        # If hierarchical classifier is requested, use dedicated package
        print(self._hierarchical)
        if self._hierarchical:
            # TODO stopping_criteria provides suboptimal quality
            classifier = sklearn_hierarchical.classifier.HierarchicalClassifier(
                class_hierarchy = hierarchy.descendants,
                root = 0,
                prediction_depth = 'nmlnp',
                stopping_criteria = 0.1,
                progress_wrapper = tqdm
            )
        
        # Otherwise, use a single logistic regression
        else:
            classifier = sklearn.linear_model.LogisticRegression(
                solver = 'lbfgs',
                multi_class = 'multinomial',
                n_jobs = 1,
                max_iter = 100
            )
        
        # Create and train pipeline
        pipeline = sklearn.pipeline.Pipeline([
            ('vectorizer', vectorizer),
            ('classifier', classifier)
        ])
        pipeline.fit(X, y)
        
        # Store relevant information
        self._hierarchy = hierarchy
        self._pipeline = pipeline
    
    # Export model to file
    def save(self, path):
        dump = (self._hierarchy, self._pipeline)
        with io.open(path, 'wb') as file:
            pickle.dump(dump, file)
    
    # Import model from file
    def load(self, path):
        with io.open(path, 'rb') as file:
            dump = pickle.load(file)
        self._hierarchy, self._pipeline = dump


# Asynchronous wrapper
class BagOfWordClassifier(Classifier):
    def __init__(self, path, executor, hierarchical=False):
        self._path = path
        self._executor = executor
        self._hierarchical = hierarchical
        self._model = Model(self._hierarchical)
        self._lock = asyncio.Lock()
        if os.path.exists(self._path):
            self._model.load(self._path)
    
    # Run synchronous model in background
    async def classify(self, text):
        async with self._lock:
            model = self._model
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self._executor, model.classify, text)
    
    # Ask for retraining (old model should be available during training)
    async def train(self, samples, adjacency):
        model = Model(self._hierarchical)
        hierarchy = HierarchyEncoder(adjacency)
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self._executor, model.train, samples, hierarchy)
        async with self._lock:
            await loop.run_in_executor(self._executor, model.save, self._path)
            self._model = model
