"""Обработчик команды /cancel."""

from telebot.types import Message

from loader import bot
from utils.logger import logger


@bot.message_handler(commands=["cancel"], state="*")
def cancel_search(message: Message) -> None:
    """Сбрасывает текущее состояние пользователя."""
    logger.info(
        f"Отмена текущего действия по команде /cancel. user_id={message.from_user.id}"
    )
    bot.delete_state(message.from_user.id, message.chat.id)
    bot.send_message(
        message.chat.id, "Поиск отменён. Чтобы найти трек, введи /track или /artist."
    )
