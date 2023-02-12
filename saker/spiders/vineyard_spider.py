import scrapy
import re
from ..items import SakerArticleItem
from scrapy import Selector

class VineyardSpider(scrapy.Spider):
    name = 'vineyard'
    allowed_domains = ['thesaker.is']
    start_urls = ['http://thesaker.is/']

    start_urls = [
        'https://thesaker.is',
    ]

    def parse(self, response):
        # Skip New Items category
        for option in response.css('select#archives-dropdown-2 option')[1:]:
            value = option.css('::attr(value)').get()
            yield response.follow(value, callback=self.parse_month)
    
    def parse_month(self, response):
        for link in response.css('h2.entry-title a'):
            yield response.follow(link, callback=self.parse_article)
        for nav in response.css('ul.page-numbers li a'):
            text = nav.css('::text').get()
            if(text == 'NEXT'):
                yield response.follow(nav, callback=self.parse_month)

    def parse_article(self, response):
        article = SakerArticleItem()
        article['url'] = response.url

        article_classes = response.css('article::attr(class)').get(default='')
        article['id'] = re.search('post-(\d+) ', article_classes).group(1)
        
        article['title'] = response.css('article div.post-title h1::text').get()
        
        meta = response.css('article div.entry-meta')
        article['date'] = meta.css('span.post-date::text').get(default='')
        article['category'] = meta.css('span.post-category a::text').get(default='')
        article['author'] = meta.css('span.post-author a::text').get(default='')
        
        article['image_urls'] = []
        a = response.css('article')
        a_html = a.get()
        #remove book-ads
        book_ads = a.css('.book-ads')
        for ba in book_ads:
            a_html = a_html.replace(ba.get(),'')
        #remove scripts
        scripts = a.css('script')
        for s in scripts:
            a_html = a_html.replace(s.get(),'')
        #remove post-views
        post_views = a.css('.post-views')
        for pv in post_views:
            a_html = a_html.replace(pv.get(),'')
        #remove post-comments
        post_comments = a.css('.post-comments')
        for pc in post_comments:
            a_html = a_html.replace(pc.get(),'')
        
        article['content'] = a_html
        article['image_urls'] = Selector(text=a_html).css('img::attr(data-src)').getall()
        article['image_urls'] = [x for x in article['image_urls'] if x]

        article['tags'] = response.css('article div.tag-list ul li a::text').getall()
        
        yield article