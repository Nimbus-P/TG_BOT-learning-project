"""Конфигурация проекта.

Загружает переменные окружения из .env, проверяет их наличие,
содержит константы бота, настройки Jamendo API и список команд меню.
"""

import os
from dotenv import load_dotenv, find_dotenv


if not find_dotenv():
    exit("Переменные окружения не загружены т.к отсутствует файл .env")
else:
    load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

RAPID_API_KEY = os.getenv("RAPID_API_KEY")

#API_BASE_URL = "https://api.jamendo.com/v3.0/"
API_BASE_URL = 'https://bakha.me/hitmoz/'

DEFAULT_COMMANDS = (
    ("start", "Запустить бота"),
    ("track", "Поиск по названию"),
    ("chart", "Показать чарт"),
    ("history", "Просмотр истории поиска"),
    ("cancel", "Отмена поиска"),
    ("help", "Вывести справку"),
)

DB_PATH = "music_bot.db"
PAGE_SIZE = 10