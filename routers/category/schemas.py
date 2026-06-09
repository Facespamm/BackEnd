from pydantic import BaseModel, Field


class CreateCategoryRequest(BaseModel):
    gender: str
    min_weight: float = Field(default=0.0, gt=0.0)
    max_weight: float = Field(default=0.0, gt=0.0)
    min_age: int
    max_age: int


class UpdateCategoryRequest(BaseModel):
    name: str
    gender: str
    min_weight: float = Field(default=0.0, gt=0.0)
    max_weight: float = Field(default=0.0, gt=0.0)
    min_age: int
    max_age: int
