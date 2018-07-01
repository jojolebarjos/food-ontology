# -*- coding: utf-8 -*-


import asyncio
from datetime import datetime
import io
import json
import os


# Key-value store
class AnnotationDataset:
    def __init__(self, path, executor):
        self._path = path
        self._executor = executor
        self._cache = None
        self._last = None
        self._lock = asyncio.Lock()
    
    
    # Internal data acquisition
    def _get(self):
        
        # Check if file exists
        if not os.path.exists(self._path):
            self._cache = {}
            return self._cache
        
        # Check if last access time is still fresh
        if self._last is not None:
            modified_time = os.path.getmtime(self._path)
            if modified_time <= self._last:
                return self._cache
        
        # Reload data
        now = datetime.now().timestamp()
        cache = {}
        with io.open(self._path, 'r', encoding='utf-8', newline='\n') as file:
            for line in file:
                entry = json.loads(line)
                cache[entry['key']] = entry
        self._cache = cache
        self._last = now
        return self._cache
    
    # Acquire latest annotation for given key(s)
    # Note: do not modify resulting object
    async def get(self, keys=None):
        loop = asyncio.get_event_loop()
        async with self._lock:
            cache = await loop.run_in_executor(self._executor, self._get)
            if keys is None:
                return cache
            if type(keys) is str:
                return cache.get(keys)
            return [cache.get(key) for key in keys]
    
    # Internal data append
    def _add(self, entries):
        
        # Make sure we are up-to-date
        self._get()
        
        # Update cache
        for entry in entries:
            self._cache[entry['key']] = entry
        
        # Add new lines in file
        with io.open(self._path, 'a', encoding='utf-8', newline='\n') as file:
            for entry in entries:
                file.write('%s\n' % json.dumps(entry))
        self._last = os.path.getmtime(self._path)
    
    # Add new annotation(s)
    async def add(self, entries):
        loop = asyncio.get_event_loop()
        if type(entries) is dict:
            entries = [entries]
        async with self._lock:
            await loop.run_in_executor(self._executor, self._add, entries)
