import logging
import sys

from .agent import Agent
from .llm import LLMError

DISCLAIMER = "Это не диагноз. Решение принимает специалист."


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    request = " ".join(sys.argv[1:])
    if not request.strip():
        print("Опиши ребёнка и запрос. Пример:")
        print('  python -m src.cli "мальчик 4 года 2 месяца, не произносит Р и Л"')
        return 1
    try:
        advice = Agent().run(request)
    except LLMError as error:
        print(f"Ошибка: {error}")
        return 1
    except ValueError as error:
        print(f"Ответ модели не прошёл валидацию: {error}")
        return 1
    print(advice.summary)
    print("\nНаправления обследования:")
    for area in advice.recommended_areas:
        print(f"  - {area}")
    print("\nСледующие шаги:")
    for step in advice.next_steps:
        print(f"  - {step}")
    print(f"\n{DISCLAIMER}")
    return 0


if __name__ == "__main__":
    sys.exit(main())