# -*- coding: utf-8 -*-


import asyncio


# Abstract asynchronous classifier interface
class Classifier:
    
    # Provide annotation for specified text
    async def classify(self, text):
        raise NotImplementedError()
    
    # Ask for retraining (old model should be available during training)
    async def train(self, samples):
        pass


# Internal synchronous model
class Model:
    
    # Annotate given samples
    def classify(self, text):
        raise NotImplementedError()
    
    # Use given samples to train
    def train(self, samples):
        pass


# Standard asynchronous wrapper
class ModelClassifier(Classifier):
    def __init__(self, factory, executor):
        self._factory = factory
        self._model = self._factory()
        self._executor = executor
        self._lock = asyncio.Lock()
    
    # Run synchronous model in background
    async def classify(self, text):
        async with self._lock:
            model = self._model
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self._executor, model.classify, text)
    
    # Ask for retraining (old model should be available during training)
    async def train(self, samples):
        model = self._factory()
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self._executor, model.train, samples)
        async with self._lock:
            self._model = model
