from datetime import datetime, timedelta, timezone
from flask import request, Blueprint, jsonify
from flasgger import swag_from
from databse.db import create_session
from models.user import User
from flask_jwt_extended import create_access_token

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')  # исправил имя с 'clubs' на 'auth'

@auth_bp.route('/login', methods=['POST'])
@swag_from({
    "summary": "Аутентификация пользователя",
    "description": "Возвращает JWT-токен и информацию о пользователе при успешном логине",
    "tags": ["Аутентификация"],
    "parameters": [
        {
            "name": "body",
            "in": "body",
            "required": True,
            "schema": {
                "type": "object",
                "properties": {
                    "username": {
                        "type": "string",
                        "example": "admin",
                        "description": "Имя пользователя"
                    },
                    "password": {
                        "type": "string",
                        "example": "secret123",
                        "description": "Пароль"
                    }
                },
                "required": ["username", "password"]
            }
        }
    ],
    "responses": {
        "200": {
            "description": "Успешный вход",
            "schema": {
                "type": "object",
                "properties": {
                    "token": {"type": "string"},
                    "user": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"},
                            "username": {"type": "string"},
                            "name": {"type": "string"},
                            "role": {"type": "string"},
                            "referee_level": {"type": "string"},
                            "tatami_assigned": {"type": "integer"}
                        }
                    }
                }
            },
            "examples": {
                "application/json": {
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
        },
        "400": {
            "description": "Некорректный запрос",
            "schema": {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "message": {"type": "string"}
                }
            }
        },
        "401": {
            "description": "Неверные учетные данные",
            "schema": {
                "type": "object",
                "properties": {
                    "message": {"type": "string"}
                }
            }
        }
    }
})
def login():
    """Аутентификация пользователя"""
    data = request.get_json(silent=True) or {}
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'success': False, 'message': 'Логин и пароль обязательны'}), 400

    user = User.query.filter_by(username=username, is_active=True).first()

    if user and user.check_password(password):
        payload = {
            'role': user.role,
            'exp': datetime.now(timezone.utc) + timedelta(hours=24)
        }

        token = create_access_token(
            identity=user.id,
            additional_claims=payload,
            expires_delta=timedelta(hours=24),
        )

        return jsonify({
            'token': token,
            'user': {
                'id': user.id,
                'username': user.username,
                'name': user.name,
                'role': user.role,
                'referee_level': user.referee_level,
                'tatami_assigned': user.tatami_assigned
            }
        }), 200
    else:
        return jsonify({'message': 'Неверные учетные данные'}), 401


@auth_bp.route('/register', methods=['POST'])
def registration():
    data = request.get_json(silent=True) or {}
    username = data.get('username')
    password = data.get('password')
    name = data.get('name')
    role = data.get('role')
    phone = data.get('phone')

    session =create_session()

    try:
        user = User(
            username=username,
            name=name,
            role=role,
            phone=phone,
            password_hash = User.set_password(password)
        )

        session.add(user)
        session.commit()
        session.close()
    cat
# @auth_ns.route('/profile')
# class Profile(Resource):
#     @auth_ns.marshal_with(user_model)
#     def get(self):
#         """Получить профиль текущего пользователя"""
#         # Здесь должна быть проверка JWT токена
#         user_id = get_user_id_from_token()  # Реализуйте эту функцию
#         user = User.query.get(user_id)
#         return user
