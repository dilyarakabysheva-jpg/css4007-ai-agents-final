import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    api_key = os.getenv("LLM_API_KEY")
    base_url = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")
    model = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
    max_steps = int(os.getenv("AGENT_MAX_STEPS", "5"))

    @classmethod
    def validate(cls):
        if not cls.api_key:
            raise RuntimeError("LLM_API_KEY не задан. Проверь файл .env")