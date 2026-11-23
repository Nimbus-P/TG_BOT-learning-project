"""Обработчик команды /start.

Регистрирует пользователя в базе данных при первом запуске бота,
при повторном обращении выводит приветствие без дублирования записи.
"""

from peewee import IntegrityError
from telebot.types import Message

from database.model import User
from loader import bot
from utils.logger import logger


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
            f"Новый пользователь зарегистрирован. user_id={user_id}, username={username or ""}, first_name={first_name}"
        )
        bot.reply_to(
            message,
            "Привет! Я бот для поиска музыки через Jamendo.\n\n"
            "🎵 О каталоге музыки\n"
            "Бот ищет музыку на платформе Jamendo, где независимые исполнители публикуют свои треки.\n"
            " Обрати внимание: известных коммерческих песен и популярных хитов здесь может не быть.\n"
            " Зато можно найти музыку независимых артистов и открыть для себя новые композиции.\n"
            " 🔎 Ищи музыку по названию трека или имени исполнителя.\n"
            "📥 Не каждый трек разрешено скачивать, но его можно послушать прямо в боте.\n\n"
            "Используй /help, чтобы посмотреть список доступных команд.",
        )
    except IntegrityError:
        logger.info(
            f"Повторный вход пользователя. user_id={user_id}, username={username or ""}, first_name={first_name}"
        )
        bot.reply_to(
            message,
            f"Рад тебя снова видеть, {first_name}!\n\n"
            "Используй /help, чтобы посмотреть список доступных команд.",
        )
