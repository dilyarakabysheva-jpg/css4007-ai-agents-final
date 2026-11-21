"""Локальная база методик обследования и поиск по ней.

На неделе 12 это обычные функции Python. На неделе 13 search_methods
будет зарегистрирована как инструмент, который выбирает сама модель.
"""

import json
import logging
from pathlib import Path

from pydantic import ValidationError

from .schemas import Method, MethodQuery

logger = logging.getLogger(__name__)

DEFAULT_PATH = Path(__file__).parent / "data" / "methods.json"


class MethodDatabaseError(Exception):
    """База методик недоступна или повреждена. Агент не должен подменять её догадками."""


class MethodDatabase:
    def __init__(self, path=DEFAULT_PATH):
        self.path = Path(path)
        self._methods = None

    def load(self):
        if self._methods is not None:
            return self._methods
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except FileNotFoundError as error:
            raise MethodDatabaseError(f"Файл базы методик не найден: {self.path}") from error
        except json.JSONDecodeError as error:
            raise MethodDatabaseError(f"Файл базы методик повреждён: {self.path}") from error

        items = raw.get("methods") if isinstance(raw, dict) else None
        if not isinstance(items, list) or not items:
            raise MethodDatabaseError("В базе методик нет списка methods")

        try:
            methods = [Method.model_validate(item) for item in items]
        except ValidationError as error:
            raise MethodDatabaseError(f"Запись в базе методик не прошла проверку: {error}") from error

        ids = [method.id for method in methods]
        if len(ids) != len(set(ids)):
            raise MethodDatabaseError("В базе методик повторяются id")

        self._methods = methods
        logger.info("загружено методик: %s", len(methods))
        return methods

    def get(self, method_id):
        for method in self.load():
            if method.id == method_id:
                return method
        return None


def search_methods(age_months, area, db=None):
    """Возвращает методики, подходящие по возрасту и направлению.

    Аргументы проверяются до обращения к базе, поэтому неверный возраст
    или неизвестное направление дают ValidationError, а не пустой список.
    Пустой список означает честное «в базе нет подходящей методики».
    """
    query = MethodQuery(age_months=age_months, area=area)
    db = db or MethodDatabase()
    found = [
        method
        for method in db.load()
        if query.area in method.areas and method.fits_age(query.age_months)
    ]
    logger.info(
        "search_methods(age_months=%s, area=%s) -> %s",
        query.age_months,
        query.area,
        [method.id for method in found],
    )
    return found
