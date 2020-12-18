# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from scrapy import Request
from scrapy.pipelines.images import ImagesPipeline
from pymongo import MongoClient
from .spiders.instagram import InstaTag, InstaPost, InstaUser, InstaFollow, InstaFollower


class GbParsePipeline:
    def __init__(self):
        self.db = MongoClient()['parse_gb_11_2']
    
    def process_item(self, item, spider):
        if spider.db_type == 'MONGO':
            if type(item) is InstaUser:
                collection = self.db[spider.name + '_users']
            if type(item) is InstaFollow:
                collection = self.db[spider.name + '_follow']
            if type(item) is InstaFollower:
                collection = self.db[spider.name + '_followers']
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
