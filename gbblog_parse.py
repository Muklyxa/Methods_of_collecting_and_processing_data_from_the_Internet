from typing import Tuple, Set
import bs4
import requests
import datetime as dt
from urllib.parse import urljoin
from database import GBDataBase


class GbBlogParse:

    def __init__(self, start_url):
        self.start_url = start_url
        self.page_done = set()
        self.db = GBDataBase('sqlite:///gb_blog.db')

    def _get(self, url):
        response = requests.get(url)
        # todo Обработка статусов и ошибки
        self.page_done.add(url)
        return bs4.BeautifulSoup(response.text, 'lxml')

    def run(self, url=None):
        if not url:
            url = self.start_url

        if url not in self.page_done:
            soup = self._get(url)
            posts, pagination = self.parse(soup)
            for post_url in posts:
                page_data = self.page_parse(self._get(post_url), post_url)
                self.save(page_data)

            for pag_url in pagination:
                self.run(pag_url)

    def parse(self, soup) -> Tuple[Set[str], Set[str]]:
        pag_ul = soup.find('ul', attrs={'class': 'gb__pagination'})
        paginations = set(
            urljoin(self.start_url, p_url.get('href')) for p_url in pag_ul.find_all('a') if p_url.get('href')
        )
        posts_wrapper = soup.find('div', attrs={'class': 'post-items-wrapper'})

        posts = set(
            urljoin(self.start_url, post_url.get('href')) for post_url in
            posts_wrapper.find_all('a', attrs={'class': 'post-item__title'})
        )

        return posts, paginations

    def page_parse(self, soup, url) -> dict:
        data = {
            'post_data': {'url': url,
                          'title': soup.find('h1', attrs={'class': 'blogpost-title'}).text,
                          'img_url': soup.find('div', attrs={'class': 'blogpost-content'}).find_next('img').get('src'),
                          'date': dt.datetime.strptime(soup.find('div', attrs={'class': 'blogpost-date-views'}).find_next('time').get('datetime')[0:19], "%Y-%m-%dT%H:%M:%S")
                          },
            'writer': {
                'name': soup.find('div', attrs={'itemprop': 'author'}).text,
                'url': urljoin(self.start_url, soup.find('div', attrs={'itemprop': 'author'}).parent.get('href'))
            },
            'tags': [],
            'comments': []
        }
        for tag in soup.find_all('a', attrs={'class': "small"}):
            tag_data = {
                'url': urljoin(self.start_url, tag.get('href')),
                'name': tag.text
            }
            data['tags'].append(tag_data)

        # get comments
        commenttable_id = soup.find('comments').get('commentable-id')
        response = requests.get("https://geekbrains.ru/api/v2/comments?commentable_type=Post&commentable_id=" + str(commenttable_id))
        comments = response.json()
        for comment in comments:
            comment = comment['comment']
            comment_data = {
                'url': comment['user']['url'],
                'name': comment['user']['full_name'],
                'text': comment['body']
            }
            data['comments'].append(comment_data)
        return data

    def save(self, post_data: dict):
        self.db.create_post(post_data)


if __name__ == '__main__':
    parser = GbBlogParse('https://geekbrains.ru/posts')
    parser.run()
