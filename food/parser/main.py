# -*- coding: utf-8 -*-


import os
from aiohttp import web
import concurrent.futures


# Get model paths
HERE = os.path.dirname(os.path.realpath(__file__))


# Load data
from .item import ItemCollection
items = ItemCollection(os.path.join(HERE, 'ingredients.txt'))


# Prepare routing table
routes = web.RouteTableDef()

# Query random samples
@routes.get('/api/sample')
async def handle_api_sample(request):
    print(request.rel_url.query.items())
    text = await items.get_random_item()
    result = {
        'text' : text
    }
    return web.json_response(result)


# Create web server
app = web.Application()
app.router.add_routes(routes)

# Instantiate some workers
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
    app['executor'] = executor

    # Run web server
    web.run_app(app)
