# -*- coding: utf-8 -*-


import asyncio
import io
import os
import random

from .sampler import Sampler


# Add prediction to sample
class PredictionSampler(Sampler):
    def __init__(self, sampler, classifier):
        self._sampler = sampler
        self._classifier = classifier
    
    # Get samples from sources
    async def sample(self, count=1):
        samples = await self._sampler.sample(count)
        texts = [sample['text'] for sample in samples]
        predictions = await self._classifier.classify(texts)
        for sample, prediction in zip(samples, predictions):
            sample['prediction'] = prediction
        return samples
