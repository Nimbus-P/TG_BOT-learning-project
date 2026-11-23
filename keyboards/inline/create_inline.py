"""Модуль генератора инлайн-клавиатуры.

Клавиатура собирается из словаря {текст кнопки: callback_data}.
Такой формат удобен: порядок кнопок в Python 3.7+ сохраняется,
а callback_data легко сопоставить с описанием кнопки.
"""

from typing import Dict, Any, List

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

from basemodel import Track


def create_buttons_info(tracks: List[Track]) -> Dict[str, str]:
    """Формирует словарь для построения инлайн-клавиатуры из результатов поиска.

    Для каждого трека создаёт кнопку с текстом вида
    "N. Название трека - Имя исполнителя", где N = индекс трека + 1.
    В качестве callback_data используется строковое представление индекса трека.

    Args:
        tracks: Словарь треков, где ключ — числовой индекс трека,
            значение — словарь с полями трека (ожидаются 'name', 'artist_name').

    Returns:
        Словарь вида {текст кнопки: callback_data} для передачи в gen_markup.
    """
    buttons_info = {}

    for track_index, track in enumerate(tracks):
        buttons_info[
            f"{track_index + 1}. {track.name} - {track.artist}"
        ] = str(track.track_id)


    return buttons_info


def gen_markup(buttons_info: Dict) -> InlineKeyboardMarkup:
    """Собирает инлайн-клавиатуру по словарю с кнопками.

    Args:
        buttons_info: Словарь вида {текст кнопки: callback_data}.

    Returns:
        Готовый объект InlineKeyboardMarkup.
    """
    # Создаём объект клавиатуры.
    keyboard = InlineKeyboardMarkup()

    for text_keyboard, callback_keyboard in buttons_info.items():
        # Создаём объект кнопки и добавляем её к клавиатуре.
        button = InlineKeyboardButton(
            text=text_keyboard, callback_data=callback_keyboard
        )
        keyboard.add(button)

    return keyboard


def create_keyboard(data_track: List[Track]) -> InlineKeyboardMarkup:
    """
    Создаёт инлайн-клавиатуру с результатами поиска треков.

    Объединяет подготовку информации о кнопках и формирование клавиатуры
    в одну операцию.

    Сначала вызывает create_buttons_info(), которая преобразует данные
    о треках в словарь с текстами кнопок и callback_data. Затем передаёт
    полученный словарь в gen_markup() для создания готовой клавиатуры.

    Args:
        data_track: Словарь с результатами поиска треков. Используется
            для формирования подписей кнопок и callback_data.
            Структура данных должна соответствовать формату,
            ожидаемому функцией create_buttons_info().

    Returns:
        InlineKeyboardMarkup: Инлайн-клавиатура с кнопками найденных
            треков, готовая для отправки пользователю через Telegram-бота.

    """
    data_markup = create_buttons_info(data_track)
    return gen_markup(data_markup)
