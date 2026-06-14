from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class MessageResponse(BaseModel):
    success: bool
    message: str


class TournamentDTO(BaseModel):
    id: int
    name: str
    start_date: date
    end_date: date
    venue: str | None = None
    city: str | None = None
    country: str
    status: str
    tatami_count: int
    athletes_count: int
    description: str | None = None
    has_consolation_fights: bool

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_tournament(cls, tournament, athletes_count: int = 0) -> "TournamentDTO":
        return cls.model_validate(
            {
                "id": tournament.id,
                "name": tournament.name,
                "start_date": tournament.start_date,
                "end_date": tournament.end_date,
                "venue": tournament.venue,
                "city": tournament.city,
                "country": tournament.country,
                "status": tournament.status.value
                if hasattr(tournament.status, "value")
                else tournament.status,
                "tatami_count": tournament.tatami_count,
                "athletes_count": athletes_count,
                "description": tournament.description,
                "has_consolation_fights": tournament.has_consolation_fights,
            }
        )


class TournamentCreateRequest(BaseModel):
    name: str = Field(min_length=1)
    start_date: date
    end_date: date
    list_category: list[int] = Field(min_length=1)
    description: str | None = None
    venue: str | None = None
    city: str | None = None
    country: str = "Россия"
    tatami_count: int = Field(default=1, ge=1, gt=0)
    has_consalation: bool = False


class TournamentUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    venue: str | None = None
    city: str | None = None
    country: str | None = None
    status: str | None = None
    tatami_count: int = Field(ge=1)
    has_consolation_fights: bool | None = None


class AddAthletesRequest(BaseModel):
    athlete_ids: list[int] = Field(min_length=1)
