# -*- coding: utf-8 -*-


import asyncio
import io


# Key-value store
class AnnotationDataset:
    def __init__(self, path, executor):
        self._path = path
        self._executor = executor
        with io.open(self._path, 'r', encoding='utf-8', newline='\n') as file:
            self._cache = dict(line[:-1].split('\t', 1) for line in file)
        self._lock = asyncio.Lock()
    
    async def get(self, text):
        async with self._lock:
            return self._cache.get(text)
    
    async def set(self, text, value):
        async with self._lock:
            self._cache[text] = value
            # TODO make this write asynchronous
            with io.open(self._path, 'a', encoding='utf-8', newline='\n') as file:
                file.write('%s\t%s\n' % (text, value), line)
    
    async def iterate(self):
        async with self._lock:
            cache = dict(self._cache)
        for text, value in cache.items():
            yield text, value
