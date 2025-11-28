from flasgger import swag_from
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from databse.db import create_session
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
                                'first_name': {'type': 'string'},
                                'last_name': {'type': 'string'},
                                'middle_name': {'type': 'string'},
                                'email': {'type': 'string'},
                                'phone': {'type': 'string'},
                                'is_active': {'type': 'boolean'},
                                'created_at': {'type': 'string'},
                                'roles': {
                                    'type': 'array',
                                    'items': {'type': 'string'}
                                }
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
            # Получаем названия ролей пользователя
            role_names = [role.name for role in user.roles] if user.roles else []

            result.append({
                'id': user.id,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'middle_name': user.middle_name,
                'email': user.email,
                'phone': user.phone,
                'is_active': user.is_active,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'roles': role_names,
                'full_name': f"{user.last_name} {user.first_name} {user.middle_name or ''}".strip()
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


@users_bp.route('/<int:user_id>', methods=['GET'])
@swag_from({
    'tags': ['Users'],
    'summary': 'Получить пользователя по ID',
    'description': 'Возвращает информацию о конкретном пользователе',
    'parameters': [
        {
            'name': 'user_id',
            'in': 'path',
            'type': 'integer',
            'required': True,
            'description': 'ID пользователя'
        }
    ],
    'responses': {
        200: {
            'description': 'Данные пользователя получены успешно',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean'},
                    'user': {
                        'type': 'object',
                        'properties': {
                            'id': {'type': 'integer'},
                            'username': {'type': 'string'},
                            'first_name': {'type': 'string'},
                            'last_name': {'type': 'string'},
                            'middle_name': {'type': 'string'},
                            'email': {'type': 'string'},
                            'phone': {'type': 'string'},
                            'is_active': {'type': 'boolean'},
                            'created_at': {'type': 'string'},
                            'updated_at': {'type': 'string'},
                            'roles': {
                                'type': 'array',
                                'items': {'type': 'string'}
                            },
                            'referees': {
                                'type': 'array',
                                'items': {
                                    'type': 'object',
                                    'properties': {
                                        'id': {'type': 'integer'},
                                        'level': {'type': 'string'},
                                        'category': {'type': 'string'}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        404: {
            'description': 'Пользователь не найден'
        },
        500: {
            'description': 'Ошибка сервера'
        }
    }
})
def get_user_by_id(user_id: int):
    """Получить пользователя по ID"""
    try:
        user = User.query.filter_by(id=user_id, is_active=True).first()

        if not user:
            return jsonify({
                'success': False,
                'message': 'Пользователь не найден'
            }), 404

        # Получаем названия ролей пользователя
        role_names = [role.name for role in user.roles] if user.roles else []

        # Информация о судьях (если есть)
        referees_info = []
        if user.referees:
            for referee in user.referees:
                referees_info.append({
                    'id': referee.id,
                    'level': getattr(referee, 'level', None),
                    'category': getattr(referee, 'category', None)
                })

        user_data = {
            'id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'middle_name': user.middle_name,
            'email': user.email,
            'phone': user.phone,
            'is_active': user.is_active,
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'updated_at': user.updated_at.isoformat() if user.updated_at else None,
            'roles': role_names,
            'full_name': f"{user.last_name} {user.first_name} {user.middle_name or ''}".strip(),
            'referees': referees_info
        }

        return jsonify({
            'success': True,
            'user': user_data
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при получении пользователя: {str(e)}'
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
                'required': ['username', 'password', 'first_name', 'last_name'],
                'properties': {
                    'username': {
                        'type': 'string',
                        'description': 'Имя пользователя (логин)'
                    },
                    'password': {
                        'type': 'string',
                        'description': 'Пароль пользователя'
                    },
                    'first_name': {
                        'type': 'string',
                        'description': 'Имя пользователя'
                    },
                    'last_name': {
                        'type': 'string',
                        'description': 'Фамилия пользователя'
                    },
                    'middle_name': {
                        'type': 'string',
                        'description': 'Отчество пользователя'
                    },
                    'email': {
                        'type': 'string',
                        'description': 'Email адрес'
                    },
                    'phone': {
                        'type': 'string',
                        'description': 'Телефон'
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

        if not data.get('username') or not data.get('password') or not data.get('first_name') or not data.get(
                'last_name'):
            return jsonify({
                'success': False,
                'message': 'Обязательные поля: username, password, first_name, last_name'
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
            first_name=data['first_name'],
            last_name=data['last_name'],
            middle_name=data.get('middle_name'),
            email=data.get('email'),
            phone=data.get('phone')
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


@users_bp.route('/<int:user_id>', methods=['PUT'])
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

            # Обновляем только переданные поля
            if 'first_name' in data:
                user.first_name = data['first_name']
            if 'last_name' in data:
                user.last_name = data['last_name']
            if 'middle_name' in data:
                user.middle_name = data['middle_name']
            if 'email' in data:
                user.email = data['email']
            if 'phone' in data:
                user.phone = data['phone']
            if 'username' in data:
                # Проверяем уникальность нового username
                if data['username'] != user.username:
                    existing = User.query.filter_by(username=data['username']).first()
                    if existing:
                        return jsonify({
                            'success': False,
                            'message': 'Пользователь с таким именем уже существует'
                        }), 400
                user.username = data['username']

            session.commit()

        return jsonify({
            'success': True,
            'message': 'Пользователь успешно обновлен'
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при обновлении пользователя: {str(e)}'
        }), 500


@users_bp.route('/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id: int):
    """Удалить пользователя"""
    session_factory = create_session()

    try:
        with session_factory() as session:
            user = session.get(User, user_id)

            if not user:
                return jsonify({
                    'success': False,
                    'message': 'Пользователь не найден'
                }), 404

            # Мягкое удаление
            user.is_active = False
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