"""Настройка логирования.

Конфигурирует loguru для записи логов в JSON-файл с ротацией
и временем хранения.
"""

from loguru import logger

logger.remove()

logger.add(
    "logs/bot.json",
    serialize=True,
    level="DEBUG",
    rotation="10 MB",
    retention="7 days",
)


from functools import wraps
from time import perf_counter


def log_function(func):
    """Декоратор для логирования вызова и времени выполнения функции."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        logger.info("Начало выполнения функции '{}'", func.__name__)
        start_time = perf_counter()

        try:
            result = func(*args, **kwargs)
        except Exception:
            logger.exception(
                "Ошибка при выполнении функции '{}'",
                func.__name__,
            )
            raise
        else:
            elapsed = perf_counter() - start_time
            logger.info(
                "Функция '{}' завершена за {:.4f} сек.",
                func.__name__,
                elapsed,
            )
            return result

    return wrapper
