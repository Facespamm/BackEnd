from datetime import datetime, timedelta, timezone

from dns.dnssecalgs import algorithms
from flask import request, Blueprint, jsonify
from flasgger import swag_from
from flask_jwt_extended import create_access_token

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
            'role': user.role,
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
                'name': user.name,
                'role': user.role,
                'referee_level': user.referee_level,
                'tatami_assigned': user.tatami_assigned
            }
        }), 200
    else:
        return jsonify({'success': False, 'message': 'Неверные учетные данные'}), 401

@auth_bp.route('/public/registrations/', methods=['POST'])
def public_registration():
    """Публичная регистрация участника"""
    data = request.get_json(silent=True) or {}

    required_fields = ['athlete_name', 'athlete_birthdate', 'club_name', 'tournament_id']
    for field in required_fields:
        if field not in data:
            return jsonify({'success': False, 'message': f'Поле {field} обязательно'}), 400


    return jsonify({'success': True, 'message': 'Регистрация успешно создана'}), 201
