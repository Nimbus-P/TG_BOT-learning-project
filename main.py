"""Точка входа бота.

Инициализирует фильтры состояний, создаёт таблицы БД, устанавливает команды
меню и запускает polling Telegram-бота.
"""
import os

from loader import bot
import handlers  # noqa
from telebot.custom_filters import StateFilter
from database.model import create_models
from utils.set_bot_commands import set_default_commands
from utils.logger import logger

if __name__ == "__main__":
    os.makedirs("logs", exist_ok=True)
    logger.info("Запуск бота...")
    bot.add_custom_filter(StateFilter(bot))
    create_models()
    set_default_commands(bot)
    logger.info("Бот запущен. Ожидание обновлений...")
    bot.infinity_polling()
