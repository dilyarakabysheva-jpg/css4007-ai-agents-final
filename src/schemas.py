from pydantic import BaseModel, Field, field_validator


class ChildProfile(BaseModel):
    """Данные ребёнка. Возраст ограничен дошкольным и школьным возрастом."""

    age_months: int = Field(ge=12, le=96)
    concerns: list[str] = Field(min_length=1)

    @field_validator("concerns")
    @classmethod
    def clean(cls, value):
        items = [item.strip() for item in value if item.strip()]
        if not items:
            raise ValueError("concerns не может быть пустым")
        return items


class AssessmentAdvice(BaseModel):
    """Ответ агента в строгой форме."""

    summary: str = Field(min_length=1)
    recommended_areas: list[str] = Field(min_length=1)
    next_steps: list[str] = Field(min_length=1)