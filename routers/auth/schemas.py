from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    login: str
    fullname: str
    email: EmailStr
    phone: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class UpdateUserRequest(BaseModel):
    first_name: str
    last_name: str
    middle_name: str
    email: EmailStr
    phone: str


class TokenResponse(BaseModel):
    success: bool
    token: str
    user: dict


class ErrorResponse(BaseModel):
    success: bool
    message: str
