# -*- coding: utf-8 -*-


import asyncio
import os
import random

from .classifier import LogisticClassifier
from .dataset import AnnotationDataset, ItemCollection, OntologyContainer


# Get folders and paths
HERE = os.path.dirname(os.path.realpath(__file__))
ONTOLOGY_TXT = os.path.join(HERE, '..', 'ontology', 'core.txt')
INGREDIENTS_TXT = os.path.join(HERE, 'dataset', 'ingredients.txt')
ANNOTATIONS_JSON = os.path.join(HERE, 'dataset', 'annotations.json')
CLASSIFIER_PKL = os.path.join(HERE, 'classifier', 'model.pkl')


# Main logic container
class API:
    def __init__(self, executor, log):
        self._executor = executor
        self._log = log
        
        # Acquire default ontology
        self._ontology = OntologyContainer(
            [ONTOLOGY_TXT],
            self._executor
        )
        
        # Prepare basic annotation dataset
        self._annotations = AnnotationDataset(
            ANNOTATIONS_JSON,
            self._executor
        )
        
        # Create basic classifier
        self._classifier = LogisticClassifier(
            self._ontology,
            self._annotations,
            CLASSIFIER_PKL,
            self._executor
        )
        
        # Acquire raw items
        self._items = ItemCollection(
            INGREDIENTS_TXT,
            self._ontology,
            self._annotations,
            self._classifier,
            self._executor
        )
    
    # Provide information about ontology
    async def label(self, identifiers=None):
        ontology = await self._ontology.get()
        if identifiers is None:
            identifiers = ontology.get_identifiers()
        labels = {id : ontology.get_properties(id) for id in identifiers}
        return {'labels' : labels}
    
    # Auto-completion tool
    async def suggest(self, query):
        return await self._ontology.suggest(query)
    
    # Annotate specified text
    async def classify(self, text, threshold=None):
        results = await self._classifier.classify([text])
        results = results[0]
        threshold = threshold or 0.0
        results = {label : probability for label, probability in sorted(results.items(), key=lambda x: x[1], reverse=True) if probability >= threshold}
        return results
    
    # Acquire samples according to specified rules
    async def sample(self, count=1, parents=None):
        
        # Acquire random samples
        texts = []
        for _ in range(count):
            text = await self._items.get_random_item()
            texts.append(text)
        
        # Predict labels
        predictions = await self._classifier.classify(texts)
        
        # Acquire any existing annotation
        annotations = []
        for text in texts:
            annotation = await self._annotations.get(text)
            annotation = set(annotation or [])
            annotations.append(annotation)
        
        # Pack samples
        samples = []
        for text, prediction, annotation in zip(texts, predictions, annotations):
            labels = {}
            for label, probability in prediction.items():
                labels[label] = {
                    'type' : 'prediction',
                    'label' : label,
                    'probability' : probability
                }
            for label in annotation:
                if label in labels:
                    labels[label]['type'] = 'truth'
                else:
                    labels[label] = {
                        'type' : 'truth',
                        'label' : label,
                        'probability' : 0.0
                    }
            
            # Keep only relevant values
            labels = sorted([v for v in labels.values() if v['probability'] > 0.01 or v['type'] == 'truth'], key=lambda v: -v['probability'])
            
            # Register sample
            sample = {
                'text' : text,
                'labels' : labels
            }
            samples.append(sample)
        
        # Ready
        return {
            'samples' : samples
        }
    
    # Register annotation
    async def annotate(self, annotations):
        await self._annotations.add(annotations)
        return { 'success' : True }
    
    # Train classifier based on existing samples
    async def train(self):
        return await self._classifier.train()
