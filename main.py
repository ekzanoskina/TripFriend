import logging
import os
from typing import Dict

from aiogram.client.default import DefaultBotProperties
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from datetime import datetime, timedelta
from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.filters.callback_data import CallbackData
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, CallbackQuery, ReplyKeyboardRemove, InputFile, \
    URLInputFile
from aiogram.utils.markdown import hbold, hunderline, hcode, hlink
import asyncio
import re
import json
from excursions_scraper import get_available_excursions
from dotenv import load_dotenv

load_dotenv()

# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)
# Объект бота
TOKEN = os.getenv('TOKEN')
bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
# Диспетчер
dp = Dispatcher()

from directions_scraper import get_directions

# если файл со ссылками на экскурсии по городам еще не был создан, то он создается в начале работы программы
if not os.path.exists('destinations.json'):
    get_directions()
with open("destinations.json", "r", encoding="utf-8") as file:
    destinations = json.load(file)


class TripInfo(StatesGroup):
    """Класс определяющий этапы взаимодействия с ботом в виде состояний конечного автомата."""
    choosing_city = State()
    choosing_start_date = State()
    choosing_end_date = State()
    showing_type_filtered_trips = State()
    showing_sorted_trips = State()


def make_row_keyboard(items: list[str]) -> ReplyKeyboardMarkup:
    """Создаёт реплай-клавиатуру с кнопками в один ряд"""
    row = [KeyboardButton(text=item) for item in items]
    return ReplyKeyboardMarkup(keyboard=[row], resize_keyboard=True)


# кнопки-подсказки для выбора города
cities = [
    [
        KeyboardButton(text='Москва'),
        KeyboardButton(text='Санкт-Петербург'),
        KeyboardButton(text='Калининград'),
    ],
    [
        KeyboardButton(text='Дубай'),
        KeyboardButton(text='Стамбул'),
        KeyboardButton(text='Тбилиси'),
    ],
]

cities_kb = ReplyKeyboardMarkup(keyboard=cities, resize_keyboard=True)


@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    """Хэндлер на команду /start"""
    await message.answer(
        text="Добро пожаловать в TripFriend!\nЯ сделаю твой отдых незабываемым. Введи название города, в который собираешься, или выбери из списка ниже:",
        reply_markup=cities_kb
    )
    await state.set_state(TripInfo.choosing_city)


@dp.message(TripInfo.choosing_city, F.text.lower().in_(destinations))
async def city_chosen(message: Message, state: FSMContext):
    """
    Обрабатывает выбор города.

    Функция принимает сообщение от пользователя и текущее состояние конечного автомата.
    Она сохраняет выбранный пользователем город в нижнем регистре и предлагает выбрать дату начала поездки.

    :param message: Входящее сообщение с выбором города от пользователя.
    :param state: Текущее состояние конечного автомата.
    """
    #  Обновляет текущее состояние, сохраняя выбранный город в нижнем регистре.
    await state.update_data(chosen_city=message.text.lower())
    # Генерирует календарь для выбора даты начала поездки с учетом локализации пользователя и задает диапазон дат.
    calendar = SimpleCalendar(show_alerts=True)
    calendar.set_dates_range(datetime(2022, 1, 1), datetime(2025, 12, 31))
    # Отправляет пользователю сообщение с просьбой выбрать дату начала поездки и прикрепляет сгенерированный календарь.
    await message.answer(
        text='Спасибо! Теперь выберите дату начала поездки.',
        reply_markup=await calendar.start_calendar(year=datetime.today().year, month=datetime.today().month)
    )
    # Устанавливает новое состояние конечного автомата `TripInfo.choosing_start_date`, переводя процесс в следующий этап выбора.
    await state.set_state(TripInfo.choosing_start_date)


@dp.message(TripInfo.choosing_city)
async def city_chosen_incorrectly(message: Message):
    """
    Информирует пользователя о неправильном выборе города и просит ввести корректное название города.

    :param message: Входящее сообщение с неправильным выбором города от пользователя.
    """
    await message.answer(
        text="Я не знаю такого города.\n"
             "Пожалуйста, выберите одно из названий из списка ниже или введите корректное название города:",
        reply_markup=cities_kb
    )


@dp.callback_query(TripInfo.choosing_start_date, SimpleCalendarCallback.filter())
async def process_start_date_choosing(callback_query: CallbackQuery, callback_data: CallbackData, state: FSMContext):
    """
    Обрабатывает выбор начальной даты путешествия через интерфейс календаря.

    Пользователю предлагается календарь для выбора начальной даты путешествия. Диапазон допустимых дат ограничен
    текущим годом и задаётся в коде функции. Выбранная дата сохраняется в состоянии и пользователю предлагается
    выбрать дату окончания поездки.

    :param callback_query: Колбэк запрос от нажатия кнопки календаря пользователем.
    :param callback_data: Данные, связанные с колбэком.
    :param state: Текущее состояние конечного автомата.
    """
    calendar = SimpleCalendar(show_alerts=True
                              )
    today_date = datetime.today()
    # Валидация выбора даты с помощью диапазона, доступного в календаре. Не может предшествовать текущей дате.
    calendar.set_dates_range(today_date - timedelta(days=1), datetime(day=today_date.day, month=today_date.month, year=today_date.year + 1))
    selected, date = await calendar.process_selection(callback_query, callback_data)
    if selected:
        # Сохраняет дату начала поездки в машину состояний
        await state.update_data(start_date=date)
        await callback_query.message.answer(
            f'Вы выбрали {date.strftime("%d.%m.%Y")}')
        # Генерирует календарь для выбора даты конца поездки.
        # Начальные значения даты и месяца - дата и месяц, выбранные пользователем в качестве начала поездки
        await callback_query.message.answer(
            'Выберите дату окончания поездки.',
            reply_markup=await calendar.start_calendar(year=date.year, month=date.month)
        )
        # Устанавливает новое состояние конечного автомата `TripInfo.choosing_end_date`, переводя процесс в выбор конечной даты.
        await state.set_state(TripInfo.choosing_end_date)


ex_types = ['Индивидуальные', 'Групповые', 'Все']


@dp.callback_query(TripInfo.choosing_end_date, SimpleCalendarCallback.filter())
async def process_end_date_choosing(callback_query: CallbackQuery, callback_data: CallbackData, state: FSMContext):
    """
    Обрабатывает выбор конечной даты путешествия через интерфейс календаря.

    Аналогично функции выбора начальной даты, пользователю предоставляется календарь для выбора конечной даты путешествия.
    Выбранная дата сохраняется в состоянии, после чего пользователю будут предложены варианты типа поездки.

    :param callback_query: Колбэк запрос от нажатия кнопки календаря пользователем.
    :param callback_data: Данные, связанные с колбэком.
    :param state: Текущее состояние конечного автомата.
    """
    calendar = SimpleCalendar(show_alerts=True)
    user_data = await state.get_data()
    calendar.set_dates_range(user_data['start_date'],
                             datetime(day=user_data['start_date'].day, month=user_data['start_date'].month,
                                      year=user_data['start_date'].year + 1))
    selected, date = await calendar.process_selection(callback_query, callback_data)
    if selected:
        await state.update_data(end_date=date)
        await callback_query.message.answer(
            f'Вы выбрали {date.strftime("%d.%m.%Y")}',
            reply_markup=make_row_keyboard(ex_types),
        )
        await state.set_state(TripInfo.showing_type_filtered_trips)


def form_trip_content(ex_info: Dict) -> str:
    """
    Формирует сообщение для отправки информации об экскурсии в Telegram чат.

    Создаёт текстовое представление информации об экскурсии с использованием переданного словаря данных.
    Возвращает сформированную строку, которую можно напрямую отправить в чат.

    :param ex_info: Словарь с информацией об экскурсии.
    :return: Строка с описанием экскурсии для отправки в Telegram.
    """
    content = (f'{hlink(ex_info["title"], "https://experience.tripster.ru" + ex_info["url"])}\n'
               f'{ex_info["description"]}\n'
               f'{hbold("Вид")}: {ex_info["type"].title()}\n'
               f'{hbold("Оценка")}: {hlink(str(ex_info["rating_value"]), "https://experience.tripster.ru" + ex_info["url"] + "#reviews")} ({ex_info["reviews_number"]})\n'
               f'{hbold("Стоимость")}: {ex_info["price"]}\n'
               f'{hbold("Продолжительность")}: {ex_info["duration"]}\n'
               f'{hbold("Способ передвижения")}: {ex_info["movement_type"]}'
               )
    return content


sorting = ['По продолжительности ↑', 'По цене ↑', 'По оценке ↓']

sorting_kb = ReplyKeyboardMarkup(keyboard=[
    [
        KeyboardButton(text=sorting[0])
    ],
    [
        KeyboardButton(text=sorting[1]),
        KeyboardButton(text=sorting[2])
    ],
], resize_keyboard=True)


@dp.message(TripInfo.showing_type_filtered_trips, F.text.in_(ex_types))
async def show_all_trips(message: Message, state: FSMContext):
    """
    Показывает все доступные экскурсии в соответствии с выбранными фильтрами.

    Отфильтровывает экскурсии по типу (групповые или индивидуальные) на основе ввода пользователя,
    запрашивает доступные экскурсии через API и отправляет их список пользователю.

    :param message: Объект сообщения, содержащий детали и текст сообщения пользователя.
    :param state: Состояние конечного автомата, позволяющее хранить и получать данные пользователя.
    """
    user_data = await state.get_data()
    excursions_args = {'city_url': destinations.get(user_data['chosen_city']), 'start_date': user_data['start_date'],
                       'end_date': user_data['end_date']}
    if message.text.lower() == 'групповые':
        excursions_args.update(type='&type=group,ticket')
    elif message.text.lower() == 'индивидуальные':
        excursions_args.update(type='&type=private')
    excursions_list = get_available_excursions(**excursions_args)
    await state.update_data(excursions_list=excursions_list)
    for ex_id, ex_info in excursions_list:
        content = form_trip_content(ex_info)
        await message.answer_photo(URLInputFile(ex_info['image']), caption=content)

    await message.answer('Отсортировать экскурсии?', reply_markup=sorting_kb)
    await state.set_state(TripInfo.showing_sorted_trips)


@dp.message(TripInfo.choosing_city)
async def type_chosen_incorrectly(message: Message):
    """
    Информирует пользователя о некорректном выборе типа экскурсии.

    :param message: Объект сообщения, содержащий детали и текст сообщения пользователя.
    """
    await message.answer(
        text="Я не знаю такого типа.\n"
             "Пожалуйста, выберите один из типов ниже:",
        reply_markup=make_row_keyboard(ex_types)
    )


@dp.message(TripInfo.showing_sorted_trips, F.text.in_(sorting))
async def show_sorted_trips(message: Message, state: FSMContext):
    """
    Показывает экскурсии, отсортированные в соответствии с выбором пользователя.

    Осуществляет сортировку списка экскурсий по цене, оценке или продолжительности
    и отправляет отсортированный список пользователю.

    :param message: Объект сообщения, содержащий детали и текст сообщения пользователя.
    :param state: Состояние конечного автомата, позволяющее хранить и получать данные пользователя.
    """
    user_data = await state.get_data()
    excursions_list = user_data['excursions_list']
    if message.text.lower() == 'по цене ↑':
        print(sorted(excursions_list, key=lambda x: re.search(r'\d+\s?\d+', x[1]['price']).group().replace('13\xa0600', '')))
        sorted_list = sorted(excursions_list, key=lambda x: int(re.search(r'\d+\s?\d+', x[1]['price']).group().replace('\xa0', '')))
    elif message.text.lower() == 'по оценке ↓':
        sorted_list = sorted(excursions_list, key=lambda x: float(re.search(r'\d+\.\d+', x[1]['rating_value']).group()),
                             reverse=True)
    elif message.text.lower() == 'по продолжительности ↑':
        sorted_list = sorted(excursions_list,
                             key=lambda x: float(re.search(r'\d+\.?\d*', x[1]['duration']).group()))
    else:
        sorted_list = excursions_list
    for ex_id, ex_info in sorted_list:
        content = form_trip_content(ex_info)
        await message.answer_photo(URLInputFile(ex_info['image']), caption=content)


@dp.message(TripInfo.showing_sorted_trips)
async def sorting_chosen_incorrectly(message: Message):
    """
    Информирует пользователя о некорректном выборе типа сортировки.

    :param message: Объект сообщения, содержащий детали и текст сообщения пользователя.
    """
    await message.answer(
        text="Я не знаю такого типа сортировки.\n"
             "Пожалуйста, выберите один из типов ниже:",
        reply_markup=sorting_kb)


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
