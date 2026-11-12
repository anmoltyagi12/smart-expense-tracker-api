from datetime import date
from typing import Optional, List, Literal
from pydantic import BaseModel

class CategoryAnalytics(BaseModel):
    category_id: int
    category_name: str
    spent: int
    budget: Optional[int] = None
    remaining: Optional[int] = None
    utilization_percent: Optional[float] = None
    status: Literal[
        "no_budget",
        "within_budget",
        "warning",
        "limit_reached",
        "exceeded"
    ]


class MonthlySummaryResponse(BaseModel):
    month: int
    year: int
    total_income: int
    total_expenses: int
    net_savings: int
    total_budget: int
    total_budget_remaining: int
    over_budget_categories: int
    categories: List[CategoryAnalytics]


class TopExpenseResponse(BaseModel):
    transaction_id: int
    amount: int
    category_id: int
    category_name: str
    date: date
    note: Optional[str] = None
    payment_method: Optional[str] = None

    class Config:
        from_attributes = True
