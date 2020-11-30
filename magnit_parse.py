import os
import time
import datetime as dt
import requests
import bs4
import pymongo
import dotenv
from urllib.parse import urljoin

dotenv.load_dotenv('.env')

months = {"янв": 1, "фев": 2, "мар": 3, "апр": 4, "мая": 5, "июн": 6,
          "июл": 7, "авг": 8, "сен": 9, "окт": 10, "ноя": 11, "дек": 12}

class MagnitParse:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.16; rv:83.0) Gecko/20100101 Firefox/83.0'
    }

    def __init__(self, start_url):
        self.start_url = start_url
        client = pymongo.MongoClient(os.getenv('DATA_BASE'))
        self.db = client['gb_parse_11']

        self.product_template = {
            'url': lambda soup: urljoin(self.start_url, soup.get('href')),
            'promo_name': lambda soup: soup.find('div', attrs={'class': 'card-sale__header'}).text,
            'product_name': lambda soup: soup.find('div', attrs={'class': 'card-sale__title'}).text,
            "old_price": lambda soup: int(soup.find('div', attrs={'class': 'label__price_old'}).find_next('span',
                                                                                                          attrs={
                                                                                                              'class': 'label__price-integer'}).text)
                                      + float(soup.find('div', attrs={'class': 'label__price_old'}).find_next('span',
                                                                                                              attrs={
                                                                                                                  'class': 'label__price-decimal'}).text) / 100,
            "new_price": lambda soup: int(soup.find('div', attrs={'class': 'label__price_new'}).find_next('span',
                                                                                                          attrs={
                                                                                                              'class': 'label__price-integer'}).text)
                                      + float(soup.find('div', attrs={'class': 'label__price_new'}).find_next('span',
                                                                                                              attrs={
                                                                                                                  'class': 'label__price-decimal'}).text) / 100,
            'image_url': lambda soup: urljoin(self.start_url, soup.find('img').get('data-src')),
            "date_from": lambda soup: dt.datetime(dt.datetime.today().year,
                                                  months[soup.find('div',
                                                                   attrs={'class': 'card-sale__date'}).find_next('p').text.split()[2][0:3]],
                                                  int(soup.find('div',
                                                            attrs={'class': 'card-sale__date'}).find_next('p').text.split()[1])),
            "date_to": lambda soup: dt.datetime(dt.datetime.today().year,
                                                  months[soup.find('div',
                                                                   attrs={'class': 'card-sale__date'}).find_next('p').find_next('p').text.split()[2][0:3]],
                                                  int(soup.find('div',
                                                            attrs={'class': 'card-sale__date'}).find_next('p').find_next('p').text.split()[1]))
        }

    @staticmethod
    def _get(*args, **kwargs):
        while True:
            try:
                response = requests.get(*args, **kwargs)
                if response.status_code != 200:
                    raise Exception
                return response
            except Exception:
                time.sleep(0.5)

    def soup(self, url) -> bs4.BeautifulSoup:
        response = self._get(url, headers=self.headers)
        return bs4.BeautifulSoup(response.text, 'lxml')

    def run(self):
        soup = self.soup(self.start_url)
        for product in self.parse(soup):
            self.save(product)

    def parse(self, soup):
        catalog = soup.find('div', attrs={'class': 'сatalogue__main'})

        for product in catalog.find_all('a', recursive=False):
            pr_data = self.get_product(product)
            yield pr_data

    def get_product(self, product_soup) -> dict:

        result = {}
        for key, value in self.product_template.items():
            try:
                result[key] = value(product_soup)
            except Exception as e:
                continue
        return result

    def save(self, product):
        collection = self.db['magnit_11']
        collection.insert_one(product)


if __name__ == '__main__':
    parser = MagnitParse('https://magnit.ru/promo/?geo=moskva')
    parser.run()

