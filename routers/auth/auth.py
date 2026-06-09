from datetime import datetime, timedelta, timezone

from fastapi import Depends, Response
from fastapi.responses import JSONResponse
from fastapi.routing import APIRouter
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from models import UserNew
from models.Enums import RoleName
from repository.auth_repo import AuthRepository
from routers.auth.schemas import (
    ErrorResponse,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UpdateUserRequest,
)
from utils.password import hash_password, verify_password
from utils.security import admin_depd, create_access_token

auth_router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@auth_router.post("/login")
async def login(enter_date: LoginRequest):
    """Аутентификация пользователя"""

    if not enter_date.login or not enter_date.password:
        return {"success": False, "message": "Логин и пароль обязательны"}

    with AuthRepository() as auth_repo:
        user = auth_repo.get_user_by_username(enter_date.login)

        user_role = (
            auth_repo.get_role_by_user(user.id)
            if user is UserNew and user.id is int
            else None
        )

        if user_role is None:
            return {"success": False, "message": "Роль пользователя не найдена"}

        password_hash = (
            user.password_hash if user and isinstance(user.password_hash, str) else None
        )
        if password_hash is None:
            return {"success": False, "message": "Пароль не установлен"}

        check_password = verify_password(enter_date.password, password_hash)

    if user and check_password:
        payload = {
            "user_id": user.id,
            "role": user_role.name,
            "exp": datetime.now(timezone.utc) + timedelta(hours=24),
        }

        token = create_access_token(additional_claims=payload)

        return TokenResponse(
            success=True,
            token=token,
            user={
                "id": user.id,
                "username": user.username,
                "name": f"{user.first_name} {user.middle_name} {user.last_name}",
                "role": user_role.name,
            },
        )
    else:
        return ErrorResponse(success=False, message="Неверные учетные данные")


@auth_router.post("/token")
async def create_token(
    response: Response, enter_data: OAuth2PasswordRequestForm = Depends()
):
    """Аутентификация пользователя"""
    if not enter_data.username or not enter_data.password:
        return {"success": False, "message": "Логин и пароль обязательны"}

    with AuthRepository() as auth_repo:
        user = auth_repo.get_user_by_username(enter_data.username)

        user_role = (
            auth_repo.get_role_by_user(user.id)
            if isinstance(user, UserNew) and isinstance(user.id, int)
            else None
        )

        if user_role is None:
            return ({"success": False, "message": "Роль пользователя не найдена"},)

        password_hash = (
            user.password_hash if user and isinstance(user.password_hash, str) else None
        )
        if password_hash is None:
            return {"success": False, "message": "Пароль не установлен"}

        check_password = verify_password(enter_data.password, password_hash)

        if user and check_password:
            payload = {
                "user_id": user.id,
                "role": user_role.name,
                "exp": datetime.now(timezone.utc) + timedelta(hours=24),
            }

            token = create_access_token(
                # identity=user.id,
                additional_claims=payload
            )

            response = JSONResponse({"access_token": token, "token_type": "bearer"})

            response.set_cookie(
                key="JWT_TOKEN",
                value=token,
                httponly=True,
                samesite="lax",
            )

            return response


@auth_router.post("/public/registrations/")
async def public_registration(register_data: RegisterRequest):
    """Публичная регистрация участника"""
    with AuthRepository() as auth_repo:
        existing_user = auth_repo.get_user_by_username(register_data.login)

        if existing_user:
            return {
                "success": False,
                "message": "Пользователь с таким логином уже существует",
            }

        names = register_data.fullname.strip().split(" ")

        new_user = UserNew(
            username=register_data.login,
            password_hash=hash_password(register_data.password),
            rst_name=names[0],
            middle_name=names[1] if len(names) > 1 else "",
            last_name=names[2] if len(names) > 1 else "",
            email=register_data.email,
            phone=register_data.phone,
            is_active=True,
        )

        user_id = auth_repo.create_user(new_user)
        role_id = auth_repo.get_role_id(RoleName.VIEWER.value)
        is_added = auth_repo.set_user_role(user_id, role_id)
        print(f"User_role is added : {is_added}")

    token = create_access_token(
        additional_claims={"role": RoleName.VIEWER.value, "user_id": user_id}
    )

    return {
        "success": True,
        "message": "Регистрация успешно создана",
        "token": token,
        "role": RoleName.VIEWER.value,
    }


@auth_router.get("/users", dependencies=[admin_depd])
async def get_users():
    """Получить список пользователей"""
    try:
        with AuthRepository() as auth_repo:
            users = auth_repo.get_users()

            result = []
            for user, role_name in users:
                result.append(
                    {
                        "id": user.id,
                        "username": user.username,
                        "name": f"{user.first_name} {user.middle_name} {user.last_name}",
                        "email": user.email,
                        "phone": user.phone,
                        "role": role_name,
                    }
                )

        return {"success": True, "users": result, "total": len(result)}

    except Exception as e:
        return {
            "success": False,
            "message": f"Ошибка при получении пользователей: {str(e)}",
        }


@auth_router.put("/{user_id}/update", dependencies=[admin_depd])
async def update_user(user_id: int, update_data: UpdateUserRequest):
    """Изменить информацию о пользователе"""
    try:
        with AuthRepository() as auth_repo:
            user = auth_repo.get_user_by_id(user_id)

            if not user or user.is_active is False:
                return {"success": False, "message": "Пользователь не найден"}

            auth_repo.update_user(user, update_data)

        return {"success": True, "message": "Данные пользователя успешно обнавленны"}
    except Exception as e:
        return {
            "success": False,
            "message": f"Ошибка при обновление данных пользователя: {str(e)}",
        }
