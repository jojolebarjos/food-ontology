# -*- coding: utf-8 -*-


import asyncio
import collections
from datetime import datetime
import difflib
import io
import os
from food.ontology.reader import iterate


# Attributes with structural meaning
HIERARCHICAL_ATTRIBUTES = {
    'product_of',
    'derivative_of',
    'part_of',
    'made_of',
    'kind_of'
    # TODO substitute-of, modifier
}


# Ontology
class Ontology:
    def __init__(self, entries):
        self._attributes = {}
        self._ascendants = {}
        self._descendants = {}
        for id, relationships in entries.items():
            attributes = {}
            ascendants = {}
            for key, values in relationships.items():
                collection = ascendants if key in HIERARCHICAL_ATTRIBUTES else attributes
                collection[key] = values
            self._attributes[id] = attributes
            self._ascendants[id] = ascendants
            self._descendants[id] = collections.defaultdict(list)
        for id, relationships in self._ascendants.items():
            for key, values in relationships.items():
                for value in values:
                    self._descendants[value][key].append(id)
    
    # Get all identifiers
    def get_identifiers(self):
        return self._attributes.keys()
    
    # Get nicely formatted properties of a single entry
    def get_properties(self, identifier):
        attributes = self._attributes.get(identifier)
        if attributes is None:
            return None
        return {
            'id' : identifier,
            **attributes,
            'ascendants' : self._ascendants[identifier],
            'descendants' : self._descendants[identifier]
        }
    
    # Find closest entries
    def get_close_matches(self, query):
        return difflib.get_close_matches(query, list(self._attributes), n=16, cutoff=0.01)


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
        now = datetime.now().timestamp()
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
    
    # Acquire suggestions
    async def suggest(self, query):
        ontology = await self.get()
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self._executor, ontology.get_close_matches, query)
    
    # TODO nice API
