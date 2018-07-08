# -*- coding: utf-8 -*-


import asyncio


# Abstract asynchronous classifier interface
class Classifier:
    
    # Provide annotation for specified text
    async def classify(self, text):
        raise NotImplementedError()
    
    # Ask for retraining (old model should be available during training)
    async def train(self, samples, adjacency):
        pass
