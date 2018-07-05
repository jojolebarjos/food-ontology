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

# Query ontology properties
@routes.get('/api/label')
async def handle_api_label(request):
    api = request.app['api']
    if 'id' in request.query:
        identifiers = request.query.getall('id')
    else:
        identifiers = None
    result = await api.label(identifiers)
    return web.json_response(result)

# Get close ontology match
@routes.get('/api/suggest')
async def handle_api_suggest(request):
    api = request.app['api']
    if 'query' not in request.query:
        raise web.HTTPBadRequest()
    query = request.query['query']
    result = {
        'labels' : await api.suggest(query)
    }
    return web.json_response(result)

# Classify specified text
@routes.get('/api/classify')
async def handle_api_classify(request):
    api = request.app['api']
    if 'text' not in request.query:
        raise web.HTTPBadRequest()
    text = request.query['text']
    # TODO allow some threshold/limit parameter
    result = await api.classify(text)
    return web.json_response(result)

# Query random samples
@routes.get('/api/sample')
async def handle_api_sample(request):
    api = request.app['api']
    try:
        count = int(request.query.get('count', 1))
    except:
        raise web.HTTPBadRequest()
    result = await api.sample(count)
    return web.json_response(result)

# Add annotation
@routes.post('/api/annotate')
async def handle_api_annotate(request):
    api = request.app['api']
    try:
        payload = await request.json()
        print(payload)
    except:
        raise web.HTTPBadRequest()
    if type(payload) is not dict:
        raise web.HTTPBadRequest()
    samples = payload.get('samples', [payload])
    entries = []
    for sample in samples:
        text = sample.get('text')
        truth = sample.get('truth')
        if type(truth) is str:
            truth = [truth]
        if type(text) is not str or not type(truth) is list or any(type(t) is not str for t in truth):
            raise web.HTTPBadRequest()
        entry = {
            'key' : text,
            'truth' : truth
        }
        entries.append(entry)
    result = await api.annotate(entries)
    return web.json_response(result)

# Ask for model retraining
@routes.post('/api/train')
async def handle_api_train(request):
    api = request.app['api']
    result = await api.train()
    return web.json_response(result)

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
