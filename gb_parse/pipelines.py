# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from scrapy import Request
from scrapy.pipelines.images import ImagesPipeline
from pymongo import MongoClient
from .spiders.instagram import InstaTag, InstaPost


class GbParsePipeline:
    def __init__(self):
        self.db = MongoClient()['parse_gb_11_2']
    
    def process_item(self, item, spider):
        if spider.db_type == 'MONGO':
            if type(item) is InstaTag:
                collection = self.db[spider.name + '_tags']
            if type(item) is InstaPost:
                collection = self.db[spider.name + '_posts']
            collection.insert_one(item)
        return item


class GbImagePipeline(ImagesPipeline):
    def get_media_requests(self, item, info):
        if type(item) is InstaPost:
            data = item.get('data')
            img_url = data['display_url']
            if img_url:
                yield Request(img_url)
        # for img_url in item.get('images', []):
        # for img_url in item.get('display_url', []):
        #     a = img_url
        #     yield Request(img_url)
    
    def item_completed(self, results, item, info):
        if type(item) is InstaPost:
            item['images'] = [itm[1] for itm in results]
        return item
