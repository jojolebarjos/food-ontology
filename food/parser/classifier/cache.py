# -*- coding: utf-8 -*-


import asyncio
from .classifier import Classifier


# Simple cache strategy (no discard)
class MemoryCacheClassifier(Classifier):
    def __init__(self, classifier):
        self._classifier = classifier
        self._cache = {}
    
    # Use in-memory value, if available
    async def classify(self, texts):
        # TODO implement cache
        return await self._classifier.classify(texts)
    
    # Invalidate cache when underlying model is ready
    async def train(self):
        status = await self._classifier.train()
        self._cache.clear()
        return status
