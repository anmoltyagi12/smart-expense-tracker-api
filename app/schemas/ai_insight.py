from typing import Literal
from pydantic import BaseModel, Field


class AIInsightContent(BaseModel):
    monthly_summary: str = Field(min_length=10, max_length=500)
    spending_observations: list[str] = Field(min_length=1, max_length=5)
    saving_suggestions: list[str] = Field(min_length=1, max_length=5)
    risk_level: Literal["low", "moderate", "high"]


class AIInsightResponse(BaseModel):
    id: int
    month: int
    year: int
    monthly_summary: str
    spending_observations: list[str]
    saving_suggestions: list[str]
    risk_level: Literal["low", "moderate", "high"]
    cached: bool
    generated_at: str
