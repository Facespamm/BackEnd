from datetime import datetime, timedelta, timezone

from flasgger import swag_from
from flask import request, Blueprint, jsonify
from flask_jwt_extended import create_access_token

from models.user import User
from repository.auth_repo import AuthRepository
from utils.security import hash_password

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')  # исправил имя с 'clubs' на 'auth'


@auth_bp.route('/public/registrations/', methods=['POST'])
@swag_from({
    "summary": "Публичная регистрация пользователя",
    "description": "Регистрация нового пользователя. Возвращает JWT-токен при успешной регистрации.",
    "tags": ["Аутентификация"],
    "requestBody": {
        "required": True,
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "username": {
                            "type": "string",
                            "example": "ivanov_ivan",
                            "description": "Уникальный логин пользователя"
                        },
                        "password": {
                            "type": "string",
                            "format": "password",
                            "example": "MyPass123!",
                            "description": "Пароль"
                        },
                        "first_name": {
                            "type": "string",
                            "example": "Иван",
                            "description": "Имя"
                        },
                        "last_name": {
                            "type": "string",
                            "example": "Иванов",
                            "description": "Фамилия"
                        },
                        "email": {
                            "type": "string",
                            "format": "email",
                            "example": "ivanov@example.com",
                            "description": "Электронная почта"
                        },
                        "phone": {
                            "type": "string",
                            "example": "+79991234567",
                            "description": "Номер телефона"
                        },
                        "role": {
                            "type": "string",
                            "enum": ["ATHLETE", "REFEREE", "VIEWER"],
                            "example": "ATHLETE",
                            "description": "Роль пользователя"
                        }
                    },
                    "required": ["username", "password", "first_name", "last_name", "email", "phone", "role"]
                },
                "example": {
                    "username": "ivanov_ivan",
                    "password": "MyPass123!",
                    "first_name": "Иван",
                    "last_name": "Иванов",
                    "email": "ivanov@example.com",
                    "phone": "+79991234567",
                    "role": "ATHLETE"
                }
            }
        }
    },
    "responses": {
        "201": {
            "description": "Пользователь успешно зарегистрирован",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "success": {"type": "boolean", "example": True},
                            "message": {"type": "string", "example": "Регистрация успешно создана"},
                            "token": {"type": "string", "description": "JWT токен для аутентификации"},
                            "role": {"type": "string", "example": "ATHLETE"}
                        }
                    },
                    "example": {
                        "success": True,
                        "message": "Регистрация успешно создана",
                        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xxxxx",
                        "role": "ATHLETE"
                    }
                }
            }
        },
        "400": {
            "description": "Ошибка валидации",
            "content": {
                "application/json": {
                    "examples": {
                        "missing_field": {
                            "value": {
                                "success": False,
                                "message": "Поле username обязательно"
                            }
                        },
                        "user_exists": {
                            "value": {
                                "success": False,
                                "message": "Пользователь с таким логином уже существует"
                            }
                        }
                    }
                }
            }
        }
    }
})
def public_registration():
    """Публичная регистрация участника"""
    data = request.get_json(silent=True) or {}

    required_fields = ['username', 'password', 'first_name', 'last_name', 'email', 'phone', 'role']

    # Проверяем обязательные поля
    for field in required_fields:
        if field not in data:
            return jsonify({
                'success': False,
                'message': f'Поле {field} обязательно'
            }), 400

    # Проверяем существование пользователя
    existing_user = User.query.filter_by(username=data['username']).first()
    if existing_user:
        return jsonify({
            'success': False,
            'message': 'Пользователь с таким логином уже существует'
        }), 400

    # Создаем пользователя с полями из модели User
    new_user = User(
        username=data['username'],
        password_hash=hash_password(data['password']),
        first_name=data['first_name'],
        last_name=data['last_name'],
        email=data['email'],
        phone=data['phone'],
        is_active=True,
    )

    try:
        auth_repo = AuthRepository()
        user_id = auth_repo.create_user(new_user)

        if not user_id:
            return jsonify({
                'success': False,
                'message': 'Не удалось создать пользователя'
            }), 500

        role_id = auth_repo.get_role_id(data['role'])

        if not role_id:
            return jsonify({
                'success': False,
                'message': f'Роль "{data["role"]}" не найдена'
            }), 400

        is_added = auth_repo.set_user_role(user_id, role_id)

        if not is_added:
            return jsonify({
                'success': False,
                'message': 'Не удалось установить роль пользователя'
            }), 500

        user_role = auth_repo.get_role_by_user(user_id)

        if not user_role:
            return jsonify({
                'success': False,
                'message': 'Не удалось получить роль пользователя'
            }), 500

        token = create_access_token(
            identity=user_id,
            additional_claims={'role': user_role.name}
        )

        return jsonify({
            'success': True,
            'message': 'Регистрация успешно создана',
            'token': token,
            'role': data['role'],
            'user_id': user_id
        }), 201

    except Exception as e:
        print(f"Ошибка при регистрации: {e}")
        return jsonify({
            'success': False,
            'message': 'Внутренняя ошибка сервера при регистрации'
        }), 500