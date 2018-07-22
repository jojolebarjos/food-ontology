# -*- coding: utf-8 -*-


import scrapy


# Basic crawler for Epicurious recipes
class EpicuriousSpider(scrapy.Spider):
    name = 'epicurious'
    
    # Acquire all recipes in expected identifier range
    def start_requests(self):
        for id in range(1, 6010):
            yield scrapy.Request('https://www.epicurious.com/recipes/food/views/%d' % id)
    
    # Do the parsing
    def parse(self, response):
        
        # Get main identifiers
        url = response.url
        try:
            id = int(url[url.rindex('-')+1:])
        except:
            return
        
        # Get title
        title = response.selector.xpath('//h1/text()').extract_first()
        title = title.strip()
        
        # Source
        # TODO author/date/source...
        
        # Rating
        rating_min = response.selector.xpath('//*[@itemprop="worstRating"]/@content').extract_first()
        rating_max = response.selector.xpath('//*[@itemprop="bestRating"]/@content').extract_first()
        rating_value = response.selector.xpath('//*[@itemprop="ratingValue"]/@content').extract_first()
        rating = float(rating_value) / (float(rating_max) - float(rating_min))
        
        # Get description
        description = response.selector.xpath('//*[@itemprop="description"]/p/text()').extract_first()
        
        # Yield
        servings = response.selector.xpath('//*[@itemprop="recipeYield"]/text()').extract_first()
        
        # Ingredients
        # TODO might use class="ingredient-group" to get subgroups
        ingredients = response.selector.xpath('//*[@itemprop="ingredients"]/text()').extract()
        
        # Preparation
        # TODO directives
        
        # Nutritional information
        calories = response.selector.xpath('//*[@itemprop="calories"]/text()').extract_first()
        carbohydrates = response.selector.xpath('//*[@itemprop="carbohydrateContent"]/text()').extract_first()
        fat = response.selector.xpath('//*[@itemprop="fatContent"]/text()').extract_first()
        protein = response.selector.xpath('//*[@itemprop="proteinContent"]/text()').extract_first()
        sodium = response.selector.xpath('//*[@itemprop="sodiumContent"]/text()').extract_first()
        polyunsaturated_fat = response.selector.xpath('//*[text()="Polyunsaturated Fat"]/../*[@class="nutri-data"]/text()').extract_first()
        fiber = response.selector.xpath('//*[@itemprop="fiberContent"]/text()').extract_first()
        monounsaturated_fat = response.selector.xpath('//*[text()="Monounsaturated Fat"]/../*[@class="nutri-data"]/text()').extract_first()
        cholesterol = response.selector.xpath('//*[@itemprop="cholesterolContent"]/text()').extract_first()
        
        # Tags
        tags = response.selector.xpath('//*[@itemprop="recipeCategory"]/text()').extract()
        
        # Return result
        yield {
            'id' : id,
            'url' : url,
            'title' : title,
            'ingredients' : ingredients
            # TODO more properties
        }
