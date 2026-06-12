from pydantic import BaseModel, EmailStr, Field, field_validator
from typing_extensions import List, Optional


class RefereeDTO(BaseModel):
    id: int
    first_name: str
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    email: Optional[EmailStr] = Field(default=None)
    phone: str
    certification_level: str

    @field_validator("email", mode="before")
    @classmethod
    def empty_email_to_none(cls, v):
        if v == "" or v is None:
            return None
        return v

    @classmethod
    def from_referee(cls, referee) -> "RefereeDTO":
        return cls.model_validate(
            {
                "id": referee.id,
                "first_name": referee.first_name,
                "last_name": referee.last_name,
                "middle_name": referee.middle_name,
                "email": referee.email,
                "phone": referee.phone,
                "certification_level": referee.certification_level.value
                if hasattr(referee.certification_level, "value")
                else referee.certification_level,
            }
        )


class CreateRefereeRequest(BaseModel):
    first_name: str
    last_name: str
    middle_name: str
    email: EmailStr
    phone: str
    certification_level: str


class AsignReferees(BaseModel):
    referees: List[int] = Field(max_length=3)

    @field_validator("referees")
    @classmethod
    def validate_referees(cls, value: List[int]) -> List[int]:
        if len(value) != 3:
            raise ValueError("Нужно выбрать ровно 3 судьи")

        if len(set(value)) != 3:
            raise ValueError("Судьи не должны повторяться")

        return value


class UpdateRefereRequest(BaseModel):
    email: EmailStr
    phone: str
    certification_level: str
