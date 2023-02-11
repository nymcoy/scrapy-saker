# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class SakerArticleItem(scrapy.Item):
    url = scrapy.Field()
    id = scrapy.Field()
    date = scrapy.Field()
    author = scrapy.Field()
    category = scrapy.Field()
    title = scrapy.Field()
    content = scrapy.Field()
    tags = scrapy.Field()
    image_urls = scrapy.Field()
    images = scrapy.Field()

