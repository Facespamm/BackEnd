from datetime import datetime
from typing import Optional

from fastapi import Query
from pydantic import BaseModel, Field


class WeighingFilterParams(BaseModel):
    tournament_id: int = Query(gt=0)
    category_id: int = Query(gt=0)
    athlete_id: Optional[int] = Query(default=None, gt=0)


class WeightCategoryDTO(BaseModel):
    name: str
    weight_range: str
    age_range: str
    gender: str

    @classmethod
    def from_category(cls, category) -> "WeightCategoryDTO":
        return cls.model_validate(
            {
                "name": category.name,
                "weight_range": f"от {category.min_weight} до {category.max_weight}",
                "age_range": f"от {category.min_year} до {category.max_year}",
                "gender": category.gender.value
                if hasattr(category.gender, "value")
                else category.gender,
            }
        )


class WeighingDTO(BaseModel):
    id: int
    athlete_name: str
    weight: float
    weight_category: Optional[WeightCategoryDTO] = None
    tournament_name: Optional[str] = None
    weighing_time: datetime
    status: bool
    is_valid: bool

    @classmethod
    def from_weighing(
        cls,
        weighing,
        athlete_name: str,
        category=None,
        tournament_name: Optional[str] = None,
        status: bool = False,
    ) -> "WeighingDTO":
        return cls.model_validate(
            {
                "id": weighing.id,
                "athlete_name": athlete_name,
                "weight": weighing.weight,
                "weight_category": WeightCategoryDTO.from_category(category)
                if category
                else None,
                "tournament_name": tournament_name,
                "weighing_time": weighing.weighing_time,
                "status": status,
                "is_valid": weighing.is_valid,
            }
        )


class CreateWeighingRequest(BaseModel):
    tournament_id: int
    category_id: int
    athlete_id: int
    weight: float = Field(gt=0)
    notes: Optional[str] = None


class UpdateWeighingRequest(BaseModel):
    weight: Optional[float] = Field(default=None, gt=0)
    weight_category: Optional[int] = None
    is_valid: Optional[bool] = None
    notes: Optional[str] = None


class ChangeCategoryRequest(BaseModel):
    category_id: int
    athlete_id: int
