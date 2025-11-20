from flask_restx import Namespace, Resource, fields
from flask import request
from models.user import User
from utils.security import hash_password, check_password
import jwt
import datetime

auth_ns = Namespace('auth', description='Аутентификация и авторизация')

login_model = auth_ns.model('Login', {
    'username': fields.String(required=True, description='Имя пользователя'),
    'password': fields.String(required=True, description='Пароль')
})

user_model = auth_ns.model('User', {
    'id': fields.Integer(readonly=True),
    'username': fields.String(required=True),
    'name': fields.String(required=True),
    'email': fields.String(),
    'phone': fields.String(),
    'role': fields.String(required=True),
    'referee_level': fields.String(),
    'tatami_assigned': fields.Integer()
})


@auth_ns.route('/login')
class Login(Resource):
    @auth_ns.expect(login_model)
    def post(self):
        """Аутентификация пользователя"""
        data = request.json
        username = data.get('username')
        password = data.get('password')

        user = User.query.filter_by(username=username, is_active=True).first()

        if user and user.check_password(password):
            # Генерация JWT токена
            token = jwt.encode({
                'user_id': user.id,
                'username': user.username,
                'role': user.role,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
            }, 'your-secret-key', algorithm='HS256')

            return {
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
            }
        else:
            return {'success': False, 'message': 'Неверные учетные данные'}, 401


# @auth_ns.route('/profile')
# class Profile(Resource):
#     @auth_ns.marshal_with(user_model)
#     def get(self):
#         """Получить профиль текущего пользователя"""
#         # Здесь должна быть проверка JWT токена
#         user_id = get_user_id_from_token()  # Реализуйте эту функцию
#         user = User.query.get(user_id)
#         return user