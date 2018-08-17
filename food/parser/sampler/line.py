# -*- coding: utf-8 -*-


import asyncio
import io
import os
import random

from .sampler import Sampler


# Generate samples from raw text file
class LineSampler(Sampler):
    def __init__(self, path, annotations=None):
        with io.open(path, 'r', encoding='utf-8') as file:
            texts = []
            for line in file:
                texts.append(line.strip())
        self._texts = texts
        self._offset = len(texts)
        self._annotations = annotations
    
    # Get samples from sources
    async def sample(self, count=1):
        texts = set()
        annotations = await self._annotations.get()
        reshuffle = False
        for _ in range(count):
            
            # If buffer is exhausted
            if self._offset >= len(self._texts):
                
                # Avoid infinite loop
                if reshuffle:
                    break
                
                # Reshuffle set and go through the whole dataset again
                self._offset = 0
                random.shuffle(self._texts)
                reshuffle = True
            
            # Try to get sample
            text = self._texts[self._offset]
            self._offset += 1
            if text in annotations:
                continue
            if text in texts:
                continue
            texts.add(text)
        
        # Return sample list
        return [{'text' : text} for text in texts]
