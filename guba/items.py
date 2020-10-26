import scrapy


class ArticleItem(scrapy.Item):
    collection = 'articles'
    url = scrapy.Field()
    created_date = scrapy.Field()
    title = scrapy.Field()
    content = scrapy.Field()
    n_pageviews = scrapy.Field()
    n_comments = scrapy.Field()
    author_id = scrapy.Field()
    stock_id = scrapy.Field()
