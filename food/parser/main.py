# -*- coding: utf-8 -*-


import os
import asyncio
from aiohttp import web
import concurrent.futures

from .api import API
from .log import Log


# Get model paths
HERE = os.path.dirname(os.path.realpath(__file__))


# Prepare routing table
routes = web.RouteTableDef()

# Static files
routes.static('/static/', os.path.join(HERE, 'static'))

# Query random samples
@routes.get('/api/sample')
async def handle_api_sample(request):
    api = request.app['api']
    result = await api.sample()
    return web.json_response(result)

# Ask for model retraining
@routes.post('/api/train')
async def handle_api_train(request):
    api = request.app['api']
    status = await api.train()
    return web.json_response({ 'success' : True })

# Add logging middleware
@web.middleware
async def middleware(request, handler):
    log = request.app['log']
    _, result = await asyncio.gather(
        log.info('%s %s' % (request.method, request.url)),
        handler(request)
    )
    return result 


# Create web server
app = web.Application(middlewares=[middleware])
app.router.add_routes(routes)

# Instantiate some workers
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
    app['executor'] = executor
    
    # Provide log manager
    log = Log(executor)
    app['log'] = log
    
    # Instantiate API container
    api = API(executor, log)
    app['api'] = api

    # Run web server
    web.run_app(app)
