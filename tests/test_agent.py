import pytest
from pydantic import ValidationError

from src.agent import Agent
from src.llm import LLMError
from src.schemas import ChildProfile


def test_невозможный_возраст_отклоняется():
    with pytest.raises(ValidationError):
        ChildProfile(age_months=400, concerns=["звукопроизношение"])


def test_пустой_список_жалоб_отклоняется():
    with pytest.raises(ValidationError):
        ChildProfile(age_months=50, concerns=[])


def test_json_достаётся_из_ответа_с_лишним_текстом():
    raw = 'Вот ответ: {"summary": "a", "recommended_areas": ["b"], "next_steps": ["c"]} готово'
    advice = Agent.parse(raw)
    assert advice.recommended_areas == ["b"]


def test_ответ_без_json_даёт_понятную_ошибку():
    with pytest.raises(LLMError):
        Agent.parse("модель решила поболтать без json")


def test_неполный_json_отклоняется():
    with pytest.raises(ValidationError):
        Agent.parse('{"summary": "только одно поле"}')