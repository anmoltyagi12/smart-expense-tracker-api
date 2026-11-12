from typing import List
from pydantic import BaseModel
from app.schemas.transaction import TransactionResponse


class TransactionSearchResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    items: List[TransactionResponse]
