from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class RecommendationRequest(BaseModel):
    city: str
    date: date
    event_format: str
    category: str
    budget: int = Field(gt=0)
    duration_hours: Optional[float] = Field(default=None, gt=0)
    language: Optional[str] = None


class WhatIfRequest(RecommendationRequest):
    budget_steps: list[int] = [50000, 100000, 200000]
    date_range_days: int = Field(default=3, ge=1, le=14)
    duration_steps: list[float] = [1, 2]


class RejectionReason(BaseModel):
    code: str
    message: str


class RecommendationCard(BaseModel):
    id: str
    name: str
    categories: list[str]
    city: Optional[str]
    price: Optional[int]
    event_formats: list[str]
    languages: list[str]
    max_hours: Optional[float]
    description: str
    score: float
    why_this: list[str]
    data_confidence: int
    price_imputed: bool
    city_imputed: bool
    synthetic: bool


class RecommendationResponse(BaseModel):
    total_contractors: int
    eligible_count: int
    returned_count: int
    recommendations: list[RecommendationCard]
    why_not: dict[str, int]
