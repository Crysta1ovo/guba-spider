import re
import scrapy
from guba.items import ArticleItem


class StocksSpider(scrapy.Spider):
    name = 'stocks'
    allowed_domains = ['guba.eastmoney.com']

    def __init__(self):
        super(StocksSpider, self).__init__()
        self.filter_words = ['tzbd', 'cfhpl', 'cjpl', 'caifuhao']

    def start_requests(self):
        for i in range(1, 3):  # 沪深
            yield scrapy.Request('http://guba.eastmoney.com/remenba.aspx?type=1&tab={}'.format(i), self.generate_stock_urls, dont_filter=True)

    def generate_stock_urls(self, response):
        stocks = response.css('.ngblistul2 li')
        for stock in stocks:
            stock_url = stock.css('a::attr(href)').extract_first()
            page = 1
            idx = stock_url.find('.html')
            stock_url = stock_url[:idx] + \
                ',f_{}'.format(page) + stock_url[idx:]  # 按发帖时间查看
            url = 'http://guba.eastmoney.com/' + stock_url
            meta = {
                'page': page
            }
            yield scrapy.Request(url, self.generate_article_urls, meta=meta, dont_filter=True)

    def generate_article_urls(self, response):
        if response.css('.noarticle'):
            return

        articles = response.css('.articleh.normal_post')
        for article in articles:
            if article.css('.l3.a3 em'):
                continue
            article_url = article.css('.l3.a3 a::attr(href)').extract_first()
            if any([word in article_url for word in self.filter_words]):
                continue
            url = 'http://guba.eastmoney.com' + article_url
            n_comments = article.css('.l2.a2::text').extract_first()
            n_pageviews = article.css('.l1.a1::text').extract_first()
            meta = {
                'n_pageviews': n_pageviews,
                'n_comments': n_comments
            }
            yield scrapy.Request(url, self.parse, meta=meta)

        # 翻页
        page = response.meta['page'] + 1

        start = response.url.find(',f_')
        end = response.url.find('.html')
        url = response.url[:start + 3] + str(page) + response.url[end:]
        meta = {
            'page': page
        }
        yield scrapy.Request(url=url, callback=self.generate_article_urls, meta=meta, dont_filter=True)

    def parse(self, response):
        item = ArticleItem()
        item['url'] = response.url
        item['created_date'] = self.get_created_date(response)
        item['title'] = self.get_title(response)
        item['content'] = self.get_content(response)
        item['n_pageviews'] = response.meta['n_pageviews']
        item['n_comments'] = response.meta['n_comments']
        item['author_id'] = self.get_author_id(response)
        item['stock_id'] = self.get_stock_id(response)
        yield item

    def get_created_date(self, response):
        created_date = re.search(
            '\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', response.css('.zwfbtime::text').extract_first()).group()
        return created_date

    def get_title(self, response):
        title = response.css('#zwconttbt::text').extract_first().strip()
        return title

    def get_content(self, response):
        root = response.xpath('//div[@class=\'stockcodec .xeditor\']')
        mul_paragraphs = ''.join(root.xpath(
            '//*[starts-with(@id, \'paragraph\')]').xpath('string(.)').extract())
        paragraph = root.xpath('string(.)').extract_first().strip()
        content = mul_paragraphs if mul_paragraphs else paragraph
        return content

    def get_author_id(self, response):
        author_id = response.css(
            '#zwconttbn a::attr(data-popper)').extract_first()
        return author_id

    def get_stock_id(self, response):
        idx = response.url.find('news,')
        stock_id = response.url[idx + 5:idx + 11]
        return stock_id
