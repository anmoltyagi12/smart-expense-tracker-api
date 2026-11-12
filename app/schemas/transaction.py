
from datetime import date as Date
from pydantic import BaseModel, Field, ConfigDict, field_validator


class TransactionCreate(BaseModel):
    amount: int = Field(gt=0, description="Amount in paise")
    type: str = Field(pattern="^(income|expense)$")
    date: Date
    note: str | None = Field(default=None, max_length=500)
    payment_method: str | None = Field(default=None, max_length=50)
    category_id: int = Field(gt=0)

    @field_validator("date")
    @classmethod
    def validate_date(cls, value):
        if value > Date.today():
            raise ValueError("Transaction date cannot be in the future")
        return value


class TransactionUpdate(BaseModel):
    amount: int | None = Field(default=None, gt=0)
    type: str | None = Field(default=None, pattern="^(income|expense)$")
    date: Date | None = None
    note: str | None = Field(default=None, max_length=500)
    payment_method: str | None = Field(default=None, max_length=50)
    category_id: int | None = Field(default=None, gt=0)

    @field_validator("date")
    @classmethod
    def validate_date(cls, value):
        if value is not None and value > Date.today():
            raise ValueError("Transaction date cannot be in the future")
        return value


class TransactionResponse(BaseModel):
    id: int
    amount: int
    type: str
    date: Date
    note: str | None
    payment_method: str | None
    user_id: int
    category_id: int

    model_config = ConfigDict(from_attributes=True)
