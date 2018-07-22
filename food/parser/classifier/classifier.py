# -*- coding: utf-8 -*-


import asyncio


# Abstract asynchronous classifier interface
class Classifier:
    
    # Provide annotation for specified texts
    async def classify(self, texts):
        raise NotImplementedError()
    
    # Ask for retraining (old model should be available during training)
    async def train(self):
        pass
