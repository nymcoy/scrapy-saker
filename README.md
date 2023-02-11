# scrapy-saker
A script to scrape [The Vineyard of the Saker](https://thesaker.is/) before it goes defunct after February 2023.

## Environment Setup
**Here are instructions for an Ubuntu 20.04 machine.**
If you don't got 'em:
```
$ sudo apt install python3 git
```

It is recommended to install and run [scrapy](https://scrapy.org/) in a virtual environment:
```
$ python3 -m venv scrapy
$ cd scrapy
$ source bin/activate
```
To exit the environment later:
```
$ deactivate
```

Next, install scrapy:
```
$ pip install scrapy
```

Get and run this project:
```
$ git clone https://github.com/nymcoy/scrapy-saker.git saker
$ cd saker
$ scrapy crawl vineyard
```
or to save the output to a file:
```
$ scrapy crawl vineyard 2> >(tee saker.log)
```
## Notes
 - When the spider is run, the stripped down html articles will download in a directory called **out**. This is modifyable in **settings.py**.
 - There is a  cache set up by default, and raw scraped pages and images are downloaded to **.scrapy/httpcache/saker**. Therefore running the spider multiple times will not crawl the live site multiple times. You can turn this feature off in **settings.py**.
 - All internal links and image sources are relative and should continue to work wherever you move the out directory.
 - Also created is a sqlite file called **saker.db** which was used to generate the indexes, but might be of use to you. Full text search is not implemented.
