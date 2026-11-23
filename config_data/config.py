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

API_KEY = os.getenv("API_KEY")


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