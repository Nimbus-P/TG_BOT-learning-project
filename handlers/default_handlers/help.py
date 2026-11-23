"""Обработчик команды /help."""

from telebot.types import Message

from config_data.config import DEFAULT_COMMANDS
from loader import bot
from utils.logger import logger


@bot.message_handler(commands=["help"])
def bot_help(message: Message):
    """Выводит список доступных команд бота."""
    logger.info(f"Запрос справки. user_id={message.from_user.id}")
    text = [f"/{command} - {desk}" for command, desk in DEFAULT_COMMANDS]
    bot.reply_to(message, "\n".join(text))
