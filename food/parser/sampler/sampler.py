# -*- coding: utf-8 -*-


import asyncio


# Abstract sample generator
class Sampler:
    
    # Acquire samples
    async def sample(self, count=1):
        raise NotImplementedError()
