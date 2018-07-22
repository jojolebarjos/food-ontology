# -*- coding: utf-8 -*-


import numpy
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from food.parser.text import tokenize


# Scikit-learn-based classifier
class Model:
    def __init__(self):
        self._pipeline = None
    
    # Classify each sample used trained model
    def classify(self, texts):
        
        # If no model has been trained, give nothing
        if self._pipeline is None:
            return [{} for _ in texts]
        
        # Otherwise, use pipeline
        probabilities = self._pipeline.predict_proba(texts)
        classes = self._pipeline.steps[-1][1].classes_
        return [dict(zip(classes, p)) for p in probabilities]
    
    # Train model from texts and associated labels
    def train(self, samples, adjacency):
        
        # Split multilabels into separate samples
        samples = [(text, label) for text, labels in samples for label in labels]
        texts, labels = zip(*samples)
        
        # Make sure no unknown label is given
        invalid_labels = set(labels)
        invalid_labels.difference_update(adjacency.keys())
        assert len(invalid_labels) == 0, ', '.join(invalid_labels)
        
        # Convert words to boolean arrays
        vectorizer = CountVectorizer(
            tokenizer = tokenize,
            # TODO ngram_range = (1, 1),
            # TODO stop_words = [...],
            binary = True,
            dtype = numpy.int32
        )
        
        # Use flat hierarchy representation
        # TODO use children to build hierarchy-aware model
        classifier = LogisticRegression(
            solver = 'lbfgs',
            multi_class = 'multinomial',
            n_jobs = 1,
            max_iter = 100
        )
        
        # Create and train pipeline
        pipeline = Pipeline([
            ('vectorizer', vectorizer),
            ('classifier', classifier)
        ])
        pipeline.fit(texts, labels)
        
        # Store model
        self._pipeline = pipeline
