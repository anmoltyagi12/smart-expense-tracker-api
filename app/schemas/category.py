from pydantic import BaseModel, Field, ConfigDict

class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    type: str = Field(pattern="^(income|expense)$")


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    type: str | None = Field(
        default=None,
        pattern="^(income|expense)$"
    )


class CategoryResponse(BaseModel):
    id: int
    name: str
    type: str
    is_default: bool
    user_id: int | None

    model_config = ConfigDict(from_attributes=True)
