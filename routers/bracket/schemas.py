from pydantic import BaseModel
from typing import Optional, List


class AthleteDTO(BaseModel):
    id: Optional[int] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    club: Optional[str] = None
    weight: Optional[float] = None

    class Config:
        extra = "allow"


class CategoryDTO(BaseModel):
    id: int
    name: str
    weight_range: str


class FightDTO(BaseModel):
    id: int
    blue_athlete: Optional[AthleteDTO] = None
    white_athlete: Optional[AthleteDTO] = None
    tatami_number: Optional[int] = None
    round: Optional[int] = None
    status_fight: Optional[str] = None
    next_fight: Optional[int] = None
    type_bracket: Optional[str] = None


class BaseResponse(BaseModel):
    success: bool
    message: Optional[str] = None


class FightsResponse(BaseModel):
    success: bool
    fights: Optional[List[FightDTO]] = None
    tournament_name: Optional[str] = None
    category: Optional[CategoryDTO] = None
    winner: Optional[AthleteDTO] = None
    message: Optional[str] = None

