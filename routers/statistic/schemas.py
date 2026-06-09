from datetime import date
from typing import Optional

from pydantic import BaseModel, EmailStr


class LiveStatisticsDTO(BaseModel):
    active_tournaments: int
    unique_athletes: int
    live_fights: int


class StatisticUserDTO(BaseModel):
    id: int
    username: str
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    is_active: bool
    roles: list[str]

    @classmethod
    def from_user(cls, user) -> "StatisticUserDTO":
        return cls.model_validate(
            {
                "id": user.id,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "middle_name": user.middle_name,
                "email": user.email,
                "phone": user.phone,
                "is_active": user.is_active,
                "roles": [role.name for role in user.roles],
            }
        )


class UpdateStatisticUserRequest(BaseModel):
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None


class UpdatedUserDTO(BaseModel):
    id: int
    username: str
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    is_active: bool

    @classmethod
    def from_user(cls, user) -> "UpdatedUserDTO":
        return cls.model_validate(
            {
                "id": user.id,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "middle_name": user.middle_name,
                "email": user.email,
                "phone": user.phone,
                "is_active": user.is_active,
            }
        )


class UsersByRoleDTO(BaseModel):
    role_name: str
    normalized_name: str
    count: int


class UsersRoleStatisticsDTO(BaseModel):
    total_active_users: int
    users_by_role: list[UsersByRoleDTO]
    users_without_role: int


class ActiveTournamentDTO(BaseModel):
    id: int
    name: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    city: Optional[str] = None
    country: Optional[str] = None
    tatami_count: int
    athletes_count: int
    live_fights_count: int

    @classmethod
    def from_tournament(
        cls,
        tournament,
        athletes_count: int,
        live_fights_count: int,
    ) -> "ActiveTournamentDTO":
        return cls.model_validate(
            {
                "id": tournament.id,
                "name": tournament.name,
                "start_date": tournament.start_date,
                "end_date": tournament.end_date,
                "city": tournament.city,
                "country": tournament.country,
                "tatami_count": tournament.tatami_count,
                "athletes_count": athletes_count,
                "live_fights_count": live_fights_count,
            }
        )
