"""Structured contractor facts from the dataset."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional, Tuple


@dataclass(frozen=True)
class Contractor:
    id: str
    anon_name: str
    categories: Tuple[str, ...]
    city: str
    city_imputed: Optional[bool]
    synthetic: Optional[bool]
    price_from_kzt: Optional[Decimal]
    price_imputed: Optional[bool]
    event_formats: Tuple[str, ...]
    languages: Tuple[str, ...]
    max_hours: Optional[Decimal]
    busy_dates: Tuple[date, ...]
    description: str


from pydantic import BaseModel, ConfigDict, Field, field_validator


class RecommendationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    city: str = Field(min_length=1)
    date: date
    event_format: str = Field(min_length=1)
    category: str = Field(min_length=1)
    budget: Decimal = Field(ge=0, allow_inf_nan=False)
    duration_hours: Optional[Decimal] = Field(default=None, gt=0, allow_inf_nan=False)
    language: Optional[str] = Field(default=None, min_length=1)

    @field_validator("budget", "duration_hours", mode="before")
    @classmethod
    def reject_boolean_numbers(cls, value):
        if isinstance(value, bool):
            raise ValueError("Ожидалось число, а не логическое значение")
        return value
