# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class RightItem(scrapy.Item):

    sale_date = scrapy.Field()
    price_paid = scrapy.Field()
    property = scrapy.Field()
    url = scrapy.Field()
    source_url = scrapy.Field()
    number_rooms = scrapy.Field()
    id = scrapy.Field()
    latitude = scrapy.Field()
    longitude = scrapy.Field()
    date_added = scrapy.Field()
    # area = scrapy.Field()
    number_imgs = scrapy.Field()
    name_area = scrapy.Field()