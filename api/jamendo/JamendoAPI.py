"""Модуль для работы с Jamendo API v3.0.

Содержит низкоуровневые функции для отправки запросов к эндпоинту /tracks/,
получения следующей страницы результатов, нормализации ответа API,
а также интерфейс SearchInterface для удобного вызова из обработчиков бота.
"""

from typing import Dict, Callable, Any
import requests

from ..basemodel import BaseSearchAdapter, NotResult, ERR, ResultSearch, Track, NOT_RESULT
from config_data.config import API_KEY
from utils.logger import logger

API_BASE_URL = "https://api.jamendo.com/v3.0/"

def _search_track(
    namesearch: str = "", artistsearch: str = "", timeout: int = 15
) -> tuple[Dict[str, Any], str] | None:
    """Отправляет запрос к эндпоинту /tracks/ Jamendo API.

    Args:
        namesearch: Название трека для поиска (параметр namesearch).
        artistsearch: Имя исполнителя для поиска (параметр artist_name).
        timeout: Таймаут запроса в секундах.

    Returns:
        Кортеж (response.json(), response.url), где response.url — полный URL
        запроса с параметрами. Возвращает None, если не передан ни один
        параметр поиска (namesearch и artistsearch пустые или не указаны).

    Raises:
        requests.HTTPError: При ошибке HTTP-статуса (через raise_for_status).
        requests.RequestException: При сетевых ошибках.
    """
    params = {
        "client_id": API_KEY,
        'limit': '200',
        "fullcount": True,
    }

    if namesearch.strip():
        params["namesearch"] = namesearch.strip()

    if artistsearch.strip():
        params["artist_name"] = artistsearch.strip()

    if params.get("namesearch") or params.get("artist_name"):
        url = f"{API_BASE_URL}/tracks/"
        logger.info(
            f"Запрос к Jamendo API: _search_track, namesearch='{namesearch}', artistsearch='{artistsearch}'"
        )
        response = requests.get(url, params=params, timeout=timeout)
        response.raise_for_status()
        logger.debug(
            f"Ответ Jamendo API: status_code={response.status_code}, url={response.url}"
        )
        return response.json(), response.url
    return None


def _next_page(url: str, timeout: int = 15) -> Dict[str, Any]:
    """Получает следующую страницу результатов по полному URL.

    Args:
        url: Полный URL следующей страницы из headers.next ответа API.
        timeout: Таймаут запроса в секундах.

    Returns:
        Сырой словарь ответа от Jamendo API для следующей страницы
        (response.json()).

    Raises:
        requests.HTTPError: При ошибке HTTP-статуса.
        requests.RequestException: При сетевых ошибках.
    """
    logger.info("Запрос к Jamendo API: _next_page")
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    logger.debug(f"Ответ Jamendo API: status_code={response.status_code}")
    return response.json()


def _result_search(
    func: Callable, *args, **kwargs
) -> Dict[Any, Any] | None | NotResult:
    """Нормализует сырой ответ Jamendo API в удобный формат.

    Вызывает переданную функцию. Для _search_track функция возвращает кортеж
    (result, url), для _next_page — только result. При успешном ответе по
    headers.status и headers.code:
    - если results пустые — возвращает NOT_RESULT
    - если есть результаты — формирует словарь с ключом 'tracks',
      где ключи треков — числовые индексы, значения — словари
      только с полями из list_keys; добавляет 'fullcount' из headers.results_fullcount;
      при наличии url первого поиска добавляет 'first_url'
    - при наличии headers.next добавляет 'next_page' со ссылкой

    Args:
        func: Функция, возвращающая сырой ответ API (_search_track или _next_page).
        *args: Позиционные аргументы для func.
        **kwargs: Именованные аргументы для func.

    Returns:
        Словарь вида {'fullcount': ..., 'first_url': ..., 'tracks': {...}, 'next_page': ...}
        при наличии результатов; NOT_RESULT при пустом results; None, если func вернула None.

    Raises:
        ERR: Если ответ API неуспешный (status != "success" или code != 0).
        KeyError: Если в ответе отсутствуют ожидаемые ключи headers/results.
    """
    if func.__name__ == "_search_track":
        result, url = func(*args, **kwargs)
    else:
        result = func(*args, **kwargs)
        url = ""
    if result is not None:
        status = result["headers"]["status"]
        code = result["headers"]["code"]
        if status == "success" and code == 0:
            if result["results"]:
                data = dict()
                if url:
                    data["first_page"] = url
                data["total_count"] = result["headers"]["results_fullcount"]
                data["tracks"] = []
                for tracks in result["results"]:
                    track = {
                        "track_id": tracks["id"],
                        "name": tracks["name"],
                        "artist": tracks["artist_name"],
                        "listen_audio": tracks["audio"],
                        "audiodownload": tracks["audiodownload"],
                    }

                    data["tracks"].append(track)
                if result["headers"].get("next"):
                    data["next_page"] = result["headers"]["next"]
                logger.info(
                    f"Успешный ответ Jamendo. fullcount={data['total_count']}, показано треков={len(data['tracks'])}"
                )
                return data
            logger.info("Jamendo API вернул пустой результат (results пустой).")
            return NOT_RESULT
        logger.warning(
            f"Ошибка API Jamendo. status={status}, code={code}, message={result['headers'].get('error_message')}"
        )
        raise ERR(
            f"Статус: {status}\nКод ошибки: {code}\nСообщение ошибки: {result['headers']['error_message']}"
        )
    return None


class JamendoAdapter(BaseSearchAdapter):

    @staticmethod
    def _search(
        search_text: str, timeout: int = 15
    ) -> Dict[Any, Any] | None | NotResult:
        """Выполняет поиск треков по названию или имени исполнителя.

        Args:
            search_text: Текст поиска.
            timeout: Таймаут запроса в секундах.

        Returns:
            Нормализованный результат от _result_search: словарь с fullcount, first_url,
            tracks, next_page. NOT_RESULT при пустом результате, None если не указаны
            параметры поиска.
        """

        if search_text.strip():
            text_message = search_text.strip().split(" - ", maxsplit=1)
            namesearch = text_message[0].strip()
            artistsearch = text_message[1].strip() if len(text_message) == 2 else ""


            return _result_search(
                func=_search_track,
                namesearch=namesearch,
                artistsearch=artistsearch,
                timeout=timeout,
            )
        return None

    @staticmethod
    def _get_next(url: str, timeout: int = 15) -> Dict[Any, Any] | None | NotResult:
        """Получает следующую страницу результатов по ссылке.

        Args:
            url: Полный URL следующей страницы из headers.next.
            timeout: Таймаут запроса в секундах.

        Returns:
            Нормализованный результат от _result_search.
        """
        return _result_search(func=_next_page, url=url, timeout=timeout)
