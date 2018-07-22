# -*- coding: utf-8 -*-


import asyncio
import io
import os
import random

from .sampler import Sampler


# Generate samples from raw text file
class LineSampler(Sampler):
    def __init__(self, path):
        with io.open(path, 'r', encoding='utf-8') as file:
            texts = []
            for line in file:
                texts.append(line.strip())
        self._texts = texts
        self._offset = len(texts)
    
    # Get samples from sources
    async def sample(self, count=1):
        samples = []
        for _ in range(count):
            if self._offset >= len(self._texts):
                self._offset = 0
                random.shuffle(self._texts)
            text = self._texts[self._offset]
            self._offset += 1
            sample = {
                'text' : text
            }
            samples.append(sample)
        return samples
