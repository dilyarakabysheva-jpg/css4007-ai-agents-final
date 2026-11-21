import json
import logging

from typing import get_args

from .age import parse_age_months
from .config import Config
from .llm import LLMClient, LLMError
from .schemas import Area, AssessmentAdvice, ChildProfile, ProfileExtraction

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "Ты помощник логопеда. Ты НЕ ставишь диагноз. "
    "Ты помогаешь специалисту выбрать направления логопедического обследования "
    "и объясняешь, что каждое из них проверяет. "
    "Если данных не хватает, скажи, чего именно не хватает. "
    "Отвечай только объектом JSON с полями: "
    "summary (строка), recommended_areas (массив строк), next_steps (массив строк)."
)

EXTRACT_PROMPT = (
    "Ты извлекаешь данные о ребёнке из описания логопеда. "
    "Ничего не придумывай: если возраста в тексте нет, верни age_months: null. "
    "Отвечай только объектом JSON с полями: "
    "age_months (целое число месяцев или null; 4 года 2 месяца = 50), "
    "concerns (массив коротких строк: жалобы и наблюдаемые трудности своими словами из текста), "
    "areas (массив кодов направлений обследования, только из списка: "
    "articulation — звукопроизношение, phonemic — фонематическое восприятие, "
    "syllable_structure — слоговая структура, vocabulary — словарь, "
    "grammar — грамматический строй, coherent_speech — связная речь, "
    "literacy — письмо и чтение)."
)

KNOWN_AREAS = set(get_args(Area))


class MissingDataError(Exception):
    """В описании ребёнка не хватает данных, без которых нельзя подбирать методики."""

    def __init__(self, missing):
        self.missing = missing
        super().__init__("Не хватает данных: " + ", ".join(missing))


def extract_json(content):
    """Достаёт первый JSON-объект из текста модели (модель любит добавлять пояснения)."""
    if not content:
        raise LLMError("Модель вернула пустой ответ")
    start = content.find("{")
    end = content.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise LLMError("В ответе модели нет JSON")
    try:
        data = json.loads(content[start : end + 1])
    except json.JSONDecodeError as error:
        raise LLMError("Модель вернула сломанный JSON") from error
    if not isinstance(data, dict):
        raise LLMError("Модель вернула JSON, но не объект")
    return data


class AgentState:
    """Состояние одного запуска. На неделе 13 сюда лягут вызовы инструментов."""

    def __init__(self, request):
        self.request = request
        self.messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": request},
        ]
        self.tool_calls = []
        self.step = 0


class Agent:
    def __init__(self, client=None, tools=None):
        self.client = client or LLMClient()
        self.tools = tools or []

    def run(self, request):
        if not request or not request.strip():
            raise ValueError("Пустой запрос")
        state = AgentState(request.strip())
        while state.step < Config.max_steps:
            state.step += 1
            logger.info("шаг %s из %s", state.step, Config.max_steps)
            response = self.client.chat(state.messages, tools=self.tools or None)
            message = response.choices[0].message
            # Неделя 13: здесь появится ветка if message.tool_calls
            return self.parse(message.content)
        raise LLMError(f"Превышен лимит шагов: {Config.max_steps}")

    def extract_profile(self, text):
        """Свободный текст -> проверенный ChildProfile.

        Модель извлекает поля, pydantic проверяет типы и диапазоны,
        возраст сверяется с детерминированным парсером.
        """
        if not text or not text.strip():
            raise ValueError("Пустое описание ребёнка")
        messages = [
            {"role": "system", "content": EXTRACT_PROMPT},
            {"role": "user", "content": text.strip()},
        ]
        response = self.client.chat(messages)
        data = extract_json(response.choices[0].message.content)

        areas = data.get("areas") or []
        if isinstance(areas, list):
            unknown = [a for a in areas if a not in KNOWN_AREAS]
            if unknown:
                logger.warning("модель вернула неизвестные направления, отброшены: %s", unknown)
            data["areas"] = [a for a in areas if a in KNOWN_AREAS]

        extraction = ProfileExtraction.model_validate(data)

        parsed_age = parse_age_months(text)
        if parsed_age is not None and parsed_age != extraction.age_months:
            logger.warning(
                "возраст от модели (%s) не совпал с текстом (%s), берём из текста",
                extraction.age_months,
                parsed_age,
            )
            extraction.age_months = parsed_age

        missing = extraction.missing_fields()
        if missing:
            raise MissingDataError(missing)

        return ChildProfile(
            age_months=extraction.age_months,
            concerns=extraction.concerns,
            areas=extraction.areas,
        )

    @staticmethod
    def parse(content):
        """Достаёт JSON из ответа модели и валидирует его."""
        return AssessmentAdvice.model_validate(extract_json(content))
