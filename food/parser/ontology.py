# -*- coding: utf-8 -*-


import asyncio
import collections
from datetime import datetime
import io
import os
from food.ontology.reader import iterate


# Ontology
class Ontology:
    def __init__(self, entries):
        self._entries = entries
    
    # TODO ontology accessors


# Asynchronous ontology container, with automatic refresh from disk
class OntologyContainer:
    def __init__(self, paths, executor):
        self._paths = list(paths)
        self._executor = executor
        self._ontology = None
        self._last = None
        self._lock = asyncio.Lock()
    
    # Get fresh internal data
    def _get(self):
        
        # Check if last access time is still fresh
        if self._last is not None:
            for path in self._paths:
                modified_time = os.path.getmtime(path)
                if modified_time > self._last:
                    break
            else:
                return self._ontology
        
        # Reload data
        now = datetime.now()
        entries = collections.defaultdict(lambda: collections.defaultdict(list))
        for path in self._paths:
            with io.open(path, 'r', encoding='utf-8') as file:
                for left, relationship, right in iterate(file):
                    entries[left][relationship].append(right)
        self._ontology = Ontology(entries)
        self._last = now
        return self._ontology
    
    # Get whole ontology object
    async def get(self):
        loop = asyncio.get_event_loop()
        async with self._lock:
            return await loop.run_in_executor(self._executor, self._get)
            
    # TODO nice API
