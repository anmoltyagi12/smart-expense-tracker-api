from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

class BudgetCreate(BaseModel):
    amount: int = Field(gt=0, description="Amount in paise")
    month: int = Field(ge=1, le=12)
    year: int = Field(ge=2024, le=2100)
    category_id: int = Field(gt=0)


class BudgetUpdate(BaseModel):
    amount: Optional[int] = Field(default=None, gt=0)


class BudgetResponse(BaseModel):
    id: int
    amount: int
    month: int
    year: int
    user_id: int
    category_id: int

    model_config = ConfigDict(from_attributes=True)
