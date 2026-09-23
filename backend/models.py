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

