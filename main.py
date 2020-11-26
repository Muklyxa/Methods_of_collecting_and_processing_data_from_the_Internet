import requests
import json

# header creating
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36'
}

# url for categories
url = "https://5ka.ru/api/v2/categories/"

# get categories
response = requests.get(url, headers=headers)
data: dict = response.json()

# for all categories
for cat in data:
    # create file
    with open(cat['parent_group_name']+'.json', 'w', encoding='UTF-8') as file:
        # url for current categories
        url = "https://5ka.ru/api/v2/special_offers/?&categories="
        url = url + cat['parent_group_code']

        # get products
        response = requests.get(url, headers=headers)
        products: dict = response.json()
        cat['products'] = products.get('results')

        # save in file
        json.dump(cat, file, ensure_ascii=False, indent=4, separators=(",", ": "))
