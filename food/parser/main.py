# -*- coding: utf-8 -*-


import os
import asyncio
from aiohttp import web
import concurrent.futures
import random


# Get model paths
HERE = os.path.dirname(os.path.realpath(__file__))


# Load data
from .item import ItemCollection
items = ItemCollection(os.path.join(HERE, 'ingredients.txt'))


# Prepare routing table
routes = web.RouteTableDef()

# Static files
routes.static('/static/', os.path.join(HERE, 'static'))

# Query random samples
@routes.get('/api/sample')
async def handle_api_sample(request):
    text = await items.get_random_item()
    dummy = ['salt', 'pepper', 'chocolate', 'milk', 'egg']
    random.shuffle(dummy)
    dummy = dummy[:random.randint(0, len(dummy))]
    dummy = {x : random.random() for x in dummy}
    result = {
        'samples' : [{
            'text' : text,
            'truth' : ['misc'],
            'prediction' : dummy
        }]
    }
    return web.json_response(result)

# Ask for model retraining
@routes.post('/api/train')
async def handle_api_train(request):
    #asyncio.ensure_future(classifier.train())
    await asyncio.sleep(1.0 + random.random() * 3)
    return web.json_response({ 'success' : True })


# Create web server
app = web.Application()
app.router.add_routes(routes)

# Instantiate some workers
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
    app['executor'] = executor

    # Run web server
    web.run_app(app)
