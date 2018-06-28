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
        await with self._lock:
            if text in self._cache:
                return self._cache[text]
        result = await self._classifier.classify(text)
        await with self._lock:
            self._cache[text] = result
        return result
    
    # Invalidate cache when underlying model is ready
    async def train(self, samples):
        await self._classifier.train(samples)
        await with self._lock:
            self._cache.clear()
