"""Модуль подключения к базе данных.

Создаёт объект подключения SqliteDatabase на основе пути из конфигурации.
Используется моделями проекта через BaseModel.Meta.database.
"""

from peewee import SqliteDatabase
from config_data.config import DB_PATH

# Подключение к файлу базы данных SQLite.
db = SqliteDatabase(DB_PATH)
