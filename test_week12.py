"""Тесты недели 12: извлечение профиля, база методик, поиск.

Живой API не нужен: модель подменяется FakeClient, который возвращает
заранее заданный текст в том же формате, что и OpenAI SDK.
"""

import json
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from src.age import parse_age_months
from src.agent import Agent, MissingDataError
from src.methods import MethodDatabase, MethodDatabaseError, search_methods


class FakeClient:
    def __init__(self, content):
        self.content = content
        self.calls = []

    def chat(self, messages, tools=None):
        self.calls.append(messages)
        message = SimpleNamespace(content=self.content, tool_calls=None)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def agent_answering(payload):
    content = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False)
    return Agent(client=FakeClient(content))


# --- извлечение ChildProfile из свободного текста ---

def test_профиль_извлекается_из_свободного_текста():
    agent = agent_answering(
        'Результат: {"age_months": 50, "concerns": ["не произносит Р и Л"], '
        '"areas": ["articulation", "vocabulary"]}'
    )
    profile = agent.extract_profile("Мальчик 4 года 2 месяца, не произносит Р и Л, словарь бедный")
    assert profile.age_months == 50
    assert profile.areas == ["articulation", "vocabulary"]


def test_ошибка_модели_в_арифметике_возраста_исправляется():
    agent = agent_answering({"age_months": 52, "concerns": ["нет Р"], "areas": ["articulation"]})
    profile = agent.extract_profile("Мальчик 4 года 2 месяца, нет Р")
    assert profile.age_months == 50


def test_без_возраста_агент_говорит_чего_не_хватает():
    agent = agent_answering({"age_months": None, "concerns": ["нет Р"], "areas": ["articulation"]})
    with pytest.raises(MissingDataError) as error:
        agent.extract_profile("Ребёнок не произносит Р")
    assert "возраст ребёнка" in error.value.missing


def test_выдуманное_направление_отбрасывается():
    agent = agent_answering(
        {"age_months": 60, "concerns": ["заикается"], "areas": ["stuttering", "coherent_speech"]}
    )
    profile = agent.extract_profile("Девочка 5 лет, заикается")
    assert profile.areas == ["coherent_speech"]


@pytest.mark.parametrize(
    "text, expected",
    [
        ("мальчик 4 года 2 месяца", 50),
        ("девочка 5 лет", 60),
        ("ребёнок 3 г. 6 мес.", 42),
        ("малыш 18 месяцев", 18),
        ("4,5 года", 54),
        ("не говорит звук Р", None),
    ],
)
def test_возраст_читается_из_текста(text, expected):
    assert parse_age_months(text) == expected


# --- база методик и поиск ---

def test_база_методик_загружается_и_содержит_не_меньше_8_методик():
    methods = MethodDatabase().load()
    assert len(methods) >= 8
    assert len({m.id for m in methods}) == len(methods)


def test_поиск_возвращает_только_подходящие_методики_из_базы():
    found = search_methods(50, "articulation")
    ids = {m.id for m in found}
    assert "filicheva_chirkina_onr" in ids
    assert all("articulation" in m.areas and m.fits_age(50) for m in found)


def test_нет_методики_для_возраста_даёт_пустой_список():
    assert search_methods(50, "literacy") == []


def test_неизвестное_направление_отклоняется_до_поиска():
    with pytest.raises(ValidationError):
        search_methods(50, "GFTA-2")


def test_недоступная_база_даёт_понятную_ошибку(tmp_path):
    db = MethodDatabase(tmp_path / "нет_такого_файла.json")
    with pytest.raises(MethodDatabaseError):
        search_methods(50, "articulation", db=db)


def test_повреждённая_запись_в_базе_отклоняется(tmp_path):
    broken = tmp_path / "methods.json"
    broken.write_text(
        json.dumps({"methods": [{
            "id": "x", "title": "t", "authors": "a",
            "age_min_months": 80, "age_max_months": 40,
            "areas": ["articulation"], "checks": "c",
        }]}),
        encoding="utf-8",
    )
    with pytest.raises(MethodDatabaseError):
        MethodDatabase(broken).load()
