# -*- coding: utf-8 -*-


import asyncio
import io
import random


# Raw dataset container
class ItemCollection:
    def __init__(self, path):
        self._path = path
        with io.open(self._path, 'r', encoding='utf-8') as file:
            self._items = [line.strip() for line in file]
    
    async def get_random_item(self):
        index = random.randint(0, len(self._items))
        return self._items[index]
