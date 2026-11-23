"""Модуль установки команд бота в меню Telegram."""

from telebot.types import BotCommand
from config_data.config import DEFAULT_COMMANDS
from utils.logger import logger


def set_default_commands(bot):
    """Устанавливает список команд бота для меню."""
    commands = [BotCommand(*i) for i in DEFAULT_COMMANDS]
    bot.set_my_commands(commands)
    logger.info(f"Команды меню бота установлены: {[c.command for c in commands]}")
