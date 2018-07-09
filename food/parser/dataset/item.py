# -*- coding: utf-8 -*-


import asyncio
import collections
import io
import os
import pickle
import random
from tqdm import tqdm

from ..text import tokenize


# Raw dataset container
class ItemCollection:
    def __init__(self, path, ontology, annotations, classifier, executor):
        self._path = path
        self._ontology = ontology
        self._annotations = annotations
        self._classifier = classifier
        self._executor = executor
        self._lock = asyncio.Lock()
        with io.open(self._path, 'r', encoding='utf-8') as file:
            self._items = [line.strip() for line in file]
        self._items_tokens = None
        self._annotated_items = None
    
    # Naive random sampling
    async def get_random_item(self):
        index = random.randint(0, len(self._items))
        return self._items[index]
    
    # Invalidate and rebuild cache
    def _rebuild(self, annotations):
        
        # Make sure items are tokenized and indexed
        if self._items_tokens is None:
            
            # Use cache, if fresh
            cache_path = self._path + '.pkl'
            if os.path.exists(cache_path) and os.path.getmtime(cache_path) >= os.path.getmtime(self._path):
                print('Reusing tokenized corpus')
                with io.open(cache_path, 'rb') as file:
                    self._items_tokens, self._items_token_map, self._items_token_count = pickle.load(file)
            
            # Otherwise, tokenize the whole corpus
            else:
                print('Tokenizing corpus...')
                self._items_tokens = [set(tokenize(item)) for item in tqdm(self._items)]
                self._items_token_map = collections.defaultdict(list)
                for index, tokens in enumerate(self._items_tokens):
                    for token in tokens:
                        self._items_token_map[token].append(index)
                self._items_token_count = collections.Counter({token : len(indices) for token, indices in self._items_token_map.items()})
                with io.open(cache_path, 'wb') as file:
                    pickle.dump((self._items_tokens, self._items_token_map, self._items_token_count), file)
        
        # Acquire annotations and related tokens
        print('Tokenizing annotations...')
        self._annotated_items = [(a['key'], a['truth']) for a in annotations.values()]
        self._annotated_items_tokens = [set(tokenize(key)) for key, _ in tqdm(self._annotated_items)]
        self._annotated_items_token_set = {token for tokens in self._annotated_items_tokens for token in tokens}
        
        # Acquire most common unknown word
        unknown_words = dict(self._items_token_count)
        for token in self._annotated_items_token_set:
            del unknown_words[token]
        unknown_words = sorted(unknown_words.items(), key=lambda x: -x[1])
        total = sum(count for _, count in unknown_words)
        self._unknown_words = [(word, count / total) for word, count in unknown_words]
        
        # Subsample unannotated samples
        print('predicting candidates confidence...')
        candidates = set(self._items)
        candidates.difference_update(key for key, _ in self._annotated_items)
        candidates = list(candidates)
        random.shuffle(candidates)
        self._candidates = candidates[:1000]
    
    # Lock-free invalidation
    async def _invalidate(self):
        loop = asyncio.get_event_loop()
        annotations = await self._annotations.get()
        await loop.run_in_executor(self._executor, self._rebuild, annotations)
        confidences = []
        for candidate in tqdm(self._candidates):
            probabilities = await self._classifier.classify(candidate)
            if len(probabilities) == 0:
                confidence = 0.0
            else:
                confidence = max(probabilities.values())
            confidences.append((confidence, candidate))
        confidences.sort(reverse=True)
        print(confidences[:10] + ['...'] + confidences[-10:])
        self._confidences = confidences[-500:]
    
    # Invalidate cache (useful after annotation or retraining)
    async def invalidate(self):
        async with self._lock:
            await self._invalidate()
    
    # Sample items with unknown words that have high frequency
    async def get_random_unknown_item(self):
        async with self._lock:
            
            # Make sure we have cached data
            if self._annotated_items is None:
                await self._invalidate()
            
            # Sample candidate that has an unknown word, with respect to distribution
            score = random.random()
            for word, probability in self._unknown_words:
                score -= probability
                if score < 0.0:
                    indices = self._items_token_map[word]
                    index = indices[random.randint(0, len(indices))]
                    return self._items[index]
            
            # If no unknown word is found, just yield some random item
            print('no more unknown words')
            return await self.get_random_item()
    
    # Sample items that have low confidence
    async def get_random_uncertain_item(self):
        async with self._lock:
            
            # Make sure we have cached data
            if self._annotated_items is None:
                await self._invalidate()
            
            # Sample candidate that has a low certainty
            if len(self._confidences) == 0:
                print('low-confidence buffer depleted')
                return await self.get_random_unknown_item()
            confidence, candidate = self._confidences.pop()
            print('%.4f%%: %s' % (100.0 * confidence, candidate))
            return candidate
