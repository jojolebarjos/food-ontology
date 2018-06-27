# -*- coding: utf-8 -*-


import scrapy
import regex


# Whitespace simplification
whitespace_regex = regex.compile(r'\s+', regex.UNICODE)


# Basic crawler for Genius Kitchen recipes
class GeniusKitchenSpider(scrapy.Spider):
    name = 'genius_kitchen'
    
    # Acquire all recipes in expected identifier range
    def start_requests(self):
        for id in range(1000): #550000
            yield scrapy.Request('http://www.geniuskitchen.com/%d' % id)
    
    # Do the parsing
    def parse(self, response):
        self.logger.info('Yay: %s', response.url)
        
        # Get main identifiers
        url = response.url
        id = int(url[url.rindex('-')+1:])
        title = response.selector.xpath('//h1/text()').extract_first()
        
        # Get average rating
        rating = response.selector.xpath('//span[@class="gk-rating-percent"]/span/text()').extract_first()
        # TODO to percent
        
        # TODO timing
        # TODO servings
        # TODO reviews
        # TODO directions
        
        # Get author
        author = response.selector.root.xpath('//h6[@class="byline"]/a')
        if len(author) > 0:
            author = author[0]
            author_url = author.attrib['href']
            author = {
                'id' : int(author_url[author_url.rindex('/')+1:]),
                'name' : author.text.strip()
            }
        else:
            author = None
        
        # Get ingredient list
        ingredients = []
        for element in response.selector.root.xpath('//ul[@class="ingredient-list"]/li'):
            text = ''.join(element.itertext())
            text = whitespace_regex.sub(' ', text).strip()
            ingredients.append(text)
        
        # Return result
        yield {
            'id' : id,
            'url' : url,
            'title' : title,
            'author' : author,
            'ingredients' : ingredients
        }
