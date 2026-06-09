from datetime import date

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class ClubDTO(BaseModel):
    id: int
    name: str
    short_name: str | None = None
    country: str | None = None
    city: str | None = None
    address: str | None = None
    phone: str | None = None
    email: str | None = None
    website: str | None = None
    coach_name: str | None = None
    founded_year: int | None = None
    athletes_count: int = 0

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_club(cls, club, athletes_count: int = 0) -> "ClubDTO":
        return cls.model_validate(
            {
                "id": club.id,
                "name": club.name,
                "short_name": club.short_name,
                "country": club.country,
                "city": club.city,
                "address": club.address,
                "phone": club.phone,
                "email": club.email,
                "website": club.website,
                "coach_name": club.coach_name,
                "founded_year": club.founded_year,
                "athletes_count": athletes_count,
            }
        )


class CreateClubRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    short_name: str | None = Field(default=None, max_length=20)
    country: str | None = Field(default=None, max_length=50)
    city: str | None = Field(default=None, max_length=50)
    address: str | None = None
    phone: str | None = Field(default=None, max_length=20)
    email: EmailStr | None = Field(default=None, max_length=100)
    website: str | None = Field(default=None, max_length=200)
    coach_name: str | None = Field(default=None, max_length=100)
    founded_year: int | None = Field(default=None, ge=1800, le=2100)

    @field_validator(
        "name",
        "short_name",
        "country",
        "city",
        "address",
        "phone",
        "website",
        "coach_name",
        mode="before",
    )
    @classmethod
    def strip_strings(cls, value):
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value


class UpdateClubRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    short_name: str | None = Field(default=None, max_length=20)
    country: str | None = Field(default=None, max_length=50)
    city: str | None = Field(default=None, max_length=50)
    address: str | None = None
    phone: str | None = Field(default=None, max_length=20)
    email: EmailStr | None = Field(default=None, max_length=100)
    website: str | None = Field(default=None, max_length=200)
    coach_name: str | None = Field(default=None, max_length=100)
    founded_year: int | None = Field(default=None, ge=1800, le=2100)

    @field_validator(
        "name",
        "short_name",
        "country",
        "city",
        "address",
        "phone",
        "website",
        "coach_name",
        mode="before",
    )
    @classmethod
    def strip_strings(cls, value):
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value


class AssignAthletesRequest(BaseModel):
    athlete_ids: list[int] = Field(min_length=1)


class ClubAthleteTournamentDTO(BaseModel):
    tournament_id: int
    tournament_name: str


class ClubAthleteDTO(BaseModel):
    id: int
    user_id: int
    last_name: str
    first_name: str
    middle_name: str | None = None
    birth_date: date | None = None
    age: int | None = None
    gender: str | None = None
    rank: str | None = None
    license_number: str | None = None
    medical_check: bool | None = None
    insurance_number: str | None = None
    is_active: bool
    tournaments: list[ClubAthleteTournamentDTO] | None = None


class MessageResponse(BaseModel):
    success: bool
    message: str


class ClubListResponse(BaseModel):
    success: bool
    clubs: list[ClubDTO]
    total: int


class ClubResponse(BaseModel):
    success: bool
    club: ClubDTO


class ClubAthletesResponse(BaseModel):
    success: bool
    club_id: int
    club_name: str
    athletes_count: int
    athletes: list[ClubAthleteDTO]


class ErrorResponse(BaseModel):
    success: bool = False
    message: str
