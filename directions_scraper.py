import json
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By

def get_directions() -> None:
    """Создает словарь, где ключами являются названия городов на русском,
    а значениями ссылки на соответствующие страницы с экскурсиями.
    Словарь записывается в json-file."""
    driver = uc.Chrome()
    driver.get('https://experience.tripster.ru/destinations/')
    cities = driver.find_elements(By.CSS_SELECTOR, "a.item-link")
    cities_dct = {}
    for city in cities:
        cities_dct[city.text.lower()] = city.get_attribute('href')

    with open("destinations.json", "w", encoding="utf-8") as file:
        json.dump(cities_dct, file, ensure_ascii=False)


