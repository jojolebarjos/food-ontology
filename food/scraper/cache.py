# -*- coding: utf-8 -*-


import logging
import os
import pickle
import scrapy
from scrapy.http import Headers, Response
from scrapy.responsetypes import responsetypes
from scrapy.utils.project import data_path
from scrapy.utils.request import request_fingerprint
from time import time
import threading
from w3lib.http import headers_raw_to_dict, headers_dict_to_raw
import zipfile


# Basic logger instance
logger = logging.getLogger(__name__)


# Custom file storage, more compact than vanilla implementation (slower, though)
class CacheStorage:
    def __init__(self, settings):
        self._folder = data_path(settings['HTTPCACHE_DIR'])
        self._lock = threading.Lock()
    
    # Nothing to do on open
    def open_spider(self, spider):
        pass

    # Nothing to do on close
    def close_spider(self, spider):
        pass
    
    # Acquire data
    def retrieve_response(self, spider, request):
        with self._lock:
        
            # Find archive, if any
            id = request_fingerprint(request)
            path = os.path.join(self._folder, spider.name, '%s.zip' % id[:2])
            if not os.path.exists(path):
                logger.debug('Cache miss: %s %s (%s)' % (request.method, request.url, id))
                return
            
            # Acquire data
            with zipfile.ZipFile(path, 'r') as archive:
                try:
                    info = archive.getinfo(id)
                except KeyError:
                    logger.debug('Cache miss: %s %s (%s)' % (request.method, request.url, id))
                    return
                logger.debug('Cache hit: %s %s (%s)' % (request.method, request.url, id))
                with archive.open(info, 'r') as file:
                    dump = pickle.load(file)
            
            # Create response
            body = dump['response_body']
            headers = Headers(headers_raw_to_dict(dump['response_headers']))
            url = dump.get('response_url')
            status = dump['status']
            respcls = responsetypes.from_args(headers=headers, url=url)
            response = respcls(url=url, headers=headers, status=status, body=body)
            return response
    
    # Store data
    def store_response(self, spider, request, response):
        with self._lock:
            
            # Create dump
            dump = {
                'url': request.url,
                'method': request.method,
                'status': response.status,
                'response_url': response.url,
                'timestamp': time(),
                'response_headers' : headers_dict_to_raw(response.headers),
                'response_body' : response.body,
                'request_headers' : headers_dict_to_raw(request.headers),
                'request_body' : request.body
            }
            
            # Find archive folder
            id = request_fingerprint(request)
            logger.debug('Cache update: %s %s (%s)' % (request.method, request.url, id))
            folder = os.path.join(self._folder, spider.name)
            if not os.path.exists(folder):
                os.makedirs(folder)
            
            # Update archive
            path = os.path.join(folder, '%s.zip' % id[:2])
            with zipfile.ZipFile(path, 'a', compression=zipfile.ZIP_LZMA) as archive:
                with archive.open(id, 'w') as file:
                    pickle.dump(dump, file)
