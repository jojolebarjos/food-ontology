# -*- coding: utf-8 -*-


import asyncio
import random

from .sampler import Sampler


# Subsample with respect to classification confidence
class ConfidenceSampler(Sampler):
    def __init__(self, sampler, oversampling=5):
        self._sampler = sampler
        self._oversampling = oversampling
    
    # Generate and prune samples
    async def sample(self, count=1):
        oversamples = await self._sampler.sample(count * self._oversampling)
        random.shuffle(oversamples)
        samples = []
        for i in range(count):
            batch = oversamples[i * self._oversampling : (i + 1) * self._oversampling]
            worst_sample = None
            worst_confidence = 999.0
            for b in batch:
                probabilities = b.get('prediction', {}).values()
                confidence = max(probabilities)
                if confidence < worst_confidence:
                    worst_sample = b
                    worst_confidence = confidence
            samples.append(worst_sample)
        return samples
