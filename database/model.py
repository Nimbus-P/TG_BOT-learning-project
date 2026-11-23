"""Модуль моделей базы данных проекта.

Содержит базовый класс BaseModel с привязкой к подключению БД,
модели User и History для хранения пользователей и истории поиска,
а также функцию create_models() для создания таблиц.
"""

import datetime

from peewee import Model, IntegerField, CharField, ForeignKeyField, DateTimeField

from .database import db
from utils.logger import logger


class BaseModel(Model):
    """Базовый класс для всех моделей проекта.

    Существует только для того, чтобы указать базу данных по умолчанию.
    Всё остальное поведение peewee наследуется автоматически.
    """

    class Meta:
        database = db


class User(BaseModel):
    """Пользователь Telegram.

    Ключевой момент: user_id — это Telegram ID пользователя, он же
    первичный ключ. Так не нужно заводить отдельную колонку id и
    следить за её уникальностью: Telegram ID уже уникален.
    """

    # Telegram ID пользователя (уникальный, первичный ключ).
    user_id = IntegerField(primary_key=True)
    # @username в Telegram. Может отсутствовать, но поле NOT NULL,
    # поэтому в обработчике подставляется пустая строка.
    username = CharField()
    # Имя пользователя.
    first_name = CharField()
    # Фамилия. В Telegram может не быть — поэтому разрешаем NULL.
    last_name = CharField(null=True)


class History(BaseModel):
    """Запись истории поиска пользователя.

    Связана с User через ForeignKeyField. Хранит поисковый запрос,
    тип поиска, общее количество найденных результатов и дату запроса.
    """

    user = ForeignKeyField(User, related_name="history")
    date = DateTimeField(default=datetime.datetime.now)
    message = CharField()
    total_result = IntegerField()


    def __str__(self):
        """Строковое представление записи истории."""
        return (
            f"{self.date.strftime('%H:%M | %d.%m.%Y')}: {self.message}\n"
            f"Количество результатов: {self.total_result}\n"
            f"{'-' * 50}"
        )


def create_models() -> None:
    """Создаёт таблицы для всех моделей проекта, если их ещё нет.

    BaseModel.__subclasses__() — список прямых наследников BaseModel,
    то есть классы User и History.

    Вызывается один раз при старте бота. Повторные вызовы безопасны:
    peewee по умолчанию не трогает уже существующие таблицы (safe=True),
    а данные в них не удаляются.

    ВНИМАНИЕ: список формируется по прямым наследникам BaseModel.
    Если появится промежуточный базовый класс, его наследники в этот
    список не попадут — тогда таблицу придётся указать явно.
    """
    models = BaseModel.__subclasses__()
    logger.info(f"Создание/проверка таблиц БД. Модели: {[m.__name__ for m in models]}")
    db.create_tables(models)
