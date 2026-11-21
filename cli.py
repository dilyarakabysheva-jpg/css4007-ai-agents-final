import logging
import sys

from pydantic import ValidationError

from .agent import Agent, MissingDataError
from .llm import LLMError
from .methods import MethodDatabase, MethodDatabaseError, search_methods
from .schemas import AREA_NAMES_RU

DISCLAIMER = "Это не диагноз. Решение принимает специалист."


def format_age(months):
    return f"{months // 12} г. {months % 12} мес. ({months} мес.)"


def run_advice(request):
    advice = Agent().run(request)
    print(advice.summary)
    print("\nНаправления обследования:")
    for area in advice.recommended_areas:
        print(f"  - {area}")
    print("\nСледующие шаги:")
    for step in advice.next_steps:
        print(f"  - {step}")


def run_profile(request):
    """Неделя 12: профиль ребёнка + методики из локальной базы.

    Порядок вызовов здесь пока фиксированный. На неделе 13 search_methods
    станет инструментом, и решать, когда его вызывать, будет модель.
    """
    profile = Agent().extract_profile(request)
    print(f"Возраст: {format_age(profile.age_months)}")
    print("Жалобы: " + "; ".join(profile.concerns))
    if not profile.areas:
        print("\nМодель не определила направления обследования. Уточните описание.")
        return
    db = MethodDatabase()
    for area in profile.areas:
        print(f"\n{AREA_NAMES_RU[area].capitalize()}:")
        methods = search_methods(profile.age_months, area, db=db)
        if not methods:
            print("  В базе нет методики для этого возраста и направления.")
        for method in methods:
            print(f"  - {method.authors}. «{method.title}» — {method.checks}")


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = sys.argv[1:]
    profile_mode = bool(args) and args[0] == "--profile"
    if profile_mode:
        args = args[1:]
    request = " ".join(args)
    if not request.strip():
        print("Опиши ребёнка и запрос. Примеры:")
        print('  python -m src.cli "мальчик 4 года 2 месяца, не произносит Р и Л"')
        print('  python -m src.cli --profile "мальчик 4 года 2 месяца, не произносит Р и Л"')
        return 1
    try:
        if profile_mode:
            run_profile(request)
        else:
            run_advice(request)
    except MissingDataError as error:
        print(f"{error}. Дополните описание и повторите запрос.")
        return 1
    except MethodDatabaseError as error:
        print(f"База методик недоступна: {error}")
        return 1
    except LLMError as error:
        print(f"Ошибка: {error}")
        return 1
    except (ValidationError, ValueError) as error:
        print(f"Данные не прошли валидацию: {error}")
        return 1
    print(f"\n{DISCLAIMER}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
