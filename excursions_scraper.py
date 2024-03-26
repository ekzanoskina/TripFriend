import re
from datetime import datetime
from typing import List

import requests
from bs4 import BeautifulSoup



def get_available_excursions(city_url:str, start_date:datetime, end_date:datetime, sorting='?sorting=rating', type:str=None) -> List[tuple]:
    """На основе переданных пользователем данных функция скрапит информацию о подходящих эксурсиях"""
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    }
    url = city_url + sorting + f'&end_date={end_date.strftime("%Y-%m-%d")}' + f'&start_date={start_date.strftime("%Y-%m-%d")}'
    if type:
        url += type
    r = requests.get(url=url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")
    excursions_dict = {}
    excursions = soup.select('div.exp-list-item-wrapper.exp-snippet')
    for i, ex in enumerate(excursions[:15], 1):
        id = re.search(r'\d+', ex.find("a", "exp-header", href=True).get('href')).group()
        excursions_dict[id] = {'title': ex.find("span", "title").text.strip(),
                               'description': ex.find('div', 'tagline').text.strip(),
                               'price': ex.find('span', 'price-current').text if ex.find('span',
                                                                                         'price-current') else '0 руб.',
                               'reviews_number': ex.find('a', 'reviews').text.strip() if ex.find(
                                   'a', 'reviews') else 0,
                               'rating_value': ex.find('span', 'rating-value').text.strip() if ex.find('span',
                                                                                                       'rating-value') else '0 отзывов',
                               'rating_place': i,
                               'duration': ex.find('div', 'duration').text if ex.find('div', 'duration') else 0,
                               'movement_type': ex.find('div', 'movement').text if ex.find('div', 'movement') else None,
                               'type': ex.find('div', 'type').text.strip(),
                               'url': ex.find("a", "exp-header", href=True).get('href'),
                               'image': ex.find('img', 'exp-pic')['data-src'] if ex.find('img', 'exp-pic') else None}
    return list(excursions_dict.items())
