# -*- coding: utf-8 -*-


import asyncio
import os
import random

from .classifier import LogisticClassifier
from .annotation import AnnotationDataset
from .ontology import OntologyContainer
from .sampler import AnnotationSampler, ConfidenceSampler, LineSampler, PredictionSampler


# Get folders and paths
HERE = os.path.dirname(os.path.realpath(__file__))
ONTOLOGY_TXT = os.path.join(HERE, '..', 'ontology', 'core.txt')
INGREDIENTS_TXT = os.path.join(HERE, 'model', 'ingredients.txt')
ANNOTATIONS_JSON = os.path.join(HERE, 'model', 'annotations.json')
CLASSIFIER_PKL = os.path.join(HERE, 'model', 'model.pkl')


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
        
        # Sample generator
        line_sampler = LineSampler(INGREDIENTS_TXT, self._annotations)
        prediction_sampler = PredictionSampler(line_sampler, self._classifier)
        confidence_sampler = ConfidenceSampler(prediction_sampler, oversampling=5)
        annotation_sampler = AnnotationSampler(confidence_sampler, self._annotations)
        self._sampler = annotation_sampler
    
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
    async def sample(self, count=1):
        samples = await self._sampler.sample(count)
        for sample in samples:
            prediction = sample.get('prediction', {})
            prediction = {label : probability for label, probability in prediction.items() if probability > 0.01}
            sample['prediction'] = prediction
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
