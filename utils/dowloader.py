from io import BytesIO

import requests

from utils.logger import logger

MAX_AUDIO_SIZE = 49_000_000


def download_audio_to_memory(url: str, track_name: str) -> BytesIO:
    """
    Загружает аудиофайл по URL в оперативную память.

    Args:
        url: Прямая ссылка на скачивание аудиофайла.
        track_name: Название трека для формирования имени файла.

    Returns:
        BytesIO: Файловый объект с содержимым аудио.

    Raises:
        requests.RequestException: При сетевых и HTTP-ошибках.
        ValueError: Если файл пустой или превышает допустимый размер.
    """
    audio_buffer = BytesIO()

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Accept": "audio/webm,audio/ogg,audio/wav,audio/*;q=0.9,application/ogg;q=0.7,video/*;q=0.6,*/*;q=0.5",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            # "Referer": "https://ru.hitmox.com/",
            # "Origin": "https://ru.hitmox.com",
            # "Sec-Fetch-Dest": "audio",
            # "Sec-Fetch-Mode": "no-cors",
            # "Sec-Fetch-Site": "same-origin",
        }

        response = requests.get(url, headers=headers, stream=True, timeout=(10, 40))

        response.raise_for_status()
        if response.status_code != 200:
            logger.error(
                f"Ошибка загрузки: "
                f"status={response.status_code}, "
                f"content_type={response.headers.get('Content-Type')}, "
                f"server={response.headers.get('Server')}, "
                f"body={response.text[:500]}"
            )
        content_length = response.headers.get("Content-Length")

        if content_length and content_length.isdigit():
            if int(content_length) > MAX_AUDIO_SIZE:
                raise ValueError("Аудиофайл превышает допустимый размер.")

        for chunk in response.iter_content(chunk_size=64 * 1024):
            if not chunk:
                continue

            if audio_buffer.tell() + len(chunk) > MAX_AUDIO_SIZE:
                raise ValueError("Аудиофайл превышает допустимый размер.")

            audio_buffer.write(chunk)

        if not audio_buffer.tell():
            raise ValueError("Получен пустой аудиофайл.")

        safe_name = track_name.replace("/", "_").replace("\\", "_")
        audio_buffer.name = f"{safe_name or 'track'}.mp3"
        audio_buffer.seek(0)

        return audio_buffer

    except Exception:
        audio_buffer.close()
        raise
