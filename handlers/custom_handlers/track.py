"""Обработчики поиска музыкальных треков.

Реализует запуск поиска через FSM, отображение результатов с помощью
инлайн-клавиатуры, локальную пагинацию, сохранение истории и отправку
выбранного аудио. Конкретный источник данных предоставляет адаптер поиска.
"""

from typing import Any, Dict

from requests import RequestException
from telebot.apihelper import ApiTelegramException, ApiHTTPException, ApiException
from telebot.types import CallbackQuery, Message


from basemodel import BaseSearchAdapter, ERR, NOT_RESULT
from config_data.adapter import ADAPTER
from config_data.config import PAGE_SIZE
from database.model import History, User

from keyboards.inline.pagination import (
    continue_track,
    create_and_down_page,
    create_and_exit_page,
    create_and_next_page,
    create_and_pagination,
    listen_and_continue,
)
from loader import bot
from states.music_bot_states import SearchStates
from utils.dowloader import download_audio_to_memory
from utils.logger import log_function, logger


adapter: BaseSearchAdapter = ADAPTER
"""Текущая реализация адаптера поиска с общим контрактом BaseSearchAdapter."""

SEARCH_PROMPT = (
    "Введите название трека или исполнителя."
)

NOT_STATES = object()

@bot.message_handler(commands=["chart"])
@log_function
def chart(message: Message) -> None:
    """Запускает сценарий поиска музыкального трека.

    Проверяет регистрацию пользователя, переводит его в состояние ожидания
    поискового запроса и отправляет инструкцию по формату ввода.

    Args:
        message: Сообщение Telegram с командой запуска поиска.

    Returns:
        None.
    """
    user = User.get_or_none(User.user_id == message.from_user.id)
    if user is None:
        logger.warning(
            "Попытка запуска поиска без регистрации. "
            f"user_id={message.from_user.id}, command=track"
        )
        bot.send_message(message.chat.id, "Вы не зарегистрированы. Напишите /start")
        return

    logger.info(f"Переход к вводу поискового запроса. user_id={user.user_id}")
    bot.set_state(message.from_user.id, SearchStates.top_track, message.chat.id)
    bot.send_message(message.chat.id, f"Вывожу чарт.")
    search(user=user, message=message)

@bot.message_handler(commands=["track"])
@log_function
def track(message: Message) -> None:
    """Запускает сценарий поиска музыкального трека.

    Проверяет регистрацию пользователя, переводит его в состояние ожидания
    поискового запроса и отправляет инструкцию по формату ввода.

    Args:
        message: Сообщение Telegram с командой запуска поиска.

    Returns:
        None.
    """
    user = User.get_or_none(User.user_id == message.from_user.id)
    if user is None:
        logger.warning(
            "Попытка запуска поиска без регистрации. "
            f"user_id={message.from_user.id}, command=track"
        )
        bot.send_message(message.chat.id, "Вы не зарегистрированы. Напишите /start")
        return

    logger.info(f"Переход к вводу поискового запроса. user_id={user.user_id}")
    bot.set_state(message.from_user.id, SearchStates.search_track, message.chat.id)
    bot.send_message(message.chat.id, SEARCH_PROMPT)


@bot.message_handler(state=SearchStates.search_track)
@log_function
def track_search(message: Message) -> None:
    """Обрабатывает текстовый запрос пользователя.

    Проверяет регистрацию пользователя и передаёт текст запроса общей
    функции поиска.

    Args:
        message: Сообщение Telegram с поисковым запросом.

    Returns:
        None.
    """
    user = User.get_or_none(User.user_id == message.from_user.id)
    if user is None:
        logger.warning(
            "Попытка поиска без регистрации. "
            f"user_id={message.from_user.id}"
        )
        bot.send_message(message.chat.id, "Вы не зарегистрированы. Напишите /start")
        return

    if message.text and message.text.strip():
        logger.info(
            f"Получен поисковый запрос. user_id={user.user_id}, "
            f"query={message.text.strip()!r}"
        )
        search(user=user, message=message)
        return

    logger.warning(f"Получено пустое сообщение вместо запроса. user_id={user.user_id}")
    bot.send_message(message.chat.id, SEARCH_PROMPT)


@log_function
def search(user: User, message: Message) -> None:
    """Выполняет поиск и обрабатывает полученный результат.

    Вызывает активный адаптер, обрабатывает отсутствие результатов, сохраняет
    успешный запрос в истории, записывает результаты в состояние пользователя
    и отправляет первую страницу списка треков.

    Args:
        user: Зарегистрированный пользователь, выполняющий поиск.
        message: Сообщение Telegram с исходным поисковым запросом.

    Returns:
        None.

    Notes:
        Ошибки API и сетевые ошибки перехватываются здесь, записываются
        в журнал и сопровождаются сообщением пользователю.
    """
    try:
        logger.info(
            f"Начало поиска. user_id={user.user_id}, query={message.text!r}"
        )

        state = bot.get_state(message.from_user.id, message.chat.id)

        results = NOT_STATES

        logger.info(f'State: {state}, results: {results}')

        if state == SearchStates.search_track.name:

            results = adapter.get_results(
                request_func=adapter._search,
                search_text=message.text,
            )
        elif state == SearchStates.top_track.name:
            results = adapter.get_results(request_func=adapter._top_tracks)

        if results is NOT_STATES:
            logger.warning(
                f"Поиск не выполнен: нет стадии. user_id={user.user_id}"
            )
            bot.send_message(message.chat.id, "Возникла ошибка. Попробуйте снова.")
            return

        if results is None:
            logger.warning(f"Поиск не выполнен: не заданы параметры. user_id={user.user_id}")
            bot.send_message(message.chat.id, "Укажите параметры поиска.")
            return

        if results is NOT_RESULT:
            logger.info(
                f"По запросу ничего не найдено. user_id={user.user_id}, "
                f"query={message.text!r}"
            )
            bot.send_message(message.chat.id, "Ничего не найдено. Попробуйте изменить запрос.")
            return

        history_entry = History(
            user=user,
            message=message.text,
            total_result=results.total_count,
        )
        history_entry.save()
        logger.info(
            f"История поиска сохранена. user_id={user.user_id}, запрос='{message.text}', total_result={results.total_count}"
        )

        bot.set_state(
            message.from_user.id, SearchStates.track_pagination, message.chat.id
        )

        total_page = (results.tracks_count + PAGE_SIZE - 1) // PAGE_SIZE
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data["results"] = results
            data["current_page"] = 0
            data["total_page"] = total_page

        logger.info(
            f"Поиск завершён. user_id={user.user_id}, "
            f"loaded_tracks={results.tracks_count}, "
            f"total_matches={results.total_count}, pages={total_page}"
        )

        first_page_tracks = results.tracks[:PAGE_SIZE]
        keyboard_factory = (
            create_and_next_page if total_page > 1 else create_and_exit_page
        )
        bot.send_message(
            message.chat.id,
            "Выберите трек:",
            reply_markup=keyboard_factory(first_page_tracks),
        )

    except ERR as ex:
        logger.exception(f"Ошибка со стороны сервиса поиска: {ex}")
        bot.send_message(message.chat.id, "Не удалось выполнить поиск. Попробуйте позже.")
    except RequestException as ex:
        logger.exception(f"Сетевая ошибка при выполнении поиска: {ex}")
        bot.send_message(message.chat.id, "Не удалось связаться с сервисом поиска. Попробуйте позже.")


@bot.message_handler(commands=["b"])
@log_function
def all_song(message: Message) -> None:
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:

        start = data["current_page"] * PAGE_SIZE
        end = start + PAGE_SIZE
        for track in data["results"].tracks[start:end]:

            try:
                audio_file = download_audio_to_memory(
                    track.audiodownload, track.name
                )

                if not audio_file:
                    bot.answer_callback_query(
                        message.chat.id, "Не удалось скачать трек", show_alert=True
                    )
                    continue
                logger.info(
                    f"Отправка аудио. user_id={message.from_user.id}, "
                    f"track_id={track.track_id}"
                )
                bot.send_audio(
                    chat_id=message.chat.id,
                    audio=audio_file,
                    title=track.name,
                    performer=track.artist,
                    reply_markup=continue_track(),
                    timeout=120,
                )

                logger.info(f"Аудиофайл отправлен: {track.name}")



            except Exception as ex:
                logger.exception(f'{ex}')
                bot.send_message(message.chat.id, f'Произошла ошибка, попробуйте еще раз.')

            except ApiTelegramException as ex:
                logger.exception(
                    f"Telegram отклонил аудио. "
                    f"method={ex.function_name}, "
                    f"error_code={ex.error_code}, "
                    f"description={ex.description}, "
                    f"track_id={track.track_id}, "
                    f"url={track.listen_audio}"
                )

            except ApiHTTPException as ex:
                logger.exception(
                    f"HTTP-ошибка Telegram API. "
                    f"method={ex.function_name}, "
                    f"status={ex.result.status_code}, "
                    f"response={ex.result.text[:1000]}"
                )

            except ApiException as ex:
                logger.exception(
                    f"Ошибка Telegram API: {ex}"
                )

@bot.callback_query_handler(
    func=lambda call: call.data == "cancel", state=SearchStates.track_pagination
)
@log_function
def chanel_tap(call: CallbackQuery) -> None:
    """Отменяет текущий поиск и завершает выбор трека.

    Подтверждает callback-запрос, удаляет состояние пагинации и сообщение
    с инлайн-клавиатурой, после чего предлагает начать новый поиск.

    Args:
        call: CallbackQuery от нажатия кнопки отмены.

    Returns:
        None.
    """
    logger.info(f"Пользователь отменил выбор трека. user_id={call.from_user.id}")
    bot.answer_callback_query(call.id)
    bot.delete_state(call.from_user.id, call.message.chat.id)
    bot.delete_message(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
    )
    bot.send_message(
        call.message.chat.id,
        "Выбор отменён. Чтобы начать новый поиск, введи /track или /chart.",
    )


@bot.callback_query_handler(
    func=lambda call: call.data == "continue", state=SearchStates.track_pagination
)
@log_function
def continue_tap(call: CallbackQuery) -> None:
    """Возвращает пользователя к списку треков после прослушивания.

    Повторно формирует клавиатуру для текущей локальной страницы и удаляет
    предыдущее сообщение с кнопкой продолжения.

    Args:
        call: CallbackQuery от нажатия кнопки продолжения.

    Returns:
        None.
    """
    logger.info(f"Возврат к списку треков. user_id={call.from_user.id}")
    bot.answer_callback_query(call.id)
    with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
        current_page = data["current_page"]

    choose_keyboard(current_page=current_page, data=data, call=call)



@bot.callback_query_handler(
    func=lambda call: call.data in ["next_page", "down_page"],
    state=SearchStates.track_pagination,
)
@log_function
def next_or_down_tap(call: CallbackQuery) -> None:
    """Переключает локальную страницу списка результатов.

    Изменяет индекс текущей страницы в пользовательском состоянии и отправляет
    клавиатуру с соответствующим срезом уже загруженного списка треков.
    Запросы к музыкальному API при локальном переключении страниц не выполняются.

    Args:
        call: CallbackQuery; значение call.data задаёт направление перехода.

    Returns:
        None.
    """
    logger.info(
        f"Переключение страницы списка. user_id={call.from_user.id}, "
        f"action={call.data}"
    )
    bot.answer_callback_query(call.id)

    with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
        new_page = data["current_page"] + (1 if call.data == "next_page" else -1)
        total_page = data["total_page"]

        # Защита от повторных или устаревших callback-запросов.
        if not 0 <= new_page < total_page:
            logger.warning(
                f"Запрошена недопустимая страница. user_id={call.from_user.id}, "
                f"page={new_page}, total_page={total_page}"
            )
            return

        data["current_page"] = new_page

    choose_keyboard(current_page=new_page, data=data, call=call)
    bot.delete_message(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
    )


@bot.callback_query_handler(
    func=lambda call: call.data.isdigit(), state=SearchStates.track_pagination
)
@log_function
def tap_keyboard(call: CallbackQuery) -> None:
    """Обрабатывает выбор трека из текущей страницы списка.

    Находит трек по идентификатору из callback_data. Если для трека доступна
    ссылка скачивания, отправляет аудио; в противном случае предлагает
    прослушивание по ссылке.

    Args:
        call: CallbackQuery с идентификатором выбранного трека.

    Returns:
        None.
    """
    bot.answer_callback_query(call.id)
    logger.info(f"Получен выбор трека. user_id={call.from_user.id}")

    with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
        start = data["current_page"] * PAGE_SIZE
        end = start + PAGE_SIZE
        selected_track_id = call.data
        selected_track = None

        for track_item in data["results"].tracks[start:end]:
            if str(track_item.track_id) == selected_track_id:
                selected_track = track_item
                break

        if selected_track is None:
            logger.warning(
                f"Выбранный трек не найден на текущей странице. "
                f"user_id={call.from_user.id}, track_id={selected_track_id}"
            )
            bot.send_message(call.message.chat.id, "Не удалось найти выбранный трек. Обнови список.")
            return

        logger.info(
            f"Выбран трек. user_id={call.from_user.id}, "
            f"track_id={selected_track.track_id}, "
            f"title={selected_track.name!r}, artist={selected_track.artist!r}"
        )

        if selected_track.audiodownload:
            logger.info(
                f"Отправка аудио. user_id={call.from_user.id}, "
                f"track_id={selected_track.track_id}"
            )

            bot.send_message(call.message.chat.id,
                "Отправляю трек...",)
            try:
                if selected_track.listen_audio is None:
                    audio_file = download_audio_to_memory(selected_track.audiodownload, selected_track.name)
                    if not audio_file:
                        bot.answer_callback_query(
                            call.id, "Не удалось скачать трек", show_alert=True
                        )
                        return
                else:
                    audio_file = selected_track.listen_audio
                logger.info(f'Передана в телеграмм. user_id={call.from_user.id}, ')
                bot.send_audio(
                    chat_id=call.message.chat.id,
                    audio=audio_file,
                    title=selected_track.name,
                    performer=selected_track.artist,
                    reply_markup=continue_track(),
                    timeout=120
                )

                logger.info(f"Аудиофайл отправлен: {selected_track.name}")


            except Exception as ex:
                logger.exception(f'{ex}')
                bot.send_message(call.message.chat.id, f'Произошла ошибка, попробуйте еще раз.')

            except ApiTelegramException as ex:
                logger.exception(
                    f"Telegram отклонил аудио. "
                    f"method={ex.function_name}, "
                    f"error_code={ex.error_code}, "
                    f"description={ex.description}, "
                    f"track_id={selected_track.track_id}, "
                    f"url={selected_track.listen_audio}"
                )

            except ApiHTTPException as ex:
                logger.exception(
                    f"HTTP-ошибка Telegram API. "
                    f"method={ex.function_name}, "
                    f"status={ex.result.status_code}, "
                    f"response={ex.result.text[:1000]}"
                )

            except ApiException as ex:
                logger.exception(
                    f"Ошибка Telegram API: {ex}"
                )


        else:
            logger.info(
                f"Отправка ссылки для прослушивания. user_id={call.from_user.id}, "
                f"track_id={selected_track.track_id}"
            )
            if selected_track.listen_audio:
                bot.send_message(
                    call.message.chat.id,
                    "Cкачивание не доступно, нажмите кнопку ниже,чтобы прослушать.",
                    reply_markup=listen_and_continue(selected_track.listen_audio),
                )
            else:
                bot.send_message(call.message.chat.id, f"Извините, трек не доступен.", reply_markup=continue_track())

        bot.delete_message(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
        )


@log_function
def choose_keyboard(
    current_page: int, data: Dict[str, Any], call: CallbackQuery
) -> Message:
    """Формирует и отправляет клавиатуру для выбранной локальной страницы.

    Выбирает тип клавиатуры в зависимости от количества страниц и положения
    текущей страницы: первой, промежуточной или последней.

    Args:
        current_page: Индекс текущей страницы; нумерация начинается с нуля.
        data: Пользовательское состояние с ключами results и total_page.
        call: CallbackQuery, используемый для определения чата.

    Returns:
        Message: Отправленное сообщение с инлайн-клавиатурой.

    Raises:
        KeyError: Если в data отсутствуют results или total_page.
    """
    start = current_page * PAGE_SIZE
    end = start + PAGE_SIZE

    page_tracks = data["results"].tracks[start:end]
    total_page = data["total_page"]

    if total_page == 1:
        keyboard_factory = create_and_exit_page
    elif current_page == 0:
        keyboard_factory = create_and_next_page
    elif current_page == total_page - 1:
        keyboard_factory = create_and_down_page
    else:
        keyboard_factory = create_and_pagination

    return bot.send_message(
        call.message.chat.id,
        "Выберите трек:",
        reply_markup=keyboard_factory(page_tracks),
    )
