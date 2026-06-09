from typing import Optional

from pydantic import BaseModel


class AthleteNameDTO(BaseModel):
    last_name: str
    first_name: str
    middle_name: Optional[str] = None


class ResultDTO(BaseModel):
    id: int
    fight_id: int
    winner_name: Optional[AthleteNameDTO] = None
    victory_type: str
    fight_duration: int

    @classmethod
    def from_result(cls, result, winner_name: dict | None) -> "ResultDTO":
        return cls.model_validate(
            {
                "id": result.id,
                "fight_id": result.fight_id,
                "winner_name": winner_name,
                "victory_type": result.victory_type.value
                if hasattr(result.victory_type, "value")
                else result.victory_type,
                "fight_duration": result.fight_duration,
            }
        )
