# -*- coding: utf-8 -*-


import asyncio

from .classifier import Classifier


# Chain coroutines
async def then(fence, task):
    await fence
    return await task


# Avoid overlapping training sessions
class DelayedClassifier(Classifier):
    def __init__(self, classifier):
        self._classifier = classifier
        self._lock = asyncio.Lock()
        self._training_future = None
        self._pending_future = None
    
    # Annotate given samples
    async def classify(self, texts):
        return await self._classifier.classify(texts)
    
    # Schedule training session
    async def train(self):
        async with self._lock:
            
            # If no training session is running, just do it
            if self._training_future is None:
                future = asyncio.ensure_future(self._train())
                self._training_future = future
            
            # Otherwise, if there is no session scheduled, prepare it
            elif self._pending_future is None:
                future = asyncio.ensure_future(then(self._training_future, self._classifier.train()))
                self._pending_future = future
            
            # Otherwise, just wait on scheduled training
            else:
                future = self._pending_future
        
        # Wait for it
        return await future
    
    # Train and then trigger any scheduled session
    async def _train(self):
        status = await self._classifier.train()
        async with self._lock:
            self._training_future = self._pending_future
            self._pending_future = None
        return status
