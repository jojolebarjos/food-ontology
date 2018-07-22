# -*- coding: utf-8 -*-


import asyncio
import io
import os
import random

from .sampler import Sampler


# Add annotation (if any) to sample
class AnnotationSampler(Sampler):
    def __init__(self, sampler, annotations):
        self._sampler = sampler
        self._annotations = annotations
    
    # Get samples from sources
    async def sample(self, count=1):
        samples = await self._sampler.sample(count)
        annotations = await self._annotations.get()
        for sample in samples:
            text = sample['text']
            annotation = annotations.get(text)
            if annotation is not None:
                annotation = annotation.get('truth')
            sample['annotation'] = annotation
        return samples
