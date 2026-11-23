"""Модуль для отображения истории поисковых запросов пользователя.

Содержит обработчики команды /history и inline-кнопок для постраничного
просмотра истории, а также функции для расчёта количества страниц
и формирования сообщения с соответствующей клавиатурой.
"""

from math import ceil
from typing import List

from telebot.types import Message, CallbackQuery

from keyboards.inline.pagination import next_page, exit_page, down_page, pagination
from loader import bot

from database.model import History, User
from states.music_bot_states import SearchStates
from utils.logger import log_function, logger


@bot.message_handler(commands=["history"])
@log_function
def history(message: Message) -> None:
    """Обрабатывает команду /history и показывает первую страницу истории.

    Проверяет регистрацию пользователя, устанавливает состояние просмотра
    истории, сохраняет номер текущей страницы и общее количество страниц
    в хранилище состояний бота. Затем получает до десяти последних записей
    и передаёт их в current_page для формирования сообщения.

    Args:
        message: Объект входящего сообщения Telegram с командой /history.

    Returns:
        None. Отправляет пользователю сообщение с историей либо уведомление
        об отсутствии регистрации или записей.

    Raises:
        Исключения базы данных или Telegram API, если не удалось получить
        историю пользователя или отправить сообщение.
    """

    user = User.get_or_none(User.user_id == message.from_user.id)
    if user is None:
        bot.send_message(message.chat.id, "Вы не зарегистрированы. Напишите /start")
        return
    history_list: List[History] = (
        user.history.order_by(-History.date).limit(10).offset(0)
    )

    result = list(map(str, history_list))

    if not result:
        bot.send_message(message.chat.id, "Нет истории поиска.")
        return

    bot.set_state(message.from_user.id, SearchStates.history_state, message.chat.id)

    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        logger.debug(
            f"user_id={ message.from_user.id}, chat_id={message.chat.id}",
        )
        data["page"] = 0
        data["all_page"] = all_page(user)
        logger.debug("Данные пагинации истории: {}", data)

    current_page(result, data["page"], data["all_page"], message=message)


@bot.callback_query_handler(
    func=lambda call: call.data in ["next_page", "down_page"],
    state=SearchStates.history_state,
)
@log_function
def page(call: CallbackQuery) -> None:
    """Обрабатывает переход между страницами истории поиска.

    Определяет направление перехода по callback_data, ограничивает номер
    страницы допустимым диапазоном, вычисляет смещение для выборки следующих
    или предыдущих десяти записей и обновляет номер страницы в хранилище.
    После получения записей вызывает current_page для отправки сообщения.

    Args:
        call: Callback-запрос Telegram от нажатия кнопки next_page или down_page.

    Returns:
        None. Отправляет выбранную страницу истории. Если пользователь
        отсутствует в базе данных, удаляет его состояние и уведомляет
        о необходимости регистрации.

    Raises:
        KeyError: Если в хранилище состояния отсутствуют ключи "page"
            или "all_page".
        Исключения базы данных или Telegram API при получении записей
        либо отправке сообщения.
    """
    bot.answer_callback_query(call.id)
    user = User.get_or_none(User.user_id == call.from_user.id)
    if user is None:
        logger.warning(
            f"Пользователь не найден в БД при пагинации истории. user_id={call.from_user.id}, chat_id={call.message.chat.id}"
        )
        bot.delete_state(call.from_user.id, call.message.chat.id)
        bot.send_message(
            call.message.chat.id, "Вы не зарегистрированы. Напишите /start"
        )
        bot.delete_message(
            chat_id=call.message.chat.id, message_id=call.message.message_id
        )
        return

    with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
        logger.info(
            f"Пагинация истории. user_id={call.from_user.id}, chat_id={call.message.chat.id}"
        )
        count_page = data["page"]
        logger.debug(
            f"Текущая страница истории: {count_page} из {data['all_page']}, кол-во записей {user.history.count()}"
        )
        count_page += 1 if call.data == "next_page" else -1
        count_page = max(min(count_page, data["all_page"] - 1), 0)
        logger.debug(f"Переход на страницу истории: {count_page} из {data["all_page"]}")
        off_set = count_page * 10
        data["page"] = count_page

    history_list: List[History] = (
        user.history.order_by(-History.date).limit(10).offset(off_set)
    )

    result = list(map(str, history_list))

    if not result:
        bot.send_message(call.message.chat.id, "Нет истории поиска.")
        return

    current_page(result, data["page"], data["all_page"], call=call)
    bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)


@bot.callback_query_handler(
    func=lambda call: call.data == "cancel", state=SearchStates.history_state
)
@log_function
def cancel(call: CallbackQuery) -> None:
    """Завершает просмотр истории по нажатию кнопки отмены.

    Подтверждает callback-запрос, удаляет сообщение с историей и очищает
    состояние пользователя, связанное с просмотром истории.

    Args:
        call: Callback-запрос Telegram от нажатия кнопки cancel.

    Returns:
        None.

    Raises:
        Исключения Telegram API, если не удалось подтвердить callback,
        удалить сообщение или очистить состояние пользователя.
    """
    bot.answer_callback_query(call.id)
    bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
    bot.delete_state(call.from_user.id, call.message.chat.id)


@log_function
def current_page(
    result: List,
    page: int,
    all_page: int,
    call: CallbackQuery | None = None,
    message: Message | None = None,
) -> Message:
    """Отправляет страницу истории с клавиатурой для доступных переходов.

    По текущему индексу страницы определяет, какие кнопки навигации нужно
    показать: только переход вперёд, только переход назад или оба направления.
    Для первой страницы, открытой командой /history, использует объект message;
    при перелистывании страниц — объект call.

    Args:
        result: Список строк с записями истории, подготовленных для вывода.
        page: Индекс текущей страницы, нумерация начинается с нуля.
        all_page: Общее количество страниц до вычитания единицы внутри функции.
        call: Callback-запрос Telegram при переходе между страницами.
            По умолчанию None.
        message: Входящее сообщение Telegram при первом открытии истории.
            По умолчанию None.

    Returns:
        Message: Объект отправленного сообщения Telegram с записями истории
        и соответствующей inline-клавиатурой.

    Raises:
        Исключения Telegram API, если не удалось отправить сообщение.
        AttributeError, если одновременно не переданы call и message.
    """
    all_page -= 1
    if page < all_page and message is not None:
        return bot.send_message(
            message.chat.id, "\n".join(result), reply_markup=next_page("next_page")
        )
    elif page == all_page and message is not None:
        return bot.send_message(
            message.chat.id, "\n".join(result), reply_markup=exit_page()
        )
    elif page == 0 and call is not None:
        return bot.send_message(
            call.message.chat.id, "\n".join(result), reply_markup=next_page("next_page")
        )

    elif page == all_page and call is not None:
        return bot.send_message(
            call.message.chat.id, "\n".join(result), reply_markup=down_page()
        )
    else:
        return bot.send_message(
            call.message.chat.id,
            "\n".join(result),
            reply_markup=pagination("next_page", "down_page"),
        )


@log_function
def all_page(user: User) -> int:
    """Рассчитывает количество страниц истории пользователя.

    Получает общее количество записей истории и делит его на размер страницы
    (десять записей), округляя результат вверх, чтобы учесть неполную страницу.

    Args:
        user: Объект пользователя базы данных, для которого рассчитывается
            количество страниц истории.

    Returns:
        int: Количество страниц истории. Возвращает 0, если записей нет.

    Raises:
        Исключения базы данных, если не удалось подсчитать записи истории.
    """
    return ceil(user.history.count() / 10)
