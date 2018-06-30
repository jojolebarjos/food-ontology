# -*- coding: utf-8 -*-


import asyncio
import os
import random

from .classifier import ModelClassifier, NaiveBagOfWordModel
from .dataset import ItemCollection, OntologyContainer


# Get folders and paths
HERE = os.path.dirname(os.path.realpath(__file__))
ONTOLOGY_TXT = os.path.join(HERE, '..', 'ontology', 'core.txt')
INGREDIENTS_TXT = os.path.join(HERE, 'dataset', 'ingredients.txt')


# Main logic container
class API:
    def __init__(self, executor, log):
        self._executor = executor
        self._log = log
        
        # Acquire default ontology
        self._ontology = OntologyContainer([ONTOLOGY_TXT], self._executor)
        
        # Create basic classifier
        def factory():
            # TODO model parameters
            return NaiveBagOfWordModel()
        self._classifier = ModelClassifier(factory, self._executor)
        
        # Prepare basic annotation dataset
        # TODO
        
        # Acquire raw items
        self._items = ItemCollection(INGREDIENTS_TXT)
    
    # Acquire samples according to specified rules
    async def sample(self, count=1):
        text = await self._items.get_random_item()
        dummy = ['salt', 'pepper', 'chocolate', 'milk', 'egg']
        random.shuffle(dummy)
        dummy = dummy[:random.randint(0, len(dummy))]
        dummy = {x : random.random() for x in dummy}
        result = {
            'samples' : [{
                'text' : text,
                'truth' : ['misc'],
                'prediction' : dummy
            }]
        }
        return result
    
    # TODO annotation accessors
    
    # Provide information about ontology
    async def ontology(self, identifiers=None):
        pass
    
    # Train classifier based on existing samples
    async def train(self):
        # TODO use asyncio.ensure_future(classifier.train()) instead?
        samples = [] # TODO acquire samples
        await self._classifier.train()
        status = { 'success' : True }
        return status
