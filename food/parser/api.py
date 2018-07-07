# -*- coding: utf-8 -*-


import asyncio
import os
import random

from .classifier import ModelClassifier, NaiveBagOfWordModel
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
        self._ontology = OntologyContainer([ONTOLOGY_TXT], self._executor)
        
        # Create basic classifier
        def factory():
            # TODO model parameters
            return NaiveBagOfWordModel(
                path = CLASSIFIER_PKL
            )
        self._classifier = ModelClassifier(factory, self._executor)
        
        # Prepare basic annotation dataset
        self._annotations = AnnotationDataset(ANNOTATIONS_JSON, self._executor)
        
        # Acquire raw items
        self._items = ItemCollection(INGREDIENTS_TXT, self._ontology, self._annotations, self._classifier, self._executor)
    
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
        results = await self._classifier.classify(text, verbose=True)
        threshold = threshold or 0.0
        results = {label : probability for label, probability in sorted(results.items(), key=lambda x: x[1], reverse=True) if probability >= threshold}
        return results
    
    # Acquire samples according to specified rules
    async def sample(self, count=1, parents=None):
        # TODO add sampling parameters (e.g. expected class)
        # TODO add sampling priority based on usage in recipes (i.e. recipes almost complete should be focused)
        samples = []
        for i in range(count):
            
            # Acquire random sample
            # TODO restrict to specified parents
            text = await self._items.get_random_item()
            
            # Compute prediction
            predictions = await self._classifier.classify(text, verbose=True)
            
            # Check if we have some annotation
            truth = await self._annotations.get(text)
            truth = truth or []
            truth = set(truth)
            
            # Pack labels
            labels = {}
            for label, probability in predictions.items():
                labels[label] = {
                    'type' : 'prediction',
                    'label' : label,
                    'probability' : probability
                }
            for label in truth:
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
        return {
            'samples' : samples
        }
    
    # Register annotation
    async def annotate(self, annotations):
        await self._annotations.add(annotations)
        return { 'success' : True }
    
    # Train classifier based on existing samples
    async def train(self):
        
        # Get samples from ontology
        ontology = await self._ontology.get()
        ontology_samples = []
        for id in ontology.get_identifiers():
            properties = ontology.get_properties(id)
            for text in properties['label']:
                sample = (text, [id])
                ontology_samples.append(sample)
        print(ontology_samples)
        
        # Get samples from annotations
        annotations = await self._annotations.get()
        annotations_samples = [(a['key'], a['truth']) for a in annotations.values()]
        
        # Train model
        samples = ontology_samples * 5 + annotations_samples
        await self._classifier.train(samples)
        return { 'success' : True }
