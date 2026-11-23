"""Обработчик команды /start.

Регистрирует пользователя в базе данных при первом запуске бота,
при повторном обращении выводит приветствие без дублирования записи.
"""

from peewee import IntegrityError
from telebot.types import Message

from database.model import User
from loader import bot
from utils.logger import logger


text = """
🎵 Привет! Я музыкальный бот.
Помогу найти музыку и послушать понравившиеся композиции прямо в Telegram.

🔎 Что я умею:
Искать треки по названию или исполнителю.
Показывать найденные композиции.
Отправлять аудио для прослушивания.
Сохранять историю поисковых запросов.
Показывать музыкальный чарт, если эта функция доступна у выбранного источника.

🎧 Как начать?
Введи команду /track, а затем отправь название песни или имя исполнителя.
Команда /history покажет историю твоих поисков.
Используй /help, чтобы посмотреть все доступные команды.

Приятного прослушивания! 🎶
"""

@bot.message_handler(commands=["start"])
def bot_start(message: Message):
    """Обработчик команды /start.

    При первом обращении создаёт запись пользователя в таблице User.
    Если пользователь уже зарегистрирован (IntegrityError по user_id),
    выводит приветствие для повторного визита.

    Args:
        message: Входящее сообщение Telegram.
    """
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name

    try:
        User.create(
            user_id=user_id,
            username=username or "",
            first_name=first_name,
            last_name=last_name,
        )
        logger.info(
            f"Новый пользователь зарегистрирован. user_id={user_id}, username={username or ''}, first_name={first_name}"
        )
        bot.reply_to(
            message,
            text= text,
        )
    except IntegrityError:
        logger.info(
            f"Повторный вход пользователя. user_id={user_id}, username={username or ''}, first_name={first_name}"
        )
        bot.reply_to(
            message,
            f"Рад тебя снова видеть, {first_name}!\n\n"
            "Используй /help, чтобы посмотреть список доступных команд.",
        )
