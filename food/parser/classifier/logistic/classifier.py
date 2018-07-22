# -*- coding: utf-8 -*-


import asyncio
import io
import os
import pickle
import time

from ..classifier import Classifier
from .model import Model


# Scikit-learn-based classifier
class LogisticClassifier(Classifier):
    def __init__(self, ontology, annotations, path, executor):
        self._ontology = ontology
        self._annotations = annotations
        self._path = path
        self._executor = executor
        
        # Load previously model, if any
        if self._path is not None and os.path.exists(self._path):
            with io.open(self._path, 'rb') as file:
                self._model = pickle.load(file)
        else:
            self._model = Model()
    
    # Run synchronous model in background
    async def classify(self, texts):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self._executor, self._model.classify, texts)
    
    # Acquire training samples and run training session
    async def train(self):
        
        # Acquire ontology
        ontology = await self._ontology.get()
        
        # Acquire annotations
        loop = asyncio.get_event_loop()
        annotations = await self._annotations.get()
        
        # Train in background
        model, status = await loop.run_in_executor(self._executor, self._train, ontology, annotations)
        if model is not None:
            self._model = model
        return status
    
    # Train logistic model
    def _train(self, ontology, annotations):
        start = time.perf_counter()
        
        # Get samples from ontology
        ontology_samples = []
        for id in ontology.get_identifiers():
            properties = ontology.get_properties(id)
            for text in properties['label']:
                sample = (text, [id])
                ontology_samples.append(sample)
        
        # Get samples from annotations
        annotations_samples = [(a['key'], a['truth']) for a in annotations.values()]
        
        # Properly weight samples
        samples = ontology_samples * 5 + annotations_samples
        
        # Acquire hierarchy
        identifiers = ontology.get_identifiers()
        adjacency = {}
        for id in identifiers:
            properties = ontology.get_properties(id)
            descendants = properties['descendants']
            children = set()
            for key, values in descendants.items():
                for value in values:
                    children.add(value)
            adjacency[id] = children
        
        # Train model
        model = Model()
        model.train(samples, adjacency)
        
        # Save model
        if self._path is not None:
            with io.open(self._path, 'wb') as file:
                pickle.dump(model, file)
        
        # Ready
        end = time.perf_counter()
        status = {
            'success' : True,
            'time_elapsed' : end - start
        }
        return model, status
