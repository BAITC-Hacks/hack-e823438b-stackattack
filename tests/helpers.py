"""Artificial fixtures, never used as production catalogue data."""
from dataclasses import replace
from datetime import date
from decimal import Decimal
from backend.models import Contractor, RecommendationRequest


def query(**changes):
    return RecommendationRequest(**dict(dict(city="Алматы", date="2026-11-14", event_format="свадьба", category="Фотограф", budget=400000, duration_hours=8, language="русский"), **changes))


def contractor(**changes):
    base = Contractor("TEST-1", "Тестовый профиль", ("Фотограф",), "Алматы", False, True,
                      Decimal(200000), False, ("свадьба",), ("русский",), Decimal(10), (), "")
    return replace(base, **changes)
