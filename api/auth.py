from datetime import datetime, timedelta, timezone

from flasgger import swag_from
from flask import request, Blueprint, jsonify
from flask_jwt_extended import create_access_token

from new_model.Enums import RoleName
from new_model.head_model.new_user import UserNew
from repository.auth_repo import AuthRepository

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
auth_repo = AuthRepository()

@auth_bp.route('/login', methods=['POST'])
@swag_from({
    "summary": "Аутентификация пользователя",
    "description": "Возвращает JWT-токен и информацию о пользователе при успешном логине",
    "tags": ["Аутентификация"],
    "requestBody": {
        "required": True,
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "username": {"type": "string", "example": "admin"},
                        "password": {"type": "string", "example": "secret123"}
                    },
                    "required": ["username", "password"]
                }
            }
        }
    },
    "responses": {
        "200": {
            "description": "Успешный вход",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "success": {"type": "boolean", "example": True},
                            "token": {"type": "string"},
                            "user": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "integer"},
                                    "username": {"type": "string"},
                                    "name": {"type": "string"},
                                    "role": {"type": "string"},
                                    "referee_level": {"type": "string", "nullable": True},
                                    "tatami_assigned": {"type": "integer", "nullable": True}
                                }
                            }
                        }
                    },
                    "example": {
                        "success": True,
                        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xxxxx",
                        "user": {
                            "id": 1,
                            "username": "admin",
                            "name": "Администратор",
                            "role": "admin",
                            "referee_level": None,
                            "tatami_assigned": None
                        }
                    }
                }
            }
        },
        "401": {
            "description": "Неверные учетные данные",
            "content": {
                "application/json": {
                    "example": {"success": False, "message": "Неверные учетные данные"}
                }
            }
        }
    }
})
def login():
    """Аутентификация пользователя"""
    data = request.get_json(silent=True) or {}
    username = data.get('username')
    password_enter = data.get('password')

    if not username or not password_enter:
        return jsonify({'success': False, 'message': 'Логин и пароль обязательны'}), 400

    user = auth_repo.get_user_by_username(username)

    user_role = auth_repo.get_role_by_user(user.id) if user else None

    if user_role is None:
        return jsonify({'success': False, 'message': 'Роль пользователя не найдена'}), 401

    if user and auth_repo.check_password(user,password_enter):
        payload = {
            'role': user_role.name,
            'exp': datetime.now(timezone.utc) + timedelta(hours=24)
        }

        token = create_access_token(
            identity=user.id,
            additional_claims=payload,
            expires_delta=timedelta(hours=24),
        )

        return jsonify({
            'success': True,
            'token': token,
            'user': {
                'id': user.id,
                'username': user.username,
                'name': user.first_name + ' '+ user.middle_name + ' ' + user.last_name,
                'role': user_role.name
            }
        }), 200
    else:
        return jsonify({'success': False, 'message': 'Неверные учетные данные'}), 401

@auth_bp.route('/public/registrations/', methods=['POST'])
def public_registration():
    """Публичная регистрация участника"""
    data = request.get_json(silent=True) or {}

    required_fields = ['login', 'fullname', 'email', 'phone', 'password','role']
    for field in required_fields:
        if field not in data:
            return jsonify({'success': False, 'message': f'Поле {field} обязательно'}), 400

    existing_user = auth_repo.get_user_by_username(data['login'])

    if existing_user:
        return jsonify({'success': False, 'message': 'Пользователь с таким логином уже существует'}), 400

    names = data['fullname'].strip().split(' ')

    new_user = UserNew(
        username=data['login'],
        password_hash = auth_repo.hash_password(data['password']),
        first_name=names[0],
        middle_name=names[1] if len(names) > 1 else '',
        last_name=names[2] if len(names) > 1 else '',
        email=data['email'],
        phone=data['phone'],
        is_active=True,
    )

    role_name = data.get('role', RoleName.VIEWER.value)
    user_id = auth_repo.create_user(new_user)
    role_id = auth_repo.get_role_id(role_name)
    is_added = auth_repo.set_user_role(user_id, role_id)
    print(f'User_role is added : {is_added}')

    user_role = auth_repo.get_role_by_user(user_id)
    token = create_access_token(identity=user_id, additional_claims={'role': user_role.name})

    return jsonify({'success': True,
                    'message': 'Регистрация успешно создана',
                    'token': token,
                    'role': data['role'],
                    }), 201
