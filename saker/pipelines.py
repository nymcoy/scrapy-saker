# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

from scrapy.exceptions import NotConfigured
from scrapy.pipelines.images import ImagesPipeline
from scrapy.pipelines.files import FSFilesStore
import hashlib, re, os, sqlite3, urllib.parse
from io import BytesIO
from scrapy.utils.python import to_bytes
from scrapy.selector import Selector
from datetime import datetime
from .items import SakerArticleItem

class SimpleImagesPipeline(ImagesPipeline):
    def file_path(self, request, response=None, info=None, *, item=None):
        image_guid = hashlib.sha1(to_bytes(request.url)).hexdigest()
        return f'{image_guid}.jpg'

class SakerArticlePipeline:
    CSS = 'style.css'

    def __init__(self, save_dir, img_dir):
        if not save_dir or not img_dir:
            raise NotConfigured
        self.save_dir = save_dir
        self.img_dir = img_dir
        self.img_dir_rel = os.path.relpath(img_dir, start=save_dir)

    @classmethod
    def from_settings(cls, settings):
        save_dir = settings['FILES_STORE']
        img_dir = settings['IMAGES_STORE']
        return cls(save_dir, img_dir)

    def process_item(self, item, spider):
        if not isinstance(item, SakerArticleItem):
            return item #ignore non-SakerArticleItems

        content = item['content']
        #fix image links
        for img in item['images']:
            article = Selector(text=content)
            img_path = self.img_dir_rel + '/' + img['path']
            img_tag = article.css(f'img[data-src="{img["url"]}"]')
            if not img_tag:
                img_tag = article.css(f'img[data-src="{urllib.parse.unquote(img["url"])}"]')
            if not img_tag:
                continue
            old_img_src = img_tag.css('::attr(src)').get()
            new_img_tag = re.sub('data-(src|srcset|sizes)="[^"]*"', '', img_tag.get()).replace(old_img_src, img_path)
            content = content.replace(img_tag.get(), new_img_tag)
            
        article = Selector(text=content)
        for img_tag in article.css('img[data-src]'):
            img_data_src = img_tag.css('::attr(data-src)').get()
            img_src = img_tag.css('::attr(src)').get()
            new_img_tag = re.sub('data-(src|srcset|sizes)="[^"]*"', '', img_tag.get()).replace(img_src, img_data_src)
            content = content.replace(img_tag.get(), new_img_tag)
        
        #fix link to other articles on the same site
        links = []
        for link in article.css('a::attr(href)').getall():
            if '//thesaker.is/category/' in link:
                new_link = 'catindex.html'
            elif '//thesaker.is/author/' in link:
                new_link = 'authorindex.html'
            elif '//thesaker.is/tag/' in link:
                new_link = 'tagindex.html'
            elif re.search('thesaker.is/?$', link):
                new_link = 'index.html'
            else:
                new_link = re.sub('^https?://thesaker.is/([^/]*)/?$', r'\1.html', link)
            
            links.append((item['url'], new_link))
            content = content.replace(link,new_link)

        html = f'''<!DOCTYPE html>
<html lang="en-us">
  <head>
    <title>{ item['title'] } | The Vineyard of the Saker</title>
    <link rel="stylesheet" href="{ self.CSS }" />
  </head>
  <body>
    <ul id="menu">
      <li><a href="index.html">Home</a></li>
      <li><a href="dateindex.html">Articles by Date</a></li>
      <li><a href="authorindex.html">Articles by Author</a></li>
      <li><a href="catindex.html">Articles by Category</a></li>
      <li><a href="tagindex.html">Articles by Tag</a></li>
    </ul>
    <article>
{ content }
    </article>
  </body>
</html>'''

        filename = item['url'][19:-1] + '.html'
        fs = FSFilesStore(self.save_dir)
        fs.persist_file(filename, BytesIO(html.encode()), None)

        #db
        cur = self.db.cursor()
        insert_article='''INSERT INTO articles 
            (article_url, article_path, article_id, article_title, article_date, article_category, article_author) 
            VALUES (?, ?, ?, ?, ?, ?, ?);'''
        try:
            d = datetime.strptime(item['date'],'%B %d, %Y')
        except:
            d = None;
        data = (item['url'], filename, item['id'], item['title'], d, item['category'], item['author'])
        cur.execute(insert_article, data)

        insert_links = '''INSERT INTO links
            (from_url, to_url)
            VALUES (?, ?);'''
        cur.executemany(insert_links, links)

        insert_tags = '''INSERT INTO tags
            (article_url, tag)
            VALUES (?, ?);'''
        cur.executemany(insert_tags, [(item['url'], t) for t in item['tags']])
        self.db.commit()
        cur.close()
        return item

    def open_spider(self, spider):
        fs = FSFilesStore(self.save_dir)
        with open('saker/sakerstyle.css', 'rb') as file:
            fs.persist_file('style.css', BytesIO(file.read()), None)
        self.db = sqlite3.connect(f'{ self.save_dir }/saker.db')
        with open('saker/sakerschema.sql') as fp:
            self.db.executescript(fp.read())

    def close_spider(self, spider):
        fs = FSFilesStore(self.save_dir)
        fs.persist_file('dateindex.html', BytesIO(self.generate_date_index().encode()), None)
        fs.persist_file('authorindex.html', BytesIO(self.generate_author_index().encode()), None)
        fs.persist_file('catindex.html', BytesIO(self.generate_category_index().encode()), None)
        fs.persist_file('tagindex.html', BytesIO(self.generate_tag_index().encode()), None)
        fs.persist_file('index.html', BytesIO(self.generate_index().encode()), None)
        if self.db:
            self.db.close()

############################
# Indexes
###########################
    styles = '''
body {
    color:#444;
    font-size: 14px;
    line-height:21px;
}

html {
    font-family: sans-serif;
    -webkit-text-size-adjust: 100%;
    -ms-text-size-adjust: 100%
}

*, *:before, *:after {
    -webkit-box-sizing: border-box;
    -moz-box-sizing: border-box;
    -ms-box-sizing: border-box;
    -o-box-sizing: border-box;
    box-sizing: border-box
}

h1{
    color:#222;
    font-weight: normal;
    line-height: 1.3;
    margin-top:2px;
    margin-bottom:12px
    font-size: 36px;
}

details {
  cursor: pointer;
  display: block;
  padding-left: 1em;
}

ul#menu {
  display: block;
  margin: 0;
  padding: 0;
  overflow: hidden;
  margin-bottom: 20px;
  border-top: 1px solid #f0f0f0;
  border-bottom: 1px solid #f0f0f0;
}

ul#menu li {
  display: inline;
  border-right: 1px solid #f0f0f0;
  display: inline-block;
  padding: 6px 14px;
  font-size: 14px;
}

'''
    def content_header(self, title):
        return f'''<!DOCTYPE html>
<html>
  <head>
    <title>{ title } | Vineyard of the Saker</title>
    <style>{ self.styles }</style>
  </head>
  <body>
    <ul id="menu">
      <li><a href="index.html">Home</a></li>
      <li><a href="dateindex.html">Articles by Date</a></li>
      <li><a href="authorindex.html">Articles by Author</a></li>
      <li><a href="catindex.html">Articles by Category</a></li>
      <li><a href="tagindex.html">Articles by Tag</a></li>
    </ul>
    <h1>{ title }</h1>
'''

    def content_footer(self):
        return'''
  </body>
</html>
'''
    def generate_date_index(self):
        content = self.content_header('Articles by Date')

        x = self.db.cursor()
        x.execute('select distinct strftime("%Y", article_date) as year from articles order by year desc;')
        
        for year, in x:
            content += f'''
    <details>
      <summary>{ year }</summary>'''

            y = self.db.cursor()
            if not year:
                y.execute('''select article_path, article_title, article_date, article_id 
                    from articles where article_date is null order by article_id;''')
                content += '''
      <ul>'''
                for path, title, d, id in y:
                    content += f'''
        <li><a href="{ path.replace('/','') }">{ title }</a></li>'''
                content += '''
      </ul>'''
            else:        
                y.execute('''select distinct strftime("%m", article_date) as month, 
                    strftime("%Y", article_date) as year from articles 
                    where year = ? order by month;''', (year,))
                for month, yr in y:
                    content += f'''
      <details>
        <summary>{ month }</summary>
        <ul>'''
                    z = self.db.cursor()
                    z.execute('''select article_path, article_title, article_date, 
                        strftime("%m", article_date) as month, strftime("%Y", article_date) as year 
                        from articles where year = ? and month = ? order by article_date;''', (year, month))
                    for path, title, d, mm, yy in z:
                        content += f'''
          <li>{d[8:10]}: <a href="{ path.replace('/','') }">{ title }</a></li>'''
                    z.close()
                    content += '''
        </ul>
      </details>'''
            y.close()
            content += '''
    </details>'''

        x.close()
        content += self.content_footer()   
        return content

    def generate_author_index(self):
        content = self.content_header('Articles by Author')

        x = self.db.cursor()
        x.execute('select article_author, count(*) as ct from articles group by article_author order by ct desc;')

        for author, ct in x:
            content += f'''
    <details>
      <summary>{ author if author else "None" }</summary>
      <ul>'''
            y = self.db.cursor()
            y.execute('''select article_path, article_title, article_author, article_date from articles 
            where article_author = ? order by article_date;''', (author,))
            for path, title, auth, d in y:
                if not d:
                    d = '0000-00-00 00:00:00'
                content += f'''
        <li>{d[:-9]}: <a href="{ path.replace('/','') }">{ title }</a></li>'''
            y.close()
            content += '''
      </ul>
    </details>'''
            
        x.close()
        content += self.content_footer()   
        return content
    
    def generate_category_index(self):
        content = self.content_header('Articles by Category')
        
        x = self.db.cursor()
        x.execute('select distinct article_category from articles order by article_category;')

        for category, in x:
            content += f'''
    <details>
      <summary>{ category if category else "None" }</summary>
      <ul>'''
            y = self.db.cursor()
            y.execute('''select article_path, article_title, article_category, article_date from articles 
            where article_category = ? order by article_date;''', (category,))
            for path, title, cat, d in y:
                if not d:
                    d = '0000-00-00 00:00:00'
                content += f'''
        <li>{d[:-9]}: <a href="{ path.replace('/','') }">{ title }</a></li>'''
            y.close()
            content += '''
      </ul>
    </details>'''
        
        x.close()
        content += self.content_footer()   
        return content

    def generate_tag_index(self):
        content = self.content_header('Articles by Tag')

        x = self.db.cursor()
        x.execute('select distinct tag from tags order by tag;')

        for tag, in x:
            content += f'''
    <details>
      <summary>{ tag }</summary>
      <ul>'''
            y = self.db.cursor()
            y.execute('''select articles.article_path, articles.article_title, articles.article_date, tags.tag 
            from articles join tags on articles.article_url=tags.article_url 
            where tags.tag = ?
            order by articles.article_date;''', (tag,))
            for path, title, d, t in y:
                if not d:
                    d = '0000-00-00 00:00:00'
                content += f'''
        <li>{d[:-9]}: <a href="{ path.replace('/','') }">{ title }</a></li>'''
            y.close()
            content += '''
      </ul>
    </details>'''
        x.close()
        content += self.content_footer()   
        return content

    def generate_index(self):
        content = self.content_header('Welcome to the Saker Archive!')
        content += '''
        <ul>
          <li><h2><a href="dateindex.html">Articles by Date</a></h2></li>
          <li><h2><a href="authorindex.html">Articles by Author</a></h2></li>
          <li><h2><a href="catindex.html">Articles by Category</a></h2></li>
          <li><h2><a href="tagindex.html">Articles by Tag</a></h2></li>
        </ul>
'''
        content += self.content_footer()
        return content