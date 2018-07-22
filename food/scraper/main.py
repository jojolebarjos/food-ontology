# -*- coding: utf-8 -*-


import os
import pathlib
import scrapy
import scrapy.crawler


# Get local directory
HERE = os.path.dirname(os.path.realpath(__file__))
CACHE_FOLDER = os.path.join(HERE, 'cache')


# Configure crawling
settings = {
    'BOT_NAME' : 'scraper',
    
    # Export to JSON file
    'FEED_URI' : pathlib.Path(os.path.join(HERE, 'export')).as_uri() + '/%(name)s.json',
    'FEED_EXPORT_ENCODING' : 'UTF-8',
    
    # Try to be nice
    'ROBOTSTXT_OBEY' : True,
    'DOWNLOAD_DELAY' : 1,
    'AUTOTHROTTLE_ENABLED' : True,
    'CONCURRENT_REQUESTS_PER_IP' : 4,
    
    # Use local cache
    'HTTPCACHE_ENABLED' : True,
    'HTTPCACHE_EXPIRATION_SECS' : 0,
    'HTTPCACHE_DIR' : CACHE_FOLDER,
    'HTTPCACHE_IGNORE_HTTP_CODES' : [],
    'HTTPCACHE_STORAGE' : 'food.scraper.cache.CacheStorage',
    
    # Disable irrelevant stuff
    #'LOG_LEVEL' : 'INFO',
    'COOKIES_ENABLED' : False,
    'TELNETCONSOLE_ENABLED' : False
}

# Select spiders
from .genius_kitchen import GeniusKitchenSpider
from .epicurious import EpicuriousSpider
spiders = [
    GeniusKitchenSpider,
    EpicuriousSpider
]

# Create process
process = scrapy.crawler.CrawlerProcess(settings)
for spider in spiders:
    process.crawl(spider)

# Run
process.start()
