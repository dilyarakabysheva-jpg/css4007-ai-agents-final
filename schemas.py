from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

# Направления обследования. Английские коды, потому что на неделе 13
# они станут значениями enum в JSON-схеме инструмента search_methods.
Area = Literal[
    "articulation",        # звукопроизношение
    "phonemic",            # фонематическое восприятие
    "syllable_structure",  # слоговая структура слова
    "vocabulary",          # словарь
    "grammar",             # грамматический строй
    "coherent_speech",     # связная речь
    "literacy",            # письмо и чтение
]

AREA_NAMES_RU = {
    "articulation": "звукопроизношение",
    "phonemic": "фонематическое восприятие",
    "syllable_structure": "слоговая структура слова",
    "vocabulary": "словарь",
    "grammar": "грамматический строй речи",
    "coherent_speech": "связная речь",
    "literacy": "письмо и чтение",
}

MIN_AGE_MONTHS = 12
MAX_AGE_MONTHS = 96


class ChildProfile(BaseModel):
    """Данные ребёнка. Возраст ограничен дошкольным и младшим школьным возрастом."""

    age_months: int = Field(ge=MIN_AGE_MONTHS, le=MAX_AGE_MONTHS)
    concerns: list[str] = Field(min_length=1)
    areas: list[Area] = Field(default_factory=list)

    @field_validator("concerns")
    @classmethod
    def clean(cls, value):
        items = [item.strip() for item in value if item.strip()]
        if not items:
            raise ValueError("concerns не может быть пустым")
        return items

    @field_validator("areas")
    @classmethod
    def unique_areas(cls, value):
        return list(dict.fromkeys(value))


class ProfileExtraction(BaseModel):
    """Сырой результат извлечения из свободного текста.

    Поля могут быть пустыми: модель не должна придумывать возраст,
    если его нет в описании. Полноту проверяет to_profile().
    """

    age_months: int | None = None
    concerns: list[str] = Field(default_factory=list)
    areas: list[Area] = Field(default_factory=list)

    def missing_fields(self):
        missing = []
        if self.age_months is None:
            missing.append("возраст ребёнка")
        if not [c for c in self.concerns if c.strip()]:
            missing.append("жалобы или наблюдаемые трудности")
        return missing


class Method(BaseModel):
    """Одна методика из локальной базы src/data/methods.json."""

    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    authors: str = Field(min_length=1)
    age_min_months: int = Field(ge=0)
    age_max_months: int = Field(ge=0)
    areas: list[Area] = Field(min_length=1)
    checks: str = Field(min_length=1)

    @model_validator(mode="after")
    def age_range_is_ordered(self):
        if self.age_min_months > self.age_max_months:
            raise ValueError(f"{self.id}: age_min_months больше age_max_months")
        return self

    def fits_age(self, age_months):
        return self.age_min_months <= age_months <= self.age_max_months


class MethodQuery(BaseModel):
    """Аргументы поиска. На неделе 13 модель будет передавать их в инструмент."""

    age_months: int = Field(ge=MIN_AGE_MONTHS, le=MAX_AGE_MONTHS)
    area: Area


class AssessmentAdvice(BaseModel):
    """Ответ агента в строгой форме."""

    summary: str = Field(min_length=1)
    recommended_areas: list[str] = Field(min_length=1)
    next_steps: list[str] = Field(min_length=1)
