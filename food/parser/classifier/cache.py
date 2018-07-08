# -*- coding: utf-8 -*-


import asyncio
from .core import Classifier


# Simple cache strategy (no discard)
class MemoryCacheClassifier(Classifier):
    def __init__(self, classifier):
        self._classifier = classifier
        self._cache = {}
        self._lock = asyncio.Lock()
    
    # Use in-memory value, if available
    async def classify(self, text):
        async with self._lock:
            if text in self._cache:
                return self._cache[text]
        result = await self._classifier.classify(text)
        async with self._lock:
            self._cache[text] = result
        return result
    
    # Invalidate cache when underlying model is ready
    async def train(self, samples, adjacency):
        await self._classifier.train(samples)
        async with self._lock:
            self._cache.clear()
