from typing import Optional

from fastapi.param_functions import Query
from pydantic import Field
from pydantic.main import BaseModel


class FilterQueryParam(BaseModel):
    tournament_id: int = Query(gt=0)
    status: Optional[str] = Query(default=None)
    tatami: Optional[int] = Query(default=None, gt=0)


class BasicInformAthleteDTO(BaseModel):
    id: int
    first_name: str
    last_name: str
    middle_name: str
    gender: str

    @classmethod
    def from_basic_athlete_inform(cls, athlete) -> "BasicInformAthleteDTO":
        if isinstance(athlete, dict):
            return cls.model_validate(athlete)

        return cls.model_validate(
            {
                "id": athlete.id,
                "first_name": athlete.first_name,
                "last_name": athlete.last_name,
                "middle_name": athlete.middle_name,
                "gender": athlete.gender.value
                if hasattr(athlete.gender, "value")
                else athlete.gender,
            }
        )


class FightDTO(BaseModel):
    id: int
    tournament_id: int
    tatami: int
    status: str
    round_number: int
    fight_number: int
    white_athlete: Optional[BasicInformAthleteDTO] = Field(default=None)
    blue_athlete: Optional[BasicInformAthleteDTO] = Field(default=None)

    @classmethod
    def from_fight(
        cls,
        fight,
        white_athlete=None,
        blue_athlete=None,
    ) -> "FightDTO":
        return cls.model_validate(
            {
                "id": fight.id,
                "tournament_id": fight.tournament_category_id,
                "tatami": fight.tatami_number,
                "status": fight.status.value
                if hasattr(fight.status, "value")
                else fight.status,
                "round_number": fight.round_number,
                "fight_number": fight.fight_number,
                "white_athlete": BasicInformAthleteDTO.from_basic_athlete_inform(
                    white_athlete
                )
                if white_athlete
                else None,
                "blue_athlete": BasicInformAthleteDTO.from_basic_athlete_inform(
                    blue_athlete
                )
                if blue_athlete
                else None,
            }
        )


class AssignRefereeRequest(BaseModel):
    referee_id: int
    role: str


class EndFightRequest(BaseModel):
    start_time: str
    end_time: str
    winner_athlete_id: int
    victory_type: str


class ChangeAthletesRequest(BaseModel):
    first_fight_id: int
    first_athlete_id: int
    second_fight_id: int
    second_athlete_id: int
