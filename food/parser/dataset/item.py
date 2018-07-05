# -*- coding: utf-8 -*-


import asyncio
import io
import random


# Raw dataset container
class ItemCollection:
    def __init__(self, path, ontology, annotations, classifier, executor):
        self._path = path
        self._ontology = ontology
        self._annotations = annotations
        self._classifier = classifier
        self._executor = executor
        with io.open(self._path, 'r', encoding='utf-8') as file:
            self._items = [line.strip() for line in file]
    
    # Naive random sampling
    async def get_random_item(self):
        index = random.randint(0, len(self._items))
        return self._items[index]
