"""Эхо-хендлер для необработанных текстовых сообщений."""

from telebot.types import Message

from loader import bot
from utils.logger import logger


# Эхо хендлер, куда летят текстовые сообщения без указанного состояния
@bot.message_handler(state=None)
def bot_echo(message: Message):
    """Обрабатывает сообщения, не соответствующие ни одной команде/состоянию."""
    logger.info(
        f"Необработанное сообщение. user_id={message.from_user.id}, text='{message.text}'"
    )
    bot.reply_to(
        message,
        "Я не понимаю эту команду. Используйте /help для просмотра списка доступных команд.",
    )
