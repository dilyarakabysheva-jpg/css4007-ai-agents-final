import logging

from openai import APIConnectionError, APIError, OpenAI, RateLimitError

from .config import Config

logger = logging.getLogger(__name__)


class LLMError(Exception):
    """Ошибка работы с моделью, понятная пользователю."""


class LLMClient:
    def __init__(self):
        Config.validate()
        self._client = OpenAI(api_key=Config.api_key, base_url=Config.base_url)

    def chat(self, messages, tools=None):
        payload = {
            "model": Config.model,
            "messages": messages,
            "temperature": 0.2,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        try:
            return self._client.chat.completions.create(**payload)
        except RateLimitError as error:
            raise LLMError("Лимит запросов исчерпан, попробуй позже") from error
        except APIConnectionError as error:
            raise LLMError("Нет связи с провайдером LLM") from error
        except APIError as error:
            raise LLMError(f"Ошибка API: {error}") from error