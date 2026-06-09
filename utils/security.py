"""
Функции безопасности и аутентификации
"""

import os
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError, encode
from jwt.api_jwt import decode_complete

from models.Enums import RoleName

scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")
TokenDependency = Annotated[str, Depends(scheme)]


def create_access_token(additional_claims: dict):
    key = os.getenv("JWT_SECRET_KEY", None)
    if key is None:
        raise ValueError("JWT_SECRET_KEY is not set in environment variables")

    algorithms = os.getenv("JWT_ALGORITHM", None)
    if algorithms is None:
        raise ValueError("JWT_ALGORITHM is not set in environment variables")
    jwt_token = encode(payload=additional_claims, key=key, algorithm=algorithms)
    return jwt_token


def decode_access_token(token: str):
    key = os.getenv("JWT_SECRET_KEY", None)
    if key is None:
        raise ValueError("JWT_SECRET_KEY is not set in environment variables")

    algorithms = os.getenv("JWT_ALGORITHM", None)
    if algorithms is None:
        raise ValueError("JWT_ALGORITHM is not set in environment variables")

    try:
        playold = decode_complete(token, key=key, algorithms=[algorithms])
        return playold
    except InvalidTokenError as e:
        print(f"❌ Invalid token: {e}")
        return None


def require_role(required_role: str):
    def dependency(token: TokenDependency):
        decoded_token = decode_access_token(token)

        if not decoded_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )

        payload = decoded_token.get("payload") if decoded_token.get("payload") else None
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )

        role = payload.get("role")

        if role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: insufficient permissions",
            )

        user_id = payload.get("user_id", None)
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: user_id is missing",
            )

        return user_id

    return dependency


admin_depd = Depends(require_role(RoleName.ADMIN.value))
refere_depd = Depends(require_role(RoleName.REFEREE.value))
athlete_depd = Depends(require_role(RoleName.ATHLETE.value))
viewer_depd = Depends(require_role(RoleName.VIEWER.value))
