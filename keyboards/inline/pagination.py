"""Модуль для создания inline-клавиатур Telegram-бота.

Содержит функции для формирования клавиатур навигации по страницам,
управления выбором треков, выхода из поиска и продолжения прослушивания.
Также предоставляет функции для объединения клавиатуры со списком треков
с кнопками пагинации и дополнительными действиями.
"""

from typing import Dict, Any, List

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

from api.basemodel import Track
from keyboards.inline.create_inline import create_keyboard
from keyboards.inline.to_listen import to_listen


def next_page(url_next: str) -> InlineKeyboardMarkup:
    """Создаёт inline-клавиатуру с кнопками выхода и перехода вперёд.

    Args:
        url_next: Значение callback_data для кнопки перехода вперёд.
            Может содержать идентификатор действия или URL следующей страницы.

    Returns:
        InlineKeyboardMarkup: Клавиатура с кнопками «Выйти» и «Вперёд».
    """
    keyboard = InlineKeyboardMarkup(row_width=2)

    keyboard.add(
        InlineKeyboardButton(text="❌ Выйти", callback_data="cancel"),
        InlineKeyboardButton(text="Вперёд ➡️", callback_data=url_next),
    )
    return keyboard


def down_page() -> InlineKeyboardMarkup:
    """Создаёт inline-клавиатуру с кнопками возврата назад и выхода.

    Returns:
        InlineKeyboardMarkup: Клавиатура с кнопками «Назад» и «Выйти».
    """
    keyboard = InlineKeyboardMarkup(row_width=2)

    keyboard.add(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="down_page"),
        InlineKeyboardButton(text="❌ Выйти", callback_data="cancel"),
    )
    return keyboard


def continue_track() -> InlineKeyboardMarkup:
    """Создаёт inline-клавиатуру для возврата к выбору треков.

    Returns:
        InlineKeyboardMarkup: Клавиатура с кнопкой «Продолжить выбор треков».
    """
    keyboard = InlineKeyboardMarkup()
    button = InlineKeyboardButton(
        text="Продолжить выбор треков", callback_data="continue"
    )
    return keyboard.add(button)


def pagination(
    url_next: str,
    url_down: str,
):
    """Создаёт inline-клавиатуру с навигацией назад, вперёд и выходом.

    Args:
        url_next: Значение callback_data для кнопки перехода на следующую страницу.
        url_down: Значение callback_data для кнопки перехода на предыдущую страницу.

    Returns:
        InlineKeyboardMarkup: Клавиатура с кнопками «Назад», «Выйти» и «Вперёд».
    """
    keyboard = InlineKeyboardMarkup(row_width=3)
    keyboard.add(
        InlineKeyboardButton(text="⬅️ Назад", callback_data=url_down),
        InlineKeyboardButton(text="❌ Выйти", callback_data="cancel"),
        InlineKeyboardButton(text="Вперёд ➡️", callback_data=url_next),
    )
    return keyboard


def exit_page():
    """Создаёт inline-клавиатуру с кнопкой выхода из выбора треков.

    Returns:
        InlineKeyboardMarkup: Клавиатура с кнопкой «Выйти».
    """
    keyboard = InlineKeyboardMarkup()
    button = InlineKeyboardButton(text="❌ Выйти", callback_data="cancel")
    return keyboard.add(button)


def create_and_next_page(
    data_track: List[Track], next_url: str = "next_page"
) -> InlineKeyboardMarkup:
    """Объединяет клавиатуру со списком треков и кнопками перехода вперёд.

    Args:
        data_track: Словарь с данными треков в формате, который принимает
            функция create_keyboard.
        next_url: Значение callback_data для кнопки перехода вперёд.
            По умолчанию используется строка "next_page".

    Returns:
        InlineKeyboardMarkup: Клавиатура со списком треков, кнопкой выхода
            и кнопкой перехода на следующую страницу.
    """
    keyboard = create_keyboard(data_track)
    keyboard.keyboard.extend(next_page(next_url).keyboard)
    return keyboard


def create_and_down_page(data_track: List[Track]) -> InlineKeyboardMarkup:
    """Объединяет клавиатуру со списком треков и кнопками назад и выхода.

    Args:
        data_track: Словарь с данными треков в формате, который принимает
            функция create_keyboard.

    Returns:
        InlineKeyboardMarkup: Клавиатура со списком треков, кнопкой возврата
            на предыдущую страницу и кнопкой выхода.
    """
    keyboard = create_keyboard(data_track)
    keyboard.keyboard.extend(down_page().keyboard)
    return keyboard


def create_and_exit_page(data_track: List[Track]) -> InlineKeyboardMarkup:
    """Объединяет клавиатуру со списком треков и кнопкой выхода.

    Args:
        data_track: Словарь с данными треков в формате, который принимает
            функция create_keyboard.

    Returns:
        InlineKeyboardMarkup: Клавиатура со списком треков и кнопкой выхода.
    """
    keyboard = create_keyboard(data_track)
    keyboard.keyboard.extend(exit_page().keyboard)
    return keyboard


def create_and_pagination(data_track: List[Track]) -> InlineKeyboardMarkup:
    """Объединяет клавиатуру со списком треков и полной навигацией по страницам.

    Args:
        data_track: Словарь с данными треков в формате, который принимает
            функция create_keyboard.

    Returns:
        InlineKeyboardMarkup: Клавиатура со списком треков и кнопками перехода
            на предыдущую и следующую страницы, а также кнопкой выхода.
    """
    keyboard = create_keyboard(data_track)
    keyboard.keyboard.extend(pagination("next_page", "down_page").keyboard)
    return keyboard


def listen_and_continue(audio: str) -> InlineKeyboardMarkup:
    """Создаёт клавиатуру для прослушивания трека и продолжения выбора.

    Args:
        audio: Ссылка или адрес аудиозаписи, передаваемый функции to_listen
            для создания кнопки прослушивания.

    Returns:
        InlineKeyboardMarkup: Клавиатура с кнопкой прослушивания трека
            и кнопкой возврата к выбору треков.
    """
    keyboard = to_listen(audio)
    keyboard.keyboard.extend(continue_track().keyboard)
    return keyboard
