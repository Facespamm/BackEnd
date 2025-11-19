from flask_restx import Namespace, Resource, fields
from flask import request
from models.user import User
from utils.security import hash_password

users_ns = Namespace('users', description='Операции с пользователями (админка)')

user_model = users_ns.model('User', {
    'username': fields.String(required=True),
    'password': fields.String(required=True),
    'name': fields.String(required=True),
    'email': fields.String(),
    'phone': fields.String(),
    'role': fields.String(required=True),
    'referee_level': fields.String(),
    'tatami_assigned': fields.Integer()
})


@users_ns.route('/')
class UserList(Resource):
    @users_ns.doc('list_users')
    def get(self):
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

            return {
                'success': True,
                'users': result,
                'total': len(result)
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Ошибка при получении пользователей: {str(e)}'
            }, 500

    @users_ns.expect(user_model)
    @users_ns.doc('create_user')
    def post(self):
        """Создать нового пользователя"""
        try:
            data = request.json

            if not data.get('username') or not data.get('password') or not data.get('name'):
                return {
                    'success': False,
                    'message': 'Обязательные поля: username, password, name'
                }, 400

            # Проверяем уникальность username
            existing_user = User.query.filter_by(username=data['username']).first()
            if existing_user:
                return {
                    'success': False,
                    'message': 'Пользователь с таким именем уже существует'
                }, 400

            user = User(
                username=data['username'],
                name=data['name'],
                email=data.get('email'),
                phone=data.get('phone'),
                role=data.get('role', 'VIEWER'),
                referee_level=data.get('referee_level'),
                tatami_assigned=data.get('tatami_assigned')
            )

            user.set_password(data['password'])

            if user.save():
                return {
                    'success': True,
                    'message': 'Пользователь успешно создан',
                    'user_id': user.id
                }, 201
            else:
                return {
                    'success': False,
                    'message': 'Ошибка при сохранении пользователя'
                }, 400

        except Exception as e:
            return {
                'success': False,
                'message': f'Ошибка при создании пользователя: {str(e)}'
            }, 500