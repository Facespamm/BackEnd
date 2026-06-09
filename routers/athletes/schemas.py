from datetime import date
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class CreateAthleteRequest(BaseModel):
    bith_date: date
    gender: str
    rank_id: Optional[int] = Field(default=None)
    medical_check: bool = Field(default=False)
    club_id: Optional[int] = Field(default=None)
    license_number: Optional[str] = Field(default=None)
    insurance_number: Optional[str] = Field(default=None)


class CreateAthleteByAdminRequest(BaseModel):
    login: str
    fullname: str
    email: EmailStr
    phone: str
    birth_date: date
    gender: str
    club_id: Optional[int] = Field(default=None)
    rank_id: Optional[int] = Field(default=None)
    license_number: Optional[str] = Field(default=None)
    medical_check: bool = Field(default=False)
    insurance_number: Optional[str] = Field(default=None)


class UpdateAthleteRequest(BaseModel):
    first_name: str
    last_name: str
    middle_name: str
    phone: str
    email: EmailStr
    birth_date: date
    gender: str
    club_id: Optional[int] = Field(default=None)
    rank_id: Optional[int] = Field(default=None)
    license_number: Optional[str] = Field(default=None)
    medical_check: Optional[bool] = Field(default=None)
    insurance_number: Optional[str] = Field(default=None)
