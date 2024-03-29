# TripFriendBot

### Telegram-бот

Телеграм-бот, который помогает выбрать экскурсии для предстоящей поездки. 
У пользователя запрашиваются пункт назначения и даты поездки, предпочтения по типу, на основе которой формируется список доступных экскурсий.
За подбор экскурсий отвечает Scraper, построенный с использованием библиотек BeautifulSoup4 для статического контента и Selenium для динамического, формируемого javascript.


### Технологии
- BeautifulSoup4
- Selenium
- aiogram3


### Установка
Клонируйте репозиторий:

```git clone https://github.com/ekzanoskina/TripFriend.git``

Cоздайте виртуальное окружение:

```python3 -m venv venv```

Убедитесь, что находитесь в директории TripFriend/ либо перейдите в неё:

```cd TripFriend/```

Активируйте виртуальное окружение:

Для Mac:
 
```source venv/bin/activate```

Для Windows:

```source venv/Scripts/activate```

При необходимости обновите pip:

```pip install --upgrade pip```

Установите зависимости из файла requirements.txt:

```pip install -r requirements.txt```

Из соображений безопасности токен телеграм бота хранится в файле .env В репозитории необходимо создать файл '.env' и заполнить его по шаблону:

```
TOKEN=<токен_вашего_бота>
```

### Скриншоты
Start command:

![Start command](screenshots/start.png?raw=true "Start")

Выбор дат поездки:

![Dates choosing](screenshots/dates_choosing.png?raw=true "Dates choosing")

Настройка сортировки экскурсий:

![Sorting menu](screenshots/sorting_menu.png?raw=true "Sorting menu")


### Использование
Проект задеплоен на бесперебойно работающий сервер [Heroku](https://www.heroku.com/).
Ссылка на бота https://t.me/TripFriendBot.