from datetime import datetime, timedelta, timezone
from flask import request, Blueprint, jsonify
from flasgger import swag_from
from jwt import JWT

from models.user import User

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')  # исправил имя с 'clubs' на 'auth'


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
    password = data.get('password')

    if not username or not password:
        return jsonify({'success': False, 'message': 'Логин и пароль обязательны'}), 400

    user = User.query.filter_by(username=username, is_active=True).first()

    if user and user.check_password(password):
        payload = {
            'user_id': user.id,
            'username': user.username,
            'role': user.role,
            'exp': datetime.now(timezone.utc) + timedelta(hours=24)
        }

        token = JWT.encode(payload, key='your-secret-key', alg='HS256')

        return jsonify({
            'success': True,
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
        return jsonify({'success': False, 'message': 'Неверные учетные данные'}), 401

# @auth_ns.route('/profile')
# class Profile(Resource):
#     @auth_ns.marshal_with(user_model)
#     def get(self):
#         """Получить профиль текущего пользователя"""
#         # Здесь должна быть проверка JWT токена
#         user_id = get_user_id_from_token()  # Реализуйте эту функцию
#         user = User.query.get(user_id)
#         return user
