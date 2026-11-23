from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


def to_listen(audio: str) -> InlineKeyboardMarkup:
    """Создаёт инлайн-клавиатуру с кнопкой для прослушивания трека.

    Args:
        audio: URL аудиозаписи, который будет использоваться
            в качестве ссылки для кнопки прослушивания.

    Returns:
        InlineKeyboardMarkup: Инлайн-клавиатура с кнопкой
        «Слушать», открывающей аудиозапись по переданной ссылке.
    """
    keyboard = InlineKeyboardMarkup()

    button = InlineKeyboardButton(text="▶️ Слушать", url=audio)

    return keyboard.add(button)
