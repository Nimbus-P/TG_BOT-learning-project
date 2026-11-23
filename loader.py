"""Инициализация бота.

Создаёт объект TeleBot с хранилищем состояний StateMemoryStorage
и токеном из конфигурации.
"""
from telebot import TeleBot
from telebot.storage import StateMemoryStorage
from config_data import config

storage = StateMemoryStorage()
bot = TeleBot(token=config.BOT_TOKEN, state_storage=storage)

