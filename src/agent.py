import json
import logging

from .config import Config
from .llm import LLMClient, LLMError
from .schemas import AssessmentAdvice

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "Ты помощник логопеда. Ты НЕ ставишь диагноз. "
    "Ты помогаешь специалисту выбрать направления логопедического обследования "
    "и объясняешь, что каждое из них проверяет. "
    "Если данных не хватает, скажи, чего именно не хватает. "
    "Отвечай только объектом JSON с полями: "
    "summary (строка), recommended_areas (массив строк), next_steps (массив строк)."
)


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

    @staticmethod
    def parse(content):
        """Достаёт JSON из ответа модели и валидирует его."""
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
        return AssessmentAdvice.model_validate(data)