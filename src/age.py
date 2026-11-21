"""Детерминированное чтение возраста из русского текста.

Языковые модели ошибаются в простой арифметике («4 года 2 месяца» -> 52),
поэтому возраст, который вернула модель, сверяется с этим парсером.
Если парсер нашёл возраст и он расходится с ответом модели, побеждает парсер.
"""

import re

_YEARS = re.compile(
    r"(?<!\d)(\d{1,2}(?:[.,]5)?)\s*(?:годик(?:а|ов)?|года|год|лет|г\.?)(?![а-яё])",
    re.IGNORECASE,
)
_MONTHS = re.compile(
    r"(?<!\d)(\d{1,2})\s*(?:месяц(?:а|ев)?|мес\.?)(?![а-яё])",
    re.IGNORECASE,
)


def parse_age_months(text):
    """Возвращает возраст в месяцах или None, если возраст в тексте не найден."""
    if not text:
        return None
    years_match = _YEARS.search(text)
    months_match = _MONTHS.search(text)
    if not years_match and not months_match:
        return None
    total = 0
    if years_match:
        total += round(float(years_match.group(1).replace(",", ".")) * 12)
    if months_match:
        total += int(months_match.group(1))
    return total
