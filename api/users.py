from flasgger import swag_from
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from database.db import create_session
from models.user import User
from config import USER_ROLES
users_bp = Blueprint('users', __name__, url_prefix='/users')


@users_bp.route('/', methods=['GET'])
@swag_from({
    'tags': ['Users'],
    'summary': 'Получить список пользователей',
    'description': 'Возвращает список всех активных пользователей (админка)',
    'responses': {
        200: {
            'description': 'Список пользователей получен успешно',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean'},
                    'users': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'id': {'type': 'integer'},
                                'username': {'type': 'string'},
                                'name': {'type': 'string'},
                                'email': {'type': 'string'},
                                'phone': {'type': 'string'},
                                'role': {'type': 'string'},
                                'role_display': {'type': 'string'},
                                'referee_level': {'type': 'string'},
                                'tatami_assigned': {'type': 'integer'}
                            }
                        }
                    },
                    'total': {'type': 'integer'}
                }
            }
        },
        500: {
            'description': 'Ошибка сервера'
        }
    }
})
def get_users():
    """Получить список пользователей"""
    try:
        users = User.query.filter_by(is_active=True).order_by(User.username).all()

        result = []
        for user in users:
            result.append({
                'id': user.id,
                'username': user.username,
                'name': user.name,
                'email': user.email,
                'phone': user.phone,
                'role': user.role,
                'role_display': user.role_display,
                'referee_level': user.referee_level,
                'tatami_assigned': user.tatami_assigned
            })

        return jsonify({
            'success': True,
            'users': result,
            'total': len(result)
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при получении пользователей: {str(e)}'
        }), 500

@users_bp.route('/', methods=['POST'])
@swag_from({
    'tags': ['Users'],
    'summary': 'Создать нового пользователя',
    'description': 'Создает нового пользователя в системе',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['username', 'password', 'name', 'role'],
                'properties': {
                    'username': {
                        'type': 'string',
                        'description': 'Имя пользователя (логин)'
                    },
                    'password': {
                        'type': 'string',
                        'description': 'Пароль пользователя'
                    },
                    'name': {
                        'type': 'string',
                        'description': 'Полное имя пользователя'
                    },
                    'email': {
                        'type': 'string',
                        'description': 'Email адрес'
                    },
                    'phone': {
                        'type': 'string',
                        'description': 'Телефон'
                    },
                    'role': {
                        'type': 'string',
                        'description': 'Роль пользователя',
                        'enum': ['ADMIN', 'REFEREE', 'SECRETARY', 'VIEWER'],
                        'default': 'VIEWER'
                    },
                    'referee_level': {
                        'type': 'string',
                        'description': 'Уровень судьи (для роли REFEREE)'
                    },
                    'tatami_assigned': {
                        'type': 'integer',
                        'description': 'Назначенное татами (для роли REFEREE)'
                    }
                }
            }
        }
    ],
    'responses': {
        201: {
            'description': 'Пользователь успешно создан',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean'},
                    'message': {'type': 'string'},
                    'user_id': {'type': 'integer'}
                }
            }
        },
        400: {
            'description': 'Ошибка валидации или пользователь уже существует'
        },
        500: {
            'description': 'Ошибка сервера'
        }
    }
})
@jwt_required()
def create_user():
    """Создать нового пользователя"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'message': 'Не передан JSON'
            }), 400

        if not data.get('username') or not data.get('password') or not data.get('name'):
            return jsonify({
                'success': False,
                'message': 'Обязательные поля: username, password, name'
            }), 400

        # Проверяем уникальность username
        existing_user = User.query.filter_by(username=data['username']).first()
        if existing_user:
            return jsonify({
                'success': False,
                'message': 'Пользователь с таким именем уже существует'
            }), 400

        user = User(
            username=data['username'],
            name=data['name'],
            email=data.get('email'),
            phone=data.get('phone'),
            role=data.get('role', USER_ROLES['VIEWER']),
            referee_level=data.get('referee_level', 0),
            tatami_assigned=data.get('tatami_assigned', None)
        )

        user.set_password(data['password'])

        if user.create():
            return jsonify({
                'success': True,
                'message': 'Пользователь успешно создан',
                'user_id': user.id
            }), 201
        else:
            return jsonify({
                'success': False,
                'message': 'Ошибка при сохранении пользователя'
            }), 400

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при создании пользователя: {str(e)}'
        }), 500

@users_bp.route('/<int:user_id>',  methods=['DELETE'])
@jwt_required()
def update_user(user_id: int):
    """Изменить информацию о пользователе"""
    session_factory = create_session()
    data = request.get_json()
    try:
        with session_factory() as session:
            user = session.get(User, user_id)

            if not user or not user.is_active:
                return jsonify({
                    'success': False,
                    'message': 'Пользователь не найден'
                }), 404

            user.name = data['name', user.name]
            user.email = data.get('email', user.email)
            user.phone = data.get('phone', user.phone)
            session.commit()

        return jsonify({
            'success': True,
            'message': 'Пользователь успешно удален'
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при удалении пользователя: {str(e)}'
        }), 500
