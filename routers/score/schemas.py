from typing import Any, List, Optional

from pydantic import BaseModel, Field


class AthleteColorRequest(BaseModel):
    athlete_color: str = Field(min_length=1)


class ScoreTechniqueRequest(AthleteColorRequest):
    technique: Optional[str] = None


class PenaltyRequest(AthleteColorRequest):
    penalty_type: str = Field(min_length=1)


class EventsBatchRequest(BaseModel):
    events: List[dict[str, Any]]
